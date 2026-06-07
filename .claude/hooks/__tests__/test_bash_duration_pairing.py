"""test_bash_duration_pairing.py — PreToolUse:Bash (mark_bash_start) +
PostToolUse:Bash (track_script_execution) duration pairing.

Covers: Pre stamps a start mark + Post computes `ms` (int ≥ 0) and clears the
mark; missing Pre → record without `ms` (graceful degrade); non-skill commands
create no mark / no record; pytest/disabled silence.
"""
import importlib
import json
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parent.parent
_LIB = _HOOKS.parent / "skills" / "_shared" / "lib"
sys.path.insert(0, str(_LIB))
sys.path.insert(0, str(_HOOKS))

SKILL_CMD = '.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/validate.py --root .'


def _reload(tmp_path, monkeypatch, extra=None):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
    for k, v in (extra or {}).items():
        monkeypatch.setenv(k, v)
    for m in ("telemetry_paths", "mark_bash_start", "track_script_execution"):
        sys.modules.pop(m, None)
    import telemetry_paths, mark_bash_start, track_script_execution  # noqa
    importlib.reload(telemetry_paths)
    importlib.reload(mark_bash_start)
    importlib.reload(track_script_execution)
    monkeypatch.setattr(mark_bash_start.sys.stdout, "write", lambda _s: None)
    monkeypatch.setattr(track_script_execution.sys.stdout, "write", lambda _s: None)
    return telemetry_paths, mark_bash_start, track_script_execution


def _lines(tmp_path, name="hook-telemetry.jsonl"):
    p = tmp_path / name
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def _pre_payload(cmd, session="s1"):
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "session_id": session})


def _post_payload(cmd, session="s1", resp=None):
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd},
                       "tool_response": resp or {}, "session_id": session})


class TestPairing:
    def test_pre_then_post_yields_ms(self, tmp_path, monkeypatch):
        _tp, pre, post = _reload(tmp_path, monkeypatch)
        pre.main(_pre_payload(SKILL_CMD))
        post.main(_post_payload(SKILL_CMD))
        recs = _lines(tmp_path)
        assert len(recs) == 1
        assert "ms" in recs[0]
        assert isinstance(recs[0]["ms"], int) and recs[0]["ms"] >= 0
        assert recs[0]["exit"] == 0

    def test_mark_is_cleared_after_post(self, tmp_path, monkeypatch):
        tpmod, pre, post = _reload(tmp_path, monkeypatch)
        pre.main(_pre_payload(SKILL_CMD))
        # The .bashtimers marker exists after Pre …
        timer_dir = tpmod.telemetry_dir() / ".bashtimers"
        assert any(timer_dir.iterdir())
        post.main(_post_payload(SKILL_CMD))
        # … and is consumed (cleared) after Post.
        assert not any(timer_dir.iterdir())

    def test_missing_pre_degrades_without_ms(self, tmp_path, monkeypatch):
        _tp, _pre, post = _reload(tmp_path, monkeypatch)
        post.main(_post_payload(SKILL_CMD))
        recs = _lines(tmp_path)
        assert len(recs) == 1
        assert "ms" not in recs[0]

    def test_different_command_does_not_pair(self, tmp_path, monkeypatch):
        _tp, pre, post = _reload(tmp_path, monkeypatch)
        pre.main(_pre_payload(SKILL_CMD))
        other = '.claude/skills/.venv/bin/python3 .claude/skills/release/scripts/release.py --bump patch'
        post.main(_post_payload(other))
        recs = _lines(tmp_path)
        assert len(recs) == 1
        assert "ms" not in recs[0], "a different command must not consume another's mark"


class TestFilterAndSilence:
    def test_non_skill_command_no_mark_no_record(self, tmp_path, monkeypatch):
        tpmod, pre, post = _reload(tmp_path, monkeypatch)
        pre.main(_pre_payload("git status"))
        post.main(_post_payload("git status"))
        assert _lines(tmp_path) == []
        assert not (tpmod.telemetry_dir() / ".bashtimers").exists() or \
            not any((tpmod.telemetry_dir() / ".bashtimers").iterdir())

    def test_disabled_no_writes(self, tmp_path, monkeypatch):
        _tp, pre, post = _reload(tmp_path, monkeypatch, extra={"CK_TELEMETRY_DISABLED": "1"})
        pre.main(_pre_payload(SKILL_CMD))
        post.main(_post_payload(SKILL_CMD))
        assert _lines(tmp_path) == []
