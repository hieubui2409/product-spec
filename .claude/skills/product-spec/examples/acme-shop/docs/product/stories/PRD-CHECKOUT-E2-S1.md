---
id: PRD-CHECKOUT-E2-S1
type: story
epic: PRD-CHECKOUT-E2
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2026-05-28
updated: 2026-05-28
personas: [shopper]
scope: in
moscow: must
size: M
horizon: now
acceptance_criteria:
  - "Given a signed-in shopper with items in the cart, when they submit valid card details via Stripe Checkout, then the payment is authorized and an order is created."
  - "Given a successful payment, when Stripe confirms the charge, then a confirmation email with the order summary is sent within 1 minute."
---

# Pay with Stripe at checkout

## User Story

**As a** shopper, **I want** to pay with my card via Stripe at checkout, **so that** I can complete my order and receive a confirmation.

## Acceptance Criteria

- Given a signed-in shopper with items in the cart, when they submit valid card details via Stripe Checkout, then the payment is authorized and an order is created.
- Given a successful payment, when Stripe confirms the charge, then a confirmation email with the order summary is sent within 1 minute.
