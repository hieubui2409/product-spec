---
id: PRD-PAYOUTS-E1-S1
type: story
epic: PRD-PAYOUTS-E1
status: approved
lang: en
owner: Mara Lin
version: 1.0.0
created: 2024-09-15
updated: 2024-12-01
personas: [ops-manager, brand-owner]
scope: in
moscow: must
size: L
horizon: now
metrics: [payout-latency-days, payout-error-rate]
acceptance_criteria:
  - "Given a brand with an available ledger balance, when the scheduled payout run executes, then the balance is reconciled and disbursed via Stripe Connect within the SLA."
  - "Given a reconciliation mismatch on a brand, when the payout run reaches that brand, then the payout is held and an ops alert is raised instead of disbursing."
---

# Scheduled payout run — Story PRD-PAYOUTS-E1-S1

## User Story

**As an** ops-manager, **I want** brand balances reconciled and paid out automatically on schedule, **so that** brands
get their money fast and correctly without manual work.

## Acceptance Criteria

- Given a brand with an available ledger balance, when the scheduled payout run executes, then the balance is reconciled and disbursed via Stripe Connect within the SLA.
- Given a reconciliation mismatch on a brand, when the payout run reaches that brand, then the payout is held and an ops alert is raised instead of disbursing.
