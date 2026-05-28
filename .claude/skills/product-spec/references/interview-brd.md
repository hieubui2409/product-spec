# Interview — BRD

Question bank for drafting/refining the **single** Business Requirements Document. Each question maps to a BRD frontmatter field or section.

## B1 — Problem / Opportunity

**target:** `brd.md → Problem / Opportunity`

- **EN:** "What business opportunity does this product unlock — and what does it cost us not to act?"
- **VI:** "Sản phẩm mở ra cơ hội kinh doanh nào — và nếu không hành động thì mất gì?"
- **5-Why trigger:** answer focuses only on tech, not business.

## B2 — Business Goals (multi)

**target:** `brd.md → goals[]` (each becomes `BRD-G<n>`)

- **EN:** "What are the 2–5 business goals this product must hit? State each as something measurable."
- **VI:** "Có 2–5 mục tiêu kinh doanh nào sản phẩm phải đạt? Phát biểu mỗi mục tiêu có thể đo lường được."
- **Options (seed forms):**
  - "Reach ${amount} ARR in {timeframe}." | "Đạt ${số tiền} ARR trong {thời gian}."
  - "Achieve {n}% repeat-purchase rate." | "Đạt tỷ lệ mua lặp lại {n}%."
  - "Cut {process} time by {n}%." | "Giảm thời gian {quy trình} {n}%."
  - "Acquire {n} customers in {market}." | "Có {n} khách hàng tại {thị trường}."
- **5-Why trigger:** unmeasurable ("delight users").

## B3 — Success Metrics

**target:** `brd.md → metrics`

- **EN:** "For each goal, what metric proves it's been hit?"
- **VI:** "Mỗi mục tiêu cần chỉ số nào để biết đã đạt?"
- **Note:** one metric per goal, max two; force a numeric target.

## B4 — Stakeholders

**target:** `brd.md → stakeholders`

- **EN:** "Who needs to sign off on this product's direction — internally and externally?"
- **VI:** "Những ai cần phê duyệt định hướng — nội bộ và bên ngoài?"

## B5 — Constraints

**target:** `brd.md → constraints`

- **EN:** "What hard constraints bind the product — budget, deadline, regulation, partnerships?"
- **VI:** "Sản phẩm bị ràng buộc bởi điều gì cứng — ngân sách, hạn chót, quy định, đối tác?"

## B6 — Market Context

**target:** `brd.md → market`

- **EN:** "What's the competitive landscape — who's already in this space, and how are we different?"
- **VI:** "Bối cảnh cạnh tranh ra sao — ai đã có mặt và mình khác như thế nào?"

## B7 — Assumptions & Risks (OPTIONAL)

**target:** `brd.md → OPTIONAL: assumptions_risks`

- **EN:** "What assumptions does the plan depend on — and what kills the plan if wrong?"
- **VI:** "Kế hoạch dựa vào giả định gì — điều gì sai sẽ khiến kế hoạch sụp đổ?"

## Adaptivity Rules

- B2 + B3: ask together (goal + metric pair) to keep traceability tight.
- Cap goals at 5 (soft). If PO names more, ask "which 3 are non-negotiable for the next 12 months?"
- Skip B7 if PO has already mentioned constraints exhaustively in B5.

## MoSCoW Hook (consumed by PRD bank)

After B2, the LLM offers an optional MoSCoW pass for the goals: "Which goals are MUST for this release, vs SHOULD/COULD/WONT?" — but goals stay status-only; MoSCoW is only meaningful at the PRD requirements layer.
