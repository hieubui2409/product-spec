#!/usr/bin/env python3
"""
assemble_digest — deterministic, script-owned core for the F1 `--export` doc.
Turns (selection + layer-filter + depth) into an ordered digest model. No HTML,
no LLM, no I/O beyond the parsed artifacts.

`build_digest` powers `--export` only. The F2 board/explorer viewers build their
OWN payloads (render_board / render_explorer) and do not call build_digest; the
sole thing they once shared — the `LAYER_FOR_TYPE` map — they no longer use
either (they filter by artifact type via render_ascii._filter_by_layers). Keep
this module export-scoped; do not re-unify the viewer payloads onto it.

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
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from spec_graph import index_artifacts


# Each artifact type belongs to one --export --layers bucket. Goals live in the
# BRD, so they share the `brd` layer; vision/prd/epic/story map to their own
# names. NOTE this is the EXPORT doc-layer vocabulary; the board/explorer viewers
# filter by artifact TYPE directly (see render_ascii._filter_by_layers) so their
# `--layers goal` matches the CLI help — the two surfaces intentionally differ.
LAYER_FOR_TYPE = {
    "vision": "vision",
    "brd": "brd",
    "goal": "brd",
    "prd": "prd",
    "epic": "epic",
    "story": "story",
}
ALL_LAYERS = ("vision", "brd", "prd", "epic", "story")

# Selection IDs that resolve to a context SINGLETON, not an edge-walk target.
# "BRD" is not a graph node (brd.md expands to goal nodes) so it is matched by
# the literal id; vision/product ARE nodes but are surfaced as singletons.
_SINGLETON_TYPES = ("vision", "brd", "product")

# Hierarchy rank for the canonical sort. `_warning` sorts to the very front so
# provenance notes lead the doc; PRODUCT context (when explicitly exported) leads
# the spec body, then top-down.
TYPE_RANK = {"_warning": -1, "product": 0, "vision": 1, "brd": 2, "goal": 3, "prd": 4, "epic": 5, "story": 6}

# Per-type verbosity at --depth context: ancestors/singletons are compacted,
# the target and its descendants render in full.
_CONTEXT_FULL_ROLES = ("target", "descendant")


def _find_by_type(artifacts: List[Dict[str, Any]], art_type: str) -> Optional[Dict[str, Any]]:
    for a in artifacts:
        if not a.get("ok"):
            continue
        fm = a.get("frontmatter") or {}
        if fm.get("type") == art_type or a.get("__type_hint") == art_type:
            return a
    return None


_SPEC_TYPES = ("goal", "prd", "epic", "story")


def _resolve_selection(select: str, graph: Dict[str, Any]) -> Tuple[Set[str], Set[str], List[str]]:
    """Classify a `--export` selection into:
      • spec_targets   — goal/PRD/epic/story node IDs to walk (ancestors+descendants)
      • singleton_types — vision/brd/product requested as CONTEXT (not edge-walked)
      • unresolved     — requested IDs that match nothing (typos / wrong case)

    `all` selects every spec node and no explicit singletons. Splitting context
    artifacts (vision/brd/product) OUT of the target set is what stops `--export
    VISION` double-rendering vision (once as target, once as the prepended
    singleton); reporting `unresolved` is what lets the caller fail loudly instead
    of writing a silently-empty doc (CLAUDE.md: no silent failure)."""
    type_by_id = {n["id"]: n.get("type") for n in graph["nodes"]}
    if select == "all":
        return ({nid for nid, t in type_by_id.items() if t in _SPEC_TYPES}, set(), [])

    spec: Set[str] = set()
    singles: Set[str] = set()
    unresolved: List[str] = []
    for w in [s.strip() for s in select.split(",") if s.strip()]:
        t = type_by_id.get(w)
        if t in _SPEC_TYPES:
            spec.add(w)
        elif t in ("vision", "product"):
            singles.add(t)
        elif w == "BRD" or t == "brd":
            singles.add("brd")
        else:
            unresolved.append(w)
    return spec, singles, unresolved


def _adjacency(graph: Dict[str, Any]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build the parents and children edge indices ONCE. ancestors()/downstream()
    each rebuild this per call, so walking N targets was O(N·edges); building it
    once here and reusing it for every target makes the digest O(N + edges)."""
    parents: Dict[str, List[str]] = defaultdict(list)
    children: Dict[str, List[str]] = defaultdict(list)
    for e in graph["edges"]:
        parents[e["from"]].append(e["to"])
        children[e["to"]].append(e["from"])
    return parents, children


