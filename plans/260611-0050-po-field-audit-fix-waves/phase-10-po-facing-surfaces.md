---
phase: 10
title: "PO-facing surfaces"
status: pending
priority: P2
effort: "4d"
dependencies: [1, 7]
---

# Phase 10: PO-facing surfaces (#2, #6, #7, #12, #13, #14)

> **2 stage (decouple rollout — lựa chọn PO):**
> **10a SHIP-CRITICAL (~1.5d, chặn rollout P13):** #2 spec-validate.yml + #12 AC-nudge (KHÔNG đụng status.py → chạy SỚM, deps chỉ [1]) + #7 age-beacon (đụng status.py → sau P7). Đây là phần value-critical PO cần để upgrade.
> **10b DEFERRED-HEAVY (~2.5d, KHÔNG chặn rollout):** #6 visuals-staleness/retention + #13 decision-index + #14 snapshot/restore. Làm tiếp sau P7 nhưng **rollout không đợi**. #14 snapshot/restore-engine cân nhắc thu hẹp (PO đã có git) — giữ VCS-nudge, engine có thể hoãn (DEC).

## Overview
Gói tính năng PO-facing cỡ S khép pain trực tiếp của PO: CI validate-on-push, visuals đông cứng, không biết
bản mới, AC khó đọc, DEC không tra được, không snapshot/restore. Mỗi đề xuất 1 deliverable độc lập, TDD riêng.

> **Serialize + scope (red-team):** #7/#14 đụng `status.py` chung P6/P7 → đi SAU (RE-READ trước sửa). Phase nhồi 6 deliverable rời → **khi cook, tách thành 6 sub-task độc lập** (mỗi cái 1 commit + tick riêng), pin file đích cụ thể trước khi code; cái nào phình quá thì tách phase con. KHÔNG gộp commit.

## Deliverables
### #2 spec-validate.yml CI (Q4=a) — CVR-F07/POX-F01
- Template GH Action chạy `check_traceability`/`check_consistency`/`check_fence` trên `docs/product/`; summary tiếng Việt vào job summary; installer hỏi PO bật không; khuyên xoá `python-package.yml` stock.
- Runner cần PyYAML → `pip install` 1 dòng + smoke job.
- TDD: lint workflow YAML hợp lệ; smoke job assert summary VI; test "không phụ thuộc file kit".

### #6 Visuals latest + staleness + retention — POX-F04/CVR-M3/BUG-F07
- `*-latest.html` alias ổn định + banner "render lúc X, spec lệch N node"; `--viz --clean`; reuse khi content-hash trùng (không ghi file mới); nudge re-render hậu approve.
- TDD: render 2 lần content trùng → KHÔNG file mới; spec đổi sau render → banner báo lệch N; `--clean` xoá cũ giữ latest.

### #7 Version age-beacon trong `--status` — ARC-F03/CVR-F02
- `status.py` đọc MANIFEST.json (`built_at`/`bundle_version`) → 1 dòng VI "bản X, cài N ngày — hỏi người phát hành bản mới". KHÔNG network.
- TDD: MANIFEST cũ N ngày → dòng beacon hiện; thiếu MANIFEST → im lặng (không lỗi).

### #12 AC-readable surface (discoverability) — POX-F05
- Công cụ ĐÃ CÓ (`workflow-export.md` + `render_export.py`) — thêm nudge sau approve + 1 dòng GUIDE; hoặc khối AC render-only "generated — đừng sửa tay".
- TDD: sau `--approve` → nudge export hiện; GUIDE có mục.

### #13 Decision index view — POX-F11
- `--decision --list PRD-X` từ `decision_register.py` (đã có 1.1.0): lọc theo `affects`/date/status, vẽ chain supersede; dashboard hàng DEC.
- TDD: fixture 44 DEC → `--list PRD-X` trả đúng tập `affects`; chain supersede đúng thứ tự.

### #14 Snapshot/restore + VCS nudge — POX-F10/CVR-M2
- `--snapshot`/`--restore <ts>` tự tạo trước migration/update lớn + README trong thư mục snapshot; `--status`/validate warn khi `docs/product` ngoài git hoặc diff lớn chưa commit; Closing-the-Loop gợi ý commit sau mốc approve.
- TDD: `--snapshot` tạo thư mục + README; `--restore` khôi phục đúng; warn khi ngoài git.

## Related Code Files
- Create: `.github/workflows/spec-validate.yml` (template recipient) + installer hỏi
- Modify: `.claude/skills/product-spec/scripts/visualize.py`/render (latest+staleness+retention), `status.py` (age-beacon + open-questions phối P7 + VCS warn)
- Modify: `render_export.py` nudge, GUIDE-EN/VI (#12)
- Create: `--decision --list` view (decision_register data), `--snapshot`/`--restore`
- Modify: REVIEW.md (không row ledger — build-new; ghi DEC), EVIDENCE nếu chạm data

## TDD — tests first
Mỗi deliverable có RED test riêng (liệt kê ở từng mục trên). Viết RED trước, GREEN sau, không gộp.

## Success Criteria
- [ ] spec-validate.yml lint xanh + smoke VI + không phụ thuộc file kit.
- [ ] Visuals: latest alias + banner lệch + reuse-hash + `--clean`.
- [ ] Age-beacon hiện theo tuổi cài; thiếu MANIFEST im lặng.
- [ ] AC nudge sau approve + GUIDE mục.
- [ ] `--decision --list PRD-X` đúng `affects` + chain supersede.
- [ ] `--snapshot`/`--restore` đúng; VCS warn ngoài git.

## Risk Assessment
- spec-validate.yml cần PyYAML runner. Mitigate: `pip install` + smoke.
- Nhiều deliverable nhỏ → trôi scope. Mitigate: TDD từng cái, tick độc lập; cái nào quá thì tách phase con.
