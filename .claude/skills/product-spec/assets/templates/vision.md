<!--
TEMPLATE: vision.md
Narrative product vision. Long-form (read once); pairs with the labels-only PRODUCT.md.
Bilingual headers via "EN | VI" format.
-->
---
id: VISION
type: vision
status: {{status}}
lang: {{lang}}
owner: {{owner}}
version: {{version}}
created: {{created}}
updated: {{updated}}
personas: {{personas}}
---
<!--
Note: vision.md intentionally omits `horizon`. The horizon enum (now/next/later)
describes WHEN work happens; vision is timeless strategy. Roadmap horizon lives
on PRDs/epics/stories. Keeping `horizon: {{horizon}}` here meant a fresh init
always landed `horizon: TBD` which fails the closed-enum check.
-->

# Vision — {{name}} | Tầm nhìn

## Problem Narrative | Câu chuyện vấn đề

{{problem_narrative}}

## Personas | Nhóm người dùng

{{personas_detail}}

## Value Proposition | Đề xuất giá trị

{{value_proposition}}

## North-Star | Sao Bắc Đẩu

{{north_star}}

## 1–3 Year Direction | Hướng đi 1–3 năm

{{direction_1_to_3_years}}

<!-- OPTIONAL: principles -->
## Principles | Nguyên tắc

{{principles}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: non_goals -->
## Non-Goals | Không phải mục tiêu

{{non_goals}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: differentiation -->
## Differentiation | Khác biệt

{{differentiation}}
<!-- /OPTIONAL -->
