# Interview — Epic + Story

Question bank for decomposing a PRD into epics and stories. Each story has explicit acceptance criteria; each epic links its parent PRD requirement and BRD goal.

## E1 — Epic Goal

**target:** `epic.md → Goal`

- **EN:** "In one sentence, what does this epic deliver to the user?"
- **VI:** "Trong một câu, epic này mang đến cho người dùng điều gì?"
- **5-Why trigger:** answer is a feature ("login page") not an outcome ("user can sign in to resume their cart").

## E2 — Business Context

**target:** `epic.md → prd_requirement_ref`, `brd_goal_ref`

- **EN:** "Which PRD requirement does this epic implement? Which BRD goal does it advance?"
- **VI:** "Epic này hiện thực yêu cầu PRD nào? Đẩy mục tiêu BRD nào?"
- **Mode:** dual select; pre-populate from the parent PRD's requirements list + `brd_goals`.

## E3 — Epic Success Criteria

**target:** `epic.md → Success Criteria`

- **EN:** "When this epic is done, what observable behavior tells us success?"
- **VI:** "Khi epic này xong, dấu hiệu quan sát được nào nói lên thành công?"

## E4 — Epic Scope

**target:** `epic.md → Scope`

- **EN:** "What's inside this epic, and what's deliberately left out?"
- **VI:** "Bên trong epic này có gì, và rõ ràng bỏ ra ngoài cái gì?"

## E5 — Epic Risks (OPTIONAL)

**target:** `epic.md → OPTIONAL: risks_section` + `risks` frontmatter

- **EN:** "Any specific risks for this epic — impact and likelihood?"
- **VI:** "Có rủi ro cụ thể nào cho epic này — mức ảnh hưởng và khả năng xảy ra?"
- **Mode:** for each risk, ask impact (low/med/high) + likelihood (low/med/high).

---

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
- **VI:** "Cho 2–4 tiêu chí chấp nhận. Dùng dạng Khi / Thì / Sao đó."
- **Templates (EN seed):**
  - "Given {state}, when {action}, then {outcome}."
  - "Given an unauthenticated visitor, when they submit valid credentials, then they reach the home page."
- **Templates (VI seed):**
  - "Khi {trạng thái}, lúc {hành động}, thì {kết quả}."
  - "Khi chưa đăng nhập, lúc nhập thông tin đúng, thì vào trang chủ."
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

## Adaptivity Rules

- E5 risks: skip silently if PRD already lists epic-level risks.
- After each story, ask "another story under this epic, or move to the next epic?"
- AC quality check: if any AC contains a vague phrase, the LLM proposes a quantified rewrite for PO accept/edit.
- Persona inheritance: a story's personas must be a subset of the epic's personas; if PO names a new one, ask whether to add it to the epic too.
