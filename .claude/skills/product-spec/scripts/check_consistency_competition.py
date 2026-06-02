"""
check_consistency_competition — COMPETITION-dimension structural checks for
check_consistency.

All deterministic — closed-enum membership + ID-grammar regex + id-set lookup
against graph["competitors"]. No LLM judgment (G-B1): the `competitive_drift`
warn is the LLM's job. Competitor IDENTITY lives ONCE in the BRD's
`competitors:` list (materialized onto graph["competitors"]).
"""

import re
from typing import Any, Dict, List

from spec_graph import make_finding as _f, competitor_id_to_name

# Competitor ID grammar: `COMP-<SLUG>` (same parent-scoped discipline as artifacts).
COMP_ID_PATTERN = re.compile(r"^COMP-[A-Z][A-Z0-9-]{0,15}$")

# COMPETITION enums.
COMPETITION_ENUMS = {
    "competitor_threat": {"low", "med", "high"},
    "competitive_parity": {"ahead", "parity", "behind", "none"},
}

# `competitive_parity` is a PRD-level map only; on any other artifact type it is
# misplaced → reuses `invalid_type` (symmetric with DEPENDS_ON_ALLOWED_TYPES).
COMPETITIVE_PARITY_ALLOWED_TYPES = ("prd",)


def _competitor_ids(graph: Dict[str, Any]) -> set:
    """The set of well-formed BRD competitor ids — the resolve target for every
    PRD `competitive_parity` key. Delegates to the single DRY home
    (spec_graph.competitor_id_to_name) so the 'resolvable competitor' rule has
    one authority shared with the drift anchors."""
    return set(competitor_id_to_name(graph))


def check_competitors(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate the BRD `competitors:` list (the DRY identity home).

    Three deterministic checks:
      - a non-mapping entry reuses the EXISTING `invalid_type` finding (F7).
      - `threat` validated against its closed enum → `unknown_enum`.
      - the competitor `id` must match the `COMP-<SLUG>` grammar → `invalid_id`.
    """
    findings: List[Dict[str, Any]] = []
    competitors = graph.get("competitors")
    if not isinstance(competitors, list):
        return findings
    # A synthetic BRD-scoped node carrier so _f() attributes the finding to the
    # BRD file (competitors have no node of their own). brd.md is the single home.
    brd_carrier = {"id": "BRD", "file": "brd.md"}
    seen_ids: set = set()
    for entry in competitors:
        if not isinstance(entry, dict):
            findings.append(_f(
                "invalid_type", "error", brd_carrier,
                f"competitors[] entry {entry!r} must be a YAML mapping with an "
                f"`id`/`name`/`threat`; got {type(entry).__name__}.",
                field="competitors", value=entry,
            ))
            continue
        threat = entry.get("threat")
        if isinstance(threat, (list, dict)):
            findings.append(_f(
                "invalid_type", "error", brd_carrier,
                f"competitor threat={threat!r} must be a single enum value; got {type(threat).__name__}.",
                field="competitors[].threat", value=threat,
            ))
        elif threat is not None and threat not in COMPETITION_ENUMS["competitor_threat"]:
            findings.append(_f(
                "unknown_enum", "error", brd_carrier,
                f"competitor threat={threat!r} not in {sorted(COMPETITION_ENUMS['competitor_threat'])}.",
                field="competitors[].threat", value=threat,
            ))
        cid = entry.get("id")
        if not (isinstance(cid, str) and COMP_ID_PATTERN.match(cid)):
            findings.append(_f(
                "invalid_id", "error", brd_carrier,
                f"competitor id {cid!r} does not match the COMP-<SLUG> grammar "
                f"({COMP_ID_PATTERN.pattern}).",
                field="competitors[].id", value=cid, expected_pattern=COMP_ID_PATTERN.pattern,
            ))
        else:
            # Two competitor entries sharing one COMP- id make a PRD parity key
            # resolve ambiguously. Flag the repeat — mirrors the artifact-level
            # dup_id loop in check_consistency.check().
            if cid in seen_ids:
                findings.append(_f(
                    "dup_id", "error", brd_carrier,
                    f"Duplicate competitor id {cid!r} in the BRD competitors: list.",
                    field="competitors[].id", value=cid,
                ))
            seen_ids.add(cid)
    return findings


def check_competitive_parity(node: Dict[str, Any], graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate one PRD's `competitive_parity` ID-keyed map.

    Three deterministic checks:
      - the whole field must be a mapping; a non-mapping reuses `invalid_type`.
      - each KEY must resolve to a `graph["competitors"][].id` → else `unknown_ref`.
      - each VALUE must be in the parity enum → `unknown_enum`.
    Absent → clean (optional; a v1 PRD has no parity map).
    """
    cp = node.get("competitive_parity")
    if cp is None:
        return []
    if node.get("type") not in COMPETITIVE_PARITY_ALLOWED_TYPES:
        return [_f(
            "invalid_type", "error", node,
            f"competitive_parity is only valid on {' or '.join(COMPETITIVE_PARITY_ALLOWED_TYPES)}; "
            f"{node.get('id')} is a {node.get('type')}.",
            field="competitive_parity", value=cp,
        )]
    if not isinstance(cp, dict):
        return [_f(
            "invalid_type", "error", node,
            f"competitive_parity={cp!r} must be an ID-keyed mapping "
            f"(e.g. {{COMP-ACME: behind}}); got {type(cp).__name__}.",
            field="competitive_parity", value=cp,
        )]
    findings: List[Dict[str, Any]] = []
    known = _competitor_ids(graph)
    for comp_id, parity in cp.items():
        if comp_id not in known:
            findings.append(_f(
                "unknown_ref", "error", node,
                f"competitive_parity key {comp_id!r} does not resolve to any BRD "
                f"competitor id; competitor identity lives in the BRD's competitors: list.",
                field="competitive_parity", ref=comp_id,
            ))
        if isinstance(parity, (list, dict)):
            findings.append(_f(
                "invalid_type", "error", node,
                f"competitive_parity[{comp_id!r}]={parity!r} must be a single parity "
                f"enum value; got {type(parity).__name__}.",
                field="competitive_parity", value=parity,
            ))
        elif parity is not None and parity not in COMPETITION_ENUMS["competitive_parity"]:
            findings.append(_f(
                "unknown_enum", "error", node,
                f"competitive_parity[{comp_id!r}]={parity!r} not in "
                f"{sorted(COMPETITION_ENUMS['competitive_parity'])}.",
                field="competitive_parity", value=parity,
            ))
    return findings
