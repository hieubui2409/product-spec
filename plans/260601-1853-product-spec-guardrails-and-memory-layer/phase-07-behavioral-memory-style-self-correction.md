---
phase: 7
title: "behavioral-memory-style-self-correction"
status: pending
priority: P2
effort: "6h"
dependencies: [4, 5, 6, 8]
---

# Phase 7: behavioral-memory-style-self-correction

## Overview
Two NEW behavioral stores extending the memory layer: **3D PO-style** (voice/vocabulary/recurring-asks → shapes prose) and **3E LLM-self-correction** (recurring mistakes/protocol slips → guards behavior). Final integrator: owns the behavioral spec + the small hook-line insertions into the hub workflow files (last writer, after P4/P5/P6/P8).

## Requirements
- Functional:
  - **3D `po-style.yaml`** (committed): register, domain vocabulary (PO's own terms), recurring asks, do/don't phrasing — **lang-keyed** (en/vi). Read at prose-gen (vision narrative / story desc / AskUserQuestion text); written when PO corrects generated wording.
  - **3E `self-corrections.json`** (committed now; privacy-toggle later): slip + violated-rule (cite the 5 principles) + frequency/last-seen + corrective reminder. Written when `check_fence.py`/Contradiction Protocol/PO catches a slip; read as pre-flight self-check before at-risk ops (e.g. before Write).
  - New `references/behavioral-memory.md`: full 3D/3E spec (purpose/file/format/DRY-guard/read-trigger/write-trigger/Script-vs-LLM) + the **distinction** (3D shapes OUTPUT wording; 3E guards BEHAVIOR).
- Non-functional: DRY — behavioral memory shapes PHRASING only, never re-homes structural facts; 3E never user-facing voice. Honesty: 3E reduces recurrence, not a hard block (soft-fence caveat).

## Architecture
- Stores under `docs/product/.memory/`. 3D is PO-authored intent (commit); 3E is session-derived (commit now per locked decision; flag privacy toggle since it can echo PO wording — mirrors agent-memory always-drop posture).
- Write triggers (the part that keeps the store from staying empty):
  - 3D: after interview rounds + on explicit PO wording-correction → hook-line in `workflow-interview.md` (P4-owned → P7 is final writer).
  - 3E: fed by `check_fence.py` (P8) structural slip detection + Contradiction Protocol (P5) → hook-line in `workflow-validate.md` (P5/P6-owned → P7 is final writer).
- Script-vs-LLM: script reads/writes files + validates shape + (for 3E) `check_fence.py` detects structural slips; LLM observes voice + writes entries + applies lessons.

## Related Code Files
- Create: `references/behavioral-memory.md`, `scripts/behavioral_memory.py` (read/write/validate 3D+3E shape), `scripts/tests/test_behavioral_memory.py`
- Modify (final writer, after owners): `references/workflow-interview.md` (3D read hook-line), `references/workflow-validate.md` (3E write hook-line)
- Runtime (PO project): `docs/product/.memory/po-style.yaml`, `docs/product/.memory/self-corrections.json`

## Tests (write FIRST — TDD)
1. `test_po_style_lang_keyed` → observations stored per-lang; reading `vi` never returns `en` voice.
2. `test_po_style_shape_validate` → malformed entry rejected; well-formed accepted.
3. `test_self_correction_append` → slip entry append + frequency increment on repeat.
4. `test_self_correction_cites_rule` → entry requires a violated-rule field (one of the 5 principles).
5. `test_behavioral_no_structural_fact` (DRY guard, **red-team RT-17 split**) → the script-side guard rejects copies of CLOSED-ENUM structural values (`scope` in/out/core-value, `moscow`, `horizon` — script-decidable). Persona-label copy detection is OUT of the pure shape-validator (persona labels are open PO free-text, not a closed enum, and PRODUCT.md is not passed in) → it is an **LLM-side** check per the Script-vs-LLM split, documented in `behavioral-memory.md`, NOT asserted in this pytest.

## Implementation Steps
1. Write tests (red).
2. Draft `references/behavioral-memory.md` (3D/3E spec + distinction + DRY guard + privacy note).
3. Implement `behavioral_memory.py` (read/write/validate 3D+3E, lang-keyed, DRY guard).
4. Add 3D read hook-line to `workflow-interview.md`; 3E write hook-line to `workflow-validate.md` (as final writer).
5. Tests green; full suite no regression.

## Success Criteria
- [ ] 3D `po-style.yaml` + 3E `self-corrections.json` schemas + helper; 5 tests pass.
- [ ] Helper + hook-lines documented (3D read in interview, 3E write in validate); script-side append/validate/shape tested. *(red-team RT-18: triggers are LLM-discretionary prose, not a deterministic guarantee — do NOT claim "stores actually accrue"; that's reduced-recurrence, not a hard invariant.)*
- [ ] DRY guard rejects structural-fact copies into po-style.
- [ ] `behavioral-memory.md` documents the OUTPUT-shaping vs BEHAVIOR-guarding distinction + privacy posture.

## Risk Assessment
- Empty-store risk (no trigger) → tests + explicit hook-lines (covered).
- Privacy leak (3E echoes PO wording, committed) → documented privacy toggle; mirrors agent-memory drop posture.
- Final-writer coordination on hub files → deps [4,5,6,8]; whole-file read before the hook-line edit.
