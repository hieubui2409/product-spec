---
id: PRD-CHECKOUT-E3-S1
type: story
epic: PRD-CHECKOUT-E3
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2024-08-05
updated: 2024-09-20
personas: [shopper]
scope: in
moscow: should
size: M
horizon: now
metrics: [checkout-completion-rate]
acceptance_criteria:
  - "Given a shopper with a placed order, when they open the tracking link, then they see the current order status (placed, fulfilled, shipped, delivered)."
  - "Given a carrier tracking update, when it is received, then the order status and last-updated timestamp reflect it within 5 minutes."
---

# Track order status — Story PRD-CHECKOUT-E3-S1

## User Story

**As a** shopper, **I want** to see where my order is after I buy, **so that** I know when to expect it without
emailing the brand.

## Acceptance Criteria

- Given a shopper with a placed order, when they open the tracking link, then they see the current order status (placed, fulfilled, shipped, delivered).
- Given a carrier tracking update, when it is received, then the order status and last-updated timestamp reflect it within 5 minutes.
