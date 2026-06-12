"""test_harvester.py — TDD tests for harvester.py (usage-summary export + suggestion harvester).

Tests (RED first, then GREEN):
1. test_export_summary_writes_markdown — --export-summary out.md writes aggregate markdown.
2. test_harvester_returns_suggestions_only — seeded corrections+repeat-edits → suggestions dict.
3. test_harvester_never_writes_anything — boundary A9: monkeypatched write-mode open raises.
4. test_auto_suggest_opt_in_gate — without --auto-suggest → no suggestions section.
5. test_export_summary_no_telemetry_graceful — empty telemetry dir → valid empty markdown, exit 0.
"""
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS))

FIX = Path(__file__).resolve().parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_cli(monkeypatch, telemetry_dir):
    """Reload analyze_telemetry with a tmp telemetry dir."""
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(telemetry_dir))
    monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
    monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
    for m in ("telemetry_paths", "catalog", "lens_usage_tokens",
              "lens_session_shape", "lens_health", "analyze_telemetry", "harvester"):
        sys.modules.pop(m, None)
    import telemetry_paths
    importlib.reload(telemetry_paths)
    import analyze_telemetry
    importlib.reload(analyze_telemetry)
    return analyze_telemetry


def _seed_invocations(telemetry_dir: Path) -> None:
    """Write minimal invocation sink so lenses don't gate out."""
    sink = telemetry_dir / "invocations.jsonl"
    records = [
        {"ts": "2026-06-12T10:00:00+00:00", "skill": "cleanmatic:product-spec",
         "session": "sessA", "via": "PreToolUse:Skill"},
        {"ts": "2026-06-12T11:00:00+00:00", "skill": "cleanmatic:product-spec",
         "session": "sessA", "via": "PreToolUse:Skill"},
        {"ts": "2026-06-12T12:00:00+00:00", "skill": "cleanmatic:release",
         "session": "sessB", "via": "PreToolUse:Skill"},
        {"ts": "2026-06-12T13:00:00+00:00", "skill": "cleanmatic:product-spec",
         "session": "sessB", "via": "PreToolUse:Skill"},
        {"ts": "2026-06-12T14:00:00+00:00", "skill": "cleanmatic:product-spec",
         "session": "sessC", "via": "PreToolUse:Skill"},
        {"ts": "2026-06-12T15:00:00+00:00", "skill": "cleanmatic:product-spec",
         "session": "sessC", "via": "PreToolUse:Skill"},
    ]
    sink.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _seed_artifact_events(telemetry_dir: Path) -> None:
    """Write artifact-events.jsonl with repeat edits on two artifacts."""
    sink = telemetry_dir / "artifact-events.jsonl"
    records = [
        {"ts": "2026-06-12T10:00:00+00:00", "artifact_path": "docs/product/PRD-X.md",
         "op": "Edit", "session": "sessA"},
        {"ts": "2026-06-12T10:01:00+00:00", "artifact_path": "docs/product/PRD-X.md",
         "op": "Edit", "session": "sessA"},
        {"ts": "2026-06-12T10:02:00+00:00", "artifact_path": "docs/product/PRD-X.md",
         "op": "Edit", "session": "sessB"},
        {"ts": "2026-06-12T10:03:00+00:00", "artifact_path": "docs/product/PRD-Y.md",
         "op": "Edit", "session": "sessA"},
        {"ts": "2026-06-12T10:04:00+00:00", "artifact_path": "docs/product/PRD-Y.md",
         "op": "Edit", "session": "sessB"},
    ]
    sink.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _seed_self_corrections(tmp_path: Path) -> Path:
    """Write a synthetic self-corrections.json, return its dir."""
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    corrections = [
        {"correction_id": "SC-001", "category": "scope",
         "artifact": "docs/product/PRD-X.md",
         "description": "Scope was assumed; PO corrected to explicit in/out"},
        {"correction_id": "SC-002", "category": "scope",
         "artifact": "docs/product/PRD-X.md",
         "description": "Another scope assumption corrected"},
        {"correction_id": "SC-003", "category": "persona",
         "artifact": "docs/product/PRODUCT.md",
         "description": "Persona count assumed; PO corrected"},
    ]
    (mem_dir / "self-corrections.json").write_text(
        json.dumps(corrections), encoding="utf-8"
    )
    return mem_dir


# ---------------------------------------------------------------------------
# Test 1 — export-summary writes markdown
# ---------------------------------------------------------------------------

class TestExportSummaryWritesMarkdown:
    """--export-summary <path> writes a markdown aggregate to disk."""

    def test_export_summary_writes_markdown(self, tmp_path, monkeypatch):
        telemetry_dir = tmp_path / "telemetry"
        telemetry_dir.mkdir()
        _seed_invocations(telemetry_dir)
        _seed_artifact_events(telemetry_dir)

        out_path = tmp_path / "out.md"
        cli = _reload_cli(monkeypatch, telemetry_dir)
        rc = cli.main([
            "--lens", "usage", "--days", "36500",
            "--export-summary", str(out_path),
        ])
        assert rc == 0
        assert out_path.exists(), "export-summary must write the file"
        content = out_path.read_text(encoding="utf-8")
        # The aggregate markdown should have at least a heading
        assert "#" in content, "exported markdown must contain headings"


# ---------------------------------------------------------------------------
# Test 2 — harvester returns suggestions only (no writes)
# ---------------------------------------------------------------------------

