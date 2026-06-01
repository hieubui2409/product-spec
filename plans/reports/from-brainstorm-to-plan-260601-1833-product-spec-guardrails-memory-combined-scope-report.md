---
type: from-brainstorm-to-plan
date: 2026-06-01
slug: product-spec-guardrails-memory-combined-scope
status: locked-for-plan
owner: hieubt
scope: product-spec (guardrails + references restructure + memory 3-store + behavioral 3D/3E + --status). claude-pack impact ≈ 0.
consolidates:
  - plans/reports/brainstorm-design-260601-1754-product-spec-memory-layer-application-report.md      # memory 3-store + soft fence + body_hash
  - plans/reports/brainstorm-design-260601-1819-product-spec-guardrails-and-behavioral-memory-report.md  # guardrails + behavioral 3D/3E
  - plans/reports/brainstorm-research-260601-1730-product-spec-memory-hook-scaling-report.md          # origin (Phase C/edit-fence DROPPED)
---

# From Brainstorm → Plan — product-spec: Guardrails + Memory (combined scope, decisions LOCKED)

> Input hợp nhất cho **MỘT plan gộp**. Mọi quyết định đã chốt qua các phiên brainstorm. CHƯA code.
> Chi tiết design nằm ở 2 report consolidates (memory=1754, guardrails+behavioral=1819); file này = scope + decisions + corrections + build-order.

---

## 0. Quyết định ĐÃ CHỐT (master table)

| # | Quyết định | Chốt | Nguồn |
|---|-----------|------|-------|
| Plan | Cấu trúc | **1 plan gộp tất cả** | phiên 1833 |
| Mem-D1 | Folder | **Split**: `docs/product/decisions.md` (visible) + `.memory/{preferences.yaml, judgments.json, po-style.yaml, self-corrections.json}` | 1754 |
| Mem-D2 | Soft fence | **F1 prose + F3 path-assert + F2 advisory `check_fence.py`** (KHÔNG hook) | 1754 |
| Mem-D3 | Decision Register | **Auto-append khi contradiction resolve + flag `--decision`** | 1754 |
| Mem-D4 | contradiction cache | **No-cache** (luôn re-run) | 1754 |
| Mem-D5 | **body_hash blocker** | Thêm `body_hash=sha256(body)[:8]` vào node dict `spec_graph.py:116` (mở khóa cache + sửa gap impact-pass bỏ sót body-edit) | 1754 §2 |
| Commit | Persist memory | **Commit TẤT CẢ** file memory (1 PO, để monitor/evidence). Toggle gitignore sau nếu cần. Caveat: `self-corrections.json` có thể echo wording PO → privacy toggle về sau | 1833 |
| Drift | Ruled-drift suppression | **Field cạnh verdict trong `judgments.json`** (po_ruling, hash-keyed → tự invalidate khi artifact đổi) | 1833 |
| Refs | Tái cấu trúc | **Split 2 file + sửa 3 DRY-dup + cập nhật pointer table** | 1833 |
| Guard-home | Nhà guardrail mới | **Anchor ngắn ở CLAUDE.md (auto-load) + detail ở `references/guardrails-and-boundaries.md` (on-demand)** | 1833 |
| Mem-scope | Phạm vi vòng này | **GỒM 3D PO-style + 3E self-correction + `--status` nudge (N2)** | 1833 |
| Scope-chal | Scope Challenge | **Always-on mỗi PRD** (chốt MVP/Full/Strip + LOCK trước decompose) | 1833 |

---

## 1. Đính chính (review-audit: surface + cite, không lật âm thầm)

### 1.1 CLAUDE.md KHÔNG bị ck update đè (confidence ~90%)
- Repo-root `CLAUDE.md`: tracked, sửa tay qua nhiều commit của user (git log) → **project-owned**.
- `.claude/.ck.json` kit chỉ quản `installedSettings.hooks` + `mcpServers` — **không** liệt kê CLAUDE.md.
- Vùng ck **CÓ** đè = `.claude/rules/*` (gồm `.claude/rules/CLAUDE.md` — "The CK CLI installs it"). **KHÔNG đặt nội dung của ta ở đó.**
- Auto-management DUY NHẤT của repo-root CLAUDE.md = block `<!-- BEGIN/END: cleanmatic:claude-pack operating guide -->` (281-387) do **chính claude-pack** regenerate (KHÔNG phải ck). Sửa phần product-spec (1-280, không marker) + ngoài marker = an toàn.
- Caveat: source ck-installer ngoài repo → chưa 100%, nhưng mọi bằng chứng local nhất quán.

### 1.2 RETRACT lỗi report 1819 (Reader B)
- 1819 nói *"claude-pack KHÔNG bundle repo CLAUDE.md → install mất rule 'When to Ask vs Assume'"* → **SAI**.
- Bằng chứng ngược: `pack.manifest.yaml: include_claudemd: true` + `selection.py:77-78` → **CÓ ship** repo-root CLAUDE.md vào tarball (recipient auto-load).
- → Hệ quả: repo-root CLAUDE.md vừa an-toàn-sửa vừa được-ship → **nhà đúng** cho guardrail PO-runtime. Bỏ luận điểm "nhấc ra vì mất". Lựa chọn thật chỉ còn golden-rule: CLAUDE.md auto-load-mọi-lượt (để guardrail ngắn luôn-cần) vs references/ on-demand (chi tiết). → đã chốt Guard-home.

