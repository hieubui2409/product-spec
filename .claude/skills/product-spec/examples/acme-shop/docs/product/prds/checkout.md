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
