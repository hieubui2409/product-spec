---
id: PRD-PAYOUTS-E1-S2
type: story
epic: PRD-PAYOUTS-E1
status: approved
lang: en
owner: Mara Lin
version: 1.0.0
created: 2024-10-01
updated: 2024-12-05
personas: [brand-owner]
scope: in
moscow: should
size: S
horizon: now
metrics: [payout-latency-days]
acceptance_criteria:
  - "Given a brand-owner viewing a completed payout period, when they request a statement, then a CSV with line items, fees, and net total downloads."
  - "Given a statement CSV, when the brand-owner opens it, then the net total matches the amount disbursed to their bank account."
---

# Payout statement export — Story PRD-PAYOUTS-E1-S2

## User Story

**As a** brand-owner, **I want** to download a statement for each payout period, **so that** I can reconcile Acme's
payouts against my own books.

## Acceptance Criteria

- Given a brand-owner viewing a completed payout period, when they request a statement, then a CSV with line items, fees, and net total downloads.
- Given a statement CSV, when the brand-owner opens it, then the net total matches the amount disbursed to their bank account.
