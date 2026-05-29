#!/usr/bin/env python3
"""
assemble_digest — deterministic, script-owned core shared by F1 export and the
F2 board/explorer viewers. Turns (selection + layer-filter + depth) into an
ordered digest model. No HTML, no LLM, no I/O beyond the parsed artifacts.

Digest element: {id, type, role, verbosity, title, frontmatter, body, ac} where
role = ancestor|target|descendant|warning, verbosity = full|struct, type =
vision|brd|goal|prd|epic|story|_warning. Emitted as a canonical SORTED list
(hierarchy rank, then ID) — downstream()/ancestors() return sets, so we sort
before emit for determinism (independent of nodes[]/set iteration order).

Vision and the BRD container are NOT graph nodes (build_nodes nodifies goals,
not the BRD; vision is isolated). ancestors()/downstream() can't reach them, so
the assembler loads them from the parsed artifacts and PREPENDS them as
`role=ancestor` singletons — a documented step, separate from the edge walk.
"""

import re
from typing import Any, Dict, List, Optional, Set

from spec_graph import ancestors, downstream


# Each artifact type belongs to one --layers bucket. Goals live in the BRD, so
# they share the `brd` layer; vision/prd/epic/story map to their own names.
LAYER_FOR_TYPE = {
    "vision": "vision",
    "brd": "brd",
    "goal": "brd",
    "prd": "prd",
    "epic": "epic",
    "story": "story",
}
ALL_LAYERS = ("vision", "brd", "prd", "epic", "story")

# Hierarchy rank for the canonical sort. `_warning` sorts to the very front so
# provenance notes lead the doc; the rest follow top-down.
TYPE_RANK = {"_warning": -1, "vision": 0, "brd": 1, "goal": 2, "prd": 3, "epic": 4, "story": 5}

# Per-type verbosity at --depth context: ancestors/singletons are compacted,
# the target and its descendants render in full.
_CONTEXT_FULL_ROLES = ("target", "descendant")


