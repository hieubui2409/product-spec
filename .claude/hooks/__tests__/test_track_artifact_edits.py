"""
test_track_artifact_edits.py — TDD tests for the artifact-edit tracking hook.

Tests:
1. Privacy gate (H3): content-bearing payload → record keys EXACTLY {ts,artifact_path,op,session},
   content fields absent from the serialized record.
2. Negative: edit outside spec tree → no event recorded.
3. op field reflects tool name (Edit/Write/MultiEdit).
4. Fail-open: malformed/empty stdin → exits 0, records nothing, does not raise.
5. (lens tests are in test_lens_artifact_heat.py)
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

SINK_NAME = "artifact-events.jsonl"


def _reload_lib(tmp_path, monkeypatch):
    """Reload telemetry_paths with CK_TELEMETRY_DIR pointing at tmp_path."""
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
    for mod_name in ("telemetry_paths", "hook_runtime"):
        sys.modules.pop(mod_name, None)
    import telemetry_paths
    importlib.reload(telemetry_paths)
    return telemetry_paths


def _reload_hook(tmp_path, monkeypatch):
    """Reload track_artifact_edits with fresh env pointing at tmp_path."""
    _reload_lib(tmp_path, monkeypatch)
    sys.modules.pop("track_artifact_edits", None)
    mod = importlib.import_module("track_artifact_edits")
    importlib.reload(mod)
    return mod


def _sink_lines(tmp_path: Path) -> list[dict]:
    p = tmp_path / SINK_NAME
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Test 1: Privacy gate (H3) — whitelist construction, EXACT key-set
# ---------------------------------------------------------------------------

class TestHookRecordsExactKeysetStripsContent:
    """H3 red-team: feed a content-bearing PostToolUse payload; the persisted
    record must contain EXACTLY {ts, artifact_path, op, session} — no content
    field can leak regardless of payload shape."""

    def test_hook_records_exact_keyset_strips_content(self, tmp_path, monkeypatch):
        mod = _reload_hook(tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        # Realistic PostToolUse payload WITH content fields
        payload = json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "docs/product/PRODUCT.md",
                "old_string": "## Old section\nsome confidential PO text",
                "new_string": "## New section\nupdated confidential content",
                "command": "should not appear",
            },
            "tool_response": {
                "content": "File edited successfully",
                "stdout": "secret output",
                "stderr": "",
            },
            "session_id": "sess-privacy-01",
        })

        mod.main(payload)

        lines = _sink_lines(tmp_path)
        assert len(lines) == 1, "one edit to a spec artifact must produce exactly one record"
        record = lines[0]

        # EXACT key-set assertion — the core H3 invariant
        assert set(record.keys()) == {"ts", "artifact_path", "op", "session"}, (
            f"record must contain EXACTLY {{ts, artifact_path, op, session}}, got: {set(record.keys())}"
        )

        # Content strings must be absent from the serialized record
        raw = json.dumps(record)
        assert "old_string" not in raw
        assert "new_string" not in raw
        assert "Old section" not in raw
        assert "New section" not in raw
        assert "confidential" not in raw
        assert "stdout" not in raw
        assert "secret output" not in raw
        assert "tool_response" not in raw
        assert "command" not in raw

        # Path field is the artifact path, not content
        assert record["artifact_path"] == "docs/product/PRODUCT.md"
        assert record["op"] == "Edit"
        assert record["session"] == "sess-privacy-01"


# ---------------------------------------------------------------------------
# Test 2: Negative — edit outside spec tree → no event
# ---------------------------------------------------------------------------

class TestHookFiresOnlyForSpecArtifacts:
    """Edits to paths outside docs/product/** must not produce any records."""

    def test_edit_outside_spec_tree_produces_no_record(self, tmp_path, monkeypatch):
        mod = _reload_hook(tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        outside_paths = [
            ".claude/hooks/some_hook.py",
            "src/main.py",
            "README.md",
            ".claude/skills/telemetry/scripts/lens_health.py",
            "docs/code-standards.md",  # docs/ but not docs/product/
        ]

        for path in outside_paths:
            mod.main(json.dumps({
                "hook_event_name": "PostToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": path},
                "session_id": "sess-outside",
            }))

        assert _sink_lines(tmp_path) == [], (
            f"edits outside docs/product/ must produce zero records, got: {_sink_lines(tmp_path)}"
        )

    def test_edit_within_spec_tree_produces_a_record(self, tmp_path, monkeypatch):
        """Positive counterpart: edits within docs/product/ ARE recorded."""
        mod = _reload_hook(tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        mod.main(json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "docs/product/epics/EPIC-1.md"},
            "session_id": "sess-inside",
        }))

        lines = _sink_lines(tmp_path)
        assert len(lines) == 1
        assert lines[0]["artifact_path"] == "docs/product/epics/EPIC-1.md"


# ---------------------------------------------------------------------------
# Test 3: op type reflects tool name
# ---------------------------------------------------------------------------

class TestHookRecordsOpType:
    """op field must reflect the actual tool name used."""

    def test_op_field_reflects_tool_name(self, tmp_path, monkeypatch):
        mod = _reload_hook(tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        tools = ["Edit", "Write", "MultiEdit"]
        for tool in tools:
            mod.main(json.dumps({
                "hook_event_name": "PostToolUse",
                "tool_name": tool,
                "tool_input": {"file_path": "docs/product/PRODUCT.md"},
                "session_id": "sess-op",
            }))

        lines = _sink_lines(tmp_path)
        assert len(lines) == 3
        assert [r["op"] for r in lines] == tools


# ---------------------------------------------------------------------------
# Test 4: Fail-open — malformed/empty stdin
# ---------------------------------------------------------------------------

class TestHookFailopenOnBadPayload:
    """Malformed or empty stdin must not raise; hook exits 0, records nothing."""

    def test_malformed_stdin_exits_zero_records_nothing(self, tmp_path, monkeypatch):
        mod = _reload_hook(tmp_path, monkeypatch)
        out_parts: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        # Should not raise
        mod.main("{bad json }{")

        assert '"continue"' in "".join(out_parts), "must always emit continue:true"
        assert _sink_lines(tmp_path) == [], "malformed stdin must record nothing"

    def test_empty_stdin_exits_zero_records_nothing(self, tmp_path, monkeypatch):
        mod = _reload_hook(tmp_path, monkeypatch)
        out_parts: list[str] = []
        monkeypatch.setattr(sys.stdout, "write", lambda s: out_parts.append(s))

        mod.main("")

        assert '"continue"' in "".join(out_parts)
        assert _sink_lines(tmp_path) == []

    def test_missing_file_path_produces_no_record(self, tmp_path, monkeypatch):
        """Payload with no tool_input.file_path → ignore, no crash."""
        mod = _reload_hook(tmp_path, monkeypatch)
        monkeypatch.setattr(sys.stdout, "write", lambda _: None)

        mod.main(json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {},  # no file_path
            "session_id": "sess-nopath",
        }))

        assert _sink_lines(tmp_path) == []
