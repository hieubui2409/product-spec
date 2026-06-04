"""test_audit_trail — C9 `--viz audit` governance view contracts.

Covers: event join from change-log + approval + DEC; the H7 orphaned-approval →
`unreconciled` row (never dropped); bilingual labels; empty-state; and the HTML
form's XSS-escaping contract (every dynamic field escaped server-side).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import assemble_audit_trail as aat  # noqa: E402
import render_html  # noqa: E402


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


@pytest.mark.bug_class  # cross-cutting invariant: HTML audit escapes every dynamic field (XSS-watch / C8)
def test_html_escapes_malicious_dynamic_fields():
    # The HTML audit form joins free-text governance fields; a `<script>` smuggled into
    # any of them MUST be escaped server-side, never emitted as live markup.
    data = {
        "schema_version": "1.0",
        "events": [
            {"date": "2026-06-04", "artifact": "PRD-X<script>alert(1)</script>",
             "action": "approved", "who_approved": "<img src=x onerror=alert(2)>",
             "what_drifted": "scope & \"risk\"", "dec_ref": "DEC-1", "reconciled": True},
            {"date": "2026-06-04", "artifact": "PRD-Y", "action": "approved",
             "who_approved": "PO", "what_drifted": "</td><script>evil()</script>",
             "dec_ref": "", "reconciled": False},
        ],
        "unreconciled_count": 1,
    }
    html = render_html.audit(data, "en")
    # No live markup survives — the angle brackets that would open a tag are escaped.
    # (Inert attribute TEXT like "onerror=alert" may remain inside the escaped string;
    # what matters is that no real `<tag>` is emitted.)
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert "</td><script>" not in html
    # The payloads appear only in escaped form.
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;img src=x onerror=alert(2)&gt;" in html
    assert "&amp;" in html and "&quot;" in html  # & and " escaped
    # Unreconciled row still flagged (not dropped) + class present.
    assert "audit-unreconciled" in html
    assert "unreconciled" in html


def test_html_empty_state_escaped():
    html = render_html.audit({"events": []}, "vi")
    assert "audit-empty" in html
    assert "Chưa có sự kiện" in html
