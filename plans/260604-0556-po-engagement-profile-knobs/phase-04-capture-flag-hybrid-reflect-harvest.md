---
phase: 4
title: "Capture: flag + hybrid reflect harvest"
status: pending
priority: P2
effort: "4h"
dependencies: [1, 2]
---

# Phase 4: Capture: flag + hybrid reflect harvest

## Overview

Make the knobs *learnable* without violating GATE-NEVER-ASSUME: explicit flag (done in Phase 1 CLI) + a hybrid
infer→propose→**PO-confirm** harvest. Bidirectional (may propose lowering rigor when the PO finds deep probing
noisy). Reuses the existing Tier-0 forcing-function + Tier-2 `--reflect` machinery — **no new mechanism**.

## Requirements

- Functional:
  - `--reflect` harvest gains an `engagement-profile` candidate category: harvester proposes a knob change with
    evidence → PO confirms → persisted via Phase-1 CLI/`save()`.
  - Dedup: harvester never re-proposes a value already set (reflect_scan dedup index includes current knob values).
  - Per-session interview forcing-function: when AI observes a repeated pattern (e.g. goals omit a metric ×N), it
    asks ONCE to add a `standing_reminder` / adjust a knob; writes only on confirm.
- Non-functional: harvest stays deterministic (script emits anchors only); all writes PO-confirmed; git-degrade-safe
  (inherits reflect_scan behavior).

## Architecture

- `reflect_scan.py`: extend `_existing_memory_index` to include `preference_knobs` (current resolved values from
  `preferences.load`) so the harvester dedups against already-set knobs. Anchors-only contract preserved (no
  judgment in the script).
- `memory-harvester.md` agent: add the `engagement-profile` candidate type (propose knob/reminder change with
  evidence; never auto-write).
- `workflow-reflect.md`: document the new category + the confirm→persist step (persist via `preferences.py --set` /
  `--add-reminder`).
- `workflow-interview.md`: add the per-session forcing-function line (end-of-session preferred over per-turn, to
  mirror the 3D honesty caveat / avoid noise — design doc unresolved Q2 resolved to end-of-session).

## Related Code Files

- Modify: `.claude/skills/product-spec/scripts/reflect_scan.py` (+ `tests/test_reflect_scan.py`)
- Modify: `.claude/agents/memory-harvester.md`
- Modify: `.claude/skills/product-spec/references/workflow-reflect.md`
- Modify: `.claude/skills/product-spec/references/workflow-interview.md` (forcing-function line)

## Implementation Steps

1. **Test first** (`test_reflect_scan.py`): `_existing_memory_index` / anchors include `preference_knobs` with the
   resolved current values; a knob already at non-default is present so the harvester can dedup. Degrade-safe when
   prefs file absent (defaults).
2. Implement the `preference_knobs` addition in `reflect_scan.py` (reuse `preferences.load`, import not re-impl).
3. Update `memory-harvester.md`: new `engagement-profile` candidate type + confirm-before-write rule.
4. Update `workflow-reflect.md` + `workflow-interview.md` with the category, the end-of-session forcing-function,
   and the confirm→`--set`/`--add-reminder` persist path.
5. Run reflect tests → green; full product-spec suite green.

## Success Criteria

- [ ] `reflect_scan` anchors expose current knob values for dedup; tests green; git-degrade-safe preserved.
- [ ] Harvester documents proposing knob/reminder changes (both directions) with evidence, write only on confirm.
- [ ] `workflow-reflect.md` + `workflow-interview.md` document the capture loop end-to-end (flag + harvest).
- [ ] No auto-write path exists — every learned change requires PO confirm (GATE-NEVER-ASSUME honored).

## Risk Assessment

- **Over-claiming "it learns"**: keep the honesty caveat (reduced-recurrence, not guaranteed capture) consistent
  with `memory-enforcement.md`. State it in the docs.
- **Forcing-function noise**: per-turn nudges annoy; resolved to end-of-session cadence. Document the choice.
