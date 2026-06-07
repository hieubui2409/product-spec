"""test_lens_forensics.py — session reconstruction parity against the fixture
transcript (skills, tool counts, tokens, files, duration)."""
import importlib
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
FIX = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def lens(monkeypatch):
    monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
    for m in ("telemetry_paths", "lens_forensics"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_forensics
    importlib.reload(lens_forensics)
    return lens_forensics


def test_default_parses_most_recent_session(lens):
    d = lens.gather()
    assert d["count"] == 1
    s = d["sessions"][0]
    assert s["session"] == "sessB"
    assert s["skills"] == ["cleanmatic:product-spec", "cleanmatic:release"]
    assert s["tool_counts"] == {"Skill": 2, "Write": 1}
    assert s["tool_calls"] == 3
    assert s["files_modified"] == ["/x.md"]
    assert s["total_tokens"] == 600  # in 420 + out 180
    assert s["duration_s"] == 180    # 09:00 → 09:03


def test_explicit_session_id(lens):
    d = lens.gather(session="sessB")
    assert d["count"] == 1
    assert d["agg_total_tokens"] == 600
    assert d["agg_tool_counts"]["Skill"] == 2


def test_missing_session_is_empty_not_error(lens):
    d = lens.gather(session="ghost")
    assert d["count"] == 0 and d["sessions"] == []
