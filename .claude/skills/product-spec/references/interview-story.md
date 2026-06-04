# Interview — Story

Question bank for decomposing an epic into stories. Each story has explicit acceptance criteria and inherits its personas from the parent epic. Epic capture is a separate pass — see `interview-epic.md`.

> **Probing depth** is set by `interview_rigor` (light/standard/deep) — `deep` challenges each unproven
> claim and hunts missing acceptance criteria / edge cases here too. The knob→behaviour home is the
> **Engagement profile** section in `workflow-interview.md`; this pass just obeys it (no duplicated table).

## Story Block

For each story under the epic:

## S1 — User Story Statement

**target:** `story.md → Story body` (As-a / I-want / so-that)

- **EN:**
  - "Which persona is this for?"
  - "What do they want to do?"
  - "So that what? (the outcome)"
- **VI:**
  - "Story này dành cho persona nào?"
  - "Họ muốn làm gì?"
  - "Để làm gì? (kết quả)"
- **Composition:** combine into "As a {persona}, I want {want}, so that {outcome}."

## S2 — Acceptance Criteria

**target:** `story.md → acceptance_criteria` (list)

- **EN:** "Give 2–4 acceptance criteria. Use the Given / When / Then form."
- **VI:** "Cho 2–4 tiêu chí chấp nhận. Dùng dạng Giả sử / Khi / Thì (Given/When/Then)."
- **Templates (EN seed):**
  - "Given {state}, when {action}, then {outcome}."
  - "Given an unauthenticated visitor, when they submit valid credentials, then they reach the home page."
- **Templates (VI seed):**
  - "Giả sử {trạng thái}, khi {hành động}, thì {kết quả}."
  - "Giả sử khách chưa đăng nhập, khi nhập đúng thông tin, thì vào được trang chủ."
- **5-Why trigger:** AC contains "should", "easy", "fast" without numbers; ask for an observable test.

## S3 — Size

**target:** `story.md → size`

- **EN:** "How big is this story — S (a day or so), M (a week), L (more than a week)?"
- **VI:** "Story này lớn cỡ nào — S (khoảng một ngày), M (một tuần), L (hơn một tuần)?"
- **Note:** size is a PO-level T-shirt, NOT story points. No engineering-unit estimation.

## S4 — Personas (subset of epic)

**target:** `story.md → personas`

- **EN:** "Which persona(s) experience this story?"
- **VI:** "Persona nào trải nghiệm story này?"
- **Mode:** multi-select pre-populated from the epic's `personas`.

## S5 — Notes / Dependencies (OPTIONAL)

**target:** `story.md → OPTIONAL: notes`, `OPTIONAL: dependencies`

- **EN:** "Anything else worth recording — design notes, dependencies on other stories?"
- **VI:** "Còn gì đáng ghi nhận không — ghi chú thiết kế, phụ thuộc story khác?"

## Adaptivity Rules (story)

- After each story, ask "another story under this epic, or move to the next epic?"
- AC quality check: if any AC contains a vague phrase, the LLM proposes a quantified rewrite for PO accept/edit.
- Persona inheritance: a story's personas must be a subset of the epic's personas; if PO names a new one, ask whether to add it to the epic too.
