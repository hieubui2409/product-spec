<!--
TEMPLATE: brd.md (Business Requirements Document) — singular per product.
Goals carry IDs (BRD-G1, BRD-G2, ...). Each goal pairs with a success metric.
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
goals: {{goals}}
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
