<!--
TEMPLATE: epic.md — rich. Goal + business-context links + scope + risks.
Epic ID = PRD-<SLUG>-E<n>. References parent PRD via `prd` and addresses ≥1 BRD goal.
`risks:` is a YAML list of dicts; each entry:
  - description: "Third-party OAuth dependency"   # required free text
    impact: high          # enum: low | med | high
    likelihood: med       # enum: low | med | high
    mitigation: "Fallback provider on standby"     # optional free text
    status: open          # enum: open | mitigated | accepted

TIME dimension (both OPTIONAL — omit and the field defaults to empty/none):
  target_date: 2026-09-30          # ISO YYYY-MM-DD; the deadline for this epic
  depends_on: [PRD-AUTH-E2]        # epic/PRD IDs this epic waits on (a cycle is a dep_cycle error)
-->
---
id: {{id}}
type: epic
prd: {{prd}}
brd_goals: {{brd_goals}}
status: {{status}}
lang: {{lang}}
owner: {{owner}}
version: {{version}}
created: {{created}}
updated: {{updated}}
personas: {{personas}}
scope: {{scope}}
moscow: {{moscow}}
horizon: {{horizon}}
metrics: {{metrics}}
risks: {{risks}}
# TIME (optional) — uncomment to set; absence parses cleanly as none/empty:
# target_date: 2026-09-30
# depends_on: [PRD-AUTH-E2]
---

# {{title}} — Epic {{id}}

## Goal | Mục tiêu

{{goal}}

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** {{prd_requirement_ref}}
- **BRD goal | Mục tiêu BRD:** {{brd_goal_ref}}

## Success Criteria | Tiêu chí thành công

{{success_criteria}}

## Scope | Phạm vi

{{scope_section}}

<!-- OPTIONAL: risks_section -->
## Risks | Rủi ro

{{risks_section}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: stories_overview -->
## Stories Overview | Tổng quan Stories

{{stories_overview}}
<!-- /OPTIONAL -->
