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
- **VI:** "Có 2–5 mục tiêu kinh doanh nào sản phẩm phải đạt? Nêu mỗi mục tiêu dưới dạng có thể đo lường được."
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
- **VI:** "Sản phẩm bị ràng buộc chặt bởi điều gì — ngân sách, hạn chót, quy định, đối tác?"

## B6 — Market Context (narrative)

**target:** `brd.md → market`

- **EN:** "What's the competitive landscape — who's already in this space, and how are we different?"
- **VI:** "Bối cảnh cạnh tranh ra sao — ai đã có mặt và mình khác như thế nào?"

## B6a — Competitors (structured, OPTIONAL)

**target:** `brd.md → competitors:` (each entry `{id: COMP-<SLUG>, name, url, threat}`) — the DRY identity home for `COMP-<SLUG>` IDs; PRDs only reference these via `competitive_parity`.

For each named competitor, capture:

- **EN:**
  - "Name a direct competitor. (I'll assign it an ID like `COMP-SHOPIFY`.)"
  - "What's their public site URL? (If you'd rather not record it, say so — I'll prefix it `private:` so it never leaves your docs.)"
  - "How big a threat are they — **low / med / high**?"
- **VI:**
  - "Nêu một đối thủ trực tiếp. (Tôi sẽ gán ID dạng `COMP-SHOPIFY`.)"
  - "URL trang công khai của họ? (Nếu không muốn ghi lại, cứ nói — tôi sẽ thêm tiền tố `private:` để nó không rời khỏi tài liệu của bạn.)"
  - "Mức độ đe doạ của họ — **thấp (low) / trung bình (med) / cao (high)**?"
- **ID rule:** slug = uppercase ASCII/digits derived from the name (`Big Cartel` → `COMP-BIGCARTEL`). Same slug rules as a PRD.
- **OpSec note:** a `url` beginning `private:` is dropped before it reaches the graph/render — offer this opt-out explicitly.
- **threat enum:** `low | med | high` (closed). Drives the competition viz threat heatmap.

## B7 — Assumptions & Risks (narrative, OPTIONAL)

**target:** `brd.md → OPTIONAL: assumptions_risks`

- **EN:** "What assumptions does the plan depend on — and what kills the plan if wrong?"
- **VI:** "Kế hoạch dựa vào giả định gì — điều gì sai sẽ khiến kế hoạch sụp đổ?"

## B7a — Structured Risks (OPTIONAL)

**target:** `brd.md → risks:` (each entry `{description, impact, likelihood, status, mitigation}`)

For each risk the PO names, capture the four enums + mitigation:

- **EN:**
  - "Describe the risk in one line."
  - "If it happens, how bad is the **impact** — low / med / high?"
  - "How **likely** is it — low / med / high?"
  - "What's its **status** — open, mitigated, or accepted?"
  - "What's the **mitigation** — what would you do about it?"
- **VI:**
  - "Mô tả rủi ro trong một câu."
  - "Nếu xảy ra, mức **ảnh hưởng** thế nào — thấp (low) / trung bình (med) / cao (high)?"
  - "Khả năng **xảy ra** ra sao — thấp (low) / trung bình (med) / cao (high)?"
  - "**Trạng thái** của nó — chưa xử lý (open), đã giảm thiểu (mitigated), hay chấp nhận (accepted)?"
  - "**Cách giảm thiểu** — bạn sẽ làm gì với nó?"
- **Enums (closed):** `impact`/`likelihood` ∈ `low | med | high`; `status` ∈ `open | mitigated | accepted` (a risk status, distinct from an artifact's `draft | review | approved`).
- **Note:** only `description` is strictly required; if the PO skips an enum, leave it unset rather than guessing. A top-heavy register (>50% `impact: high`) and a sizeable feature with zero risks both warn at validate.

## Adaptivity Rules

- B2 + B3: ask together (goal + metric pair) to keep traceability tight.
- Cap goals at 5 (soft). If PO names more, ask "which 3 are non-negotiable for the next 12 months?"
- Skip B7 if PO has already mentioned constraints exhaustively in B5.
- B6a (competitors) is optional and only offered after B6; skip silently if the PO says there are no direct competitors worth tracking. Each competitor named in the B6 narrative should be offered an ID so a PRD can reference it.
- B7a (structured risks) layers enums onto B7; if the PO has already named risks in B7 prose, reuse those descriptions and only ask the missing enums. Do not invent a risk the PO never raised.

## MoSCoW Hook (consumed by PRD bank)

After B2, the LLM offers an optional MoSCoW pass for the goals: "Which goals are MUST for this release, vs SHOULD/COULD/WONT?" — but goals stay status-only; MoSCoW is only meaningful at the PRD requirements layer.
