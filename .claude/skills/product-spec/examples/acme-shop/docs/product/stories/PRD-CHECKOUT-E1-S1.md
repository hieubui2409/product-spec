---
id: PRD-CHECKOUT-E1-S1
type: story
epic: PRD-CHECKOUT-E1
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2024-06-18
updated: 2024-08-12
personas: [shopper]
scope: in
moscow: must
size: M
horizon: now
metrics: [checkout-completion-rate]
acceptance_criteria:
  - "Given a shopper at checkout, when they enter a valid email, then a magic-link sign-in email is sent within 30 seconds."
  - "Given a shopper who clicked the magic link, when they return to the tab, then their cart is preserved and the checkout form is pre-filled with any saved address."
---

# Magic-link sign-in at checkout — Story PRD-CHECKOUT-E1-S1

## User Story

**As a** shopper, **I want** to sign in via a magic link at checkout, **so that** I don't have to remember a password
and can complete my purchase quickly.

## Acceptance Criteria

- Given a shopper at checkout, when they enter a valid email, then a magic-link sign-in email is sent within 30 seconds.
- Given a shopper who clicked the magic link, when they return to the tab, then their cart is preserved and the checkout form is pre-filled with any saved address.
