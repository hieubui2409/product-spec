# Research Report: Backlog nhóm C / D / E — grounding cho brainstorm

> Timestamp: 2026-06-03 17:58 UTC · Scope: BACKLOG.md nhóm C (deepen product-spec), D (shared foundation), E (close PO pipeline).
> Phương pháp: 3 Explore agent đọc codebase (read-only) + 3 WebSearch best-practice. Report-only, không sửa skill.

## Executive Summary

- **Nhóm C** chủ yếu là *nối các mảnh đã có*, không phải xây mới. C9 (audit trail) đã có sẵn `.snapshots/`, `diff_graphs()`, template `change-log-entry.md`, khối `approval:`, `decision_register.py` — thiếu là **một view tổng hợp "ai đổi gì, ai duyệt, khi nào"**. C10 (issue-tracker) là item *rủi ro nhất với định vị skill*: hiện **không có code mạng nào** (đúng thiết kế), thêm vào dễ đụng ranh "no code generation / no network at runtime".
- **Nhóm D** gây bất ngờ: **D11 (gom code chung) gần như không có cơ sở** — trùng lặp thực tế ≈ 0. Determinism chỉ ở claude-pack; HTML/escaping chỉ ở product-spec; critique & pack **không sinh HTML**. Chỉ vài hàm tiện ích nhỏ bị copy (`_now()` 4 bản, `_hashable()` 3 bản). → D11 nên **thu hẹp drastically** (YAGNI). D12 (CI gate) mới là phần đáng làm: product-spec & critique **chưa có CI workflow riêng** dù có 31 + 10 file test.
- **Nhóm E** là leverage cao nhất. E1 & E2 **chưa tồn tại flag** (`--apply-critique`, `--discover` đều chưa có) — đây là tính năng mới. Hạ tầng cho E1 đã chín muồi (DEC register, GATE-NO-SILENT-REVERSAL, `--update` impact-pass). E4 có thể là mode mỏng trên `--export`/`--summary`. E5 = chuẩn hóa hybrid lỏng (đã chốt).

---

## Nhóm C — Deepen product-spec

### C9 — Semantic spec changelog / audit trail

**Đã có sẵn (re-use, đừng xây lại):**
- `.snapshots/` — `spec_graph.py:519` `write_snapshot()`, lưu `docs/product/visuals/.snapshots/<ISO>-<hash8>.json`; deterministic naming (content giống → tên giống).
- Delta logic — `spec_graph.py:469` `changed_nodes()`, `:492` `diff_graphs()`; `CHANGED_FIELDS = (status, scope, moscow, horizon, size, body_hash)` (`:466`). Field thiếu 1 bên → UNKNOWN (không churn giả).
- Changelog template — `assets/templates/change-log-entry.md` (đã có `author`, `date`, `affected_set`, `dims`); append vào `docs/product/change-log.md` (newest-top).
- Approval metadata — frontmatter `approval: {approved_by, approved_at, approved_version}` (`frontmatter-and-id-spec.md:171`). `status.py:207` đã có `stale_approvals` (approved nhưng đổi sau snapshot).
- Decision register — `decision_register.py`, `docs/product/decisions.md`, grammar `^DEC-\d+$`.

**Gap:** chưa có **view audit-trail hợp nhất** (timeline: artifact × action × who-approved × when × what-drifted). Các mảnh rời, chưa kết thành 1 bảng governance đọc được.

**Best practice (web):** audit trail = chronological, tamper-resistant, ghi *who/what/when/why* + version metadata (new version created, previous preserved, version incremented), exportable, retention/point-in-time. → đã khớp gần hết với cấu trúc hiện có; chỉ cần ráp + render.

**Files để chạm:** `spec_graph.py` (mở rộng diff nếu cần), `status.py` (stale_approvals đã có), template changelog, có thể thêm 1 view trong `visualize.py`/`render_*`.

### C10 — Round-trip to issue tracker (stories → GitHub Issues, giữ ID)

**Hiện trạng:** `render_export.py` xuất `docs/product/exports/...md|html`; story frontmatter giàu (`id, type, epic, status, personas, scope, moscow, size, horizon, metrics, acceptance_criteria`). **KHÔNG có code mạng** (`requests/http/urllib` đều không) — `fs_guard.py` ép mọi write nằm trong `docs/product/`.

