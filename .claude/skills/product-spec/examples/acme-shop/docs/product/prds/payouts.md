---
id: PRD-PAYOUTS
type: prd
brd_goals: [BRD-G4]
status: approved
lang: en
owner: Mara Lin
version: 1.0.0
created: 2024-09-01
updated: 2025-01-15
personas: [brand-owner, ops-manager]
scope: in
moscow: must
horizon: now
metrics: [payout-latency-days, payout-error-rate]
risks:
  - description: "A reconciliation mismatch sends an incorrect payout amount to a brand."
    impact: high
    likelihood: low
    status: mitigated
    mitigation: "Double-entry ledger reconciliation before each payout run; held payouts on mismatch."
  - description: "Stripe Connect payout schedule changes shift latency past the 3-day SLA."
    impact: low
    likelihood: low
    status: accepted
    mitigation: "Monitor Stripe payout webhooks; alert ops if latency trends up."
competitive_parity:
  COMP-SHOPIFY: parity
target_date: 2024-12-15
---

# Brand Payouts — PRD PRD-PAYOUTS

## Overview & Problem

Selling is only half the promise; the brand has to get paid, quickly and correctly. Payouts is the money-movement
spine: it takes captured order revenue, nets Acme's fee, reconciles against the ledger, and pays the brand on a
predictable schedule via Stripe Connect. Shipped Dec 2024. It directly owns BRD-G4 (sub-3-day latency) and is running
at ~1.8 days average latency with a payout-error-rate near zero.

## Personas

- **brand-owner** — wants money in the bank fast and a statement they can reconcile against their own books.
- **ops-manager** — runs and monitors payout operations; investigates any held or mismatched payout.

## Use Cases / Flows

1. Orders are captured through checkout; revenue accrues to the brand's ledger balance (net of fees).
2. A scheduled payout run aggregates the brand's available balance.
3. The run reconciles the ledger against captured payments; any mismatch holds the payout for ops review.
4. Reconciled payouts are disbursed via Stripe Connect to the brand's bank account.
5. brand-owner downloads a payout statement (line items, fees, net) for their records.

## Functional Requirements (MoSCoW)

### Must

- Per-brand ledger accruing net revenue per captured order.
- Scheduled automated payout run (configurable cadence per brand).
- Double-entry reconciliation before disbursement; hold-on-mismatch.
- Disbursement via Stripe Connect.
- Downloadable payout statement (CSV) per period.

### Should

- ops-manager dashboard of pending / held / disbursed payouts.

### Could

- On-demand (instant) payout for an extra fee.

### Won't (this round)

- Multi-currency settlement (single settlement currency per brand).
- Brand-configurable fee tiers.

## Non-Functional Requirements

- Average payout latency under 3 days (BRD-G4); target the run completes within hours of schedule.
- Payout runs are idempotent — a retried run never double-pays.
- Every disbursement is traceable to its ledger entries (audit trail).

## Success Metrics → BRD Goals

- **payout-latency-days** → BRD-G4 (the goal, directly).
- **payout-error-rate** → BRD-G4 (a correct payout is part of "under 3 days" being meaningful).

## Dependencies & Risks

- **Reconciliation mismatch** (impact: high, likelihood: low — mitigated) — an incorrect amount reaching a brand.
  Mitigation shipped: double-entry reconciliation + hold-on-mismatch.
- **Stripe schedule drift** (impact: low, likelihood: low — accepted) — Stripe payout timing shifting latency.
  Accepted; monitored via payout webhooks with an ops alert.

## Competitive Parity

- vs COMP-SHOPIFY — **parity** on payout reliability and cadence; we match the incumbent on money movement and
  differentiate elsewhere (the fan relationship).
