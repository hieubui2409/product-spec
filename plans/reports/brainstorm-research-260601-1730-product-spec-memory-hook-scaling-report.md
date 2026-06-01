---
type: brainstorm-research-design
date: 2026-06-01
slug: product-spec-memory-hook-scaling
status: proposal
owner: hieubt
scope: product-spec (+ claude-pack dependency for hook shipping)
related:
  - .claude/skills/product-spec/
  - .claude/skills/claude-pack/
---

# Brainstorm — product-spec: Memory layer · Hook layer · Scaling khi spec lớn

> Báo cáo research + design. CHƯA code. 3 hướng nâng cấp giao nhau ở **một** subsystem lõi.
> Mini-workflow: phân tích inline, không fan-out agent (tránh 429).

---

## 0. TL;DR (đọc cái này trước)

1. **3 ý tưởng KHÔNG độc lập.** "Cache LLM judgment" (memory) + "incremental validation" (scaling) + "what-changed nudge" (hook) là **CÙNG một engine**: một *judgment-cache + delta-aware validation* deterministic. Build 1 lần, phục vụ cả 3. Đây là đòn bẩy cao nhất.
2. **Ranh giới sở hữu (ràng buộc cứng):** chỉ `product-spec` + `claude-pack` thuộc repo này. Hooks/agents/rules `.claude/*` khác là của **ClaudeKit (ck)**, cài từ ngoài → **không được sửa** (ck update sẽ đè). Mọi hook cho product-spec phải **tự đóng gói** trong skill/bundle.
3. **Gap claude-pack:** ship hook verbatim được, NHƯNG *"no automatic hook merge in v1"* — PO phải tự wire vào `settings.json`. Đây là phần đắt nhất, phụ thuộc chéo → **để cuối**.
4. **Đề xuất 3 phase theo đòn bẩy/độ phụ thuộc:**
   - **Phase A** (cao nhất, self-contained): judgment-cache + incremental validate + dup pre-filter.
   - **Phase B** (rẻ, self-contained): decision register + PO prefs + `--status` health (nudge kiểu pull).
   - **Phase C** (đắt, phụ thuộc claude-pack): edit-fence hook + cơ chế merge settings.json.

---

## 1. Problem statement & yêu cầu

PO non-technical dùng product-spec. Ba nỗi đau:

- **Memory:** mỗi lần invoke đọc lại toàn bộ `docs/product/`, dựng lại graph, re-judge từ đầu. Không nhớ *quyết định + lý do* (re-litigate), không nhớ *prefs*, không tái dùng *judgment* cũ.
- **Hook/an toàn:** luật "skill chỉ ghi trong `docs/product/`" hiện chỉ là **chỉ dẫn LLM mềm** (CLAUDE.md/SKILL.md). Nếu PO copy spec vào folder code, LLM có thể hallucinate ghi ra code. Muốn nhắc validate/approve.
- **Scaling:** khi spec lớn (nhiều PRD/Epic/Story), các pass LLM nổ token.

### Yêu cầu chốt từ PO (phiên này)
| # | Item | Chốt |
|---|------|------|
| Scope | Phân phối | **Both, dogfood trước**; kiến trúc sẵn sàng ship PO. |
| Memory | Lưu gì | **Cả 3**: cache judgment + PO prefs + decisions/rationale (+ chốt định nghĩa ở §3). |
| Hook | Strictness | **Để ngỏ** — báo cáo trình trade-off + khuyến nghị. |
| Output | Phiên này | **Báo cáo research+design** (file này). Chưa code. |

---

## 2. Bối cảnh codebase (scout)

