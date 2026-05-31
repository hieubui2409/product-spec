#!/usr/bin/env python3
"""
spec_graph — load all artifacts under <root>/docs/product/ and build the
directed graph story -> epic -> prd -> brd_goal -> vision.

Structural-only: parses frontmatter, resolves explicit ID links, exposes a
downstream() query for delta-update. NO judgment.

CLI:
    spec_graph.py --root <project-dir> [--snapshot]
        --snapshot writes a JSON snapshot to docs/product/visuals/.snapshots/
                   in addition to printing graph JSON to stdout.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from encoding_utils import configure_utf8_console
from frontmatter_parser import parse_file

configure_utf8_console()


ARTIFACT_GLOBS = {
    "product": ["PRODUCT.md"],
    "vision": ["vision.md"],
    "brd": ["brd.md"],
    "prd": ["prds/*.md"],
    "epic": ["epics/*.md"],
    "story": ["stories/*.md"],
}

# The single authoritative expected-child-type map for the hierarchy. The gap
# views (render_ascii/render_mermaid) and the unaddressed-parent check
# (check_traceability) all key off this; importing it here keeps the rule in one
# home so adding a hierarchy level edits one place, not three.
CHILD_TYPE_FOR_PARENT = {
    "goal": "prd",
    "prd": "epic",
    "epic": "story",
}


def load_artifacts(product_dir: Path) -> List[Dict[str, Any]]:
    """Walk docs/product/ and parse every artifact. Includes parse_error entries."""
    artifacts: List[Dict[str, Any]] = []
    for art_type, globs in ARTIFACT_GLOBS.items():
        for pattern in globs:
            for path in sorted(product_dir.glob(pattern)):
                parsed = parse_file(path)
                parsed["__type_hint"] = art_type
                artifacts.append(parsed)
    return artifacts


def _title_from_h1(body: str, node_id: Optional[str]) -> str:
    """Pull a human title from the artifact's first H1 — the templates put the
    title ONLY in the `# {{title}} — <TYPE> <id>` heading, never in frontmatter, so
    without this every PRD/epic/story node carries an empty title (the graph views
    show bare IDs and the board/explorer cards have no heading). Strip a trailing
    ` — …<id>` qualifier the templates append; a hand-written heading with no such
    suffix (e.g. `# Automated Payouts Epic`) is kept verbatim."""
    if not body:
        return ""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            h = line[2:].strip()
            if node_id and "—" in h:
                head, _, tail = h.rpartition("—")
                if node_id in tail:
                    h = head.strip() or h
            return h
    return ""


def _node_type(art: Dict[str, Any]) -> Optional[str]:
    """Resolve an artifact's type identically everywhere: a malformed `type:`
    (a YAML list/dict from a hand-edit) coerces to None so it falls back to the
    directory-derived hint instead of short-circuiting an `or` with a truthy
    non-string and poisoning a downstream `== "brd"` / dict-key test."""
    raw = art.get("frontmatter", {}).get("type")
    return (raw if isinstance(raw, str) else None) or art.get("__type_hint")


def build_nodes(artifacts: List[Dict[str, Any]], product_dir: Path) -> List[Dict[str, Any]]:
    """Convert parsed artifacts to graph nodes. BRD goals are expanded from brd.md.goals."""
    nodes: List[Dict[str, Any]] = []
    for art in artifacts:
        if not art["ok"]:
            continue
        fm = art["frontmatter"]
        rel = Path(art["file"]).resolve().relative_to(product_dir.resolve()).as_posix()
        node_type = _node_type(art)
        if node_type == "brd":
            goals = fm.get("goals") or []
            for g in goals:
                if not isinstance(g, dict):
                    continue
                nodes.append(_node_from_goal(g, parent_file=rel))
        else:
            nodes.append(_node_from_artifact(fm, rel, node_type, art.get("body") or ""))
    return nodes


def _node_from_artifact(fm: Dict[str, Any], file_rel: str, node_type: Optional[str],
                        body: str = "") -> Dict[str, Any]:
    nid = _scalar_id(fm.get("id"))
    return {
        "id": nid,
        "type": node_type,
        # Frontmatter `name`/`title` win when present; otherwise fall back to the
        # body H1 so the title is never empty (see _title_from_h1).
        "title": fm.get("name") or fm.get("title") or _title_from_h1(body, nid) or "",
        "status": fm.get("status"),
        "scope": fm.get("scope"),
        "moscow": fm.get("moscow"),
        "horizon": fm.get("horizon"),
        "size": fm.get("size"),
        "personas": fm.get("personas") or [],
        "metrics": fm.get("metrics") or [],
        "owner": fm.get("owner"),
        "version": fm.get("version"),
        "lang": fm.get("lang"),
        "file": file_rel,
        "brd_goals": fm.get("brd_goals") or [],
        "epic": _scalar_link(fm.get("epic")),
        "prd": _scalar_link(fm.get("prd")),
        # TIME dimension: single ISO target_date (PyYAML parses `2026-09-30` to a
        # datetime.date; the JSON CLI coerces via default=str). Optional → None
        # when absent so a v1 artifact stays back-compatible (no churn).
        "target_date": fm.get("target_date"),
        # depends_on edge — a list of artifact IDs (PRD+Epic only; the type-guard
        # in check_consistency flags a non-empty list on any other type). Sorted +
        # uniform empty default on ALL node types: harmless on a story/goal (the
        # list is empty there) and makes the dep adjacency build branch-free.
        # A bare scalar `depends_on: PRD-X` is silently coerced to [] by
        # _as_id_list — crash-safety by design; wrong-type placement on a non-empty
        # list is still flagged by check_consistency._check_depends_on_type.
        "depends_on": _as_id_list(fm.get("depends_on")),
        # Raw `risks:` list preserved on the node (not just aggregated into
        # graph["risks"]) so check_consistency can enum-validate each entry's
        # impact/likelihood/status and flag a non-dict entry via invalid_type.
        # Kept as `None` when absent so a v1 artifact without risks: stays
        # back-compatible (no empty-list churn in snapshots/diffs).
        "risks": fm.get("risks"),
        # COMPETITION dimension: a PRD references BRD competitors by ID via an
        # ID-keyed map `competitive_parity: {COMP-ACME: behind}` (enum value
        # ahead|parity|behind|none). Preserved verbatim on the node so the
        # consistency check enum-/ref-validates each entry, the matrix/heatmap
        # renderer reads it, and the drift LLM-input builder resolves it against
        # graph["competitors"]. `None` when absent → a v1 PRD stays back-compat.
        "competitive_parity": fm.get("competitive_parity"),
    }


def _node_from_goal(goal: Dict[str, Any], parent_file: str) -> Dict[str, Any]:
    return {
        "id": _scalar_id(goal.get("id")),
        "type": "goal",
        "title": goal.get("title") or "",
        "status": goal.get("status"),
        "metrics": goal.get("metrics") or [],
        "owner": goal.get("owner"),
        "file": parent_file,
        # No `parent` edge field: goals attach to PRODUCT directly in the rendered
        # tree (build_edges emits no goal->BRD edge — see its comment). A stored
        # `parent: BRD` here would be an inert field no consumer reads.
    }


def build_edges(nodes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """For each child node, emit edges to its parent(s) by ID."""
    edges: List[Dict[str, str]] = []
    for n in nodes:
        ntype = n["type"]
        if ntype == "story" and n.get("epic"):
            edges.append({"from": n["id"], "to": n["epic"], "kind": "epic"})
        elif ntype == "epic" and n.get("prd"):
            edges.append({"from": n["id"], "to": n["prd"], "kind": "prd"})
        elif ntype == "prd":
            # Guard the iteration: brd_goals is kept RAW on the node (so the
            # LIST_FIELDS check can still flag a bare-string `brd_goals: BRD-G1`
            # as invalid_type). Iterate only when it is a list and emit an edge
            # only for str elements — never char-split a bare string into phantom
            # single-char edges, and preserve edge ORDER for parents_of multi-goal.
            goals = n.get("brd_goals")
            for g in (goals if isinstance(goals, list) else []):
                if isinstance(g, str):
                    edges.append({"from": n["id"], "to": g, "kind": "brd_goal"})
        # Goal nodes have no outbound edge in the graph: there is no `brd`
        # container node, and goals are rendered as direct children of
        # PRODUCT by the tree renderers. An earlier `goal -> "BRD"` edge
        # produced a phantom unlabeled box in the tree Mermaid output.
    return edges


def _assemble_graph(artifacts: List[Dict[str, Any]], product_dir: Path, root: Path) -> Dict[str, Any]:
    """Build the graph JSON from already-parsed artifacts. Split from build_graph
    so callers that also need the raw artifacts (export / board / explorer) can
    parse docs/product/ exactly once via build_graph_with_artifacts()."""
    nodes = build_nodes(artifacts, product_dir)
    edges = build_edges(nodes)
    parse_errors = [{"file": a["file"], "error": a["error"]} for a in artifacts if not a["ok"]]
    return {
        "version": "1.0",
        "generated_at": _now(),
        "product": _product_meta(artifacts),
        "nodes": nodes,
        "edges": edges,
        "risks": _risks(artifacts, product_dir),
        # COMPETITION dimension: the single DRY home for competitor IDENTITY,
        # materialized once from the BRD's `competitors:` list. The consistency
        # check, the parity-matrix/threat-heatmap renderer, AND the drift
        # LLM-input builder ALL read this top-level key — nothing re-parses
        # brd.md inline. Empty list when the BRD declares no competitors (a v1
        # spec stays back-compatible).
        "competitors": _competitors(artifacts),
        "parse_errors": parse_errors,
        "root_path": str(root),
    }


def _missing_dir_graph(root: Path) -> Dict[str, Any]:
    return {"version": "1.0", "generated_at": _now(), "product": {}, "nodes": [], "edges": [], "risks": [], "competitors": [], "parse_errors": [], "missing_product_dir": True, "root_path": str(root)}


def build_graph(root: Path) -> Dict[str, Any]:
    """Top-level: parse, build, return graph JSON shape per visualization-spec.md.

    `root_path` is included so downstream checkers (e.g. the `.session.md`
    gitignore guard in check_consistency) can inspect repo-level state
    without needing to be threaded a separate `root` argument.
    """
    product_dir = root / "docs" / "product"
    if not product_dir.exists():
        return _missing_dir_graph(root)
    artifacts = load_artifacts(product_dir)
    return _assemble_graph(artifacts, product_dir, root)


def build_graph_with_artifacts(root: Path):
    """Return (graph, artifacts) parsing docs/product/ ONCE. build_graph re-parses
    internally and discards the artifact list, so any caller that needs both the
    graph and the raw artifacts (export, board, explorer) MUST use this to avoid a
    redundant second full parse of every artifact file."""
    product_dir = root / "docs" / "product"
    if not product_dir.exists():
        return _missing_dir_graph(root), []
    artifacts = load_artifacts(product_dir)
    return _assemble_graph(artifacts, product_dir, root), artifacts


def index_artifacts(artifacts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map artifact id -> parsed artifact, for ok top-level files (product/vision/
    brd/prd/epic/story). Goals live inside brd.md and are not indexed here. Shared
    by the digest assembler and the board/explorer viewers (single id->artifact
    loop instead of one re-implementation per renderer).

    Keys by _scalar_id (same coercion build_nodes uses) so a malformed-id artifact
    is indexed under '<invalid-id>' rather than dropped — body/AC/export continue
    to work; check_consistency surfaces the id error separately."""
    out: Dict[str, Dict[str, Any]] = {}
    for a in artifacts:
        if not a.get("ok"):
            continue
        aid = _scalar_id((a.get("frontmatter") or {}).get("id"))
        out[aid] = a
    return out


