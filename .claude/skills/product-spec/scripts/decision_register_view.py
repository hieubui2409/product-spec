#!/usr/bin/env python3
"""
decision_register_view — presentation layer over the Decision Register.

Focused sibling of decision_register (mirrors the check_consistency_* / render_html
sibling pattern): keeps decision_register.py flat by extracting all VIEW logic here.

Public API:
    filter_by_affects(records, artifact_id) -> List[Dict]
        Filter a record list to those whose `affects` field equals artifact_id.

    render_supersede_chain(dec_id, records) -> str
        Follow `supersedes` links transitively from dec_id, returning a human-readable
        chain string newest→oldest (e.g. "DEC-3 → DEC-2 → DEC-1"). Guards against cycles (visited-set)
        and dangling references (fail-soft: notes the missing target in the chain).

    render_dashboard_row(dec_id, record, chain_str) -> Dict
        Return a dashboard row dict: {id, status, date, title, chain}.

    render_dashboard_summary(records) -> Dict
        Return aggregate counts: {total, by_status, latest_id}.

Reuses parse_decisions() from decision_register — single DEC loader (DRY).
No new write path; append-only data model unchanged.
"""

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# filter_by_affects
# ---------------------------------------------------------------------------

def filter_by_affects(
    records: List[Dict[str, Any]],
    artifact_id: str,
) -> List[Dict[str, Any]]:
    """Return records whose `affects` field matches artifact_id exactly.

    Comparison is case-sensitive (artifact ids are canonical uppercase,
    e.g. 'PRD-AUTH'). Returns an empty list when no match — never crashes
    on a missing or empty `affects` field.
    """
    return [r for r in records if r.get("affects", "") == artifact_id]


# ---------------------------------------------------------------------------
# render_supersede_chain
# ---------------------------------------------------------------------------

def render_supersede_chain(
    dec_id: str,
    records: List[Dict[str, Any]],
) -> str:
    """Follow `supersedes` links transitively from dec_id and render the chain.

    The chain is rendered newest-to-oldest (the most recent ruling is the leftmost
    node): "DEC-3 → DEC-2 → DEC-1". The starting dec_id is the oldest node, so it
    reads rightmost.

    Cycle safety: a visited-set guards against DEC-A ↔ DEC-B mutual references;
    when a cycle is detected the traversal terminates and the repeated node is
    noted with a [cycle] marker.

    Dangling reference safety: when a `supersedes` target is not present in the
    register the chain renders that target with a [missing] marker and stops —
    never crashes (fail-soft per architecture decision).
    """
    # Build an index for O(1) lookup.
    by_id: Dict[str, Dict[str, Any]] = {r["id"]: r for r in records}

    visited: set = set()
    chain: List[str] = []
    current_id: Optional[str] = dec_id

    while current_id is not None:
        if current_id in visited:
            # Cycle detected — append cycle marker and stop.
            chain.append(f"{current_id} [cycle]")
            break
        visited.add(current_id)

        if current_id not in by_id:
            # Dangling reference — append missing marker and stop.
            chain.append(f"{current_id} [missing]")
            break

        chain.append(current_id)
        record = by_id[current_id]

        # Walk forward: find a record that supersedes the current one.
        # The `supersedes` field on a record points BACKWARDS (the record it
        # retired), so to walk FORWARD we look for a record whose `supersedes`
        # equals the current id.
        next_id: Optional[str] = None
        for r in records:
            if r.get("supersedes", "") == current_id and r["id"] != current_id:
                # Pick the first successor found (file order = append order).
                next_id = r["id"]
                break

        if next_id is None:
            # No forward successor found. Check if this record itself has a
            # `supersedes` pointing backward to a target that does not exist in
            # the register (dangling backward reference). Surface it as [missing].
            backward_target = record.get("supersedes", "")
            if backward_target and backward_target not in by_id:
                chain.append(f"{backward_target} [missing]")

        current_id = next_id

    # Rendered newest→oldest: the forward walk builds the chain oldest-first, so
    # reverse it for display (the most recent ruling reads leftmost). A terminal
    # [cycle]/[missing] marker sits at the newest tip where the walk stopped, so
    # it leads the reversed string — which is where the stop occurred.
    return " → ".join(reversed(chain))


# ---------------------------------------------------------------------------
# render_dashboard_row
# ---------------------------------------------------------------------------

def render_dashboard_row(
    dec_id: str,
    record: Dict[str, Any],
    chain_str: str,
) -> Dict[str, Any]:
    """Return a dashboard row dict for one DEC entry.

    Shape: {id, status, date, title, chain}. Suitable for JSON serialization
    and consumption by visualize.py / the --decision surface.
    """
    return {
        "id": dec_id,
        "status": record.get("status", "active"),
        "date": record.get("date", ""),
        "title": record.get("title", ""),
        "chain": chain_str,
    }


# ---------------------------------------------------------------------------
# render_dashboard_summary
# ---------------------------------------------------------------------------

def render_dashboard_summary(
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return aggregate counts over the full record list.

    Shape: {total, by_status: {status: count, ...}, latest_id}.
    latest_id is the id of the last record in file order (most recently appended),
    or None when the list is empty.
    """
    by_status: Dict[str, int] = {}
    for r in records:
        s = r.get("status", "active")
        by_status[s] = by_status.get(s, 0) + 1

    latest_id = records[-1]["id"] if records else None

    return {
        "total": len(records),
        "by_status": by_status,
        "latest_id": latest_id,
    }


# ---------------------------------------------------------------------------
# list_by_affects — convenience entry point called by decision_register CLI
# ---------------------------------------------------------------------------

def list_by_affects(
    records: List[Dict[str, Any]],
    artifact_id: str,
) -> List[Dict[str, Any]]:
    """Filter + enrich: return dashboard rows for all DECs affecting artifact_id.

    Each row includes the resolved supersede chain. Returns an empty list when
    no records match.
    """
    matching = filter_by_affects(records, artifact_id)
    rows = []
    for rec in matching:
        chain = render_supersede_chain(rec["id"], records)
        rows.append(render_dashboard_row(rec["id"], rec, chain))
    return rows
