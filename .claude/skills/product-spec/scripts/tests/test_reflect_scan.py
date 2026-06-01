"""Tests for the deterministic `--reflect` harvest SCRIPT half (`reflect_scan.py`).

`reflect_scan` is the script-only anchor feeder for the Tier-2 retroactive harvest.
It reads structurally-readable state — git commits touching `docs/product/` since the
last reflect/validate, the files each touched, revert/fix markers, and a dedup index
of already-recorded memory (DECs + self-corrections + po-style) — and emits ONLY
anchors. It makes NO candidate judgment (the read-only opus harvester does that), and
ALWAYS exits 0 (advisory). It is GIT-DEGRADE-SAFE: with no git repo it harvests the
`.memory/`/`decisions.md` file state only, marks `git_available: false`, skips commit
candidates, and never crashes.

The dedup index reuses the SAME readers `memory_gap` uses (`decision_register`,
`behavioral_memory`) — never a re-homed parser — so the harvester never re-proposes a
write that is already on record.

Tests (scenario-named, deterministic):
  1. commits touching docs/product since the last marker are listed; older excluded.
  2. a revert/fix commit is flagged as a self-correction candidate anchor.
  3. a candidate already in `.memory`/`decisions.md` is excluded from the dedup index.
  4. not a git repo → no crash, exit 0, file-state anchors only, `git_available:false`.
  5. same repo state → identical anchors (no wall-clock in the deterministic body).
  6. a malformed input surfaces a `parse_error` anchor + still exits 0.
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph, write_snapshot  # noqa: E402
import judgment_cache as jc  # noqa: E402
import decision_register as dr  # noqa: E402
import behavioral_memory as bm  # noqa: E402
import reflect_scan  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def _proj(tmp_path: Path, git: bool = True) -> Path:
    """A writable copy of the valid-spec fixture, optionally a committed git repo."""
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    if git:
        _git(proj, "init", "-q")
        _git(proj, "config", "user.email", "t@t.t")
        _git(proj, "config", "user.name", "t")
        _git(proj, "add", "-A")
        _git(proj, "commit", "-q", "-m", "base spec")
    return proj


def _validate_baseline(proj: Path) -> Path:
    """Simulate a `--validate`: snapshot the graph + write the last_validated marker
    (the harvest cutoff the script reads to bound commit candidates)."""
    graph = build_graph(proj)
    snap = write_snapshot(graph, proj)
    jc.write_last_validated(proj, snap)
    return snap


def _append_to(proj: Path, rel: str, line: str):
    p = proj / "docs" / "product" / rel
    p.write_text(p.read_text(encoding="utf-8") + line, encoding="utf-8")


def _commit(proj: Path, rel: str, line: str, msg: str):
    """Append to a docs/product file and commit it with `msg`."""
    _append_to(proj, rel, line)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", msg)


def _shas(anchors: dict) -> set:
    return {c["sha"] for c in anchors.get("commits_since_last", [])}


def _subjects(anchors: dict) -> set:
    return {c["subject"] for c in anchors.get("commits_since_last", [])}


# ---------------------------------------------------------------------------
# 1. commits since the last marker
# ---------------------------------------------------------------------------

def test_anchors_commits_since_last(tmp_path):
    """Commits touching docs/product AFTER the last-validated marker are listed as
    candidates; commits BEFORE the marker are excluded (already in the baseline)."""
    proj = _proj(tmp_path)
    # An OLD change, committed, THEN the validate cutoff — it is on the wrong side.
    _commit(proj, "stories/PRD-AUTH-E1-S1.md", "\nOld edit.\n", "old change")
    # Marker timestamps are second-granular; ensure the cutoff lands strictly after
    # the old commit and strictly before the new one.
    time.sleep(1.1)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    time.sleep(1.1)
    # A NEW change after the cutoff — this is the harvest candidate.
    _commit(proj, "stories/PRD-AUTH-E1-S1.md", "\nNew edit after validate.\n",
            "new change after validate")

    anchors = reflect_scan.collect(proj)
    assert anchors["git_available"] is True
    subjects = _subjects(anchors)
    assert "new change after validate" in subjects
    assert "old change" not in subjects
    # Each commit anchor records the docs/product files it touched.
    new = [c for c in anchors["commits_since_last"]
           if c["subject"] == "new change after validate"][0]
    assert any("stories/PRD-AUTH-E1-S1.md" in f for f in new["files"])


# ---------------------------------------------------------------------------
# 2. revert/fix markers → self-correction candidate
# ---------------------------------------------------------------------------

def test_revert_fix_markers(tmp_path):
    """A commit whose subject reads as a revert/fix is flagged as a self-correction
    candidate anchor (the harvester proposes a 3E slip the inline layer missed)."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    time.sleep(1.1)
    _commit(proj, "stories/PRD-AUTH-E1-S1.md", "\nA fix.\n",
            "fix: revert wrong scope on the auth story")

    anchors = reflect_scan.collect(proj)
    fix = [c for c in anchors["commits_since_last"]
           if c["subject"].startswith("fix:")][0]
    assert fix["is_revert_or_fix"] is True
    # And it is surfaced in the dedicated self-correction candidate list.
    cand_shas = {c["sha"] for c in anchors["revert_fix_candidates"]}
    assert fix["sha"] in cand_shas


