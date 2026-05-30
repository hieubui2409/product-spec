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


def build_nodes(artifacts: List[Dict[str, Any]], product_dir: Path) -> List[Dict[str, Any]]:
    """Convert parsed artifacts to graph nodes. BRD goals are expanded from brd.md.goals."""
    nodes: List[Dict[str, Any]] = []
    for art in artifacts:
        if not art["ok"]:
            continue
        fm = art["frontmatter"]
        rel = Path(art["file"]).resolve().relative_to(product_dir.resolve()).as_posix()
        node_type = fm.get("type") or art.get("__type_hint")
        if node_type == "brd":
            goals = fm.get("goals") or []
            for g in goals:
                if not isinstance(g, dict):
                    continue
                nodes.append(_node_from_goal(g, parent_file=rel))
        else:
            nodes.append(_node_from_artifact(fm, rel, node_type))
    return nodes


def _node_from_artifact(fm: Dict[str, Any], file_rel: str, node_type: Optional[str]) -> Dict[str, Any]:
    return {
        "id": fm.get("id") or "<missing-id>",
        "type": node_type,
        "title": fm.get("name") or fm.get("title") or "",
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
        "epic": fm.get("epic"),
        "prd": fm.get("prd"),
        # TIME dimension: single ISO target_date (PyYAML parses `2026-09-30` to a
        # datetime.date; the JSON CLI coerces via default=str). Optional → None
        # when absent so a v1 artifact stays back-compatible (no churn).
        "target_date": fm.get("target_date"),
        # depends_on edge — a list of artifact IDs (PRD+Epic only; the type-guard
        # in check_consistency flags a non-empty list on any other type). Sorted +
        # uniform empty default on ALL node types: harmless on a story/goal (the
        # list is empty there) and makes the dep adjacency build branch-free.
        "depends_on": sorted(fm.get("depends_on") or []),
        # Raw `risks:` list preserved on the node (not just aggregated into
        # graph["risks"]) so check_consistency can enum-validate each entry's
        # impact/likelihood/status and flag a non-dict entry via invalid_type.
        # Kept as `None` when absent so a v1 artifact without risks: stays
        # back-compatible (no empty-list churn in snapshots/diffs).
        "risks": fm.get("risks"),
    }


def _node_from_goal(goal: Dict[str, Any], parent_file: str) -> Dict[str, Any]:
    return {
        "id": goal.get("id") or "<missing-id>",
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
            for g in n.get("brd_goals", []):
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
        "parse_errors": parse_errors,
        "root_path": str(root),
    }


def _missing_dir_graph(root: Path) -> Dict[str, Any]:
    return {"version": "1.0", "generated_at": _now(), "product": {}, "nodes": [], "edges": [], "risks": [], "parse_errors": [], "missing_product_dir": True, "root_path": str(root)}


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
    loop instead of one re-implementation per renderer)."""
    out: Dict[str, Dict[str, Any]] = {}
    for a in artifacts:
        if not a.get("ok"):
            continue
        aid = (a.get("frontmatter") or {}).get("id")
        if aid:
            out[str(aid)] = a
    return out


def _product_meta(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    for a in artifacts:
        if a["ok"] and (a["frontmatter"].get("type") == "product" or a.get("__type_hint") == "product"):
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
    return out


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
    if sorted(cur_p.get("personas") or []) != sorted(base_p.get("personas") or []):
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
    body = json.dumps({"snapshot_at": generated_at, **graph}, indent=2, ensure_ascii=False)
    # First 8 hex chars of SHA-256 of the serialized body; content-derived so
    # identical graph states produce the same filename (idempotent writes).
    content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]
    # generated_at is ISO 8601 with trailing "Z"; strip non-alnum for compact form.
    ts = generated_at.replace("-", "").replace(":", "")
    path = snap_dir / f"{ts}-{content_hash}.json"
    path.write_text(body, encoding="utf-8")
    return path


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
