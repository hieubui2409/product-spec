---
id: PRD-SEARCH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
horizon: now
scope: core-value
competitive_parity:
  COMP-ACME: behind
  COMP-SHOPIFY: parity
---

# Search PRD (drift borderline — must NOT flag)

A core-value PRD with 2 data points, but one is `parity` (not `behind`). Eligible
(scope core-value AND 2 verdicts) yet the rule "EVERY real parity == behind" does
NOT hold → the LLM returns finding:null (below_threshold). Guards the over-flag.
