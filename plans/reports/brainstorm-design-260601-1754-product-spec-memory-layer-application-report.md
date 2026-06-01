---
type: brainstorm-design
date: 2026-06-01
slug: product-spec-memory-layer-application
status: proposal
owner: hieubt
scope: product-spec (memory layer + soft fence) — claude-pack/hook OUT
supersedes_partial: brainstorm-research-260601-1730-product-spec-memory-hook-scaling-report.md (§3, §4a, §10#5)
related:
  - .claude/skills/product-spec/scripts/spec_graph.py
  - .claude/skills/product-spec/references/workflow-validate.md
  - .claude/skills/product-spec/references/workflow-interview.md
---

# Brainstorm Design — product-spec: Memory layer + Soft fence (cách áp dụng)

> Tiếp nối report `…-memory-hook-scaling` (1730). Phiên này **thu hẹp**: chỉ memory-layer storage
> + soft fence. CHƯA code. Integration-ready cho `/ck:plan`.

---

## 0. Scope chốt phiên này

| | |
|---|---|
| **IN** | Memory layer (3 sub-store: decisions / preferences / judgment-cache) · soft fence (F1+F3+F2) · `body_hash` per-node (blocker) |
| **DROP** | Edit-fence PreToolUse hook (H1) · Phase C · phụ thuộc claude-pack hook-merge |
| **DEFER** | `--status` nudge (N2) · commit-vs-gitignore cho `judgments.json` · engine orchestration chi tiết (read/store cache trong Step 2) · dup pre-filter / batched-LLM / scoped-validate (Phase A scaling) |

Lưu ý: phiên này định nghĩa **file + schema + điểm tích hợp** của memory layer. *Orchestration* đầy đủ
của judgment-cache (khi nào đọc/ghi trong vòng `--validate`, batching) là phần engine Phase A — chốt khi plan.

---

## 1. Quyết định đã chốt (PO duyệt phiên này)

| # | Fork | Chốt |
|---|------|------|
| D1 | Bố cục folder | **Split**: `decisions.md` visible + `.memory/{preferences.yaml, judgments.json}` ẩn |
| D2 | Soft fence | **F1 prose + F3 path-assert + F2 advisory script** (`check_fence.py`) |
| D3 | Ghi Decision Register | **Auto** khi contradiction resolve **+** flag `--decision` standalone |
| D4 | contradiction cache | **Không cache** (luôn re-run) — KISS, correctness-first |
| D5 | Prior art web-research | Không — grounding từ code đủ |

---

## 2. ⚠️ Blocker — `body_hash` per-node CHƯA tồn tại

Report 1730 (§2) giả định *"content_hash per-node có sẵn ở `spec_graph.py:497`"*. **Sai — verified by source:**

- `spec_graph.py:497` `content_hash = sha256(body)[:8]` là hash **toàn bộ snapshot JSON** (đặt tên file snapshot), KHÔNG per-node.
- `_node_from_artifact` (`spec_graph.py:113-161`) dựng node với field frontmatter (`id/status/scope/moscow/…`) nhưng **KHÔNG có hash body**.

**Hệ quả kép:**
1. Khóa cache `(check, node_id, content_hash, …)` thiếu nguyên liệu → judgment-cache không chạy được nếu không thêm.
2. **Gap có sẵn:** impact-pass (`workflow-validate.md` Step 2.5, line 56) detect "node đổi" bằng so `status/scope/moscow/horizon/size` — **KHÔNG so body**. → PO sửa AC/mô tả story mà không đụng frontmatter ⇒ impact-pass **bỏ sót**. Đây là bug latent độc lập với memory.

**Fix (1 thay đổi, lợi 2):** thêm `"body_hash": sha256(body.encode()).hexdigest()[:8]` vào dict trong `_node_from_artifact`. Mở khóa cache + sửa luôn gap impact-pass. Snapshot tự động mang theo (node được serialize nguyên vào snapshot body).

- **Touchpoint:** `spec_graph.py:116` (thêm 1 key vào dict trả về). `body` đã sẵn trong scope hàm (param).
- **Ripple:** snapshot delta (Step 2.5) sau đó so thêm `body_hash` để bắt body-edit. `diff_graphs` (line 450) chỉ so id-set + product fields — phần "changed node by field" nằm ở orchestration Step 2.5, thêm `body_hash` vào danh sách field so sánh.

---

## 3. Kiến trúc memory layer (đã chốt D1)

```
docs/product/
├── change-log.md          (đã có — append-only "what happened")
├── decisions.md           (MỚI · visible · committed — append-only "WHY")
├── .memory/               (MỚI · ẩn)
│   ├── preferences.yaml    (PO config/prefs · committed)
│   └── judgments.json      (LLM verdict cache · machine · commit policy DEFER)
└── visuals/.snapshots/     (đã có)
```

Nguyên tắc xuyên suốt: **memory KHÔNG đẻ source-of-truth thứ 2.** Frontmatter vẫn là chân lý structural;
memory chỉ lưu thứ frontmatter KHÔNG có (lý do, pref, verdict tái dùng).

### 3A. Decision Register — `docs/product/decisions.md`

Mục tiêu: nhớ **lý do** → **chặn re-litigate** + nuôi contradiction protocol.

**Format (PO-readable markdown, append-only):**
```markdown
## DEC-3 — Guest checkout = out-of-scope (v1)
- date: 2026-06-01 · owner: hieubt · status: active
- related: PRD-CART, BRD-G2
- decision: Không xây guest checkout ở v1.
- rationale: PCI scope nổ + nhu cầu đo được thấp (<3% giỏ hàng).
- supersedes: —
```

| Khía cạnh | Thiết kế |
|---|---|
| ID grammar | `DEC-<n>` · regex `^DEC-\d+$` · next-free-int do **script** cấp (mirror cách `generate_templates.py` cấp parent-scoped ID) |
| DRY guard | Chỉ *quyết định + lý do* + link ID. **KHÔNG** copy structural fact. Vi phạm = lint sau (out-of-scope phiên này). |
| Lifecycle | Append-only · `status: active \| superseded` · quyết định mới dùng `supersedes: DEC-n`, KHÔNG xóa |
| Trigger ghi (D3) | **(auto)** Contradiction protocol resolve (`workflow-validate.md:85-95`) → append DEC ghi Keep/Change/Hybrid + rationale PO đưa. **(manual)** flag `--decision` → PO log quyết định độc lập |
| Đọc | Contradiction protocol đọc `decisions.md` **TRƯỚC** khi surface: nếu chủ đề trùng `DEC` cũ `active` → "Bạn đã quyết DEC-3 (…vì PCI); claim mới mở lại — giữ DEC-3 hay supersede?" → diệt re-litigation |
| Script-vs-LLM | Script: cấp `DEC-n` + validate grammar + parse các record. LLM: viết prose rationale + quyết định trùng-chủ-đề |

**Vòng khép kín chống re-litigate:**
```
contradiction phát hiện ──► đọc decisions.md ──► trùng DEC active?
   │                                                  │ có → nhắc PO: giữ/supersede DEC cũ
   │                                                  │ không → surface mới (protocol)
   └────────── PO chốt Keep/Change/Hybrid ──► auto-append DEC-(n+1) (why + lựa chọn)
```

### 3B. PO Preferences — `docs/product/.memory/preferences.yaml`

Mục tiêu: nhớ thói quen → bớt hỏi lại.

```yaml
lang: vi                 # default interview lang (vẫn khai per-artifact; frontmatter thắng)
detail_level: standard   # terse | standard | deep
prioritization: moscow   # moscow | kano | rice
dismissed_reminders: []  # id reminder PO bảo ngừng hiện
```

| Khía cạnh | Thiết kế |
|---|---|
| DRY guard | Là **default/pref**, KHÔNG source-of-truth. `lang` per-artifact vẫn thắng; file chỉ seed option mặc định khi bắt đầu artifact mới |
| Đọc | Interview flow (`workflow-interview.md`) seed default cho `AskUserQuestion` |
| Ghi | Khi PO set pref / dismiss reminder |
| Schema | KV nhỏ, enum đóng. Thiếu key → fallback hard-coded default (back-compat) |

### 3C. Judgment Cache — `docs/product/.memory/judgments.json`

Mục tiêu: tái dùng verdict LLM cho node không đổi → token ↓ + scaling. (Sub-store memory + đòn bẩy scaling.)

```json
{
  "cache_version": 1,
  "model_id": "claude-opus-4-8",
  "entries": {
    "invest_quality|PRD-AUTH-E1-S1|a1b2c3d4|vi|": { "verdict": {...}, "stored_at": "..." },
    "core_value_drift|PRD-AUTH|a1b2c3d4|vi|cv:9f8e": { "verdict": {...} },
    "semantic_duplication|PRD-AUTH+PRD-LOGIN|aaaa1111+bbbb2222|vi|": { "verdict": {...} }
  }
}
```

| Khía cạnh | Thiết kế |
|---|---|
| Khóa | `check \| scope_key \| hash(es) \| lang \| dep_hash` · single-node: `scope_key=node_id` · `semantic_duplication`: cặp sort `(idA+idB \| hashA+hashB)` · `core_value_drift`: `dep_hash=cv:<hash(PRODUCT.core_value)>` · `contradiction`: **KHÔNG có entry** (D4) |
| Owner | Script `judgment_cache.py`: tính khóa + staleness (deterministic, từ `body_hash` + dep). LLM **chỉ** sản xuất verdict. Mirror khuôn `*_anchors.py` |
| Invalidate | `body_hash` đổi HOẶC `dep_hash` đổi → miss · `cache_version`/`model_id` mismatch → miss toàn bộ (an toàn nâng model) · escape `--no-cache` |
| Đọc/ghi | Đọc TRƯỚC Step 2 (emit node stale/fresh per check) · Ghi SAU Step 2 (store verdict). **Orchestration chi tiết = engine Phase A, để plan** |
| Commit policy | DEFER (gitignore-lean cho dogfood; toggle sau). Thiết kế coi như pluggable — không phụ thuộc git |

---

## 4. Soft fence (D2: F1 + F3 + F2) — KHÔNG hook

| Lớp | Cơ chế | Touchpoint | Chi phí |
|---|--------|-----------|--------|
| **F1. Prose rule** | Siết `SKILL.md`/`CLAUDE.md`: "skill CHỈ ghi `docs/product/`" thành operating rule loud + self-check nhắc LLM trước Write | `SKILL.md`, CLAUDE.md product-spec block | 0 |
| **F3. Path-assert script** | `generate_templates.py` + `render_*` thêm `assert resolved_path under docs/product/` + lỗi thân thiện nếu thoát | mọi script ghi file | Rẻ |
| **F2. Advisory `check_fence.py`** | Script pull: quét `git status`/file vừa đụng → báo "file ngoài docs/product/ bị chạm — chủ ý?". Advisory, KHÔNG chặn; LLM tự chạy như kỷ luật (vd cuối op ghi-nặng / đầu `--validate`) | MỚI `scripts/check_fence.py` | Trung |

**Sự thật trần trụi (ghi vào doc, không giấu PO):** F1+F3+F2 **KHÔNG** chặn raw `Write` của LLM ra file code — chỉ
kỷ luật prose + tự vệ đường-script + advisory bắt-sớm. Chặn cứng raw-LLM-write cần PreToolUse hook (H1, **đã bỏ**).
Soft fence = "giảm xác suất + bắt sớm", KHÔNG "bất khả xâm phạm".

---

## 5. Danh mục thay đổi (cho /ck:plan)

**Script mới:**
- `scripts/judgment_cache.py` — `--check` emit stale/fresh per check · `--store` ghi verdict · `--no-cache`/version stamp.
- `scripts/decision_register.py` — `--alloc-id` cấp `DEC-n` · `--append` validate+ghi record · `--list` parse các DEC active.
- `scripts/check_fence.py` — advisory quét file ngoài `docs/product/`.

**Script sửa:**
- `spec_graph.py:116` — thêm `body_hash` vào node dict (BLOCKER §2).
- `generate_templates.py` + `render_*.py` — F3 path-assert.

**Reference sửa:**
- `workflow-validate.md` — Step 2.5 so thêm `body_hash` (sửa gap impact-pass) · contradiction protocol đọc/ghi `decisions.md` · (engine cache read/store = Phase A, đánh dấu TODO).
- `workflow-interview.md` — đọc `preferences.yaml` seed default.

**CLAUDE.md / SKILL.md:**
- F1 prose rule · mô tả `.memory/` + `decisions.md` trong Output Layout · thêm `--decision` flag vào bảng flag.

**Template mới:** `assets/templates/decision-record.md` (`{{token}}` cho DEC record).

---

## 6. Tuân thủ luật lõi

| Luật (CLAUDE.md) | Tuân thủ |
|---|---|
| Frontmatter = source-of-truth | Memory chỉ lưu why/pref/verdict; structural vẫn ở frontmatter. ✅ |
| DRY — 1 nhà/fact | decisions = rationale+link ID (không copy fact) · prefs = default (lang per-artifact thắng) · cache = tối ưu, không authoritative. ✅ |
| Script-vs-LLM split | Script: body_hash, DEC-id alloc, cache key+staleness, path-assert, fence scan. LLM: rationale, verdict, trùng-chủ-đề. ✅ |
| No silent reversal | `decisions.md` + contradiction protocol KHÔNG auto-flip; supersede tường minh. ✅ |
| Never overwrite manual prose | decisions/prefs append/merge, không đè. ✅ |
| Skill never writes outside docs/product/ | Memory nằm trong `docs/product/`; F3 assert củng cố. ✅ |

---

## 7. Rủi ro & giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|--------|-----|-----------|
| Soft fence tạo ảo giác "đã an toàn" | Trung | Doc §4 nói rõ KHÔNG chặn raw-LLM-write; chỉ kỷ luật+advisory |
| Cache verdict cũ sau nâng model | Trung | `model_id`+`cache_version` stamp → mismatch=miss toàn bộ · `--no-cache` · `strict_gate.py` structural-only nên CI không phụ thuộc cache |
| `decisions.md` drift khỏi frontmatter (vi phạm DRY) | Trung | Chỉ rationale+link ID; lint DRY để vòng sau |
| `body_hash` đổi format snapshot cũ | Thấp | Thêm field optional; snapshot cũ thiếu `body_hash` → coi mọi node "changed" lần đầu (re-validate 1 lần, đúng & an toàn) |
| DEC-id race (2 append đồng thời) | Thấp | Dogfood single-dev; script alloc đọc-max+1 atomic-enough; team-mode để sau |
| `judgments.json` git noise (nếu sau commit) | Defer | Key sort ổn định khi cần; quyết định commit để sau |

---

## 8. Success metrics

- PO sửa AC story (chỉ body) → impact-pass **bắt được** node đó (hiện đang bỏ sót) — test trên fixture.
- Contradiction trùng chủ đề có `DEC` active → skill trích DEC gốc thay vì hỏi lại từ đầu — mọi case có DEC tương ứng.
- Re-validate spec không đổi → các check single-node **0 LLM call** (cache hit 100%), trừ `contradiction` (D4 luôn chạy).
- `check_fence.py` báo đúng khi có file ngoài `docs/product/` bị chạm trong phiên test.
- `preferences.yaml` có `lang: vi` → artifact mới seed default vi mà không hỏi lại.

---

## 9. Open decisions (để dành plan / vòng sau)

1. **`judgments.json` commit hay gitignore** (DEFER có chủ đích) — chốt khi đụng CI/team.
2. **`--status` nudge (N2)** — defer; làm cùng Phase B scaling.
3. **Engine orchestration** cache read/store trong Step 2 + batching (S4) + dup pre-filter (S2) + scoped-validate (S3) — Phase A scaling, plan riêng.
4. **DRY-lint cho decisions.md** (phát hiện copy structural fact) — vòng sau.
5. **Team-mode DEC-id allocation** (lock/merge) — khi rời dogfood single-dev.

---

## 10. Next steps

- Duyệt design → `/ck:plan` (cân nhắc `--tdd`: §2 `body_hash` + impact-pass đụng logic ĐANG có test → khóa hành vi trước).
- Plan nên có fixture: (a) spec với body-edit-only để test impact-pass fix; (b) spec re-validate để đo cache-hit; (c) project có file ngoài docs/product/ để test `check_fence.py`.
- Thứ tự build đề xuất trong plan: **body_hash (blocker)** → decisions.md + contradiction wiring (giá trị PO cao nhất) → preferences.yaml → soft fence F1/F3/F2 → judgments.json file+script (engine orchestration tách Phase A).
