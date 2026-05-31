---
id: PRD-CHECKOUT
type: prd
brd_goals: [BRD-G1, BRD-G2, BRD-G3]
status: approved
lang: en
owner: Jane Doe
version: 1.2.0
created: 2024-06-10
updated: 2025-03-12
personas: [shopper]
scope: core-value
moscow: must
horizon: now
metrics: [checkout-completion-rate]
risks:
  - description: "Stripe onboarding/KYC delays a brand's first payout, blocking launch."
    impact: high
    likelihood: med
    status: mitigated
    mitigation: "Pre-collect KYC docs during brand onboarding, before checkout goes live."
  - description: "Cart abandonment if the single-page form feels long on mobile."
    impact: med
    likelihood: med
    status: accepted
    mitigation: "Inline validation + saved addresses for returning shoppers."
competitive_parity:
  COMP-SHOPIFY: behind
  COMP-BIGCARTEL: parity
  COMP-ETSY: behind
target_date: 2024-09-30
---

# Checkout — PRD PRD-CHECKOUT

## Overview & Problem

At launch, shoppers could browse a brand's catalog but could not buy. Direct payment is the table-stakes feature of
the whole product — without it, the value proposition ("sell directly to your fans") does not exist. Checkout was the
first thing we shipped (Q3 2024) and remains core-value: every dollar of GMV and every repeat purchase flows through
it. It is now live across all 120+ brands and runs at ~78% completion, ahead of the 75% target.

## Personas

- **shopper** — a returning fan completing a purchase, usually on mobile, often signed out between drops.

## Use Cases / Flows

1. Shopper adds one or more items to the cart from a brand's storefront.
2. Shopper opens checkout; if signed out, signs in via a magic link (no password).
3. Shopper enters or selects a saved delivery address and pays via Stripe Checkout.
4. Shopper confirms; receives a confirmation email and an order-tracking link.
5. Shopper can return later to track order status from the link.

## Functional Requirements (MoSCoW)

### Must

- Cart with add / remove / quantity controls, persisted across the sign-in hop.
- Magic-link sign-in at checkout (passwordless).
- Single-page checkout form: delivery address + payment.
- Payment via Stripe Checkout (Stripe holds all card data).
- Order confirmation email with receipt + tracking link.

### Should

- Saved addresses for returning shoppers, pre-filled on the next purchase.
- Order-status tracking page (placed → fulfilled → shipped → delivered).

### Could

- Apple Pay / Google Pay express checkout.

### Won't (this round)

- Multi-currency checkout (single settlement currency per brand for now).
- Split payments / installments.

## Non-Functional Requirements

- Checkout page interactive under 2s on a 4G mobile connection.
- PCI compliance fully delegated to Stripe; no card data touches Acme servers.
- Cart and address state survive a magic-link round-trip without data loss.
- 99.9% checkout availability; payment failures degrade gracefully with a retry.

## Success Metrics → BRD Goals

- **checkout-completion-rate** → BRD-G1 (brands ship orders so we keep onboarding), BRD-G2 (repeat purchases compound),
  BRD-G3 (completed checkouts are the GMV). Current: ~78% vs 75% target.

## Scope In / Out

**In scope:** sign-in, address, payment, confirmation, order tracking for the web storefront.

**Out of scope:** mobile-native checkout (see PRD-MOBILE), multi-currency, subscriptions.

## Dependencies & Risks

- **Stripe KYC delay** (impact: high, likelihood: med — mitigated) — a brand's first payout could stall behind Stripe
  verification, blocking go-live. Mitigation shipped: KYC is pre-collected during onboarding.
- **Mobile cart abandonment** (impact: med, likelihood: med — accepted) — a long single-page form hurts completion on
  4G. Accepted with inline validation + saved addresses; revisit if completion dips below target.

## Competitive Parity

Parity is judged against the BRD competitors (identity lives in `brd.md`):

- vs COMP-SHOPIFY — **behind** on ecosystem breadth (apps, themes); deliberate — we win on direct-to-fan economics.
- vs COMP-BIGCARTEL — **parity** on storefront-checkout simplicity.
- vs COMP-ETSY — **behind** on marketplace discovery, by design (we are not a marketplace).
