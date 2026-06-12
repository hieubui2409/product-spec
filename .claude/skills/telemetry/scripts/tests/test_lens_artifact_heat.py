"""
test_lens_artifact_heat.py — TDD tests for the artifact-heat lens.

Tests:
5. gather() tallies edits per artifact_path and ranks by edit count.
6. gather() with no events returns empty/zero without crashing.
"""

import importlib
import json
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))

SINK_NAME = "artifact-events.jsonl"


def _setup_telemetry(monkeypatch, tmp_path):
    """Reload telemetry_paths with CK_TELEMETRY_DIR pointing at tmp_path."""
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
    for mod_name in ("telemetry_paths", "lens_artifact_heat"):
        sys.modules.pop(mod_name, None)
    import telemetry_paths
    importlib.reload(telemetry_paths)
    import lens_artifact_heat
    importlib.reload(lens_artifact_heat)
    return lens_artifact_heat


def _write_artifact_events(tmp_path: Path, events: list[dict]) -> None:
    """Write synthetic artifact-edit events to the sink file."""
    sink = tmp_path / SINK_NAME
    lines = [json.dumps(e) for e in events]
    sink.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 5: gather() tallies edits per artifact and ranks by heat
# ---------------------------------------------------------------------------

class TestHeatLensTalliesPerArtifact:
    """Seed N events across 2 paths → gather() returns correct per-path counts
    in descending edit-count order."""

    def test_heat_lens_tallies_per_artifact_ranked(self, tmp_path, monkeypatch):
        lens = _setup_telemetry(monkeypatch, tmp_path)

        # PRD-X edited 3 times, PRD-Y edited 1 time
        events = [
            {"ts": "2026-06-12T10:00:00+00:00", "artifact_path": "docs/product/PRD-X.md", "op": "Edit",  "session": "s1"},
            {"ts": "2026-06-12T10:01:00+00:00", "artifact_path": "docs/product/PRD-X.md", "op": "Write", "session": "s1"},
            {"ts": "2026-06-12T10:02:00+00:00", "artifact_path": "docs/product/PRD-Y.md", "op": "Edit",  "session": "s2"},
            {"ts": "2026-06-12T10:03:00+00:00", "artifact_path": "docs/product/PRD-X.md", "op": "Edit",  "session": "s2"},
        ]
        _write_artifact_events(tmp_path, events)

        result = lens.gather()

        assert result["lens"] == "artifact_heat"
        rows = result["rows"]
        assert len(rows) == 2

        # PRD-X first (most edits)
        assert rows[0]["artifact"] == "docs/product/PRD-X.md"
        assert rows[0]["edits"] == 3
        assert rows[1]["artifact"] == "docs/product/PRD-Y.md"
        assert rows[1]["edits"] == 1

    def test_heat_lens_row_carries_last_edit_timestamp(self, tmp_path, monkeypatch):
        """Each row must carry the timestamp of the most recent edit."""
        lens = _setup_telemetry(monkeypatch, tmp_path)

        events = [
            {"ts": "2026-06-12T08:00:00+00:00", "artifact_path": "docs/product/PRODUCT.md", "op": "Edit", "session": "s1"},
            {"ts": "2026-06-12T09:00:00+00:00", "artifact_path": "docs/product/PRODUCT.md", "op": "Edit", "session": "s1"},
        ]
        _write_artifact_events(tmp_path, events)

        result = lens.gather()
        rows = result["rows"]
        assert len(rows) == 1
        # last_edit should be the max timestamp
        assert rows[0]["last_edit"] == "2026-06-12T09:00:00+00:00"

    def test_heat_lens_respects_days_window(self, tmp_path, monkeypatch):
        """Events older than days cutoff must be excluded."""
        lens = _setup_telemetry(monkeypatch, tmp_path)

        events = [
            # Very old event (100 days ago mock — we use days=0 to exclude all)
            {"ts": "2020-01-01T00:00:00+00:00", "artifact_path": "docs/product/OLD.md", "op": "Edit", "session": "s1"},
            {"ts": "2026-06-12T10:00:00+00:00", "artifact_path": "docs/product/NEW.md", "op": "Edit", "session": "s2"},
        ]
        _write_artifact_events(tmp_path, events)

        # With days=1, only the recent event should be included
        result = lens.gather(days=1)
        rows = result["rows"]
        artifact_names = [r["artifact"] for r in rows]
        assert "docs/product/NEW.md" in artifact_names
        assert "docs/product/OLD.md" not in artifact_names


# ---------------------------------------------------------------------------
# Test 6: empty sink → lens returns empty/zero, no crash
# ---------------------------------------------------------------------------

class TestHeatLensEmptyGraceful:
    """No events → lens returns expected empty structure without crashing."""

    def test_empty_sink_returns_empty_rows(self, tmp_path, monkeypatch):
        lens = _setup_telemetry(monkeypatch, tmp_path)
        # Sink file does not exist at all

        result = lens.gather()

        assert result["lens"] == "artifact_heat"
        assert result["rows"] == []
        assert result["total_edits"] == 0

    def test_empty_sink_file_returns_empty_rows(self, tmp_path, monkeypatch):
        """Empty sink file (exists but has no lines) → no crash."""
        lens = _setup_telemetry(monkeypatch, tmp_path)

        # Write an empty sink file
        (tmp_path / SINK_NAME).write_text("", encoding="utf-8")

        result = lens.gather()

        assert result["rows"] == []
        assert result["total_edits"] == 0

    def test_malformed_jsonl_lines_skipped_gracefully(self, tmp_path, monkeypatch):
        """Malformed lines in the sink must be skipped, not crash the lens."""
        lens = _setup_telemetry(monkeypatch, tmp_path)

        (tmp_path / SINK_NAME).write_text(
            "not json at all\n"
            + json.dumps({"ts": "2026-06-12T10:00:00+00:00", "artifact_path": "docs/product/PRODUCT.md", "op": "Edit", "session": "s1"})
            + "\n",
            encoding="utf-8",
        )

        result = lens.gather()
        assert result["total_edits"] == 1
        assert len(result["rows"]) == 1
