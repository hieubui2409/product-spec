"""Tests for the opt-in Tier-1 Stop hook (`.claude/hooks/memory_gap_hook.py`).

The hook is a thin, deterministic POLICY wrapper around the `memory_gap`
detector (P2). It owns NO detection logic — it imports `memory_gap.collect`
and only decides, per signal, whether to BLOCK the turn-end (force a
continuation so the LLM records the missing memory) or ALLOW it.

Per-signal policy (locked):
  - `fence_breach`            → PERSIST. Block while the gap remains; ignores
                                `stop_hook_active` (the breach is a hard fence
                                violation independently caught by check_fence).
                                Loop-safe via an internal block-count backstop
                                (the documented CC 8-cap is a bonus, not the
                                guarantee — P1 A7 fallback).
  - `validate_no_marker`      → NUDGE-ONCE. Block once with an actionable reason;
  - `approved_changed_no_dec`   honor `stop_hook_active` so the continuation's
                                Stop is allowed (a false positive costs exactly
                                one re-judgment, never a loop — P1 A6 fallback).

No-op guard (cheap, near-free on non-product turns):
  - A `PostToolUse` matcher `Write|Edit` writes an EPHEMERAL, session-keyed
    "touched docs/product" flag in the system temp dir (NOT under docs/product/,
    NOT committed). The `Stop` hook runs the detector ONLY when the flag is set
    AND `docs/product/` exists — else it exits 0 immediately without importing
    or running the detector.

The hook NEVER writes the memory layer (`.memory/`, decisions.md). It only
nudges the LLM, who writes via the existing writers. The only file the hook
itself creates is the ephemeral touched-flag in $TMPDIR.

These tests feed SYNTHETIC stdin (no live CC spike needed) and load the hook
handler via importlib from its top-level path with a fixture
`CLAUDE_PROJECT_DIR`, mirroring how CC invokes it.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph, write_snapshot  # noqa: E402
import judgment_cache as jc  # noqa: E402

# The hook lives at the repo top level, NOT under the skill scripts/. Resolve it
# relative to this test: scripts/tests/ -> scripts/ -> product-spec/ -> skills/
# -> .claude/ -> hooks/memory_gap_hook.py.
HOOK_PATH = (
    SCRIPTS_DIR.parent.parent.parent / "hooks" / "memory_gap_hook.py"
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


# ---------------------------------------------------------------------------
# Load the top-level hook module by path (CC invokes it as a standalone file;
# the test loads it the same way the design ships it — never copied logic).
# ---------------------------------------------------------------------------

def _load_hook():
    spec = importlib.util.spec_from_file_location("memory_gap_hook", HOOK_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Fixture helpers (mirror test_memory_gap.py so the hook is exercised against a
# real graph/snapshot, not a stub).
# ---------------------------------------------------------------------------

def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def _proj(tmp_path: Path, git: bool = True) -> Path:
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    if git:
        _git(proj, "init", "-q")
        _git(proj, "config", "user.email", "t@t.t")
        _git(proj, "config", "user.name", "t")
        _git(proj, "add", "-A")
        _git(proj, "commit", "-q", "-m", "base")
    return proj


def _validate_baseline(proj: Path):
    graph = build_graph(proj)
    snap = write_snapshot(graph, proj)
    jc.write_last_validated(proj, snap)
    return snap


def _append_to(proj: Path, rel: str, line: str):
    p = proj / "docs" / "product" / rel
    p.write_text(p.read_text(encoding="utf-8") + line, encoding="utf-8")


def _stop_stdin(proj: Path, *, session_id="sess-1", stop_hook_active=False):
    """The Stop-event stdin the hook reads. Only confirmed CC fields are set
    (P1 A2); `stop_hook_active` is optional and read defensively."""
    payload = {
        "session_id": session_id,
        "transcript_path": str(proj / "transcript.jsonl"),
        "cwd": str(proj),
        "hook_event_name": "Stop",
    }
    if stop_hook_active:
        payload["stop_hook_active"] = True
    return json.dumps(payload)


def _post_tool_stdin(proj: Path, file_path: str, *, session_id="sess-1",
                     tool_name="Write"):
    """The PostToolUse stdin — only `tool_name` + `tool_input.file_path` are read
    (P1 A4: never the result field)."""
    return json.dumps({
        "session_id": session_id,
        "cwd": str(proj),
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
    })


def _run_hook(mode, stdin, project_dir, env_extra=None):
    """Invoke the hook handler as CC does: a subprocess fed stdin, with
    `CLAUDE_PROJECT_DIR` set. Returns (returncode, stdout, stderr)."""
    import os
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env_extra:
        env.update(env_extra)
    args = [sys.executable, str(HOOK_PATH)]
    if mode == "post":
        args.append("--post-tool-use")
    proc = subprocess.run(args, input=stdin, capture_output=True, text=True,
                          env=env)
    return proc.returncode, proc.stdout, proc.stderr


def _set_touched_flag(mod, proj, session_id="sess-1"):
    """Set the ephemeral touched-flag the no-op guard checks, via the hook's own
    helper so the test never duplicates the path scheme."""
    mod.set_touched_flag(session_id)


def _isolate_tmp(tmp_path, monkeypatch):
    """Point $TMPDIR at a fresh dir so touched-flags from other tests/sessions
    never leak in (the flag is session-keyed but the dir is shared)."""
    tdir = tmp_path / "tmp"
    tdir.mkdir()
    monkeypatch.setenv("TMPDIR", str(tdir))
    return tdir


# ---------------------------------------------------------------------------
# 1. no-op: no docs/product/ → exit 0, detector never runs
# ---------------------------------------------------------------------------

def test_noop_when_no_docs_product(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    # A bare project with no spec tree at all.
    proj = tmp_path / "bare"
    proj.mkdir()
    # Even with the touched flag set, a missing docs/product/ short-circuits.
    mod.set_touched_flag("sess-1")
    rc = mod.handle_stop(_load_stdin_dict(_stop_stdin(proj)), str(proj))
    assert rc == 0


def _load_stdin_dict(s):
    return json.loads(s)


# ---------------------------------------------------------------------------
# 2. no-op: docs/product exists but the touched-flag is unset → exit 0
# ---------------------------------------------------------------------------

def test_noop_when_flag_unset(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)
    # docs/product/ exists, but no Write/Edit touched it this session → no flag.
    rc = mod.handle_stop(_load_stdin_dict(_stop_stdin(proj)), str(proj))
    assert rc == 0


# ---------------------------------------------------------------------------
# 3. fence_breach → block JSON (ok:false; reason names the in-fence fix)
# ---------------------------------------------------------------------------

def test_fence_breach_blocks(tmp_path, monkeypatch, capsys):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    # A stray write OUTSIDE the fence → check_fence reports it → fence_breach.
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (proj / "src" / "app.py").write_text("print('x')\n", encoding="utf-8")

    mod.set_touched_flag("sess-1")
    rc = mod.handle_stop(_load_stdin_dict(_stop_stdin(proj)), str(proj))
    assert rc == mod.BLOCK_EXIT  # exit 2 (CC blocking contract, stderr-fed)

    out = capsys.readouterr()
    payload = json.loads(out.out)
    assert payload["ok"] is False
    assert payload["decision"] == "block"
    # The reason is actionable and names the in-fence remediation.
    assert "docs/product/" in payload["reason"]
    # The reason is ALSO on stderr (P1 A5 dual-path block).
    assert payload["reason"] in out.err or "docs/product/" in out.err


# ---------------------------------------------------------------------------
# 4. fence persist IGNORES stop_hook_active → still blocks on a continuation
# ---------------------------------------------------------------------------

def test_fence_persist_ignores_stop_hook_active(tmp_path, monkeypatch, capsys):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (proj / "src" / "app.py").write_text("print('x')\n", encoding="utf-8")

    mod.set_touched_flag("sess-1")
    # stop_hook_active=True would ALLOW a nudge-once signal, but fence persists.
    rc = mod.handle_stop(
        _load_stdin_dict(_stop_stdin(proj, stop_hook_active=True)), str(proj))
    assert rc == mod.BLOCK_EXIT
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert any(s["type"] == "fence_breach" for s in payload.get("signals", [])) \
        or "docs/product/" in payload["reason"]


# ---------------------------------------------------------------------------
# 5. nudge-once HONORS stop_hook_active → exit 0 on the continuation
# ---------------------------------------------------------------------------

def test_nudge_once_honors_stop_hook_active(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    # Flip an APPROVED artifact with no DEC → approved_changed_no_dec (nudge-once).
    _append_to(proj, "prds/auth.md", "\nApproved edit, no DEC yet.\n")

    mod.set_touched_flag("sess-1")
    # On the CONTINUATION stop (stop_hook_active=True) the nudge-once is honored.
    rc = mod.handle_stop(
        _load_stdin_dict(_stop_stdin(proj, stop_hook_active=True)), str(proj))
    assert rc == 0


# ---------------------------------------------------------------------------
# 6. nudge-once BLOCKS the first time (stop_hook_active false/absent)
# ---------------------------------------------------------------------------

def test_nudge_once_blocks_first_time(tmp_path, monkeypatch, capsys):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    _append_to(proj, "prds/auth.md", "\nApproved edit, no DEC yet.\n")

    mod.set_touched_flag("sess-1")
    rc = mod.handle_stop(_load_stdin_dict(_stop_stdin(proj)), str(proj))
    assert rc == mod.BLOCK_EXIT
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    # The reason names the writer + the --ack-no-dec escape (the locked policy).
    assert "--decision" in payload["reason"] or "decision" in payload["reason"]
    assert "--ack-no-dec" in payload["reason"]


# ---------------------------------------------------------------------------
# 7. clean spec → no signals → exit 0
# ---------------------------------------------------------------------------

def test_clean_spec_allows_stop(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")

    mod.set_touched_flag("sess-1")
    rc = mod.handle_stop(_load_stdin_dict(_stop_stdin(proj)), str(proj))
    assert rc == 0


# ---------------------------------------------------------------------------
# 8. PostToolUse sets the flag for a docs/product write, NOT for an outside one
# ---------------------------------------------------------------------------

def test_post_tool_use_sets_flag(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)

    # A Write under docs/product/ → flag set.
    inside = str(proj / "docs" / "product" / "prds" / "auth.md")
    rc_in = mod.handle_post_tool_use(
        _load_stdin_dict(_post_tool_stdin(proj, inside, session_id="sx")),
        str(proj))
    assert rc_in == 0
    assert mod.touched_flag_set("sx")

    # A Write OUTSIDE docs/product/ (different session) → flag NOT set.
    outside = str(proj / "src" / "app.py")
    rc_out = mod.handle_post_tool_use(
        _load_stdin_dict(_post_tool_stdin(proj, outside, session_id="sy")),
        str(proj))
    assert rc_out == 0
    assert not mod.touched_flag_set("sy")


# ---------------------------------------------------------------------------
# 9. the hook NEVER writes the memory layer (only the ephemeral touched-flag)
# ---------------------------------------------------------------------------

def test_hook_never_writes_memory(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    # Make the spec dirty in a way that triggers BOTH a block and a nudge.
    _append_to(proj, "prds/auth.md", "\nApproved edit, no DEC yet.\n")
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (proj / "src" / "app.py").write_text("print('x')\n", encoding="utf-8")

    mem = proj / "docs" / "product" / ".memory"
    before = _dir_snapshot(mem)
    decisions = (proj / "docs" / "product" / "decisions.md")
    dec_before = decisions.read_text(encoding="utf-8") if decisions.exists() else None

    mod.set_touched_flag("sess-1")
    # Run the Stop hook (it will block — fence persist).
    mod.handle_stop(_load_stdin_dict(_stop_stdin(proj)), str(proj))

    after = _dir_snapshot(mem)
    dec_after = decisions.read_text(encoding="utf-8") if decisions.exists() else None
    assert before == after, "the hook must not mutate .memory/"
    assert dec_before == dec_after, "the hook must not mutate decisions.md"


def _dir_snapshot(d: Path):
    """Map of relative-path -> bytes for every file under `d` (or {} if absent)."""
    if not d.exists():
        return {}
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(d))] = p.read_bytes()
    return out


# ---------------------------------------------------------------------------
# CLI shape — the hook is invokable as a standalone file in both modes
# ---------------------------------------------------------------------------

def test_cli_stop_mode_blocks_exit_two(tmp_path, monkeypatch):
    """End-to-end through a subprocess (how CC invokes it): a fence breach blocks
    with exit 2 and JSON on stdout; the touched-flag must be set first."""
    tdir = _isolate_tmp(tmp_path, monkeypatch)
    proj = _proj(tmp_path)
    _validate_baseline(proj)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "validated")
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (proj / "src" / "app.py").write_text("print('x')\n", encoding="utf-8")

    # Set the flag via the PostToolUse subprocess path (full round-trip).
    inside = str(proj / "docs" / "product" / "prds" / "auth.md")
    rc_p, _, _ = _run_hook("post", _post_tool_stdin(proj, inside),
                           proj, env_extra={"TMPDIR": str(tdir)})
    assert rc_p == 0

    rc, out, err = _run_hook("stop", _stop_stdin(proj), proj,
                             env_extra={"TMPDIR": str(tdir)})
    assert rc == 2, (out, err)
    payload = json.loads(out)
    assert payload["ok"] is False


def test_cli_stop_mode_noop_exit_zero(tmp_path, monkeypatch):
    """No touched-flag → the Stop subprocess exits 0 fast (no detector run)."""
    tdir = _isolate_tmp(tmp_path, monkeypatch)
    proj = _proj(tmp_path)
    rc, out, err = _run_hook("stop", _stop_stdin(proj), proj,
                             env_extra={"TMPDIR": str(tdir)})
    assert rc == 0, (out, err)
