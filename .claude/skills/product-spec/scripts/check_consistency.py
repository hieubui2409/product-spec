#!/usr/bin/env python3
"""
check_consistency — structural consistency checks. No judgment.

Detects:
- missing_ac / low_ac_count   (stories without enough acceptance criteria)
- invalid_id                  (ID does not match parent-scoped grammar)
- dup_id                      (two artifacts share the same ID)
- unknown_enum                (closed-enum field with disallowed value)
- status_inconsistency        (child approved under draft parent, etc.)

Emits findings JSON per validation-rules-spec.md. Always exits 0.

CLI:
    check_consistency.py --root <project-dir>
"""

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from encoding_utils import configure_utf8_console
from spec_graph import build_graph

configure_utf8_console()


ID_PATTERN_BY_TYPE = {
    "goal": re.compile(r"^BRD-G[0-9]+$"),
    "prd": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}$"),
    "epic": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+$"),
    "story": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+-S[0-9]+$"),
}

ENUMS = {
    "status": {"draft", "review", "approved"},
    "scope": {"in", "out", "core-value"},
    "moscow": {"must", "should", "could", "wont"},
    "horizon": {"now", "next", "later"},
    "size": {"S", "M", "L"},
    "lang": {"en", "vi"},
}

STATUS_ORDER = {"draft": 0, "review": 1, "approved": 2}


def check(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    id_to_nodes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for n in graph["nodes"]:
        id_to_nodes[n["id"]].append(n)

    for nid, ns in id_to_nodes.items():
        if len(ns) > 1:
            files = sorted({n.get("file") for n in ns if n.get("file")})
            findings.append({
                "check": "dup_id",
                "severity": "error",
                "artifact_id": nid,
                "file": None,
                "detail": f"Duplicate ID {nid} appears in {files}.",
                "context": {"files": list(files)},
            })

    for n in graph["nodes"]:
        ntype = n.get("type")
        nid = n.get("id") or ""
        pattern = ID_PATTERN_BY_TYPE.get(ntype)
        if pattern and not pattern.match(nid):
            findings.append(_f("invalid_id", "error", n, f"ID {nid!r} does not match expected pattern for {ntype}.", expected_pattern=pattern.pattern))

        for field in ("status", "scope", "moscow", "horizon", "size", "lang"):
            v = n.get(field)
            if v is None:
                continue
            if v not in ENUMS[field]:
                findings.append(_f("unknown_enum", "error", n, f"Field {field}={v!r} not in {sorted(ENUMS[field])}.", field=field, value=v))

        if ntype == "story":
            ac = _resolve_ac(n)
            if not ac:
                findings.append(_f("missing_ac", "error", n, "Story has no acceptance_criteria."))
            elif len(ac) < 2:
                findings.append(_f("low_ac_count", "warn", n, f"Story has {len(ac)} acceptance criteria; >=2 recommended.", count=len(ac)))

    findings.extend(_status_inconsistency(graph))
    return findings


def _resolve_ac(node: Dict[str, Any]) -> List[Any]:
    raw = node.get("acceptance_criteria")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [x for x in raw if x not in (None, "")]
    return []


def _status_inconsistency(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for n in graph["nodes"]:
        parent_id = n.get("epic") or n.get("prd")
        if not parent_id:
            continue
        parent = nodes_by_id.get(parent_id)
        if not parent:
            continue
        cs = STATUS_ORDER.get(n.get("status") or "", -1)
        ps = STATUS_ORDER.get(parent.get("status") or "", -1)
        if cs > ps and cs >= 0 and ps >= 0:
            findings.append(_f(
                "status_inconsistency",
                "warn",
                n,
                f"{n['id']} status={n.get('status')!r} is more advanced than parent {parent_id} status={parent.get('status')!r}.",
                parent_id=parent_id,
            ))
    return findings


def _f(check_id: str, severity: str, node: Dict[str, Any], detail: str, **context) -> Dict[str, Any]:
    return {
        "check": check_id,
        "severity": severity,
        "artifact_id": node.get("id"),
        "file": node.get("file"),
        "detail": detail,
        "context": context or None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()

    parsed_node_extras: Dict[str, Any] = {}
    graph = build_graph(root)

    # Augment story nodes with their acceptance_criteria from frontmatter
    # (graph nodes intentionally don't carry AC by default; load lazily).
    _enrich_with_ac(graph, root)

    findings = check(graph)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "checked_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
        "findings": findings,
        "graph": graph,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def _enrich_with_ac(graph: Dict[str, Any], root: Path) -> None:
    """Re-parse story files to attach acceptance_criteria onto graph nodes."""
    from frontmatter_parser import parse_file  # avoid top-level cycle on tests
    product_dir = root / "docs" / "product"
    for n in graph["nodes"]:
        if n.get("type") != "story":
            continue
        f = n.get("file")
        if not f:
            continue
        result = parse_file(product_dir / f)
        if result["ok"]:
            n["acceptance_criteria"] = result["frontmatter"].get("acceptance_criteria") or []


if __name__ == "__main__":
    sys.exit(main())
