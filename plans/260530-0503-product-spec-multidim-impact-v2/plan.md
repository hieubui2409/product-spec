---
title: "product-spec v2.0.0 — multi-dim impact (risk/time/competition) + consistency engine, Workflow-orchestrated"
description: "Extend shipped product-spec (v1.1.0->2.0.0): finish RISK, add TIME (target_date + depends_on w/ cycle detection) + COMPETITION (parity matrix), impact-propagation engine, ASCII->HTML-native default. Executed via Workflow-tool orchestrator gated by goal.md."
status: pending
priority: P2
branch: "master"
tags: []
blockedBy: []
blocks: []
created: "2026-05-29T22:09:46.831Z"
createdBy: "ck:plan"
source: skill
---

# product-spec v2.0.0 — multi-dim impact (risk/time/competition) + consistency engine, Workflow-orchestrated

## Overview

Extend the **shipped** `cleanmatic:product-spec` skill (`v1.1.0` → **`2.0.0`** major) to fully serve **UC3 — consistency + multi-dimensional impact**. Two problems: (A) consistency/propagation is already solved by `downstream()`; (B) multi-dimensional assessment needs new structure. We add structure for **RISK** (finish the half-wired bug), **TIME** (`target_date` + `depends_on`), **COMPETITION** (parity matrix), an **impact-propagation engine**, and **downgrade ASCII** to an HTML-native default (ASCII retained as minimal text-summary tree — NOT deleted).

**Design source (authoritative):** `plans/reports/brainstorm-design-260530-0309-product-spec-multidim-impact-uc3-report.md` (67-question interview, §0 = PO decisions). Acceptance contract: [`goal.md`](./goal.md).

**Execution model — Workflow-tool orchestrated (the centerpiece):** Phase 1 builds a Workflow orchestrator that runs every content phase (2–7) through a fixed pipeline — **plan → validate → red-team → scope-driven TDD tests → implement → phase-review → cross-phase-review → checkpoint** — then a global tail of **overall-review → multi-wave review (looped against `goal.md` until 2 clean waves) → fix → ship**. `--tdd`: tests-first in every content phase.

**Non-negotiable deal-breakers (Q59), enforced by `goal.md` Category A/B:** traceability + ID integrity · back-compat with v1 specs · no-auto-edit-approved (contradiction protocol) · determinism · strict Script-vs-LLM split.

**Two highest-risk trade-offs (report §0.1):** **(T1)** `depends_on` can create cycles → mandatory `dep_cycle` detection (3-color DFS) + cycle-safe renderers BEFORE the edge ships (Phase 3 prerequisite). **(T2)** subjective LLM checks (`time_realism`, `competitive_drift`) hallucinate → mandatory structured anchors + cite-data-or-don't-flag (Phases 3/4).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Workflow Orchestration Harness](./phase-01-workflow-orchestration-harness.md) | Pending |
| 2 | [Risk Hardening](./phase-02-risk-hardening.md) | Pending |
| 3 | [Time and Dependencies](./phase-03-time-and-dependencies.md) | Pending |
| 4 | [Competition](./phase-04-competition.md) | Pending |
| 5 | [Impact Engine and Migration](./phase-05-impact-engine-and-migration.md) | Pending |
| 6 | [ASCII Downgrade to HTML-native](./phase-06-ascii-downgrade-to-html-native.md) | Pending |
| 7 | [Docs and 2.0.0 Release](./phase-07-docs-and-2-0-0-release.md) | Pending |

## Dependencies

**Cross-plan:** extends `260528-0912-cleanmatic-product-spec-skill` (status `completed` — skill v1.1.0 shipped). That dependency is already satisfied; no `blockedBy`/`blocks` link required.

**Internal phase order (sequential — later phases depend on earlier schema):**

```
P1 harness ─┬─> P2 risk ──> P3 time ──> P4 competition ──> P5 impact+migration ──> P6 ascii ──> P7 docs/release
            └─ (P1 produces goal.md + Workflow orchestrator that drive P2–P7)
```

- **P3 hard prerequisite (T1):** `dep_cycle` detection + cycle-safe renderers MUST land before the `depends_on` edge is parsed into the graph.
- **P4 depends on P3** schema plumbing (frontmatter parser extension for ID-keyed maps).
- **P5 impact-engine** consumes the multi-dim fields from P2–P4; **migration** runs after schema is final.
- **P6 (ASCII downgrade)** is the only near-breaking change — placed late; ASCII retained as text-summary (not deleted), so risk is LOW.
- **P7** bumps `2.0.0` + migrates `examples/acme-shop` once everything is green.

## Validation Log

### Session 1 — 2026-05-30
**Trigger:** `/ck:plan validate` after `--hard` red-team (RT1 content + RT2 orchestrator; 23 findings applied)
**Questions asked:** 4

#### Verification Results
- Claims checked: 12 | **Verified: 12 | Failed: 0** | Unverified: 0 | Tier: Full (7 phases)
- Key verified vs live code: `spec_graph` {`_node_from_artifact:82`, `_risks:214`, `_closure:226`, `downstream:251`}; bug #3 (`epic.md` has `risks:`, `prd.md`=0); `brd.md:53` Market Context; `visualize VIEWS:39`; `check_consistency` `invalid_type:110` + `_self_reference:193` + `PERSONA_SOFT_CAP`; `check_traceability` owns `dangling_link`; `change-log-entry.md` has `affected_set`, no `dims`; `examples/acme-shop` + `eval/evals.json` + references present.
- Failures: none.

#### Questions & Answers
1. **[Scope]** `depends_on` scope → **PRD + Epic** (Story/Goal excluded via type-guard → `invalid_type`).
2. **[Assumptions]** `time_realism` thresholds → **size=L AND ≥6 stories AND <21 days** (R2 defaults; module consts, commented).
3. **[Scope]** impact-pass on `--validate` → **Snapshot-delta** (reuse `.snapshots/`; first-run no-baseline → skip).
4. **[Tradeoffs]** cook execution model → **Full-auto P1→P7 + waves** (orchestrator as-built; abort-guard + ship-block protect non-convergence).

#### Confirmed Decisions
- All 4 confirm the current plan design (Q1–Q3 chose the plan default; Q4 chose full-auto = orchestrator as-built). No phase-gated variant added.

#### Impact on Phases
- **None.** No propagation needed — the plan already encodes all four decisions.

#### Whole-Plan Consistency Sweep
- Ran during red-team integration + re-grep: `invalid_shape`→`invalid_type` (clean), `risk_blindspot`→script (clean), `<1s` SLA removed, gate coverage `goal.md` ≡ orchestrator (**31/31**, no orphan/dangling). Validation decisions introduce no new terms → no new contradictions. **CLEAN.**

#### Recommendation
**PROCEED.** Verification `Failed: 0` → eligible for implementation. Cook via the Workflow orchestrator (full-auto, per Q4).
