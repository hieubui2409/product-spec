# Interview — PRD

Question bank for drafting a Product Requirements Document for one feature-area. Each question maps to a PRD frontmatter field or section.

## P0 — Target Feature-Area

**target:** `prd.md → id (slug)`, `title`

- **EN:** "Give the feature-area a short uppercase slug (e.g., AUTH, BILLING, ONBOARDING). And a one-line title."
- **VI:** "Đặt slug ngắn in hoa cho mảng tính năng này (ví dụ AUTH, BILLING). Và một câu tiêu đề."

## P1 — Overview & Problem

**target:** `prd.md → Overview & Problem`

- **EN:** "What problem does this feature-area solve — what does the user feel today, what do they feel after?"
- **VI:** "Mảng tính năng này giải quyết vấn đề gì — người dùng cảm thấy gì hôm nay, và sau khi có nó?"
- **5-Why trigger:** answer doesn't change the user's experience.

## P2 — Personas (subset)

**target:** `prd.md → personas`

- **EN:** "Of the product personas, which ones use this feature-area? (subset of PRODUCT.md personas)"
- **VI:** "Trong các persona của sản phẩm, mảng tính năng này dành cho ai? (tập con của PRODUCT.md)"
- **Mode:** multi-select pre-populated from `PRODUCT.md.personas`.

## P3 — Use Cases / Flows

**target:** `prd.md → Use Cases / Flows`

- **EN:** "Walk me through a user's day using this feature — step by step (story mapping)."
- **VI:** "Mô tả một ngày của người dùng khi dùng tính năng này — từng bước (story mapping)."
- **Mode:** free-form; LLM offers numbered structure.

## P4 — Functional Requirements (MoSCoW)

**target:** `prd.md → MoSCoW lists`

For each requirement the PO names, ask:

- **EN:** "Is this MUST-have for launch, SHOULD-have, COULD-have, or WONT (this round)?"
- **VI:** "Yêu cầu này là BẮT BUỘC cho ra mắt, NÊN có, CÓ THỂ có, hay KHÔNG (lần này)?"
- **MoSCoW Gate (5-Why):** if PO calls everything MUST → ask "if X delays launch by a month, is it still MUST?" Iterate until at most 60% are MUST.

## P5 — Non-Functional Requirements

**target:** `prd.md → NFRs`

- **EN:** "Beyond features, what does the product need to be — fast, secure, accessible, multilingual? Be specific."
- **VI:** "Ngoài chức năng, sản phẩm cần là gì — nhanh, an toàn, dễ tiếp cận, đa ngôn ngữ? Cụ thể."
- **Seed options:** performance, security, accessibility, localization, reliability, observability.

## P6 — Success Metrics → BRD Goals

**target:** `prd.md → brd_goals` (frontmatter), `Success Metrics`

- **EN:** "Which BRD goals does this feature-area advance? Pick from the list."
- **VI:** "Mảng tính năng này đẩy mục tiêu BRD nào? Chọn từ danh sách."
- **Mode:** multi-select pre-populated from existing `BRD-G<n>` IDs.

## P7 — Scope In / Out (OPTIONAL)

**target:** `prd.md → OPTIONAL: scope_in_out`

- **EN:** "Anything close to this feature that is EXPLICITLY out of scope this round?"
- **VI:** "Có gì gần với tính năng này CHẮC CHẮN ngoài phạm vi lần này?"

## P8 — Dependencies & Risks (OPTIONAL)

**target:** `prd.md → OPTIONAL: dependencies_risks`

- **EN:** "What does this feature depend on (other teams, third-party services, data)? What could go wrong?"
- **VI:** "Tính năng này phụ thuộc gì (đội khác, dịch vụ ngoài, dữ liệu)? Điều gì có thể sai?"

## P9 — Open Questions (OPTIONAL)

**target:** `prd.md → OPTIONAL: open_questions`

- **EN:** "What questions are still open — to revisit before sign-off?"
- **VI:** "Còn câu hỏi nào chưa rõ — cần xem lại trước khi phê duyệt?"

## P10 — Horizon & Scope Tag

**target:** `prd.md → horizon`, `scope`

- **EN:** "Is this feature-area NOW (this release), NEXT, or LATER? And is it part of the product's CORE value or just IN scope?"
- **VI:** "Mảng tính năng này là BÂY GIỜ (release này), TIẾP, hay SAU? Và là phần CỐT LÕI của giá trị sản phẩm hay chỉ TRONG phạm vi?"

## Adaptivity Rules

- For a small product, allow skipping P5 (NFRs) and P7/P8/P9.
- After P4 + P5, the LLM offers a structural validation pass before continuing.
- Persona-related skip: P2 auto-skips if `PRODUCT.md` has only one persona.
- MoSCoW MoSCoW-gate is mandatory for every PRD (do not let everything be MUST).
