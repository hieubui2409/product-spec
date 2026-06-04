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

Foundation. Add the 3 engagement knobs to `preferences.py` schema and a deterministic `--set` write-CLI. Pure
script logic → **tests-first** (TDD). Everything additive: zero breaking changes.

## Requirements

- Functional:
  - `interview_rigor` ∈ {light, standard, deep}, default `deep`.
  - `action_prompting` ∈ {minimal, standard, proactive}, default `proactive`.
  - `standing_reminders` = `list[str]`, default `[]` (modeled on existing `dismissed_reminders`).
  - `preferences.py --set <key>=<value>` write-CLI (repeatable), routes through `save()` (enum-validated, fenced).
    For `standing_reminders`, support `--add-reminder <s>` / `--remove-reminder <s>` (union/remove, not enum).
- Non-functional:
  - Non-breaking: missing keys degrade to defaults; old files load unchanged.
  - `save()` keeps file byte-stable (sorted keys, LF) — no churn vs current writer.

## Architecture

- `DEFAULTS` += 3 keys; `ENUMS` += `interview_rigor`, `action_prompting` (NOT `standing_reminders` — it is a list,
  validated like `dismissed_reminders`).
- `load()`: existing list-handling branch already covers a new list key — generalize the `dismissed_reminders`
  branch to also coerce `standing_reminders` to `list[str]`.
- `save()`: existing list-guard generalized to both list keys.
- CLI: extend `main()` (currently read-only dump) with optional `--set KEY=VALUE` (repeatable),
  `--add-reminder`, `--remove-reminder`. Mirror the `behavioral_memory.py --voice` CLI shape. With no write flag,
  behavior unchanged (still dumps `load()`). A bad enum → `PreferenceError` → non-zero exit + clear message,
  nothing written.

## Related Code Files

- Modify: `.claude/skills/product-spec/scripts/preferences.py`
- Modify: `.claude/skills/product-spec/scripts/tests/test_preferences.py`

## Implementation Steps

1. **Tests first** in `test_preferences.py`:
   - defaults: fresh `load()` returns `interview_rigor=deep`, `action_prompting=proactive`, `standing_reminders=[]`.
   - backward-compat: a `preferences.yaml` written WITHOUT the new keys still loads them at default (the core
     non-breaking assertion).
   - enum guard: `save({"interview_rigor":"hard"})` → `PreferenceError` (note: `hard` is NOT a value — light/standard/deep).
   - list handling: `standing_reminders` round-trips a list; a non-list value degrades on read, raises on save.
   - CLI: `--set action_prompting=minimal` persists; `--add-reminder "re-check metric on goals"` unions;
     `--remove-reminder` removes; `--set` with bad enum exits non-zero and writes nothing.
2. Run tests → red.
3. Implement schema (`DEFAULTS`/`ENUMS`), generalize list branches in `load()`/`save()`.
4. Implement CLI write flags in `main()`.
5. Run tests → green. Run full `product-spec` pytest to confirm no regression.

## Success Criteria

- [ ] New tests pass; existing `test_preferences.py` + full suite green (no regression).
- [ ] Fresh load yields the 3 documented defaults.
- [ ] Old-file (no new keys) load == defaults (non-breaking proven by test).
- [ ] `--set` / `--add-reminder` / `--remove-reminder` persist correctly; bad enum writes nothing, non-zero exit.

## Risk Assessment

- **YAML bool coercion** (`off/on/no/yes`) already handled for enum keys; new enums are word-valued so unaffected —
  but add a test that a literal `standing_reminders: [no]` does not silently become `[False]` (coerce to str).
- **CLI value parsing**: `--set k=v` splitting on first `=` only (values may contain `=`). Test it.
