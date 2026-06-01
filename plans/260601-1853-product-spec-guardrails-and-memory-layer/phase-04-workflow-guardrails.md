---
phase: 4
title: "workflow-guardrails"
status: pending
priority: P2
effort: "5h"
dependencies: [2]
---

# Phase 4: workflow-guardrails

## Overview
Per-workflow guardrails inside the split reference files: whole-tree consistency-sweep gate, extend no-silent-reversal to confirmed-but-draft PO answers, Validation Log schema, **Scope Challenge always-on per PRD**, scout-first-ask-second, and an engineering-jargon→product-term reframe. Prose phase; structural verification. Depends on P2 (operates on the post-split files).

## Requirements
- Functional:
  - **Consistency-sweep gate** (in `workflow-update.md`): after an `--update`/edit, re-scan the whole tree for stale cross-references; block "done" until zero unresolved contradictions.
  - **No-silent-reversal extended** (in `workflow-update.md` + `workflow-auto.md`): protect ANY PO-confirmed answer recorded in `.session.md` (scope/persona/threshold), not just `approved` artifacts — surface (verbatim original + reason + trade-off + keep/change/hybrid) before regenerating.
  - **Validation Log schema** (in `workflow-validate.md`? NO — that file is P1/P2/P5/P6 hub) → place the schema in `validation-rules-spec.md` is P2's... → **place in `workflow-update.md`/`.session.md` format note**; record verbatim question + all options + verbatim "Other" + rationale + session#.
  - **Scope Challenge always-on** (in `workflow-interview.md`): before decomposing every PRD, ask MVP/Full/Strip + complexity-smell, then LOCK; later out-of-mode additions are surfaced not silently added. **(red-team RT-13 — no double-ask)** Division of labor vs the existing mandatory MoSCoW gate: Scope Challenge sets the COARSE intent lock (MVP/Full/Strip) ONCE pre-decomposition; the MoSCoW gate then OPERATIONALIZES it per-requirement and must stay CONSISTENT with the locked intent (flag if the MUST-set exceeds the locked MVP). Do NOT re-ask "what's the MVP" — MoSCoW derives the detail; Scope Challenge owns the boundary.
  - **scout-first-ask-second** (in `workflow-interview.md`): resolve from existing artifacts (cite by ID) before interrupting the PO; ask only when spec is silent / two approved conflict / business-judgment.
  - **eng-jargon→product reframe** (in `interview-frameworks.md`): a reframe pattern beside 5-Why for when the PO slips into engineering framing (DB schema / story points).
- Non-functional: PO-facing; reuse existing mechanisms (snapshot delta for the sweep, `.session.md` for confirmed answers).

## Architecture
- Consistency-sweep reuses snapshot delta + `downstream()` to enumerate cross-refs; the gate is an LLM step ("re-read all, reconcile, block on contradiction").
- Validation Log = an append section schema (mirrors ck `validate-question-framework.md:64-67`); home in `.session.md` schema note (`frontmatter-and-id-spec.md` Session Schema is P2-owned → coordinate: P4 references it, the schema text lives in `workflow-interview.md` Closing-the-Loop or a small addition; avoid editing P2-owned `frontmatter-and-id-spec.md`). **Decision: Validation Log schema documented in `workflow-interview.md` + `workflow-update.md`; the `.session.md` Session Schema field list addition (if needed) is deferred to P2 ownership note.**

## Related Code Files
- Modify: `references/workflow-update.md`, `references/workflow-auto.md`, `references/workflow-interview.md`, `references/interview-frameworks.md` (all P2-created/owned-by-P4 here)
- Read for context: `references/validation-rules-spec.md` (gold_plating — Scope Challenge complements it), `scripts/spec_graph.py` (downstream/diff for sweep)

## Verification (structural — no pytest)
1. `workflow-interview.md` contains a Scope-Challenge step BEFORE PRD decomposition + a scout-first-ask-second rule; grep proves presence.
2. `workflow-update.md` contains the consistency-sweep gate + extended no-silent-reversal (covers `.session.md` confirmed answers).
3. `interview-frameworks.md` has the eng-jargon reframe section.
4. No broken cross-ref to the now-split filenames (grep clean).
5. Manual read: PO-vocabulary, Scope-Challenge wording fits non-technical PO.

## Implementation Steps
1. Add Scope-Challenge (always-on) + scout-first-ask-second to `workflow-interview.md`.
2. Add consistency-sweep gate + extended no-silent-reversal to `workflow-update.md`; mirror the no-silent-reversal note in `workflow-auto.md`.
3. Add Validation Log schema to `workflow-interview.md`/`workflow-update.md`.
4. Add eng-jargon→product reframe to `interview-frameworks.md`.
5. Run structural checks #1–#4 + manual read #5.

## Success Criteria
- [ ] Scope Challenge always-on per PRD + LOCK behavior documented.
- [ ] Consistency-sweep gate blocks on unresolved cross-artifact contradictions.
- [ ] No-silent-reversal extended to confirmed-draft `.session.md` answers.
- [ ] Validation Log schema + scout-first-ask-second + eng-jargon reframe present.
- [ ] Zero broken cross-refs.

## Risk Assessment
- Scope Challenge friction for small PRDs → locked decision is always-on; mitigate wording (terse, skippable-by-explicit-PO per override-surface-risk).
- Hub coordination: P4 must NOT edit P2-owned `frontmatter-and-id-spec.md`/`SKILL.md`/`validation-rules-spec.md` — keep Validation Log schema in P4-owned workflow files.
- Parallel-safe with P3 (distinct files).
