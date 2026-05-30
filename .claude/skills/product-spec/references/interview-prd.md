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
- **VI:** "Có gì sát với tính năng này mà CHẮC CHẮN nằm ngoài phạm vi lần này không?"

## P8 — Dependencies & Risks (narrative, OPTIONAL)

**target:** `prd.md → OPTIONAL: dependencies_risks`

- **EN:** "What does this feature depend on (other teams, third-party services, data)? What could go wrong?"
- **VI:** "Tính năng này phụ thuộc gì (đội khác, dịch vụ ngoài, dữ liệu)? Điều gì có thể sai?"

## P8a — Structured Risks (OPTIONAL)

**target:** `prd.md → risks:` (each entry `{description, impact, likelihood, status, mitigation}`)

For each risk the PO raises in P8, capture the four enums + mitigation (same shape as the epic/BRD risk bank):

- **EN:**
  - "Describe the risk in one line."
  - "**Impact** if it happens — low / med / high?"
  - "**Likelihood** — low / med / high?"
  - "**Status** — open, mitigated, or accepted?"
  - "**Mitigation** — what would you do about it?"
- **VI:**
  - "Mô tả rủi ro trong một câu."
  - "**Ảnh hưởng** nếu xảy ra — thấp (low) / trung bình (med) / cao (high)?"
  - "**Khả năng xảy ra** — thấp (low) / trung bình (med) / cao (high)?"
  - "**Trạng thái** — chưa xử lý (open), đã giảm thiểu (mitigated), hay chấp nhận (accepted)?"
  - "**Cách giảm thiểu** — bạn sẽ làm gì với nó?"
- **Enums (closed):** `impact`/`likelihood` ∈ `low | med | high`; `status` ∈ `open | mitigated | accepted`. Only `description` is required.

## P8b — Target Date & Dependencies (structured, OPTIONAL)

**target:** `prd.md → target_date` (single ISO date), `depends_on` (list of artifact IDs)

- **EN:**
  - "Is there a target date for this feature-area? Give me a calendar date (YYYY-MM-DD)."
  - "Does this feature wait on any other PRD or epic before it can ship? Name them — I'll record the IDs."
- **VI:**
  - "Mảng tính năng này có ngày mục tiêu không? Cho tôi một ngày lịch (YYYY-MM-DD)."
  - "Tính năng này có phải chờ PRD hay epic nào khác trước khi ra mắt không? Nêu tên — tôi sẽ ghi lại các ID."
- **target_date:** a single `YYYY-MM-DD`. A child due after its parent (or before a prerequisite) warns at validate; overdue-vs-today is advisory only (not a validate gate).
- **depends_on:** a list of existing PRD/epic IDs. An unresolved target is `dep_dangling` (error); a circular chain is `dep_cycle` (error) — so only offer IDs that already exist.

## P8c — Competitive Parity (structured, OPTIONAL)

**target:** `prd.md → competitive_parity:` (mapping `{COMP-ID: ahead|parity|behind|none}`)

Only offered when the BRD declares `competitors:`. For each BRD competitor, ask where this feature-area stands:

- **EN:** "Versus {competitor name}, on this feature-area are we **ahead**, at **parity**, **behind**, or do we **not** play here (none)?"
- **VI:** "So với {tên đối thủ}, ở mảng tính năng này mình **dẫn trước (ahead)**, **ngang bằng (parity)**, **thua kém (behind)**, hay **không tham gia (none)**?"
- **Mode:** per-competitor single-select, pre-populated from the BRD's `competitors:` IDs.
- **Keys are IDs, not names:** each key must resolve to a BRD `COMP-<SLUG>` (else `unknown_ref` error at validate). Never re-declare a competitor here — identity lives once in `brd.md`.
- **parity enum (closed):** `ahead | parity | behind | none`.

## P9 — Open Questions (OPTIONAL)

**target:** `prd.md → OPTIONAL: open_questions`

- **EN:** "What questions are still open — to revisit before sign-off?"
- **VI:** "Còn câu hỏi nào chưa rõ — cần xem lại trước khi phê duyệt?"

## P10 — Horizon & Scope Tag

**target:** `prd.md → horizon`, `scope`

- **EN:** "Is this feature-area NOW (this release), NEXT, or LATER? And is it part of the product's CORE value or just IN scope?"
- **VI:** "Mảng tính năng này thuộc HIỆN TẠI (release này), TIẾP THEO, hay SAU NÀY? Và nó là phần CỐT LÕI của giá trị sản phẩm, hay chỉ NẰM TRONG phạm vi?"

## Adaptivity Rules

- For a small product, allow skipping P5 (NFRs) and P7/P8/P9.
- After P4 + P5, the LLM offers a structural validation pass before continuing.
- Persona-related skip: P2 auto-skips if `PRODUCT.md` has only one persona.
- MoSCoW MoSCoW-gate is mandatory for every PRD (do not let everything be MUST).
- P8a/P8b are layered onto P8: only ask the structured enums/dates after the PO has described deps/risks in P8 prose; reuse those descriptions and ask only the missing structured pieces.
- P8c auto-skips when the BRD declares no `competitors:` — there is nothing to score parity against.
