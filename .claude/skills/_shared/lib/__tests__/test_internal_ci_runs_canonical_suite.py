"""Guard: the internal-test-suite workflow must run the exact telemetry+hooks+_shared
pytest target set that CONTRIBUTING.md documents as mandatory. Without this guard the
workflow command and the doc can drift apart (the class of gap that let a red telemetry
test ship on the default branch)."""
from pathlib import Path

# repo root = .../.claude/skills/_shared/lib/__tests__/ -> up 5
_ROOT = Path(__file__).resolve().parents[5]
_WORKFLOW = _ROOT / ".github" / "workflows" / "internal-test-suite.yml"
_CONTRIBUTING = _ROOT / "CONTRIBUTING.md"

# The three pytest targets that form the canonical "telemetry + hooks + shared" suite.
_TARGETS = (".claude/skills/telemetry", ".claude/hooks", ".claude/skills/_shared")


def test_workflow_file_exists():
    assert _WORKFLOW.exists(), f"missing CI workflow: {_WORKFLOW}"


def test_workflow_runs_all_canonical_targets():
    body = _WORKFLOW.read_text(encoding="utf-8")
    # All three targets must appear together on a single pytest invocation line.
    pytest_lines = [ln for ln in body.splitlines() if "pytest" in ln and ".claude" in ln]
    assert pytest_lines, "workflow has no pytest invocation over .claude targets"
    assert any(all(t in ln for t in _TARGETS) for ln in pytest_lines), (
        "internal-test-suite.yml must run pytest over all of "
        f"{_TARGETS} on one line; found: {pytest_lines}"
    )


def test_contributing_documents_same_targets():
    # If CONTRIBUTING drops/renames a target, this fails so the workflow is revisited too.
    body = _CONTRIBUTING.read_text(encoding="utf-8")
    canonical = [ln for ln in body.splitlines() if "pytest" in ln and all(t in ln for t in _TARGETS)]
    assert canonical, (
        "CONTRIBUTING.md must document one pytest line covering "
        f"{_TARGETS}; keep it in sync with internal-test-suite.yml"
    )
