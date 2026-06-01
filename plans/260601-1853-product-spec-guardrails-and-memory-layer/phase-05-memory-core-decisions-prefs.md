---
phase: 5
title: "memory-core-decisions-prefs"
status: done
priority: P1
effort: "6h"
dependencies: [2, 8]
---

# Phase 5: memory-core-decisions-prefs

## Overview
Decision Register (`decisions.md` + `decision_register.py`) wired into the Contradiction Protocol to kill re-litigation, plus PO Preferences (`preferences.yaml`). First memory stores. Script-vs-LLM split: script allocates `DEC-n` + validates + parses; LLM writes rationale. Depends on P2 (co-edits the post-DRY `workflow-validate.md`).

## Requirements
- Functional:
  - `decision_register.py`: `--alloc-id` (next free `DEC-n`), `--append` (validate grammar + write a record), `--list` (parse active DECs). Lives under `docs/product/decisions.md` (visible, committed).
  - Contradiction Protocol wiring (`workflow-validate.md`): on resolve (Keep/Change/Hybrid) **auto-append a DEC**; on a new contradiction, **read `decisions.md` first** → if a matching active DEC exists, surface it ("you decided DEC-n because … — keep or supersede?").
  - `--decision` flag: PO logs a standalone decision.
  - `preferences.yaml` under `docs/product/.memory/`: `lang`, `detail_level`, `prioritization`, `dismissed_reminders`. Closed enums; missing key → hard-coded default.
- Non-functional: DRY — decisions hold rationale + ID links only, NEVER structural facts; prefs are defaults (frontmatter `lang` still wins). All committed.

## Architecture
- ID grammar `^DEC-\d+$`; `--alloc-id` = max-existing + 1 (read-then-write; single-PO so no lock — note team-mode lock as future).
- `decisions.md` record template → add `assets/templates/decision-record.md` (`{{token}}` fill, consumed by `generate_templates.py` pattern OR by `decision_register.py` directly).
- Lifecycle: append-only; `status: active|superseded`; new decision uses `supersedes: DEC-n`.
- `preferences.yaml` read by the interview flow — the *read hook* lives in `workflow-interview.md` which is **P4-owned**; P5 defines the schema + a `preferences` read/write helper (small script fn or documented convention). P5 does NOT edit `workflow-interview.md`.
- `SKILL.md` is owned ENTIRELY by **P2** (references list + ALL flag rows). P5 implements the `--decision` logic + documents it; **P2 adds the `--decision` SKILL flag row** (P2 knows it from this plan). P5 does NOT edit SKILL.md — avoids a second writer.

## Related Code Files
- Create: `scripts/decision_register.py` (imports `fs_guard` from P8a for the `decisions.md` write → dep [8]), `assets/templates/decision-record.md`, `scripts/tests/test_decision_register.py`
- Modify: `references/workflow-validate.md` (Contradiction Protocol wiring — **after P2 in the validate-hub chain**)
- NOT owned here: `SKILL.md` `--decision` flag row (added by P2)
- Runtime (PO project, via templates/scripts, not skill repo): `docs/product/decisions.md`, `docs/product/.memory/preferences.yaml`

## Tests (write FIRST — TDD)
1. `test_alloc_id_first` → empty/absent decisions.md → `DEC-1`; with DEC-1,DEC-2 → `DEC-3`.
2. `test_alloc_id_ignores_superseded` → numbering monotonic regardless of status.
3. `test_append_validates_grammar` → reject malformed id/record; accept well-formed; append-only (no overwrite).
4. `test_list_active` → returns only `status: active`.
5. `test_preferences_missing_key_default` → absent key → documented default; never crash.

## Implementation Steps
1. Write tests (red).
2. Implement `decision_register.py` (`--alloc-id/--append/--list`) + `decision-record.md` template.
3. Define `preferences.yaml` schema + read/write helper + default fallback.
4. Wire Contradiction Protocol in `workflow-validate.md` (read decisions.md first; auto-append on resolve) + implement + document `--decision` (P2 adds its SKILL row).
5. Tests green; full suite no regression.

## Success Criteria
- [ ] `decision_register.py` alloc/append/list works; 5 tests pass.
- [ ] Contradiction Protocol reads decisions.md first + auto-appends a DEC on resolve.
- [ ] `--decision` flag documented + functional.
- [ ] `preferences.yaml` schema + default fallback; DRY guards documented (no structural facts in decisions).

## Risk Assessment
- DRY drift (decisions copying structural facts) → guard in template + doc; DRY-lint deferred.
- DEC-id race (concurrent append) → single-PO now; team-mode lock = future note.
- Validate-hub coordination: edits `workflow-validate.md` after P2 (DAG `dependencies: [2]`).
