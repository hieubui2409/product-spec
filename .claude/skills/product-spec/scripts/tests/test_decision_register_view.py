"""Tests for decision_register_view — the presentation layer over the Decision Register.

Covers:
- filter_by_affects: filter records by artifact linkage field
- render_supersede_chain: transitive chain resolution
- render_dashboard_row: row shape and content
- Negative: empty affects match, cycle safety, dangling supersede ref

Fixtures are synthetic only; no real PO data.
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from decision_register import parse_decisions  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture helpers (reuse the same _seed/_record pattern from test_decision_register)
# ---------------------------------------------------------------------------

def _decisions_path(root: Path) -> Path:
    return root / "docs" / "product" / "decisions.md"


def _seed(root: Path, *records: str) -> Path:
    """Write a decisions.md with given record blocks."""
    p = _decisions_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    header = "# Decision Register\n\n"
    p.write_text(header + "\n".join(records) + ("\n" if records else ""), encoding="utf-8")
    return p


def _record(
    dec_id: str,
    status: str = "active",
    supersedes: str = "",
    affects: str = "",
) -> str:
    sup = f"supersedes: {supersedes}\n" if supersedes else ""
    aff = f"affects: {affects}\n" if affects else ""
    return (
        "---\n"
        f"id: {dec_id}\n"
        f"status: {status}\n"
        "date: 2026-06-01\n"
        f"{aff}"
        f"{sup}"
        "---\n"
        f"## {dec_id} — sample ruling\n\n"
        "Rationale prose here.\n"
    )


# ---------------------------------------------------------------------------
# Test 1: filter_by_affects returns only records whose affects matches artifact
# ---------------------------------------------------------------------------

def test_list_affects_filters_by_artifact(tmp_path):
    """filter_by_affects(records, 'PRD-AUTH') returns only the AUTH-affecting DECs."""
    from decision_register_view import filter_by_affects

    _seed(
        tmp_path,
        _record("DEC-1", affects="PRD-AUTH"),
        _record("DEC-2", affects="PRD-PAY"),
        _record("DEC-3", affects="PRD-AUTH"),
        _record("DEC-4"),  # no affects
    )
    records = parse_decisions(tmp_path)
    result = filter_by_affects(records, "PRD-AUTH")
    ids = [r["id"] for r in result]
    assert ids == ["DEC-1", "DEC-3"]
    # PRD-PAY not in result
    assert all(r["affects"] == "PRD-AUTH" for r in result)


# ---------------------------------------------------------------------------
# Test 2: supersede chain resolves transitively in order (oldest→newest)
# ---------------------------------------------------------------------------

def test_supersede_chain_resolves_transitively(tmp_path):
    """DEC-A superseded-by DEC-B superseded-by DEC-C → chain A→B→C rendered."""
    from decision_register_view import render_supersede_chain

    _seed(
        tmp_path,
        _record("DEC-1", status="superseded"),
        _record("DEC-2", status="superseded", supersedes="DEC-1"),
        _record("DEC-3", status="active", supersedes="DEC-2"),
    )
    records = parse_decisions(tmp_path)
    chain = render_supersede_chain("DEC-1", records)
    # The chain must mention all three IDs in order
    assert "DEC-1" in chain
    assert "DEC-2" in chain
    assert "DEC-3" in chain
    # DEC-1 appears before DEC-2 appears before DEC-3
    assert chain.index("DEC-1") < chain.index("DEC-2") < chain.index("DEC-3")


# ---------------------------------------------------------------------------
# Test 3: render_dashboard_row returns correct shape and values
# ---------------------------------------------------------------------------

def test_dashboard_summary_counts(tmp_path):
    """render_dashboard_summary returns correct per-status counts."""
    from decision_register_view import render_dashboard_summary

    _seed(
        tmp_path,
        _record("DEC-1", status="active"),
        _record("DEC-2", status="active"),
        _record("DEC-3", status="superseded"),
        _record("DEC-4", status="active"),
        _record("DEC-5", status="superseded"),
    )
    records = parse_decisions(tmp_path)
    summary = render_dashboard_summary(records)
    assert summary["total"] == 5
    assert summary["by_status"]["active"] == 3
    assert summary["by_status"]["superseded"] == 2
    # Latest ruling is the last record (DEC-5 by file order)
    assert summary["latest_id"] == "DEC-5"


# ---------------------------------------------------------------------------
# Test 4: --affects PRD-NONE with no matching DEC → empty result, no crash
# ---------------------------------------------------------------------------

def test_affects_no_match_empty(tmp_path):
    """filter_by_affects with no matching artifact returns empty list without error."""
    from decision_register_view import filter_by_affects

    _seed(
        tmp_path,
        _record("DEC-1", affects="PRD-AUTH"),
        _record("DEC-2", affects="PRD-PAY"),
    )
    records = parse_decisions(tmp_path)
    result = filter_by_affects(records, "PRD-NONE")
    assert result == []


# ---------------------------------------------------------------------------
# Test 5 (negative / red-team): cyclic supersede reference terminates (no infinite loop)
# ---------------------------------------------------------------------------

def test_supersede_cycle_no_infinite_loop(tmp_path):
    """Mutual cycle DEC-A↔DEC-B → chain traversal terminates; no RecursionError."""
    from decision_register_view import render_supersede_chain

    # Build records manually with a cycle; use raw file write so the register
    # append-path's duplicate/dangling guard is bypassed (synthetic fixture only).
    p = _decisions_path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "# Decision Register\n\n"
        "---\n"
        "id: DEC-10\n"
        "status: active\n"
        "date: 2026-06-01\n"
        "supersedes: DEC-11\n"
        "---\n"
        "## DEC-10 — cycle node A\n\nRationale.\n"
        "\n"
        "---\n"
        "id: DEC-11\n"
        "status: active\n"
        "date: 2026-06-01\n"
        "supersedes: DEC-10\n"
        "---\n"
        "## DEC-11 — cycle node B\n\nRationale.\n",
        encoding="utf-8",
    )
    records = parse_decisions(tmp_path)
    # Must not raise RecursionError or loop forever.
    chain = render_supersede_chain("DEC-10", records)
    # Both nodes appear; the chain is finite (cycle broken).
    assert "DEC-10" in chain
    assert "DEC-11" in chain


# ---------------------------------------------------------------------------
# Test 6 (negative / red-team): dangling supersede reference — fail-soft, no crash
# ---------------------------------------------------------------------------

def test_dangling_supersede_reference(tmp_path):
    """DEC referencing a non-existent superseded id → fail-soft, chain rendered with note."""
    from decision_register_view import render_supersede_chain

    _seed(
        tmp_path,
        _record("DEC-20", supersedes="DEC-999"),  # DEC-999 does not exist
    )
    records = parse_decisions(tmp_path)
    # Must not raise; should return a string describing the dangling link.
    chain = render_supersede_chain("DEC-20", records)
    assert "DEC-20" in chain
    # The dangling target is noted in some way (broken or missing marker).
    assert "DEC-999" in chain
