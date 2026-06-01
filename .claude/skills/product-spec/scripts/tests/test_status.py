"""Tests for the `--status` spec-health feeder (`status.py`).

`--status` is a READ-ONLY pull nudge. It reports the spec's health against the
LAST `--validate` baseline: which nodes changed since then (unvalidated work),
which are still drafts, which approved artifacts drifted (stale approvals), and
which are overdue (reusing the `time_advisory` date math). It NEVER writes — in
particular it only READS `docs/product/.memory/last_validated.json`, the marker
the validate hub writes; it never creates or mutates it.

Script-vs-LLM split: this feeder owns the deterministic structural facts (the
snapshot delta, the draft set, the overdue set, the stale-approval set). The LLM
composes the human-readable nudge from this JSON per `references/workflow-status.md`.

Degradation invariant: with NO baseline marker the feeder reports
`baseline: false` ("no validation baseline yet") — it must NOT mark every node as
unvalidated. A spec that was never validated has nothing to compare against.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph, write_snapshot  # noqa: E402
import judgment_cache as jc  # noqa: E402
import status  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


def _proj(tmp_path: Path) -> Path:
    """A writable copy of the valid-spec fixture."""
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    return proj


def _validate_baseline(proj: Path) -> Path:
    """Simulate a `--validate`: write a snapshot of the current state and the
    `last_validated.json` marker pointing at it (exactly what the validate hub
    does via judgment_cache.write_last_validated)."""
    graph = build_graph(proj)
    snap = write_snapshot(graph, proj)
    jc.write_last_validated(proj, snap)
    return snap


# ---------- API: build_status() ----------

def test_status_no_baseline_degrades(tmp_path):
    """With NO last_validated.json the feeder reports baseline:false — NOT every
    node flagged. A never-validated spec has no comparison point."""
    proj = _proj(tmp_path)
    report = status.build_status(proj)
    assert report["baseline"] is False
    # Degraded: no per-node unvalidated set is asserted (nothing to compare).
    assert report["unvalidated"] == []


def test_status_clean_after_validate(tmp_path):
    """Immediately after a validate baseline, with no edits, nothing is
    unvalidated."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    report = status.build_status(proj)
    assert report["baseline"] is True
    assert report["unvalidated"] == []


def test_status_lists_unvalidated(tmp_path):
    """After a validate baseline, edit a story body → it shows up as unvalidated
    (changed since last validate). The baseline marker is read, never written."""
    proj = _proj(tmp_path)
    snap = _validate_baseline(proj)
    marker = proj / "docs" / "product" / ".memory" / "last_validated.json"
    marker_before = marker.read_text(encoding="utf-8")

    story = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md"
    story.write_text(story.read_text(encoding="utf-8") + "\nEdited after validate.\n",
                     encoding="utf-8")

    report = status.build_status(proj)
    assert report["baseline"] is True
    assert "PRD-AUTH-E1-S1" in report["unvalidated"]
    # Read-only: the marker is untouched.
    assert marker.read_text(encoding="utf-8") == marker_before


