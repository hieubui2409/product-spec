---
id: BRD
type: brd
status: approved
lang: en
owner: Jane Doe
version: 1.5.0
created: 2024-06-01
updated: 2026-05-20
goals:
  - id: BRD-G1
    title: "Onboard 100 boutique brands in 12 months"
    metrics: [brands-onboarded]
    status: approved
    owner: Mara Lin
  - id: BRD-G2
    title: "Achieve 80% 90-day repeat-purchase rate"
    metrics: [repeat-rate-90d]
    status: approved
    owner: Jane Doe
  - id: BRD-G3
    title: "Reach $2M GMV in the first year"
    metrics: [gmv-year1]
    status: approved
    owner: Jane Doe
  - id: BRD-G4
    title: "Keep average brand payout latency under 3 days"
    metrics: [payout-latency-days]
    status: approved
    owner: Mara Lin
  - id: BRD-G5
    title: "Launch native mobile shopping by year 2"
    metrics: [mobile-mau]
    status: review
    owner: Devon Park
  - id: BRD-G6
    title: "Scale to 500 brands with cross-brand discovery (year 3)"
    metrics: [brands-onboarded-y3]
    status: draft
    owner: Jane Doe
competitors:
  - id: COMP-SHOPIFY
    name: "Shopify"
    url: "https://www.shopify.com"
    threat: high
  - id: COMP-BIGCARTEL
    name: "Big Cartel"
    url: "https://www.bigcartel.com"
    threat: med
  - id: COMP-ETSY
    name: "Etsy"
    url: "https://www.etsy.com"
    threat: high
  - id: COMP-SUBSTACK
    name: "Substack"
    url: "https://substack.com"
    threat: low
---

# Business Requirements Document

## Problem / Opportunity

Boutique fashion brands are under-served by every tool on the market. Marketplaces (Etsy, social-commerce add-ons)
extract 30%+ in fees and commissions and keep the customer relationship; generic storefronts (Shopify, Big Cartel)
keep the revenue but offer nothing for the fan relationship that drives a small brand's repeat business. The
opportunity is the segment in between: a direct-to-fan storefront that keeps the brand's margin AND gives the brand a
first-class fan relationship — messaging, segments, loyalty — that no incumbent ships.

We entered this market in mid-2024. Two years in, the thesis has held: the core storefront proved the economics, and
the open frontier — the part competitors structurally cannot copy without cannibalizing their marketplace fee
model — is the fan-CRM layer we are building now.

## Business Goals

- **BRD-G1** — Onboard 100 boutique brands in 12 months. _(approved; ACHIEVED — 120+ brands by mid-2025.)_
- **BRD-G2** — Achieve 80% 90-day repeat-purchase rate. _(approved; in progress — currently ~71%, the fan-CRM bet.)_
- **BRD-G3** — Reach $2M GMV in the first year. _(approved; ACHIEVED — ~$2.1M year-1 GMV, ~$2.4M cumulative.)_
- **BRD-G4** — Keep average brand payout latency under 3 days. _(approved; ACHIEVED — running ~1.8 days.)_
- **BRD-G5** — Launch native mobile shopping by year 2. _(in review — slipped from year-2; mobile PRD is later-horizon.)_
- **BRD-G6** — Scale to 500 brands with cross-brand discovery (year 3). _(draft — depends on discovery, deliberately out-of-scope for now.)_

## Success Metrics

| Metric | Target | Current actual (2026-05) |
|--------|--------|--------------------------|
| brands-onboarded | 100 in year 1 | 120+ (target hit) |
| repeat-rate-90d | 80% | ~71% (climbing with fan-CRM) |
| gmv-year1 | $2.0M | ~$2.1M (target hit) |
| payout-latency-days | < 3.0 days | ~1.8 days (target hit) |
| mobile-mau | 25,000 by end of year 2 | n/a (mobile not yet shipped) |
| brands-onboarded-y3 | 500 | 120+ (year-3 goal) |
| fan-message-open-rate | 40% open on broadcasts | ~38% (FANCRM in beta) |
| checkout-completion-rate | 75% | ~78% (shipped, exceeds target) |

## Stakeholders

- **Jane Doe** — Founder / CEO; accountable for vision, GMV, repeat-rate.
- **Mara Lin** — Head of Operations; owns brand onboarding (BRD-G1) and payouts (BRD-G4).
- **Devon Park** — Head of Product/Eng; owns the mobile and analytics roadmap (BRD-G5).
- **Design-partner brands (5 founding, now 120+)** — the boutique brand-owners whose feedback steers the roadmap.
- **Stripe** — payments + payout infrastructure partner (Stripe Connect).

## Constraints

- Series-A budget (~$4M raised after the seed); ~18 months of runway as of mid-2026.
- Team of ~14 (6 eng); small enough that the roadmap is sequenced, not parallelized.
- PCI scope is offloaded to Stripe; we hold no card data.
- Multi-region data residency (US/EU) is a hard requirement for EU brand payouts.

## Market Context

Shopify owns the long tail of independent commerce but extracts ~2.9% + per-transaction fees and surfaces no
fan-level messaging — a brand on Shopify rents its audience back from Meta. Etsy commands fashion-adjacent discovery
but takes ~6.5% plus listing and ad fees, and the buyer belongs to Etsy, not the brand. Substack proved that fans will
pay creators directly and that an owned audience is defensible — but it has no commerce, inventory, or payout spine.
The white space is a real storefront fronted by an owned fan relationship; that is the wedge Acme occupies.

## Assumptions & Risks

- **Assumption:** boutique brands will pay a SaaS fee for fan ownership rather than chase marketplace reach. _(Validated
  by 120+ paying brands.)_
- **Assumption:** fans will tolerate a slightly higher price for direct support of the brand. _(Holding; ~78% checkout
  completion.)_
- **Risk:** a payments-partner concentration on Stripe — a Stripe outage or policy change hits payouts directly.
  Mitigation: payout-run idempotency + reconciliation; a second processor is a future option, not built.
- **Risk:** the fan-CRM bet (BRD-G2) is the company's differentiation; if open/engagement rates underperform, the
  repeat-rate goal stalls. Mitigation: ship in beta to design-partner brands first, instrument open/reply rates.

## Goal → Metric Table

| Goal ID | Goal | Metric | Target |
|---------|------|--------|--------|
| BRD-G1 | Onboard 100 boutique brands in 12 months | brands-onboarded | 100 |
| BRD-G2 | Achieve 80% 90-day repeat-purchase rate | repeat-rate-90d | 80% |
| BRD-G3 | Reach $2M GMV in the first year | gmv-year1 | $2.0M |
| BRD-G4 | Keep average brand payout latency under 3 days | payout-latency-days | < 3 days |
| BRD-G5 | Launch native mobile shopping by year 2 | mobile-mau | 25,000 MAU |
| BRD-G6 | Scale to 500 brands with cross-brand discovery (year 3) | brands-onboarded-y3 | 500 |
