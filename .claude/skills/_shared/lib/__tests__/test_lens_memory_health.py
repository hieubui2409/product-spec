"""test_lens_memory_health.py — memory-dir validation parity against the fixture
memory dir (orphan file, dead index entry, broken [[link]]); asserts read-only."""
import importlib
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
FIX = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def lens(monkeypatch):
    monkeypatch.setenv("CK_MEMORY_DIR", str(FIX / "memory"))
    for m in ("telemetry_paths", "lens_memory_health"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_memory_health
    importlib.reload(lens_memory_health)
    return lens_memory_health


def test_detects_orphan_dead_and_broken_link(lens):
    d = lens.gather()
    assert d["count"] == 2
    assert d["orphans"] == ["orphan-fact.md"]
    assert d["dead_entries"] == ["missing-file.md"]
    assert d["broken_links"] == [{"from": "good-fact.md", "to": "nonexistent"}]
    assert d["issue_count"] == 3
    assert d["status"] == "YELLOW"


def test_frontmatter_parsed_nested_type_valid(lens):
    d = lens.gather()
    # both fixtures declare metadata.type: reference (valid) → no invalid frontmatter
    assert d["invalid_frontmatter"] == []
    assert d["type_distribution"] == {"reference": 2}


def test_is_read_only_no_writes(lens):
    before = sorted(p.name for p in (FIX / "memory").iterdir())
    idx_before = (FIX / "memory" / "MEMORY.md").read_text()
    d = lens.gather()
    assert d["read_only"] is True
    assert d["fix_preview"] == ["missing-file.md"]  # dry-run only
    # nothing on disk changed
    assert sorted(p.name for p in (FIX / "memory").iterdir()) == before
    assert (FIX / "memory" / "MEMORY.md").read_text() == idx_before
    assert not hasattr(lens, "apply_fix")  # no mutating path exists


def test_missing_memory_dir_is_fail_soft(monkeypatch, tmp_path):
    monkeypatch.setenv("CK_MEMORY_DIR", str(tmp_path / "nope"))
    for m in ("telemetry_paths", "lens_memory_health"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_memory_health
    importlib.reload(lens_memory_health)
    d = lens_memory_health.gather()
    assert d["count"] == 0 and d["status"] == "GREEN"
