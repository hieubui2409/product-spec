"""
test_telemetry_hooks.py — pytest integration suite for the 3 Python telemetry hooks.

Each hook is exercised by importing it directly (no subprocess) with the
CK_TELEMETRY_DIR env var redirected to a tmp directory so real sinks are
untouched. PYTEST_CURRENT_TEST is cleared so writes actually happen inside
the test body (the module-level disabled() check reads it at call time).

Covers:
  - track_skill_invocation: PreToolUse:Skill, UserPromptExpansion, non-skill
  - track_script_execution: skill-script match, error exit inference, non-skill
  - emit_session_summary: transcript → skills + files + duration
  - fail-open: CK_TELEMETRY_DISABLED → continue:true, no writes
  - JSONL non-forgery: skill name with embedded newline → 1 physical line
  - dedup: same session|skill|minute → exactly 1 record
  - script-path filter: only .claude/skills/*/scripts/*.py|sh paths recorded
"""

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

_HOOKS = Path(__file__).resolve().parent.parent
_LIB = _HOOKS.parent / "skills" / "telemetry" / "scripts"
sys.path.insert(0, str(_LIB))
sys.path.insert(0, str(_HOOKS))


def _reload_lib(tmp_path, monkeypatch, extra: dict | None = None):
    """Reload telemetry_paths with CK_TELEMETRY_DIR pointing at tmp_path."""
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
    if extra:
        for k, v in extra.items():
            monkeypatch.setenv(k, v)
    # Drop hook_runtime too so its per-process config cache is re-read fresh
    # (no CK_HOOK_CONFIG here → the real config loads; telemetry keys default on).
    for mod_name in ("telemetry_paths", "hook_runtime"):
        sys.modules.pop(mod_name, None)
    import telemetry_paths
    importlib.reload(telemetry_paths)
    return telemetry_paths


def _reload_hook(hook_module: str, tmp_path, monkeypatch, extra: dict | None = None):
    """Reload a hook module with fresh env."""
    _reload_lib(tmp_path, monkeypatch, extra)
    sys.modules.pop(hook_module, None)
    mod = importlib.import_module(hook_module)
    importlib.reload(mod)
    return mod


def _sink_lines(tmp_path: Path, name: str) -> list[dict]:
    p = tmp_path / name
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# track_skill_invocation
# ---------------------------------------------------------------------------

class TestTrackSkillInvocation:
    def test_pretooluse_skill_payload_writes_one_invocations_line(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_skill_invocation", tmp_path, monkeypatch)
        out_parts = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        mod.main(json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": "product-spec"},
            "session_id": "s1",
        }))

        out = "".join(out_parts)
        assert '"continue": true' in out or '"continue":true' in out
        lines = _sink_lines(tmp_path, "invocations.jsonl")
        assert len(lines) == 1
        assert lines[0]["skill"] == "product-spec"
        assert lines[0]["via"] == "PreToolUse:Skill"

    def test_userpromptexpansion_payload_slash_stripped(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_skill_invocation", tmp_path, monkeypatch)
        out_parts = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        mod.main(json.dumps({
            "hook_event_name": "UserPromptExpansion",
            "command": "/cook --auto plan.md",
            "session_id": "s2",
        }))

        out = "".join(out_parts)
        assert '"continue"' in out
        lines = _sink_lines(tmp_path, "invocations.jsonl")
        assert len(lines) == 1
        assert lines[0]["skill"] == "cook"
        assert lines[0]["via"] == "UserPromptExpansion"

    def test_non_skill_pretooluse_bash_no_write(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_skill_invocation", tmp_path, monkeypatch)
        out_parts = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        mod.main(json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "session_id": "s3",
        }))

        assert '"continue"' in "".join(out_parts)
        assert _sink_lines(tmp_path, "invocations.jsonl") == []

    def test_dedup_same_session_skill_minute_yields_one_record(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_skill_invocation", tmp_path, monkeypatch)
        out_parts: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        # Same session_id and skill; main() computes minute bucket from now —
        # both calls happen within the same minute in CI.
        payload = json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": "sample-skill"},
            "session_id": "sess-dedup",
        })
        mod.main(payload)
        # Reload hook but keep same telemetry_paths (same dedup dir).
        sys.modules.pop("track_skill_invocation", None)
        mod2 = importlib.import_module("track_skill_invocation")
        importlib.reload(mod2)
        out_parts2: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts2.append(s))
        mod2.main(payload)

        lines = _sink_lines(tmp_path, "invocations.jsonl")
        assert len(lines) == 1, "same session|skill|minute must collapse to 1 record"

    def test_jsonl_non_forgery_embedded_newline_in_skill_name(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_skill_invocation", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        evil = 'evil\n{"injected":true}'
        mod.main(json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": evil},
            "session_id": "s-evil",
        }))

        raw = (tmp_path / "invocations.jsonl").read_text()
        physical = [l for l in raw.splitlines() if l.strip()]
        assert len(physical) == 1, "embedded newline must not produce extra JSONL lines"
        assert json.loads(physical[0])["skill"] == evil


