"""Tests for critique_scan.py — the deterministic bundle/snapshot/drift assembler.

Reuses product-spec's valid-spec fixture (BRD-G1/G2 <- PRD-AUTH <- PRD-AUTH-E1
<- PRD-AUTH-E1-S1). All modes must exit 0 (advisory) and never crash."""

import json
from pathlib import Path

import pytest

from critique_test_support import make_proj, append_to, run_scan
import critique_scan


BUNDLE_KEYS = {
    "bundle_version", "scope", "lang", "target_ids", "ancestry", "digest",
    "source_files", "structural_findings", "cached_verdicts", "competitors",
    "prior_reports", "drift_threshold", "parse_errors",
}
FINDING_KEYS = {"check", "severity", "artifact_id", "file", "detail", "context"}


def test_bundle_exact_top_level_keys(tmp_path):
    proj = make_proj(tmp_path)
    code, bundle = run_scan(proj, "--scope", "all")
    assert code == 0
    assert set(bundle.keys()) == BUNDLE_KEYS
    assert bundle["bundle_version"] == critique_scan.BUNDLE_VERSION
    assert bundle["scope"] == "all"


def test_finding_shape(tmp_path):
    proj = make_proj(tmp_path)
    # Story is draft under an approved epic chain -> at least a status finding.
    _code, bundle = run_scan(proj, "--scope", "all")
    findings = bundle["structural_findings"]
    assert isinstance(findings, list)
    for f in findings:
        assert FINDING_KEYS.issubset(set(f.keys()))


def test_source_files_keyed_by_id_are_line_numbered_ground_truth(tmp_path):
    """source_files is keyed by ARTIFACT ID (the citation prefix itself) and maps to
    that artifact's 1-based line-numbered file content. This is what makes a lens
    `<id>:<line>` resolve in the PO's real file (regression guard for the
    bundle-offset fabrication defect AND the path-vs-id ambiguity)."""
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    sources = bundle["source_files"]
    assert isinstance(sources, dict) and sources, "source_files must be a non-empty map"

    # Keyed by artifact ID, not file path: the story id resolves, a path does not.
    assert "PRD-AUTH-E1-S1" in sources
    assert "stories/PRD-AUTH-E1-S1.md" not in sources

    # The numbering matches the real story file lines exactly.
    numbered = sources["PRD-AUTH-E1-S1"].splitlines()
    raw = (proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md").read_text(
        encoding="utf-8").splitlines()
    assert len(numbered) == len(raw)
    for i, (num_line, raw_line) in enumerate(zip(numbered, raw), 1):
        assert num_line == f"{i}: {raw_line}", f"line {i} prefix mismatch"

    # Each BRD goal id is independently citable (they share brd.md but each gets a key).
    assert "BRD-G1" in sources


