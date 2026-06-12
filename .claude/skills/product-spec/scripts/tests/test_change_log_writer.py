"""Tests for the monthly change-log rotation writer.

Covers:
  - Append to month-keyed file (dir auto-created)
  - Cross-month rotation (June + July → two files)
  - Dedup idempotent guard (same entry twice → single occurrence)
  - assemble_audit_trail reads legacy + rolled files
  - Legacy-only back-compat (only change-log.md present)
  - Orphan path check (artifact file missing → unreconciled flagged)
  - Existing path not flagged (live artifact → clean)
  - Ref-doc instruction lines invoke the writer (not freehand prose)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import change_log_writer as clw  # noqa: E402
import assemble_audit_trail as aat  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _spec_root(tmp_path: Path) -> Path:
    """Minimal spec root with docs/product/ already created."""
    (tmp_path / "docs" / "product").mkdir(parents=True)
    return tmp_path


# Change-log entry fixture (matches the template format assemble_audit_trail parses)
_ENTRY_JUNE = """\
## 2026-06-15 — approved | duyệt

- **Artifact | Tài liệu:** PRD-AUTH (prd)
- **Action | Hành động:** approved
- **Reason | Lý do:** PO sign-off
- **Affected downstream | Ảnh hưởng phía dưới:** []
- **Dimensions touched | Chiều bị ảnh hưởng:** scope
- **Author | Tác giả:** hieu
"""

_ENTRY_JULY = """\
## 2026-07-03 — created | tạo