---

## 2. References restructure (cụ thể)

### 2.1 Split (progressive-disclosure — load only when needed)
| Từ | Thành | Lý do |
|----|-------|-------|
| `interview-epic-story.md` (120L) | `interview-epic.md` + `interview-story.md` | `--epic` không cần prompt story & ngược lại |
| `workflow-auto-and-update.md` (139L) | `workflow-auto.md` + `workflow-update.md` | `--auto` vs `--update` là 2 flow độc lập |

### 2.2 Sửa 3 DRY-dup (Principle 2 — 1 nhà + link)
| Nội dung trùng | 2 chỗ hiện tại | Nhà authoritative đề xuất |
|----------------|----------------|---------------------------|
| Contradiction Protocol | `workflow-validate.md:85` + `validation-rules-spec.md:169` | `validation-rules-spec.md` (workflow-validate link) |
| Human Report Format | `workflow-validate.md:70` + `validation-rules-spec.md:205` | `validation-rules-spec.md` (workflow-validate link) |
| Findings Schema | `validation-rules-spec.md:182` + `frontmatter-and-id-spec.md:231` | `frontmatter-and-id-spec.md` (schema aggregator; validation-rules link) |

### 2.3 Cập nhật pointer (sau split)
- `CLAUDE.md → Workflow Pointers` + `SKILL.md` references list: map `--epic`→interview-epic, `--story`→interview-story, `--auto`→workflow-auto, `--update`→workflow-update.
- Thêm `references/guardrails-and-boundaries.md` vào pointer table với ghi chú **"load bất kể flag"** (guardrail luôn-cần).

---

## 3. Build order đề xuất cho plan gộp (đòn bẩy ÷ phụ thuộc)

| Phase | Nội dung | Loại | Phụ thuộc |
|-------|----------|------|-----------|
| **P1** | **body_hash blocker** (`spec_graph.py:116`) + sửa impact-pass body-detect (`workflow-validate.md` Step 2.5 so thêm body_hash) | script + prose | 0 (nền cho cache) |
| **P2** | References restructure: split 2 + DRY 3 + pointer updates | prose/structural | 0 (độc lập) |
| **P3** | Guardrails anchor: CLAUDE.md (off-topic redirect, no-code redirect, anti-rationalization table, named-GATE, "applies every turn", override-surface-risk) + `references/guardrails-and-boundaries.md` | prose | 0 |
| **P4** | Workflow guardrails: consistency-sweep gate (workflow-update) · mở rộng no-silent-reversal → confirmed-draft (workflow-auto+update) · Validation Log schema · **Scope Challenge always-on** (workflow-interview) · scout-first-ask-second · eng-jargon→product reframe (interview-frameworks) · authoritative diagram/flag-family | prose | P2 (file đã split) |
| **P5** | Memory core: `decisions.md` + `decision_register.py` (alloc DEC-n, append, list) + contradiction wiring (đọc/auto-append + `--decision`) · `preferences.yaml` + interview seed | script + prose | P1 |
| **P6** | Judgment cache: `judgments.json` + `judgment_cache.py` (key+staleness) + incremental `--validate` orchestration + **ruled-drift field** + verified-sticky (suppress ruled drift) | script | P1, P5 |
| **P7** | Behavioral: 3D `po-style.yaml` (read ở prose-gen, write khi PO sửa wording, lang-keyed) + 3E `self-corrections.json` (write từ check_fence/contradiction, pre-flight read) | script + prose | P5, P8(F2) |
| **P8** | Soft fence (F1 prose · F3 path-assert trong generate_templates/render_* · F2 `check_fence.py`) + `--status` nudge N2 (reuse time_advisory + snapshot delta + last_validated) | script + prose | P1 |
| **P9** | claude-pack impact verify: confirm references mới auto-ship (slug rglob), **0 sửa manifest/safety_check** | verify | tất cả |

> Lưu ý DRY: nối **verified-sticky (P6)** với ruled-drift field — cùng cơ chế, đừng đẻ 2. **3E (P7)** tiêu thụ output `check_fence.py` (P8) → P8 trước hoặc song song P7.

---

## 4. Impact (tái khẳng định)
- **product-spec:** phần guidance = doc/prose thuần (0 script); memory + behavioral + fence = script mới (`decision_register.py`, `judgment_cache.py`, `check_fence.py`) + sửa `spec_graph.py` (body_hash) + path-assert trong generate_templates/render_*.
- **claude-pack: 0 sửa bắt buộc** — references mới auto-ship (manifest slug + rglob). `.memory/` của PO ngoài scope packer.
- **File ngoài skill: KHÔNG sửa** — repo-root CLAUDE.md sửa được (project-owned) nhưng đó là *trong scope sản phẩm*; `.claude/rules/*` (ck) read-only tuyệt đối.

## 5. Open questions
**Không còn** — toàn bộ đã chốt ở §0. (Plan-time chỉ còn chi tiết triển khai: ngưỡng N cho complexity-smell của Scope Challenge nếu sau muốn nới always-on; nhà chính xác của 3 DRY-dup có thể vi chỉnh khi viết.)