def test_bundle_version_is_2(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["bundle_version"] == 2


def test_ancestry_for_deep_story(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1-S1")
    anc = bundle["ancestry"]
    # The story's chain: epic PRD-AUTH-E1, prd PRD-AUTH, goal BRD-G1, plus vision.
    assert anc["epic"] and anc["epic"]["id"] == "PRD-AUTH-E1"
    assert anc["prd"] and anc["prd"]["id"] == "PRD-AUTH"
    goal_ids = [g["id"] for g in anc["brd_goals"] if g]
    assert "BRD-G1" in goal_ids
    assert anc["vision"] is not None and anc["vision"]["type"] == "vision"
    # Target = the story itself (a leaf -> no descendants).
    assert bundle["target_ids"] == ["PRD-AUTH-E1-S1"]


def test_scope_all_targets_whole_tree(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert "PRD-AUTH-E1-S1" in bundle["target_ids"]
    assert "PRD-AUTH" in bundle["target_ids"]


def test_unknown_scope_records_parse_error(tmp_path):
    proj = make_proj(tmp_path)
    code, bundle = run_scan(proj, "--scope", "NOPE-X9")
    assert code == 0
    assert bundle["target_ids"] == []
    assert any("unknown scope" in e for e in bundle["parse_errors"])


def test_load_cache_none_tolerant(tmp_path):
    proj = make_proj(tmp_path)  # fixture ships no .memory/judgments.json
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["cached_verdicts"] == []


def test_competitors_empty_when_brd_has_none(tmp_path):
    proj = make_proj(tmp_path)  # valid-spec BRD declares no competitors:
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["competitors"] == []


def test_drift_threshold_default_and_override(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["drift_threshold"] == 3
    # Override via preferences.yaml (non-enum int).
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "preferences.yaml").write_text("critique_drift_threshold: 5\n", encoding="utf-8")
    _code, bundle2 = run_scan(proj, "--scope", "all")
    assert bundle2["drift_threshold"] == 5


def test_snapshot_writes_marker_through_fence(tmp_path):
    proj = make_proj(tmp_path)
    code, result = run_scan(proj, "--snapshot", "--scope", "all")
    assert code == 0
    marker = proj / "docs" / "product" / ".memory" / "last_critique.json"
    assert marker.is_file()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"critiqued_at", "scope", "body_hash"}
    # Goals (body_hash None) are skipped; story/prd/epic/vision are present.
    assert "PRD-AUTH-E1-S1" in data["body_hash"]
    assert "BRD-G1" not in data["body_hash"]  # goal -> no body_hash


def test_snapshot_routes_through_fence(tmp_path, monkeypatch):
    # Prove write_snapshot actually calls the fence (not just that the fence works):
    # monkeypatch the imported fs_guard assert to raise, then confirm --snapshot
    # surfaces the error payload (exit 0) — i.e. the write went through the fence.
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
    # And the marker was NOT written (the fence stopped it before any write).
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
    # Edit one story body -> exactly one node body_hash changes.
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
    # No judgments.json -> fall back to a live build, still counts the edit.
    assert result["source"] == "live"
    assert result["changed_count"] == 1


def _write_judgments(proj, entries: dict, model_id="m", lang="en"):
    """Hand-write a judgments.json with the given {key: entry} map."""
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    payload = {"cache_version": 1, "model_id": model_id, "entries": entries}
    (mem / "judgments.json").write_text(json.dumps(payload), encoding="utf-8")


def test_vs_validated_zero_change_when_validated_node_matches(tmp_path):
    # H1 regression: the critique snapshot covers ALL bodied nodes; the validate-time
    # cache covers only the ONE story that was judged, and its hash MATCHES the
    # snapshot (nothing actually changed). --vs-validated must report changed_count 0
    # — un-validated baseline nodes are unknown, not drifted.
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
    # A validated node whose validate-time hash differs from the critique baseline is
    # real drift; the many un-validated nodes are still NOT counted.
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
    # H2: a node with two distinct validate-time hashes is UNCERTAIN -> excluded.
    proj = make_proj(tmp_path)
    sys_path_psp = str(critique_scan._psp_dir())
    import sys
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


def test_malformed_artifact_parse_error_exit_0(tmp_path):
    proj = make_proj(tmp_path)
    # Corrupt a frontmatter block.
    bad = proj / "docs" / "product" / "prds" / "auth.md"
    bad.write_text("---\nid: [unclosed\n: : :\n---\n# broken\n", encoding="utf-8")
    code, bundle = run_scan(proj, "--scope", "all")
    assert code == 0
    assert bundle["parse_errors"]  # at least one parse error surfaced


def test_missing_product_spec_dir_loud(tmp_path, monkeypatch):
    # If product-spec scripts dir is absent, the import raises a clear error; main()
    # catches it and emits an {error: ...} payload, still exit 0.
    proj = make_proj(tmp_path)
    monkeypatch.setattr(critique_scan, "_psp_dir", lambda: tmp_path / "nonexistent")
    code, result = run_scan(proj, "--scope", "all")
    assert code == 0
    assert "error" in result
