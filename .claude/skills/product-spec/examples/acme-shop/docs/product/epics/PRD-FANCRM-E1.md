---
id: PRD-FANCRM-E1
type: epic
prd: PRD-FANCRM
brd_goals: [BRD-G2]
status: review
lang: en
owner: Jane Doe
version: 0.3.0
created: 2025-11-10
updated: 2026-05-15
personas: [brand-owner, shopper]
scope: in
moscow: should
horizon: next
target_date: 2026-07-15
risks:
  - description: "Broadcasts flagged as spam destroy deliverability and the feature's value."
    impact: high
    likelihood: med
    status: open
    mitigation: "Authenticated sending domains, double opt-in, one-click unsubscribe."
---

# Fan Messaging Epic

## Goal

A brand-owner can broadcast to fans and reply to them from a unified inbox.

## Business Context

- PRD requirement: broadcast composer (send to segment/all) + reply inbox.
- BRD goal: BRD-G2 (fan engagement is the leading indicator of the repeat-purchase rate).

## Success Criteria

Broadcast open rate at or above 40%; replies threaded reliably per fan; deliverability protected by authenticated
domains. _In beta with design-partner brands; ~38% open rate so far._

## Scope

Broadcast composer with segment/all targeting, deliverability hardening (authenticated domains, double opt-in,
unsubscribe), open/click instrumentation, and the reply inbox. SMS and lifecycle automation are out of this epic.

## Risks

- **Spam / deliverability** (impact: high, likelihood: med — open) — the make-or-break risk; broadcasts in spam make
  the feature worthless. Mitigation in progress: authenticated sending domains, double opt-in, one-click unsubscribe.