**Best practice (web):** sync **một chiều, idempotent**; lưu ID gốc (`PRD-AUTH-E1-S1`) vào **custom field / marker / back-ref** trên issue; link PR↔issue để truy vết end-to-end. (vd issues2stories dùng custom field giữ ID.)

**Căng thẳng định vị (quan trọng):** thêm network + token vào product-spec **vi phạm** 2 lời hứa README: "No external network calls at runtime" và "non-technical PO". → C10 nên cân nhắc **không nhét vào product-spec runtime**; thay vào đó xuất một **artifact trung gian** (vd `issues.jsonl` / `gh`-import file) để dev/CI đẩy lên — giữ skill sạch, đẩy phần network ra ngoài.

**Gap:** ID-mapping back-ref (issue number → story frontmatter) chưa có; credential strategy chưa có; sync-back chưa định nghĩa.

---

## Nhóm D — Shared foundation

### D11 — Extract shared determinism + safety + HTML (drift risk)

**Phát hiện chính: trùng lặp thực tế ≈ 0.**
| Hạng mục | Thực tế | Kết luận |
|---|---|---|
| Determinism (PAX/mtime0/sorted) | Chỉ `claude-pack/pack/tarball.py` | 0 trùng |
| HTML escaping (`_escape`) | Chỉ `product-spec/render_html.py:129` | 0 trùng |
| HTML design-system (vendor+CSS) | Chỉ product-spec | 0 trùng |
| **critique & claude-pack sinh HTML?** | **KHÔNG** (Markdown only) | **không có HTML sink tương tự** |
| Hàm tiện ích nhỏ | `_now()` ×4, `_hashable()` ×3, `_inline/build_payload/_node_index` ×2-3 | trùng nhẹ |

→ Tiền đề D11 ("XSS patched ở product-spec, liệu pack/critique có sink tương tự?") **bị bác bỏ bằng dữ liệu**: hai skill kia không sinh HTML. Việc trừu tượng hóa "common base" lúc này là **over-engineering (YAGNI)**. Phần đáng làm duy nhất: gom ~2 hàm vi mô (`_now`, `_hashable`) — lợi ích nhỏ, không khẩn cấp.

**Test an toàn đã có:** `test_html_sanitize.py` (23 assert), `test_render_viewer.py` (board/explorer XSS), `test_fs_guard` (symlink), `test_safety_check` (case-insensitive), `test_pack_determinism`.

### D12 — Cross-skill regression gate trong CI

