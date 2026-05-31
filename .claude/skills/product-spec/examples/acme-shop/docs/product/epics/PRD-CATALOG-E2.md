---
id: PRD-CATALOG-E2
type: epic
prd: PRD-CATALOG
brd_goals: [BRD-G3]
status: approved
lang: en
owner: Devon Park
version: 1.0.0
created: 2024-07-05
updated: 2024-12-10
personas: [shopper, brand-owner]
scope: in
moscow: must
horizon: now
target_date: 2024-08-25
depends_on: [PRD-CATALOG-E1]
risks:
  - description: "Large image galleries slow the product detail page on mobile."
    impact: med
    likelihood: med
    status: mitigated
    mitigation: "Responsive image CDN + lazy-loading below the fold."
---

# Brand Storefront Epic

## Goal

A shopper can browse a brand's storefront and open a product detail page ready to add to cart.

## Business Context

- PRD requirement: shopper browse (categories, search) + product detail page.
- BRD goal: BRD-G3 (the storefront is the surface that converts browsing into GMV).
- Depends on PRD-CATALOG-E1 (products must exist and be published before they can be browsed).

## Success Criteria

Browse first-paint under 1.5s on 4G; product detail add-to-cart works for every in-stock variant. _Shipped Aug 2024._

## Scope

Category navigation, in-catalog search, and the product detail page (gallery, variant selector, stock state,
add-to-cart). Cross-brand search is out (PRD-DISCOVERY).

## Risks

- **Slow image-heavy PDP on mobile** (impact: med, likelihood: med — mitigated) — large galleries hurt load time.
  Mitigation shipped: responsive image CDN + lazy-loading below the fold.
