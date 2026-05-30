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

Vision and PRODUCT ARE graph nodes, but they carry NO edges (build_nodes wires
goal→prd→epic→story; the BRD container itself is not a node — brd.md expands to
goal nodes). So ancestors()/downstream() can't reach vision/product/BRD via the
edge walk; the assembler loads them from the parsed artifacts and PREPENDS them
as `role=ancestor` singletons — a documented step, separate from the edge walk.
"""

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from spec_graph import index_artifacts, parents_of, children_of, _closure, resolve_ac, ID_SENTINELS


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
        # Match the singleton context artifacts by their LITERAL token too, mirroring
        # BRD — vision.md/PRODUCT.md may omit an `id:` (node id then '<missing-id>'),
        # so a token-equals-id match alone would reject `--export VISION` with a
        # self-contradictory 'unresolved' error that still lists VISION as available.
        elif w == "VISION" or t == "vision":
            singles.add("vision")
        elif w == "PRODUCT" or t == "product":
            singles.add("product")
        elif w == "BRD" or t == "brd":
            singles.add("brd")
        else:
            unresolved.append(w)
    return spec, singles, unresolved


def _adjacency(graph: Dict[str, Any]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build the parents and children edge indices ONCE (via the shared spec_graph
    builders). ancestors()/downstream() build one each per call, so walking N
    targets was O(N·edges); building both once here keeps the digest O(N + edges)."""
    return parents_of(graph), children_of(graph)


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
    # Use resolve_ac (the single DRY home) so None/''-filtered AC count matches the
    # validator (check_consistency) and no blank/None items leak into export bullets.
    ac = resolve_ac({"acceptance_criteria": fm.get("acceptance_criteria")}) if node["type"] == "story" else None
    return {
        "id": node["id"],
        "type": node["type"],
        "role": role,
        "verbosity": verbosity,
        "title": node.get("title") or fm.get("name") or fm.get("title") or "",
        "frontmatter": fm or {k: v for k, v in node.items() if k not in ("id", "type")},
        "body": body,
        "ac": ac,
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

    Raises ValueError when the selection names IDs that resolve to nothing,
    resolves to nothing at all, names an unknown `--layers` token, or is filtered
    to empty by `--layers`. `--export all` stays allowed-empty ONLY on a genuinely
    empty/fresh spec (nothing to filter); if `--layers` strips all PRE-EXISTING
    content it fails loud too — so the export path never writes a silently-empty
    doc (CLAUDE.md: no silent failure)."""
    if layers:
        bad = [l for l in layers if l not in ALL_LAYERS]
        if bad:
            raise ValueError(
                f"--export: unknown --layers value(s) {sorted(bad)}. "
                f"Valid export layers: {list(ALL_LAYERS)}. (The board/explorer "
                f"viewers use artifact-type layers goal/prd/epic/story instead.)"
            )
    layer_set = set(layers) if layers else set(ALL_LAYERS)
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    art_by_id = index_artifacts(artifacts)

    targets, singleton_types, unresolved = _resolve_selection(select, graph)
    if unresolved:
        # Subtract BOTH internal sentinels (<missing-id> and <invalid-id>) so the
        # PO-facing typo-help never suggests an internal coercion value as a
        # selectable artifact ID. ID_SENTINELS is the single DRY home (spec_graph).
        valid = sorted((set(nodes_by_id) | {"VISION", "BRD", "PRODUCT"}) - set(ID_SENTINELS))
        raise ValueError(
            f"--export: unresolved selection {sorted(unresolved)} — no such artifact. "
            f"Available IDs: {valid}"
        )
    if select != "all" and not targets and not singleton_types:
        raise ValueError("--export: selection resolved to no artifacts (empty or whitespace).")

    parents, children = _adjacency(graph)
    ctx_ids: Set[str] = set()
    desc_ids: Set[str] = set()
    # Memoize each target's child-reach: the --layers warning below re-uses it to
    # decide "surfaced via sub-layer vs absent" instead of re-walking the subtree.
    reach_children: Dict[str, Set[str]] = {}
    for t in targets:
        ctx_ids |= _closure(parents, t)
        r = _closure(children, t)
        reach_children[t] = r
        desc_ids |= r
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
        if ntype == "story":
            # A story is a leaf — it has no descendant layers, so an excluded
            # story is simply absent, NOT "surfaced via sub-layers".
            tail = (f"{len(ids)} selected {ntype}(s) (e.g. {ids[0]}) are absent — "
                    f"a story is a leaf with no sub-layers to surface it.")
        else:
            # Partition excluded goal/prd/epic ids: those with at least one
            # INCLUDED descendant truly surface via a sub-layer; those whose whole
            # subtree is also excluded are absent with no trace (a childless goal,
            # or a node every descendant of which is filtered out). Claiming the
            # latter "appears via sub-layers" is the silent-failure the no-silent
            # rule forbids.
            surfaced = [t for t in ids if any(
                d in nodes_by_id and _in_layers(nodes_by_id[d]["type"], layer_set)
                for d in reach_children.get(t, ()))]
            absent = [t for t in ids if t not in surfaced]
            parts: List[str] = []
            if surfaced:
                parts.append(f"{len(surfaced)} appear only via their included "
                             f"sub-layers (e.g. {surfaced[0]})")
            if absent:
                parts.append(f"{len(absent)} are absent entirely — no included "
                             f"sub-layer surfaces them (e.g. {absent[0]})")
            tail = f"{len(ids)} selected {ntype}(s): " + "; ".join(parts) + "."
        warnings.append({
            "id": ntype, "type": "_warning", "role": "warning", "verbosity": "struct",
            "title": "layers-excluded-root",
            "frontmatter": {}, "body": "",
            "detail": f"--layers {sorted(layer_set)} excluded the {ntype.upper()} layer; " + tail,
            "ac": None,
        })

    kept = [e for e in entries if _in_layers(e["type"], layer_set)]
    # Fail loud when the selection filters to nothing. For a NAMED selection that
    # is any empty (e.g. `--export VISION --layers prd`, or a leaf goal under
    # `--layers story`). For `--export all`, only when `--layers` actively stripped
    # PRE-EXISTING content (entries non-empty → kept empty): `--export all` on a
    # genuinely empty/fresh spec (no entries to filter) stays the one allowed-empty
    # case. Writing the silently-empty doc is the exact failure the unresolved-ID
    # guard closes (CLAUDE.md: no silent failure).
    if not kept and (select != "all" or (layers and entries)):
        raise ValueError(
            f"--export: selection {select!r} with --layers {sorted(layer_set)} "
            f"resolved to no content — every selected artifact's layer was excluded. "
            f"Drop --layers, or include the selected artifact's layer."
        )
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
            # Filter empty strings after mapping: goal entries lacking both title
            # and id produce "" — exclude them so the separator isn't stray.
            titles = [
                t for t in (
                    str(g.get("title") or g.get("id") or "")
                    for g in goals if isinstance(g, dict)
                )
                if t
            ]
            if titles:
                out.append(["goals", "; ".join(titles)])
    if entry["type"] == "story" and isinstance(entry.get("ac"), list):
        out.append(["acceptance_criteria", f"{len(entry['ac'])} item(s)"])
    return out
