---
id: PRD-FANCRM-E2-S1
type: story
epic: PRD-FANCRM-E2
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2026-02-05
updated: 2026-05-12
personas: [brand-owner]
scope: in
moscow: should
size: M
horizon: next
metrics: [repeat-rate-90d]
acceptance_criteria:
  - "Given a brand-owner building a segment, when they filter by purchase history (e.g. bought in last 90 days), then the matching fan count is shown and the segment can be saved."
  - "Given a saved segment, when the nightly recompute runs, then segment membership reflects the latest purchase data."
---

# Segment by purchase history — Story PRD-FANCRM-E2-S1

## User Story

**As a** brand-owner, **I want** to build audience segments from purchase history, **so that** I can target the right
fans — recent buyers, big spenders — instead of blasting everyone.

## Acceptance Criteria

- Given a brand-owner building a segment, when they filter by purchase history (e.g. bought in last 90 days), then the matching fan count is shown and the segment can be saved.
- Given a saved segment, when the nightly recompute runs, then segment membership reflects the latest purchase data.