def _product_meta(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    for a in artifacts:
        if a["ok"] and _node_type(a) == "product":
            fm = a["frontmatter"]
            return {
                "name": fm.get("name"),
                "core_value": fm.get("core_value"),
                "personas": fm.get("personas") or [],
            }
    return {}


def _risks(artifacts: List[Dict[str, Any]], product_dir: Path) -> List[Dict[str, Any]]:
    """Aggregate every artifact's `risks:` list into flat risk objects.

    Each emitted object carries its source `node` id plus the risk fields,
    including `mitigation` (free text) and `status` (open|mitigated|accepted)
    so the HTML risk grid can show them in the cell drill-down. Non-dict
    entries (e.g. `risks: ["just a string"]`) are skipped here — the bad shape
    is surfaced as an `invalid_type` finding by check_consistency, not by
    silently materializing a malformed graph risk.
    """
    risks: List[Dict[str, Any]] = []
    for a in artifacts:
        if not a["ok"]:
            continue
        fm = a["frontmatter"]
        for r in fm.get("risks") or []:
            if isinstance(r, dict):
                risks.append({"node": fm.get("id"), **r})
    return risks


# A competitor `url` beginning with this prefix is an internal/secret reference
# (e.g. `private:internal/teardown.pdf`). It is the OpSec single chokepoint: the
# parser DROPS such a URL here so the secret path can never reach the graph, the
# consistency findings, OR any render. The competitor itself is still kept (only
# its url is stripped) — id/name/threat remain usable.
_PRIVATE_URL_PREFIX = "private:"


def _competitors(artifacts: List[Dict[str, Any]]) -> List[Any]:
    """Materialize the BRD's `competitors:` list into the graph's single DRY home.

    Competitor IDENTITY lives ONCE in the BRD. Each well-formed entry surfaces
    as `{id, name, url, threat}`; a `url` starting `private:` is the encrypted
    OpSec case — its value is dropped to `None` so the secret path never reaches
    the graph, the findings, OR any render (single chokepoint, G-E4).

    A non-mapping entry (e.g. a bare string) is PRESERVED verbatim in the list so
    check_consistency can flag it as `invalid_type` — the single DRY home carries
    the raw shape; consumers (renderers, the drift builder) filter to dicts (the
    same `isinstance(c, dict)` guard the tests use). The BRD is not a graph node
    (its goals are expanded), so this top-level key is competitors' only home.
    Empty list when there is no BRD / no `competitors:` (a v1 spec stays clean).
    """
    competitors: List[Any] = []
    for a in artifacts:
        if not a["ok"]:
            continue
        fm = a["frontmatter"]
        if _node_type(a) != "brd":
            continue
        for c in fm.get("competitors") or []:
            if not isinstance(c, dict):
                competitors.append(c)  # bad shape → invalid_type (check_consistency)
                continue
            url = c.get("url")
            # Coerce a non-string url (a list/dict from malformed YAML) to None
            # FIRST so the single chokepoint stores only a clean str-or-None,
            # then apply the OpSec drop: a `private:`-prefixed URL is dropped so
            # the secret path never reaches the graph or any render (G-E4).
            if not isinstance(url, str):
                url = None
            elif url.strip().startswith(_PRIVATE_URL_PREFIX):
                url = None
            competitors.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "url": url,
                "threat": c.get("threat"),
            })
    return competitors


