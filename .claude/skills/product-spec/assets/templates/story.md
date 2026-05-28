<!--
TEMPLATE: story.md — rich. As-a/I-want/so-that + AC + size + personas.
Story ID = PRD-<SLUG>-E<n>-S<n>. References parent epic via `epic`.
-->
---
id: {{id}}
type: story
epic: {{epic}}
status: {{status}}
lang: {{lang}}
owner: {{owner}}
version: {{version}}
created: {{created}}
updated: {{updated}}
personas: {{personas}}
scope: {{scope}}
moscow: {{moscow}}
size: {{size}}
horizon: {{horizon}}
metrics: {{metrics}}
acceptance_criteria: {{acceptance_criteria}}
---

# {{title}} — Story {{id}}

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** {{persona}}
**I want** | **Tôi muốn** {{want}}
**so that** | **để** {{so_that}}.

## Acceptance Criteria | Tiêu chí chấp nhận

{{acceptance_criteria_bullets}}

<!-- OPTIONAL: notes -->
## Notes | Ghi chú

{{notes}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: dependencies -->
## Dependencies | Phụ thuộc

{{dependencies}}
<!-- /OPTIONAL -->
