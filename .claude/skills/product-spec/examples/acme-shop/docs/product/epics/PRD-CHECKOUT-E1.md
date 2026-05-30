---
id: PRD-CHECKOUT-E1
type: epic
prd: PRD-CHECKOUT
brd_goals: [BRD-G1]
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2026-05-28
updated: 2026-05-28
personas: [shopper]
scope: in
moscow: must
horizon: now
target_date: 2026-08-15
risks:
  - description: "Magic-link emails land in spam, blocking sign-in at checkout."
    impact: med
    likelihood: med
    status: open
    mitigation: "Use an authenticated sending domain (SPF/DKIM) + a fallback resend."
---

# Sign-In + Address Epic

## Goal

Shoppers can sign in and enter a delivery address, ready to pay.

## Business Context

- PRD requirement: Magic-link sign-in + single-page address entry.
- BRD goal: BRD-G1 (brands ship orders so we onboard more).

## Success Criteria

Sign-in success rate above 90%; address step completion above 80%.

## Scope

Sign-in (email magic link), address entry. Payment + confirmation are the follow-on Stripe Payment epic
(PRD-CHECKOUT-E2).

## Risks

- **Magic-link spam** (impact: med, likelihood: med, open) — sign-in emails caught by spam filters. Mitigation:
  authenticated sending domain + resend fallback.