# ---------------------------------------------------------------------------
# 3. dedup against already-recorded memory
# ---------------------------------------------------------------------------

def test_dedup_against_existing_memory(tmp_path):
    """The dedup index lists what is ALREADY recorded (DECs + self-corrections) so
    the harvester never re-proposes a write on record. Reuses the existing readers
    (`decision_register`, `behavioral_memory`) — no re-homed parser."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)

    # Record a DEC + a self-correction through the existing writers.
    dec_id = dr.alloc_id(proj)
    dr.append_decision(
        proj, dec_id, title="Keep auth scope",
        rationale="PO ruled the scope stays.", affects="PRD-AUTH",
    )
    bm.record_self_correction(
        proj, slip="wrote code instead of a story",
        violated_rule="no_silent_reversal",
        reminder="redirect build requests to a story with AC",
    )

    anchors = reflect_scan.collect(proj)
    idx = anchors["existing_memory"]
    # Recorded DEC ids + their affected nodes are in the dedup index.
    assert dec_id in idx["decision_ids"]
    assert "PRD-AUTH" in idx["decision_affects"]
    # Recorded self-correction slips are in the dedup index.
    assert any("wrote code instead of a story" in s for s in idx["self_correction_slips"])


# ---------------------------------------------------------------------------
# 4. git-degrade: not a git repo
# ---------------------------------------------------------------------------

def test_git_degrade_no_repo(tmp_path):
    """No git repo → no crash, `git_available: false`, no commit candidates, and the
    file-state dedup index is still harvested from `.memory/`/`decisions.md`."""
    proj = _proj(tmp_path, git=False)
    _validate_baseline(proj)
    dec_id = dr.alloc_id(proj)
    dr.append_decision(proj, dec_id, title="A ruling",
                       rationale="because", affects="PRD-AUTH")

    anchors = reflect_scan.collect(proj)
    assert anchors["git_available"] is False
    assert anchors["commits_since_last"] == []
    assert anchors["revert_fix_candidates"] == []
    # File-state harvest still works with no git.
    assert dec_id in anchors["existing_memory"]["decision_ids"]


# ---------------------------------------------------------------------------
# 5. deterministic
# ---------------------------------------------------------------------------

def test_deterministic(tmp_path):
    """Same repo state → identical deterministic anchors (commit list + dedup index).
    Wall-clock provenance lives outside the compared body."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    time.sleep(1.1)
    _commit(proj, "stories/PRD-AUTH-E1-S1.md", "\nEdit.\n", "change one")

    a = reflect_scan.collect(proj)
    b = reflect_scan.collect(proj)
    assert a == b


# ---------------------------------------------------------------------------
# 6. exit 0 always (malformed input → parse_error anchor)
# ---------------------------------------------------------------------------

def test_exit_zero_always(tmp_path):
    """A malformed artifact surfaces a `parse_error` anchor and the CLI still exits
    0 (advisory feeder, never a gate, never a traceback)."""
    proj = _proj(tmp_path, git=False)
    # Corrupt a frontmatter so the graph build records a parse error.
    bad = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md"
    bad.write_text("---\n: : : not yaml :\n---\nbody\n", encoding="utf-8")

    out = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "reflect_scan.py"), "--root", str(proj)],
        capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr
    payload = json.loads(out.stdout)
    assert payload["git_available"] is False
    assert any(a["type"] == "parse_error" for a in payload.get("parse_errors", []))
