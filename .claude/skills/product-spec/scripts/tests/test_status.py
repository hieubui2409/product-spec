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

import status  # noqa: E402

# Shared scaffolding (single home in conftest). `--status` never needs a git repo,
# so `_proj` pins git=False to keep this file's plain copytree-only behavior.
from conftest import VALID, make_proj, validate_baseline  # noqa: E402,F401

_validate_baseline = validate_baseline


def _proj(tmp_path: Path) -> Path:
    """A writable copy of the valid-spec fixture (no git repo — --status never
    reads working-tree state)."""
    return make_proj(tmp_path, git=False)


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


# ---------- unrecorded_signals (memory_gap wiring) + reflect suggestion ----------

_STORY_TMPL = """---
id: {sid}
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

# {sid}

A story added after the validate baseline.
"""


def _add_story(proj: Path, sid: str) -> None:
    """Add a brand-new story under the existing epic (drift the live graph)."""
    (proj / "docs" / "product" / "stories" / f"{sid}.md").write_text(
        _STORY_TMPL.format(sid=sid), encoding="utf-8")


def _memory_snapshot(proj: Path):
    """Map every file under .memory/ to (size, mtime_ns, bytes) so a single byte or
    a new file is detectable — the read-only invariant guard."""
    mem = proj / "docs" / "product" / ".memory"
    if not mem.exists():
        return {}
    out = {}
    for p in sorted(mem.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(proj))] = (st.st_size, st.st_mtime_ns,
                                             p.read_bytes())
    return out


def test_status_includes_unrecorded_signals(tmp_path):
    """A seeded memory gap surfaces in `unrecorded_signals`. A fresh spec with no
    validate baseline has a `validate_no_marker` gap (the single home is memory_gap;
    status only imports + reports it)."""
    proj = _proj(tmp_path)
    report = status.build_status(proj)
    assert "unrecorded_signals" in report
    types = [s["type"] for s in report["unrecorded_signals"]]
    assert "validate_no_marker" in types
    # The section carries memory_gap's structured shape, not a re-derived one.
    for sig in report["unrecorded_signals"]:
        assert {"type", "severity", "subject", "evidence",
                "suggested_writer"} <= set(sig)


def test_status_clean_empty_signals(tmp_path):
    """A recorded spec (validate baseline, no drift, no fence breach) has no memory
    gaps → `unrecorded_signals: []`."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    report = status.build_status(proj)
    assert report["unrecorded_signals"] == []


def test_status_reflect_suggestion_on_high_drift(tmp_path):
    """High drift-since-last-validate adds a soft one-line `--reflect` suggestion;
    a clean (low-drift) baseline carries none. The suggestion is advisory text, not
    a gate."""
    # Low drift: clean baseline → no reflect suggestion.
    low = _proj(tmp_path / "low")
    _validate_baseline(low)
    low_report = status.build_status(low)
    assert low_report["unvalidated"] == []
    assert low_report.get("reflect_suggestion") in (None, "")

    # High drift: many nodes changed since the baseline → suggestion present.
    high = _proj(tmp_path / "high")
    _validate_baseline(high)
    for n in range(2, 8):  # add six new stories → well past the high-drift line
        _add_story(high, f"PRD-AUTH-E1-S{n}")
    high_report = status.build_status(high)
    assert len(high_report["unvalidated"]) >= 5
    assert high_report.get("reflect_suggestion")
    assert "--reflect" in high_report["reflect_suggestion"]


def test_status_still_readonly(tmp_path):
    """Wiring memory_gap into --status must NOT make it write under .memory/.
    Snapshot every .memory/ byte before and after — running --status (including the
    new unrecorded_signals pass) changes nothing on disk."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)  # creates .memory/ with a marker + snapshot ref
    before = _memory_snapshot(proj)
    status.build_status(proj)
    after = _memory_snapshot(proj)
    assert before == after, "--status must not write or mutate anything under .memory/"


def test_status_no_memory_dir_graceful(tmp_path):
    """Absent `.memory/` (never validated, no acks) → no crash, empty-ish report.
    memory_gap degrades, and status surfaces its signals without touching disk."""
    proj = _proj(tmp_path)
    mem = proj / "docs" / "product" / ".memory"
    if mem.exists():
        shutil.rmtree(mem)
    assert not mem.exists()
    report = status.build_status(proj)  # must not raise
    assert "unrecorded_signals" in report
    # Degraded cleanly and never created the directory.
    assert not mem.exists(), "--status must not create .memory/"