| Thành phần | Hiện trạng | Liên quan |
|-----------|-----------|-----------|
| Persistence | `.session.md` (interview state, resumable) · `change-log.md` (append-only delta) · `impact/*.md` · `visuals/.snapshots/*.json` | Có "what", thiếu "why" + cache + prefs |
| **Content hash** | `spec_graph.py:497` đã tính `content_hash=sha256(body)[:8]` per-node trong snapshot; `render_export.py` cũng dùng | **Khóa cache có sẵn — không phải dựng mới** |
| Snapshot delta | `spec_graph.diff_graphs(cur,prev)` → `{added,removed,product_changes}`; impact-pass đã derive change-set | Nền cho incremental validate |
| Validation LLM | `invest_quality` O(n)/story · `vagueness` O(n) · `core_value_drift` O(n)/node · **`semantic_duplication` O(n²)** pairwise PRD · `gold_plating` · `time_realism` · `competitive_drift` · `contradiction` | Re-run TOÀN BỘ mỗi lần — nguồn nổ token |
| Hook infra (ck) | `.claude/hooks/*.cjs`, `PreToolUse` matcher theo tool, block exit 2, driven `.ckignore`. `scout-block.cjs` = khuôn mẫu fence | **Của ck — chỉ tham chiếu, không sửa** |
| claude-pack | manifest có field `hooks:` (ship verbatim) · `include_settings:false` · per-skill `install.sh` opt-in `RUN_HOOKS=1` · **"no automatic hook merge in v1"** | Gap để hook chạy ở máy PO |
| Script-vs-LLM split | Luật lõi: script deterministic (parse/graph/hash/key), LLM phán đoán | Mọi thiết kế phải tôn trọng |

---

## 3. IDEA 1 — Memory layer (chốt định nghĩa)

**Định nghĩa chốt:** "Memory" = 3 sub-store dưới `docs/product/.memory/`, **không** đẻ nguồn-sự-thật-thứ-2 (frontmatter vẫn là source-of-truth; memory chỉ lưu thứ frontmatter KHÔNG có).

| Sub-store | File | Nội dung | DRY guard |
|-----------|------|----------|-----------|
| **A. Decision Register** | `.memory/decisions.md` (committed, PO đọc được) | Append-only Product Decision Records: `DEC-<n>` + rationale + related IDs + date/owner. VD: "guest-checkout = out-of-scope vì PCI + nhu cầu thấp". | Chỉ lưu *lý do* + *quyết định*; tham chiếu ID, KHÔNG copy structural fact |
| **B. Judgment Cache** | `.memory/judgments.json` (machine) | Verdict LLM keyed theo hash → tái dùng node không đổi. **Vừa memory vừa đòn bẩy scaling.** | Cache là tối ưu, KHÔNG bao giờ authoritative |
| **C. PO Preferences** | `.memory/preferences.yaml` | lang (vi/en), naming, mức chi tiết, framework ưa dùng (MoSCoW/Kano), reminder đã dismiss | KV nhỏ; lang vẫn khai per-artifact |

### 3B chi tiết — Judgment Cache (lõi)

**Khóa cache (deterministic, do SCRIPT tính):**
```
key = (check_name, node_id, content_hash, lang, dep_hashes[])
```
- `invest_quality`/`vagueness`: dep = ∅ (chỉ body node).
- `core_value_drift`: dep = `hash(PRODUCT.md.core_value)`.
- `semantic_duplication`: key = **cặp** `(hash_A, hash_B)` đã sort.
- `contradiction`: dep = tập hash các artifact `approved` → khó cache → **để không-cache** (hoặc cache yếu, miss khi tập approved đổi).

**Cơ chế (đúng Script-vs-LLM split):**
- SCRIPT mới `judgment_cache.py`: `--check` → emit danh sách node *stale/fresh* per check (tính hash, so cache); `--store` → ghi verdict LLM vào cache. **Script sở hữu key + staleness (hash/graph deterministic); LLM chỉ sản xuất verdict.**
- Invalidate: content_hash đổi HOẶC dep_hash đổi → miss → re-run LLM → store.
- Stamp `cache_version` + `model_id`; mismatch → coi như miss toàn bộ (an toàn khi nâng model).
- Escape hatch: `--validate --no-cache`.

### Lựa chọn lưu trữ
- **M1**: rải file lẻ trong `docs/product/`. **M2 (chọn)**: gom `.memory/` 1 nhà. **M3**: reuse global `~/.claude/.../memory` — ✗ loại (per-machine, không ship, không git theo spec, PO không thấy).