- **Artifact | Tài liệu:** PRD-BILLING (prd)
- **Action | Hành động:** created
- **Reason | Lý do:** new feature
- **Affected downstream | Ảnh hưởng phía dưới:** []
- **Dimensions touched | Chiều bị ảnh hưởng:** scope
- **Author | Tác giả:** hieu
"""


# ---------------------------------------------------------------------------
# (A) Writer tests
# ---------------------------------------------------------------------------

def test_writer_appends_to_month_file(tmp_path):
    """Entry dated 2026-06 lands in change-log/2026-06.md (dir auto-created)."""
    root = _spec_root(tmp_path)
    clw.write_change_log_entry(root, _ENTRY_JUNE, when="2026-06-15")

    month_file = root / "docs" / "product" / "change-log" / "2026-06.md"
    assert month_file.exists(), "month file not created"
    content = month_file.read_text(encoding="utf-8")
    assert "PRD-AUTH" in content
    assert "approved" in content


def test_writer_rotates_across_months(tmp_path):
    """Entries dated June + July → two separate month files, each with its entry."""
    root = _spec_root(tmp_path)
    clw.write_change_log_entry(root, _ENTRY_JUNE, when="2026-06-15")
    clw.write_change_log_entry(root, _ENTRY_JULY, when="2026-07-03")

    cl_dir = root / "docs" / "product" / "change-log"
    june_file = cl_dir / "2026-06.md"
    july_file = cl_dir / "2026-07.md"

    assert june_file.exists(), "June month file missing"
    assert july_file.exists(), "July month file missing"
    assert "PRD-AUTH" in june_file.read_text(encoding="utf-8")
    assert "PRD-BILLING" in july_file.read_text(encoding="utf-8")
    # Entries should NOT cross-contaminate
    assert "PRD-BILLING" not in june_file.read_text(encoding="utf-8")
    assert "PRD-AUTH" not in july_file.read_text(encoding="utf-8")


def test_writer_dedup_idempotent(tmp_path):
    """Writing the identical entry twice results in a single occurrence (dedup on date+artifact+action)."""
    root = _spec_root(tmp_path)
    clw.write_change_log_entry(root, _ENTRY_JUNE, when="2026-06-15")
    clw.write_change_log_entry(root, _ENTRY_JUNE, when="2026-06-15")  # exact duplicate

    month_file = root / "docs" / "product" / "change-log" / "2026-06.md"
    content = month_file.read_text(encoding="utf-8")
    # The heading line "## 2026-06-15 — approved" must appear exactly once
    occurrences = content.count("## 2026-06-15 — approved")
    assert occurrences == 1, (
        f"Dedup guard failed: heading appeared {occurrences} times (expected 1)"
    )


# ---------------------------------------------------------------------------
# (C) assemble_audit_trail cross-file read tests
# ---------------------------------------------------------------------------

def test_assemble_reads_legacy_and_rolled(tmp_path):
    """Legacy change-log.md + rolled change-log/2026-06.md → merged, chronological, no dupes."""
    root = _spec_root(tmp_path)

    # Legacy file — an older entry
    _write(root / "docs" / "product" / "change-log.md",
           "# Change Log\n\n"
           "## 2026-05-20 — created | tạo\n\n"
           "- **Artifact | Tài liệu:** PRD-LEGACY (prd)\n"
           "- **Action | Hành động:** created\n"
           "- **Dimensions touched | Chiều bị ảnh hưởng:** scope\n")

    # Rolled month file — a newer entry
    _write(root / "docs" / "product" / "change-log" / "2026-06.md",
           "## 2026-06-15 — approved | duyệt\n\n"
           "- **Artifact | Tài liệu:** PRD-AUTH (prd)\n"
           "- **Action | Hành động:** approved\n"
           "- **Dimensions touched | Chiều bị ảnh hưởng:** scope\n")

    data = aat.assemble(root)
    artifacts = [e["artifact"] for e in data["events"]]
    assert "PRD-LEGACY" in artifacts, "legacy file entry not read"
    assert "PRD-AUTH" in artifacts, "rolled month file entry not read"

    # Check chronological ordering: PRD-LEGACY (May) before PRD-AUTH (June)
    legacy_idx = next(i for i, e in enumerate(data["events"]) if e["artifact"] == "PRD-LEGACY")
    auth_idx = next(i for i, e in enumerate(data["events"]) if e["artifact"] == "PRD-AUTH")
    assert legacy_idx < auth_idx, "events not in chronological order"


def test_legacy_only_still_read(tmp_path):
    """When only the legacy change-log.md exists (no change-log/ dir), it is fully read."""
    root = _spec_root(tmp_path)

    _write(root / "docs" / "product" / "change-log.md",
           "# Change Log\n\n"
           "## 2026-04-10 — created | tạo\n\n"
           "- **Artifact | Tài liệu:** BRD (brd)\n"
           "- **Action | Hành động:** created\n"
           "- **Dimensions touched | Chiều bị ảnh hưởng:** problem\n")

    data = aat.assemble(root)
    artifacts = [e["artifact"] for e in data["events"]]
    assert "BRD" in artifacts, "legacy-only change-log not read"
    assert len([e for e in data["events"] if e["artifact"] == "BRD"]) == 1


# ---------------------------------------------------------------------------
# (D) Orphan path check tests
# ---------------------------------------------------------------------------

def test_missing_artifact_path_flagged(tmp_path):
    """A change-log entry whose artifact file does not exist → unreconciled/orphan flagged."""
    root = _spec_root(tmp_path)

    # Entry references PRD-GHOST, but no file for it exists in docs/product/
    _write(root / "docs" / "product" / "change-log" / "2026-06.md",
           "## 2026-06-10 — created | tạo\n\n"
           "- **Artifact | Tài liệu:** PRD-GHOST (prd)\n"
           "- **Action | Hành động:** created\n"
           "- **Dimensions touched | Chiều bị ảnh hưởng:** scope\n")

    data = aat.assemble(root)
    ghost_events = [e for e in data["events"] if e["artifact"] == "PRD-GHOST"]
    assert ghost_events, "PRD-GHOST event missing entirely"
    assert any(not e["reconciled"] for e in ghost_events), (
        "PRD-GHOST artifact path missing but event not marked unreconciled"
    )
    assert data["unreconciled_count"] >= 1


def test_existing_path_not_flagged(tmp_path):
    """A change-log entry whose artifact file exists → not flagged as unreconciled."""
    root = _spec_root(tmp_path)

    # Create the artifact file
    _write(root / "docs" / "product" / "prds" / "auth.md",
           "---\nid: PRD-AUTH\ntype: prd\nstatus: draft\n---\n\n# Auth PRD\n")

    # Entry that references the live artifact
    _write(root / "docs" / "product" / "change-log" / "2026-06.md",
           "## 2026-06-15 — created | tạo\n\n"
           "- **Artifact | Tài liệu:** PRD-AUTH (prd)\n"
           "- **Action | Hành động:** created\n"
           "- **Dimensions touched | Chiều bị ảnh hưởng:** scope\n")

    data = aat.assemble(root)
    auth_cl_events = [e for e in data["events"]
                      if e["artifact"] == "PRD-AUTH" and e["action"] == "created"]
    assert auth_cl_events, "PRD-AUTH change-log event missing"
    # The orphan check must NOT flag a live artifact path as unreconciled
    orphan_events = [e for e in auth_cl_events if not e["reconciled"]]
    assert not orphan_events, (
        "PRD-AUTH artifact file exists but was incorrectly flagged as unreconciled/orphan"
    )


# ---------------------------------------------------------------------------
# (D+) Dedup triple correctness — must not suppress genuinely distinct entries
# ---------------------------------------------------------------------------

_ENTRY_PRD_AUTH_UPDATED = """\
## 2026-01-05 — updated | cập nhật

