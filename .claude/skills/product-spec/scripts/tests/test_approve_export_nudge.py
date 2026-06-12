"""Discoverability contract: the approve flow must point the PO at export.

After a sign-off, an approved spec's acceptance criteria are most useful when they
can leave the repo as one shareable, read-once document. The skill closes that loop
by nudging `--export` right after `--approve`. This test guards the nudge against
silent removal in three homes:

  1. SKILL.md `--approve` flow row references `--export` (the LLM-facing behavior).
  2. GUIDE-EN.md "B4 — Approve" section forward-points to export (PO-facing how-to).
  3. GUIDE-VI.md "B4 — Approve" section does the same (parity across languages).

It is a presence contract, not a wording contract — it asserts the cross-link
exists, not its exact phrasing.
"""
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL_DIR / "SKILL.md"
GUIDE_EN = SKILL_DIR / "GUIDE-EN.md"
GUIDE_VI = SKILL_DIR / "GUIDE-VI.md"


def _approve_flag_row(skill_text: str) -> str:
    """The SKILL.md flag-table row whose first cell names `--approve`."""
    for line in skill_text.splitlines():
        if line.startswith("|") and "`--approve`" in line.split("|", 2)[1]:
            return line
    raise AssertionError("no `--approve` row found in SKILL.md flag table")


def _section(text: str, header_substr: str) -> str:
    """Return the lines of the `### ` section whose heading contains `header_substr`,
    up to the next `### ` heading (or end of file)."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("### ") and header_substr in line:
            start = i
            break
    assert start is not None, f"section '### …{header_substr}…' not found"
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("### "):
            end = j
            break
    return "\n".join(lines[start:end])


def test_skill_approve_row_points_at_export():
    """The `--approve` flow row nudges `--export` so the approved spec can be shared."""
    row = _approve_flag_row(SKILL_MD.read_text(encoding="utf-8"))
    assert "--export" in row, (
        "SKILL.md --approve row must nudge --export (post-sign-off shareable copy)"
    )


def test_guide_en_approve_section_links_export():
    """GUIDE-EN B4 (Approve) forward-points to export."""
    section = _section(GUIDE_EN.read_text(encoding="utf-8"), "B4")
    assert "Approve" in section, "located the wrong B4 section"
    assert "export" in section.lower(), (
        "GUIDE-EN B4 (Approve) must point the PO at export as the next step"
    )


def test_guide_vi_approve_section_links_export():
    """GUIDE-VI B4 (Approve) forward-points to export (language parity)."""
    section = _section(GUIDE_VI.read_text(encoding="utf-8"), "B4")
    assert "Approve" in section, "located the wrong B4 section"
    assert "export" in section.lower(), (
        "GUIDE-VI B4 (Approve) must point the PO at export as the next step"
    )
