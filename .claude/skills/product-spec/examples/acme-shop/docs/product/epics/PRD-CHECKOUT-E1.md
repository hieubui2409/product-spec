---
id: PRD-CHECKOUT-E1
type: epic
prd: PRD-CHECKOUT
brd_goals: [BRD-G1]
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2024-06-15
updated: 2024-09-20
personas: [shopper]
scope: in
moscow: must
horizon: now
target_date: 2024-08-15
risks:
  - description: "Magic-link emails land in spam, blocking sign-in at checkout."
    impact: med
    likelihood: med
    status: mitigated
    mitigation: "Use an authenticated sending domain (SPF/DKIM) + a fallback resend."
---

# Sign-In + Address Epic

## Goal

Shoppers can sign in and enter a delivery address, ready to pay.

## Business Context

- PRD requirement: Magic-link sign-in + single-page address entry.
- BRD goal: BRD-G1 (brands ship orders so we onboard more).

## Success Criteria

Sign-in success rate above 90%; address-step completion above 80%. _Shipped Aug 2024; both criteria met in production._

## Scope

Sign-in (email magic link), address entry, and saved addresses for returning shoppers. Payment + confirmation are the
follow-on Stripe Payment epic (PRD-CHECKOUT-E2).

## Risks

- **Magic-link spam** (impact: med, likelihood: med — mitigated) — sign-in emails caught by spam filters. Mitigation
  shipped: authenticated sending domain (SPF/DKIM) + resend fallback.
