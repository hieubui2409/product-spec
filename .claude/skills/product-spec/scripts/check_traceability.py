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
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from encoding_utils import configure_utf8_console
from spec_graph import (
    build_graph, _now, CHILD_TYPE_FOR_PARENT, matching_child_counts,
    make_finding as _f,
)

configure_utf8_console()


def check(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    node_ids: Set[str] = {n["id"] for n in graph["nodes"]}
    # Shared expected-child counts (one pass over the edges); the gap views key
    # off the same helper so views and validator never disagree on a gap.
    child_counts = matching_child_counts(graph)

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
            if child_counts.get(n["id"], 0) == 0:
                check_id = "orphan_brd_goal" if ntype == "goal" else "unaddressed_parent"
                findings.append(_f(check_id, "warn", n, f"{n['id']} has no {expected_child} addressing it (gap-analysis input).", expected_child=expected_child))

    findings.extend(_check_dep_dangling(graph, node_ids))
    findings.extend(_check_dep_cycles(graph))

    for parse_err in graph.get("parse_errors", []):
        findings.append({
            "check": "parse_error",
            "severity": "error",
            "artifact_id": None,
            "file": parse_err["file"],
            "detail": parse_err["error"],
        })
    return findings


# ── depends_on graph family (lives here beside dangling_link) ────────────────
#
# The `depends_on: [ID]` edge joins the dangling family already owned by this
# module: an unresolved target is `dep_dangling` (error, beside dangling_link),
# and a circular chain is `dep_cycle` (error). Keeping the whole graph-walk
# dependency family in one home means a hierarchy/edge change edits one file.


def _build_dep_adj(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    """node id -> sorted list of its depends_on targets, for every node that
    declares the edge. Sorted at the graph layer (spec_graph stores it sorted),
    so the cycle walk's iteration order — and thus its output — is deterministic
    (G-A4). Targets that do not resolve to a real node are still included here:
    `dep_dangling` owns the missing-ID report; the cycle walk simply skips any
    target that is not itself a key (it cannot be on a cycle)."""
    adj: Dict[str, List[str]] = {}
    for n in graph["nodes"]:
        adj[n["id"]] = list(n.get("depends_on") or [])
    return adj


def find_dep_cycles(adj: Dict[str, List[str]]) -> List[List[str]]:
    """Return every dependency cycle in `adj` as a closed path.

    Iterative 3-color DFS (white/gray/black) over an explicit stack — NOT
    recursion — so a ~2000-deep linear chain cannot raise RecursionError
    (design-report F4 / goal G-D3). Sorted iteration makes the output
    deterministic. A back-edge to a GRAY node yields the cycle path including
    the repeated closing node, e.g. ``["A", "B", "A"]``. A target absent from
    `adj` (a dangling depends_on) is skipped — it can never be on a cycle, and
    `dep_dangling` owns the missing-ID report."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {}
    cycles: List[List[str]] = []
    for root in sorted(adj):
        if color.get(root, WHITE) != WHITE:
            continue
        color[root] = GRAY
        path = [root]
        stack = [(root, iter(sorted(adj.get(root, []))))]
        while stack:
            node, it = stack[-1]
            advanced = False
            for nbr in it:
                if nbr not in adj:        # dangling target → dep_dangling owns it
                    continue
                c = color.get(nbr, WHITE)
                if c == GRAY:             # back-edge → cycle
                    cycles.append(path[path.index(nbr):] + [nbr])
                elif c == WHITE:
                    color[nbr] = GRAY
                    path.append(nbr)
                    stack.append((nbr, iter(sorted(adj.get(nbr, [])))))
                    advanced = True
                    break
            if not advanced:             # node exhausted → backtrack
                color[node] = BLACK
                path.pop()
                stack.pop()
    return cycles


def _check_dep_dangling(graph: Dict[str, Any], node_ids: Set[str]) -> List[Dict[str, Any]]:
    """Flag any `depends_on` target that does not resolve to a real artifact.

    Same dangling family as `dangling_link` (parent edges) — a depends_on edge
    pointing at a ghost ID is `dep_dangling` (error). Independent of the type
    guard (check_consistency) — even a wrongly-placed depends_on is still
    checked for resolvability here."""
    findings: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        for dep in n.get("depends_on") or []:
            if dep not in node_ids:
                findings.append(_f(
                    "dep_dangling", "error", n,
                    f"{n['id']} depends_on unknown artifact {dep}.",
                    ref=dep,
                ))
    return findings


def _check_dep_cycles(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Emit one `dep_cycle` error per detected cycle; `context.cycle` carries the
    closed path. Anchored on the first node of the cycle path so the finding has
    a concrete `artifact_id`/`file`."""
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for cycle in find_dep_cycles(_build_dep_adj(graph)):
        anchor = nodes_by_id.get(cycle[0], {"id": cycle[0]})
        findings.append(_f(
            "dep_cycle", "error", anchor,
            f"Circular depends_on chain: {' → '.join(cycle)}.",
            cycle=cycle,
        ))
    return findings


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
        "checked_at": _now(),
        "findings": findings,
        "graph": graph,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
