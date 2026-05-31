---
id: PRD-CHECKOUT-E3
type: epic
prd: PRD-CHECKOUT
brd_goals: [BRD-G2]
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2024-08-01
updated: 2024-09-25
personas: [shopper]
scope: in
moscow: should
horizon: now
target_date: 2024-09-30
depends_on: [PRD-CHECKOUT-E2]
risks:
  - description: "Carrier tracking webhooks are unreliable, so status can lag the real shipment."
    impact: low
    likelihood: med
    status: accepted
    mitigation: "Show last-known status with a timestamp; link out to the carrier."
---

# Order Tracking Epic

## Goal

A shopper can see the status of a placed order, from placed through delivered.

## Business Context

- PRD requirement: order-status tracking page reachable from the confirmation email.
- BRD goal: BRD-G2 (a smooth post-purchase experience drives the repeat purchase).
- Depends on PRD-CHECKOUT-E2 (an order must be created and confirmed before it can be tracked).

## Success Criteria

Order-status page reachable for 100% of placed orders; carrier status reflected within 5 minutes of a tracking update.
_Shipped Sep 2024 alongside the launch._

## Scope

Order-status tracking page (placed → fulfilled → shipped → delivered), carrier-webhook ingestion, link from the
confirmation email. Returns/refunds are out of scope for this epic.

## Risks

- **Carrier webhook unreliability** (impact: low, likelihood: med — accepted) — status can lag the real shipment.
  Accepted: show last-known status with a timestamp and link out to the carrier.
