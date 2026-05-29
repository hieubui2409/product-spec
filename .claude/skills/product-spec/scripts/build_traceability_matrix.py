#!/usr/bin/env python3
"""
build_traceability_matrix — render the story -> epic -> PRD -> BRD-goal -> metric
matrix as a markdown table, from the graph JSON. Plus an artifact/ID/status index.

CLI:
    build_traceability_matrix.py --root <project-dir>
        Emits JSON {matrix_markdown, index, graph}. Always exits 0.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from encoding_utils import configure_utf8_console
from spec_graph import build_graph

configure_utf8_console()


def _cell(s: Any) -> str:
    # Markdown tables split cells on `|`, so any raw pipe inside a cell
    # bleeds into adjacent columns. Escape it as the standard `\|` so
    # GFM renders it visibly without breaking the table. Newlines collapse
    # to spaces for the same reason.
    text = "" if s is None else str(s)
    return text.replace("|", r"\|").replace("\n", " ").replace("\r", " ") or "—"


def build_matrix(graph: Dict[str, Any]) -> str:
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    stories = [n for n in graph["nodes"] if n.get("type") == "story"]
    rows: List[List[str]] = []
    for s in stories:
        epic = nodes_by_id.get(s.get("epic") or "")
        prd = nodes_by_id.get(epic.get("prd") if epic else "") if epic else None
        raw_brd_goals = prd.get("brd_goals", []) if prd else []
        # Guard against bare-string regressions: a hand-edited `brd_goals: BRD-G1`
        # iterates per character without this check, producing garbled cells.
        brd_goals = raw_brd_goals if isinstance(raw_brd_goals, list) else []
        metric_cell = ", ".join(s.get("metrics") or []) or "—"
        rows.append([
            _cell(s.get("id")),
            _cell(epic.get("id") if epic else None),
            _cell(prd.get("id") if prd else None),
            _cell(", ".join(brd_goals)) if brd_goals else "—",
            _cell(metric_cell),
            _cell(s.get("status")),
            _cell(s.get("scope")),
            _cell(s.get("moscow")),
        ])

    rows.sort()
    header = ["Story", "Epic", "PRD", "BRD Goals", "Metrics", "Status", "Scope", "MoSCoW"]
    sep = ["---"] * len(header)
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    if not rows:
        lines.append("| (no stories) |  |  |  |  |  |  |  |")
    return "\n".join(lines)


def build_index(graph: Dict[str, Any]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for n in graph["nodes"]:
        out.append({
            "id": n.get("id") or "—",
            "type": n.get("type") or "—",
            "status": n.get("status") or "—",
            "file": n.get("file") or "—",
        })
    out.sort(key=lambda x: (x["type"], x["id"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", action="store_true",
                    help="also write docs/product/visuals/traceability-matrix.md")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)
    matrix = build_matrix(graph)
    index = build_index(graph)

    out = {
        "schema_version": "1.0",
        "root": str(root),
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
        "matrix_markdown": matrix,
        "index": index,
        "graph": graph,
    }

    if args.write:
        target_dir = root / "docs" / "product" / "visuals"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "traceability-matrix.md"
        target.write_text(f"# Traceability Matrix\n\n_Generated {out['generated_at']}_\n\n{matrix}\n", encoding="utf-8")
        out["__written_to"] = str(target.relative_to(root))

    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
