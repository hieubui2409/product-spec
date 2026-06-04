"""Grounding guard for the engagement-profile docs.

The `interview_rigor` / `action_prompting` knob→behaviour tables live in
`workflow-interview.md` (the DRY home). This test asserts that home actually cites the
EXACT enum tokens registered in `preferences.ENUMS`, so a future schema rename can't
silently leave the docs describing a token that no longer exists (token drift).

Mirrors the phase-7 release-doc grounding style (resolve REFERENCES_DIR, read the doc,
assert tokens present), scoped to the 2 product-spec engagement knobs."""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import preferences  # noqa: E402

REFERENCES_DIR = SCRIPTS_DIR.parent / "references"
WORKFLOW_INTERVIEW = REFERENCES_DIR / "workflow-interview.md"


def _doc() -> str:
    return WORKFLOW_INTERVIEW.read_text(encoding="utf-8")


def test_engagement_section_present():
    doc = _doc()
    assert "Engagement profile" in doc, (
        "workflow-interview.md must document the Engagement profile (the knob→behaviour home)"
    )
    # Both knob names must appear by their exact preference-key spelling.
    assert "interview_rigor" in doc
    assert "action_prompting" in doc


def test_action_prompting_tokens_grounded():
    doc = _doc()
    for token in sorted(preferences.ENUMS["action_prompting"]):
        assert token in doc, (
            f"action_prompting enum token {token!r} is not documented in "
            "workflow-interview.md — token drift between schema and docs"
        )


def test_interview_rigor_tokens_grounded():
    # `deep` is also used by critique_inherit_depth, so a bare `deep` match would be
    # ambiguous. Require interview_rigor to be documented alongside each of its tokens
    # (the section header names the knob, then the table lists every token).
    doc = _doc()
    assert "interview_rigor" in doc
    for token in sorted(preferences.ENUMS["interview_rigor"]):
        assert token in doc, (
            f"interview_rigor enum token {token!r} is not documented in "
            "workflow-interview.md — token drift between schema and docs"
        )
    # Guard the ambiguous token specifically: `deep` must co-occur with the knob name
    # in the engagement section, not only in the unrelated critique_inherit_depth note.
    start = doc.index("Engagement profile")
    section = doc[start:]
    assert "deep" in section, "interview_rigor `deep` must be documented in the engagement section"


def test_concise_but_deep_orthogonality_documented():
    # The detail_level-vs-rigor orthogonality (the "concise but deep" combo) must be
    # explicit so reviewers don't read `deep` rigor as "more verbose".
    doc = _doc().lower()
    assert "concise but deep" in doc or ("concise" in doc and "interview_rigor: deep" in _doc())
