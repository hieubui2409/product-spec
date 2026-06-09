---
title: "Bundle context/flow optimization (measure-first, conservative)"
description: ""
status: completed
priority: P2
branch: "master"
tags: []
blockedBy: []
blocks: []
created: "2026-06-09T04:48:01.598Z"
createdBy: "ck:plan"
source: skill
---

# Bundle context/flow optimization (measure-first, conservative)

## Overview

Measure-first, **conservative** optimization of the bundle's per-turn context FLOW — core skills
`product-spec` + `product-spec-critique`; `release`/`telemetry` light-touch (low value/freq). The ask is
**flow effectiveness**, not byte-cutting.

**NON-NEGOTIABLE:** no edit may reduce a skill's reasoning effectiveness. Every change ships with TWO
proofs: **(a)** the harness shows the SKILL.md token cost dropped + the GATE co-presence check is green,
**(b)** STRUCTURE held (full pytest **658** green) AND REASONING held (a **spawned sub-agent** judges the
routing/advisory scenarios before vs after — see below). Missing (b) → revert. TDD: lock current behavior
before each refactor.

**Source brainstorm:** `plans/reports/brainstorm-260609-1048-bundle-context-flow-optimization-report.md`

**The lever (sole focus):** **SKILL.md flag-table verbosity** — the only context paid on EVERY skill
activation. Compact each flag to what+when+ref-pointer+GATE-keyword; relocate elaboration into the ref that
already loads when the flag fires (net info preserved). **OUT (removed entirely per PO 2026-06-09, after
red-team — low value / high risk):** (1) GATE/fact prose dedup (could silently delete a safety GATE from a
flag's context — BLOCKER-2), (2) trimming the on-demand reference files (already lazy-loaded → negligible
per-turn saving, unverifiable). Also OUT: `.claude/rules/*` (ClaudeKit), `voice-and-tone.md` content,
runtime caching/hooks.

## Red-team rework (2026-06-09) — verdict REWORK, applied

Adversarial review found the original plan's safety claim broken; applied:
- **BLOCKER-1 (the reasoning gate was theater):** offline `run_evals`/pytest asserts STRUCTURE only
  (2 structural for product-spec, **0 for critique**); there is **no routing/flag-selection eval at all**
  (every existing scenario names its own flag). → Reasoning gate redefined (sub-agent, below) + Phase 2
  AUTHORS routing-selection scenarios before any compaction.
- **MAJOR-3:** the per-flag load-set is flat prose, not a table → the harness gates on **per-skill SKILL.md
  size** + a mechanical **GATE co-presence check**; per-flag token numbers are advisory only.
- **Scope cut (PO):** the two low-value/high-risk pieces — GATE/fact dedup and reference-file trimming —
  are **removed entirely** (not deferred). Only the SKILL.md lever remains.
- **MINOR-7:** one focused commit per compaction (surgical revert).

**Reasoning proof (the honest NON-NEGOTIABLE) — PO-resolved, NO API key:** offline pytest 658 = STRUCTURE
preserved (necessary, not sufficient). REASONING preserved is proven by **spawning a sub-agent** (itself a
Claude instance = the LLM judge) to (i) produce the eval materials / goldens and (ii) run + judge the
routing-selection + affected advisory scenarios **before vs after** each compaction, reading both SKILL.md
versions and ruling whether routing/reasoning held. A sub-agent "after < before" verdict → revert that
commit. (`llm_eval.py` HTTP path optional, not required.)

**Build order:** harness + co-presence guard (1) → routing-eval authoring + sub-agent proof protocol (2)
→ SKILL.md compaction (3) → wiring + docs (4).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Token-footprint harness + GATE co-presence guard](./phase-01-token-footprint-harness.md) | Complete |
| 2 | [Routing-eval authoring + sub-agent proof protocol](./phase-02-flow-audit-gate-fact-dedup.md) | Complete |
| 3 | [SKILL.md flag-table compaction](./phase-03-skill-md-flag-table-compaction.md) | Complete |
| 4 | [Double-gate wiring + docs](./phase-04-double-gate-wiring-docs.md) | Complete |

> **Execution complete 2026-06-09.** Proof trail: [`EVIDENCE.md`](./EVIDENCE.md). product-spec SKILL.md
> −11.8% / critique −3.7% (per-turn lever); harness + co-presence guard + pytest regression guard added;
> best-of-3 sub-agent routing judge 18/18 HELD; pytest 658/172/39 green; 3 review waves clean (ship).

## Dependencies

