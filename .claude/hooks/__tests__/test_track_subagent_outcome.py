"""test_track_subagent_outcome.py — SubagentStop telemetry hook.

Covers: explicit-outcome passthrough, transcript-tail classification
(success / api_error / timeout / blocked / unknown), agent_type resolution
(payload field → filename fallback), fail-open on malformed input, and
pytest/CK_TELEMETRY_DISABLED silence. Mirrors the reload-with-fresh-env pattern
of test_telemetry_hooks.py so writes actually happen inside the test body.
"""
import importlib
import json
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parent.parent
_LIB = _HOOKS.parent / "skills" / "_shared" / "lib"
sys.path.insert(0, str(_LIB))
sys.path.insert(0, str(_HOOKS))


def _reload(tmp_path, monkeypatch, extra=None):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
    for k, v in (extra or {}).items():
        monkeypatch.setenv(k, v)
    for m in ("telemetry_paths", "track_subagent_outcome"):
        sys.modules.pop(m, None)
    import telemetry_paths, track_subagent_outcome  # noqa
    importlib.reload(telemetry_paths)
    importlib.reload(track_subagent_outcome)
    monkeypatch.setattr(track_subagent_outcome.sys.stdout, "write", lambda _s: None)
    return track_subagent_outcome


def _lines(tmp_path, name="subagent-outcomes.jsonl"):
    p = tmp_path / name
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def _transcript(tmp_path, name, rows):
    p = tmp_path / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return str(p)


class TestExplicitOutcome:
    def test_explicit_timeout_recorded_with_agent_type(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        mod.main(json.dumps({"agent_type": "researcher", "outcome": "timeout", "session_id": "s1"}))
        recs = _lines(tmp_path)
        assert len(recs) == 1
        assert recs[0]["outcome"] == "timeout"
        assert recs[0]["agent_type"] == "researcher"
        assert recs[0]["session"] == "s1"

    def test_unknown_enum_value_falls_through_to_unknown(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        mod.main(json.dumps({"agent_type": "x", "outcome": "weird-value"}))
        assert _lines(tmp_path)[0]["outcome"] == "unknown"


class TestTranscriptClassification:
    def test_clean_stop_is_success(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        tp = _transcript(tmp_path, "agent-coder-1.jsonl", [
            {"message": {"role": "assistant", "stop_reason": "end_turn",
                         "content": [{"type": "text", "text": "done"}]}},
        ])
        mod.main(json.dumps({"transcript_path": tp, "session_id": "s1"}))
        assert _lines(tmp_path)[0]["outcome"] == "success"

    def test_api_error_text_is_api_error(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        tp = _transcript(tmp_path, "agent-researcher-9.jsonl", [
            {"message": {"role": "assistant",
                         "content": [{"type": "text", "text": "Overloaded: status 529"}]}},
        ])
        mod.main(json.dumps({"transcript_path": tp}))
        assert _lines(tmp_path)[0]["outcome"] == "api_error"

    def test_no_clean_stop_no_error_is_unknown_not_success(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        tp = _transcript(tmp_path, "agent-x-2.jsonl", [
            {"message": {"role": "assistant",
                         "content": [{"type": "tool_use", "name": "Bash", "input": {}}]}},
        ])
        mod.main(json.dumps({"transcript_path": tp}))
        assert _lines(tmp_path)[0]["outcome"] == "unknown"

    def test_agent_type_from_filename_when_payload_lacks_it(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        tp = _transcript(tmp_path, "agent-code-reviewer-abc123.jsonl", [
            {"message": {"role": "assistant", "stop_reason": "end_turn", "content": []}},
        ])
        mod.main(json.dumps({"transcript_path": tp}))
        assert _lines(tmp_path)[0]["agent_type"] == "code-reviewer"

    def test_no_transcript_no_explicit_is_unknown(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        mod.main(json.dumps({"session_id": "s1"}))
        assert _lines(tmp_path)[0]["outcome"] == "unknown"


class TestFailOpen:
    def test_malformed_stdin_does_not_raise_and_continues(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch)
        out = []
        monkeypatch.setattr(mod.sys.stdout, "write", lambda s: out.append(s))
        mod.main("not json }{")
        assert '"continue"' in "".join(out)

    def test_disabled_no_write(self, tmp_path, monkeypatch):
        mod = _reload(tmp_path, monkeypatch, extra={"CK_TELEMETRY_DISABLED": "1"})
        mod.main(json.dumps({"agent_type": "x", "outcome": "success"}))
        assert _lines(tmp_path) == []
