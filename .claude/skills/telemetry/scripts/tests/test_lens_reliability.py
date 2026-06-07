"""test_lens_reliability.py — subagent-outcome aggregation parity against the
fixture sink (per-type success/timeout, success rate, failure modes, gate)."""
import importlib
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
FIX = Path(__file__).resolve().parent / "fixtures"
BIG_DAYS = 36500


@pytest.fixture
def lens(monkeypatch):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(FIX / "telemetry"))
    for m in ("telemetry_paths", "lens_reliability"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_reliability
    importlib.reload(lens_reliability)
    return lens_reliability


def _row(d, atype):
    return next(r for r in d["rows"] if r["agent_type"] == atype)


def test_per_type_counts_and_rate(lens):
    d = lens.gather(days=BIG_DAYS)
    assert d["total"] == 3
    r = _row(d, "researcher")
    assert r["total"] == 2 and r["success"] == 1 and r["timeout"] == 1 and r["success_rate"] == 50
    cr = _row(d, "code-reviewer")
    assert cr["total"] == 1 and cr["success"] == 1 and cr["success_rate"] == 100


def test_top_failure_modes(lens):
    d = lens.gather(days=BIG_DAYS)
    assert d["top_failure_modes"] == [("timeout", 1)]


def test_gated_below_threshold(lens):
    assert lens.gather(days=BIG_DAYS)["gated"] is True  # 3 < 5


def test_empty_window_no_error(lens):
    d = lens.gather(days=0)
    assert d["total"] == 0 and d["rows"] == [] and d["gated"] is True
