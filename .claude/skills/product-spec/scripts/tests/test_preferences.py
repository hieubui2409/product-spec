"""Tests for preferences.py — the PO-preferences memory store.

Covers the existing defaults/enums plus the new non-enum `critique_drift_threshold`
key (consumed by cleanmatic:product-spec-critique). The read path must never raise.

Also covers the 2 product-spec engagement knobs (`interview_rigor`, `action_prompting`)
and the load-merge `--set` write-CLI (must preserve every other committed key)."""

import subprocess
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


def test_defaults_has_exactly_fifteen_keys(tmp_path):
    # Guards the DEFAULTS/ENUMS symmetry contract as keys are added. 15 = the original
    # 10 + the 3 product-spec-critique cross-critique keys (critique_inherit/rollup/depth)
    # + the 2 product-spec engagement knobs (interview_rigor/action_prompting).
    assert set(preferences.load(tmp_path)) == set(preferences.DEFAULTS)
    assert len(preferences.DEFAULTS) == 17
    # Both engagement knobs are closed enums (not free scalars).
    assert "interview_rigor" in preferences.ENUMS
    assert "action_prompting" in preferences.ENUMS
    # The two learning-loop verdict floors are float scalars (range-validated by the
    # consumer), so they are deliberately NOT in ENUMS.
    assert "outcome_hit_floor" not in preferences.ENUMS
    assert "outcome_partial_floor" not in preferences.ENUMS


def test_cross_critique_defaults(tmp_path):
    prefs = preferences.load(tmp_path)
    assert prefs["critique_inherit"] == "on"
    assert prefs["critique_rollup"] == "on"
    assert prefs["critique_inherit_depth"] == "nearest"


def test_critique_inherit_off_coerces_to_token(tmp_path):
    # YAML 1.1 parses bare `off` as Python False; the enum coercion must map it
    # back to the "off" string token (NOT leave a bare False, NOT drop the key).
    _write_prefs(tmp_path, "critique_inherit: off\n")
    assert preferences.load(tmp_path)["critique_inherit"] == "off"
    _write_prefs(tmp_path, "critique_rollup: off\n")
    assert preferences.load(tmp_path)["critique_rollup"] == "off"


def test_critique_inherit_depth_deep_round_trips(tmp_path):
    _write_prefs(tmp_path, "critique_inherit_depth: deep\n")
    assert preferences.load(tmp_path)["critique_inherit_depth"] == "deep"


def test_cross_critique_save_round_trip(tmp_path):
    preferences.save(tmp_path, {"critique_inherit": "off", "critique_inherit_depth": "deep"})
    prefs = preferences.load(tmp_path)
    assert prefs["critique_inherit"] == "off"
    assert prefs["critique_inherit_depth"] == "deep"


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
    # detail_level (product-spec) and critique_detail_level (product-spec-critique) never bleed.
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


# --------------------------------------------------------------------------
# Engagement knobs (product-spec): interview_rigor + action_prompting
# --------------------------------------------------------------------------

def test_engagement_knobs_default_standard(tmp_path):
    # Both default to `standard`, mirroring detail_level (neutral posture — no
    # GATE-NEVER-ASSUME breach from a strict-by-default knob).
    prefs = preferences.load(tmp_path)
    assert prefs["interview_rigor"] == "standard"
    assert prefs["action_prompting"] == "standard"


def test_engagement_knobs_backward_compat(tmp_path):
    # An old preferences.yaml written WITHOUT the new keys still resolves them to
    # `standard` (non-breaking: missing keys degrade to defaults).
    _write_prefs(tmp_path, "lang: vi\ndetail_level: concise\n")
    prefs = preferences.load(tmp_path)
    assert prefs["interview_rigor"] == "standard"
    assert prefs["action_prompting"] == "standard"
    assert prefs["lang"] == "vi"


def test_engagement_knobs_enum_values_round_trip(tmp_path):
    for v in ("light", "standard", "deep"):
        _write_prefs(tmp_path, f"interview_rigor: {v}\n")
        assert preferences.load(tmp_path)["interview_rigor"] == v
    for v in ("minimal", "standard", "proactive"):
        _write_prefs(tmp_path, f"action_prompting: {v}\n")
        assert preferences.load(tmp_path)["action_prompting"] == v


def test_engagement_knobs_out_of_range_falls_back(tmp_path):
    _write_prefs(tmp_path, "interview_rigor: hard\naction_prompting: aggressive\n")
    prefs = preferences.load(tmp_path)
    assert prefs["interview_rigor"] == "standard"
    assert prefs["action_prompting"] == "standard"


def test_save_invalid_engagement_enum_raises(tmp_path):
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"interview_rigor": "hard"})
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"action_prompting": "aggressive"})


# --------------------------------------------------------------------------
# --set write-CLI — load→merge→save (red-team A/N data-loss fix)
# --------------------------------------------------------------------------

def _run_cli(tmp_path, *cli_args):
    """Invoke preferences.py as a subprocess (exercises main()'s real argv path)."""
    script = SCRIPTS_DIR / "preferences.py"
    return subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), *cli_args],
        capture_output=True,
        text=True,
    )


