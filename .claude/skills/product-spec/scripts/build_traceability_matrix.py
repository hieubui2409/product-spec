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


def build_matrix(graph: Dict[str, Any]) -> str:
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    stories = [n for n in graph["nodes"] if n.get("type") == "story"]
    rows: List[List[str]] = []
    for s in stories:
        epic = nodes_by_id.get(s.get("epic") or "")
        prd = nodes_by_id.get(epic.get("prd") if epic else "") if epic else None
        brd_goals = prd.get("brd_goals", []) if prd else []
        metric_cell = ", ".join(s.get("metrics") or []) or "—"
        rows.append([
            s.get("id") or "—",
            (epic.get("id") if epic else "—") or "—",
            (prd.get("id") if prd else "—") or "—",
            ", ".join(brd_goals) or "—",
            metric_cell,
            s.get("status") or "—",
            s.get("scope") or "—",
            s.get("moscow") or "—",
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

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