def test_status_lists_added_and_removed(tmp_path):
    """Both set-diff halves are surfaced as unvalidated work: a node ADDED since the
    baseline lands in `added`, a node REMOVED since the baseline lands in `removed`,
    and both fold into `unvalidated` — exercising the `set(added)|set(removed)` union,
    not just the per-field change set."""
    proj = _proj(tmp_path)
    stories = proj / "docs" / "product" / "stories"
    # Seed a second story BEFORE the baseline so the snapshot captures it; removing
    # it after the baseline is what exercises the `removed` branch.
    doomed_story = stories / "PRD-AUTH-E1-S2.md"
    doomed_story.write_text("""---
id: PRD-AUTH-E1-S2
type: story
epic: PRD-AUTH-E1
status: draft
lang: en
scope: in
moscow: should
size: S
horizon: now
acceptance_criteria:
  - "Given a user, when X, then Y."
---

# Second Story

A story present at baseline, deleted afterwards.
""", encoding="utf-8")

    _validate_baseline(proj)

    # Add a brand-new story under the existing epic (the `added` half).
    new_story = stories / "PRD-AUTH-E1-S3.md"
    new_story.write_text("""---
id: PRD-AUTH-E1-S3
type: story
epic: PRD-AUTH-E1
status: draft
lang: en
scope: in
moscow: should
size: S
horizon: now
acceptance_criteria:
  - "Given a user, when X, then Y."
---

# Third Story

A story added after the validate baseline.
""", encoding="utf-8")
    # Delete a story that existed at baseline (the `removed` half).
    doomed_story.unlink()

    report = status.build_status(proj)
    assert "PRD-AUTH-E1-S3" in report["added"]
    assert "PRD-AUTH-E1-S2" in report["removed"]
    # Both set-diff halves fold into the unvalidated set.
    assert "PRD-AUTH-E1-S3" in report["unvalidated"]
    assert "PRD-AUTH-E1-S2" in report["unvalidated"]


def test_status_lists_drafts(tmp_path):
    """Drafts are surfaced regardless of baseline (the fixture has a draft epic +
    draft story)."""
    proj = _proj(tmp_path)
    report = status.build_status(proj)
    assert "PRD-AUTH-E1" in report["drafts"]
    assert "PRD-AUTH-E1-S1" in report["drafts"]
    # Approved artifacts are not drafts.
    assert "PRD-AUTH" not in report["drafts"]


def test_status_stale_approvals(tmp_path):
    """An APPROVED artifact whose body changed since the last validate is a stale
    approval — it carries an approval the new wording was never validated under."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    prd = proj / "docs" / "product" / "prds" / "auth.md"  # status: approved
    prd.write_text(prd.read_text(encoding="utf-8") + "\nNew approved-PRD body line.\n",
                   encoding="utf-8")
    report = status.build_status(proj)
    assert "PRD-AUTH" in report["stale_approvals"]
    # And it is also an unvalidated change.
    assert "PRD-AUTH" in report["unvalidated"]


def test_status_overdue_reuses_time_advisory(tmp_path):
    """Overdue items come from the shared time_advisory date math, pinned via
    --today so the result is reproducible."""
    proj = _proj(tmp_path)
    # Give the PRD a past target_date.
    prd = proj / "docs" / "product" / "prds" / "auth.md"
    text = prd.read_text(encoding="utf-8")
    text = text.replace("status: approved",
                        "status: approved\ntarget_date: 2026-01-15", 1)
    prd.write_text(text, encoding="utf-8")
    report = status.build_status(proj, today="2026-06-01")
    overdue_ids = [o["artifact_id"] for o in report["overdue"]]
    assert "PRD-AUTH" in overdue_ids


# ---------- CLI ----------

def test_status_cli_exit_zero_no_baseline(tmp_path):
    proj = _proj(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "status.py"), "--root", str(proj)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["baseline"] is False
    assert "drafts" in out and "overdue" in out and "unvalidated" in out


def test_status_cli_after_validate(tmp_path):
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "status.py"),
         "--root", str(proj), "--today", "2026-06-01"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["baseline"] is True
    assert out["unvalidated"] == []


def test_status_cli_bad_today_nonzero(tmp_path):
    """A malformed --today is the one input error worth a non-zero exit (mirrors
    time_advisory); the nudge itself never gates."""
    proj = _proj(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "status.py"),
         "--root", str(proj), "--today", "not-a-date"],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0


def test_status_never_writes_marker(tmp_path):
    """The whole point of P8b: --status only READS last_validated.json. Running it
    must not create the marker when none exists, nor mutate it when one does."""
    proj = _proj(tmp_path)
    marker = proj / "docs" / "product" / ".memory" / "last_validated.json"
    status.build_status(proj)
    assert not marker.exists(), "--status must not create the validate marker"