**Workflow hiện có (chỉ claude-pack):**
- `claude-pack-ci.yml` (PR paths claude-pack/**, 3 OS × 3 Python)
- `claude-pack-integration.yml` (weekly, live product-spec dogfood)
- `claude-pack-release.yml` (tag `claude-pack-v*`)

**Gap lớn:** **product-spec (31 test) & product-spec-critique (10 test) KHÔNG có CI workflow riêng** — chạy thủ công. Tổng 50 file test sẵn sàng nhưng không có gate tự động cho 2 skill cốt lõi.

**Red-team "10-cycle":** thực tế là chuỗi C9→C10→C11 (`plans/reports/cycle-11-...md`); xu hướng bug giảm 101→67→37; symlink/case-insensitive/XSS **giữ vững qua mọi cycle**. → biến thành gate lặp lại được = chạy 50 test này trong CI + vài test bug-class chéo.

---

## Nhóm E — Close the PO pipeline

### E1 — Apply-critique loop (`--apply-critique <report>`) — CHƯA TỒN TẠI

**Hạ tầng đã chín:**
- Critique report: `docs/product/critique/<ts>-<scope>.md`, mỗi finding có `lens / evidence(ID:line) / why_it_dies / fix / severity` — **nhưng KHÔNG có finding ID ổn định** (findings transient). → vòng apply phải neo theo `evidence ID:line` + nội dung, không theo finding-id.
- DEC register + grammar + script append sẵn (`decision_register.py`).
- GATE-NO-SILENT-REVERSAL (`guardrails-and-boundaries.md:102`) + `--update` impact-pass (`workflow-update.md`, 7 bước, "NEVER auto-rewrite prose").

→ E1 = **mode mới trên product-spec** ráp 3 mảnh có sẵn: đọc report → mỗi finding Keep/Change+re-approve/Defer → ghi DEC. Rủi ro thấp về hạ tầng, cao về thiết kế UX (mapping finding↔artifact khi không có finding-id).

### E2 — Discovery seed (`--discover`) — CHƯA TỒN TẠI

**Hiện trạng:** gần nhất là `--auto` (brain-dump → decompose). Vision interview (V1–V7, `interview-vision.md`) **hỏi mở** "ai là 2-4 nhóm người" — *giả định bạn đã biết personas*. Personas sống ở `PRODUCT.md` (`personas: [slug]` + bullet one-liner; narrative ở vision.md).

→ E2 bổ sung *tiền-giai-đoạn*: nạp transcript/ticket/competitor-notes → tổng hợp **ứng viên** personas/problems/JTBD để **mồi** interview thay vì bắt đầu trắng. Bổ trợ, không thay interview.

### E3 — Outcome tracking — **HOÃN** (đã chốt: sản phẩm chưa ra thị trường). Chỉ ghi khung tối thiểu, không đào sâu.

### E4 — Stakeholder brief

- `--summary` → `docs/product/exec-summary.md` (template cố định: name+core-value, BRD goals, PRDs, roadmap, personas, top-3 risks).
- `--export` → tree-slice linh hoạt (subtree + layer filter), md/html.
- **Gap:** chưa có mode "release-notes / exec one-pager" theo *audience* khác. Bilingual: cả hai kế thừa `lang` session, không có override per-flag.
→ E4 = mode mỏng tái dùng assembler có sẵn; YAGNI-friendly.

### E5 — Per-skill release identity (đã chốt: chuẩn hóa hybrid lỏng)

- `claude-pack-release.yml:27` lấy version **từ tag** `claude-pack-v*`, **không đọc SKILL.md version** (xác nhận).
- Chỉ claude-pack có `CHANGELOG.md` (keepachangelog format, theme-grouped, bao cả 3 skill). product-spec & critique **không có CHANGELOG**.
- SKILL.md version (`2.0.0 / 1.0.0 / 0.1.0`) là *nội bộ, trang trí*; bundle ship `1.1.0`.

**Best practice (web): Changesets** — mỗi package CHANGELOG riêng, tách "ý định đổi" khỏi commit, nhưng **vẫn gom phát hành**. → khớp đúng yêu cầu "nhất quán per-skill, không tách CI release". KISS: thêm CHANGELOG cho 2 skill + làm CI **đọc** SKILL.md version để verify khớp, không tách release.

---

## Tổng hợp định hướng (đầu vào cho brainstorm)

| Item | Trạng thái hạ tầng | Hướng | Cờ |
|---|---|---|---|
| C9 | Mảnh đã có, thiếu view hợp nhất | Ráp audit-trail view | ✅ giá trị/chi phí tốt |
| C10 | Không có network (cố ý) | Xuất artifact trung gian, đẩy network RA NGOÀI skill | ⚠️ đụng định vị |
| D11 | Trùng lặp ≈ 0 | Thu hẹp còn gom 2 hàm vi mô / hoặc bỏ | 🟥 YAGNI, hạ ưu tiên |
| D12 | 50 test sẵn, thiếu CI 2 skill | Thêm CI workflow product-spec + critique + bug-class chéo | ✅ đáng làm |
| E1 | Hạ tầng chín, chưa có flag | Mode mới `--apply-critique` | 🟢 leverage cao nhất |
| E2 | Chỉ có `--auto`/interview | Mode mới `--discover` (mồi interview) | 🟢 med-high |
| E3 | — | HOÃN, khung tối thiểu | ⏸ |
| E4 | assembler sẵn | Mode mỏng tái dùng | 🟡 low, rẻ |
| E5 | hybrid lỏng | +2 CHANGELOG, CI verify version | ✅ rẻ, chốt rồi |

## Unresolved questions

1. **C10 định vị:** chấp nhận đẩy network/token ra ngoài product-spec (xuất file import) hay làm skill mới *outward-facing*? (BACKLOG §E: "new skill chỉ justify cho outward-facing integration".)
2. **E1 mapping:** findings không có ID ổn định — neo theo `evidence ID:line`? Khi spec đổi sau critique thì `:line` lệch — cần chiến lược chống lệch.
3. **D11:** có chấp nhận đóng item gần như toàn bộ (chỉ giữ gom 2 hàm) không, hay vẫn muốn "design-system tái dùng" cho tương lai?