**Open decision — commit `judgments.json` hay gitignore?**
- Commit: tái dùng cross-session/CI, nhưng git noise + merge-conflict team + risk verdict cũ.
- Gitignore: sạch git, mỗi clone trả phí validate lần đầu.
- *Lean:* commit + key sort ổn định + version stamp; hoặc gitignore nếu team đông. Chốt khi plan.

---

## 4. IDEA 2 — Hook layer

Hai mục tiêu khác bản chất: **(2a) edit-fence** (chặn ghi sai chỗ) và **(2b) validate/approve nudge** (nhắc).

### 4a. Edit-fence — chặn LLM ghi ra ngoài `docs/product/`

| Approach | Cơ chế | Pros | Cons |
|----------|--------|------|------|
| **H1. Standalone PreToolUse hook** | File hook tự đóng gói (mirror `scout-block.cjs` exit-2), chặn Write/Edit ngoài `docs/product/**` hoặc ngoài md/html/mermaid/yaml/json | Thứ DUY NHẤT chặn được raw `Write` của LLM (đúng nỗi đau hallucinate) | Cần đăng ký vào `settings.json` (gap claude-pack); fire trên MỌI Write → false-positive ở project hỗn hợp code+spec |
| **H2. Script path-guard** | Mọi write của skill đi qua script → assert refuse ghi ngoài `docs/product/` | Self-contained, ship tự động, 0 wiring | **Chỉ** chặn write của SCRIPT; KHÔNG chặn raw `Write` của LLM → không đủ một mình |
| **H3. Hybrid (chọn)** | Lớp 1 chỉ dẫn (đã có) + Lớp 2 H2 (free, ship ngay) + Lớp 3 H1 opt-in marker | Defense-in-depth; phần free triển khai ngay; phần đắt tách riêng | H1 vẫn vướng gap claude-pack |

**Vấn đề cốt lõi của H1 — "hook không biết đang là product-spec context":** hook fire trên mọi Write/Edit, không biết task nào. Nếu chặn cứng "chỉ docs/product/**" → chặn luôn edit code ở project hỗn hợp.
**Giải (opt-in + project-type gating):**
- Fence **OFF mặc định**, bật qua marker tường minh: `PRODUCT.md` frontmatter `edit_fence: docs/product` (hoặc `.claude/product-spec.fence`).
- Project-type detect: có `docs/product/PRODUCT.md` **và** KHÔNG có manifest code (package.json/pyproject…) → spec-only → installer default fence **ON**. Project hỗn hợp → default **OFF** (hoặc warn-only).
- Knob strictness: `block` (exit 2) | `warn` (chỉ cảnh báo) — **để PO/installer chọn** (đáp ứng "decide later").

### 4b. Validate/approve nudge

| Approach | Cơ chế | Pros | Cons |
|----------|--------|------|------|
| **N1. PostToolUse/UserPromptSubmit reminder** | Sau khi artifact đổi, inject text "N node đổi từ lần --validate cuối; M draft chưa approve" | Push chủ động | Cần wiring hook (gap) |
| **N2. `--status` health script (chọn)** | Script pull: liệt kê unvalidated changes, drafts, overdue (reuse `time_advisory.py`), stale approvals | **0 wiring**, self-contained, compose sẵn time_advisory | Pull — PO phải hỏi (skill tự chạy ở SessionStart-equivalent: đầu mỗi lần invoke menu) |
| **N3. SessionStart hook** | In health khi mở project | Tự động | Cùng gap wiring như H1 |

**Lean nudge = N2**: nudge KHÔNG cần là hook. Skill tự chạy `--status` ở đầu menu không-flag → in health → tránh hoàn toàn gap settings.json. Tận dụng `.snapshots/` + marker `last_validated`.

