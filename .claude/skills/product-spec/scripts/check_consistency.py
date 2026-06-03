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
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from spec_graph import (
    build_graph,
    _now,
    ID_PATTERN_BY_TYPE,
    make_finding as _f,
    resolve_ac as _resolve_ac,
)

# TIME / RISK / COMPETITION checks live in focused sibling modules.
from check_consistency_time import (
    check_target_date_shape as _check_target_date_shape,
    check_depends_on_type as _check_depends_on_type,
    time_child_late as _time_child_late,
    dep_order as _dep_order,
    DEPENDS_ON_ALLOWED_TYPES,
    # Re-exported: callers that imported _parse_iso_date from this module directly
    # (time_realism_anchors, time_advisory, status) continue to resolve here.
    parse_iso_date as _parse_iso_date,
)
from check_consistency_risk import (
    check_risks as _check_risks,
    risk_high_ratio as _risk_high_ratio,
    risk_blindspot as _risk_blindspot,
    RISK_HIGH_RATIO,
    RISK_BLINDSPOT_MIN_STORIES,
)
from check_consistency_competition import (
    check_competitors as _check_competitors,
    check_competitive_parity as _check_competitive_parity,
    COMPETITIVE_PARITY_ALLOWED_TYPES,
    COMP_ID_PATTERN,
    COMPETITION_ENUMS,
)

configure_utf8_console()


ENUMS = {
    "status": {"draft", "review", "approved"},
    "scope": {"in", "out", "core-value"},
    "moscow": {"must", "should", "could", "wont"},
    "horizon": {"now", "next", "later"},
    "size": {"S", "M", "L"},
    "lang": {"en", "vi"},
    # Risk-entry sub-field enums. Distinct keys from the artifact-level `status`
    # above: a risk's `status` is open|mitigated|accepted, NOT the artifact's
    # draft|review|approved lifecycle. Validated per-entry in check_risks().
    "risk_impact": {"low", "med", "high"},
    "risk_likelihood": {"low", "med", "high"},
    "risk_status": {"open", "mitigated", "accepted"},
    # COMPETITION enums. `threat` is a BRD competitor's threat tier;
    # `competitive_parity` is a PRD's per-competitor parity verdict.
    "competitor_threat": {"low", "med", "high"},
    "competitive_parity": {"ahead", "parity", "behind", "none"},
}

# List-typed frontmatter fields. If a generate-templates regression (or a
# manual hand-edit) leaves these as a bare scalar, downstream renderers
# iterate it per character and emit phantom personas / dangling links.
LIST_FIELDS = (
    "personas",
    "metrics",
    "brd_goals",
    "risks",
    "acceptance_criteria",
)

# Soft cap surfaced as a warn during PO interview. Brainstorm §3 + §11 +
# interview-vision V2 set "cap 2-4 (soft)".
PERSONA_SOFT_CAP = 4

