---
phase: 9
title: "reflect-harvest-and-agent"
status: completed
priority: P2
effort: "7h"
dependencies: [2, 6]
---

# Phase 9: reflect-harvest-and-agent

## Overview
Tier-2 retroactive harvest: `--reflect` runs a context-isolated, read-only opus sub-agent that reads git + `.memory`
state → proposes memory candidates as a report → the main agent interviews the PO → persists accepted ones via existing
writers (persist-after-confirm). Catches memory the inline layer missed, from structurally-readable sources only.

## Requirements
- Functional:
  - `reflect_scan.py` (deterministic, script half): emit anchors — commits touching `docs/product/` since last
    reflect/validate, files changed, revert/fix commit markers, existing-memory dedup index (vs `.memory/` +
    `decisions.md`, reusing `memory_gap` dedup). **Git-degrade-safe:** no git repo → harvest `.memory/`/`decisions.md`
    diff state only, skip commit candidates, never crash, always exit 0.
  - `.claude/agents/memory-harvester.md` (top-level): frontmatter `name: memory-harvester`, `model: opus`,
    `tools: Glob, Grep, Read, Bash` (read-only — NO Write/Edit/NotebookEdit/Task), `description` naming it serves
    product-spec `--reflect`. Body = the harvest job: read anchors+diffs → candidate report (proposed DECs /
    self-corrections / po-style). It NEVER writes memory.
  - `references/workflow-reflect.md`: the flow — `reflect_scan` → spawn harvester (Task) → candidate report →
    main-agent PO interview (accept/edit/reject) → persist via `decision_register --append` / `behavioral_memory --voice`
    / `record_self_correction` through `fs_guard`. "Silent" = no extra ceremony AFTER PO approval; never an unconfirmed
    decision/voice write (GATE-NEVER-ASSUME).
- Non-functional: read-only sub-agent enforced at the TOOL layer; persist single-homed in main agent + scripts;
  candidates are proposals; opt-in/explicit; sub-agent token cost paid only on `--reflect`.

## Architecture
`reflect_scan.py` (anchors) ∥ `memory-harvester.md` (LLM judgment) ∥ `workflow-reflect.md` (orchestration). Mirrors the
`*_anchors.py` script-half + the SKILL reference-flow pattern. The harvester is the FIRST shipped agent for the skill →
top-level `.claude/agents/` so it is spawnable; bundled via manifest (P11).

## Related Code Files
- Create: `scripts/reflect_scan.py`, `scripts/tests/test_reflect_scan.py`, `.claude/agents/memory-harvester.md`, `references/workflow-reflect.md`
- Read for context: `scripts/memory_gap.py` (dedup), `scripts/decision_register.py`, `scripts/behavioral_memory.py`, an existing `.claude/agents/*.md` (frontmatter format), `references/workflow-validate.md` (persist writers)

## Tests (write FIRST — TDD, for `reflect_scan.py`)
1. `test_anchors_commits_since_last` → commits touching docs/product since marker → listed; older → excluded.
2. `test_revert_fix_markers` → a revert/fix commit → flagged as a self-correction candidate anchor.
3. `test_dedup_against_existing_memory` → a candidate already in `.memory`/`decisions.md` → excluded (reuses `memory_gap`).
4. `test_git_degrade_no_repo` → not a git repo → no crash, exit 0, file-state anchors only, `git_available:false`.
5. `test_deterministic` → same repo state → identical anchors.
6. `test_exit_zero_always` → malformed inputs → exit 0 + `parse_error` anchor.

## Verification (agent + reference — structural)
- `memory-harvester.md` frontmatter: `model: opus`, tools are exactly the read-only set (no Write/Edit/Task).
- `workflow-reflect.md`: persist step routes through existing writers (no new write home); PO-confirm gate present; §5-clean.

## Implementation Steps
1. Write `reflect_scan.py` tests (red); implement (anchors + git-degrade); green.
2. Author `.claude/agents/memory-harvester.md` (read-only opus harvester).
3. Author `references/workflow-reflect.md` (scan → spawn → report → interview → persist-after-confirm).
4. Structural checks; full suite no regression.

## Success Criteria
- [ ] 6 `reflect_scan` tests pass; full suite green.
- [ ] Harvester agent is read-only at the tool layer + opus; cannot write memory.
- [ ] `--reflect` flow persists ONLY after PO confirm, via existing writers (no new write home).
- [ ] Git-degrade path verified (no repo → no crash).

## Risk Assessment
- Sub-agent can't see the live conversation (by design) → only git/file harvest; documented (3D conversational nuance is
  the forcing-function's job, not reflect).
- PO token cost (opus) → opt-in/explicit only; never auto-run.