### Gap claude-pack (phải flag — phụ thuộc chéo lớn nhất)
Để bất kỳ hook nào *active* ở máy PO:
- **(a)** Thêm bước "hook-merge" idempotent vào recipient installer (merge stanza product-spec vào `settings.json` của PO + backup). Scope creep claude-pack nhưng bounded. *Long-term sạch.*
- **(b)** Ship hook + 1 dòng hướng dẫn paste trong INSTALL/GUIDE. 0 đổi claude-pack, nhưng dựa vào PO non-technical tự làm → rủi ro.
- **(c)** Per-skill `install.sh` (opt-in `RUN_HOOKS=1`) tự merge settings.json. Cơ chế đã hỗ trợ, nhưng security-gated + opt-in → PO dễ skip.
- *Lean:* dogfood-first dùng (c)/(b); long-term (a). **H2 (script path-guard) ship FREE ngay, không vướng gap.**

---

## 5. IDEA 3 — Scaling khi spec lớn

Bottleneck xếp theo chi phí:
1. **Validation re-run toàn bộ** — đắt nhất. `semantic_duplication` O(n²) tệ nhất; INVEST/vagueness/drift O(n).
2. Export/summary dump cả spec vào LLM.
3. Context: đọc cả `docs/product/` vào LLM mỗi pass.
4. Viz graph khổng lồ (chủ yếu script-side, rẻ).

| Tweak | Mô tả | Reuse |
|-------|-------|-------|
| **S1. Incremental validate (đòn bẩy chính)** | Chỉ re-run LLM cho node có content_hash đổi HOẶC dep đổi. Steady-state: O(n)/O(n²) → **O(Δ)** | = Idea 1B cache + snapshot delta (đã có) |
| **S2. Dup pre-filter** | SCRIPT tính similarity rẻ (keyword/persona/scope/Jaccard title) → chỉ emit *candidate pairs* > threshold cho LLM. n(n-1)/2 → ~k | Script-vs-LLM split |
| **S3. Scoped validate** | `--validate <PRD-ID>` chỉ subtree → PO check 1 feature-area không trả phí cả spec | spec_graph subtree/downstream |
| **S4. Batched sequential LLM** | Chia pass theo PRD-subtree, chạy **tuần tự bounded batches** thay vì 1 prompt khổng lồ / fan-out lớn → **trị đúng 429** | — |
| **S5. Viz at scale** | Spec lớn default `board`/`explorer` (đã filter/search client-side) thay ASCII/Mermaid khổng lồ; thêm `--depth`/`--layers` cho graph view | export depth presets đã có |
| **S6. change-log rotation** | Archive entry cũ → `change-log.archive.md`, giữ N gần nhất | minor |

**Lưu ý 429 (nỗi đau user):** S4 là câu trả lời trực tiếp — *bounded sequential batches*, KHÔNG parallel fan-out. S1+S2 giảm tổng số call → giảm áp lực rate.

---

## 6. Luận điểm hợp nhất (quan trọng nhất)

**Idea 1B + S1 + S2 + S4 + nudge-N2 = MỘT subsystem:** *deterministic judgment-cache + delta-aware validation engine.*

```
spec_graph (hash, có sẵn) ──► judgment_cache.py (key + staleness, MỚI)
        │                              │
        ▼                              ▼
 snapshot delta (có sẵn) ──► stale set ──► LLM judge CHỈ stale (batched) ──► store verdict
        │                                                                       │
        └──────────────► --status health (nudge, pull) ◄────────── last_validated marker
```
Build engine này 1 lần → phục vụ memory (cache + reuse), scaling (incremental + pre-filter + batch), và nudge ("what changed since last validate"). **Đây là nơi nên đổ công đầu tiên.**

---

## 7. Phân phase đề xuất (YAGNI/KISS — đòn bẩy ÷ phụ thuộc)

