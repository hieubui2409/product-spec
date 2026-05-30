<!--
TEMPLATE: brd.md (Business Requirements Document) — singular per product.
Goals carry IDs (BRD-G1, BRD-G2, ...). Each goal pairs with a success metric.

COMPETITION dimension — `competitors:` is the DRY home for competitor IDENTITY
(defined ONCE here; each PRD references them by ID via `competitive_parity`).
Each entry:
  - id: COMP-ACME            # ID grammar: COMP-<SLUG> (uppercase, ≤16-char slug)
    name: "Acme Commerce"
    url: "https://acme.example"   # stored ONLY, never fetched; a `private:`
                                  # prefix is IGNORED (OpSec — never displayed)
    threat: high              # enum: low | med | high
Omit the whole block and the field defaults to empty (a v1 BRD stays valid).
-->
---
id: BRD
type: brd
status: {{status}}
lang: {{lang}}
owner: {{owner}}
version: {{version}}
created: {{created}}
updated: {{updated}}
# goals: list-of-dicts. Each entry MUST carry id/title/metrics/status/owner.
# See references/frontmatter-and-id-spec.md → "BRD goals (under brd.md `goals:` key)".
# Example shape (delete this block and the example once your real goals are filled):
#   goals:
#     - id: BRD-G1
#       title: "Onboard 100 boutique brands in 12 months"
#       metrics: [brands-onboarded]
#       status: draft
#       owner: Jane Doe
#     - id: BRD-G2
#       title: "Achieve 80% 90-day repeat-purchase rate"
#       metrics: [repeat-rate-90d]
#       status: draft
#       owner: Jane Doe
goals: {{goals}}
# competitors: list-of-dicts (DRY home for competitor identity). Each entry
# carries id (COMP-<SLUG>) + name + url + threat (low|med|high). Empty [] is fine
# for a v1 BRD; each PRD references these by ID via `competitive_parity`.
competitors: {{competitors}}
---

# Business Requirements Document | Tài liệu Yêu cầu Kinh doanh

## Problem / Opportunity | Vấn đề / Cơ hội

{{problem_opportunity}}

## Business Goals | Mục tiêu kinh doanh

{{goals_section}}

## Success Metrics | Chỉ số thành công

{{metrics_section}}

## Stakeholders | Bên liên quan

{{stakeholders}}

## Constraints | Ràng buộc

{{constraints}}

## Market Context | Bối cảnh thị trường

{{market_context}}

<!-- OPTIONAL: assumptions_risks -->
## Assumptions & Risks | Giả định và Rủi ro

{{assumptions_risks}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: goal_metric_table -->
## Goal → Metric Table | Bảng Mục tiêu → Chỉ số

| Goal ID | Goal | Metric | Target |
|---------|------|--------|--------|
{{goal_metric_rows}}
<!-- /OPTIONAL -->
