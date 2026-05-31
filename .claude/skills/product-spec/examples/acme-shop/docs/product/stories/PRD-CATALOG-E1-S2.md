---
id: PRD-CATALOG-E1-S2
type: story
epic: PRD-CATALOG-E1
status: approved
lang: en
owner: Devon Park
version: 1.0.0
created: 2024-07-10
updated: 2024-08-20
personas: [store-admin]
scope: in
moscow: must
size: M
horizon: now
metrics: [catalog-publish-rate]
acceptance_criteria:
  - "Given a product with variant stock counts, when an order is placed, then the matching variant stock is decremented atomically."
  - "Given a variant at zero stock, when a shopper opens the product, then that variant is shown as sold out and cannot be added to cart."
---

# Track inventory per variant — Story PRD-CATALOG-E1-S2

## User Story

**As a** store-admin, **I want** accurate per-variant stock counts, **so that** we never oversell during a drop and
fans see what is actually available.

## Acceptance Criteria

- Given a product with variant stock counts, when an order is placed, then the matching variant stock is decremented atomically.
- Given a variant at zero stock, when a shopper opens the product, then that variant is shown as sold out and cannot be added to cart.