def _closure(adj: Dict[str, List[str]], start: str) -> Set[str]:
    """Transitive closure of `start` over an adjacency map (the single home for the
    iterative stack walk that downstream/ancestors and the assembler all need)."""
    out: Set[str] = set()
    stack = list(adj.get(start, []))
    while stack:
        n = stack.pop()
        if n in out:
            continue
        out.add(n)
        stack.extend(adj.get(n, []))
    # Exclude the start itself: a self-edge (start->start) or a cycle that loops
    # back to start must not report a node as its own descendant.
    return out - {start}


def children_of(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    """parent id -> list of child ids (the forward adjacency). Mirror of
    parents_of; one home for the `children[e["to"]].append(e["from"])` build the
    renderers and downstream() otherwise re-type. Edge convention: `to`=parent,
    `from`=child (see build_edges)."""
    out: Dict[str, List[str]] = defaultdict(list)
    for e in graph["edges"]:
        out[str(e["to"])].append(str(e["from"]))
    return out


def downstream(graph: Dict[str, Any], node_id: str) -> Set[str]:
    """Return the set of node IDs reachable as descendants of node_id."""
    return _closure(children_of(graph), node_id)


def ancestors(graph: Dict[str, Any], node_id: str) -> Set[str]:
    """Return the set of node IDs reachable as ancestors (parents) of node_id.

    The inverse of downstream(): walks child -> parent over the same
    `{from, to}` edges (where `from` is the child and `to` the parent). For a
    story it returns its epic, PRD, and the goal(s) the PRD addresses — i.e.
    `ancestors("PRD-AUTH-E1-S1") == {"PRD-AUTH-E1", "PRD-AUTH", "BRD-G1"}`.

    It returns the goals + PRD/epic chain ONLY. Vision and the BRD container
    are NOT graph nodes (build_nodes nodifies goals, not the BRD; vision is an
    isolated node with no edges), so they can never appear here. The assembler
    prepends them as singletons instead — do not add phantom Vision/BRD edges.

    Public graph API kept as the symmetric mirror of downstream() and exercised
    by the assembler's tests; the production digest assembler inlines its own
    _adjacency()/_reach() walk for the batched O(N+edges) build, so this is not
    on the export hot path — do not "fix" the assembler to call it.
    """
    return _closure(parents_of(graph), node_id)


def matching_child_counts(graph: Dict[str, Any]) -> Dict[str, int]:
    """For each parent-type node id, count inbound edges whose SOURCE node is of
    the EXPECTED child type (goal←prd, prd←epic, epic←story). The single home for
    the 'unaddressed parent' rule shared by the gap views and check_traceability —
    counting only expected-type children means a stray wrong-type edge (e.g. a goal
    with a story pointing at it on a malformed graph) does not mask the gap."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    counts: Dict[str, int] = defaultdict(int)
    for e in graph["edges"]:
        src_type = nodes_by_id.get(e["from"], {}).get("type")
        tgt_type = nodes_by_id.get(e["to"], {}).get("type")
        if tgt_type in CHILD_TYPE_FOR_PARENT and CHILD_TYPE_FOR_PARENT[tgt_type] == src_type:
            counts[e["to"]] += 1
    return dict(counts)


def parents_of(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    """child id -> list of ALL parent ids, in edge order, distinct, str-coerced.

    The single home for the tree-parent rule the explorer payload and the ASCII
    orphan-forest both need. A PRD with `brd_goals: [G1, G2]` has two parents, so
    multi-goal coverage renders under EACH goal (matching the ASCII tree) instead
    of only the first; root determination tests against ANY parent being present.
    Self-edges (id == id) are dropped — a node is never its own tree parent — which
    also neutralizes the self/cyclic-parent hang in the downstream client walk."""
    out: Dict[str, List[str]] = defaultdict(list)
    for e in graph["edges"]:
        child, par = str(e["from"]), str(e["to"])
        if par != child and par not in out[child]:
            out[child].append(par)
    return dict(out)


def diff_graphs(current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Structural diff between two graph snapshots: added/removed node ids plus the
    PRODUCT-level fields (name/core_value/personas) that changed. The single home
    for the set-math + product-change rule the ASCII and Mermaid delta views share;
    each view keeps only its own formatting (and ASCII its per-field node diff)."""
    cur_ids = {n["id"] for n in current.get("nodes", [])}
    base_ids = {n["id"] for n in baseline.get("nodes", [])}
    cur_p = current.get("product") or {}
    base_p = baseline.get("product") or {}
    product_changes: List[str] = []
    for field in ("name", "core_value"):
        if cur_p.get(field) != base_p.get(field):
            product_changes.append(field)
    # Coerce each persona to str before sorting: a malformed PRODUCT.md may carry
    # a non-str persona entry (int/dict from a hand-edit) that would raise TypeError
    # on a mixed-type sorted() call and crash --viz delta.
    cur_set = {str(p) for p in (cur_p.get("personas") or [])}
    base_set = {str(p) for p in (base_p.get("personas") or [])}
    if cur_set != base_set:
        product_changes.append("personas")
    return {
        "added": sorted(cur_ids - base_ids),
        "removed": sorted(base_ids - cur_ids),
        "product_changes": product_changes,
    }


def write_snapshot(graph: Dict[str, Any], root: Path) -> Path:
    """Persist a graph snapshot under docs/product/visuals/.snapshots/<ISO>-<hash>.json.

    Filename is derived from `graph["generated_at"]` (so name and in-body
    `snapshot_at` agree to the second) plus the first 8 hex digits of the
    SHA-256 of the JSON body. The hash suffix prevents two snapshots taken
    in the same second from silently overwriting each other while keeping
    the filename deterministic (same content → same hash → same path).
    """
    snap_dir = root / "docs" / "product" / "visuals" / ".snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    generated_at = graph.get("generated_at") or _now()
    # `default=str` coerces YAML-typed values such as a `target_date` (which
    # PyYAML auto-parses to `datetime.date`) into ISO strings — the same
    # convention the stdout JSON uses. Without it a v2 spec carrying any
    # `target_date` crashes the snapshot write (and so blocks the --validate
    # impact-pass that reads the snapshot delta).
    body = json.dumps({"snapshot_at": generated_at, **graph}, indent=2, ensure_ascii=False, default=str)
    # First 8 hex chars of SHA-256 of the serialized body; content-derived so
    # identical graph states produce the same filename (idempotent writes).
    content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]
    # generated_at is ISO 8601 with trailing "Z"; strip non-alnum for compact form.
    ts = generated_at.replace("-", "").replace(":", "")
    path = snap_dir / f"{ts}-{content_hash}.json"
    path.write_text(body, encoding="utf-8")
    return path


