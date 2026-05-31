---
id: PRD-ANALYTICS
type: prd
brd_goals: [BRD-G3, BRD-G4]
status: draft
lang: en
owner: Devon Park
version: 0.1.0
created: 2026-02-10
updated: 2026-05-10
personas: [brand-owner, ops-manager]
scope: in
moscow: should
horizon: next
metrics: [dashboard-dau]
risks:
  - description: "Dashboard query load on the primary Postgres degrades storefront latency."
    impact: med
    likelihood: med
    status: open
    mitigation: "Serve analytics from read replicas + nightly rollup tables, never the primary."
competitive_parity:
  COMP-SHOPIFY: behind
target_date: 2026-10-31
depends_on: [PRD-PAYOUTS]
---

# Brand Analytics — PRD PRD-ANALYTICS

## Overview & Problem

Brands can sell, get paid, and message fans — but they cannot yet see how the business is doing in one place. Today a
brand-owner stitches together checkout receipts, payout statements, and gut feel. Analytics gives them a revenue
dashboard: revenue over time, top products, repeat-vs-new mix, and exportable reports. ops-manager gets the same lens
across brands to spot payout or GMV anomalies early. Planned for the back half of year 2 (status: draft).

## Personas

- **brand-owner** — wants to see revenue trends, best sellers, and repeat-customer mix at a glance.
- **ops-manager** — wants a cross-brand view to catch GMV dips and payout anomalies.

## Use Cases / Flows

1. brand-owner opens the dashboard and views revenue over a selectable date range.
2. brand-owner drills into top products and the repeat-vs-new buyer split.
3. brand-owner exports the period's report as CSV for their accountant.
4. ops-manager views the cross-brand roll-up to monitor BRD-G3 (GMV) and BRD-G4 (payout health).

## Functional Requirements (MoSCoW)

### Must

- Revenue-over-time chart with selectable date ranges.
- Top-products breakdown for the period.
- CSV export of the period's revenue report.

### Should

- Repeat-vs-new buyer mix (ties to the north-star repeat-rate).
- ops-manager cross-brand roll-up view.

### Could

- Cohort retention curves per acquisition month.
- Scheduled emailed weekly summary.

### Won't (this round)

- Real-time / streaming analytics (nightly rollups are sufficient).
- Custom report builder.

## Non-Functional Requirements

- All analytics queries served from read replicas + nightly rollup tables; never the storefront primary.
- Dashboard first paint under 2s for a typical brand's data volume.
- Numbers reconcile with payout statements (single source of truth: the ledger).

## Success Metrics → BRD Goals

- **dashboard-dau** → BRD-G3 (brands who watch revenue grow it) and BRD-G4 (ops catching payout anomalies fast).

## Dependencies & Risks

- Depends on PRD-PAYOUTS — analytics revenue figures derive from the payout ledger, the single source of truth.
- **Query load on primary** (impact: med, likelihood: med — open) — analytics traffic could degrade storefront
  latency. Mitigation planned: read replicas + nightly rollups, never the primary.

## Competitive Parity

- vs COMP-SHOPIFY — **behind**; Shopify's analytics suite is mature and deep. We aim for the few numbers a boutique
  brand actually acts on, not parity on breadth.
