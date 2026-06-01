---
phase: 6
title: "tier0-forcing-functions-refs"
status: completed
priority: P1
effort: "5h"
dependencies: [2, 3, 4, 5]
---

# Phase 6: tier0-forcing-functions-refs

## Overview
The portable (no-hook) reliability core, in the reference prose the LLM follows: a REQUIRED "Memory pass" in
`--validate`, a per-prose-turn 3D forcing-function in interview, the batch-store wiring, and the `unrecorded_signals`
doc. Prose phase — verified by structural checks, not pytest. `workflow-validate.md` is a single-owner hub here (no
other phase edits it) to avoid conflict.

## Requirements
- Functional (reference edits):
  - `workflow-validate.md`: add **Step "Memory pass"** — the validate report MUST include a section answering
    *contradiction→DEC? · slip→3E? · `memory_gap` candidates?* (even "none"); wire Step 2 to emit one batch payload and
    call `judgment_cache --store-batch` (P3) instead of N× `--store`.
  - `workflow-interview.md`: add a **per-prose-turn 3D forcing-function** ("did the PO correct wording this turn? →
    `record_po_style`") + an **end-of-interview validate nudge** ("you changed N items since last validate — run
    `--validate`?"). Update the existing `--dump po-style` read hook reference if needed.
  - `workflow-status.md`: document the `unrecorded_signals` section + the soft `--reflect` suggestion.
  - `behavioral-memory.md`: update 3D/3E **write-trigger** sections to reference the forcing-functions + the (opt-in)
    hook + `--voice`; keep the honesty caveats.
  - **NEW `references/memory-enforcement.md` (red-team R3 — DRY home):** the single operative home for the whole
    enforcement model — the `memory_gap` signal catalogue, the Tier-0 forcing-functions, the Tier-1 opt-in hook +
    per-signal policy (fence=persist / others=nudge-once), the recommend-and-ask install posture, and the honest ceiling.
    P7 (hook) + P9 (reflect) + CLAUDE.md (P10) LINK here instead of restating. Without it the hook's how/why is homeless.
- Non-functional: DRY single-home (no fact stated authoritatively in two refs — cross-link by id); no leaked plan-phase
  refs (rule §5); token-reasonable.

## Architecture
Pure documentation wiring over P2–P5 scripts. `workflow-validate.md` reconciles the new "Memory pass" with the existing
Contradiction Protocol / Decision Register wiring (already in the file). The forcing-functions are prompt-level
"consideration" gates, NOT script gates.

## Related Code Files
- Create: `references/memory-enforcement.md` (DRY home for the enforcement model — red-team R3)
- Modify: `references/workflow-validate.md` (Memory pass + batch-store wiring) — **sole owner**
- Modify: `references/workflow-interview.md` (3D per-turn forcing-fn + validate nudge)
- Modify: `references/workflow-status.md` (unrecorded_signals + reflect hint)
- Modify: `references/behavioral-memory.md` (3D/3E trigger update)
- Read for context: P2 `memory_gap`, P3 `--store-batch`, P4 `--voice`, P5 status output

## Verification (structural — no pytest)
- `grep` confirms a "Memory pass" section exists in `workflow-validate.md` and names the batch-store call.
- `grep` confirms the 3D per-turn forcing-fn + validate nudge in `workflow-interview.md`.
- Cross-ref check: every script/flag named resolves to a real script/flag (P2–P5); no dangling refs.
- §5 check: no `P<n>`/phase/finding-code leaks in the edited prose.
- DRY check: the "Memory pass" steps live in ONE home (workflow-validate.md); others link, not copy.

## Implementation Steps
1. Edit `workflow-validate.md` (Memory pass + batch-store), reconciling with existing Contradiction/Decision wiring.
2. Edit `workflow-interview.md` (3D per-turn forcing-fn + end nudge).
3. Edit `workflow-status.md` + `behavioral-memory.md`.
4. Run the structural verification checks; fix any dangling ref / §5 leak / DRY dup.

## Success Criteria
- [ ] "Memory pass" section present + names `--store-batch`; 3D forcing-fn + validate nudge present.
- [ ] All structural checks pass (cross-ref resolves, no §5 leak, DRY single-home).
- [ ] No edit to any file owned by another phase (esp. CLAUDE.md/SKILL.md → P10).

## Risk Assessment
- Hub conflict: `workflow-validate.md` already carries Contradiction/Decision wiring + cache orchestration — read the
  WHOLE file before editing; reconcile, don't duplicate. Sole-owner here prevents parallel-write conflict.
