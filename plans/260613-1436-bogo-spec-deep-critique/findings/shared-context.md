# Shared Context — Deep Critique of the BoGo Product Spec

**You are critiquing a REAL product spec authored by a non-technical Product Owner (PO).**
Spec root: `/home/hieubt15/Documents/vsf/bogo-product-spec/docs/product/`
Authored with the `product-spec` toolkit **v2.0.0** (current toolkit is v2.4.0 — version gap matters, see §5).

Read this whole file first. Then read ONLY the artifact files assigned to you (paths in your task prompt).

---

## 1. What BoGo is (product summary)

BoGo = a Vietnamese **SaaS management platform for small & medium businesses (SMEs)**. One app that
unifies **HR/payroll + task management + internal communication + a Vietnamese AI assistant**, multi-tenant
(each org's data fully separated). Pre-commercial (no paying org yet).

- **North Star:** số tổ chức hoạt động tích cực hằng tuần (org has ≥60% staff active/week). Target: 100 active orgs in 12 months, ≥70% activation rate.
- **Personas (5):** `ORG_ADMIN` (org admin), `EXEC` (leadership), `DEPT_MGR` (dept manager), `STAFF` (employee), `PLATFORM_ADMIN` (BoGo-side platform ops).
- **Horizons:** now (0–3mo MVP), next (3–6mo), later (6–12mo).
- **Vision's 3 platform promises:** (1) each org its own isolated space; (2) the org chart is the backbone (multi-dept, multi-level); (3) **self-service** — new orgs self-register, self-configure, self-operate with no BoGo manual intervention.

## 2. Spec inventory (what exists)

VISION (approved v0.4.0) · BRD (3 goals, 8 competitors) · **9 PRDs / 21 epics / 80 stories**.

| PRD | Title | Horizon | Epics | Stories |
|-----|-------|---------|-------|---------|
| PRD-HR | Quản trị nhân sự & lương | now | 3 | 14 |
| PRD-TASK | Giao việc | now | 4 | 14 |
| PRD-COMM | Giao tiếp nội bộ | now | 3 | 14 |
| PRD-AI | Trợ lý ảo AI | now | 2 | 13 |
| PRD-PLATFORM | Nền tảng SaaS: gói, thanh toán & khởi tạo tổ chức | now | 3 | 8 |
| PRD-SUPPORT | Hỗ trợ khách hàng | now | 1 | 3 |
| PRD-APPROVAL | Quản lý phê duyệt | next | 1 | 5 |
| PRD-RESOURCE | Tài nguyên tổ chức (hồ sơ & tài liệu) | next | 1 | 4 |
| PRD-REPORT | (đang tái cấu trúc — DEC-45) | — | 3 | 5 |

BRD goals: **G1** tăng trưởng số tổ chức active · **G2** nâng hiệu quả quản trị cho tổ chức · **G3** kích hoạt thành công & giữ chân tổ chức.

## 3. KNOWN issues — already found in the prior validation report (DO NOT just re-report these)

The PO already ran a validate pass (`validation-report-20260610T132709Z.md`). It already found & fixed 3 content
contradictions (DEC-45/49 fallout) and logged these OPEN/accepted items. **Only mention an item below if you can
ESCALATE it with a NEW consequence or a sharper fix. Otherwise spend your effort on NEW findings.**

- **[GAP-ORG] (biggest known gap):** VISION promises org self-service (self-signup, build multi-level org chart,
  bulk-create accounts, role permissions); BRD-G1/G3 bet on it; AI-E2-S5 walks ORG_ADMIN through it — **but no story
  builds those screens.** PLATFORM_ADMIN has almost nothing (1 kill-switch AC). HR-E1-S6 manages *employee* records,
  not *org* setup.
- Accepted warnings: persona count 5>4 (intentional); PRD-AI-E1 & PRD-HR-E1 high-risk ratio (accepted at DEC-49);
  PRODUCT.md missing `core_value`; INVEST overloads (AI-E2-S4 mini-LMS in one story; HR-E1-S6 has 11 AC);
  3 vague AC ("thông báo lỗi rõ ràng" HR-E1-S1, COMM-E2-S1; "trả lời ngắn gọn" AI-E2-S5);
  Excel export in 3 places (HR-E1-S4, HR-E2-S2, TASK-E4-S4); 7 competitors but no PRD declares `competitive_parity`.

## 4. Deterministic structural verdict (already computed — this is your ammo, don't recompute)

Ran the v2.4.0 structural checkers on the spec:
- **Traceability: 0 errors. Dead links: 0. Dependency cycles: 0. Fence: clean. Matrix: complete.** The graph is structurally healthy.
- Consistency: **145 findings, but 140 are version-drift, NOT defects:**
  - `bad_version_format` ×60 — artifacts use two-part versions (`0.4`, `0.5`); v2.4.0 wants three-part semver. **Cosmetic. One bulk fix.**
  - `misplaced_parent_field` ×80 — every story carries `prd:`+`brd_goals:` in frontmatter; v2.4.0 says a story's only parent edge is `epic`. **Low-severity DRY/drift smell, bulk-fixable.**
  - The only "real" structural signals both toolkit versions agree on: 3× `risk_high_ratio`, 2× `persona_cap` — all already accepted.

**Implication:** the machine-checkable layer is basically exhausted. Real improvements now must come from
**human judgment** — your lens. Look for things a script CANNOT see.

## 5. Version-compare facts (for the tooling-gap angle)

- bogo authored on **product-spec v2.0.0**; current toolkit is **v2.4.0**. (MANIFEST says "1.1.0" — that's the release label, ignore it.)
- v2.4.0's `check_consistency_schema.py` (the source of the 140 drift findings) **does not exist in v2.0.0** — the PO's
  tooling was structurally blind to version-format & parent-field normalization.
- v2.4.0 adds (that v2.0.0 lacked): `check_consistency_product`, `open_questions`, `change_log_writer`, snapshot/restore,
  audit-trail, outcomes/learning, id-backfill migration.
- If you spot a spec problem that a *tooling feature* (existing or missing) should have caught, FLAG it as a tooling-gap.

## 6. How to report each finding (MANDATORY format)

Return findings as structured items. Each finding MUST have:
- `id`: short slug (e.g. `prod-ai-overreach-1`)
- `lens`: product | tech | market | craft | spine | tooling
- `severity`: blocker | high | medium | low
- `scope_id`: the artifact ID it targets (e.g. `PRD-AI-E2-S4`)
- `evidence`: `<ARTIFACT-ID>:<line>` — you MUST open the actual `.md` file and use a REAL line number. Never guess.
- `title`: one plain-language line (Vietnamese)
- `why_it_dies`: the concrete product/market/build consequence if left as-is (Vietnamese, plain language)
- `fix`: a specific, actionable fix (Vietnamese, plain language)
- `is_known`: true if it overlaps a §3 known item (then your `why`/`fix` MUST add something new), else false

## 7. Tone (the PO is non-technical)

Write findings in **plain Vietnamese, low jargon**. Be direct and honest about severity — don't soften real problems —
but explain the *consequence in business terms*, not framework names. No gratuitous sarcasm. Every finding earns its
place with evidence + why + fix. If something is genuinely fine, don't invent a problem.
