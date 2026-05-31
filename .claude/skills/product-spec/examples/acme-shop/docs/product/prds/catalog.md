---
id: PRD-CATALOG
type: prd
brd_goals: [BRD-G1, BRD-G3]
status: approved
lang: en
owner: Devon Park
version: 1.1.0
created: 2024-06-12
updated: 2025-02-20
personas: [store-admin, brand-owner, shopper]
scope: core-value
moscow: must
horizon: now
metrics: [catalog-publish-rate, time-to-first-product]
risks:
  - description: "Inventory oversell during a high-traffic product drop when stock counts race."
    impact: high
    likelihood: low
    status: mitigated
    mitigation: "Atomic stock decrement at order creation; oversell guard with reserved-stock window."
  - description: "Slow time-to-first-product onboarding frustrates new brands before they see value."
    impact: med
    likelihood: med
    status: accepted
    mitigation: "CSV bulk import + guided first-product wizard."
competitive_parity:
  COMP-SHOPIFY: behind
  COMP-BIGCARTEL: parity
  COMP-ETSY: behind
target_date: 2024-08-31
---

# Catalog & Storefront — PRD PRD-CATALOG

## Overview & Problem

A brand cannot sell what it cannot list. Catalog was the second core-value piece shipped (Aug 2024): the brand-facing
tools to add products, track inventory, and publish a storefront, and the shopper-facing browse + product-detail
surface. It is the front door of every brand on Acme. Today it backs all 120+ brands; median time-to-first-product is
under 20 minutes via the guided wizard and CSV import.

## Personas

- **store-admin** — manages the catalog day-to-day: adds products, edits variants, keeps stock accurate.
- **brand-owner** — sets up the storefront, curates what is published, owns the brand presentation.
- **shopper** — browses the catalog and opens product detail pages before buying.

## Use Cases / Flows

1. store-admin adds a product (title, photos, price, variants) or bulk-imports a CSV.
2. store-admin sets and adjusts inventory counts per variant.
3. brand-owner publishes the product to the live storefront.
4. shopper browses the brand's catalog (categories, search) and opens a product detail page.
5. shopper adds to cart → hands off to checkout (PRD-CHECKOUT).

## Functional Requirements (MoSCoW)

### Must

- Add / edit / archive products with photos, price, description, and variants (size, color).
- Per-variant inventory tracking with atomic decrement at order time (oversell guard).
- Publish / unpublish to the live storefront.
- Shopper browse: category navigation, in-catalog search.
- Product detail page with gallery, variant selector, stock state, add-to-cart.

### Should

- CSV bulk import for brands migrating an existing catalog.
- Guided first-product wizard to cut time-to-first-product.

### Could

- Collections / lookbooks for curated merchandising.

### Won't (this round)

- Cross-brand catalog search (that is PRD-DISCOVERY, deliberately out of scope).
- Digital / non-physical products.

## Non-Functional Requirements

- Storefront browse pages cached at the edge; first paint under 1.5s on 4G.
- Inventory writes serialized so concurrent drop traffic cannot oversell.
- Catalog edits visible on the live storefront within 60s of publish.

## Success Metrics → BRD Goals

- **catalog-publish-rate** → BRD-G1 (a published catalog is a live brand we can count toward onboarding).
- **time-to-first-product** → BRD-G1, BRD-G3 (faster to first product = faster to first sale = GMV sooner).

## Scope In / Out

**In scope:** single-brand catalog management, inventory, storefront browse + product detail.

**Out of scope:** cross-brand discovery (PRD-DISCOVERY), advanced merchandising rules.

## Dependencies & Risks

- **Inventory oversell** (impact: high, likelihood: low — mitigated) — concurrent drop traffic racing on stock counts.
  Mitigation shipped: atomic decrement + reserved-stock window.
- **Slow first-product onboarding** (impact: med, likelihood: med — accepted) — friction before a brand sees value.
  Accepted with the CSV import + wizard; tracked via time-to-first-product.

## Competitive Parity

- vs COMP-SHOPIFY — **behind** on app/theme ecosystem and merchandising depth; acceptable for our segment.
- vs COMP-BIGCARTEL — **parity** on simple-catalog management for small brands.
- vs COMP-ETSY — **behind** on discovery surface, by design (no marketplace).
