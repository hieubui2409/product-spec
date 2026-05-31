---
id: PRD-FANCRM-E2
type: epic
prd: PRD-FANCRM
brd_goals: [BRD-G2]
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2026-02-01
updated: 2026-05-15
personas: [brand-owner]
scope: in
moscow: should
horizon: next
target_date: 2026-08-31
depends_on: [PRD-FANCRM-E1]
risks:
  - description: "Segment definitions over purchase history get stale as data grows."
    impact: low
    likelihood: med
    status: open
    mitigation: "Recompute segments nightly from the rollup tables."
---

# Audience Segments Epic

## Goal

A brand-owner can build and save audience segments from purchase history and target broadcasts at them.

## Business Context

- PRD requirement: audience segments by purchase history (recency, frequency, lifetime spend).
- BRD goal: BRD-G2 (targeted messaging to the right fans drives repeat purchase harder than blasting everyone).
- Depends on PRD-FANCRM-E1 (broadcasts must exist before segment targeting is useful).

## Success Criteria

A segment's fan count is accurate at save time and stays fresh via nightly recompute; segments are reusable across
broadcasts.

## Scope

Segment builder over purchase history, saved/reusable segment definitions, nightly recompute. Predictive/ML
segmentation is out.

## Risks

- **Stale segments** (impact: low, likelihood: med — open) — definitions drift as purchase data grows. Mitigation
  planned: nightly recompute from the rollup tables.
