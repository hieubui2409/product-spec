"""Open-questions detector guards.

An acceptance-criterion, a body line, or a `.session.md` note carrying "cần PO xác
định" / "TBD" / "Vẫn còn mở" is an unresolved decision riding inside an artifact that
may already look done. The detector gives those markers a first-class home: `--status`
lists them, and the `--approve` flow consults the per-file scan so an artifact with a
hanging parameter is not sealed silently. The scan covers the whole spec tree (not just
`must` ACs) because the real defect spans both a story `must` and free business
questions in the session notes.

Synthetic fixtures only (no real PO data).
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import open_questions  # noqa: E402


_PRODUCT = """---
id: PRODUCT
type: product
status: approved
lang: en
created: 2026-05-28
updated: 2026-05-30
name: "X"
core_value: "y"
personas: [shopper]
---
"""


def _story(ac_line: str) -> str:
    return f"""---
id: PRD-AUTH-E1-S1
type: story
epic: PRD-AUTH-E1
status: draft
lang: en
created: 2026-05-28
updated: 2026-06-01
personas: [shopper]
scope: in
moscow: must
size: S
horizon: now
metrics: [m]
acceptance_criteria:
  - "{ac_line}"
  - "Given a bad password, when they submit, then an error shows."
---

# Story body
"""


def _scaffold(tmp_path: Path, ac_line: str) -> Path:
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT, encoding="utf-8")
    (prod / "stories" / "story.md").write_text(_story(ac_line), encoding="utf-8")
    return proj


def test_vietnamese_marker_surfaced_naming_file(tmp_path):
    proj = _scaffold(tmp_path, "Given checkout, the fee threshold is 30 (cần PO xác định).")
    hits = open_questions.scan(proj)
    assert hits, "an unresolved PO marker must surface"
    h = hits[0]
    assert h["file"].endswith("story.md"), "the hit must name the offending file"
    assert "cần PO xác định" in h["snippet"]


def test_english_tbd_marker(tmp_path):
    proj = _scaffold(tmp_path, "Given checkout, the retry count is TBD.")
    hits = open_questions.scan(proj)
    assert any("TBD" in h["snippet"] for h in hits)


def test_clean_story_has_no_open_questions(tmp_path):
    proj = _scaffold(tmp_path, "Given a visitor, when they sign in, then a session is created.")
    assert open_questions.scan(proj) == [], "a fully-specified story raises nothing"


def test_scan_file_for_approve_warn(tmp_path):
    proj = _scaffold(tmp_path, "Given refunds, the window is open (Vẫn còn mở).")
    story = proj / "docs" / "product" / "stories" / "story.md"
    hits = open_questions.scan_file(story, rel="docs/product/stories/story.md")
    assert hits, "the per-file scan backing --approve must flag the marker"
    assert hits[0]["file"] == "docs/product/stories/story.md"


def test_session_open_questions_note(tmp_path):
    proj = _scaffold(tmp_path, "Given a visitor, when they sign in, then a session is created.")
    (proj / "docs" / "product" / ".session.md").write_text(
        "---\nphase: done\nupdated: 2026-06-02\n---\n\n"
        "## Vẫn còn mở\n- Số tiền phí: chưa chốt với PO.\n",
        encoding="utf-8",
    )
    hits = open_questions.scan(proj)
    assert any(h["file"].endswith(".session.md") for h in hits), \
        "open-questions notes in the session file must surface too"


def test_marker_in_body_not_just_ac(tmp_path):
    """The scan covers the whole artifact, not only acceptance-criteria — a marker in
    a body paragraph must surface too (locks the broad-scan contract: a must-AC-only
    scan would miss the free business questions the real defect also had)."""
    proj = _scaffold(tmp_path, "Given a visitor, when they sign in, then a session is created.")
    story = proj / "docs" / "product" / "stories" / "story.md"
    story.write_text(
        story.read_text(encoding="utf-8") + "\nPricing tier is still TBD pending finance.\n",
        encoding="utf-8",
    )
    hits = open_questions.scan(proj)
    assert any("TBD" in h["snippet"] for h in hits), "a body-line marker must surface, not only AC markers"


def test_status_surfaces_open_questions(tmp_path):
    proj = _scaffold(tmp_path, "Given checkout, the fee is 30 (cần PO xác định).")
    import status
    report = status.build_status(proj, today="2026-06-12")
    assert "open_questions" in report, "the status feeder must expose open_questions"
    assert any("cần PO xác định" in h["snippet"] for h in report["open_questions"])
