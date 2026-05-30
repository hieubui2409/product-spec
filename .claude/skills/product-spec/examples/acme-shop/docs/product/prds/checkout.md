---
id: PRD-CHECKOUT
type: prd
brd_goals: [BRD-G1, BRD-G2]
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2026-05-28
updated: 2026-05-28
personas: [shopper]
scope: core-value
moscow: must
horizon: now
metrics: [checkout-completion-rate]
target_date: 2026-09-30
competitive_parity:
  COMP-SHOPIFY: behind
  COMP-BIGCARTEL: parity
risks:
  - description: "Stripe onboarding/KYC delays a brand's first payout, blocking launch."
    impact: high
    likelihood: med
    status: open
    mitigation: "Pre-collect KYC docs during brand onboarding, before checkout goes live."
  - description: "Cart abandonment if the single-page form feels long on mobile."
    impact: med
    likelihood: med
    status: open
    mitigation: "Inline validation + saved addresses for returning shoppers."
---

# Checkout PRD

## Overview & Problem

Shoppers can browse but cannot yet buy. Direct payment is the table-stakes feature for the launch — without it, the value prop ("sell directly") doesn't exist.

## Personas

- shopper

## Use Cases / Flows

1. Shopper adds items to cart.
2. Shopper opens checkout.
3. Shopper enters delivery address + payment.
4. Shopper confirms; gets a receipt + order tracking link.

## Functional Requirements (MoSCoW)

### Must

- Cart with add/remove/quantity controls.
- Single-page checkout form (address + payment).
- Payment via Stripe Checkout.
- Order confirmation email.

### Should

- Saved addresses for returning shoppers.

### Could

- Apple/Google Pay express checkout.

### Won't (this round)

- Multi-currency.

## Non-Functional Requirements

- Page load under 2s on 4G mobile.
- PCI compliance via Stripe (no card data on our servers).

## Success Metrics → BRD Goals

- checkout-completion-rate -> BRD-G1 (brands ship orders), BRD-G2 (repeat purchases).

## Timeline

Target ship: 2026-09-30 (Q3 launch deadline from the BRD). Sign-in lands first; Stripe payment follows.

## Risk Register

- **Stripe KYC delay** (impact: high, likelihood: med, open) — a brand's first payout can stall behind Stripe
  verification. Mitigation: pre-collect KYC during onboarding.
- **Mobile cart abandonment** (impact: med, likelihood: med, open) — a long single-page form hurts completion on 4G.
  Mitigation: inline validation + saved addresses.

## Competitive Parity

Parity is judged against the BRD competitors (identity lives in `brd.md`):

- vs COMP-SHOPIFY — **behind** on ecosystem breadth, but that is deliberate: we win on direct-to-fan economics, not
  feature count.
- vs COMP-BIGCARTEL — **parity** on storefront simplicity; we differentiate on fan loyalty, not checkout mechanics.
