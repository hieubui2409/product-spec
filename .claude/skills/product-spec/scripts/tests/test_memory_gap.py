"""Tests for the deterministic memory-gap detector (`memory_gap.py`).

`memory_gap` is the SCRIPT-only, single DRY home for "memory that looks
unrecorded". It emits structured signals (never a judgment) consumed downstream
by `--status`, the validate forcing-function, the Stop hook, and `--reflect`
dedup. It ALWAYS exits 0 (advisory) and is deterministic (same input → same JSON).

Signal types (each `{type, severity, subject, evidence, suggested_writer}`):
  - `fence_breach`            — a write landed outside docs/product/ (reuses
                                `check_fence.scan` — no copied logic).
  - `validate_no_marker`      — the live graph drifted from (or has no)
                                `.memory/last_validated.json` (PERSISTED-STATE
                                only: the script cannot know a `--validate` ran
                                this session; it compares the live graph vs the
                                marker's snapshot).
  - `approved_changed_no_dec` — an `approved` artifact's `body_hash` changed vs
                                the last-validated snapshot but no NEW `DEC-<n>`
                                exists in decisions.md. Surfaced, never blocked
                                (a legit approved edit is a false positive the
                                hook nudges once).
  - `judged_not_stored`       — graph drifted but `judgments.json` did not grow
                                vs the `.memory/last_judged.json` marker. Marker
                                ABSENT → signal SKIPPED (degrade, never false-fire).

`--ack-no-dec <node-id>` records `.memory/no-dec-acks.json` `{node_id: body_hash}`;
`collect()` SUPPRESSES `approved_changed_no_dec` for a node whose CURRENT
`body_hash` matches its ack (the PO marks "no DEC needed" once). A later body
change re-arms the signal (the ack no longer matches).

Single-home invariant: fence detection is `check_fence.scan` (imported), graph +
body_hash + snapshot are `spec_graph`, decisions are `decision_register`, the
last-validated marker path is `judgment_cache._last_validated_path` — never copied.
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
import decision_register as dr  # noqa: E402
import check_fence  # noqa: E402
import memory_gap  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def _proj(tmp_path: Path, git: bool = True) -> Path:
    """A writable copy of the valid-spec fixture, optionally a committed git repo
    so the fence scan has a clean working-tree baseline (only NEW touches show)."""
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    if git:
        _git(proj, "init", "-q")
        _git(proj, "config", "user.email", "t@t.t")
        _git(proj, "config", "user.name", "t")
        _git(proj, "add", "-A")
        _git(proj, "commit", "-q", "-m", "base")
    return proj


def _validate_baseline(proj: Path) -> Path:
    """Simulate a `--validate`: snapshot the current graph + write the
    `last_validated.json` marker pointing at it (what the validate hub does)."""
    graph = build_graph(proj)
    snap = write_snapshot(graph, proj)
    jc.write_last_validated(proj, snap)
    return snap


def _types(signals):
    return {s["type"] for s in signals}


def _by_type(signals, t):
    return [s for s in signals if s["type"] == t]


def _append_to(proj: Path, rel: str, line: str):
    p = proj / "docs" / "product" / rel
    p.write_text(p.read_text(encoding="utf-8") + line, encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. clean spec → no signals
# ---------------------------------------------------------------------------

def test_no_signals_clean_spec(tmp_path):
    """A fully-recorded spec — validated baseline, nothing touched outside the
    fence, no approved drift — emits no signals."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    # Commit the memory writes so the working tree is clean (no fence breach).
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")

    signals = memory_gap.collect(proj)
    assert signals == [], signals


# ---------------------------------------------------------------------------
# 2. fence_breach (reuses check_fence)
# ---------------------------------------------------------------------------

