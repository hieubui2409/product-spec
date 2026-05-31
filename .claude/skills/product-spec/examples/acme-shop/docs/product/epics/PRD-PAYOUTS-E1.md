---
id: PRD-PAYOUTS-E1
type: epic
prd: PRD-PAYOUTS
brd_goals: [BRD-G4]
status: approved
lang: en
owner: Mara Lin
version: 1.0.0
created: 2024-09-10
updated: 2024-12-12
personas: [brand-owner, ops-manager]
scope: in
moscow: must
horizon: now
target_date: 2024-11-30
risks:
  - description: "A retried payout run double-pays a brand."
    impact: high
    likelihood: low
    status: mitigated
    mitigation: "Idempotency keys per run; ledger guard rejects duplicate disbursement."
---

# Automated Payouts Epic

## Goal

A scheduled run reconciles each brand's balance and disburses it via Stripe Connect, with a downloadable statement.

## Business Context

- PRD requirement: scheduled payout run with reconciliation + payout-statement export.
- BRD goal: BRD-G4 (sub-3-day payout latency — the goal this epic exists to hit).

## Success Criteria

Average payout latency under 3 days; payout-error-rate near zero; every disbursement traceable to its ledger entries.
_Shipped Nov 2024; running ~1.8 days._

## Scope

Per-brand ledger, scheduled run, double-entry reconciliation with hold-on-mismatch, Stripe Connect disbursement, and
CSV statement export. Multi-currency settlement and instant payouts are out.

## Risks

- **Double-pay on retry** (impact: high, likelihood: low — mitigated) — a retried run paying twice. Mitigation shipped:
  idempotency keys per run + a ledger guard rejecting duplicate disbursement.
