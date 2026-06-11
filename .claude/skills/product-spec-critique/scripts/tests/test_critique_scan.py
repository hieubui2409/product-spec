"""Tests for critique_scan.py — the CLI entrypoint + public facade.

Module-level signal correctness lives in the focused test modules
(test_critique_bundle / _provenance / _drift / _inherit / _cache); this file covers
the CLI integration smoke: required bundle keys, scope errors, malformed input, the
missing-product-spec degrade, and that the facade re-exports resolve."""

import critique_scan
from critique_test_support import make_proj, run_scan


# Required top-level bundle keys (asserted as a SUBSET so the contract can grow).
BUNDLE_KEYS = {
    "bundle_version", "scope", "lang", "target_ids", "ancestry", "digest",
    "source_files", "structural_findings", "cached_verdicts", "competitors",
    "prior_reports", "drift_threshold", "provenance", "inherited_context",
    "descendant_rollup", "parse_errors",
}


def test_bundle_has_required_top_level_keys(tmp_path):
    proj = make_proj(tmp_path)
    code, bundle = run_scan(proj, "--scope", "all")
    assert code == 0
    assert BUNDLE_KEYS.issubset(set(bundle.keys()))
    assert bundle["bundle_version"] == critique_scan.BUNDLE_VERSION
    assert bundle["scope"] == "all"
    assert bundle["provenance"]["reuse"] == "none"  # run-1 of a fresh fixture


def test_bundle_version_is_2(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["bundle_version"] == 2


def test_unknown_scope_records_parse_error(tmp_path):
    proj = make_proj(tmp_path)
    code, bundle = run_scan(proj, "--scope", "NOPE-X9")
    assert code == 0
    assert bundle["target_ids"] == []
    assert any("unknown scope" in e for e in bundle["parse_errors"])


def test_malformed_artifact_parse_error_exit_0(tmp_path):
    proj = make_proj(tmp_path)
    bad = proj / "docs" / "product" / "prds" / "auth.md"
    bad.write_text("---\nid: [unclosed\n: : :\n---\n# broken\n", encoding="utf-8")
    code, bundle = run_scan(proj, "--scope", "all")
    assert code == 0
    assert bundle["parse_errors"]


def test_missing_product_spec_dir_loud(tmp_path, monkeypatch):
    # If the product-spec scripts dir is absent, _import_psp raises a clear error;
    # main() catches it and emits an {error: ...} payload, still exit 0. Patch the
    # REAL home (critique_common._psp_dir), which _import_psp consults.
    import critique_common
    proj = make_proj(tmp_path)
    monkeypatch.setattr(critique_common, "_psp_dir", lambda: tmp_path / "nonexistent")
    code, result = run_scan(proj, "--scope", "all")
    assert code == 0
    assert "error" in result


def test_facade_reexports_resolve():
    # The split modules are re-exported under critique_scan for back-compat.
    for name in ("emit_bundle", "write_snapshot", "compute_drift",
                 "build_report_frontmatter", "compute_provenance_reuse",
                 "record_critique_state", "_scoped_content_hashes", "BUNDLE_VERSION"):
        assert hasattr(critique_scan, name), f"facade missing {name}"