def test_fence_breach_detected(tmp_path):
    """A file written OUTSIDE docs/product/ surfaces a `fence_breach` signal whose
    subject matches what `check_fence.scan` reports."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    # A stray write outside the spec boundary.
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (proj / "src" / "app.py").write_text("print('x')\n", encoding="utf-8")

    signals = memory_gap.collect(proj)
    breaches = _by_type(signals, "fence_breach")
    assert breaches, signals
    subjects = {s["subject"] for s in breaches}
    assert "src/app.py" in subjects
    # The subject set matches check_fence's own findings (no logic drift).
    fence_files = {f["file"] for f in check_fence.scan(proj)}
    assert subjects == fence_files


# ---------------------------------------------------------------------------
# 3. validate_no_marker
# ---------------------------------------------------------------------------

def test_validate_no_marker(tmp_path):
    """No `last_validated.json` at all → `validate_no_marker`. After a validate
    baseline with no edits the signal clears; editing a body re-fires it (the live
    graph drifted from the validated snapshot)."""
    proj = _proj(tmp_path)

    # No marker yet → signal present.
    assert "validate_no_marker" in _types(memory_gap.collect(proj))

    # Baseline, nothing edited → signal clears.
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    assert "validate_no_marker" not in _types(memory_gap.collect(proj))

    # Edit a draft story body → live graph drifts from the validated snapshot.
    _append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\nEdited after validate.\n")
    assert "validate_no_marker" in _types(memory_gap.collect(proj))


# ---------------------------------------------------------------------------
# 4. approved_changed_no_dec → clears when a DEC is added
# ---------------------------------------------------------------------------

def test_approved_changed_no_dec(tmp_path):
    """Flip an APPROVED artifact's body (PRD-AUTH) with no new DEC → the
    `approved_changed_no_dec` signal fires for that node. Recording a DEC in
    decisions.md clears it (the ruling is now on record)."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")

    # Change the approved PRD body (body_hash now differs from the snapshot).
    _append_to(proj, "prds/auth.md", "\nNew approved-PRD body line.\n")

    sigs = _by_type(memory_gap.collect(proj), "approved_changed_no_dec")
    assert any(s["subject"] == "PRD-AUTH" for s in sigs), sigs

    # Record a DEC → the ruling exists, the signal clears.
    dec_id = dr.alloc_id(proj)
    dr.append_decision(proj, dec_id=dec_id, title="Approved PRD edit ruling",
                       rationale="The new wording is intentional and approved.",
                       affects="PRD-AUTH")
    sigs2 = _by_type(memory_gap.collect(proj), "approved_changed_no_dec")
    assert not any(s["subject"] == "PRD-AUTH" for s in sigs2), sigs2


# ---------------------------------------------------------------------------
# 5. judged_not_stored — fires on drift, clears on growth, skipped w/o marker
# ---------------------------------------------------------------------------

def test_judged_not_stored(tmp_path):
    """With a `.memory/last_judged.json` marker present and the graph drifted but
    `judgments.json` NOT grown beyond the marker's count → `judged_not_stored`.
    Growing the cache past the marker clears it. With NO marker the signal is
    SKIPPED (degrade, never a false fire)."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")

    # Drift the graph so there is "something to judge".
    _append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\nDrifted body.\n")

    # No last_judged marker yet → SKIPPED (degrade).
    assert "judged_not_stored" not in _types(memory_gap.collect(proj))

    # Write the marker recording the current (0) verdict count vs the live graph
    # (no cache has been stored yet) using the production batch-store marker writer.
    jc.write_last_judged(proj, 0, build_graph(proj))
    # Drift the graph AGAIN, past the marker, with no new judgments stored.
    _append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\nMore drift, unjudged.\n")
    assert "judged_not_stored" in _types(memory_gap.collect(proj))

    # Grow the cache past the marker → cleared.
    graph = build_graph(proj)
    key = jc.compute_key("vagueness", ["PRD-AUTH-E1-S1"], graph)
    jc.store(proj, key, {"verdict": "ok"}, model_id="test-model")
    assert "judged_not_stored" not in _types(memory_gap.collect(proj))


# ---------------------------------------------------------------------------
# 6. --ack-no-dec suppresses approved_changed_no_dec until body re-changes
# ---------------------------------------------------------------------------

def test_ack_no_dec_suppresses(tmp_path):
    """`--ack-no-dec PRD-AUTH` records the node's CURRENT body_hash. `collect()`
    then suppresses `approved_changed_no_dec` for it while the body is unchanged
    (PO marked "no DEC needed" once). A later body edit re-arms the signal (the
    recorded hash no longer matches the live body)."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    _append_to(proj, "prds/auth.md", "\nApproved edit, PO says no DEC needed.\n")

    # Signal fires before the ack.
    assert any(s["subject"] == "PRD-AUTH"
               for s in _by_type(memory_gap.collect(proj), "approved_changed_no_dec"))

    # Ack it → suppressed while body_hash matches.
    ack_path = memory_gap.ack_no_dec(proj, "PRD-AUTH")
    assert ack_path.exists()
    assert not any(s["subject"] == "PRD-AUTH"
                   for s in _by_type(memory_gap.collect(proj), "approved_changed_no_dec"))

    # A later body change re-arms (the recorded hash is now stale).
    _append_to(proj, "prds/auth.md", "\nAnother approved edit.\n")
    assert any(s["subject"] == "PRD-AUTH"
               for s in _by_type(memory_gap.collect(proj), "approved_changed_no_dec"))


