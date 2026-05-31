---
id: PRD-MOBILE-E1
type: epic
prd: PRD-MOBILE
brd_goals: [BRD-G5]
status: draft
lang: en
owner: Devon Park
version: 0.1.0
created: 2026-04-05
updated: 2026-05-05
personas: [shopper]
scope: in
moscow: could
horizon: later
target_date: 2027-02-28
risks:
  - description: "App-store review cycles slow native iteration."
    impact: med
    likelihood: med
    status: open
    mitigation: "Thin native shell over web checkout; batch native changes."
---

# Mobile App Shell Epic

## Goal

A shopper can browse and buy from a followed brand in a native app shell.

## Business Context

- PRD requirement: native app shell with native browse + embedded web checkout.
- BRD goal: BRD-G5 (native mobile shopping; the channel where most shoppers already are).

## Success Criteria

App cold-start under 3s; native browse at 60fps; checkout completes through the embedded web flow at parity with web.

## Scope

Native iOS/Android shell, native browse + product detail, embedded web checkout, and drop push notifications. A fully
native checkout reimplementation and mobile brand-admin are out.

## Risks

- **App-store review latency** (impact: med, likelihood: med — open) — slows iteration vs the web cadence. Mitigation:
  thin native shell over web checkout so most changes ship without a store release.