# ---------------------------------------------------------------------------
# track_script_execution
# ---------------------------------------------------------------------------

class TestTrackScriptExecution:
    def test_skill_script_bash_writes_hook_telemetry_line_exit_0(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        mod.main(json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": ".claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/visualize.py --root ."},
            "tool_response": {"stdout": "ok", "stderr": ""},
        }))

        lines = _sink_lines(tmp_path, "hook-telemetry.jsonl")
        assert len(lines) == 1
        assert lines[0]["script"] == "product-spec/scripts/visualize.py"
        assert lines[0]["exit"] == 0
        assert lines[0]["source"] == "hook:bash"

    def test_script_record_carries_session_join_key(self, tmp_path, monkeypatch):
        # The record must carry `session` so the workflow/health lenses can join it to
        # the other three sinks (which all record it). Previously computed but dropped.
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)
        mod.main(json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "session_id": "sess-join-1",
            "tool_input": {"command": ".claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/visualize.py --root ."},
            "tool_response": {"stdout": "ok", "stderr": ""},
        }))
        rec = _sink_lines(tmp_path, "hook-telemetry.jsonl")[0]
        assert rec["session"] == "sess-join-1"

    def test_error_in_tool_response_infers_exit_1(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        mod.main(json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 .claude/skills/sample-skill/scripts/foo.py"},
            "tool_response": {"is_error": True, "stderr": "Traceback (most recent call last):"},
        }))

        lines = _sink_lines(tmp_path, "hook-telemetry.jsonl")
        assert len(lines) == 1
        assert lines[0]["exit"] == 1

    def test_non_skill_bash_git_no_write(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        mod.main(json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
            "tool_response": {"stdout": ""},
        }))

        assert _sink_lines(tmp_path, "hook-telemetry.jsonl") == []

    def test_script_path_filter_ignores_paths_outside_skills_scripts(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        # A command containing .py but NOT inside .claude/skills/*/scripts/
        mod.main(json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 /tmp/random_script.py"},
            "tool_response": {"stdout": ""},
        }))

        assert _sink_lines(tmp_path, "hook-telemetry.jsonl") == []

    def test_reference_only_command_is_not_counted_as_run(self, tmp_path, monkeypatch):
        # grep/ls/cat that merely REFERENCE a skill-script path must not be recorded
        # as an execution — otherwise the validate-proxy (reading these records)
        # inflates the pass rate with greps over check_*.py.
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)
        for cmd in (
            "grep -n foo .claude/skills/product-spec/scripts/check_consistency.py",
            "ls .claude/skills/product-spec/scripts/visualize.py",
            "cat .claude/skills/release/scripts/release.py",
        ):
            mod.main(json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd},
                                 "tool_response": {"stdout": "x"}}))
        assert _sink_lines(tmp_path, "hook-telemetry.jsonl") == []

    def test_direct_and_compound_execution_are_counted(self, tmp_path, monkeypatch):
        # path at command start (direct exec) and after an interpreter in a
        # cd && python3 compound both count as real runs.
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)
        mod.main(json.dumps({"tool_name": "Bash",
            "tool_input": {"command": ".claude/skills/product-spec/scripts/visualize.py --root ."},
            "tool_response": {"stdout": "ok"}}))
        mod.main(json.dumps({"tool_name": "Bash",
            "tool_input": {"command": "cd /repo && python3 .claude/skills/release/scripts/release.py --bump patch"},
            "tool_response": {"stdout": "ok"}}))
        lines = _sink_lines(tmp_path, "hook-telemetry.jsonl")
        assert [l["script"] for l in lines] == [
            "product-spec/scripts/visualize.py", "release/scripts/release.py"]

    def test_absolute_and_var_prefixed_execution_are_counted(self, tmp_path, monkeypatch):
        # An executed script reached via an absolute or "$CLAUDE_PROJECT_DIR"-prefixed
        # path still counts; the leading dir prefix must not break detection and
        # group(1) stays the skill-relative path. (A grep/ls of such a path stays
        # rejected — the prefix cannot bridge the space at an argument position.)
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)
        mod.main(json.dumps({"tool_name": "Bash",
            "tool_input": {"command": "python3 /home/u/proj/.claude/skills/product-spec/scripts/validate.py --root ."},
            "tool_response": {"stdout": "ok"}}))
        mod.main(json.dumps({"tool_name": "Bash",
            "tool_input": {"command": '"$CLAUDE_PROJECT_DIR"/.claude/skills/.venv/bin/python3 "$CLAUDE_PROJECT_DIR"/.claude/skills/release/scripts/release.py'},
            "tool_response": {"stdout": "ok"}}))
        lines = _sink_lines(tmp_path, "hook-telemetry.jsonl")
        assert [l["script"] for l in lines] == [
            "product-spec/scripts/validate.py", "release/scripts/release.py"]

    def test_always_emits_continue_true(self, tmp_path, monkeypatch):
        mod = _reload_hook("track_script_execution", tmp_path, monkeypatch)
        out_parts: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        mod.main("{bad json")

        assert '"continue"' in "".join(out_parts)


