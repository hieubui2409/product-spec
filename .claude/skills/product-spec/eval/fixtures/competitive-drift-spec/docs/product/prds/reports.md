---
id: PRD-REPORTS
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
horizon: next
scope: in
competitive_parity:
  COMP-ACME: behind
  COMP-NICHE: none
---

# Reports PRD (drift missing-anchor — must NOT flag)

NOT a core-value PRD (scope: in) AND only 1 real verdict (COMP-NICHE is `none`,
which is not a data point). Ineligible on BOTH the scope and the >=2-data facets
→ the LLM returns finding:null (missing_anchor). It must NOT flag on `behind`
alone. The explicit anti-hallucination case.
