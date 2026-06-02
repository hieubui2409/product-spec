---
phase: 1
title: "Preferences schema"
status: pending
effort: ""
---

# Phase 1: Preferences schema

## Overview

Extend the single preferences home (`product-spec/scripts/preferences.py`) for levels 7-9 + the register config + the
split detail levels. All closed-enum, default-safe, never-raise on read (existing contract).

## Requirements
- Functional: new/extended keys validate on read+write, default to safe values, degrade on bad input.
- Non-functional: keep DRY (one DEFAULTS + one ENUMS home); no consumer logic here (scripts own schema, LLM owns use).

## Architecture

Add to `DEFAULTS` + `ENUMS` (closed enums; out-of-range → default on read, `PreferenceError` on save):

| Key | Enum | Default | Drives |
|-----|------|---------|--------|
| `critique_level` | `1..9` (was `1..6`) | `3` | default voice level. **9 is valid as a standing default**, but a resolved level 9 (from pref OR flag) re-confirms EVERY run and downgrades to 8 on decline (gate in Phase 3, not schema). |
| `critique_detail_level` | `concise·standard·verbose` | `standard` | **spec-critique** report verbosity (SEPARATE from `detail_level`) |
| `critique_address_gender` | `m·f` | `m` | lv7 address: `ông/tôi` (m) ↔ `bà/tôi` (f) |
| `critique_dialect` | `bac·trung·nam` | `bac` | lv8+ pronoun, the PO's OWN voice: `mày/tao` (bac) ↔ `mi/tau` (trung) ↔ nam |
| `critique_profanity` | `off·abbrev·strong` | `strong` | profanity **aimed at the work**: off ↔ `đm/vl` abbrev ↔ `đm/vl/vãi` strong. Default `strong` (lv9 re-confirms every run). Enum is a strength tier; the IN/OUT token rule lives in voice-and-tone (`đậu xanh` minced-oath IN, literal `đụ má mày` OUT). |
| `detail_level` (exists) | `concise·standard·verbose` | `standard` | **product-spec** output verbosity (Phase 4 wires it) |

Profanity applies at level 9 (work-targeted only); dialect at level ≥8; gender at level 7. The WHERE-it-applies logic
lives in the workflow/voice docs, not the script (script-vs-LLM split). `critique_level` accepts 1..9; the safety of
lv9 (B5) is enforced in the workflow as a **mandatory per-run re-confirm that downgrades to 8 on decline** (Phase 3),
not as a schema cap.

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/preferences.py` (DEFAULTS + ENUMS + module docstring keys list)
- Modify (tests in Phase 6): `.claude/skills/product-spec/scripts/tests/test_preferences.py`

## Implementation Steps
1. Change `critique_level` ENUM from `frozenset(range(1,7))` to `frozenset(range(1,10))` (1..9). Default stays 3.
2. Add the four new keys to `DEFAULTS` with the defaults above.
3. Add closed-enum frozensets for `critique_detail_level` (`concise·standard·verbose`), `critique_address_gender`
   (`m·f`), `critique_dialect` (`bac·trung·nam`), `critique_profanity` (`off·abbrev·strong`) to `ENUMS`.
4. Update the module docstring "Keys" block: each key + the level-applicability note + the note that level 9 is valid
   but re-confirms per run (enforced in the workflow, not here) + a one-line floor pointer (floor in voice/IN-OUT table).
5. No consumer code here. (the new keys are read by the LLM workflow + consolidate/humanize, Phase 3.)

## Success Criteria
- [ ] `preferences.load` returns all keys with documented defaults on an empty project (10 keys total now).
- [ ] `critique_level: 9` loads as 9 (valid); `critique_level: 10` falls back to 3; `save({critique_level:10})` raises.
      (The per-run re-confirm + downgrade-to-8 for level 9 is a Phase-3 workflow behavior, not a schema check.)
- [ ] Each new enum: valid value loads; out-of-range falls back to default; `save` of a bad value raises.
- [ ] `critique_profanity` accepts `off·abbrev·strong`; `đụ má`-style tokens are not representable (no such enum value).
- [ ] `detail_level` and `critique_detail_level` are independent (setting one does not affect the other).
- [ ] Existing keys (`lang`, `detail_level`, `critique_drift_threshold`, `critique_level: 6` files, …) stay valid.

## Risk Assessment
- Low. Pure schema addition mirroring the existing `critique_level` pattern. Risk = forgetting the enum→default
  symmetry; covered by Phase 6 tests. Existing `critique_level: 6` files stay valid (6 ∈ 1..9).
