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

# Reference table for the parent-link field per artifact type. Kept as
# documentation; build_edges() inlines the same routing because story/epic
# carry a scalar parent and PRD carries a list (brd_goals), which is hard
# to express uniformly. The `goal` row used to claim a `parent: BRD` link;
# the spec dropped that field — BRD is a singleton container, goals attach
# to PRODUCT directly in the rendered tree.
PARENT_FIELD_BY_TYPE = {
    "story": ("epic", "epic"),
    "epic": ("prd", "prd"),
    "prd": ("brd_goals", "brd_goal"),  # list field
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
        "parent": "BRD",
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
    risks: List[Dict[str, Any]] = []
    for a in artifacts:
        if not a["ok"]:
            continue
        fm = a["frontmatter"]
        for r in fm.get("risks") or []:
            if isinstance(r, dict):
                risks.append({"node": fm.get("id"), **r})
    return risks


def downstream(graph: Dict[str, Any], node_id: str) -> Set[str]:
    """Return the set of node IDs reachable as descendants of node_id."""
    children: Dict[str, List[str]] = defaultdict(list)
    for e in graph["edges"]:
        children[e["to"]].append(e["from"])
    out: Set[str] = set()
    stack = list(children.get(node_id, []))
    while stack:
        n = stack.pop()
        if n in out:
            continue
        out.add(n)
        stack.extend(children.get(n, []))
    return out


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
    """
    parents: Dict[str, List[str]] = defaultdict(list)
    for e in graph["edges"]:
        parents[e["from"]].append(e["to"])
    out: Set[str] = set()
    stack = list(parents.get(node_id, []))
    while stack:
        n = stack.pop()
        if n in out:
            continue
        out.add(n)
        stack.extend(parents.get(n, []))
    return out


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