def _index_artifacts(artifacts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map artifact id -> parsed artifact, for top-level files (vision/brd/prd/
    epic/story). Goals are inside brd.md and are not indexed here."""
    out: Dict[str, Dict[str, Any]] = {}
    for a in artifacts:
        if not a.get("ok"):
            continue
        fm = a.get("frontmatter") or {}
        aid = fm.get("id")
        if aid:
            out[str(aid)] = a
    return out


def _find_by_type(artifacts: List[Dict[str, Any]], art_type: str) -> Optional[Dict[str, Any]]:
    for a in artifacts:
        if not a.get("ok"):
            continue
        fm = a.get("frontmatter") or {}
        if fm.get("type") == art_type or a.get("__type_hint") == art_type:
            return a
    return None


def _resolve_targets(select: str, graph: Dict[str, Any]) -> Set[str]:
    """Resolve `all` | single ID | comma-list into a set of graph node IDs
    (goals/PRDs/epics/stories only — vision/BRD are singletons)."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    if select == "all":
        return {n["id"] for n in graph["nodes"] if n["type"] in ("goal", "prd", "epic", "story")}
    wanted = [s.strip() for s in select.split(",") if s.strip()]
    return {w for w in wanted if w in nodes_by_id}


def _verbosity(role: str, depth: str) -> str:
    if depth == "full":
        return "full"
    if depth == "brief":
        return "struct"
    return "full" if role in _CONTEXT_FULL_ROLES else "struct"


def _entry(node: Dict[str, Any], role: str, verbosity: str, artifact: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    fm = (artifact or {}).get("frontmatter") or {}
    body = (artifact or {}).get("body") or ""
    # Goals carry no narrative body and no AC; their frontmatter is the goal dict.
    ac = fm.get("acceptance_criteria") if node["type"] == "story" else None
    return {
        "id": node["id"],
        "type": node["type"],
        "role": role,
        "verbosity": verbosity,
        "title": node.get("title") or fm.get("name") or fm.get("title") or "",
        "frontmatter": fm or {k: v for k, v in node.items() if k not in ("id", "type")},
        "body": body,
        "ac": ac if isinstance(ac, list) else None,
    }


def _first_h1(body: str) -> str:
    """First level-1 markdown heading in the body, used as a singleton title
    when vision.md/brd.md carry no frontmatter name/title."""
    m = re.search(r"^#\s+(.+?)\s*$", body or "", re.MULTILINE)
    return m.group(1).strip() if m else ""


def _singleton_entry(artifact: Dict[str, Any], art_type: str, depth: str) -> Dict[str, Any]:
    fm = artifact.get("frontmatter") or {}
    body = artifact.get("body") or ""
    return {
        "id": str(fm.get("id") or art_type.upper()),
        "type": art_type,
        "role": "ancestor",
        "verbosity": _verbosity("ancestor", depth),
        "title": fm.get("name") or fm.get("title") or _first_h1(body) or art_type.upper(),
        "frontmatter": fm,
        "body": body,
        "ac": None,
    }


def build_digest(
    graph: Dict[str, Any],
    artifacts: List[Dict[str, Any]],
    select: str = "all",
    layers: Optional[List[str]] = None,
    depth: str = "context",
) -> List[Dict[str, Any]]:
    """Build the ordered digest model. See module docstring for the contract."""
    layer_set = set(layers) if layers else set(ALL_LAYERS)
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    art_by_id = _index_artifacts(artifacts)

    targets = _resolve_targets(select, graph)
    ctx_ids: Set[str] = set()
    desc_ids: Set[str] = set()
    for t in targets:
        ctx_ids |= ancestors(graph, t)
        desc_ids |= downstream(graph, t)
    ctx_ids -= targets
    desc_ids -= targets
    desc_ids -= ctx_ids

    entries: List[Dict[str, Any]] = []

    def _add(ids: Set[str], role: str) -> None:
        for nid in ids:
            node = nodes_by_id.get(nid)
            if node is None:
                continue
            entries.append(_entry(node, role, _verbosity(role, depth), art_by_id.get(nid)))

    _add(targets, "target")
    _add(ctx_ids, "ancestor")
    _add(desc_ids, "descendant")

    # Vision + BRD context = singletons. Prepend them whenever their layer is
    # included AND the selection actually contains spec content below them
    # (goals/PRDs/epics/stories) — i.e. there is something to contextualize.
    has_spec_content = bool(targets | ctx_ids | desc_ids)
    if has_spec_content:
        vision_art = _find_by_type(artifacts, "vision")
        if vision_art and "vision" in layer_set:
            entries.append(_singleton_entry(vision_art, "vision", depth))
        brd_art = _find_by_type(artifacts, "brd")
        if brd_art and "brd" in layer_set:
            entries.append(_singleton_entry(brd_art, "brd", depth))

    # --layers precedence (owner-locked, D2): an excluded type is dropped even
    # if it is the selected root's own type. When that happens, emit a
    # provenance warning so the read-once doc is not silently context-less.
    warnings: List[Dict[str, Any]] = []
    for tid in sorted(t for t in targets if LAYER_FOR_TYPE.get(nodes_by_id[t]["type"]) not in layer_set):
        ntype = nodes_by_id[tid]["type"]
        warnings.append({
            "id": tid, "type": "_warning", "role": "warning", "verbosity": "struct",
            "title": "layers-excluded-root",
            "frontmatter": {}, "body": "",
            "detail": (
                f"--layers {sorted(layer_set)} excluded the {ntype.upper()} context "
                f"for the selected root {tid}; the doc shows only the included layers."
            ),
            "ac": None,
        })

    kept = [e for e in entries if LAYER_FOR_TYPE.get(e["type"]) in layer_set]
    kept.extend(warnings)
    kept.sort(key=lambda e: (TYPE_RANK.get(e["type"], 99), str(e["id"])))
    return kept


def compact_fields(entry: Dict[str, Any]) -> List[List[str]]:
    """Deterministic struct compaction: the key fields to show when an entry is
    rendered at `verbosity=struct` (narrative body dropped). Returns ordered
    `[label, value]` pairs. Stories -> AC count; goals -> metrics; BRD -> goal
    titles; plus the common scope/status/moscow/horizon enums when present.
    """
    fm = entry.get("frontmatter") or {}
    out: List[List[str]] = []
    for key in ("status", "scope", "moscow", "horizon", "size", "owner"):
        if fm.get(key) not in (None, ""):
            out.append([key, str(fm.get(key))])
    if entry["type"] == "goal" or entry["type"] == "brd":
        metrics = fm.get("metrics")
        if isinstance(metrics, list) and metrics:
            out.append(["metrics", ", ".join(str(m) for m in metrics)])
    if entry["type"] == "brd":
        goals = fm.get("goals")
        if isinstance(goals, list):
            titles = [str(g.get("title") or g.get("id") or "") for g in goals if isinstance(g, dict)]
            if titles:
                out.append(["goals", "; ".join(titles)])
    if entry["type"] == "story" and isinstance(entry.get("ac"), list):
        out.append(["acceptance_criteria", f"{len(entry['ac'])} item(s)"])
    return out
