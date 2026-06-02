"""Tests for critique_provenance.py — report frontmatter + the 4-way reuse decision
(none / full / consolidate_only / relens). Exercised via the critique_scan facade."""

import sys

from critique_test_support import make_proj, append_to
import critique_scan
import critique_provenance
import critique_cache


def _spec_graph():
    psp = str(critique_scan._psp_dir())
    if psp not in sys.path:
        sys.path.insert(0, psp)
    import spec_graph
    return spec_graph


def _write_report(proj, name, frontmatter, body="# Critique: x\n"):
    crit = proj / "docs" / "product" / "critique"
    crit.mkdir(parents=True, exist_ok=True)
    (crit / name).write_text(frontmatter + body, encoding="utf-8")


def _stash(proj, text):
    p = proj / "docs" / "product" / "critique" / "_rt.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_build_frontmatter_round_trip(tmp_path):
    proj = make_proj(tmp_path)
    fm = critique_scan.build_report_frontmatter(proj, "all", 5, "vi", None, "abc123")
    assert fm.startswith("---\n") and fm.rstrip().endswith("---")
    parsed = critique_scan._read_report_frontmatter(_stash(proj, fm + "# h\n"))
    assert parsed["critique_scope"] == "all"
    assert parsed["level"] == 5
    assert parsed["lang"] == "vi"
    assert parsed["lens_findings_hash"] == "abc123"
    assert isinstance(parsed["body_hash"], dict) and parsed["body_hash"]
    assert "register" not in parsed  # omitted below level 7


def test_frontmatter_register_present_at_level_7(tmp_path):
    proj = make_proj(tmp_path)
    reg = {"gender": "m", "dialect": "bac", "profanity": "strong"}
    fm = critique_scan.build_report_frontmatter(proj, "all", 7, "vi", reg, "h7")
    parsed = critique_scan._read_report_frontmatter(_stash(proj, fm + "# h\n"))
    assert parsed["register"] == reg


def test_prior_reports_reads_frontmatter(tmp_path):
    proj = make_proj(tmp_path)
    fm = critique_scan.build_report_frontmatter(proj, "all", 3, "vi", None, "lh1")
    _write_report(proj, "260603-0001-all.md", fm)
    priors = critique_scan._prior_reports(proj)
    rec = next(r for r in priors if r["path"].endswith("260603-0001-all.md"))
    assert rec["critique_scope"] == "all"
    assert rec["level"] == 3
    assert isinstance(rec["body_hash"], dict)
    assert rec["lens_findings_hash"] == "lh1"


def test_prior_reports_fallback_no_frontmatter(tmp_path):
    proj = make_proj(tmp_path)
    _write_report(proj, "c1-all-lvl3.md", "", body="# Critique: all · level 3\n")
    priors = critique_scan._prior_reports(proj)
    rec = next(r for r in priors if r["path"].endswith("c1-all-lvl3.md"))
    assert rec["body_hash"] is None
    assert rec["scope"] is None  # filename NOT trusted for scope


def test_provenance_none_no_prior(tmp_path):
    proj = make_proj(tmp_path)
    res = critique_scan.compute_provenance_reuse(proj, "all", 5, "vi")
    assert res["reuse"] == "none"


def test_provenance_fresh_forces_none(tmp_path):
    proj = make_proj(tmp_path)
    fm = critique_scan.build_report_frontmatter(proj, "all", 5, "vi", None, "lh")
    _write_report(proj, "260603-0001-all.md", fm)
    res = critique_scan.compute_provenance_reuse(proj, "all", 5, "vi", fresh=True)
    assert res["reuse"] == "none"


def test_provenance_filename_only_degrades_none(tmp_path):
    # A filename-only prior named c1-all-lvl3.md must NOT false-match scope.
    proj = make_proj(tmp_path)
    _write_report(proj, "c1-all-lvl3.md", "", body="# Critique: all · level 3\n")
    assert critique_scan.compute_provenance_reuse(proj, "all", 3, "vi")["reuse"] == "none"
    assert critique_scan.compute_provenance_reuse(proj, "all-lvl3", 3, "vi")["reuse"] == "none"


def test_provenance_full(tmp_path):
    proj = make_proj(tmp_path)
    fm = critique_scan.build_report_frontmatter(proj, "all", 5, "vi", None, "lh")
    _write_report(proj, "260603-0001-all.md", fm)
    assert critique_scan.compute_provenance_reuse(proj, "all", 5, "vi")["reuse"] == "full"


