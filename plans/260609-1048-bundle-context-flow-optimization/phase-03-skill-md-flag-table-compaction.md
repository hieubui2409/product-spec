---
phase: 3
title: "SKILL.md flag-table compaction"
status: completed
priority: P2
effort: "0.5d"
dependencies: [2]
---

# Phase 3: SKILL.md flag-table compaction

## Overview

Conservatively compact the verbose flag tables in `SKILL.md` (paid on EVERY skill activation). Per flag,
keep **what + when + ref-pointer + the one GATE keyword** — enough for the router to choose correctly —
and move the elaboration (edge cases, examples, multi-clause behavior) into the ref that already loads
when that flag fires. Routing crispness preserved; no flag becomes ambiguous.

## Requirements

- Functional:
  - **Candidate set (PO-validated — only these; terse flags untouched):**
    - product-spec (16 verbose): `--viz` (970c), `--learn` (690c), `preferences.py --set` (560c),
      `--apply-critique` (459c), `--discover` (400c), `--layers` (379c), `--format` (362c), `--reflect`
      (326c), `--summary` (319c), `--decision` (297c), `--voice` (296c), `--compact-mode` (293c), `--lang`
      (240c), `--export` (208c), `--filter-wont` (193c), `--status` (192c).
    - critique: `--level 1..9` (1590c) + `[scope]` (225c).
    - **SKIP** (already terse / mid, no gain): product/brd/prd/epic/story, validate, strict, approve,
      group-by, depth, auto, update; the 5 critique-mid flags (`--no-web`/`--refresh-web`/`--no-inherit`/
      `--no-rollup`/`--inherit`).
  - Reduce each candidate row to: `<flag> | <what> · <when> · GATE:<keyword if any> · see <ref>`.
  - **Detail-home (PO-validated):**
    - Flags WITH a ref → relocate elaboration into that ref (`--learn`→workflow-learn, `--voice`→
      behavioral-memory, etc.).
    - viz/export flags (`--viz`/`--format`/`--filter-wont`/`--layers`/`--group-by`/`--depth`/
      `--compact-mode`) → relocate into the EXISTING `visualization-spec.md` + `workflow-export.md`.
    - `--status` → reuse existing `workflow-status.md`.
    - **`--summary`, `--decision`, `--lang` → CREATE a dedicated small ref each** (`workflow-summary.md`,
      `workflow-decision.md`, `workflow-lang.md`) + wire into the on-demand section.
  - **Detail relocation, not deletion:** every removed clause lands in its ref (net info preserved).
  - Keep the always-on safety lines + the no-flag menu intact (router-critical).
- Non-functional: SKILL.md stays self-consistent (each compacted row's ref-pointer matches the on-demand
  section); the harness SKILL.md token count drops without losing a flag's "when to use".

## Architecture

```
per flag row: extract elaboration → ensure present in its ref → replace row with compact line
keep: flag name, 1-line what+when, GATE keyword, ref pointer
verify: harness (SKILL.md tokens ↓) + routing eval (flag chosen correctly) + pytest/eval green
```

## Related Code Files

- Modify: `.claude/skills/product-spec/SKILL.md` (16 candidate rows + on-demand section)
- Modify: `.claude/skills/product-spec-critique/SKILL.md` (`--level`, `[scope]` rows)
- Modify (absorb relocated detail): `references/visualization-spec.md`, `references/workflow-export.md`,
  `references/workflow-status.md`, + the per-flag `workflow-*.md`/`behavioral-memory.md` that already exist
- Create: `references/workflow-summary.md`, `references/workflow-decision.md`, `references/workflow-lang.md`
  (the 3 truly ref-less flags — PO-chosen dedicated refs)
- Reuse: `context_footprint.py` (Phase 1) for the SKILL.md before/after delta + co-presence check

## Implementation Steps (TDD)

1. **Lock first:** the routing-selection scenarios from Phase 2 are green on the current SKILL.md +
   the harness baseline is captured. (Phase 2 guarantees this gate now EXISTS — red-team BLOCKER-1.)
2. Per flag (one focused commit each — red-team MINOR-7): confirm the elaboration exists in its ref (add
   if missing — relocation, not loss), then compact the row.
3. Reconcile each compacted row's ref-pointer with the on-demand section (no dangling pointer); run the
   Phase-1 co-presence check (a compacted row must not orphan a GATE keyword).
4. **Verify per commit (the honest gate):** harness shows SKILL.md tokens dropped + co-presence green;
   pytest 658 green (structure); **the Phase-2 sub-agent best-of-3 majority** rules routing/reasoning held
   before/after. A majority "after worse" or a tie → revert just that commit (restore the discriminating
   detail). `<!-- Updated: Validation Session 1 — candidate set + detail-home + best-of-3 -->`

## Success Criteria

- [ ] The 16 product-spec verbose flags + critique `--level`/`[scope]` compacted to one crisp line each
      (what+when+GATE+ref); terse + critique-mid flags untouched.
- [ ] Every relocated clause present in its ref; 3 new refs created (summary/decision/lang) + wired into
      the on-demand section; viz/export detail in visualization-spec/workflow-export.
- [ ] Harness: SKILL.md token count reduced for both core skills + co-presence green.
- [ ] pytest 658 green + the **best-of-3 sub-agent** confirms no flag-selection/reasoning regression.
- [ ] No-flag menu + always-on safety lines unchanged.

## Risk Assessment

- **Compaction makes the router pick the wrong flag** → keep the "when to use" + GATE keyword that
  discriminates; the Phase-2 routing scenarios are now a REAL gate (they did not exist before the
  red-team rework); restore detail on regression, reverting just that one commit.
- **Relocated detail goes missing** → step 2 verifies presence in the ref BEFORE removing from the table.
- **Pointer drift** (row points at a ref the on-demand section doesn't list) → step 3 reconciles.
