"""Tests for critique_drift.py — the --snapshot / --drift modes (exercised through
the critique_scan CLI facade). All modes exit 0 (advisory) and never crash."""

import json

from critique_test_support import make_proj, append_to, run_scan
import critique_scan


def test_snapshot_writes_marker_through_fence(tmp_path):
    proj = make_proj(tmp_path)
    code, result = run_scan(proj, "--snapshot", "--scope", "all")
    assert code == 0
    marker = proj / "docs" / "product" / ".memory" / "last_critique.json"
    assert marker.is_file()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"critiqued_at", "scope", "body_hash"}
    assert "PRD-AUTH-E1-S1" in data["body_hash"]
    assert "BRD-G1" not in data["body_hash"]  # goal -> no body_hash


def test_snapshot_routes_through_fence(tmp_path, monkeypatch):
    # Prove write_snapshot actually calls the fence: monkeypatch the imported fs_guard
    # assert to raise, then confirm --snapshot surfaces the error payload (exit 0).
    proj = make_proj(tmp_path)
    import sys
    sys.path.insert(0, str(critique_scan._psp_dir()))
    import fs_guard

    def _boom(path, root):
        raise fs_guard.FenceError("blocked")

    monkeypatch.setattr(fs_guard, "assert_under_docs_product", _boom)
    code, result = run_scan(proj, "--snapshot", "--scope", "all")
    assert code == 0
    assert "error" in result and "FenceError" in result["error"]
    assert not (proj / "docs" / "product" / ".memory" / "last_critique.json").exists()


def test_drift_missing_marker_is_first_run(tmp_path):
    proj = make_proj(tmp_path)
    code, result = run_scan(proj, "--drift")
    assert code == 0
    assert result["over"] is False
    assert result.get("first_run") is True


def test_drift_counts_after_single_body_edit(tmp_path):
    proj = make_proj(tmp_path)
    run_scan(proj, "--snapshot", "--scope", "all")  # baseline
    append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\n\nExtra body line to shift the hash.\n")
    _code, result = run_scan(proj, "--drift")
    assert result["changed_count"] == 1
    assert result["changed_ids"] == ["PRD-AUTH-E1-S1"]
    assert result["over"] is False  # 1 < default threshold 3


def test_drift_over_threshold(tmp_path):
    proj = make_proj(tmp_path)
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "preferences.yaml").write_text("critique_drift_threshold: 1\n", encoding="utf-8")
    run_scan(proj, "--snapshot", "--scope", "all")
    append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\n\nchanged\n")
    _code, result = run_scan(proj, "--drift")
    assert result["changed_count"] == 1
    assert result["over"] is True


def test_drift_vs_validated_falls_back_without_cache(tmp_path):
    proj = make_proj(tmp_path)
    run_scan(proj, "--snapshot", "--scope", "all")
    append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\n\nchanged\n")
    _code, result = run_scan(proj, "--drift", "--vs-validated")
    assert result["source"] == "live"
    assert result["changed_count"] == 1


def _write_judgments(proj, entries: dict, model_id="m", lang="en"):
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    payload = {"cache_version": 1, "model_id": model_id, "entries": entries}
    (mem / "judgments.json").write_text(json.dumps(payload), encoding="utf-8")


def test_vs_validated_zero_change_when_validated_node_matches(tmp_path):
    proj = make_proj(tmp_path)
    run_scan(proj, "--snapshot", "--scope", "all")
    marker = json.loads(
        (proj / "docs" / "product" / ".memory" / "last_critique.json").read_text("utf-8"))
    story_hash = marker["body_hash"]["PRD-AUTH-E1-S1"]
    _write_judgments(proj, {
        f"invest_quality|PRD-AUTH-E1-S1|{story_hash}|en|": {"verdict": "pass"},
    })
    _code, result = run_scan(proj, "--drift", "--vs-validated")
    assert result["source"] == "validated"
    assert result["changed_count"] == 0
    assert result["over"] is False


def test_vs_validated_counts_only_drifted_validated_node(tmp_path):
    proj = make_proj(tmp_path)
    run_scan(proj, "--snapshot", "--scope", "all")
    _write_judgments(proj, {
        "invest_quality|PRD-AUTH-E1-S1|deadbeef|en|": {"verdict": "pass"},  # != snapshot
    })
    _code, result = run_scan(proj, "--drift", "--vs-validated")
    assert result["source"] == "validated"
    assert result["changed_ids"] == ["PRD-AUTH-E1-S1"]
    assert result["changed_count"] == 1


def test_validated_hashes_excludes_conflicting_node(tmp_path):
    # A node with two distinct validate-time hashes is UNCERTAIN -> excluded.
    proj = make_proj(tmp_path)
    import sys
    sys_path_psp = str(critique_scan._psp_dir())
    if sys_path_psp not in sys.path:
        sys.path.insert(0, sys_path_psp)
    import judgment_cache
    _write_judgments(proj, {
        "invest_quality|PRD-AUTH-E1-S1|aaaa1111|en|": {"verdict": "pass"},
        "testability|PRD-AUTH-E1-S1|bbbb2222|en|": {"verdict": "fail"},  # conflicting hash
        "invest_quality|PRD-AUTH|cccc3333|en|": {"verdict": "pass"},     # single -> kept
    })
    got = critique_scan._validated_body_hashes(judgment_cache, proj)
    assert "PRD-AUTH-E1-S1" not in got  # conflicting -> excluded
    assert got.get("PRD-AUTH") == "cccc3333"  # single -> kept
