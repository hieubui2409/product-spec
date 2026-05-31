---
id: PRD-MOBILE
type: prd
brd_goals: [BRD-G5]
status: draft
lang: en
owner: Devon Park
version: 0.1.0
created: 2026-04-01
updated: 2026-05-05
personas: [shopper]
scope: in
moscow: could
horizon: later
metrics: [mobile-mau]
risks:
  - description: "App-store review cycles slow iteration versus the web release cadence."
    impact: med
    likelihood: med
    status: open
    mitigation: "Ship a thin native shell over the web checkout; reserve native screens for browse/buy."
  - description: "Maintaining a second client doubles the surface for a small team."
    impact: low
    likelihood: med
    status: open
    mitigation: "Reuse the web design system + API; defer native-only features."
competitive_parity:
  COMP-SHOPIFY: behind
  COMP-ETSY: behind
target_date: 2027-03-31
---

# Native Mobile Shopping — PRD PRD-MOBILE

## Overview & Problem

Shoppers already buy mostly on mobile, but through the mobile web. A native app would let fans browse and buy faster,
get push notifications for drops (which compounds the fan-CRM bet), and keep Acme on the home screen. This is BRD-G5,
which slipped from its original year-2 target into a later horizon — a deliberate sequencing call to ship fan-CRM and
analytics first. Status: draft; scoped as a thin native shell over the proven web checkout to keep a small team's
maintenance surface low.

## Personas

- **shopper** — a returning fan who wants a faster, home-screen path to browse and buy, with drop notifications.

## Use Cases / Flows

1. shopper installs the app and signs in (magic link, same as web).
2. shopper browses a followed brand's catalog in native screens.
3. shopper buys through the embedded, proven web checkout flow.
4. shopper receives a push notification when a followed brand drops or restocks.

## Functional Requirements (MoSCoW)

### Must

- Native app shell (iOS + Android) wrapping the storefront.
- Native browse + product detail for followed brands.
- Buy via the existing web checkout embedded in the shell.

### Should

- Push notifications for drops and restocks (ties to fan-CRM).

### Could

- Native payment sheets (Apple Pay / Google Pay) in the shell.
- Offline browse of cached catalog.

### Won't (this round)

- A fully native checkout reimplementation (reuse web; revisit only if metrics justify).
- Brand-admin tooling on mobile (admin stays web).

## Non-Functional Requirements

- Reuse the web API and design system; no parallel backend.
- App cold-start under 3s; browse screens scroll at 60fps on mid-range devices.
- Release cadence accommodates app-store review (batch native changes).

## Success Metrics → BRD Goals

- **mobile-mau** → BRD-G5 (the goal, directly — monthly active mobile shoppers).

## Scope In / Out

**In scope:** native shell, native browse, embedded web checkout, drop push.

**Out of scope:** native checkout reimplementation, brand-admin on mobile.

## Dependencies & Risks

- **App-store review latency** (impact: med, likelihood: med — open) — slows iteration. Mitigation: thin shell over
  web so most changes ship without a store release.
- **Second-client maintenance** (impact: low, likelihood: med — open) — doubles surface for a small team. Mitigation:
  reuse API + design system, defer native-only features.

## Competitive Parity

- vs COMP-SHOPIFY — **behind**; Shopify offers a polished Shop app. We trail on native maturity for now.
- vs COMP-ETSY — **behind**; Etsy's app is a core channel. Catching up here is the point of BRD-G5.
