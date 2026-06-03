"""test_audit_trail — C9 `--viz audit` governance view contracts.

Covers: event join from change-log + approval + DEC; the H7 orphaned-approval →
`unreconciled` row (never dropped); bilingual labels; empty-state; and the no-HTML
guard (the audit view must wire NO html emitter this phase).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import assemble_audit_trail as aat  # noqa: E402


def _spec_root(tmp_path: Path) -> Path:
    dp = tmp_path / "docs" / "product"
    dp.mkdir(parents=True)
    return tmp_path


def _write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_event_join_from_changelog_and_dec(tmp_path):
    root = _spec_root(tmp_path)
    _write(root / "docs/product/change-log.md",
           "# Change Log\n\n## 2026-06-01 — Add PRD-AUTH | Thêm\n\n"
           "- **Artifact | Tài liệu:** PRD-AUTH (prd)\n"
           "- **Action | Hành động:** created | tạo\n"
           "- **Dimensions touched | Chiều:** scope\n")
    _write(root / "docs/product/decisions.md",
           "# Decision Register\n\n---\nid: DEC-1\nstatus: active\ndate: 2026-06-02\naffects: PRD-AUTH\n---\n\n"
           "## DEC-1 — keep scope\n\nrationale here\n")
    data = aat.assemble(root)
    arts = {e["artifact"] for e in data["events"]}
    assert "PRD-AUTH" in arts
    dec_rows = [e for e in data["events"] if e["dec_ref"] == "DEC-1"]
    assert dec_rows and dec_rows[0]["artifact"] == "PRD-AUTH"


def test_orphaned_approval_is_unreconciled(tmp_path):
    # An approved artifact with NO change-log entry and NO DEC → must render unreconciled (H7).
    root = _spec_root(tmp_path)
    _write(root / "docs/product/prds/auth.md",
           "---\nid: PRD-ORPH\ntype: prd\nstatus: approved\n"
           "approval:\n  approved_by: Hieu PO\n  approved_at: 2026-05-01\n---\n\n# Orphan\n")
    data = aat.assemble(root)
    orph = [e for e in data["events"] if e["artifact"] == "PRD-ORPH"]
    assert orph, "approval event missing"
    assert any(not e["reconciled"] for e in orph), "orphaned approval should be unreconciled, not dropped"
    assert data["unreconciled_count"] >= 1
    # And the unreconciled marker is rendered, not hidden.
    out = aat.render_ascii(data, "en")
    assert "unreconciled" in out


def test_bilingual_labels(tmp_path):
    root = _spec_root(tmp_path)
    _write(root / "docs/product/change-log.md",
           "# CL\n\n## 2026-06-01 — x | y\n\n- **Artifact | T:** PRD-X (prd)\n- **Action | H:** created | tao\n")
    data = aat.assemble(root)
    en = aat.render_markdown(data, "en")
    vi = aat.render_markdown(data, "vi")
    assert "Who approved" in en
    assert "Người duyệt" in vi


def test_empty_state(tmp_path):
    root = _spec_root(tmp_path)
    data = aat.assemble(root)
    assert data["events"] == []
    assert "No audit events yet." in aat.render_ascii(data, "en")
    assert "Chưa có sự kiện" in aat.render_ascii(data, "vi")


def test_no_html_emitter_wired():
    # XSS-watch guard: the audit assembler must expose NO html renderer this phase.
    assert not hasattr(aat, "render_html")
    public = [n for n in dir(aat) if n.startswith("render_")]
    # ASCII + markdown only (incl. the release-notes delta markdown helper) — NO html emitter.
    assert set(public) == {"render_ascii", "render_markdown", "render_release_delta_md"}, public
    assert not any("html" in n.lower() for n in dir(aat))
