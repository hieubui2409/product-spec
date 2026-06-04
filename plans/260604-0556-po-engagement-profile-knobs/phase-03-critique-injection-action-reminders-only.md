---
phase: 3
title: "Critique injection (action+reminders only)"
status: pending
priority: P2
effort: "2h"
dependencies: [1]
---

# Phase 3: Critique injection (action+reminders only)

## Overview

Apply ONLY `action_prompting` + `standing_reminders` to product-spec-critique. **Explicitly NOT** `interview_rigor`
(critique harshness is owned by `critique_level` 1..9 — applying rigor too would collide ladders). `critique_scan`
already reads `preferences`, so this is additive read + workflow guidance.

## Requirements

- Functional:
  - `action_prompting` shapes density of fix-suggestions in the critique report (minimal = terse fix per finding;
    proactive = fuller remediation prompts) — bounded so it never turns the report into an implementation plan.
  - `standing_reminders` surfaced as cross-cutting checks the critic always applies.
  - `interview_rigor` is NOT read by critique; `critique_level` untouched.
- Non-functional: critique stays report-only (no spec edits, no CI gating) — `action_prompting=proactive` must not
  breach the report-only contract.

## Architecture

- `critique_scan.py`: include `action_prompting` + `standing_reminders` in the bundle it already assembles from
  `preferences.load()` (alongside `critique_level`/`critique_detail_level`). No new store.
- `workflow-critique.md`: document how the consolidator/lenses use them; add an explicit "rigor NOT applied here"
  note pointing to `critique_level` as the harshness home (resolve overlap B from the design doc).

## Related Code Files

- Modify: `.claude/skills/product-spec-critique/scripts/critique_scan.py`
- Modify: `.claude/skills/product-spec-critique/references/workflow-critique.md`
- Read for context: `critique_bundle.py`, `references/voice-and-tone.md`.
- Modify (test): `.claude/skills/product-spec-critique/scripts/tests/test_critique_scan.py` (assert the two keys
  appear in the bundle; assert rigor does NOT).

## Implementation Steps

1. **Test first**: extend `test_critique_scan.py` — bundle includes `action_prompting` + `standing_reminders`
   from prefs; bundle does NOT include `interview_rigor`.
2. Add the two keys to the `critique_scan` bundle assembly (reuse `preferences.load`).
3. Update `workflow-critique.md`: fix-suggestion density per `action_prompting` (with the report-only bound),
   `standing_reminders` as always-checks, and the explicit "harshness = `critique_level`, not rigor" note.
4. Run critique test suite → green.

## Success Criteria

- [ ] `critique_scan` bundle carries `action_prompting` + `standing_reminders`, never `interview_rigor`.
- [ ] `workflow-critique.md` states the report-only bound on proactive fix-prompts + the rigor/critique_level
      separation.
- [ ] Critique test suite green; no change to `critique_level` behavior.

## Risk Assessment

- **Scope creep (design doc unresolved Q3)**: `action_prompting=proactive` could push the report toward a fix-list,
  violating report-only. Mitigate: cap at "suggest the fix direction per finding", never multi-step plans; assert
  the bound in the workflow doc and a lens-prompt note.
