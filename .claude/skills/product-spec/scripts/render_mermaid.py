#!/usr/bin/env python3
"""
render_mermaid — emit Mermaid v11 blocks for the 9 visualization views.

Each function returns a string containing a fenced ```mermaid block ready
to paste into markdown. Where a view cannot be expressed cleanly in Mermaid,
the renderer falls back to a `pre`-block with the ASCII version.
"""

from collections import defaultdict
from typing import Any, Dict, List

from render_ascii import (
    tree as ascii_tree,
    heatmap as ascii_heatmap,
    persona as ascii_persona,
    risk as ascii_risk,
)


def _fence(body: str) -> str:
    return f"```mermaid\n{body}\n```"


def _safe_label(s: str) -> str:
    return (s or "").replace('"', "'").replace("\n", " ")


def tree(graph: Dict[str, Any]) -> str:
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    lines = ["flowchart TB"]
    name = _safe_label((graph.get("product") or {}).get("name") or "PRODUCT")
    lines.append(f'  PRODUCT["{name}"]')
    for n in graph["nodes"]:
        label = _safe_label(f"{n['id']}\\n{n.get('title') or ''}")
        lines.append(f'  {_safe_id(n["id"])}["{label}"]')
    for e in graph["edges"]:
        lines.append(f"  {_safe_id(e['from'])} --> {_safe_id(e['to'])}")
    goal_ids = [nid for nid, n in nodes_by_id.items() if n["type"] == "goal"]
    for gid in goal_ids:
        lines.append(f"  {_safe_id(gid)} --> PRODUCT")
    return _fence("\n".join(lines))


def _safe_id(s: str) -> str:
    return s.replace("-", "_").replace(":", "_")


def heatmap(graph: Dict[str, Any]) -> str:
    # Mermaid lacks a true heatmap; fall back to a pre block with ASCII.
    return f"<pre>\n{ascii_heatmap(graph)}\n</pre>"


def scope(graph: Dict[str, Any]) -> str:
    # quadrantChart: x = moscow (must..wont), y = scope (out..core-value)
    must = sum(1 for n in graph["nodes"] if n.get("moscow") == "must")
    should = sum(1 for n in graph["nodes"] if n.get("moscow") == "should")
    could = sum(1 for n in graph["nodes"] if n.get("moscow") == "could")
    wont = sum(1 for n in graph["nodes"] if n.get("moscow") == "wont")
    body = f"""quadrantChart
  title Scope x MoSCoW
  x-axis Won't --> Must
  y-axis Out --> Core-Value
  quadrant-1 Must / Core
  quadrant-2 Won't / Core
  quadrant-3 Won't / Out
  quadrant-4 Must / Out
  Must-stories: [0.85, 0.5]
  Should-stories: [0.65, 0.5]
  Could-stories: [0.35, 0.5]
  Won't-stories: [0.15, 0.5]"""
    counts = f"\n%% counts — must:{must} should:{should} could:{could} wont:{wont}"
    return _fence(body + counts)


def roadmap(graph: Dict[str, Any]) -> str:
    items_by_horizon: Dict[str, List[str]] = defaultdict(list)
    for n in graph["nodes"]:
        if n["type"] not in ("prd", "epic", "story"):
            continue
        items_by_horizon[n.get("horizon") or "unspecified"].append(n["id"])
    lines = ["timeline", "  title Roadmap"]
    for h in ("now", "next", "later", "unspecified"):
        items = sorted(items_by_horizon.get(h, []))
        if not items and h == "unspecified":
            continue
        lines.append(f"  section {h.title()}")
        for it in items[:8]:
            lines.append(f"    {it} : {h}")
    return _fence("\n".join(lines))


def persona(graph: Dict[str, Any]) -> str:
    return f"<pre>\n{ascii_persona(graph)}\n</pre>"


def gap(graph: Dict[str, Any]) -> str:
    children = defaultdict(int)
    for e in graph["edges"]:
        children[e["to"]] += 1
    expected = {"goal": "PRD", "prd": "epic", "epic": "story"}
    lines = ["flowchart LR", "  classDef gap fill:#fce4e4,stroke:#cc0000"]
    for n in graph["nodes"]:
        if n["type"] in expected and children[n["id"]] == 0:
            sid = _safe_id(n["id"])
            lines.append(f'  {sid}["{n["id"]}\\n(missing {expected[n["type"]]})"]:::gap')
    if len(lines) == 2:
        lines.append('  OK["(no structural gaps)"]')
    return _fence("\n".join(lines))


def moscow(graph: Dict[str, Any]) -> str:
    counts = defaultdict(int)
    for n in graph["nodes"]:
        if n["type"] != "story":
            continue
        counts[n.get("moscow") or "?"] += 1
    body = f"""quadrantChart
  title Stories — MoSCoW
  x-axis Won't --> Must
  y-axis Could --> Should
  quadrant-1 Must
  quadrant-2 Should
  quadrant-3 Could
  quadrant-4 Won't
  Stories: [0.5, 0.5]
%% counts: must={counts.get('must',0)} should={counts.get('should',0)} could={counts.get('could',0)} wont={counts.get('wont',0)}"""
    return _fence(body)


def risk(graph: Dict[str, Any]) -> str:
    return f"<pre>\n{ascii_risk(graph)}\n</pre>"


def delta(current: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    cur_ids = {n["id"]: n for n in current.get("nodes", [])}
    base_ids = {n["id"]: n for n in baseline.get("nodes", [])}
    added = sorted(set(cur_ids) - set(base_ids))
    removed = sorted(set(base_ids) - set(cur_ids))
    lines = ["flowchart TB", "  classDef added fill:#dcedc1", "  classDef removed fill:#ffd1d1"]
    for a in added:
        lines.append(f'  {_safe_id(a)}["+ {a}"]:::added')
    for r in removed:
        lines.append(f'  {_safe_id(r)}["- {r}"]:::removed')
    if len(lines) == 3:
        lines.append('  OK["(no changes)"]')
    return _fence("\n".join(lines))
