"""test_lens_health.py — coarse script-health aggregates from the fixture
hook-telemetry.jsonl: per-script runs/errors/rate + avg `ms` (present when the
Pre/Post pair recorded it, None when it degraded).
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
    for m in ("telemetry_paths", "lens_health"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_health
    importlib.reload(lens_health)
    return lens_health


def _row(d, script):
    return next(r for r in d["rows"] if r["script"] == script)


def test_totals(lens):
    d = lens.gather()
    assert d["total_runs"] == 4
    assert d["scripts"] == 3
    assert d["total_errors"] == 1
    assert d["approx"] is True


def test_per_script_error_and_avg_ms(lens):
    d = lens.gather()
    v = _row(d, "product-spec/scripts/validate.py")
    assert v["runs"] == 2 and v["errors"] == 0 and v["avg_ms"] == 1000  # (1200+800)/2

    r = _row(d, "release/scripts/release.py")
    assert r["runs"] == 1 and r["errors"] == 1 and r["error_rate"] == 100 and r["avg_ms"] == 300

    vis = _row(d, "product-spec/scripts/visualize.py")
    assert vis["avg_ms"] is None  # no ms field on its record → degrades


def test_gated_below_threshold(lens):
    assert lens.gather()["gated"] is True  # 4 runs < 5


def test_missing_sink_does_not_raise(monkeypatch, tmp_path):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path))  # empty dir, no sink
    for m in ("telemetry_paths", "lens_health"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_health
    importlib.reload(lens_health)
    d = lens_health.gather()
    assert d["total_runs"] == 0 and d["rows"] == []
