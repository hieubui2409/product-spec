#!/usr/bin/env python3
"""
analyze_telemetry.py — CLI front for the usage-&-health lenses. Deterministic
gather + render; the LLM (cleanmatic:telemetry skill) narrates the output. It
NEVER judges — it surfaces counts/rates/spans for the skill to adjudicate.
READ-ONLY. Ships in the release bundle.

Usage:
  analyze_telemetry.py --lens usage|session|health|all
                       [--days N] [--top N] [--format md|json|ascii|mermaid]
                       [--no-tokens]

Lenses land across phases; the registry below is the single extension point.
Env: CK_TELEMETRY_DIR / CK_SESSIONS_DIR / CK_SKILLS_DIR redirect inputs (tests).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
# Lens / render / catalog / formatters modules are flat siblings in this scripts/
# dir (self-contained skill layout — telemetry no longer depends on _shared).
sys.path.insert(0, str(_SCRIPT_DIR))

from formatters import json_output  # noqa: E402
import lens_usage_tokens  # noqa: E402
import lens_session_shape  # noqa: E402
import lens_health  # noqa: E402
import lens_forensics  # noqa: E402
import lens_memory_health  # noqa: E402
import lens_product_memory  # noqa: E402
import lens_workflow_chains  # noqa: E402
import lens_reliability  # noqa: E402
import lens_validate_proxy  # noqa: E402
import lens_artifact_heat  # noqa: E402

# name → gather callable taking the parsed args, returning a render-agnostic dict.
LENSES: dict[str, callable] = {
    "usage": lambda a: lens_usage_tokens.gather(days=a.days, with_tokens=not a.no_tokens),
    "session": lambda a: lens_session_shape.gather(),
    "health": lambda a: lens_health.gather(),
    "forensics": lambda a: lens_forensics.gather(session=a.session, all_sessions=a.all_sessions),
    "memory": lambda a: lens_memory_health.gather(),
    "product_memory": lambda a: lens_product_memory.gather(),
    "workflow": lambda a: lens_workflow_chains.gather(days=a.days, top=(a.top or 10)),
    "reliability": lambda a: lens_reliability.gather(days=a.days),
    "validate": lambda a: lens_validate_proxy.gather(days=a.days),
    "artifact_heat": lambda a: lens_artifact_heat.gather(days=a.days),
}

# The order lenses appear in --lens all / --overview.
OVERVIEW_ORDER = ["usage", "session", "health", "reliability", "workflow", "validate",
                  "memory", "product_memory", "artifact_heat"]


def gather_lens(name: str, args) -> dict:
    return LENSES[name](args)


def gather_all(args) -> list[dict]:
    """Overview = every lens, each isolated. A single lens raising (e.g. the
    workflow lens fail-loud when data/skill-chains.yaml is absent on a recipient)
    must NOT blank the other six — it degrades to a VISIBLE error entry the
    renderer surfaces (never a silent drop). The per-lens gather() keeps raising
    at the function level (loud for unit tests); isolation lives only here."""
    out: list[dict] = []
    for n in OVERVIEW_ORDER:
        if n not in LENSES:
            continue
        try:
            out.append(gather_lens(n, args))
        except Exception as e:  # noqa: BLE001 — one lens must not kill the overview
            out.append({"lens": n, "error": f"{type(e).__name__}: {e}"})
    return out


def _render(data, fmt: str, args) -> str:
    if fmt == "json":
        return json_output(data)
    # md / ascii / mermaid / overview are provided by telemetry_render (Phase 5);
    # imported lazily so the spine works even before that module exists.
    import telemetry_render  # noqa: E402
    aggregates = data if isinstance(data, list) else [data]
    if fmt == "ascii":
        return telemetry_render.render_ascii(aggregates, lang=args.lang)
    if fmt == "mermaid":
        return telemetry_render.render_mermaid(aggregates, lang=args.lang)
    return telemetry_render.render_md(aggregates, top=args.top, lang=args.lang)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Telemetry usage & health lenses")
    ap.add_argument("--lens", default="all",
                    help="usage|session|health|all (more lenses land in later phases)")
    ap.add_argument("--overview", action="store_true", help="compose all lenses (== --lens all)")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, help="limit usage table to top N skills (md format only)")
    ap.add_argument("--no-tokens", action="store_true", help="skip token attribution (faster)")
    ap.add_argument("--session", help="forensics: parse one session by id")
    ap.add_argument("--all-sessions", action="store_true", help="forensics: across all sessions")
    ap.add_argument("--format", choices=["md", "json", "ascii", "mermaid"], default="md")
    ap.add_argument("--lang", choices=["vi", "en"], default="vi",
                    help="language for fixed scaffolding labels (vi default; LLM narrates prose in this language)")
    ap.add_argument("--export-summary", metavar="PATH", default=None,
                    help="write the markdown aggregate to PATH (default: .claude/telemetry/usage-summary.md)")
    ap.add_argument("--auto-suggest", action="store_true",
                    help="(opt-in) append harvester suggestions after the normal render")
    args = ap.parse_args(argv)

    if args.overview or args.lens == "all":
        data = gather_all(args)
    elif args.lens in LENSES:
        data = gather_lens(args.lens, args)
    else:
        print(f"unknown lens: {args.lens!r}; known: {', '.join(LENSES)} | all", file=sys.stderr)
        return 2

    rendered = _render(data, args.format, args)
    print(rendered)

    # --export-summary: write the aggregate markdown to disk (empty telemetry → valid empty md).
    if args.export_summary is not None or args.auto_suggest:
        export_path = args.export_summary
        if export_path is None:
            # default path when only --auto-suggest was given without --export-summary
            from pathlib import Path as _Path
            export_path = str(_Path(sys.argv[0]).resolve().parent.parent.parent / "telemetry" / "usage-summary.md")
        _write_export_summary(rendered, export_path, args)

    return 0


def _write_export_summary(rendered: str, path: str, args) -> None:
    """Write the rendered markdown (+ optional harvester suggestions) to *path*."""
    from pathlib import Path as _Path
    out = _Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    content = rendered
    if args.auto_suggest:
        content = content + "\n\n" + _harvester_section(args)
    out.write_text(content, encoding="utf-8")


def _harvester_section(args) -> str:
    """Invoke harvester and render its suggestions as a markdown section."""
    try:
        import harvester  # noqa: E402 — sibling module, imported lazily
        result = harvester.harvest_suggestions(days=getattr(args, "days", 30))
        suggestions = result.get("suggestions", [])
    except Exception as exc:  # noqa: BLE001 — harvester must never crash the CLI
        return f"## Suggestions\n\n_Harvester error: {exc}_\n"

    lang = getattr(args, "lang", "vi")
    import telemetry_render  # noqa: E402
    heading = telemetry_render._t(lang, "suggest_h")
    if not suggestions:
        none_label = telemetry_render._t(lang, "suggest_none")
        return f"{heading}\n\n{none_label}\n"

    lines = [heading, ""]
    for s in suggestions:
        lines.append(
            f"- **{s.get('artifact', '?')}** ({s.get('category', '?')}, "
            f"count={s.get('count', 0)}): {s.get('why', '')}"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
