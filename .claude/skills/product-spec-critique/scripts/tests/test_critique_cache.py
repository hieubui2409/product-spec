"""Tests for critique_cache.py — the JSON-dict stores (findings-index, critique-state,
humanized-cache) + the fence chokepoint. The file-per-key stores (web/lens) are
tested in test_critique_blob_cache.py. All reads tolerate missing/corrupt (empty/None,
never raise); all writes resolve through fs_guard before disk."""

import pytest

from critique_test_support import make_proj
import critique_cache as cc


# ---------------------------------------------------------------------------
# findings-index  (evidence-ID query cache, lossy: blockers + DEC-worthy)
# ---------------------------------------------------------------------------

def _finding(eid, severity="blocker", why="w", fix="f", dec_worthy=False):
    return {"evidence_id": eid, "severity": severity, "why": why, "fix": fix,
            "dec_worthy": dec_worthy}


def test_findings_index_upsert_then_load(tmp_path):
    proj = make_proj(tmp_path)
    cc.upsert_findings(proj, "260603-0001", "all", [_finding("PRD-AUTH")])
    idx = cc.load_index(proj)
    assert "PRD-AUTH@260603-0001" in idx
    entry = idx["PRD-AUTH@260603-0001"]
    assert entry["evidence_id"] == "PRD-AUTH"
    assert entry["severity"] == "blocker"
    assert entry["report_ts"] == "260603-0001"
    assert entry["scope"] == "all"


def test_findings_index_same_id_ts_overwrites(tmp_path):
    proj = make_proj(tmp_path)
    cc.upsert_findings(proj, "260603-0001", "all", [_finding("PRD-AUTH", why="old")])
    cc.upsert_findings(proj, "260603-0001", "all", [_finding("PRD-AUTH", why="new")])
    idx = cc.load_index(proj)
    assert len(idx) == 1
    assert idx["PRD-AUTH@260603-0001"]["why"] == "new"


def test_findings_index_different_ts_coexist(tmp_path):
    proj = make_proj(tmp_path)
    cc.upsert_findings(proj, "260603-0001", "all", [_finding("PRD-AUTH")])
    cc.upsert_findings(proj, "260603-0002", "all", [_finding("PRD-AUTH")])
    idx = cc.load_index(proj)
    assert "PRD-AUTH@260603-0001" in idx
    assert "PRD-AUTH@260603-0002" in idx


def test_findings_index_persists_finding_fingerprint(tmp_path):
    # N1: the new additive field round-trips through upsert → load.
    proj = make_proj(tmp_path)
    cc.upsert_findings(proj, "260603-0001", "all",
                       [{**_finding("PRD-AUTH:3"),
                         "finding_fingerprint": "abc123abc123abc1"}])
    entry = cc.load_index(proj)["PRD-AUTH:3@260603-0001"]
    assert entry["finding_fingerprint"] == "abc123abc123abc1"


def test_findings_index_legacy_row_tolerant(tmp_path):
    # Crit 4: a legacy finding with no finding_fingerprint key persists + loads
    # with the field defaulted to None (no KeyError on the missing key).
    proj = make_proj(tmp_path)
    cc.upsert_findings(proj, "260603-0001", "all", [_finding("PRD-AUTH:3")])
    entry = cc.load_index(proj)["PRD-AUTH:3@260603-0001"]
    assert entry.get("finding_fingerprint") is None


def test_findings_index_corrupt_returns_empty(tmp_path):
    proj = make_proj(tmp_path)
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "critique-findings-index.json").write_text("{ not json", encoding="utf-8")
    assert cc.load_index(proj) == {}


def test_findings_index_missing_returns_empty(tmp_path):
    proj = make_proj(tmp_path)
    assert cc.load_index(proj) == {}


# ---------------------------------------------------------------------------
# critique-state marker
# ---------------------------------------------------------------------------

def test_state_round_trip(tmp_path):
    proj = make_proj(tmp_path)
    cc.save_state(proj, "all", last_ts="260603-0001", provenance_hash="abc123",
                  blocker_count=2, drift_since=0)
    state = cc.load_state(proj)
    assert state["all"]["provenance_hash"] == "abc123"
    assert state["all"]["blocker_count"] == 2


def test_state_two_scopes_independent(tmp_path):
    proj = make_proj(tmp_path)
    cc.save_state(proj, "all", provenance_hash="aaa")
    cc.save_state(proj, "PRD-AUTH", provenance_hash="bbb")
    state = cc.load_state(proj)
    assert state["all"]["provenance_hash"] == "aaa"
    assert state["PRD-AUTH"]["provenance_hash"] == "bbb"


def test_state_missing_returns_empty(tmp_path):
    proj = make_proj(tmp_path)
    assert cc.load_state(proj) == {}


# ---------------------------------------------------------------------------
# humanized-output cache
# ---------------------------------------------------------------------------

def test_humanized_round_trip(tmp_path):
    proj = make_proj(tmp_path)
    cc.put_humanized(proj, "hash-of-consolidated", "humanized markdown")
    assert cc.get_humanized(proj, "hash-of-consolidated") == "humanized markdown"


def test_humanized_unknown_returns_none(tmp_path):
    proj = make_proj(tmp_path)
    assert cc.get_humanized(proj, "nope") is None


# ---------------------------------------------------------------------------
# fence
# ---------------------------------------------------------------------------

def test_writes_go_through_fence(tmp_path, monkeypatch):
    """A redirected (out-of-tree) write must be refused by fs_guard. Monkeypatch the
    fence to raise and confirm the cache write propagates it."""
    proj = make_proj(tmp_path)
    import sys
    psp = str(cc._psp_dir())
    if psp not in sys.path:
        sys.path.insert(0, psp)
    import fs_guard

    def _boom(path, root):
        raise fs_guard.FenceError("blocked")

    monkeypatch.setattr(fs_guard, "assert_under_docs_product", _boom)
    with pytest.raises(fs_guard.FenceError):
        cc.put_humanized(proj, "h", "text")


def test_state_path_under_memory(tmp_path):
    proj = make_proj(tmp_path)
    cc.save_state(proj, "all", provenance_hash="x")
    p = proj / "docs" / "product" / ".memory" / "critique-state.json"
    assert p.is_file()
    assert p.resolve().is_relative_to((proj / "docs" / "product").resolve())
