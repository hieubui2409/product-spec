"""test_register_new_hooks.py — the 2 NEW telemetry registrations added for the
usage-&-health lenses: PreToolUse:Bash → mark_bash_start.py and SubagentStop →
track_subagent_outcome.py. Asserts they register, are idempotent, pass --check,
and are stripped by --remove — without disturbing the pre-existing telemetry or
ck-managed entries.
"""
import importlib
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS))

CK_SETTINGS = {
    "hooks": {
        "Stop": [{"hooks": [{"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/session-state.cjs'}]}],
        "PreToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/descriptive-name.cjs'}]}],
    }
}


def _load(root, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    sys.modules.pop("register_telemetry_hooks", None)
    import register_telemetry_hooks as m
    importlib.reload(m)
    return m


def _write(root, data):
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "settings.json").write_text(json.dumps(data, indent=2))


def _read(root):
    return json.loads((root / ".claude" / "settings.json").read_text())


def _cmds(s):
    return [h["command"] for arr in (s.get("hooks") or {}).values() for g in arr for h in (g.get("hooks") or []) if h.get("command")]


def test_new_hooks_registered_on_correct_events(tmp_path, monkeypatch):
    _write(tmp_path, CK_SETTINGS)
    mod = _load(tmp_path, monkeypatch)
    mod.main([])
    s = _read(tmp_path)

    # PreToolUse:Bash carries mark_bash_start.py
    bash_pre = next((g for g in s["hooks"]["PreToolUse"] if g.get("matcher") == "Bash"), None)
    assert bash_pre is not None
    assert any("mark_bash_start.py" in h["command"] for h in bash_pre["hooks"])

    # SubagentStop carries track_subagent_outcome.py
    assert "SubagentStop" in s["hooks"]
    assert any("track_subagent_outcome.py" in c for g in s["hooks"]["SubagentStop"] for c in [h["command"] for h in g["hooks"]])

    # ck entries untouched
    assert any("descriptive-name.cjs" in c for c in _cmds(s))
    assert any("session-state.cjs" in c for c in _cmds(s))


def test_idempotent_second_run_adds_nothing(tmp_path, monkeypatch, capsys):
    _write(tmp_path, CK_SETTINGS)
    _load(tmp_path, monkeypatch).main([])
    first = len(_cmds(_read(tmp_path)))
    _load(tmp_path, monkeypatch).main([])
    assert len(_cmds(_read(tmp_path))) == first


def test_check_passes_after_register_for_new_hooks(tmp_path, monkeypatch):
    _write(tmp_path, CK_SETTINGS)
    assert _load(tmp_path, monkeypatch).main(["--check"]) == 1
    _load(tmp_path, monkeypatch).main([])
    assert _load(tmp_path, monkeypatch).main(["--check"]) == 0


def test_remove_strips_new_hooks_too(tmp_path, monkeypatch):
    _write(tmp_path, CK_SETTINGS)
    _load(tmp_path, monkeypatch).main([])
    _load(tmp_path, monkeypatch).main(["--remove"])
    cmds = _cmds(_read(tmp_path))
    assert not any("mark_bash_start.py" in c for c in cmds)
    assert not any("track_subagent_outcome.py" in c for c in cmds)
    # Bash PreToolUse group is telemetry-only here → removed once emptied.
    s = _read(tmp_path)
    bash_pre = next((g for g in s["hooks"].get("PreToolUse", []) if g.get("matcher") == "Bash"), None)
    assert bash_pre is None
    assert "SubagentStop" not in s.get("hooks", {})
    # ck entries survive
    assert any("descriptive-name.cjs" in c for c in cmds)
