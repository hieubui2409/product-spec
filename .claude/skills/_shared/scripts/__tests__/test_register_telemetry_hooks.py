"""
test_register_telemetry_hooks.py — pytest suite for register_telemetry_hooks.py.

Tests idempotent wiring of Python telemetry hooks into settings.json:
  - registers all events; preserves ck-managed entries
  - idempotent: second run adds zero new entries
  - --check exits 1 before registration, 0 after
  - --remove strips all telemetry + legacy node .cjs entries, restores ck-only shape
  - --prune-spike removes spike entries, keeps other telemetry + ck
  - legacy node .cjs commands are replaced (not duplicated) on register
"""

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS))

# A minimal ck-managed settings.json: one pre-existing Stop hook + a PreToolUse
# group we must NOT disturb.
CK_SETTINGS: dict = {
    "hooks": {
        "Stop": [{"hooks": [{"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/session-state.cjs'}]}],
        "PreToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/descriptive-name.cjs'}]}],
    }
}

# Settings that already have the old node .cjs telemetry registrations wired.
LEGACY_SETTINGS: dict = {
    "hooks": {
        "Stop": [{"hooks": [
            {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/session-state.cjs'},
            {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/emit-session-summary.cjs'},
        ]}],
        "PreToolUse": [
            {"matcher": "Write",  "hooks": [{"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/descriptive-name.cjs'}]},
            {"matcher": "Skill",  "hooks": [
                {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/track-skill-invocation.cjs'},
                {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/telemetry-spike.cjs'},
            ]},
        ],
        "PostToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/track-script-execution.cjs'},
            {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/telemetry-spike.cjs'},
        ]}],
        "UserPromptExpansion": [{"hooks": [
            {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/track-skill-invocation.cjs'},
            {"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR"/.claude/hooks/telemetry-spike.cjs'},
        ]}],
    }
}


def _load(root: Path, monkeypatch) -> object:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    sys.modules.pop("register_telemetry_hooks", None)
    mod = importlib.import_module("register_telemetry_hooks")
    importlib.reload(mod)
    return mod


def _write_settings(root: Path, data: dict) -> None:
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "settings.json").write_text(json.dumps(data, indent=2))


def _read_settings(root: Path) -> dict:
    return json.loads((root / ".claude" / "settings.json").read_text())


def _all_commands(s: dict) -> list[str]:
    out: list[str] = []
    for arr in (s.get("hooks") or {}).values():
        for g in arr:
            for h in (g.get("hooks") or []):
                if h.get("command"):
                    out.append(h["command"])
    return out


# ---------------------------------------------------------------------------
# register (default)
# ---------------------------------------------------------------------------

class TestRegister:
    def test_registers_all_events_preserves_ck_entries(self, tmp_path, monkeypatch):
        _write_settings(tmp_path, CK_SETTINGS)
        mod = _load(tmp_path, monkeypatch)

        rc = mod.main([])
        assert rc == 0

        s = _read_settings(tmp_path)
        cmds = _all_commands(s)

        # ck entries intact
        assert any("session-state.cjs" in c for c in cmds), "ck Stop hook preserved"
        assert any("descriptive-name.cjs" in c for c in cmds), "ck PreToolUse hook preserved"

        # Python telemetry wired
        assert any("track_skill_invocation.py" in c for c in cmds)
        assert any("track_script_execution.py" in c for c in cmds)
        assert any("emit_session_summary.py" in c for c in cmds)

        # ship-both: skill hook on BOTH PreToolUse:Skill AND UserPromptExpansion
        skill_group = next((g for g in s["hooks"]["PreToolUse"] if g.get("matcher") == "Skill"), None)
        assert skill_group is not None
        assert any("track_skill_invocation.py" in h["command"] for h in skill_group["hooks"])
        assert any("track_skill_invocation.py" in h["command"] for h in s["hooks"]["UserPromptExpansion"][0]["hooks"])

        # Stop has BOTH session-state (ck) and emit_session_summary (telemetry)
        stop_cmds = [h["command"] for g in s["hooks"]["Stop"] for h in g.get("hooks", [])]
        assert any("session-state.cjs" in c for c in stop_cmds)
        assert any("emit_session_summary.py" in c for c in stop_cmds)

    def test_idempotent_second_run_adds_nothing(self, tmp_path, monkeypatch, capsys):
        _write_settings(tmp_path, CK_SETTINGS)
        mod = _load(tmp_path, monkeypatch)
        mod.main([])
        count_after_first = len(_all_commands(_read_settings(tmp_path)))

        mod2 = _load(tmp_path, monkeypatch)
        rc = mod2.main([])
        assert rc == 0

        captured = capsys.readouterr()
        assert "0 new entr" in captured.out
        assert len(_all_commands(_read_settings(tmp_path))) == count_after_first

    def test_replaces_legacy_node_cjs_telemetry_no_double_fire(self, tmp_path, monkeypatch):
        """If old node .cjs telemetry hooks exist they are removed, Python ones inserted."""
        _write_settings(tmp_path, LEGACY_SETTINGS)
        mod = _load(tmp_path, monkeypatch)

        mod.main([])

        cmds = _all_commands(_read_settings(tmp_path))
        # No legacy telemetry .cjs should remain
        legacy = [c for c in cmds if any(p in c for p in [
            "track-skill-invocation.cjs",
            "track-script-execution.cjs",
            "emit-session-summary.cjs",
            "telemetry-spike.cjs",
        ])]
        assert legacy == [], f"legacy node .cjs entries must be removed: {legacy}"
        # Python hooks are present
        assert any("track_skill_invocation.py" in c for c in cmds)
        assert any("track_script_execution.py" in c for c in cmds)
        assert any("emit_session_summary.py" in c for c in cmds)
        # ck non-telemetry entries still intact
        assert any("session-state.cjs" in c for c in cmds)
        assert any("descriptive-name.cjs" in c for c in cmds)


# ---------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------

class TestCheck:
    def test_check_exits_1_before_register_0_after(self, tmp_path, monkeypatch):
        _write_settings(tmp_path, CK_SETTINGS)

        mod = _load(tmp_path, monkeypatch)
        assert mod.main(["--check"]) == 1

        mod.main([])

        mod2 = _load(tmp_path, monkeypatch)
        assert mod2.main(["--check"]) == 0


# ---------------------------------------------------------------------------
# --remove
# ---------------------------------------------------------------------------

class TestRemove:
    def test_remove_strips_all_telemetry_restores_ck_only_shape(self, tmp_path, monkeypatch):
        _write_settings(tmp_path, CK_SETTINGS)
        mod = _load(tmp_path, monkeypatch)
        mod.main([])

        mod2 = _load(tmp_path, monkeypatch)
        rc = mod2.main(["--remove"])
        assert rc == 0

        s = _read_settings(tmp_path)
        cmds = _all_commands(s)
        assert not any(x in c for c in cmds for x in ["track_skill", "track_script", "emit_session"]), \
            "all telemetry gone after --remove"
        assert any("session-state.cjs" in c for c in cmds), "ck Stop intact"
        assert any("descriptive-name.cjs" in c for c in cmds), "ck PreToolUse intact"
        # UserPromptExpansion was created by telemetry-only → removed entirely
        assert "UserPromptExpansion" not in s.get("hooks", {}), \
            "telemetry-only event key dropped when emptied"

    def test_remove_also_strips_legacy_node_cjs(self, tmp_path, monkeypatch):
        _write_settings(tmp_path, LEGACY_SETTINGS)
        mod = _load(tmp_path, monkeypatch)
        mod.main(["--remove"])

        cmds = _all_commands(_read_settings(tmp_path))
        assert not any(p in c for c in cmds for p in [
            "track-skill-invocation.cjs",
            "track-script-execution.cjs",
            "emit-session-summary.cjs",
            "telemetry-spike.cjs",
        ]), "legacy node .cjs entries removed by --remove"
        assert any("session-state.cjs" in c for c in cmds)
        assert any("descriptive-name.cjs" in c for c in cmds)


# ---------------------------------------------------------------------------
# --prune-spike
# ---------------------------------------------------------------------------

class TestPruneSpike:
    def test_prune_spike_removes_spike_keeps_other_telemetry_and_ck(self, tmp_path, monkeypatch):
        _write_settings(tmp_path, CK_SETTINGS)
        mod = _load(tmp_path, monkeypatch)
        mod.main([])

        mod2 = _load(tmp_path, monkeypatch)
        rc = mod2.main(["--prune-spike"])
        assert rc == 0

        cmds = _all_commands(_read_settings(tmp_path))
        assert not any("telemetry-spike" in c for c in cmds), "spike entries gone"
        assert any("track_skill_invocation.py" in c for c in cmds), "skill hook stays"
        assert any("session-state.cjs" in c for c in cmds), "ck stays"

    def test_prune_spike_also_removes_legacy_spike_cjs(self, tmp_path, monkeypatch):
        _write_settings(tmp_path, LEGACY_SETTINGS)
        mod = _load(tmp_path, monkeypatch)
        mod.main(["--prune-spike"])

        cmds = _all_commands(_read_settings(tmp_path))
        assert not any("telemetry-spike.cjs" in c for c in cmds)
