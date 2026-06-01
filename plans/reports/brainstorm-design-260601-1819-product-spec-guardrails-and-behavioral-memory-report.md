---
type: brainstorm-design
date: 2026-06-01
slug: product-spec-guardrails-and-behavioral-memory
status: proposal
owner: hieubt
scope: product-spec (guidance/guardrails + behavioral memory) · claude-pack impact = near-zero (auto-ship)
method: workflow fan-out (5 read-only readers) → inline synthesis
references_read:
  - .claude/skills/fix · ck-plan · cook (ck patterns, read-only)
  - .claude/rules/*.md (ck dev rules, read-only)
  - .claude/skills/product-spec/{SKILL.md, references/*, CLAUDE.md block}
  - .claude/skills/claude-pack/{SKILL.md, scripts/*}, .claude/pack.manifest.yaml
  - plans/reports/brainstorm-design-260601-1754-product-spec-memory-layer-application-report.md
related:
  - .claude/agent-memory/ (ck precedent, reference-only)
---

# Brainstorm Design — product-spec: Guardrails bổ sung + Behavioral memory

> Tiếp nối series memory-layer. Phiên này trả lời 2 câu hỏi: **(1)** skill có cần bổ sung chỉ-dẫn/ràng-buộc
> không (drift, lẫn spec-vs-code, triết lý, protocol)? **(2)** thiết kế memory bắt **hành vi/thói quen/lỗi/giọng văn**
> của PO/LLM. + khoanh vùng **impact**. Đối chiếu ck:fix/ck:plan/cook + ck `.claude/rules` (read-only, KHÔNG sửa).
> CHƯA code — advisory.

---

## 0. TL;DR

1. **Có, cần bổ sung — và đa số là gap thật.** 4 guardrail PO yêu cầu: **Q3 (triết lý)** + **Q4 (protocol)** đã *mạnh*;
   **Q1 (redirect off-topic)** gần như **chưa có**; **Q2 (lẫn spec-vs-code)** *mỏng & một chiều* (chỉ CLAUDE.md, chỉ
   câu "write the API"). → 2 gap HIGH.
2. **Phát hiện đắt nhất:** rule **"When to Ask vs Assume"** + nhiều guardrail PO-facing **đang nằm ở repo-root
   `CLAUDE.md` (dev-facing)** — mà **claude-pack KHÔNG bundle file này** → bản install **mất** rule. Fix = *nhấc rule
   vào trong skill* (SKILL.md/references), KHÔNG sửa file ngoài.
3. **No-silent-reversal hiện chỉ bảo vệ `approved`.** ck rule bảo vệ **mọi quyết định PO đã xác nhận** (kể cả draft ghi
   trong `.session.md`). `--update`/`--auto` có thể *regenerate mất* một scope-decision draft mà không surface → gap HIGH.
4. **Behavioral memory = 2 store MỚI**, tách bạch: **3D PO-style** (giọng/từ vựng/hay-hỏi → định hình *prose*, commit,
   lang-keyed) vs **3E LLM-self-correction** (lỗi lặp/trượt protocol → tự-guard *hành vi*, gitignore). KHÔNG nhét vào
   `preferences.yaml` (enum đóng, sai semantics).
5. **Impact gần như chỉ trong product-spec, toàn doc/prose** (0 script cho phần guidance). **claude-pack auto-ship**
   mọi file mới trong `references/` (manifest list theo *slug*, rglob cả thư mục) → **0 sửa manifest**. File ngoài skill:
   **không sửa** (ck rules read-only; repo-root CLAUDE.md = nguồn để *nhấc rule ra*, không phải để sửa).
6. **ck pattern đáng bê nguyên** (ROI cao, rủi ro ~0): **Anti-Rationalization table** + **Whole-Tree Consistency Sweep**
   gate. Pattern engineering-only (prevention-gate test, pre-state re-run, 0-delegations, 3-strikes) **KHÔNG** chuyển —
   giữ skill PO non-technical.

---

## 1. Phần A — Gap chỉ-dẫn/guardrail (câu hỏi "skill có cần bổ sung không")

### 1.1 Bốn guardrail PO yêu cầu — trạng thái hiện tại

| Guardrail | Trạng thái | Bằng chứng | Gap |
|---|---|---|---|
| **Q1. Redirect khi PO lạc đề (off product-scope)** | **Gần như CHƯA có** | Có discipline *trong-spec* (MoSCoW gate, gold_plating, core_value_drift, 5-Why) nhưng KHÔNG có chỉ-dẫn xử lý hội thoại lạc khỏi domain (chit-chat, hỏi kỹ thuật rời rạc, "viết hộ cái email") | **HIGH** |
| **Q2. Không lẫn spec-work với viết code** | **Mỏng & một chiều** | Chỉ `CLAUDE.md → What This Skill Does NOT Do → No code generation`, chỉ cho câu "write the API". KHÔNG ở SKILL.md, KHÔNG ở reference. KHÔNG phủ case "spec bị copy vào repo code → PO nhờ viết code" | **HIGH** |
| **Q3. Bám triết lý sản phẩm (vocab PO, non-technical)** | **MẠNH** | `CLAUDE.md:6-7`, `SKILL.md:162`, no-eng-jargon, size S/M/L không story-point (`interview-epic-story.md:97`) | Thiếu redirect khi *PO tự* trượt sang eng-framing (đòi DB schema/story point) → MED |
| **Q4. Tuân thủ protocol/workflow** | **MẠNH** | scripts-first (`CLAUDE.md` P3, `workflow-validate.md:131`), frontmatter source-of-truth (P1), no-silent-reversal (P4), DRY (P2) | Thiếu câu "4 luật này áp dụng MỌI lượt, kể cả no-flag chat" → LOW |

### 1.2 ck pattern đáng bê (đối chiếu ck:fix/ck:plan/cook + ck rules)

| Pattern (nguồn) | Áp dụng vào product-spec | Ưu tiên |
|---|---|---|
| **Anti-Rationalization table** (`fix/SKILL.md:79-90`) | Bảng "ý nghĩ tắt → phản biện": *"PO đã biết họ muốn gì, bỏ qua interview"→"persona/scope ngầm gây rework"*; *"AC hiển nhiên, khỏi viết"→"INVEST cần AC tường minh"*. Bê thẳng vào CLAUDE.md block | **HIGH** (ROI cao, rủi ro ~0) |
| **Whole-Tree Consistency Sweep gate** (`ck-plan/SKILL.md:263-270`) | Sau `--update`/edit: re-scan TOÀN tree tìm cross-ref cũ (persona gỡ khỏi PRODUCT.md vẫn được PRD trích; goal đổi chữ nhưng story còn quote cũ); block tới khi 0 mâu thuẫn. **Đóng gap thật của delta-propagation** | **HIGH** |
| **Lift "When to Ask vs Assume" vào skill** (`review-audit-self-decision.md` ↔ repo CLAUDE.md) | Rule đang ở dev-CLAUDE.md, KHÔNG ship → install mất. Nhấc vào `SKILL.md`/`workflow-interview.md` | **HIGH** |
| **Mở rộng no-silent-reversal → mọi PO-confirmed answer** (`review-audit-self-decision.md:23-40`) | Hiện chỉ chặn `approved`. Bảo vệ cả quyết định draft PO ghi trong `.session.md` khỏi bị `--update`/`--auto` xóa âm thầm | **HIGH** |
| **Scout-first-ask-second / confidence gate** (`review-audit-self-decision.md:42-57`) | Nửa thiếu của "ask-vs-assume": *resolve-from-spec TRƯỚC khi hỏi PO*. Đọc artifact + cite ID; chỉ hỏi khi spec im lặng / 2 approved mâu thuẫn / là business-judgment. Giảm over-ask | MED |
| **Verified/decided-is-sticky** (`review-audit-self-decision.md:3-10`) | LLM judgment check (core_value_drift, gold_plating) **re-derive mỗi `--validate`, không nhớ PO đã phán** → nag lại cùng cảnh báo. Ghi PO-ruling + suppress-unless-changed. **Nối thẳng behavioral/judgment-cache** | MED |
| **Named HARD-GATE framing** (XML-fenced, `fix/SKILL.md:25-77`) | Bọc P4 + "Never assume" thành gate tường minh: refusal + override + escalation | MED |
| **Validation Log schema** (`ck-plan/validate-question-framework.md:64-67`) | Ghi verbatim: full question + mọi option + verbatim "Other" + rationale + session# → audit trail resume-safe, gia cố `.session.md`/`change-log.md` | MED |
| **Scope Challenge + RESPECT-IT lock** (`ck-plan/scope-challenge.md:67-76`) | Step-0 mỗi PRD: chọn MVP/full/strip + complexity-smell (quá nhiều epic/story) rồi **LOCK** → chặn gold-plating *chủ động* thay vì bắt ở `--validate` | MED |
| **Consolidated guardrails reference** | `references/guardrails-and-boundaries.md` gom off-topic-redirect + no-code-redirect + philosophy-anchor + protocol-recap; link vào pointer table để **load bất kể flag** | MED |
| **Authoritative diagram overrides prose** (`fix/SKILL.md:116`) | 1 mermaid flow "(Authoritative)" mỗi flag-family (interview/validate/export) → giải drift prose giữa các reference dài | MED |
| Override-with-surfaced-risk (`cook/SKILL.md:85`) | PO bỏ qua confirmation = **surface risk**, không bỏ âm thầm | LOW |

**KHÔNG chuyển (giữ skill non-technical):** prevention-gate regression test · pre-state capture+re-run · "0-delegations=INCOMPLETE" · 3-strikes-question-architecture · DONE/BLOCKED status enum · context-isolation. Tất cả engineering/subagent-internal.

---

## 2. Phần B — Behavioral memory (câu hỏi "bắt hành vi/thói quen/lỗi/giọng")

`preferences.yaml` (store 3B của memory report) là **config enum đóng** (lang/detail/prioritization) — **KHÔNG** chứa
được giọng/từ-vựng/lỗi (sai schema + sai semantics: prefs *seed default câu hỏi*, behavioral *định hình prose/guard hành
vi*). → cần **2 store MỚI**, dùng đúng rubric 7-dòng của report cũ (purpose/file/format/DRY-guard/read/write/split):

### 3D. PO-STYLE memory — định hình *output*

| | |
|---|---|
| **Mục tiêu** | Bắt *cách PO giao tiếp* để prose + AskUserQuestion khớp register của họ |
| **File** | `docs/product/.memory/po-style.yaml` (hoặc `po-voice.md`) · **committed** (PO-authored intent) |
| **Nội dung** | register (terse/narrative, formal/casual) · **từ vựng riêng** (PO nói "khách vãng lai" ≠ "guest user") · **hay-hỏi** ("luôn thêm dòng metric", "luôn tách mobile/web") · do/don't phrasing |
| **DRY guard** | Định hình **PHRASING ONLY**, KHÔNG re-home structural fact (persona label vẫn ở PRODUCT.md), KHÔNG đụng AC. Frontmatter vẫn thắng (như prefs) |
| **Bilingual** | **Lang-keyed** (en/vi) — register vi ≠ en; tránh giọng en rò vào prose vi |
| **Read** | Bước sinh prose: vision narrative, story description, text AskUserQuestion (`workflow-interview.md`) |
| **Write** | LLM quan sát qua các vòng interview + khi **PO sửa wording** generated |
| **Split** | LLM-owned (quan sát + áp dụng = judgment); script chỉ đọc/ghi file + validate shape |

### 3E. LLM-SELF-CORRECTION memory — guard *hành vi*

| | |
|---|---|
| **Mục tiêu** | Bắt *lỗi lặp của LLM* với luật skill → tự-guard phiên sau |
| **File** | `docs/product/.memory/self-corrections.json` · **gitignore** (session-derived, không phải PO intent; + privacy) |
| **Nội dung** | mô tả slip · luật bị vi phạm (cite 5 Principle: "ghi ngoài docs/product/"=F1; "auto-flip approved"=no-silent-reversal; "suy structure từ heading"=P1; "set approved không qua --approve"=sign-off) · tần suất/last-seen · reminder sửa |
| **DRY guard** | Internal guardrail, KHÔNG user-facing voice. Honesty §soft-fence: **giảm tái phạm, KHÔNG block cứng** |
| **Read** | Pre-flight self-check trước thao tác rủi ro (trước Write → check slip fence cũ → gia cố F1) |
| **Write** | Khi `check_fence.py` / contradiction-protocol / PO **bắt được** vi phạm |
| **Split** | LLM viết entry + rút bài học; **script DETECT structural slip** (`check_fence.py` đã quét file-ngoài-docs/product) feed candidate |

**Phân biệt cốt lõi (đừng gộp):** 3D định hình **WORDING ra ngoài** · 3E guard **BEHAVIOR bên trong**. Khác read-trigger
(prose-gen vs pre-Write), khác git posture (commit vs gitignore).

**Từ `.claude/agent-memory` (ck, reference-only):** *bê KHÁI NIỆM* (per-actor persisted learnings, gitignore,
failure-pattern recall — `team/SKILL.md:322-325`); **bỏ LOCATION** (`.claude/agent-memory/<name>/` — product-spec ghi
DUY NHẤT trong `docs/product/`). Lưu ý: agent-memory bị `safety-rules.md:32` xem là "leaks transcripts → always-drop" →
3E phải theo posture gitignore/never-ship tương tự.

**Cảnh báo trigger (quan trọng):** nếu KHÔNG định nghĩa write-trigger rõ → store **rỗng vĩnh viễn** (đúng như scaffold
`.claude/agent-memory/` đang trống). Trigger là phần thịt, không phải schema.

---

## 3. Phần C — Khoanh vùng & ước lượng impact

### 3.1 product-spec (toàn bộ doc/prose — 0 script cho guidance)

| Surface | Thay đổi | Loại |
|---|---|---|
| `CLAUDE.md` (block product-spec) | Anti-Rationalization table · Q1 off-topic principle · named-GATE cho P4/"never assume" · "áp dụng mọi lượt" note · Output Layout thêm `.memory/` 3D/3E | prose |
| `SKILL.md` | bullet "spec-only, no-code redirect" · nhấc "When to Ask vs Assume" · scout-first-ask-second | prose |
| `references/guardrails-and-boundaries.md` **(MỚI)** | gom off-topic + no-code + philosophy-anchor + protocol-recap; link vào pointer table (load bất kể flag) | prose |
| `references/workflow-interview.md` | Step-0 Scope Challenge + lock · scout-first-ask-second · 3D style read/write · eng-jargon→product reframe | prose |
| `references/workflow-validate.md` | Validation Log schema · verified-sticky (suppress ruled drift) · 3E self-correction write-trigger | prose |
| `references/workflow-auto-and-update.md` | Whole-Tree Consistency Sweep gate · mở rộng no-silent-reversal → confirmed-draft answer | prose |
| `references/interview-frameworks.md` | "Reframe eng asks in product terms" cạnh 5-Why | prose |
| memory report `…-1754-…` §3, §0 | thêm 3D/3E + scope table | doc |
| `scripts/check_fence.py` (đã đề xuất ở report cũ) | feed candidate cho 3E (khi build) | script (đã trong scope memory) |

### 3.2 claude-pack — **near-zero**

- **Auto-ship:** manifest list skill theo **slug** (`pack.manifest.yaml:7-9`), `selection.py:35` rglob **cả thư mục skill** → mọi `references/*.md` mới + SKILL.md mở rộng **ship tự động, 0 sửa manifest**. (Tương phản: agents/rules/hooks list từng-file → mới cần sửa manifest.)
- **Runtime memory PO** (`docs/product/.memory/`, `decisions.md`) **NGOÀI scope packer** — packer chỉ walk `root/.claude`, scanner default `--scan .claude` (`safety_check.py:265`). Không ship, không cần drop.
- **0 sửa** `pack.manifest.yaml`, **0 sửa** `safety_check.py`. Ngoại lệ DUY NHẤT (med, *chỉ nếu*): nếu sau này thêm **runtime-state dir UNDER skill** (`.claude/skills/product-spec/<state>/`) → rglob auto-ship → phải đặt tên trùng drop-dir hoặc thêm `ALWAYS_DROP_DIRS` (`safety_check.py:42-47`). Hiện **không có** nhu cầu đó (3D/3E nằm ở `docs/product/`).
- Optional (low): 1 dòng clarify ở `claude-pack/references/safety-rules.md` rằng `docs/product/` là PO-output ngoài scope packer.

### 3.3 File ngoài skill — **KHÔNG sửa**

| File ngoài | Quyết định |
|---|---|
| `.claude/rules/*.md` (ck dev rules) | **Read-only, MUST NOT sửa** — ck cài cho dev, update sẽ đè |
| repo-root `CLAUDE.md` (dev-facing) | **Không sửa** — đây là *nguồn để NHẤC rule PO-facing VÀO skill*, không phải đích sửa. (Đang chứa "When to Ask vs Assume" mà install bị mất) |
| `.claude/agent-memory/` (ck) | Reference-only — bê concept, bỏ location |
| `pack.manifest.yaml` / `safety_check.py` | 0 sửa (auto-ship; xem 3.2) |

→ **Kết luận impact:** thay đổi **đóng khung trong product-spec**, **toàn prose/doc** cho phần guidance; behavioral 3D/3E
nối vào memory-layer plan đã có (chỉ 3E đụng `check_fence.py` vốn đã trong scope đó). claude-pack & file ngoài: **0 sửa
bắt buộc**.

---

## 4. Khuyến nghị ưu tiên (ROI ÷ rủi ro)

| # | Việc | Ưu tiên | Vì sao |
|---|------|---------|--------|
| 1 | Anti-Rationalization table (CLAUDE.md) | **HIGH** | ROI cao nhất, rủi ro ~0, bê thẳng |
| 2 | Q1 off-topic redirect + Q2 spec-vs-code refuse → `guardrails-and-boundaries.md` + SKILL.md | **HIGH** | 2 gap thật, đúng nỗi đau PO nêu |
| 3 | Mở rộng no-silent-reversal → confirmed-draft answer (`workflow-auto-and-update.md`) | **HIGH** | `--update`/`--auto` đang xóa âm thầm quyết định draft |
| 4 | Whole-Tree Consistency Sweep gate (`workflow-auto-and-update.md`) | **HIGH** | Đóng gap stale cross-ref delta-propagation |
| 5 | Nhấc "When to Ask vs Assume" vào skill | **HIGH** | Install đang mất rule |
| 6 | Behavioral 3D + 3E vào memory report | **HIGH** | Câu hỏi #2 của PO; thiết kế-from-scratch |
| 7 | scout-first-ask-second · verified-sticky · Validation Log · Scope-Challenge lock · named-GATE · guardrails-reference · authoritative-diagram | MED | gia cố, không khẩn |
| 8 | override-surface-risk · "mọi lượt" note · real-vs-abstract restraint · bilingual/privacy posture 3D/3E | LOW | hoàn thiện |

---

## 5. Open decisions (chốt khi plan)

1. **Gộp guidance vào plan memory-layer hiện có hay tách plan riêng?** Lean: guidance (Phần A) là *prose-only, độc lập* → có thể tách "guardrails doc pass" làm trước (nhanh, 0 script); behavioral 3D/3E *merge vào* memory plan (đụng script/trigger).
2. **3E lưu ở đâu khi nó "machine-ish" nhưng phải trong `docs/product/`?** Đề xuất `.memory/self-corrections.json` gitignore. Xác nhận posture privacy (có thể echo wording PO).
3. **"Verified-sticky" (suppress ruled drift) lưu ở đâu** — entry trong `decisions.md` (DEC cho ruling) hay field cạnh verdict trong `judgments.json`? Nối điểm #6 §10 memory report.
4. **Scope Challenge lock** áp mỗi PRD có quá nặng cho PO non-technical không? Có thể chỉ bật khi PRD vượt ngưỡng (N epic/story).
5. **Authoritative-diagram per flag-family** — thêm bảo trì; có đáng so với chỉ siết prose?

---

## 6. Next steps

- PO duyệt ưu tiên §4. Nếu OK → `/ck:plan` (default): **Phần A guardrails = prose pass độc lập, làm trước** (0 script,
  ship nhanh, auto-bundle); **Phần B behavioral 3D/3E = merge vào plan memory-layer** (đụng trigger + `check_fence.py`).
- Khi plan: nối **verified-sticky** (item 7) với judgment-cache (memory report §10 #5) để tránh đẻ cơ chế trùng.
- Fixture đề xuất: (a) hội thoại lạc đề + spec-trong-repo-code để test redirect Q1/Q2; (b) `--update` xóa-quyết-định-draft
  để test no-silent-reversal mở rộng; (c) cross-ref cũ để test Consistency Sweep.

## Unresolved questions
- #1 §5: tách plan guardrails hay gộp memory — cần PO chốt phạm vi vòng tới.
- #3 §5: nhà của "ruled-drift suppression" (decisions.md vs judgments.json) — quyết khi thiết kế judgment-cache.
- Scope Challenge cho PO non-technical: bật-luôn hay bật-theo-ngưỡng?
