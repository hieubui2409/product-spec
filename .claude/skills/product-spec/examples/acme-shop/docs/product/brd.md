---
id: BRD
type: brd
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2026-05-28
updated: 2026-05-28
goals:
  - id: BRD-G1
    title: "Onboard 100 boutique brands in 12 months"
    status: approved
    metrics: [brands-onboarded]
  - id: BRD-G2
    title: "Achieve 80% 90-day repeat-purchase rate"
    status: approved
    metrics: [repeat-rate-90d]
competitors:
  - id: COMP-SHOPIFY
    name: "Shopify"
    url: "https://www.shopify.com"
    threat: high
  - id: COMP-BIGCARTEL
    name: "Big Cartel"
    url: "https://www.bigcartel.com"
    threat: med
---

# Business Requirements Document

## Problem / Opportunity

Boutique brands need a direct-to-fan storefront with a healthy revenue split. We have an opportunity to capture the segment marketplaces under-serve.

## Business Goals

- BRD-G1 — Onboard 100 boutique brands in 12 months.
- BRD-G2 — Achieve 80% 90-day repeat-purchase rate.

## Success Metrics

- brands-onboarded (target: 100)
- repeat-rate-90d (target: 80%)

## Stakeholders

Founders, lead engineer, design partner brands (5).

## Constraints

Q3 launch deadline; ~$300K seed budget.

## Market Context

Shopify owns the long tail but extracts ~3% + transaction fees and surfaces no fan-level messaging. Direct-to-fan competitors (Substack-for-fashion) don't exist.

## Competitive Landscape

Competitor identity is declared once in the frontmatter `competitors:` list (the DRY home); PRDs reference these IDs
from their `competitive_parity` map.

- COMP-SHOPIFY (Shopify) — high threat: dominant incumbent, deep ecosystem, but no fan-level messaging.
- COMP-BIGCARTEL (Big Cartel) — med threat: indie-maker storefront, simpler than us, weak on direct-to-fan loyalty.