def _reach(adj: Dict[str, List[str]], start: str) -> Set[str]:
    """Transitive closure of `start` over the given adjacency (parents or children)."""
    out: Set[str] = set()
    stack = list(adj.get(start, []))
    while stack:
        n = stack.pop()
        if n in out:
            continue
        out.add(n)
        stack.extend(adj.get(n, []))
    return out


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


def _in_layers(etype: str, layer_set: Set[str]) -> bool:
    """Whether an entry of `etype` survives the --layers filter. PRODUCT context is
    layer-agnostic: it only ever enters the digest when explicitly `--export`ed, so
    a `--layers` subset must not silently strip it."""
    if etype == "product":
        return True
    return LAYER_FOR_TYPE.get(etype) in layer_set


def build_digest(
    graph: Dict[str, Any],
    artifacts: List[Dict[str, Any]],
    select: str = "all",
    layers: Optional[List[str]] = None,
    depth: str = "context",
) -> List[Dict[str, Any]]:
    """Build the ordered digest model. See module docstring for the contract.

    Raises ValueError when the selection names IDs that resolve to nothing, or
    resolves to nothing at all (except `--export all`, which is allowed to be
    empty on a fresh spec) — so the export path fails loudly instead of writing a
    silently-empty doc (CLAUDE.md: no silent failure)."""
    layer_set = set(layers) if layers else set(ALL_LAYERS)
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    art_by_id = index_artifacts(artifacts)

    targets, singleton_types, unresolved = _resolve_selection(select, graph)
    if unresolved:
        valid = sorted(set(nodes_by_id) | {"VISION", "BRD", "PRODUCT"})
        raise ValueError(
            f"--export: unresolved selection {sorted(unresolved)} — no such artifact. "
            f"Available IDs: {valid}"
        )
    if select != "all" and not targets and not singleton_types:
        raise ValueError("--export: selection resolved to no artifacts (empty or whitespace).")

    parents, children = _adjacency(graph)
    ctx_ids: Set[str] = set()
    desc_ids: Set[str] = set()
    for t in targets:
        ctx_ids |= _reach(parents, t)
        desc_ids |= _reach(children, t)
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

    # Context singletons (PRODUCT/Vision/BRD). They are NOT edge-walk targets — a
    # singleton is prepended once when (a) it was explicitly selected, or (b) the
    # selection holds spec content below it (so there is something to contextualize).
    # Dedup against ids already present so `--export VISION` cannot render twice.
    present_ids = {e["id"] for e in entries}
    has_spec_content = bool(targets | ctx_ids | desc_ids)

    def _add_singleton(art_type: str, requested: bool) -> None:
        if not requested:
            return
        art = _find_by_type(artifacts, art_type)
        if art is None:
            return
        entry = _singleton_entry(art, art_type, depth)
        if entry["id"] in present_ids:
            return
        # --layers gating is applied uniformly by the final `kept` filter below;
        # no per-singleton layer guard here (it was redundant with that filter).
        entries.append(entry)
        present_ids.add(entry["id"])

    _add_singleton("product", "product" in singleton_types)
    _add_singleton("vision", has_spec_content or "vision" in singleton_types)
    _add_singleton("brd", has_spec_content or "brd" in singleton_types)

    # --layers precedence (owner-locked, D2): an excluded type is dropped even if
    # it is a selected root's own type. Emit ONE provenance warning per excluded
    # TYPE (not per node) so `--export all --layers prd` cannot flood the header
    # with a near-identical blockquote for every goal/epic/story.
    warnings: List[Dict[str, Any]] = []
    excluded: Dict[str, List[str]] = defaultdict(list)
    for t in targets:
        ntype = nodes_by_id[t]["type"]
        if LAYER_FOR_TYPE.get(ntype) not in layer_set:
            excluded[ntype].append(t)
    for ntype in sorted(excluded):
        ids = sorted(excluded[ntype])
        warnings.append({
            "id": ntype, "type": "_warning", "role": "warning", "verbosity": "struct",
            "title": "layers-excluded-root",
            "frontmatter": {}, "body": "",
            "detail": (
                f"--layers {sorted(layer_set)} excluded the {ntype.upper()} layer; "
                f"{len(ids)} selected {ntype}(s) appear only via their included "
                f"sub-layers (e.g. {ids[0]})."
            ),
            "ac": None,
        })

    kept = [e for e in entries if _in_layers(e["type"], layer_set)]
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
