---
id: PRD-FANCRM-E1-S1
type: story
epic: PRD-FANCRM-E1
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2025-11-15
updated: 2026-05-10
personas: [brand-owner, shopper]
scope: in
moscow: should
size: L
horizon: next
metrics: [fan-message-open-rate]
acceptance_criteria:
  - "Given a brand-owner with a composed broadcast, when they send to a segment, then opted-in fans in that segment receive the message and unsubscribed fans are suppressed."
  - "Given a sent broadcast, when fans open or click it, then per-broadcast open and click rates are recorded and shown to the brand-owner."
---

# Send a fan broadcast — Story PRD-FANCRM-E1-S1

## User Story

**As a** brand-owner, **I want** to broadcast a message to my fans, **so that** I can announce a drop directly to the
people who already love the brand.

## Acceptance Criteria

- Given a brand-owner with a composed broadcast, when they send to a segment, then opted-in fans in that segment receive the message and unsubscribed fans are suppressed.
- Given a sent broadcast, when fans open or click it, then per-broadcast open and click rates are recorded and shown to the brand-owner.
