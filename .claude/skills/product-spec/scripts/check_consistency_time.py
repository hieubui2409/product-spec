"""
check_consistency_time — TIME-dimension structural checks for check_consistency.

All checks compare dates already on the graph (never the wall clock).
The wall-clock `overdue` advisory lives in time_advisory.py, outside this gate.
"""

import datetime as dt
import re
from typing import Any, Dict, List

from spec_graph import make_finding as _f

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Allowed artifact types for depends_on (non-empty list on any other type
# reuses the existing invalid_type finding).
DEPENDS_ON_ALLOWED_TYPES = ("prd", "epic")


def parse_iso_date(v: Any):
    """Coerce a node's target_date to a datetime.date for comparison, or None.

    PyYAML already parses a valid `YYYY-MM-DD` to datetime.date (or datetime).
    A str only reaches here if it slipped the shape gate; parse it leniently
    and return None on failure so a malformed value (already flagged invalid_type)
    simply drops out of the ordering checks.
    """
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str) and _ISO_DATE_RE.match(v.strip()):
        try:
            return dt.date.fromisoformat(v.strip())
        except ValueError:
            return None
    return None


def check_target_date_shape(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """target_date must be an ISO calendar date (YYYY-MM-DD). Absent is clean.
    A value PyYAML left as a non-ISO string is invalid_type."""
    v = node.get("target_date")
    if v is None:
        return []
    if isinstance(v, (dt.date, dt.datetime)):
        return []
    if isinstance(v, str) and _ISO_DATE_RE.match(v.strip()):
        try:
            dt.date.fromisoformat(v.strip())
            return []
        except ValueError:
            pass
    return [_f(
        "invalid_type", "error", node,
        f"Field target_date={v!r} must be a valid ISO calendar date (YYYY-MM-DD).",
        field="target_date", value=v,
    )]


def check_depends_on_type(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """`depends_on` is allowed on PRD + Epic only. A non-empty list on any other
    artifact type reuses the EXISTING `invalid_type` finding (no new check id).
    An empty/absent list is always fine."""
    deps = node.get("depends_on")
    if not deps:
        return []
    if node.get("type") in DEPENDS_ON_ALLOWED_TYPES:
        return []
    return [_f(
        "invalid_type", "error", node,
        f"Field depends_on is only valid on {' or '.join(DEPENDS_ON_ALLOWED_TYPES)}; "
        f"{node['id']} is a {node.get('type')}.",
        field="depends_on", value=deps,
    )]


def time_child_late(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when a child's target_date is AFTER its parent's (an epic due after
    its PRD finishes is incoherent). Only fires when BOTH dates parse."""
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for n in graph["nodes"]:
        parent_id = n.get("epic") or n.get("prd")
        if not parent_id:
            continue
        parent = nodes_by_id.get(parent_id)
        if not parent:
            continue
        cd = parse_iso_date(n.get("target_date"))
        pd = parse_iso_date(parent.get("target_date"))
        if cd is None or pd is None:
            continue
        if cd > pd:
            findings.append(_f(
                "time_child_late", "warn", n,
                f"{n['id']} target_date {cd} is after parent {parent['id']} "
                f"target_date {pd}; a child cannot finish after its parent.",
                parent_id=parent["id"],
                child_target_date=str(cd),
                parent_target_date=str(pd),
            ))
    return findings


def dep_order(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when A depends_on B but A.target_date < B.target_date — A is due
    before the prerequisite it waits on. Only fires when BOTH dates parse."""
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for n in graph["nodes"]:
        ad = parse_iso_date(n.get("target_date"))
        if ad is None:
            continue
        for dep in n.get("depends_on") or []:
            target = nodes_by_id.get(dep)
            if not target:
                continue  # dep_dangling owns the missing-ID case
            bd = parse_iso_date(target.get("target_date"))
            if bd is None:
                continue
            if ad < bd:
                findings.append(_f(
                    "dep_order", "warn", n,
                    f"{n['id']} target_date {ad} is before its prerequisite "
                    f"{target['id']} target_date {bd}; A cannot complete before B.",
                    depends_on=dep,
                    target_date=str(ad),
                    prerequisite_target_date=str(bd),
                ))
    return findings