def test_provenance_consolidate_only_with_lens_cache(tmp_path):
    proj = make_proj(tmp_path)
    arr = [{"lens": "product", "evidence": "PRD-AUTH:1", "critique": "x",
            "why_it_dies": "y", "fix": "z", "severity": "blocker"}]
    h = critique_cache._lens_findings_hash(arr)
    critique_cache.put_lens_findings(proj, h, arr)
    fm = critique_scan.build_report_frontmatter(proj, "all", 3, "vi", None, h)
    _write_report(proj, "260603-0001-all.md", fm)
    res = critique_scan.compute_provenance_reuse(proj, "all", 7, "vi")
    assert res["reuse"] == "consolidate_only"
    assert res["lens_findings_hash"] == h


def test_provenance_consolidate_only_missing_lens_cache_degrades_relens(tmp_path):
    proj = make_proj(tmp_path)
    fm = critique_scan.build_report_frontmatter(proj, "all", 3, "vi", None, "absent-hash")
    _write_report(proj, "260603-0001-all.md", fm)
    res = critique_scan.compute_provenance_reuse(proj, "all", 7, "vi")
    assert res["reuse"] == "relens"  # never a broken half-reuse


def test_provenance_relens_one_node(tmp_path):
    proj = make_proj(tmp_path)
    fm = critique_scan.build_report_frontmatter(proj, "all", 5, "vi", None, "lh")
    _write_report(proj, "260603-0001-all.md", fm)
    append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\n\nbody shift\n")
    res = critique_scan.compute_provenance_reuse(proj, "all", 5, "vi")
    assert res["reuse"] == "relens"
    assert res["changed_ids"] == ["PRD-AUTH-E1-S1"]


def test_provenance_fast_path_skips_report_read(tmp_path, monkeypatch):
    # A critique-state provenance_hash match decides without PARSING the prior
    # report — assert _latest_frontmatter_prior (in critique_provenance) is not called.
    # (The existence guard only stats the report, it does not parse it.)
    proj = make_proj(tmp_path)
    _write_report(proj, "260603-0001-all.md", "")  # report exists so `full` stands
    sg = _spec_graph()
    bh = critique_scan._scoped_body_hashes(sg, proj, "all")
    ph = critique_scan._provenance_hash(bh)
    critique_cache.save_state(proj, "all", provenance_hash=ph, level=5, lang="vi",
                              report="docs/product/critique/260603-0001-all.md",
                              lens_findings_hash=None)
    called = {"hit": False}
    monkeypatch.setattr(critique_provenance, "_latest_frontmatter_prior",
                        lambda r, s: called.__setitem__("hit", True) or None)
    res = critique_scan.compute_provenance_reuse(proj, "all", 5, "vi")
    assert res["reuse"] == "full"
    assert called["hit"] is False


def test_fast_path_dangling_report_falls_through(tmp_path):
    # Fast-path `full` pointing at a NON-EXISTENT report must fall through to the
    # slow path (here → none, no real prior) instead of returning a dangling full.
    proj = make_proj(tmp_path)
    sg = _spec_graph()
    bh = critique_scan._scoped_body_hashes(sg, proj, "all")
    ph = critique_scan._provenance_hash(bh)
    critique_cache.save_state(proj, "all", provenance_hash=ph, level=5, lang="vi",
                              report="docs/product/critique/GONE-all.md",
                              lens_findings_hash=None)
    res = critique_scan.compute_provenance_reuse(proj, "all", 5, "vi")
    assert res["reuse"] == "none"


def test_provenance_register_change_reconsolidates(tmp_path):
    # Same body + same level/lang but DIFFERENT register (level >= 7 voice axis)
    # must re-consolidate, not serve stale voice as `full`.
    proj = make_proj(tmp_path)
    arr = [{"lens": "product", "evidence": "PRD-AUTH:1", "critique": "x",
            "why_it_dies": "y", "fix": "z", "severity": "blocker"}]
    h = critique_cache._lens_findings_hash(arr)
    critique_cache.put_lens_findings(proj, h, arr)
    reg_m = {"gender": "m", "dialect": "bac", "profanity": "strong"}
    fm = critique_scan.build_report_frontmatter(proj, "all", 7, "vi", reg_m, h)
    _write_report(proj, "260603-0001-all.md", fm)
    reg_f = {"gender": "f", "dialect": "bac", "profanity": "strong"}
    res = critique_scan.compute_provenance_reuse(proj, "all", 7, "vi", register=reg_f)
    assert res["reuse"] == "consolidate_only"
    res_same = critique_scan.compute_provenance_reuse(proj, "all", 7, "vi", register=reg_m)
    assert res_same["reuse"] == "full"


def test_record_critique_state_writes_marker(tmp_path):
    proj = make_proj(tmp_path)
    critique_scan.record_critique_state(proj, "all", 5, "vi", "lh", blocker_count=2,
                                        report="r.md", now_iso="260603-0001")
    state = critique_cache.load_state(proj)
    assert state["all"]["last_ts"] == "260603-0001"
    assert state["all"]["blocker_count"] == 2
    assert state["all"]["drift_since"] == 0
    assert state["all"]["provenance_hash"]
