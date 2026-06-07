"""
test_telemetry_paths.py — pytest suite for telemetry_paths.py.

Covers the fail-open invariants the telemetry layer promises:
  (a) append_event writes exactly one JSON line per call
  (b) disabled() short-circuits writes (env-gated, incl. test runs)
  (c) a sink over the size cap is rotated to .bak before the fresh write
  (d) any write failure or non-serializable record is swallowed (never raises)
  (e) append_event_once dedup: same key → 1 record; different keys → distinct
  (f) JSONL non-forgery: skill name with embedded newline/quotes → 1 physical line
"""

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

# Ensure the lib directory is importable.
_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))


def _load(tmp_path, extra_env: dict | None = None):
    """Import telemetry_paths fresh. Caller must set env via monkeypatch first.

    The helper only reloads the module — it does NOT touch os.environ so it
    cannot fight monkeypatch's cleanup. All env setup (CK_TELEMETRY_DIR,
    CK_TELEMETRY_DISABLED, PYTEST_CURRENT_TEST) is the caller's responsibility.
    """
    if "telemetry_paths" in sys.modules:
        del sys.modules["telemetry_paths"]
    import telemetry_paths
    importlib.reload(telemetry_paths)
    return telemetry_paths


def _read_lines(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# (a) basic write
# ---------------------------------------------------------------------------

class TestAppendEvent:
    def test_writes_exactly_one_parseable_json_line_per_call(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        mod.append_event("invocations.jsonl", {"ts": "T", "skill": "product-spec", "session": "s1"})
        mod.append_event("invocations.jsonl", {"ts": "T", "skill": "claude-pack",   "session": "s1"})

        sink = tmp_path / "invocations.jsonl"
        lines = _read_lines(sink)
        assert len(lines) == 2
        assert lines[0]["skill"] == "product-spec"
        assert lines[1]["skill"] == "claude-pack"

    # (b) disabled via CK_TELEMETRY_DISABLED
    def test_disabled_ck_telemetry_disabled_no_write(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.setenv("CK_TELEMETRY_DISABLED", "1")
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        assert mod.disabled() is True
        mod.append_event("invocations.jsonl", {"ts": "T", "skill": "x"})
        assert not (tmp_path / "invocations.jsonl").exists()

    # (b) disabled via PYTEST_CURRENT_TEST
    def test_disabled_pytest_current_test_no_write(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_x (call)")
        mod = _load(tmp_path)

        assert mod.disabled() is True
        mod.append_event("invocations.jsonl", {"ts": "T", "skill": "x"})
        assert not (tmp_path / "invocations.jsonl").exists()

    # (c) rotation at cap
    def test_rotates_sink_over_cap_to_bak(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        sink = tmp_path / "hook-telemetry.jsonl"
        # Extend the file past the 8 MB cap via truncate (creates a sparse hole
        # on Linux; no need to allocate 9 MB of real data).
        with open(sink, "wb") as fh:
            fh.truncate(9 * 1024 * 1024)

        mod.append_event("hook-telemetry.jsonl", {"ts": "T", "source": "hook:bash", "script": "a/scripts/b.py", "exit": 0})

        bak = Path(str(sink) + ".bak")
        assert bak.exists(), ".bak should exist after rotation"
        lines = _read_lines(sink)
        assert len(lines) == 1, "fresh sink holds exactly the new line"
        assert lines[0]["exit"] == 0

    # (d) swallow write failure
    def test_swallows_write_failure_unwritable_dir(self, tmp_path, monkeypatch):
        blocker = tmp_path / "blocker"
        blocker.write_text("i am a file")
        bad_dir = str(blocker / "nested")
        monkeypatch.setenv("CK_TELEMETRY_DIR", bad_dir)
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path, {"CK_TELEMETRY_DIR": bad_dir})

        # Must not raise
        mod.append_event("invocations.jsonl", {"ts": "T", "skill": "x"})

    # (d) swallow non-serializable record
    def test_swallows_non_serializable_record_circular_ref(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        circular: dict = {"ts": "T"}
        circular["self"] = circular  # type: ignore[assignment]

        mod.append_event("invocations.jsonl", circular)
        assert not (tmp_path / "invocations.jsonl").exists()


# ---------------------------------------------------------------------------
# (e) dedup / append_event_once
# ---------------------------------------------------------------------------

class TestAppendEventOnce:
    def test_same_dedup_key_yields_exactly_one_record(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        key = "s1|product-spec|2026-06-06T10:21"
        mod.append_event_once("invocations.jsonl", {"ts": "T", "skill": "product-spec", "via": "PreToolUse:Skill"}, key)
        mod.append_event_once("invocations.jsonl", {"ts": "T", "skill": "product-spec", "via": "UserPromptExpansion"}, key)

        lines = _read_lines(tmp_path / "invocations.jsonl")
        assert len(lines) == 1, "duplicate invocation logged once"
        assert lines[0]["via"] == "PreToolUse:Skill", "first event wins"

    def test_different_dedup_keys_yield_distinct_records(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        mod.append_event_once("invocations.jsonl", {"skill": "a"}, "s1|a|m1")
        mod.append_event_once("invocations.jsonl", {"skill": "b"}, "s1|b|m1")

        lines = _read_lines(tmp_path / "invocations.jsonl")
        assert len(lines) == 2

    def test_disabled_no_marker_no_write(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.setenv("CK_TELEMETRY_DISABLED", "1")
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        mod.append_event_once("invocations.jsonl", {"skill": "a"}, "s1|a|m1")
        assert not (tmp_path / "invocations.jsonl").exists()
        assert not (tmp_path / ".dedup").exists()


# ---------------------------------------------------------------------------
# (f) JSONL non-forgery: malicious skill names cannot inject extra lines
# ---------------------------------------------------------------------------

class TestJsonlNonForgery:
    def test_skill_name_with_embedded_newline_yields_exactly_one_physical_line(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        evil_skill = 'evil\n{"injected": true}'
        mod.append_event("invocations.jsonl", {"ts": "T", "skill": evil_skill})

        raw = (tmp_path / "invocations.jsonl").read_text()
        physical_lines = [l for l in raw.splitlines() if l.strip()]
        assert len(physical_lines) == 1, "embedded newline must not produce extra JSONL lines"
        parsed = json.loads(physical_lines[0])
        assert parsed["skill"] == evil_skill

    def test_skill_name_with_embedded_quotes_parses_as_single_record(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mod = _load(tmp_path)

        evil_skill = '"}{tricky'
        mod.append_event("invocations.jsonl", {"ts": "T", "skill": evil_skill})

        raw = (tmp_path / "invocations.jsonl").read_text()
        physical_lines = [l for l in raw.splitlines() if l.strip()]
        assert len(physical_lines) == 1
        assert json.loads(physical_lines[0])["skill"] == evil_skill
