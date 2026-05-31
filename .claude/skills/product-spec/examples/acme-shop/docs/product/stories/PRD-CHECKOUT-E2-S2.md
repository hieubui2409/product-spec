---
id: PRD-CHECKOUT-E2-S2
type: story
epic: PRD-CHECKOUT-E2
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2024-08-15
updated: 2024-09-10
personas: [shopper]
scope: in
moscow: must
size: S
horizon: now
metrics: [checkout-completion-rate]
acceptance_criteria:
  - "Given a successful payment, when Stripe confirms the charge, then an order-confirmation email with the receipt and tracking link is sent within 1 minute."
  - "Given a confirmation email that fails to send, when the failure is detected, then it is retried and the order still appears in the shopper's account."
---

# Order confirmation email — Story PRD-CHECKOUT-E2-S2

## User Story

**As a** shopper, **I want** an email confirming my order with a receipt and tracking link, **so that** I have a record
of the purchase and a way to follow it.

## Acceptance Criteria

- Given a successful payment, when Stripe confirms the charge, then an order-confirmation email with the receipt and tracking link is sent within 1 minute.
- Given a confirmation email that fails to send, when the failure is detected, then it is retried and the order still appears in the shopper's account.