def _as_id_list(v: Any) -> List[str]:
    """Coerce a frontmatter `depends_on` into a sorted list of ID strings.

    A non-list (a bare scalar / None / mapping from malformed YAML) yields [] —
    so build_graph never raises on a mixed-type `sorted()` and never silently
    splits a bare string into characters (`sorted("PRD-2") == ['-','2','D','P','R']`).
    The wrong-artifact-type placement is surfaced separately by check_consistency."""
    if not isinstance(v, list):
        return []
    return sorted(x for x in v if isinstance(x, str))


def _scalar_id(v: Any) -> str:
    """Coerce a frontmatter `id` to a hashable str so it can NEVER raise when used
    as a dict key / set element (every checker, the matrix, the renderers, and the
    digest assembler index nodes by id). Absent → `<missing-id>`; a non-string
    (list/dict/int from a hand-edit) → `<invalid-id>`, which then fails the
    ID-grammar regex and surfaces as `invalid_id` instead of crashing the gate."""
    if isinstance(v, str):
        return v or "<missing-id>"
    if v is None:
        return "<missing-id>"
    return "<invalid-id>"


# The two sentinel strings _scalar_id() emits for absent/malformed IDs. Callers
# that present valid IDs to the PO (e.g. assemble_digest's unresolved-selection
# help text) subtract these so the PO never sees an internal sentinel as a
# "selectable" artifact ID. Single authoritative home — import, never re-literal.
ID_SENTINELS = ("<missing-id>", "<invalid-id>")


