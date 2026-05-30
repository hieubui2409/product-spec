<!--
TEMPLATE: prd.md (Product Requirements Document) — one per feature-area.
Multi-PRD per BRD. Carries narrative, scope, NFRs, success metrics.
Does NOT enumerate stories (that lives in epic/story files).
`risks:` is a YAML list of dicts; each entry:
  - description: "Third-party OAuth dependency"   # required free text
    impact: high          # enum: low | med | high
    likelihood: med       # enum: low | med | high
    mitigation: "Fallback provider on standby"     # optional free text
    status: open          # enum: open | mitigated | accepted
-->
---
id: {{id}}
type: prd
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
---

# {{title}} — PRD {{id}}

## Overview & Problem | Tổng quan và Vấn đề

{{overview_problem}}

## Personas | Nhóm người dùng

{{personas_section}}

## Use Cases / Flows | Tình huống sử dụng / Luồng

{{use_cases}}

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

{{must_have}}

### Should | Nên có

{{should_have}}

### Could | Có thể có

{{could_have}}

### Won't (this round) | Không (lần này)

{{wont_have}}

## Non-Functional Requirements | Yêu cầu phi chức năng

{{nfrs}}

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

{{success_metrics}}

<!-- OPTIONAL: scope_in_out -->
## Scope In / Out | Phạm vi Trong / Ngoài

**In scope | Trong phạm vi:**

{{scope_in}}

**Out of scope | Ngoài phạm vi:**

{{scope_out}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: dependencies_risks -->
## Dependencies & Risks | Phụ thuộc và Rủi ro

{{dependencies_risks}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: open_questions -->
## Open Questions | Câu hỏi mở

{{open_questions}}
<!-- /OPTIONAL -->
