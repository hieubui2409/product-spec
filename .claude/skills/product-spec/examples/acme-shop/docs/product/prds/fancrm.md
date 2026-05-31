---
id: PRD-FANCRM
type: prd
brd_goals: [BRD-G2]
status: review
lang: en
owner: Jane Doe
version: 0.6.0
created: 2025-11-04
updated: 2026-05-18
personas: [brand-owner, shopper]
scope: core-value
moscow: should
horizon: next
metrics: [fan-message-open-rate, repeat-rate-90d]
risks:
  - description: "Broadcast messaging is treated as spam by mailbox providers, tanking deliverability."
    impact: high
    likelihood: med
    status: open
    mitigation: "Per-brand authenticated sending domains, double opt-in, one-click unsubscribe."
  - description: "Low broadcast open rates would undercut the repeat-purchase thesis."
    impact: med
    likelihood: med
    status: open
    mitigation: "Beta with design-partner brands; instrument open/reply rate before GA."
competitive_parity:
  COMP-SUBSTACK: parity
  COMP-SHOPIFY: ahead
  COMP-BIGCARTEL: ahead
target_date: 2026-08-31
---

# Fan-CRM — PRD PRD-FANCRM

## Overview & Problem

This is the differentiator — the reason a brand chooses Acme over a generic storefront. The core storefront proved the
economics; fan-CRM proves the thesis that owning the fan relationship drives repeat purchase (BRD-G2). It gives a
brand-owner a direct line to the fans who bought from them: broadcast a drop, reply to a fan, and segment the audience
by purchase history. Currently in beta with design-partner brands (status: review). Early signal: ~38% broadcast open
rate against a 40% target, and beta brands show a measurable lift in 90-day repeat rate.

## Personas

- **brand-owner** — composes and sends broadcasts, replies to fans, builds audience segments.
- **shopper** — receives a broadcast, opens it, replies, and (the goal) comes back to buy.

## Use Cases / Flows

1. brand-owner composes a broadcast (new drop, restock, behind-the-scenes) and sends to a segment or the whole list.
2. shopper receives the message, opens it, and follows the link back to the storefront.
3. shopper replies; the reply lands in the brand's inbox.
4. brand-owner replies from a unified inbox.
5. brand-owner builds a segment (e.g. "bought in the last 90 days", "spent > $200") and targets a broadcast at it.

## Functional Requirements (MoSCoW)

### Must

- Broadcast composer with send-to-segment or send-to-all.
- Per-brand authenticated sending domain, double opt-in, one-click unsubscribe.
- Reply inbox: incoming fan replies threaded per shopper.
- Open / click instrumentation per broadcast.

### Should

- Audience segments by purchase history (recency, frequency, lifetime spend).
- Saved segment definitions reusable across broadcasts.

### Could

- Automated lifecycle messages (post-purchase thank-you, win-back).
- SMS channel in addition to email.

### Won't (this round)

- Cross-brand messaging or shared audiences (that would break the "fan list belongs to the brand" principle).
- Paid ad audiences / lookalikes.

## Non-Functional Requirements

- Broadcast send fans out without blocking the composer UI; large lists send asynchronously.
- Deliverability protected: authenticated domains, suppression of unsubscribed/bounced addresses.
- A fan can unsubscribe in one click; suppression honored on the next send.

## Success Metrics → BRD Goals

- **fan-message-open-rate** → BRD-G2 (engaged fans are the leading indicator of repeat purchase).
- **repeat-rate-90d** → BRD-G2 (the goal, directly — the whole point of the fan relationship).

## Scope In / Out

**In scope:** per-brand broadcast messaging, reply inbox, purchase-history segments.

**Out of scope:** cross-brand audiences, paid acquisition, a full marketing-automation suite.

## Dependencies & Risks

- **Deliverability / spam** (impact: high, likelihood: med — open) — the single biggest threat; if broadcasts land in
  spam, the feature is worthless. Mitigation in progress: authenticated domains, double opt-in, one-click unsubscribe.
- **Low open rates** (impact: med, likelihood: med — open) — would undercut the repeat thesis. Mitigated by beta-first
  rollout with instrumentation before GA.

## Competitive Parity

- vs COMP-SUBSTACK — **parity** on direct creator→audience messaging; Substack proved the model, we add the commerce
  spine underneath it.
- vs COMP-SHOPIFY — **ahead**; Shopify has no native fan-relationship layer, only third-party email apps bolted on.
- vs COMP-BIGCARTEL — **ahead**; Big Cartel offers no audience messaging at all.
