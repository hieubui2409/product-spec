---
phase: 1
title: "Schema and write-CLI in preferences"
status: pending
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Schema and write-CLI in preferences

## Overview

Foundation. Add **2 closed-enum** engagement knobs to `preferences.py` + a `--set` write-CLI that does
`load→merge→save` (the red-team's #1 data-loss fix). Pure script logic → **tests-first** (TDD). Additive, non-breaking.

## Requirements

- Functional:
  - `interview_rigor` ∈ {light, standard, deep}, default **standard**.
  - `action_prompting` ∈ {minimal, standard, proactive}, default **standard**.
  - `preferences.py --set <key>=<value>` (repeatable) → enum-validated, fenced, and **load-merge**: preserves every
    other existing key. No list key in v1 (`standing_reminders` dropped).
- Non-functional:
  - Non-breaking: missing keys degrade to defaults; old files load unchanged.
  - `save()` byte-stable (sorted keys, LF) — no churn.

## Architecture

- `DEFAULTS` += `interview_rigor: "standard"`, `action_prompting: "standard"`; `ENUMS` += both. (13 → **15** keys.)
- `load()`/`save()` already handle scalar enums — the 2 new keys need no new branch.
- **CLI (the critical part):** extend `main()` with `--set KEY=VALUE` (repeatable). It MUST:
  1. `prefs = load(root)` (resolve current, incl. existing committed keys),
  2. apply each `--set` onto `prefs` (split on FIRST `=` only),
  3. `save(root, prefs)` (enum-validated; a bad value raises `PreferenceError` → non-zero exit, nothing written).
  - With no `--set`, behavior unchanged (still dumps `load()`).
  - Mirrors the `behavioral_memory.py --voice` load-merge model (`behavioral_memory.py:155-176`) — which the original
    plan cited but did not replicate.

## Related Code Files

- Modify: `.claude/skills/product-spec/scripts/preferences.py`
- Modify: `.claude/skills/product-spec/scripts/tests/test_preferences.py`

## Implementation Steps

1. **Tests first** in `test_preferences.py`:
   - **Update the existing count guard**: `test_defaults_has_exactly_thirteen_keys` → **15**; update its comment;
     keep/extend the `set(load(...)) == set(DEFAULTS)` symmetry assertion and assert both new keys are in `ENUMS`
     (red-team B).
   - defaults: fresh `load()` → `interview_rigor=standard`, `action_prompting=standard`.
   - backward-compat: a `preferences.yaml` written WITHOUT the new keys still loads them at `standard`.
   - enum guard: `save({"interview_rigor":"hard"})` → `PreferenceError` (`hard` is not a value).
   - **load-merge (red-team A/N)**: write `{lang:vi, critique_level:9}`; run CLI `--set interview_rigor=deep`; reload
     → `lang==vi`, `critique_level==9`, `interview_rigor==deep` ALL present (no clobber).
   - CLI: `--set` two keys in one call both persist; `--set k=bad` exits non-zero, file unchanged; value containing
     `=` splits on first `=` only.
2. Run tests → red.
3. Implement schema (2 keys in `DEFAULTS`/`ENUMS`).
4. Implement the load-merge `--set` CLI in `main()`.
5. Run tests → green. Full `product-spec` pytest → confirm no regression.

## Success Criteria

- [ ] New + updated tests pass; full suite green (count guard now 15 — no contradiction).
- [ ] Fresh load yields both defaults = `standard`.
- [ ] Old-file (no new keys) load == defaults (non-breaking proven).
- [ ] `--set` preserves all other existing keys (load-merge proven by test); bad enum writes nothing, non-zero exit.

## Risk Assessment

- **Data loss if `--set` skips load-merge (red-team A, Critical)** — the load-merge test is the guard; it MUST exist
  and pass before this phase is done.
- **CLI `k=v` parsing**: split on first `=` only (values may contain `=`). Tested.
