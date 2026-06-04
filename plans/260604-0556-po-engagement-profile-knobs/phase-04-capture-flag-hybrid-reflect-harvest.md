---
phase: 4
title: "Capture: --set flag + end-of-session forcing-function"
status: pending
priority: P2
effort: "2h"
dependencies: [1, 2]
---

# Phase 4: Capture: --set flag + end-of-session forcing-function

## Overview

Make the knobs *learnable* without violating GATE-NEVER-ASSUME, using only PO-driven paths with real evidence. The
explicit `--set` flag landed in Phase 1. This phase adds the **live end-of-session forcing-function**. The original
`--reflect engagement-profile` harvest is **CUT** (red-team G/E/F/H: `reflect_scan` emits git-only anchors; soft
traits leave no deterministic signal, so a retroactive harvest would manufacture candidates — forbidden).

## Requirements

- Functional:
  - During the live interview the AI may observe real conversational evidence (e.g. goals omitted a metric ×N this
    session; PO repeatedly waved off deep probing as noise). At session close it asks ONCE — tighten OR relax a knob —
    and on PO confirm persists via Phase-1 `preferences.py --set` (load-merge).
  - Bidirectional: may propose lowering `interview_rigor` (relax) as well as raising it.
- Non-functional:
  - **No auto-write** (red-team P): the write only happens after an explicit PO confirm in the close-out
    `AskUserQuestion`. The script cannot enforce "confirmed"; with reminders + harvest cut, the ONLY writers are
    `--set` (PO-typed) and this forcing-function (PO-confirmed) — no auto path exists.
  - **No third standalone nudge** (red-team L): piggyback the EXISTING Closing-the-Loop sequence
    (`workflow-interview.md:236-242`, the end-of-interview validate nudge), as one batched close-out — not a separate
    interrupt.

## Architecture

- `workflow-interview.md` Closing-the-Loop section: add the engagement-knob proposal as an OPTIONAL item in the
  existing close-out batch (only when live evidence exists), with the confirm→`--set` persist path.
- Honesty caveat consistent with `memory-enforcement.md`: this raises consideration-rate, not write-quality
  ("reduced recurrence", never "the store fills itself").
- **No** `reflect_scan.py` / `memory-harvester.md` / `workflow-reflect.md` changes (harvest cut).

## Related Code Files

- Modify: `.claude/skills/product-spec/references/workflow-interview.md` (Closing-the-Loop addition only)

## Implementation Steps

1. Add the end-of-session forcing-function line to the existing Closing-the-Loop batch: condition (live evidence),
   the one-question tighten/relax `AskUserQuestion`, and confirm→`preferences.py --set` persist.
2. Add the honesty caveat (consideration-rate, not guaranteed capture).
3. Verify the multi-write session path is safe (depends on Phase-1 load-merge; the Phase-1 load-merge test covers it).
4. Grounding check: the line references the real Phase-1 CLI flags + enum tokens.

## Success Criteria

- [ ] Closing-the-Loop documents the optional knob proposal as part of the existing batch (no separate nudge).
- [ ] Persist path is confirm→`--set` (load-merge); bidirectional (tighten/relax) documented.
- [ ] No `--reflect`/harvester/`reflect_scan` changes exist (harvest stays cut).
- [ ] Honesty caveat present; no over-claim of auto-capture.

## Risk Assessment

- **Confirm gate is LLM-prose only (red-team P)**: accepted — there is no auto-write path left to abuse, and `--set`
  is the deterministic PO-consent path. Document plainly that markdown cannot enforce the gate.
- **Noise (red-team L)**: piggybacking the existing close-out is the mitigation; do not add a standalone prompt.
