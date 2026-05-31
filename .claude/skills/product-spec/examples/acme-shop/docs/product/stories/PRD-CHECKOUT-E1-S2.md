---
id: PRD-CHECKOUT-E1-S2
type: story
epic: PRD-CHECKOUT-E1
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2024-07-01
updated: 2024-08-10
personas: [shopper]
scope: in
moscow: should
size: S
horizon: now
metrics: [checkout-completion-rate]
acceptance_criteria:
  - "Given a returning shopper who saved an address on a prior order, when they reach the address step, then their default saved address is pre-selected."
  - "Given a shopper editing the address, when they save a new address, then it is stored on their account and offered on the next checkout."
---

# Saved addresses for returning shoppers — Story PRD-CHECKOUT-E1-S2

## User Story

**As a** shopper, **I want** my delivery address remembered between purchases, **so that** I can check out faster on my
next order without retyping it.

## Acceptance Criteria

- Given a returning shopper who saved an address on a prior order, when they reach the address step, then their default saved address is pre-selected.
- Given a shopper editing the address, when they save a new address, then it is stored on their account and offered on the next checkout.