- **Artifact | Tài liệu:** PRD-AUTH (prd)
- **Action | Hành động:** updated
- **Reason | Lý do:** scope change
- **Affected downstream | Ảnh hưởng phía dưới:** []
- **Dimensions touched | Chiều bị ảnh hưởng:** scope
- **Author | Tác giả:** hieu
"""

_ENTRY_PRD_PAY_APPROVED = """\
## 2026-01-05 — approved | duyệt

- **Artifact | Tài liệu:** PRD-PAY (prd)
- **Action | Hành động:** approved
- **Reason | Lý do:** PO sign-off
- **Affected downstream | Ảnh hưởng phía dưới:** []
- **Dimensions touched | Chiều bị ảnh hưởng:** scope
- **Author | Tác giả:** hieu
"""

_ENTRY_PRD_AUTH_APPROVED = """\
## 2026-01-05 — approved | duyệt

- **Artifact | Tài liệu:** PRD-AUTH (prd)
- **Action | Hành động:** approved
- **Reason | Lý do:** PO sign-off v2
- **Affected downstream | Ảnh hưởng phía dưới:** []
- **Dimensions touched | Chiều bị ảnh hưởng:** scope
- **Author | Tác giả:** hieu
"""


def test_distinct_triple_not_suppressed_by_field_contamination(tmp_path):
    """The dedup check must compare the (date, artifact, action) triple as a
    unit — not three independent substring checks.

    Scenario: the month file already contains:
      (2026-01-05, PRD-AUTH, updated)   ← same date + artifact, different action
      (2026-01-05, PRD-PAY,  approved)  ← same date + action, different artifact

    Writing (2026-01-05, PRD-AUTH, approved) is a NEW distinct triple.
    It must NOT be suppressed — the heading count for that month file must increase.
    """
    root = _spec_root(tmp_path)

    # Pre-populate with two entries whose fields "contaminate" the triple space
    clw.write_change_log_entry(root, _ENTRY_PRD_AUTH_UPDATED, when="2026-01-05")
    clw.write_change_log_entry(root, _ENTRY_PRD_PAY_APPROVED, when="2026-01-05")

    month_file = root / "docs" / "product" / "change-log" / "2026-01.md"
    heading_count_before = month_file.read_text(encoding="utf-8").count("## 2026-01-05")

    # Write the new distinct triple
    clw.write_change_log_entry(root, _ENTRY_PRD_AUTH_APPROVED, when="2026-01-05")

    heading_count_after = month_file.read_text(encoding="utf-8").count("## 2026-01-05")
    assert heading_count_after > heading_count_before, (
        f"Distinct triple (PRD-AUTH, approved) was wrongly suppressed by dedup. "
        f"Heading count before={heading_count_before}, after={heading_count_after}"
    )


# ---------------------------------------------------------------------------
# (B) Ref-doc tests
# ---------------------------------------------------------------------------

_REF_DIR = Path(__file__).resolve().parent.parent.parent / "references"

_REF_DOCS = {
    "workflow-validate.md": _REF_DIR / "workflow-validate.md",
    "workflow-interview.md": _REF_DIR / "workflow-interview.md",
    "workflow-update.md": _REF_DIR / "workflow-update.md",
}

# The writer call marker that must appear in each ref doc's change-log instruction.
# All 3 ref docs must reference the writer (write_change_log_entry or --write flag).
_WRITER_MARKER = "write_change_log_entry"


def test_ref_docs_invoke_writer():
    """The 3 workflow ref docs must reference write_change_log_entry in their change-log-append instruction."""
    missing = []
    for name, path in _REF_DOCS.items():
        if not path.exists():
            missing.append(f"{name}: FILE NOT FOUND at {path}")
            continue
        content = path.read_text(encoding="utf-8")
        if _WRITER_MARKER not in content:
            missing.append(f"{name}: does not reference '{_WRITER_MARKER}'")
    assert not missing, (
        "Ref doc(s) still use freehand prose instead of the writer call:\n"
        + "\n".join(missing)
    )