STATUS_ORDER = {"draft": 0, "review": 1, "approved": 2}

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _parse_semver(v: Any) -> Optional[tuple]:
    if not isinstance(v, str):
        return None
    m = _SEMVER_RE.match(v.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def check(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    id_to_nodes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for n in graph["nodes"]:
        id_to_nodes[n["id"]].append(n)

    for nid, ns in id_to_nodes.items():
        if len(ns) > 1:
            # Skip sentinel values: two artifacts with missing/invalid IDs are a
            # separate invalid_id finding each; reporting them as a "duplicate"
            # produces a misleading dup_id <missing-id>/<invalid-id> false positive.
            if nid in ("<missing-id>", "<invalid-id>"):
                continue
            files = sorted({n.get("file") for n in ns if n.get("file")})
            carrier = {"id": nid, "file": files[0] if files else None}
            findings.append(_f(
                "dup_id", "error", carrier,
                f"Duplicate ID {nid} appears in {files}.",
                files=list(files),
            ))

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
            # Guard the set-membership test: an unhashable value would raise
            # TypeError on `v not in <set>`. Surface it as invalid_type.
            if isinstance(v, (list, dict)):
                findings.append(_f("invalid_type", "error", n, f"Field {field}={v!r} must be a single enum value; got {type(v).__name__}.", field=field, value=v))
            elif v not in ENUMS[field]:
                findings.append(_f("unknown_enum", "error", n, f"Field {field}={v!r} not in {sorted(ENUMS[field])}.", field=field, value=v))

        for field in LIST_FIELDS:
            v = n.get(field)
            if v is None:
                continue
            if not isinstance(v, list):
                findings.append(_f(
                    "invalid_type",
                    "error",
                    n,
                    f"Field {field}={v!r} must be a YAML list; got {type(v).__name__}.",
                    field=field,
                    value=v,
                ))

        findings.extend(_check_risks(n))
        findings.extend(_check_target_date_shape(n))
        findings.extend(_check_depends_on_type(n))
        findings.extend(_check_competitive_parity(n, graph))

        personas = n.get("personas")
        if isinstance(personas, list) and len(personas) > PERSONA_SOFT_CAP:
            findings.append(_f(
                "persona_cap_exceeded",
                "warn",
                n,
                f"{n['id']} declares {len(personas)} personas; soft cap is {PERSONA_SOFT_CAP}. "
                f"Consider narrowing to the primary buyers.",
                count=len(personas),
                cap=PERSONA_SOFT_CAP,
            ))

        if ntype == "story":
            ac = _resolve_ac(n)
            if not ac:
                findings.append(_f("missing_ac", "error", n, "Story has no acceptance_criteria."))
            elif len(ac) < 2:
                findings.append(_f("low_ac_count", "warn", n, f"Story has {len(ac)} acceptance criteria; >=2 recommended.", count=len(ac)))

        # A BRD goal must carry at least one success metric (frontmatter-and-id-spec:
        # `metrics` "required, >=1 metric slug"). Iterate `type:goal` nodes (metrics are
        # populated onto goal nodes by spec_graph._node_from_goal) — NOT the LIST_FIELDS
        # type loop, which only checks shape. `error` mirrors missing_ac. A non-empty list
        # passes; None/[] fails. (An invalid non-list `metrics` is already an invalid_type.)
        if ntype == "goal":
            metrics = n.get("metrics")
            # Fire on a missing key (None) OR an empty list; stay silent on a non-empty list.
            # (Parenthesized for clarity — a non-list `metrics` is already an invalid_type above.)
            if metrics is None or (isinstance(metrics, list) and not metrics):
                findings.append(_f(
                    "goal_without_metric", "error", n,
                    f"BRD goal {nid} has no success metric; at least one metric slug is required.",
                ))

    findings.extend(_status_inconsistency(graph))
    findings.extend(_version_inconsistency(graph))
    findings.extend(_self_reference(graph))
    findings.extend(_session_md_gitignore(graph))
    findings.extend(_risk_high_ratio(graph))
    findings.extend(_risk_blindspot(graph))
    findings.extend(_time_child_late(graph))
    findings.extend(_dep_order(graph))
    findings.extend(_check_competitors(graph))
    return findings


def _version_inconsistency(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flag any child whose semver `version` exceeds its parent's.

    Only flags when BOTH versions parse cleanly so a missing or malformed
    `version:` is silently ignored (the dedicated parse check handles it).
    """
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for n in graph["nodes"]:
        parent_id = n.get("epic") or n.get("prd")
        if not parent_id:
            continue
        parent = nodes_by_id.get(parent_id)
        if not parent:
            continue
        cv = _parse_semver(n.get("version"))
        pv = _parse_semver(parent.get("version"))
        if cv is None or pv is None:
            continue
        if cv > pv:
            findings.append(_f(
                "version_inconsistency",
                "warn",
                n,
                f"{n['id']} version {n.get('version')} exceeds parent {parent['id']} version {parent.get('version')}.",
                parent_id=parent["id"],
                child_version=n.get("version"),
                parent_version=parent.get("version"),
            ))
    return findings


def _self_reference(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flag any artifact whose parent reference points at itself.

    Real-world rare but a common LLM hallucination when --auto reassigns IDs.
    """
    findings: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        nid = n.get("id")
        if not nid:
            continue
        for key in ("epic", "prd"):
            ref = n.get(key)
            if ref == nid:
                findings.append(_f(
                    "self_reference",
                    "error",
                    n,
                    f"{nid} references itself via `{key}: {nid}`.",
                    field=key,
                ))
        brd_goals = n.get("brd_goals") or []
        if isinstance(brd_goals, list) and nid in brd_goals:
            findings.append(_f(
                "self_reference",
                "error",
                n,
                f"{nid} references itself in `brd_goals`.",
                field="brd_goals",
            ))
    return findings


def _session_md_gitignore(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when a `.gitignore` pattern likely excludes `.session.md`.

    §16 mandates `.session.md` be committed for cross-machine resume.
    Best-effort only; a false positive is acceptable since the finding is `warn`.
    """
    findings: List[Dict[str, Any]] = []
    root_path_raw = graph.get("root_path")
    if not root_path_raw:
        return findings
    root = Path(root_path_raw)
    session = root / "docs" / "product" / ".session.md"
    gitignore = root / ".gitignore"
    if not gitignore.exists() or not session.exists():
        return findings
    try:
        patterns = gitignore.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return findings
    for raw in patterns:
        p = raw.strip()
        if not p or p.startswith("#"):
            continue
        if ".session.md" in p or p in ("*.md", "docs/product/**", "docs/**"):
            findings.append({
                "check": "session_md_gitignored",
                "severity": "warn",
                "artifact_id": None,
                "file": ".gitignore",
                "detail": (
                    f".gitignore pattern {p!r} likely excludes docs/product/.session.md. "
                    f"§16 requires the session file to be committed for cross-machine resume."
                ),
                "context": {"pattern": p},
            })
            break
    return findings


def _status_inconsistency(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}

    def _flag(child: Dict[str, Any], parent: Dict[str, Any]) -> None:
        child_status = child.get("status")
        parent_status = parent.get("status")
        cs = STATUS_ORDER.get(child_status if isinstance(child_status, str) else "", -1)
        ps = STATUS_ORDER.get(parent_status if isinstance(parent_status, str) else "", -1)
        if cs > ps and cs >= 0 and ps >= 0:
            findings.append(_f(
                "status_inconsistency",
                "warn",
                child,
                f"{child['id']} status={child.get('status')!r} is more advanced than parent {parent['id']} status={parent.get('status')!r}.",
                parent_id=parent["id"],
            ))

    for n in graph["nodes"]:
        parent_id = n.get("epic") or n.get("prd")
        if parent_id:
            parent = nodes_by_id.get(parent_id)
            if parent:
                _flag(n, parent)

        if n.get("type") == "prd":
            brd_goals = n.get("brd_goals")
            if not isinstance(brd_goals, list):
                continue
            for gid in brd_goals:
                if not isinstance(gid, str):
                    continue
                goal = nodes_by_id.get(gid)
                if goal:
                    _flag(n, goal)

    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()

    graph = build_graph(root)

    # Augment story nodes with their acceptance_criteria from frontmatter
    # (graph nodes intentionally don't carry AC by default; load lazily).
    _enrich_with_ac(graph, root)

    findings = check(graph)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "checked_at": _now(),
        "findings": findings,
        "graph": graph,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
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