def _scalar_link(v: Any) -> Optional[str]:
    """Coerce a scalar parent link (`epic` / `prd`) to str|None at the single
    source. A non-string (list/dict from malformed YAML) → None, so build_edges
    and every `nodes_by_id.get(parent_id)` lookup never hash an unhashable value;
    the now-missing parent surfaces as an orphan/dangling finding (fail-soft)
    rather than crashing every downstream gate + analytical script."""
    return v if isinstance(v, str) else None


# Canonical horizon section order (the single home; renderers import it instead
# of repeating the ('now','next','later') tuple). 'unspecified' is appended by
# each renderer that needs an overflow bucket.
HORIZON_ORDER = ("now", "next", "later")

# Parent-scoped ID grammar — the single authoritative home. check_consistency and
# generate_templates both import these instead of re-encoding the same regex with
# "kept in sync" comments. `<SLUG>` = uppercase ASCII letter start, then up to 15
# letters/digits/hyphens.
ID_PATTERN_BY_TYPE = {
    "goal": re.compile(r"^BRD-G[0-9]+$"),
    "prd": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}$"),
    "epic": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+$"),
    "story": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+-S[0-9]+$"),
}
# Competitor ID grammar: `COMP-<SLUG>` (same parent-scoped discipline).
COMP_ID_PATTERN = re.compile(r"^COMP-[A-Z][A-Z0-9-]{0,15}$")


