"""test_low_volume_gate.py — the sparse-data gate boundary. Below threshold the
lens must suppress advice; at/above it must not. Mirrors D3 (the generalized
'_No data yet_' path).
"""
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))

from telemetry_paths import low_volume_gate, LOW_VOLUME_THRESHOLD  # noqa: E402


def test_below_threshold_is_gated():
    assert low_volume_gate(LOW_VOLUME_THRESHOLD - 1) is True


def test_at_threshold_is_not_gated():
    assert low_volume_gate(LOW_VOLUME_THRESHOLD) is False


def test_above_threshold_is_not_gated():
    assert low_volume_gate(LOW_VOLUME_THRESHOLD + 100) is False


def test_zero_is_gated():
    assert low_volume_gate(0) is True


def test_custom_threshold_honored():
    assert low_volume_gate(2, threshold=3) is True
    assert low_volume_gate(3, threshold=3) is False


def test_non_numeric_count_is_gated_conservatively():
    assert low_volume_gate(None) is True  # type: ignore[arg-type]