def test_set_load_merge_preserves_other_keys(tmp_path):
    # Seed an existing file with unrelated keys, then --set one engagement knob.
    # The pre-existing keys MUST survive (save() is a blind full-dict overwrite, so
    # the CLI has to load→merge→save — red-team finding A).
    _write_prefs(tmp_path, "lang: vi\ncritique_level: 9\n")
    res = _run_cli(tmp_path, "--set", "interview_rigor=deep")
    assert res.returncode == 0, res.stderr
    prefs = preferences.load(tmp_path)
    assert prefs["lang"] == "vi"
    assert prefs["critique_level"] == 9
    assert prefs["interview_rigor"] == "deep"


def test_set_multiple_keys_one_call(tmp_path):
    res = _run_cli(
        tmp_path, "--set", "interview_rigor=deep", "--set", "action_prompting=proactive"
    )
    assert res.returncode == 0, res.stderr
    prefs = preferences.load(tmp_path)
    assert prefs["interview_rigor"] == "deep"
    assert prefs["action_prompting"] == "proactive"


def test_set_bad_enum_nonzero_and_file_unchanged(tmp_path):
    _write_prefs(tmp_path, "lang: vi\n")
    res = _run_cli(tmp_path, "--set", "interview_rigor=bad")
    assert res.returncode != 0
    # Nothing was written: the seeded file is intact and the knob is still default.
    prefs = preferences.load(tmp_path)
    assert prefs["lang"] == "vi"
    assert prefs["interview_rigor"] == "standard"


def test_set_value_splits_on_first_equals(tmp_path):
    # A value containing `=` splits on the FIRST `=` only. `lang=en=extra` would make
    # the value `en=extra` (not a valid enum) → non-zero, proving the split point.
    res = _run_cli(tmp_path, "--set", "lang=en=extra")
    assert res.returncode != 0
    # Sanity: a clean value with no stray `=` works.
    res2 = _run_cli(tmp_path, "--set", "lang=vi")
    assert res2.returncode == 0, res2.stderr
    assert preferences.load(tmp_path)["lang"] == "vi"


def test_set_malformed_pair_nonzero(tmp_path):
    # No `=` at all is a usage error → non-zero, nothing written.
    res = _run_cli(tmp_path, "--set", "interview_rigor")
    assert res.returncode != 0


def test_set_int_enum_key_coerces_digit_string(tmp_path):
    # argparse hands `--set` string values; an int-enum key (critique_level, enum is
    # ints 1..9) must coerce the digit string to int so it matches the enum and persists
    # as an int — not silently fail with a string/int type mismatch.
    res = _run_cli(tmp_path, "--set", "critique_level=7")
    assert res.returncode == 0, res.stderr
    assert preferences.load(tmp_path)["critique_level"] == 7  # int, not "7"


def test_set_int_passthrough_key_coerces(tmp_path):
    # The non-enum int key critique_drift_threshold also coerces, keeping the on-disk
    # type canonical (int), not a quoted string.
    res = _run_cli(tmp_path, "--set", "critique_drift_threshold=10")
    assert res.returncode == 0, res.stderr
    assert preferences.load(tmp_path)["critique_drift_threshold"] == 10


def test_set_unknown_key_rejected_nonzero(tmp_path):
    # A typo'd key must NOT silently no-op: save() drops unknown keys, so the CLI rejects
    # them up front (exit non-zero) rather than printing "saved" while writing nothing.
    _write_prefs(tmp_path, "lang: vi\n")
    res = _run_cli(tmp_path, "--set", "interview_rigour=deep")  # British-spelling typo
    assert res.returncode != 0
    # Nothing changed: the real knob is still default, the seeded key intact.
    prefs = preferences.load(tmp_path)
    assert prefs["interview_rigor"] == "standard"
    assert prefs["lang"] == "vi"


def test_set_float_floor_rejects_non_numeric_at_write_time(tmp_path):
    # A non-numeric float-key value must FAIL AT WRITE (exit non-zero, nothing saved) —
    # not save with exit 0 and break a later --learn run (the delayed-failure trap).
    res = _run_cli(tmp_path, "--set", "outcome_hit_floor=notanumber")
    assert res.returncode != 0
    assert preferences.load(tmp_path)["outcome_hit_floor"] == 0.9  # untouched default


def test_set_float_floor_rejects_out_of_range(tmp_path):
    # Range [0,1] is guarded at write time so a 1.5 floor can't reach --learn.
    res = _run_cli(tmp_path, "--set", "outcome_partial_floor=1.5")
    assert res.returncode != 0
    assert preferences.load(tmp_path)["outcome_partial_floor"] == 0.5


def test_set_float_floor_valid_persists_as_float(tmp_path):
    res = _run_cli(tmp_path, "--set", "outcome_hit_floor=0.95")
    assert res.returncode == 0, res.stderr
    val = preferences.load(tmp_path)["outcome_hit_floor"]
    assert val == 0.95 and isinstance(val, float)
