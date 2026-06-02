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
    # Default voice level is 5 (no-mercy), the last level before a mandated roast (6+).
    assert prefs["critique_level"] == 5
    # Levels 7-9 register knobs + the split detail level (defaults).
    assert prefs["critique_detail_level"] == "standard"
    assert prefs["critique_address_gender"] == "m"
    assert prefs["critique_dialect"] == "bac"
    # Default strong: level 9 re-confirms with the PO every run, so it runs at full power.
    assert prefs["critique_profanity"] == "strong"


def test_defaults_has_exactly_ten_keys(tmp_path):
    # Guards the DEFAULTS/ENUMS symmetry contract as keys are added.
    assert set(preferences.load(tmp_path)) == set(preferences.DEFAULTS)
    assert len(preferences.DEFAULTS) == 10


def test_critique_level_enum_accepts_6_and_9(tmp_path):
    # 6 stays valid (1..9 superset of the old 1..6); 9 is now a valid standing default.
    _write_prefs(tmp_path, "critique_level: 6\n")
    assert preferences.load(tmp_path)["critique_level"] == 6
    _write_prefs(tmp_path, "critique_level: 9\n")
    assert preferences.load(tmp_path)["critique_level"] == 9


def test_critique_level_out_of_range_falls_back(tmp_path):
    # Closed enum 1..9: 0 or 10 (or a string) is treated as absent -> default 5.
    # (The per-run re-confirm + downgrade-to-8 for a resolved 9 is workflow behaviour,
    # NOT a schema check — load() returns 9 verbatim.)
    _write_prefs(tmp_path, "critique_level: 10\n")
    assert preferences.load(tmp_path)["critique_level"] == 5
    _write_prefs(tmp_path, "critique_level: 0\n")
    assert preferences.load(tmp_path)["critique_level"] == 5


def test_save_critique_level_9_ok_10_raises(tmp_path):
    # 9 is a valid standing default; 0 and 10 are out of the 1..9 enum.
    preferences.save(tmp_path, {"critique_level": 9})
    assert preferences.load(tmp_path)["critique_level"] == 9
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"critique_level": 0})
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"critique_level": 10})


def test_register_enums_accept_fallback_and_save_raise(tmp_path):
    # critique_address_gender m|f
    _write_prefs(tmp_path, "critique_address_gender: f\n")
    assert preferences.load(tmp_path)["critique_address_gender"] == "f"
    _write_prefs(tmp_path, "critique_address_gender: x\n")
    assert preferences.load(tmp_path)["critique_address_gender"] == "m"
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"critique_address_gender": "x"})

    # critique_dialect bac|trung|nam
    _write_prefs(tmp_path, "critique_dialect: trung\n")
    assert preferences.load(tmp_path)["critique_dialect"] == "trung"
    _write_prefs(tmp_path, "critique_dialect: hue\n")
    assert preferences.load(tmp_path)["critique_dialect"] == "bac"
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"critique_dialect": "hue"})


def test_critique_profanity_enum_only_off_abbrev_strong(tmp_path):
    for v in ("off", "abbrev", "strong"):
        _write_prefs(tmp_path, f"critique_profanity: {v}\n")
        assert preferences.load(tmp_path)["critique_profanity"] == v
    # No family/sexual-target value is representable; an unknown token falls back to the
    # default (strong) on read and raises on save.
    _write_prefs(tmp_path, "critique_profanity: du-ma\n")
    assert preferences.load(tmp_path)["critique_profanity"] == "strong"
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"critique_profanity": "du-ma"})


@pytest.mark.parametrize(
    "token,expected",
    [
        # YAML 1.1 parses these bare tokens as booleans. load() maps the bool back to
        # the enum string: False -> "off" (a real enum value), True -> "on" (NOT an
        # enum value, so it falls back to the default 'strong').
        ("off", "off"),
        ("no", "off"),   # no -> False -> "off"
        ("on", "strong"),   # on -> True -> "on" (not in enum) -> default
        ("yes", "strong"),  # yes -> True -> "on" (not in enum) -> default
    ],
)
def test_critique_profanity_yaml_boolean_tokens(tmp_path, token, expected):
    _write_prefs(tmp_path, f"critique_profanity: {token}\n")
    assert preferences.load(tmp_path)["critique_profanity"] == expected


def test_bool_coercion_cannot_mismap_a_non_profanity_enum(tmp_path):
    # `critique_address_gender: off` parses as False -> "off", which is NOT a gender
    # enum value, so it must fall back to the default 'm' (never silently become "off").
    _write_prefs(tmp_path, "critique_address_gender: off\n")
    assert preferences.load(tmp_path)["critique_address_gender"] == "m"


def test_detail_levels_are_independent(tmp_path):
    # detail_level (product-spec) and critique_detail_level (spec-critique) never bleed.
    _write_prefs(tmp_path, "detail_level: concise\ncritique_detail_level: verbose\n")
    prefs = preferences.load(tmp_path)
    assert prefs["detail_level"] == "concise"
    assert prefs["critique_detail_level"] == "verbose"
    # Setting one via save() leaves the other at its default.
    preferences.save(tmp_path, {"critique_detail_level": "concise"})
    reloaded = preferences.load(tmp_path)
    assert reloaded["critique_detail_level"] == "concise"
    assert reloaded["detail_level"] == "standard"


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