def make_finding(check_id: str, severity: str, node: Dict[str, Any], detail: str, **context) -> Dict[str, Any]:
    """The single home for the finding-record constructor shared by
    check_consistency and check_traceability (both previously defined a
    byte-identical `_f`). Keeps the finding shape in one place so the two
    checkers cannot drift."""
    return {
        "check": check_id,
        "severity": severity,
        "artifact_id": node.get("id"),
        "file": node.get("file"),
        "detail": detail,
        "context": context or None,
    }


def resolve_ac(node: Dict[str, Any]) -> List[Any]:
    """Effective acceptance_criteria for a node: a list with None/'' entries
    filtered out. The single home for the 'AC count' rule so the validator
    (check_consistency) and the explorer badge (render_explorer) cannot diverge
    on whether blank/None entries count."""
    raw = node.get("acceptance_criteria")
    if isinstance(raw, list):
        return [x for x in raw if x not in (None, "")]
    return []


def moscow_story_counts(graph: Dict[str, Any]) -> Dict[str, int]:
    """Per-bucket story histogram (must/should/could/wont). The single home for
    the tally the ASCII and Mermaid moscow renderers both need."""
    counts: Dict[str, int] = {"must": 0, "should": 0, "could": 0, "wont": 0}
    for n in graph.get("nodes", []):
        if n.get("type") != "story":
            continue
        m = n.get("moscow")
        if isinstance(m, str) and m in counts:
            counts[m] += 1
    return counts


