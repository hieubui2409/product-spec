---
id: PRD-CHECKOUT-E1-S1
type: story
epic: PRD-CHECKOUT-E1
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2026-05-28
updated: 2026-05-28
personas: [shopper]
scope: in
moscow: must
size: M
horizon: now
acceptance_criteria:
  - "Given a shopper at checkout, when they enter a valid email, then a magic-link sign-in email is sent within 30 seconds."
  - "Given a shopper who clicked the magic link, when they return to the tab, then their cart is preserved and the checkout form is pre-filled with any saved address."
---

# Magic-link sign-in at checkout

## User Story

**As a** shopper, **I want** to sign in via a magic link at checkout, **so that** I don't have to remember a password and can complete my purchase quickly.

## Acceptance Criteria

- Given a shopper at checkout, when they enter a valid email, then a magic-link sign-in email is sent within 30 seconds.
- Given a shopper who clicked the magic link, when they return to the tab, then their cart is preserved and the checkout form is pre-filled with any saved address.