# ---------------------------------------------------------------------------
# 7. deterministic
# ---------------------------------------------------------------------------

def test_deterministic(tmp_path):
    """Same input → byte-identical signal JSON across two runs (signals carry no
    wall-clock; the body of the report is purely a function of disk state)."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _append_to(proj, "prds/auth.md", "\nDrift for determinism check.\n")

    a = json.dumps(memory_gap.collect(proj), sort_keys=True, ensure_ascii=False)
    b = json.dumps(memory_gap.collect(proj), sort_keys=True, ensure_ascii=False)
    assert a == b


# ---------------------------------------------------------------------------
# 8. exit 0 always, even on malformed inputs (parse_error signal, never crash)
# ---------------------------------------------------------------------------

def test_exit_zero_always(tmp_path):
    """A malformed artifact must not crash the detector: it surfaces a
    `parse_error` signal and the CLI still exits 0 (advisory). Determinism + the
    advisory contract hold even on bad input."""
    proj = _proj(tmp_path)
    # Corrupt a story's frontmatter so the graph build records a parse_error.
    bad = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md"
    bad.write_text("---\n: : : not: valid: yaml: [\n---\n# broken\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "memory_gap.py"), "--root", str(proj)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert "signals" in out
    assert any(s["type"] == "parse_error" for s in out["signals"]), out["signals"]


# ---------------------------------------------------------------------------
# 9. reuses check_fence (single home, no logic drift)
# ---------------------------------------------------------------------------

def test_reuses_check_fence(tmp_path):
    """The `fence_breach` subjects emitted by `memory_gap` are EXACTLY the files
    `check_fence.scan` reports — proving the detector imports the fence logic
    rather than re-implementing the git-porcelain scan."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    (proj / "config").mkdir(parents=True, exist_ok=True)
    (proj / "config" / "x.yaml").write_text("k: v\n", encoding="utf-8")
    (proj / "notes.txt").write_text("hi\n", encoding="utf-8")

    fence_files = {f["file"] for f in check_fence.scan(proj)}
    gap_files = {s["subject"] for s in _by_type(memory_gap.collect(proj), "fence_breach")}
    assert gap_files == fence_files
    assert "config/x.yaml" in gap_files
    assert "notes.txt" in gap_files


# ---------------------------------------------------------------------------
# CLI shape — JSON {signals:[...]} on stdout, exit 0
# ---------------------------------------------------------------------------

def test_cli_emits_signals_json_exit_zero(tmp_path):
    proj = _proj(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "memory_gap.py"), "--root", str(proj)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert isinstance(out.get("signals"), list)
    # Each signal carries the full shape.
    for s in out["signals"]:
        assert set(s) >= {"type", "severity", "subject", "evidence", "suggested_writer"}


def test_cli_ack_no_dec_writes_marker(tmp_path):
    """`--ack-no-dec <id>` writes the ack marker under .memory/ and exits 0."""
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _append_to(proj, "prds/auth.md", "\nApproved edit.\n")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "memory_gap.py"),
         "--root", str(proj), "--ack-no-dec", "PRD-AUTH"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    ack = proj / "docs" / "product" / ".memory" / "no-dec-acks.json"
    assert ack.exists()
    data = json.loads(ack.read_text(encoding="utf-8"))
    assert "PRD-AUTH" in data
