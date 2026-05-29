#!/usr/bin/env python3
"""
visualize — dispatcher for the 9 visualization views in 3 formats
(ASCII / Mermaid / inline-vendored HTML).

Reads the graph JSON from spec_graph and routes the chosen view through the
matching renderer.

CLI:
    visualize.py --view <name> --format <ascii|mermaid|html> --root <dir>
                 [--lang en|vi] [--diff <snapshot.json>]

Views: tree | heatmap | scope | roadmap | persona | gap | moscow | risk | delta
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from encoding_utils import configure_utf8_console
from spec_graph import build_graph

import render_ascii
import render_mermaid
import render_html

configure_utf8_console()


VIEWS = ("tree", "heatmap", "scope", "roadmap", "persona", "gap", "moscow", "risk", "delta")
FORMATS = ("ascii", "mermaid", "html")


def _render_ascii(view: str, graph: Dict[str, Any], baseline: Optional[Dict[str, Any]], lang: str = "en", filter_wont: bool = False) -> str:
    if view == "delta":
        if not baseline:
            return "(no baseline yet — run --validate to create one)"
        return render_ascii.delta(graph, baseline)
    fn = getattr(render_ascii, view)
    # tree/roadmap accept (lang, filter_wont); persona accepts (filter_wont);
    # moscow accepts (lang) only (counts are inherent — filter doesn't apply).
    if view in ("tree", "roadmap"):
        return fn(graph, lang=lang, filter_wont=filter_wont)
    if view == "moscow":
        return fn(graph, lang=lang)
    if view == "persona":
        return fn(graph, filter_wont=filter_wont)
    return fn(graph)


def _render_mermaid(view: str, graph: Dict[str, Any], baseline: Optional[Dict[str, Any]], lang: str = "en", filter_wont: bool = False) -> str:
    if view == "delta":
        if not baseline:
            return "```\n(no baseline yet — run --validate to create one)\n```"
        return render_mermaid.delta(graph, baseline)
    fn = getattr(render_mermaid, view)
    if view in ("tree", "roadmap"):
        return fn(graph, lang=lang, filter_wont=filter_wont)
    if view == "moscow":
        return fn(graph, lang=lang)
    return fn(graph)


def _load_baseline(root: Path, override: Optional[str]) -> Optional[Dict[str, Any]]:
    snap_dir = root / "docs" / "product" / "visuals" / ".snapshots"

    def _read_snapshot(path: Path) -> Dict[str, Any]:
        # A corrupt snapshot file (truncated write, hand-edit, merge artefact)
        # would otherwise raise an uncaught JSONDecodeError and crash the
        # visualize pipeline. Surface a readable error and the offending
        # path so the PO can delete or repair it.
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"snapshot file is not valid JSON: {path} ({exc.msg} "
                f"at line {exc.lineno} col {exc.colno})"
            ) from exc

    if override:
        p = Path(override)
        if not p.is_absolute():
            p = snap_dir / override
        if not p.exists():
            # Originally returned None silently — the dispatcher then rendered
            # the generic "no baseline yet" message and a PO who typoed a
            # filename never learned why their --snapshot was ignored.
            available = sorted(snap_dir.glob("*.json")) if snap_dir.exists() else []
            available_names = [s.name for s in available]
            raise FileNotFoundError(
                f"--snapshot baseline not found: {p}. "
                f"Available snapshots in {snap_dir}: {available_names or '(none)'}"
            )
        return _read_snapshot(p)
    if not snap_dir.exists():
        return None
    # Order by mtime, not filename: snapshot names are <ts-to-second>-<hash>,
    # so same-second snapshots would otherwise sort by content hash (not time).
    snaps = sorted(snap_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not snaps:
        return None
    # With 1 snapshot, compare against the live graph (current). With 2+, use
    # the second-most-recent so the freshly-taken snapshot doesn't shadow the
    # change the PO is trying to see.
    target = snaps[-2] if len(snaps) >= 2 else snaps[-1]
    return _read_snapshot(target)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--view", required=True, choices=VIEWS)
    ap.add_argument("--format", default="ascii", choices=FORMATS)
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    ap.add_argument(
        "--snapshot", default=None,
        help="path or filename of a baseline snapshot in .snapshots/ "
             "(used by --view delta). Alias --diff is kept for one cycle "
             "for transitional compatibility.",
    )
    ap.add_argument("--diff", dest="snapshot", default=None, help=argparse.SUPPRESS)
    ap.add_argument(
        "--filter-wont", action="store_true",
        help="hide deferred items (moscow=wont or scope=out) from tree/roadmap/persona. "
             "Default keeps them visible with a `*` marker.",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)
    baseline = _load_baseline(root, args.snapshot) if args.view == "delta" else None

    if args.format == "ascii":
        body = _render_ascii(args.view, graph, baseline, lang=args.lang, filter_wont=args.filter_wont)
        print(body)
        return 0

    if args.format == "mermaid":
        body = _render_mermaid(args.view, graph, baseline, lang=args.lang, filter_wont=args.filter_wont)
        print(body)
        return 0

    # html
    mermaid_text = _render_mermaid(args.view, graph, baseline, lang=args.lang, filter_wont=args.filter_wont)
    # Mermaid renderers return either a ```mermaid fenced block (true Mermaid
    # DSL) or a plain ``` fenced block (ASCII fallback for views Mermaid can't
    # express: heatmap, persona, risk, no-baseline delta). Only the former
    # belongs in a <div class="mermaid"> wrapper; the latter must be HTML-
    # escaped inside a <pre> tag so the browser renders raw text and Mermaid
    # leaves it alone.
    if mermaid_text.startswith("```mermaid"):
        body_text = mermaid_text
        view_format = "mermaid"
    else:
        body_text = _render_ascii(args.view, graph, baseline, lang=args.lang, filter_wont=args.filter_wont)
        view_format = "pre"
    out = render_html.write(root, args.view, view_format, body_text, graph, lang=args.lang)
    print(json.dumps({"written": str(out.relative_to(root)) if out.is_relative_to(root) else str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