- Internal: **1 → 2 → 3 → 4** (linear). 1 (harness+co-presence) is the measurement+safety gate. 2 authors
  the routing/reasoning eval that 3 needs (no compaction without a reasoning gate that exists). 3 (SKILL.md
  compaction) is gated by 1+2. 4 wires the regression guard + version/docs.
- Cross-plan: `260609-1110-telemetry-hook-io-and-crash-audit` has **executed** (working-tree changes:
  hooks, telemetry SKILL.md 197→118 + v1.0.1, product-spec `install.sh`, +2 tests in
  `test_memory_gap_hook.py`). **No file overlap** with this plan's active scope (harness, routing-eval,
  product-spec/critique SKILL.md compaction) → **not blocking**. Effect on this plan: the structural
  baseline is now **658** (was 656); product-spec/critique SKILL.md sizes (196/182) are **unchanged**, so
  the compaction candidate set still holds.
- The learning-loop plan `260609-0847` is DONE (shipped `--learn`); its files are part of the surface this
  plan measures, not a dependency.

## Acceptance (whole-plan)

- Harness reports per-skill **SKILL.md token reduction** for product-spec + critique; **GATE co-presence
  check green** (no GATE pointer without its authoritative home in the flag's load-set ∪ always-on).
- **Structure:** full pytest **658 green** after every block (verified baseline, venv interpreter, no rtk
  hook). **Reasoning:** the spawned sub-agent judges the routing-selection + advisory scenarios green
  before/after each compaction. No reasoning proof → revert.
- No GATE removed; one focused commit per compaction.
- `verify_skill_versions.py` + CHANGELOG consistent for changed skills.

## PO decisions (both RESOLVED 2026-06-09)

1. **Reasoning proof** — **spawn a sub-agent** to generate eval materials + judge routing/advisory
   scenarios before/after. No API key (the sub-agent is the LLM judge).
2. **Scope** — **SKILL.md compaction ONLY.** The two low-value/high-risk pieces (GATE/fact dedup +
   reference-file trimming) are **removed entirely** from the plan.

## Validation Log

### Verification Results (Standard tier, 4 phases) — 2026-06-09

- Claims checked: 4 · Verified: 4 · Failed: **0** · Unverified: 0
- `_shared/lib/` exists (harness home valid); `context_footprint.py` absent (new file, correct);
  eval advisory assertions = **13 product-spec / 22 critique** (matches the red-team finding that the
  reasoning signal doesn't gate offline); SKILL.md = product-spec **196** / critique **182** (matches plan).
- Red-team already ran (`## Red-team rework`); no `[UNVERIFIED]` tags outstanding.

### Session 1 (2026-06-09) — 3 questions, all answered

- **Q1 Compaction candidate set** → **16 verbose product-spec flags** (`--viz` 970c, `--learn` 690c,
  `preferences.py --set` 560c, `--apply-critique`, `--discover`, `--layers`, `--format`, `--reflect`,
  `--summary`, `--decision`, `--voice`, `--compact-mode`, `--lang`, `--export`, `--filter-wont`,
  `--status`) **+ critique `--level 1..9` (1590c) + `[scope]`**. SKIP: terse flags (product/brd/prd/epic/
  story, validate, strict, approve, group-by, depth, auto, update) + the 5 critique-mid flags. → Phase 3.
- **Q2 Sub-agent judge confidence** → **best-of-3 / majority vote** per compacted flag (not a single
  pass). → Phase 2 (proof recipe) + Phase 3 (per-commit gate).
- **Q3 Detail-home for ref-less flags** → **create a dedicated ref** for the truly ref-less leftovers
  (`--summary`, `--decision`, `--lang`); `--status` reuses its existing `workflow-status.md`; the
  viz/export flags (`--viz`/`--format`/`--filter-wont`/`--layers`/`--group-by`/`--depth`/`--compact-mode`)
  relocate into the EXISTING `visualization-spec.md` + `workflow-export.md`. → Phase 3.

### Whole-Plan Consistency Sweep
✅ Clean (2026-06-09): candidate set + detail-home propagated to Phase 3; best-of-3 propagated to Phase
2+3; no stale "deferred/Phase 5/GATE-dedup/ref-trim" references remain (the two cut pieces appear only in
the explicit "removed entirely" note). 0 unresolved contradictions.

### Rebaseline after sibling plan (2026-06-09)
The `260609-1110-telemetry-hook-io-and-crash-audit` plan executed; re-verified impact: structural baseline
**656 → 658** (updated across plan + phases), product-spec/critique SKILL.md sizes unchanged (candidate set
intact), no file overlap with active scope. Suite re-run green at 658. No plan logic change needed.
