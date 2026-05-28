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


def _render_ascii(view: str, graph: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> str:
    if view == "delta":
        if not baseline:
            return "(no baseline yet — run --validate to create one)"
        return render_ascii.delta(graph, baseline)
    return getattr(render_ascii, view)(graph)


def _render_mermaid(view: str, graph: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> str:
    if view == "delta":
        if not baseline:
            return "<pre>(no baseline yet — run --validate to create one)</pre>"
        return render_mermaid.delta(graph, baseline)
    return getattr(render_mermaid, view)(graph)


def _load_baseline(root: Path, override: Optional[str]) -> Optional[Dict[str, Any]]:
    snap_dir = root / "docs" / "product" / "visuals" / ".snapshots"
    if override:
        p = Path(override)
        if not p.is_absolute():
            p = snap_dir / override
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    if not snap_dir.exists():
        return None
    snaps = sorted(snap_dir.glob("*.json"))
    if len(snaps) < 2:
        return None
    return json.loads(snaps[-2].read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--view", required=True, choices=VIEWS)
    ap.add_argument("--format", default="ascii", choices=FORMATS)
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    ap.add_argument("--diff", default=None, help="path or filename of a baseline snapshot in .snapshots/")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)
    baseline = _load_baseline(root, args.diff) if args.view == "delta" else None

    if args.format == "ascii":
        body = _render_ascii(args.view, graph, baseline)
        print(body)
        return 0

    if args.format == "mermaid":
        body = _render_mermaid(args.view, graph, baseline)
        print(body)
        return 0

    # html
    mermaid_text = _render_mermaid(args.view, graph, baseline)
    out = render_html.write(root, args.view, "mermaid", mermaid_text, graph, lang=args.lang)
    print(json.dumps({"written": str(out.relative_to(root)) if out.is_relative_to(root) else str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