class TestHarvesterReturnsSuggestionsOnly:
    """harvest_suggestions() returns a dict with a 'suggestions' list; no writes."""

    def test_harvester_returns_suggestions_only(self, tmp_path, monkeypatch):
        telemetry_dir = tmp_path / "telemetry"
        telemetry_dir.mkdir()
        _seed_artifact_events(telemetry_dir)
        mem_dir = _seed_self_corrections(tmp_path)

        monkeypatch.setenv("CK_TELEMETRY_DIR", str(telemetry_dir))
        for m in ("telemetry_paths", "harvester"):
            sys.modules.pop(m, None)
        import telemetry_paths
        importlib.reload(telemetry_paths)
        import harvester
        importlib.reload(harvester)

        result = harvester.harvest_suggestions(
            days=36500,
            corrections_path=mem_dir / "self-corrections.json",
        )

        assert isinstance(result, dict), "harvest_suggestions must return a dict"
        assert "suggestions" in result, "result must have 'suggestions' key"
        suggestions = result["suggestions"]
        assert isinstance(suggestions, list), "'suggestions' must be a list"
        assert len(suggestions) > 0, "should produce at least one suggestion from seeded data"

        # Each suggestion must have the required shape
        for s in suggestions:
            assert "category" in s, "suggestion must have 'category'"
            assert "artifact" in s, "suggestion must have 'artifact'"
            assert "count" in s, "suggestion must have 'count'"
            assert "why" in s, "suggestion must have 'why'"


# ---------------------------------------------------------------------------
# Test 3 — boundary A9: harvester never opens anything for writing
# ---------------------------------------------------------------------------

class TestHarvesterNeverWritesAnything:
    """Boundary A9: monkeypatch open+Path.write_text/write_bytes to raise on write-mode.
    harvest_suggestions() must complete without triggering any write."""

    def test_harvester_never_writes_anything(self, tmp_path, monkeypatch):
        telemetry_dir = tmp_path / "telemetry"
        telemetry_dir.mkdir()
        _seed_artifact_events(telemetry_dir)
        mem_dir = _seed_self_corrections(tmp_path)

        monkeypatch.setenv("CK_TELEMETRY_DIR", str(telemetry_dir))
        for m in ("telemetry_paths", "harvester"):
            sys.modules.pop(m, None)
        import telemetry_paths
        importlib.reload(telemetry_paths)
        import harvester
        importlib.reload(harvester)

        _real_open = open  # keep a reference for read-mode pass-through

        def _guarded_open(file, mode="r", *args, **kwargs):
            write_modes = {"w", "a", "x", "w+", "a+", "x+", "wb", "ab", "xb"}
            # Normalize mode string (strip 'b' prefix effects handled by write_modes)
            normalized = mode.strip().rstrip("b")
            if any(wm in mode for wm in write_modes):
                raise IOError(
                    f"BOUNDARY-A9 VIOLATION: harvester attempted write-mode open "
                    f"({mode!r}) on {file!r}"
                )
            return _real_open(file, mode, *args, **kwargs)

        def _guarded_write_text(self, *args, **kwargs):
            raise IOError(
                f"BOUNDARY-A9 VIOLATION: harvester called Path.write_text on {self!r}"
            )

        def _guarded_write_bytes(self, *args, **kwargs):
            raise IOError(
                f"BOUNDARY-A9 VIOLATION: harvester called Path.write_bytes on {self!r}"
            )

        import builtins
        with (
            patch.object(builtins, "open", side_effect=_guarded_open),
            patch.object(Path, "write_text", _guarded_write_text),
            patch.object(Path, "write_bytes", _guarded_write_bytes),
        ):
            # Must complete without raising
            result = harvester.harvest_suggestions(
                days=36500,
                corrections_path=mem_dir / "self-corrections.json",
            )

        # And return a valid result
        assert "suggestions" in result


# ---------------------------------------------------------------------------
# Test 4 — opt-in gate: without --auto-suggest no suggestions section
# ---------------------------------------------------------------------------

class TestAutoSuggestOptInGate:
    """Without --auto-suggest the rendered output must NOT contain a suggestions section."""

    def test_auto_suggest_absent_produces_no_suggestions_section(self, tmp_path, monkeypatch):
        telemetry_dir = tmp_path / "telemetry"
        telemetry_dir.mkdir()
        _seed_invocations(telemetry_dir)

        cli = _reload_cli(monkeypatch, telemetry_dir)
        # Capture stdout
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["--lens", "usage", "--days", "36500"])
        assert rc == 0
        output = buf.getvalue()
        # No suggestions heading must appear
        assert "## Suggestions" not in output
        assert "## Gợi ý" not in output


# ---------------------------------------------------------------------------
# Test 5 — empty telemetry dir → valid empty markdown, exit 0
# ---------------------------------------------------------------------------

class TestExportSummaryNoTelemetryGraceful:
    """Empty telemetry dir → --export-summary writes a valid (possibly empty) markdown, exit 0."""

    def test_export_summary_empty_telemetry_writes_valid_markdown(self, tmp_path, monkeypatch):
        telemetry_dir = tmp_path / "telemetry"
        telemetry_dir.mkdir()
        # No sink files at all — fully empty telemetry dir

        out_path = tmp_path / "empty-summary.md"
        cli = _reload_cli(monkeypatch, telemetry_dir)
        rc = cli.main([
            "--lens", "usage", "--days", "36500",
            "--export-summary", str(out_path),
        ])
        assert rc == 0, "must exit 0 even with no telemetry data"
        assert out_path.exists(), "must still write the file"
        content = out_path.read_text(encoding="utf-8")
        # Valid markdown: must not be empty (at minimum an empty-section note)
        assert len(content) > 0, "exported file must not be empty"