# ---------------------------------------------------------------------------
# emit_session_summary
# ---------------------------------------------------------------------------

class TestEmitSessionSummary:
    def test_reads_transcript_path_writes_sessions_line(self, tmp_path, monkeypatch):
        mod = _reload_hook("emit_session_summary", tmp_path, monkeypatch)
        out_parts: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        transcript = tmp_path / "fake-session.jsonl"
        rows = [
            {"timestamp": "2026-06-06T10:00:00Z", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "product-spec"}}]}},
            {"timestamp": "2026-06-06T10:01:00Z", "message": {"content": [{"type": "tool_use", "name": "Write", "input": {"file_path": "/a.md"}}]}},
            {"timestamp": "2026-06-06T10:05:00Z", "message": {"content": [{"type": "tool_use", "name": "Task",  "input": {}}]}},
        ]
        transcript.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

        mod.main(json.dumps({"session_id": "sess-x", "transcript_path": str(transcript)}))

        assert '"continue"' in "".join(out_parts)
        lines = _sink_lines(tmp_path, "sessions.jsonl")
        assert len(lines) == 1
        rec = lines[0]
        assert rec["skills"] == ["product-spec"]
        assert rec["files_modified"] == 1
        assert rec["subagents"] == 1
        assert rec["duration_s"] == 300
        assert rec["session"] == "sess-x"

    def test_duration_nonzero_when_first_record_has_no_timestamp(self, tmp_path, monkeypatch):
        # A leading meta/summary record with no timestamp must not zero out duration:
        # scan forward to the first record that has one (the 43/43 duration_s:0 bug).
        mod = _reload_hook("emit_session_summary", tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda s: None)
        transcript = tmp_path / "no-leading-ts.jsonl"
        rows = [
            {"type": "summary", "summary": "meta record, no timestamp"},
            {"timestamp": "2026-06-06T10:00:00Z", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "product-spec"}}]}},
            {"timestamp": "2026-06-06T10:05:00Z", "message": {"content": [{"type": "tool_use", "name": "Write", "input": {"file_path": "/a.md"}}]}},
        ]
        transcript.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        mod.main(json.dumps({"session_id": "s", "transcript_path": str(transcript)}))
        rec = _sink_lines(tmp_path, "sessions.jsonl")[0]
        assert rec["duration_s"] == 300  # 10:00 → 10:05, not 0
        assert rec["skills"] == ["product-spec"]

    def test_scan_head_returns_first_ts_and_early_skills(self, tmp_path, monkeypatch):
        mod = _reload_hook("emit_session_summary", tmp_path, monkeypatch)
        transcript = tmp_path / "head.jsonl"
        rows = [
            {"type": "summary", "summary": "no timestamp here"},
            {"timestamp": "2026-06-06T09:00:00Z", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "product-spec"}}]}},
        ]
        transcript.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        ts, skills = mod.scan_head(str(transcript))
        assert ts == "2026-06-06T09:00:00Z"
        assert skills == ["product-spec"]

    def test_no_transcript_still_emits_continue_true(self, tmp_path, monkeypatch):
        mod = _reload_hook("emit_session_summary", tmp_path, monkeypatch)
        out_parts: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        mod.main(json.dumps({"session_id": "ghost", "transcript_path": "/nonexistent/path.jsonl"}))

        assert '"continue"' in "".join(out_parts)
        # No sessions line written because transcript missing — that's fine.


# ---------------------------------------------------------------------------
# fail-open: disabled telemetry still returns continue:true
# ---------------------------------------------------------------------------

class TestFailOpen:
    def test_ck_telemetry_disabled_hook_still_continues_no_writes(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.setenv("CK_TELEMETRY_DISABLED", "1")
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        for mod_name in ("telemetry_paths", "track_skill_invocation"):
            sys.modules.pop(mod_name, None)
        import telemetry_paths, track_skill_invocation
        importlib.reload(telemetry_paths)
        importlib.reload(track_skill_invocation)

        out_parts: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        track_skill_invocation.main(json.dumps({
            "tool_name": "Skill",
            "tool_input": {"skill": "x"},
            "session_id": "s",
        }))

        assert '"continue"' in "".join(out_parts)
        assert _sink_lines(tmp_path, "invocations.jsonl") == []

    def test_malformed_stdin_does_not_raise(self, tmp_path, monkeypatch):
        for hook in ("track_skill_invocation", "track_script_execution", "emit_session_summary"):
            mod = _reload_hook(hook, tmp_path, monkeypatch)
            out_parts: list[str] = []
            monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))
            mod.main("not json at all }{")
            assert '"continue"' in "".join(out_parts), f"{hook} must emit continue:true on bad stdin"
