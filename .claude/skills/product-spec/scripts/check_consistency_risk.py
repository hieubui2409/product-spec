"""
check_consistency_risk — RISK-dimension structural checks for check_consistency.

Validates each entry of a node's `risks:` list (enum membership, shape),
and graph-level risk health signals (high-ratio warning, blind-spot warning).
All deterministic — no LLM judgment.
"""

from typing import Any, Dict, List

from spec_graph import make_finding as _f, matching_child_counts

# Risk-entry sub-field enums (distinct from the artifact-level `status`).
RISK_ENUMS = {
    "risk_impact": {"low", "med", "high"},
    "risk_likelihood": {"low", "med", "high"},
    "risk_status": {"open", "mitigated", "accepted"},
}

# When more than this fraction of an artifact's risks sit at `impact: high`,
# `risk_high_ratio` warns (the risk register is top-heavy).
RISK_HIGH_RATIO = 0.5

# An epic with at least this many child stories but zero declared risks trips
# `risk_blindspot`. The child-story count is a deterministic graph traversal.
RISK_BLINDSPOT_MIN_STORIES = 5


def check_risks(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate each entry of a node's `risks:` list.

    Two structural checks, both deterministic:
      - a non-dict entry reuses the EXISTING `invalid_type` finding rather than
        inventing a new `invalid_shape` — keeps the catalog small.
      - `impact` / `likelihood` / `status` validated against their closed enums
        → `unknown_enum`. A risk's `status` is open|mitigated|accepted,
        distinct from the artifact status.
    """
    raw = node.get("risks")
    if not isinstance(raw, list):
        return []
    findings: List[Dict[str, Any]] = []
    risk_field_to_enum = {
        "impact": "risk_impact",
        "likelihood": "risk_likelihood",
        "status": "risk_status",
    }
    for entry in raw:
        if not isinstance(entry, dict):
            findings.append(_f(
                "invalid_type",
                "error",
                node,
                f"risks[] entry {entry!r} must be a YAML mapping with a "
                f"`description`; got {type(entry).__name__}.",
                field="risks",
                value=entry,
            ))
            continue
        for risk_field, enum_key in risk_field_to_enum.items():
            val = entry.get(risk_field)
            if val is None:
                continue
            if isinstance(val, (list, dict)):
                # Unhashable value where a scalar enum is expected — guard the
                # membership test below from raising TypeError (fail-soft).
                findings.append(_f(
                    "invalid_type",
                    "error",
                    node,
                    f"risk {risk_field}={val!r} must be a single enum value; got {type(val).__name__}.",
                    field=f"risks[].{risk_field}",
                    value=val,
                ))
            elif val not in RISK_ENUMS[enum_key]:
                findings.append(_f(
                    "unknown_enum",
                    "error",
                    node,
                    f"risk {risk_field}={val!r} not in {sorted(RISK_ENUMS[enum_key])}.",
                    field=f"risks[].{risk_field}",
                    value=val,
                ))
    return findings


def risk_high_ratio(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when more than RISK_HIGH_RATIO of an artifact's risks are `high`
    impact. Per-node, deterministic count; only artifacts with at least one
    risk are considered."""
    findings: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        risks = n.get("risks")
        if not isinstance(risks, list):
            continue
        dict_risks = [r for r in risks if isinstance(r, dict)]
        total = len(dict_risks)
        if total == 0:
            continue
        high = sum(1 for r in dict_risks if r.get("impact") == "high")
        if high / total > RISK_HIGH_RATIO:
            pct = round(high / total * 100)
            findings.append(_f(
                "risk_high_ratio",
                "warn",
                n,
                f"{n['id']} has {high}/{total} risks ({pct}%) at impact=high; "
                f"more than {round(RISK_HIGH_RATIO * 100)}% — review whether the "
                f"register is over-rated or the feature is genuinely high-exposure.",
                high=high,
                total=total,
            ))
    return findings


def risk_blindspot(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn for an epic with >= RISK_BLINDSPOT_MIN_STORIES child stories and zero
    declared risks. The child-story count is a deterministic graph traversal —
    NOT an LLM judgment — keeping the check in the script layer per the
    Script-vs-LLM split."""
    findings: List[Dict[str, Any]] = []
    child_counts = matching_child_counts(graph)
    for n in graph["nodes"]:
        if n.get("type") != "epic":
            continue
        risks = n.get("risks")
        has_risk = isinstance(risks, list) and any(isinstance(r, dict) for r in risks)
        if has_risk:
            continue
        story_count = child_counts.get(n["id"], 0)
        if story_count >= RISK_BLINDSPOT_MIN_STORIES:
            findings.append(_f(
                "risk_blindspot",
                "warn",
                n,
                f"{n['id']} has {story_count} child stories but no declared risks. "
                f"A feature of this size with an empty risk register is a blind spot.",
                story_count=story_count,
            ))
    return findings
