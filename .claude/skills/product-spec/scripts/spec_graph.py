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

PARENT_FIELD_BY_TYPE = {
    "story": ("epic", "epic"),
    "epic": ("prd", "prd"),
    "prd": ("brd_goals", "brd_goal"),  # list field
    "goal": ("parent", "brd"),
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
        elif ntype == "goal":
            edges.append({"from": n["id"], "to": "BRD", "kind": "brd"})
    return edges


def build_graph(root: Path) -> Dict[str, Any]:
    """Top-level: parse, build, return graph JSON shape per visualization-spec.md."""
    product_dir = root / "docs" / "product"
    if not product_dir.exists():
        return {"version": "1.0", "generated_at": _now(), "product": {}, "nodes": [], "edges": [], "risks": [], "parse_errors": [], "missing_product_dir": True}

    artifacts = load_artifacts(product_dir)
    nodes = build_nodes(artifacts, product_dir)
    edges = build_edges(nodes)
    parse_errors = [{"file": a["file"], "error": a["error"]} for a in artifacts if not a["ok"]]
    product_meta = _product_meta(artifacts)
    risks = _risks(artifacts, product_dir)

    return {
        "version": "1.0",
        "generated_at": _now(),
        "product": product_meta,
        "nodes": nodes,
        "edges": edges,
        "risks": risks,
        "parse_errors": parse_errors,
    }


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


def write_snapshot(graph: Dict[str, Any], root: Path) -> Path:
    """Persist a graph snapshot under docs/product/visuals/.snapshots/<ISO>.json."""
    snap_dir = root / "docs" / "product" / "visuals" / ".snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = snap_dir / f"{ts}.json"
    path.write_text(json.dumps({"snapshot_at": graph["generated_at"], **graph}, indent=2, ensure_ascii=False), encoding="utf-8")
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
        print(json.dumps({"node": args.downstream, "downstream": ids}, indent=2, ensure_ascii=False))
        return 0

    if args.snapshot:
        snap = write_snapshot(graph, root)
        graph["__snapshot_path"] = str(snap.relative_to(root))

    print(json.dumps(graph, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
