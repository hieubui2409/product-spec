# Interview — Vision

Question bank the skill uses to draft `vision.md` and the labels in `PRODUCT.md`. Each question is tagged with the artifact + field it fills, has an EN and a VI form, and notes any 5-Why follow-up trigger.

The LLM composes `AskUserQuestion` calls from these records and skips questions already answered by an existing `PRODUCT.md`. Persona cap: soft 2–4.

## V1 — Problem

**target:** `vision.md → Problem Narrative`, `PRODUCT.md → one_line_description`

- **EN:** "In one sentence, what problem does this product solve for whom?"
- **VI:** "Trong một câu, sản phẩm này giải quyết vấn đề gì cho ai?"
- **Options (PO-friendly seed):**
  - "Helps {who} do {task} without {pain}." | "Giúp {ai} làm {việc} mà không phải {khó khăn}."
  - "Replaces {legacy} with a simpler way." | "Thay thế {cách cũ} bằng cách đơn giản hơn."
  - "Connects {group A} with {group B}." | "Kết nối {nhóm A} với {nhóm B}."
- **5-Why trigger:** answer is vague (e.g., "make X better").

## V2 — Personas

**target:** `vision.md → Personas`, `PRODUCT.md → personas` (labels)

- **EN:** "Who are the 2–4 main types of people who will use this product?"
- **VI:** "Sản phẩm này có 2–4 nhóm người dùng chính nào?"
- **Mode:** multi-select with custom add. Cap at 4 (soft).
- **5-Why trigger:** PO names more than 4 personas → ask which two are the primary buyers.

## V3 — Value Proposition

**target:** `vision.md → Value Proposition`, `PRODUCT.md → core_value`

- **EN:** "What's the one thing this product does better than the alternative — the line we'd put on the homepage?"
- **VI:** "Sản phẩm làm tốt nhất điều gì so với phương án khác — câu in trên trang chủ?"
- **Options (formula seeds):**
  - "For {persona}, this is the only product that {claim}." | "Đối với {persona}, đây là sản phẩm duy nhất {tuyên bố}."
  - "We let {persona} {result} in {time}." | "Chúng tôi giúp {persona} đạt {kết quả} trong {thời gian}."
- **5-Why trigger:** marketing-speak without a concrete claim ("the best", "world-class").

## V4 — North-Star Metric

**target:** `vision.md → North-Star Metric`

- **EN:** "If you could track exactly one number that says the product is winning, what is it?"
- **VI:** "Nếu chỉ chọn một chỉ số duy nhất cho thấy sản phẩm đang thắng thế, đó là chỉ số gì?"
- **Options (PO-friendly):**
  - "Active users per week" | "Người dùng hoạt động mỗi tuần"
  - "Repeat purchase rate" | "Tỷ lệ mua lặp lại"
  - "Time saved per customer per task" | "Thời gian tiết kiệm cho mỗi khách / tác vụ"

## V5 — Direction

**target:** `vision.md → 1–3 Year Direction`, `PRODUCT.md → roadmap_one_liner`

- **EN:** "Looking 1–3 years out, what bigger picture does this product fit into?"
- **VI:** "Nhìn 1–3 năm tới, bức tranh lớn của sản phẩm là gì?"

## V6 — Current Implementation

**target:** `PRODUCT.md → current_implementation`

- **EN:** "Where are we today — concept, prototype, MVP, in-market?"
- **VI:** "Hiện tại đang ở đâu — ý tưởng, prototype, MVP, đã ra thị trường?"

> Note: an earlier V6 asked the PO to set `vision.horizon`. The vision template
> intentionally omits `horizon` (vision is timeless strategy — horizon belongs
> on PRDs/epics/stories). The horizon question was removed to stop collecting
> an answer that would land nowhere.

## V7 — Deployment

**target:** `PRODUCT.md → deployment`

- **EN:** "Where does it live — web, mobile, on-prem, cloud?"
- **VI:** "Sản phẩm chạy ở đâu — web, mobile, on-prem, cloud?"

## Adaptivity Rules

- Skip if `PRODUCT.md` already has the field filled and the PO hasn't asked to redo it.
- 5-Why follows a vague answer: ask "why" up to 3 times; on the 3rd, propose a concrete reformulation for the PO to accept/reject.
- VI questions are translations of the EN form; never localize the field tag.
