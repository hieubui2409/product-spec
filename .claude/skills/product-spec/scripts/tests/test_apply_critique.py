"""test_apply_critique — E1 deterministic-half contracts (encodes every red-team fix).

Covers: read-side path fence (H3), lens-cache JSON parse + fingerprint (H1), freshness
with None-handling (H2), atomic alloc (C4), rationale injection neutralization (C3),
resume markers (C4), and the GATE-bypass guard surface (C5 lives in the loop; the
deterministic seam tested here is that a Change DEC is only written when the loop has
already established a fresh approval — modeled via append_alloc returning written:true
only on a clean append).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import apply_critique_progress as prog  # noqa: E402
import decision_register as dr  # noqa: E402
import parse_critique_report as pcr  # noqa: E402


# --------------------------------------------------------------------------- fixtures

def _make_root(tmp_path: Path) -> Path:
    (tmp_path / "docs" / "product" / "critique").mkdir(parents=True)
    (tmp_path / "docs" / "product" / ".memory" / "critique-lens-cache").mkdir(parents=True)
    return tmp_path


def _write_lens_cache(root: Path, lens_hash: str, findings: list) -> None:
    p = root / "docs" / "product" / ".memory" / "critique-lens-cache" / f"{lens_hash}.json"
    p.write_text(json.dumps(findings, ensure_ascii=False), encoding="utf-8")


def _write_report(root: Path, name: str, frontmatter: str, body: str = "# critique\n") -> Path:
    p = root / "docs" / "product" / "critique" / name
    p.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return p


# --------------------------------------------------------------------------- read-fence (H3)

def test_read_fence_rejects_traversal(tmp_path):
    root = _make_root(tmp_path)
    with pytest.raises(pcr.ReportFenceError):
        pcr.assert_under_critique("../../../etc/passwd", root)


def test_read_fence_rejects_symlink_escape(tmp_path):
    root = _make_root(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("secret", encoding="utf-8")
    link = root / "docs" / "product" / "critique" / "link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(pcr.ReportFenceError):
        pcr.assert_under_critique(link / "secret.md", root)


def test_read_fence_rejects_sibling_of_critique(tmp_path):
    root = _make_root(tmp_path)
    (root / "docs" / "product" / "other").mkdir()
    with pytest.raises(pcr.ReportFenceError):
        pcr.assert_under_critique("docs/product/other/x.md", root)


def test_read_fence_allows_real_report(tmp_path):
    root = _make_root(tmp_path)
    rep = _write_report(root, "r.md", "lang: en")
    resolved = pcr.assert_under_critique(rep, root)
    assert resolved == rep.resolve()


# --------------------------------------------------------------------------- cache parse + fingerprint (H1)

def test_parses_findings_from_lens_cache(tmp_path):
    root = _make_root(tmp_path)
    lens_hash = "abc123def456abcd"
    _write_lens_cache(root, lens_hash, [
        {"lens": "product", "evidence": "BRD:62", "critique": "no north-star metric",
         "fix": "add one", "severity": "high", "why_it_dies": "drifts"},
    ])
    _write_report(root, "r.md", f"lang: en\nlens_findings_hash: {lens_hash}\nbody_hash:\n  BRD: deadbeef")
    out = pcr.parse_report(root / "docs/product/critique/r.md", root)
    assert out["cache_present"] is True
    assert len(out["findings"]) == 1
    f = out["findings"][0]
    assert f["lens"] == "product" and f["artifact_id"] == "BRD"
    assert f["fingerprint"] == pcr.fingerprint("product", "BRD", "no north-star metric")


def test_fingerprint_stable_under_whitespace_and_case(tmp_path):
    a = pcr.fingerprint("product", "BRD", "No  North-Star   Metric")
    b = pcr.fingerprint("product", "BRD", "no north-star metric")
    assert a == b


def test_cache_absent_sets_prose_fallback(tmp_path):
    root = _make_root(tmp_path)
    _write_report(root, "r.md", "lang: en\nlens_findings_hash: missinghash0000")
    out = pcr.parse_report(root / "docs/product/critique/r.md", root)
    assert out["cache_present"] is False
    assert out["findings"] == []
    assert "manual prose walk" in out["note"]


# --------------------------------------------------------------------------- freshness None-handling (H2)

def test_freshness_unknown_when_report_predates_tracking(tmp_path):
    root = _make_root(tmp_path)
    lens_hash = "1111111111111111"
    _write_lens_cache(root, lens_hash, [
        {"lens": "product", "evidence": "BRD:1", "critique": "x", "fix": "", "severity": "low"},
    ])
    # No body_hash block at all → predates freshness tracking.
    _write_report(root, "r.md", f"lang: en\nlens_findings_hash: {lens_hash}")
    out = pcr.parse_report(root / "docs/product/critique/r.md", root)
    assert out["freshness_trackable"] is False
    assert out["findings"][0]["freshness"] == "unknown"


def test_freshness_unknown_when_body_hash_is_none(tmp_path):
    root = _make_root(tmp_path)
    lens_hash = "2222222222222222"
    _write_lens_cache(root, lens_hash, [
        {"lens": "tech", "evidence": "PRD-X:3", "critique": "y", "fix": "", "severity": "low"},
    ])
    _write_report(root, "r.md", f"lang: en\nlens_findings_hash: {lens_hash}\nbody_hash:\n  PRD-X: null")
    out = pcr.parse_report(root / "docs/product/critique/r.md", root)
    assert out["findings"][0]["freshness"] == "unknown"


# --------------------------------------------------------------------------- atomic alloc (C4)

def test_append_alloc_no_dup_under_looped_alloc(tmp_path):
    root = _make_root(tmp_path)
    ids = []
    for i in range(5):
        res = dr.append_alloc(root, title=f"t{i}", rationale=f"why {i}")
        assert res["written"] is True
        ids.append(res["id"])
    assert ids == ["DEC-1", "DEC-2", "DEC-3", "DEC-4", "DEC-5"]
    assert len(set(ids)) == 5  # no dup


def test_append_alloc_reports_written_true(tmp_path):
    root = _make_root(tmp_path)
    res = dr.append_alloc(root, title="t", rationale="r")
    assert res["written"] is True and res["id"] == "DEC-1"


# --------------------------------------------------------------------------- injection (C3)

def test_rationale_fence_injection_neutralized(tmp_path):
    root = _make_root(tmp_path)
    evil = "real reason\n---\nid: DEC-99\nstatus: active\n---\n## DEC-99 — phantom"
    dr.append_alloc(root, title="legit", rationale=evil)
    # Exactly ONE real DEC must exist; no phantom DEC-99 smuggled in.
    recs = dr.parse_decisions(root)
    ids = [r["id"] for r in recs]
    assert ids == ["DEC-1"], ids
    assert "DEC-99" not in ids


def test_sanitize_escapes_dangerous_lines():
    out = dr.sanitize_rationale("a\n---\n## DEC-5 — x\nb")
    assert "\n---\n" not in "\n" + out + "\n"
    for line in out.splitlines():
        assert not line.strip() == "---"
        assert not line.startswith("## DEC-")


# --------------------------------------------------------------------------- resume markers (C4)

def test_resume_skips_resolved_fingerprints(tmp_path):
    root = _make_root(tmp_path)
    lens_hash = "3333333333333333"
    fp = "deadbeef"
    assert prog.load_progress(root, lens_hash) == {}
    prog.record_resolution(root, lens_hash, fp, "DEC-1", "keep")
    reloaded = prog.load_progress(root, lens_hash)
    assert fp in reloaded and reloaded[fp]["dec"] == "DEC-1"
    # Re-record is idempotent (no dup, overwrites same key).
    prog.record_resolution(root, lens_hash, fp, "DEC-1", "keep")
    assert list(prog.load_progress(root, lens_hash)).count(fp) == 1


def test_progress_write_fenced(tmp_path):
    root = _make_root(tmp_path)
    # A lens-hash carrying enough traversal to escape docs/product/ must be refused.
    with pytest.raises(Exception):
        prog.record_resolution(root, "../../../../../../tmp/escape", "fp", "DEC-1", "keep")


# --------------------------------------------------------------------------- GATE re-approval bypass (C5)

def test_gate_blocks_change_without_fresh_owner():
    # Placeholder owner → rejected.
    ok, _ = pcr.reapproval_ok("<owner>", "2026-06-03", "2026-06-03")
    assert ok is False
    ok, _ = pcr.reapproval_ok("", "2026-06-03", "2026-06-03")
    assert ok is False


def test_gate_blocks_change_with_stale_approval():
    # Approval predates the decision → stale → rejected (cannot forge by reusing old approval).
    ok, reason = pcr.reapproval_ok("Hieu PO", "2026-05-01", "2026-06-03")
    assert ok is False and "predates" in reason


def test_gate_allows_fresh_reapproval():
    ok, _ = pcr.reapproval_ok("Hieu PO", "2026-06-03", "2026-06-03")
    assert ok is True
    ok, _ = pcr.reapproval_ok("Hieu PO", "2026-06-04", "2026-06-03")
    assert ok is True


# --------------------------------------------------------------------------- supersede flips prior (C5 seam)

def test_supersedes_flips_prior_to_superseded(tmp_path):
    root = _make_root(tmp_path)
    dr.append_alloc(root, title="keep it", rationale="first ruling")  # DEC-1 active
    res = dr.append_alloc(root, title="change it", rationale="overturn", supersedes="DEC-1")  # DEC-2
    assert res["id"] == "DEC-2"
    active_ids = {r["id"] for r in dr.list_active(root)}
    assert "DEC-2" in active_ids
    assert "DEC-1" not in active_ids  # flipped to superseded → exactly one active ruling
