#!/usr/bin/env python3
"""
check_traceability — structural traceability checks. No judgment.

Detects:
- orphan_story / orphan_epic / orphan_prd  (referenced parent does not exist)
- dangling_link                            (any frontmatter ID reference unresolved)
- unaddressed_parent                       (a parent with zero inbound child edges)
- orphan_brd_goal                          (BRD goal with no PRD addressing it)

Emits findings JSON per validation-rules-spec.md. Always exits 0.

CLI:
    check_traceability.py --root <project-dir>
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from encoding_utils import configure_utf8_console
from spec_graph import build_graph

configure_utf8_console()


CHILD_TYPE_FOR_PARENT = {
    "goal": "prd",
    "prd": "epic",
    "epic": "story",
}


def check(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    node_ids: Set[str] = {n["id"] for n in graph["nodes"]}
    inbound_by_target: Dict[str, List[Dict[str, str]]] = {}
    for e in graph["edges"]:
        inbound_by_target.setdefault(e["to"], []).append(e)

    for n in graph["nodes"]:
        ntype = n["type"]
        if ntype == "story":
            if not n.get("epic"):
                findings.append(_f("orphan_story", "error", n, "Story has no epic reference."))
            elif n["epic"] not in node_ids:
                findings.append(_f("dangling_link", "error", n, f"Story references unknown epic {n['epic']}.", ref=n["epic"]))
        elif ntype == "epic":
            if not n.get("prd"):
                findings.append(_f("orphan_epic", "error", n, "Epic has no PRD reference."))
            elif n["prd"] not in node_ids:
                findings.append(_f("dangling_link", "error", n, f"Epic references unknown PRD {n['prd']}.", ref=n["prd"]))
        elif ntype == "prd":
            brd_goals = n.get("brd_goals")
            if not brd_goals:
                findings.append(_f("orphan_prd", "error", n, "PRD has no BRD goals declared."))
            elif not isinstance(brd_goals, list):
                # A bare string (hand-edit regression) would iterate per character,
                # producing phantom "unknown BRD goal B/R/D/-/G/1" findings.
                # Emit one invalid_type finding and skip iteration.
                findings.append(_f(
                    "invalid_type", "error", n,
                    f"Field brd_goals={brd_goals!r} must be a YAML list; got {type(brd_goals).__name__}.",
                    field="brd_goals", value=brd_goals,
                ))
            else:
                for g in brd_goals:
                    if g not in node_ids:
                        findings.append(_f("dangling_link", "error", n, f"PRD references unknown BRD goal {g}.", ref=g))

        if ntype in CHILD_TYPE_FOR_PARENT:
            expected_child = CHILD_TYPE_FOR_PARENT[ntype]
            edges_in = inbound_by_target.get(n["id"], [])
            child_count = sum(1 for e in edges_in if _from_node_type(graph, e["from"]) == expected_child)
            if child_count == 0:
                check_id = "orphan_brd_goal" if ntype == "goal" else "unaddressed_parent"
                findings.append(_f(check_id, "warn", n, f"{n['id']} has no {expected_child} addressing it (gap-analysis input).", expected_child=expected_child))

    for parse_err in graph.get("parse_errors", []):
        findings.append({
            "check": "parse_error",
            "severity": "error",
            "artifact_id": None,
            "file": parse_err["file"],
            "detail": parse_err["error"],
        })
    return findings


def _from_node_type(graph: Dict[str, Any], node_id: str) -> str:
    for n in graph["nodes"]:
        if n["id"] == node_id:
            return n["type"] or ""
    return ""


def _f(check_id: str, severity: str, node: Dict[str, Any], detail: str, **context) -> Dict[str, Any]:
    return {
        "check": check_id,
        "severity": severity,
        "artifact_id": node.get("id"),
        "file": node.get("file"),
        "detail": detail,
        "context": context or None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)
    findings = check(graph)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "checked_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
        "findings": findings,
        "graph": graph,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
