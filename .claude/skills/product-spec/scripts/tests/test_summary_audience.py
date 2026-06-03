"""test_summary_audience — E4 `--summary --audience exec|release-notes` deterministic seam.

exec = current --summary (regression: the exec_summary template + path are untouched). release-notes
= a since-last-approved delta from the C9 audit trail, filled into a new release_notes template via the
SAME render path. No new top-level flag, no new assembler (M1: reuse the value path, not token-sub misuse).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import assemble_audit_trail as aat  # noqa: E402
import generate_templates as gt  # noqa: E402


def _spec_root(tmp_path: Path) -> Path:
    (tmp_path / "docs" / "product").mkdir(parents=True)
    return tmp_path


def _write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_exec_summary_template_unchanged_regression():
    # audience=exec must remain the existing exec-summary path — registered + on disk, untouched.
    assert gt.TYPE_TEMPLATE["exec_summary"] == "exec-summary.md"
    assert gt.OUTPUT_PATH_FOR_TYPE["exec_summary"] == "exec-summary.md"
    assert (gt.TEMPLATES_DIR / "exec-summary.md").is_file()


def test_release_notes_template_registered():
    assert gt.TYPE_TEMPLATE["release_notes"] == "release-notes.md"
    assert gt.OUTPUT_PATH_FOR_TYPE["release_notes"] == "release-notes.md"
    assert (gt.TEMPLATES_DIR / "release-notes.md").is_file()


def test_release_notes_renders_all_tokens_no_leftovers():
    template = (gt.TEMPLATES_DIR / "release-notes.md").read_text(encoding="utf-8")
    values = {
        "status": "draft", "lang": "en", "owner": "PO", "version": "1.0.0",
        "created": "2026-06-03", "updated": "2026-06-03", "generated_at": "2026-06-03T00:00:00Z",
        "name": "Acme", "changes_since_approved": "- 2026-06-02 · PRD-X · approved",
        "top_risks": "none",
    }
    out = gt.render(template, values, keep_optional=[])
    assert "{{" not in out  # every token resolved
    assert "Release Notes — Acme" in out
    assert "PRD-X" in out


def test_since_last_approved_filters_to_after_latest_approval(tmp_path):
    root = _spec_root(tmp_path)
    # An approved artifact (2026-05-01) + a later change-log entry (2026-06-02).
    _write(root / "docs/product/prds/x.md",
           "---\nid: PRD-X\ntype: prd\nstatus: approved\n"
           "approval:\n  approved_by: PO\n  approved_at: 2026-05-01\n---\n# X\n")
    _write(root / "docs/product/change-log.md",
           "# CL\n\n## 2026-06-02 — update | x\n\n- **Artifact | T:** PRD-X (prd)\n- **Action | H:** edited | sua\n")
    _write(root / "docs/product/change-log.md",
           (root / "docs/product/change-log.md").read_text(encoding="utf-8") +
           "\n## 2026-04-01 — old | x\n\n- **Artifact | T:** PRD-X (prd)\n- **Action | H:** created | tao\n")
    delta = aat.since_last_approved(root)
    assert delta["since"] == "2026-05-01"
    dates = {e["date"] for e in delta["events"]}
    assert "2026-06-02" in dates  # after approval → kept
    assert "2026-04-01" not in dates  # before approval → excluded


def test_release_delta_bilingual_empty_state(tmp_path):
    root = _spec_root(tmp_path)
    delta = aat.since_last_approved(root)
    assert "No audit events yet." in aat.render_release_delta_md(delta, "en")
    assert "Chưa có sự kiện" in aat.render_release_delta_md(delta, "vi")
