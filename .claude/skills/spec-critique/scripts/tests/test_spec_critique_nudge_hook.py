"""Tests for the opt-in ADVISORY Stop hook `.claude/hooks/spec_critique_nudge.py`.

The hook nudges (never blocks) when the spec drifted >= threshold node bodies since
the last critique, gated cheaply on "a --validate happened since the last critique".
It must: emit `hookSpecificOutput.additionalContext` + exit 0, nudge once per session
per drift-count, and NEVER emit `decision:block` / exit 2. Any failure → silent exit 0.

The hook is loaded by path (CC invokes it as a standalone file). Drift is delegated
to critique_scan.py; with no judgments.json it falls back to a live build, which is
enough to exercise the nudge path here.
"""

import importlib.util
import io
import json
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

from critique_test_support import make_proj, append_to, run_scan

HOOK_PATH = (
    Path(__file__).resolve().parents[4] / "hooks" / "spec_critique_nudge.py"
)


def _load_hook():
    spec = importlib.util.spec_from_file_location("spec_critique_nudge", HOOK_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _isolate_tmp(tmp_path, monkeypatch):
    tdir = tmp_path / "tmp"
    tdir.mkdir()
    monkeypatch.setenv("TMPDIR", str(tdir))
    return tdir


def _set_threshold(proj, n):
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "preferences.yaml").write_text(f"critique_drift_threshold: {n}\n", encoding="utf-8")


def _mark_validated_newer(proj):
    """Write last_validated.json with an mtime strictly newer than last_critique.json
    so the hook's cheap gate (validate-since-critique) passes."""
    mem = proj / "docs" / "product" / ".memory"
    lv = mem / "last_validated.json"
    lv.write_text("{}", encoding="utf-8")
    lc = mem / "last_critique.json"
    if lc.exists():
        future = lc.stat().st_mtime + 10
        import os
        os.utime(lv, (future, future))


def _run_stop(mod, proj, *, session_id="sess-1", stop_hook_active=False):
    payload = {"session_id": session_id, "cwd": str(proj), "hook_event_name": "Stop"}
    if stop_hook_active:
        payload["stop_hook_active"] = True
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.handle_stop(payload, str(proj))
    return rc, buf.getvalue()


def _drifted_project(tmp_path, threshold=1):
    """A project where the spec drifted >= threshold since the last critique, with a
    fresh --validate marker so the cheap gate passes."""
    proj = make_proj(tmp_path)
    _set_threshold(proj, threshold)
    run_scan(proj, "--snapshot", "--scope", "all")  # last_critique baseline
    append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\n\nbody edit shifts the hash\n")
    _mark_validated_newer(proj)
    return proj


# ---------------------------------------------------------------------------

def test_nudge_fires_once_over_threshold(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _drifted_project(tmp_path, threshold=1)

    rc, out = _run_stop(mod, proj)
    assert rc == 0
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "/spec-critique" in payload["hookSpecificOutput"]["additionalContext"]
    # Advisory contract: never a block decision.
    assert "decision" not in payload


def test_nudge_silent_second_call_same_session(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _drifted_project(tmp_path, threshold=1)

    rc1, out1 = _run_stop(mod, proj)
    assert out1.strip()  # nudged
    rc2, out2 = _run_stop(mod, proj)
    assert rc2 == 0
    assert out2.strip() == ""  # silent — already nudged this session+count


def test_stop_hook_active_suppresses(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _drifted_project(tmp_path, threshold=1)

    rc, out = _run_stop(mod, proj, stop_hook_active=True)
    assert rc == 0
    assert out.strip() == ""


def test_under_threshold_silent(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _drifted_project(tmp_path, threshold=5)  # 1 change < 5

    rc, out = _run_stop(mod, proj)
    assert rc == 0
    assert out.strip() == ""


def test_no_spec_tree_noop(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    bare = tmp_path / "bare"
    bare.mkdir()
    rc, out = _run_stop(mod, bare)
    assert rc == 0
    assert out.strip() == ""


def test_gate_blocks_when_no_validate_since_critique(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = make_proj(tmp_path)
    _set_threshold(proj, 1)
    run_scan(proj, "--snapshot", "--scope", "all")
    append_to(proj, "stories/PRD-AUTH-E1-S1.md", "\n\nchanged\n")
    # No last_validated.json written → gate fails → silent even though drift exists.
    rc, out = _run_stop(mod, proj)
    assert rc == 0
    assert out.strip() == ""


def test_missing_critique_scan_graceful(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _drifted_project(tmp_path, threshold=1)
    # Point the scan resolver at a nonexistent path → _run_drift returns None → no-op.
    monkeypatch.setattr(mod, "_critique_scan_path", lambda: tmp_path / "nope.py")
    rc, out = _run_stop(mod, proj)
    assert rc == 0
    assert out.strip() == ""


def test_never_writes_under_docs_product(tmp_path, monkeypatch):
    _isolate_tmp(tmp_path, monkeypatch)
    mod = _load_hook()
    proj = _drifted_project(tmp_path, threshold=1)
    before = {p.name for p in (proj / "docs" / "product" / ".memory").iterdir()}
    _run_stop(mod, proj)
    after = {p.name for p in (proj / "docs" / "product" / ".memory").iterdir()}
    assert before == after  # hook created nothing under docs/product/
