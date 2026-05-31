---
id: PRD-CHECKOUT-E2
type: epic
prd: PRD-CHECKOUT
brd_goals: [BRD-G1]
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2024-07-01
updated: 2024-09-25
personas: [shopper]
scope: in
moscow: must
horizon: now
target_date: 2024-09-15
depends_on: [PRD-CHECKOUT-E1]
risks:
  - description: "Stripe webhook delivery is delayed, so the confirmation email lags the payment."
    impact: med
    likelihood: low
    status: mitigated
    mitigation: "Poll the PaymentIntent on the return URL as a fallback to the webhook."
---

# Stripe Payment Epic

## Goal

A signed-in shopper can pay with Stripe and receive an order confirmation.

## Business Context

- PRD requirement: Payment via Stripe Checkout + order confirmation email.
- BRD goal: BRD-G1 (brands ship orders so we onboard more).
- Depends on PRD-CHECKOUT-E1 (sign-in + address must exist before payment).

## Success Criteria

Payment success rate above 95%; confirmation email delivered within 1 minute of payment. _Shipped Sep 2024; running
above target._

## Scope

Stripe Checkout payment widget, payment confirmation, order confirmation email.

## Risks

- **Webhook delay** (impact: med, likelihood: low — mitigated) — Stripe webhook lags the redirect. Mitigation shipped:
  poll the PaymentIntent on the return URL.
