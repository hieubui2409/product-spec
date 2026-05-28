#!/usr/bin/env python3
"""
render_ascii — deterministic ASCII renderers for the 9 visualization views.

All functions take the graph JSON (per visualization-spec.md) and return a
plain-text string. Zero dependencies; safe in any terminal.
"""

from collections import defaultdict
from typing import Any, Dict, List


def tree(graph: Dict[str, Any]) -> str:
    """Vision -> PRODUCT -> BRD -> goals -> PRDs -> epics -> stories."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    children = defaultdict(list)
    for e in graph["edges"]:
        children[e["to"]].append(e["from"])

    lines: List[str] = []
    name = (graph.get("product") or {}).get("name") or "(no PRODUCT.md)"
    lines.append(f"PRODUCT: {name}")

    goal_ids = sorted([nid for nid, n in nodes_by_id.items() if n["type"] == "goal"])
    for i, gid in enumerate(goal_ids):
        last_g = i == len(goal_ids) - 1
        lines.append(f"{'└── ' if last_g else '├── '}{gid} — {nodes_by_id[gid].get('title') or ''}")
        prefix_g = "    " if last_g else "│   "
        prds = sorted(children.get(gid, []))
        for j, pid in enumerate(prds):
            last_p = j == len(prds) - 1
            lines.append(f"{prefix_g}{'└── ' if last_p else '├── '}{pid}")
            prefix_p = prefix_g + ("    " if last_p else "│   ")
            epics = sorted(children.get(pid, []))
            for k, eid in enumerate(epics):
                last_e = k == len(epics) - 1
                lines.append(f"{prefix_p}{'└── ' if last_e else '├── '}{eid}")
                prefix_e = prefix_p + ("    " if last_e else "│   ")
                stories = sorted(children.get(eid, []))
                for m, sid in enumerate(stories):
                    last_s = m == len(stories) - 1
                    lines.append(f"{prefix_e}{'└── ' if last_s else '├── '}{sid}")
    return "\n".join(lines)


def heatmap(graph: Dict[str, Any]) -> str:
    """status grid: rows=type, cols=status."""
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for n in graph["nodes"]:
        t = n["type"] or "?"
        s = n.get("status") or "?"
        counts[t][s] += 1
    types = sorted(counts.keys())
    statuses = ["draft", "review", "approved"]
    header = "| Type    | " + " | ".join(f"{s:8}" for s in statuses) + " |"
    sep = "|" + "-" * (len(header) - 2) + "|"
    lines = [header, sep]
    for t in types:
        row = f"| {t:7} | " + " | ".join(f"{counts[t].get(s, 0):>8}" for s in statuses) + " |"
        lines.append(row)
    return "\n".join(lines)


def scope(graph: Dict[str, Any]) -> str:
    """scope tag x MoSCoW grid."""
    cells: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for n in graph["nodes"]:
        sc = n.get("scope") or "?"
        ms = n.get("moscow") or "?"
        cells[sc][ms] += 1
    rows = ["in", "core-value", "out"]
    cols = ["must", "should", "could", "wont"]
    header = "| Scope        | " + " | ".join(f"{c:7}" for c in cols) + " |"
    lines = [header, "|" + "-" * (len(header) - 2) + "|"]
    for r in rows:
        lines.append(f"| {r:12} | " + " | ".join(f"{cells[r].get(c, 0):>7}" for c in cols) + " |")
    return "\n".join(lines)


def roadmap(graph: Dict[str, Any]) -> str:
    """now / next / later groupings."""
    groups: Dict[str, List[str]] = defaultdict(list)
    for n in graph["nodes"]:
        if n["type"] not in ("prd", "epic", "story"):
            continue
        h = n.get("horizon") or "unspecified"
        groups[h].append(n["id"])

    sections = []
    for h in ("now", "next", "later", "unspecified"):
        items = sorted(groups.get(h, []))
        if not items and h == "unspecified":
            continue
        sections.append(f"## {h.upper()}")
        if not items:
            sections.append("  (empty)")
        else:
            for it in items:
                sections.append(f"  - {it}")
    return "\n".join(sections) or "(no PRDs/epics/stories yet)"


def persona(graph: Dict[str, Any]) -> str:
    """persona x feature(PRD/epic) coverage (story count)."""
    personas = sorted(set((graph.get("product") or {}).get("personas") or []))
    if not personas:
        for n in graph["nodes"]:
            for p in n.get("personas", []) or []:
                if p not in personas:
                    personas.append(p)
        personas = sorted(set(personas))

    prds = sorted([n["id"] for n in graph["nodes"] if n["type"] == "prd"])
    cells: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    epic_to_prd = {n["id"]: n.get("prd") for n in graph["nodes"] if n["type"] == "epic"}
    for n in graph["nodes"]:
        if n["type"] != "story":
            continue
        prd_id = epic_to_prd.get(n.get("epic"))
        for p in n.get("personas", []) or []:
            if prd_id:
                cells[p][prd_id] += 1
    if not personas:
        return "(no personas yet)"
    header = "| Persona      | " + " | ".join(f"{p:10}" for p in prds) + " |"
    lines = [header, "|" + "-" * (len(header) - 2) + "|"]
    for p in personas:
        lines.append(f"| {p:12} | " + " | ".join(f"{cells[p].get(prd, 0):>10}" for prd in prds) + " |")
    return "\n".join(lines)


def gap(graph: Dict[str, Any]) -> str:
    """Bullet list of unaddressed nodes (gap-analysis input — structural only)."""
    children = defaultdict(int)
    for e in graph["edges"]:
        children[e["to"]] += 1
    expected = {"goal": "PRD", "prd": "epic", "epic": "story"}
    out: List[str] = []
    for n in graph["nodes"]:
        kind = n["type"]
        if kind in expected and children[n["id"]] == 0:
            out.append(f"  - {n['id']} ({kind}) has no {expected[kind]} addressing it")
    return "\n".join(out) or "(no structural gaps)"


def moscow(graph: Dict[str, Any]) -> str:
    """MoSCoW quadrant counts among stories."""
    counts: Dict[str, int] = defaultdict(int)
    for n in graph["nodes"]:
        if n["type"] != "story":
            continue
        counts[n.get("moscow") or "?"] += 1
    rows = [
        f"| Must:   {counts.get('must', 0):>4} | Should: {counts.get('should', 0):>4} |",
        f"| Could:  {counts.get('could', 0):>4} | Won't:  {counts.get('wont', 0):>4} |",
    ]
    return "\n".join(rows)


def risk(graph: Dict[str, Any]) -> str:
    """3x3 risk matrix: impact x likelihood."""
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in graph.get("risks", []):
        counts[r.get("impact", "?")][r.get("likelihood", "?")] += 1
    rows = ["high", "med", "low"]
    cols = ["low", "med", "high"]
    header = "| Impact \\ Lik | " + " | ".join(f"{c:4}" for c in cols) + " |"
    lines = [header, "|" + "-" * (len(header) - 2) + "|"]
    for r in rows:
        lines.append(f"| {r:12} | " + " | ".join(f"{counts[r].get(c, 0):>4}" for c in cols) + " |")
    return "\n".join(lines)


def delta(current: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    """Unified-diff-style: added / removed / changed nodes between two graphs."""
    cur_ids = {n["id"]: n for n in current.get("nodes", [])}
    base_ids = {n["id"]: n for n in baseline.get("nodes", [])}
    added = sorted(set(cur_ids) - set(base_ids))
    removed = sorted(set(base_ids) - set(cur_ids))
    changed: List[str] = []
    for nid in sorted(set(cur_ids) & set(base_ids)):
        for field in ("status", "scope", "moscow", "horizon", "size"):
            if cur_ids[nid].get(field) != base_ids[nid].get(field):
                changed.append(f"  ~ {nid}.{field}: {base_ids[nid].get(field)} -> {cur_ids[nid].get(field)}")
    lines: List[str] = []
    for a in added:
        lines.append(f"  + {a}")
    for r in removed:
        lines.append(f"  - {r}")
    lines.extend(changed)
    return "\n".join(lines) or "(no changes)"