| Phase | Nội dung | Phụ thuộc | Giá trị |
|-------|----------|-----------|---------|
| **A** | `judgment_cache.py` + incremental `--validate` + dup pre-filter (S2) + batched LLM (S4) | 0 (pure product-spec script) | ★★★ token ↓ mạnh, trị 429 |
| **B** | Decision Register (`decisions.md`, ID `DEC-n`, nối contradiction protocol) + PO prefs (`preferences.yaml`) + `--status` health (N2) + script path-guard (H2) + scoped `--validate <ID>` (S3) | 0 (skill-native) | ★★ an toàn + memory + nudge, rẻ |
| **C** | Edit-fence PreToolUse hook (H1, opt-in marker, block/warn knob) + claude-pack settings.json hook-merge (gap (a)) + viz-at-scale (S5) | **claude-pack** | ★ chặn raw LLM write, nhưng đắt + cross-skill |

Lý do thứ tự: A/B self-contained, đòn bẩy cao, ship được ngay; C kéo theo claude-pack → để cuối, sau marker/knob đã rõ.

---

## 8. Rủi ro & giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|--------|-----|-----------|
| Cache verdict cũ sau khi đổi model LLM | Trung | `model_id`+`cache_version` stamp → mismatch = miss toàn bộ; `--no-cache`; `strict_gate.py` vốn structural-only (LLM-free) nên CI không phụ thuộc cache |
| Commit `judgments.json` → git noise/merge-conflict | Trung | Key sort ổn định; hoặc gitignore (chốt §3) |
| Edit-fence false-positive ở project hỗn hợp | Cao | Opt-in marker + project-type gating + `warn` mode mặc định cho mixed |
| claude-pack auto-merge `settings.json` đụng hook của PO | Cao | Idempotent + backup + chỉ thêm stanza có namespace `product-spec-*`; opt-in |
| Decision Register drift khỏi frontmatter (vi phạm DRY) | Trung | Decisions chỉ chứa rationale + nối ID; KHÔNG copy structural fact |
| Dup pre-filter bỏ sót cặp trùng thật (recall) | Thấp–Trung | Threshold thận trọng + `--no-prefilter` để chạy full O(n²) khi cần audit |
| H2 tạo ảo giác "đã an toàn" (thực ra chỉ chặn script) | Trung | Doc rõ: H2 chặn script-write; raw-LLM-write cần H1 (Phase C) |

---

## 9. Success metrics

- Re-validate spec 100-story **không đổi** → token ↓ **≥70%** (cache hit-rate cao).
- `semantic_duplication` call LLM ↓ từ n(n-1)/2 xuống ~k candidate (đo trên fixture lớn).
- Project có fence ON: **0** raw-LLM-write thoát `docs/product/` trong test.
- Contradiction surfacing trích được rationale gốc từ `decisions.md` ở mọi case có `DEC` tương ứng.
- Không còn 429 trên spec lớn nhờ batched-sequential (S4).

---

## 10. Open decisions (cần chốt khi lập plan)

1. **`judgments.json`: commit hay gitignore?** (team size + CI reuse vs git noise).
2. **Edit-fence default strictness:** `block` cho spec-only, `warn` cho mixed — OK chưa? Hay luôn `warn` ở v1?
3. **claude-pack hook-merge:** chọn (a) installer auto-merge / (b) doc thủ công / (c) per-skill install.sh cho bản dogfood?
4. **Phase C có làm trong vòng này không**, hay dừng ở A+B (self-contained) và để C khi claude-pack sẵn sàng?
5. **`contradiction` check:** chấp nhận không-cache (luôn re-run) hay cache yếu theo tập-approved-hash?
6. **"claude-ship"** trong note của bạn — có phải ý là `claude-pack`? (repo này chỉ có product-spec + claude-pack). Xác nhận để khỏi hiểu nhầm scope.

---

## 11. Next steps

- PO review báo cáo → chốt §10 (đặc biệt #4: phạm vi vòng này = A+B hay A+B+C).
- Nếu duyệt → handoff `/ck:plan` (default cho A+B; cân nhắc `--tdd` vì A đụng validation logic đang có test → khóa hành vi trước khi đổi).
- Engine Phase A nên có fixture spec-lớn trong `eval/fixtures/` để đo token-saving + recall dup pre-filter.
