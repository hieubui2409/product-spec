---
id: PRD-DISCOVERY
type: prd
brd_goals: [BRD-G6]
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2026-05-02
updated: 2026-05-02
personas: [shopper]
scope: out
moscow: wont
horizon: later
metrics: [discovery-ctr]
risks:
  - description: "Cross-brand discovery risks re-commoditizing brands into a marketplace, violating the core promise."
    impact: high
    likelihood: low
    status: open
    mitigation: "Opt-in only; rank by fan affinity, never paid placement; brands control inclusion."
competitive_parity:
  COMP-ETSY: behind
---

# Cross-Brand Discovery — PRD PRD-DISCOVERY

## Overview & Problem

The year-3 ambition (BRD-G6): let a fan of one Acme brand discover adjacent brands they would love — a personalized
discovery feed across the network. This is the most strategically sensitive item in the spec. Done wrong, it turns
Acme into the very marketplace we promised brands we would never be (ranking brands against each other, taxing
attention). Marked **scope: out / wont** for now precisely because the team has not yet resolved how to add discovery
without breaking the core promise. It stays in the spec as a tracked, deferred bet, not a committed build.

## Personas

- **shopper** — a fan of one brand who might love an adjacent brand, surfaced by genuine affinity rather than ads.

## Use Cases / Flows

1. shopper who bought from brand A sees a discovery feed of affinity-matched brands.
2. shopper follows or buys from a newly discovered brand B.
3. brand-owner opts their brand into (or out of) the discovery network and sees referral attribution.

## Functional Requirements (MoSCoW)

### Must

- _(none committed — the PRD is deferred; requirements are exploratory until the marketplace-risk question is resolved.)_

### Should

- _(deferred)_

### Could

- Personalized cross-brand discovery feed, ranked by fan affinity.
- Brand opt-in/opt-out controls and referral attribution.

### Won't (this round)

- Any paid placement or pay-to-rank mechanic (would violate the no-marketplace principle).
- Algorithmic ranking that pits brands against each other for impressions.

## Non-Functional Requirements

- Discovery must be opt-in per brand; a brand can never be surfaced without consent.
- Ranking signal is fan affinity only — never paid placement, never engagement-maximization at the brand's expense.

## Success Metrics → BRD Goals

- **discovery-ctr** → BRD-G6 (cross-brand discovery click-through is the leading indicator of the year-3 network goal).

## Scope In / Out

**Out of scope (this round):** the entire build. This is a tracked future bet, deliberately not committed.

## Dependencies & Risks

- **Marketplace re-commoditization** (impact: high, likelihood: low — open) — the existential risk: discovery done
  wrong betrays the core promise to brands. Mitigation principle: opt-in only, affinity-ranked, never paid placement.

## Competitive Parity

- vs COMP-ETSY — **behind**; Etsy is discovery-native. Our deliberate bet is that owned-fan discovery, done without a
  marketplace tax, can beat Etsy's model on brand economics — if and when we build it.