def competitor_id_to_name(graph: Dict[str, Any]) -> Dict[str, str]:
    """Map well-formed BRD competitor id -> name. The DRY home for the
    'resolvable competitor' rule the consistency check and the drift anchors
    both need (each previously re-encoded the `isinstance(c, dict) and
    isinstance(c.get('id'), str)` guard)."""
    out: Dict[str, str] = {}
    for c in graph.get("competitors") or []:
        if isinstance(c, dict) and isinstance(c.get("id"), str):
            out[c["id"]] = c.get("name") if isinstance(c.get("name"), str) else c["id"]
    return out


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="project root (contains docs/product/)")
    ap.add_argument("--snapshot", action="store_true", help="also write a snapshot file")
    ap.add_argument("--downstream", default=None, help="print downstream set for the given ID and exit")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)

    if args.downstream:
        ids = sorted(downstream(graph, args.downstream))
        print(json.dumps({"node": args.downstream, "downstream": ids}, indent=2, ensure_ascii=False, default=str))
        return 0

    if args.snapshot:
        snap = write_snapshot(graph, root)
        graph["__snapshot_path"] = str(snap.relative_to(root))

    # `default=str` coerces YAML-typed values such as `status: 2026-05-29`
    # (which PyYAML auto-parses to `datetime.date`) into ISO strings, so
    # the script keeps its "always exit 0, emit JSON" contract instead
    # of raising `TypeError: Object of type date is not JSON serializable`.
    print(json.dumps(graph, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
