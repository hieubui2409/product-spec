<!--
TEMPLATE: PRODUCT.md
Token convention: {{token}} substituted by generate_templates.py.
Optional sections wrapped in <!-- OPTIONAL: name --> ... <!-- /OPTIONAL -->.
generate_templates.py drops optional blocks the PO chose to skip.
Bilingual headers: EN above, VI below (commented). lang chooses which is kept.
-->
---
id: PRODUCT
type: product
status: {{status}}
lang: {{lang}}
owner: {{owner}}
version: {{version}}
created: {{created}}
updated: {{updated}}
name: "{{name}}"
one_line_description: "{{one_line_description}}"
current_implementation: "{{current_implementation}}"
deployment: "{{deployment}}"
roadmap_one_liner: "{{roadmap_one_liner}}"
core_value: "{{core_value}}"
personas: {{personas}}
---

# {{name}} — Product Context | Bối cảnh sản phẩm

> Thin labels only. Narrative lives in `vision.md`. Stakeholders / business goals live in `brd.md`. — Chỉ nhãn ngắn. Phần kể chi tiết ở `vision.md`. Mục tiêu kinh doanh ở `brd.md`.

## One-Line Description | Mô tả một câu

{{one_line_description}}

## Core Value | Giá trị cốt lõi

_(authoritative value lives in frontmatter `core_value` field — see top of file. Body deliberately blank to keep one source of truth.)_

## Current Implementation | Hiện trạng triển khai

{{current_implementation}}

## Deployment | Triển khai

{{deployment}}

## Roadmap One-Liner | Lộ trình một câu

{{roadmap_one_liner}}

## Personas | Nhóm người dùng

{{personas_bullets}}

<!-- OPTIONAL: contact -->
## Contact | Liên hệ

{{contact}}
<!-- /OPTIONAL -->
