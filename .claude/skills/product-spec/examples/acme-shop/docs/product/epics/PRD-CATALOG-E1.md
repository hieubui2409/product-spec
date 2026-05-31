---
id: PRD-CATALOG-E1
type: epic
prd: PRD-CATALOG
brd_goals: [BRD-G1]
status: approved
lang: en
owner: Devon Park
version: 1.0.0
created: 2024-06-20
updated: 2024-12-10
personas: [store-admin, brand-owner]
scope: in
moscow: must
horizon: now
target_date: 2024-07-31
risks:
  - description: "Concurrent stock edits during a drop race and oversell."
    impact: high
    likelihood: low
    status: mitigated
    mitigation: "Atomic decrement with a reserved-stock window."
---

# Catalog Management Epic

## Goal

A store-admin can add, edit, publish products and keep inventory accurate.

## Business Context

- PRD requirement: product CRUD, per-variant inventory, publish/unpublish.
- BRD goal: BRD-G1 (a populated, published catalog is what makes a brand "live").

## Success Criteria

A new product is publishable within minutes; inventory never oversells during a drop. _Shipped Jul 2024; median
time-to-first-product under 20 minutes._

## Scope

Product add/edit/archive with variants and photos, per-variant inventory tracking with atomic decrement, publish to
the live storefront. CSV import is in this epic; merchandising rules are out.

## Risks

- **Inventory oversell** (impact: high, likelihood: low — mitigated) — concurrent stock edits during a drop race.
  Mitigation shipped: atomic decrement with a reserved-stock window.
