"""test_lens_session_shape.py — session-shape aggregates from the fixture
sessions.jsonl: counts, duration avg/median, file + subagent totals, and
flat-slug-normalized skill co-occurrence.
"""
import importlib
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
FIX = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def lens(monkeypatch):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(FIX / "telemetry"))
    monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
    for m in ("telemetry_paths", "catalog", "lens_session_shape"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_session_shape
    importlib.reload(lens_session_shape)
    return lens_session_shape


def test_counts_and_durations(lens):
    d = lens.gather(skills_dir=FIX / "skills")
    assert d["sessions"] == 2
    assert d["avg_duration_s"] == 2700   # (3600 + 1800) / 2
    assert d["median_duration_s"] == 2700.0
    assert d["files_modified_total"] == 5  # 3 + 2
    assert d["subagents_total"] == 3       # 1 + 2


def test_cooccurrence_normalized_to_dir_slugs(lens):
    d = lens.gather(skills_dir=FIX / "skills")
    pairs = dict(d["top_cooccurrence"])
    # sessB's 3 skills (slug + dir forms) normalize to 3 dirs → 3 unordered pairs
    assert pairs.get("product-spec + product-spec-critique") == 1
    assert pairs.get("product-spec + release") == 1
    assert pairs.get("product-spec-critique + release") == 1


def test_gated_below_threshold(lens):
    d = lens.gather(skills_dir=FIX / "skills")
    assert d["gated"] is True  # 2 sessions < 5
