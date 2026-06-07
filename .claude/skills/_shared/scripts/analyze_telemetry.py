#!/usr/bin/env python3
"""
analyze_telemetry.py — CLI front for the usage-&-health lenses. Deterministic
gather + render; the LLM (cleanmatic:telemetry skill) narrates the output. It
NEVER judges — it surfaces counts/rates/spans for the skill to adjudicate.
READ-ONLY. CM-local dev tooling (NOT shipped in the pack bundle).

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
_LIB = _SCRIPT_DIR.parent / "lib"
sys.path.insert(0, str(_LIB))

from formatters import json_output  # noqa: E402
import lens_usage_tokens  # noqa: E402
import lens_session_shape  # noqa: E402
import lens_health  # noqa: E402
import lens_forensics  # noqa: E402
import lens_memory_health  # noqa: E402
import lens_workflow_chains  # noqa: E402
import lens_reliability  # noqa: E402
import lens_validate_proxy  # noqa: E402

# name → gather callable taking the parsed args, returning a render-agnostic dict.
LENSES: dict[str, callable] = {
    "usage": lambda a: lens_usage_tokens.gather(days=a.days, with_tokens=not a.no_tokens),
    "session": lambda a: lens_session_shape.gather(),
    "health": lambda a: lens_health.gather(),
    "forensics": lambda a: lens_forensics.gather(session=a.session, all_sessions=a.all_sessions),
    "memory": lambda a: lens_memory_health.gather(),
    "workflow": lambda a: lens_workflow_chains.gather(days=a.days, top=(a.top or 10)),
    "reliability": lambda a: lens_reliability.gather(days=a.days),
    "validate": lambda a: lens_validate_proxy.gather(days=a.days),
}

# The order lenses appear in --lens all / --overview.
OVERVIEW_ORDER = ["usage", "session", "health", "reliability", "workflow", "validate", "memory"]


def gather_lens(name: str, args) -> dict:
    return LENSES[name](args)


def gather_all(args) -> list[dict]:
    return [gather_lens(n, args) for n in OVERVIEW_ORDER if n in LENSES]


def _render(data, fmt: str, args) -> str:
    if fmt == "json":
        return json_output(data)
    # md / ascii / mermaid / overview are provided by telemetry_render (Phase 5);
    # imported lazily so the spine works even before that module exists.
    import telemetry_render  # noqa: E402
    aggregates = data if isinstance(data, list) else [data]
    if fmt == "ascii":
        return telemetry_render.render_ascii(aggregates)
    if fmt == "mermaid":
        return telemetry_render.render_mermaid(aggregates)
    return telemetry_render.render_md(aggregates, top=args.top)


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
    args = ap.parse_args(argv)

    if args.overview or args.lens == "all":
        data = gather_all(args)
    elif args.lens in LENSES:
        data = gather_lens(args.lens, args)
    else:
        print(f"unknown lens: {args.lens!r}; known: {', '.join(LENSES)} | all", file=sys.stderr)
        return 2

    print(_render(data, args.format, args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
