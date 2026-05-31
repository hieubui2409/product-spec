---
id: PRD-ANALYTICS-E1
type: epic
prd: PRD-ANALYTICS
brd_goals: [BRD-G3, BRD-G4]
status: draft
lang: en
owner: Devon Park
version: 0.1.0
created: 2026-02-15
updated: 2026-05-08
personas: [brand-owner, ops-manager]
scope: in
moscow: should
horizon: next
target_date: 2026-10-15
risks:
  - description: "Heavy dashboard queries on the primary degrade storefront latency."
    impact: med
    likelihood: med
    status: open
    mitigation: "Serve from read replicas + nightly rollup tables."
---

# Revenue Dashboard Epic

## Goal

A brand-owner can see revenue over time and export a period report; ops gets a cross-brand roll-up.

## Business Context

- PRD requirement: revenue-over-time chart + CSV report export.
- BRD goal: BRD-G3 (brands who watch revenue grow it) and BRD-G4 (ops catching payout/GMV anomalies early).

## Success Criteria

Dashboard numbers reconcile with payout statements; first paint under 2s; export matches on-screen totals.

## Scope

Revenue-over-time chart with date ranges, top-products breakdown, CSV export, and the ops cross-brand roll-up. Cohort
retention and a custom report builder are out.

## Risks

- **Query load on primary** (impact: med, likelihood: med — open) — analytics traffic degrading storefront latency.
  Mitigation planned: serve from read replicas + nightly rollup tables, never the primary.
