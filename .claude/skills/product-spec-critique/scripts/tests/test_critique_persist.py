"""Tests for critique_persist.py — the one-shot reuse-cache write + the --doctor
reconcile. Fixture-driven over the synthetic valid-spec tree (no real PO data)."""

import json

from critique_test_support import make_proj, run_scan
import critique_cache
import critique_persist


_FINDINGS = [
    {"lens": "product", "evidence": "PRD-AUTH:5", "critique": "thin value",
     "why_it_dies": "w", "fix": "f", "severity": "blocker"},
    {"lens": "tech", "evidence": "PRD-AUTH-E1-S1:12", "critique": "too big",
     "why_it_dies": "w", "fix": "f", "severity": "major"},
]
_REPORT = "docs/product/critique/260601-all.md"


def test_persist_writes_lens_cache_index_and_state(tmp_path):
    """One call writes all three reuse stores: the lens-cache (verbatim), the
    findings-index (lossy: blockers + DEC-worthy), and the per-scope critique-state."""
    proj = make_proj(tmp_path)
    res = critique_persist.persist_critique_outputs(
        proj, "all", 5, "vi", _FINDINGS, blocker_count=1, report=_REPORT)
    lh = res["lens_findings_hash"]
    assert lh and res["wrote_lens_cache"] is True
    assert critique_cache.get_lens_findings(proj, lh) == _FINDINGS
    state = critique_cache.load_state(proj).get("all")
    assert state and state.get("lens_findings_hash") == lh
    assert state.get("provenance_hash")
    index = critique_cache.load_index(proj)
    assert any(e.get("evidence_id") == "PRD-AUTH:5" for e in index.values())


def test_persist_is_idempotent(tmp_path):
    """Re-persisting the same array keys to the same hash and re-puts harmlessly."""
    proj = make_proj(tmp_path)
    a = critique_persist.persist_critique_outputs(proj, "all", 5, "vi", _FINDINGS, 1, report=_REPORT)
    b = critique_persist.persist_critique_outputs(proj, "all", 5, "vi", _FINDINGS, 1, report=_REPORT)
    assert a["lens_findings_hash"] == b["lens_findings_hash"]
    assert critique_cache.get_lens_findings(proj, b["lens_findings_hash"]) == _FINDINGS


def test_persist_empty_findings_still_records_state(tmp_path):
    """No lens findings → no lens-cache (nothing to key) but critique-state is STILL
    recorded so the next run's fast-path is anchored."""
    proj = make_proj(tmp_path)
    res = critique_persist.persist_critique_outputs(proj, "all", 5, "vi", [], 0, report=_REPORT)
    assert res["lens_findings_hash"] is None and res["wrote_lens_cache"] is False
    assert critique_cache.load_state(proj).get("all", {}).get("provenance_hash")


def test_doctor_flags_missing_lens_cache_and_report(tmp_path):
    """--doctor surfaces the failure mode: a state record whose report AND lens-cache
    do not exist on disk."""
    proj = make_proj(tmp_path)
    critique_cache.save_state(proj, "all", provenance_hash="abc", level=5, lang="vi",
                              report="docs/product/critique/GONE-all.md",
                              lens_findings_hash="deadbeefdeadbeef")
    rep = critique_persist.doctor(proj)
    assert rep["ok"] is False
    joined = " ".join(rep["issues"])
    assert "GONE-all.md" in joined
    assert "deadbeefdeadbeef" in joined


def test_doctor_clean_after_persist(tmp_path):
    """After a report is on disk AND persist wrote its caches, --doctor is clean."""
    proj = make_proj(tmp_path)
    crit = proj / "docs" / "product" / "critique"
    crit.mkdir(parents=True, exist_ok=True)
    (crit / "260601-all.md").write_text("# Critique: all\n", encoding="utf-8")
    critique_persist.persist_critique_outputs(proj, "all", 5, "vi", _FINDINGS, 1, report=_REPORT)
    rep = critique_persist.doctor(proj)
    assert rep["ok"] is True, rep["issues"]
    assert rep["reports_not_in_state"] == []


def test_persist_cli_via_input_envelope(tmp_path):
    """The script-side seam the workflow calls: `--persist --input <envelope.json>`."""
    proj = make_proj(tmp_path)
    env = {"scope": "all", "level": 5, "lang": "vi", "blocker_count": 1,
           "lens_findings": _FINDINGS, "report": _REPORT}
    envp = tmp_path / "env.json"
    envp.write_text(json.dumps(env), encoding="utf-8")
    code, result = run_scan(proj, "--persist", "--input", str(envp))
    assert code == 0
    assert result["wrote_lens_cache"] is True
    assert critique_cache.get_lens_findings(proj, result["lens_findings_hash"]) == _FINDINGS


def test_persist_cli_missing_input_is_advisory_error(tmp_path):
    """No --input degrades to an error record, never a crash (advisory contract)."""
    proj = make_proj(tmp_path)
    code, result = run_scan(proj, "--persist")
    assert code == 0
    assert result.get("error") == "no_input"


def test_persist_cli_non_int_level_is_advisory_error(tmp_path):
    """A malformed envelope (level/blocker_count not coercible to int) degrades to a
    clean bad_input record instead of leaking a raw exception type to the caller."""
    proj = make_proj(tmp_path)
    env = {"scope": "all", "level": None, "lang": "vi", "lens_findings": _FINDINGS}
    envp = tmp_path / "bad.json"
    envp.write_text(json.dumps(env), encoding="utf-8")
    code, result = run_scan(proj, "--persist", "--input", str(envp))
    assert code == 0
    assert result.get("error") == "bad_input"


def test_doctor_cli(tmp_path):
    """--doctor is reachable through the CLI and returns the reconcile record."""
    proj = make_proj(tmp_path)
    code, result = run_scan(proj, "--doctor")
    assert code == 0
    assert result["ok"] is True  # empty state → nothing to reconcile
    assert result["scopes"] == [] and result["reports_on_disk"] == []
