"""Tests for preferences.py — the PO-preferences memory store.

Covers the existing defaults/enums plus the new non-enum `critique_drift_threshold`
key (consumed by cleanmatic:spec-critique). The read path must never raise."""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import preferences


def _write_prefs(root: Path, text: str) -> None:
    mem = root / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "preferences.yaml").write_text(text, encoding="utf-8")


def test_defaults_when_no_file(tmp_path):
    prefs = preferences.load(tmp_path)
    assert prefs["lang"] == "en"
    assert prefs["detail_level"] == "standard"
    assert prefs["prioritization"] == "moscow"
    assert prefs["dismissed_reminders"] == []
    assert prefs["critique_drift_threshold"] == 3


def test_critique_drift_threshold_override(tmp_path):
    _write_prefs(tmp_path, "critique_drift_threshold: 7\n")
    assert preferences.load(tmp_path)["critique_drift_threshold"] == 7


def test_critique_drift_threshold_non_int_passed_through(tmp_path):
    # Non-enum key: load() does NOT validate; it passes the raw value through. The
    # consumer (critique_scan) is responsible for the int() coercion.
    _write_prefs(tmp_path, "critique_drift_threshold: not-a-number\n")
    assert preferences.load(tmp_path)["critique_drift_threshold"] == "not-a-number"


def test_enum_out_of_range_falls_back(tmp_path):
    _write_prefs(tmp_path, "lang: zz\n")
    assert preferences.load(tmp_path)["lang"] == "en"


def test_corrupt_yaml_degrades_to_defaults(tmp_path):
    _write_prefs(tmp_path, ": : : not yaml\n")
    prefs = preferences.load(tmp_path)
    assert prefs["lang"] == "en"
    assert prefs["critique_drift_threshold"] == 3


def test_save_drops_unknown_keys_keeps_threshold(tmp_path):
    preferences.save(tmp_path, {"critique_drift_threshold": 4, "bogus": 1})
    reloaded = preferences.load(tmp_path)
    assert reloaded["critique_drift_threshold"] == 4
    assert "bogus" not in reloaded


def test_save_invalid_enum_raises(tmp_path):
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"lang": "zz"})
