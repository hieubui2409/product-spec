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

### #7 Version age-beacon trong `--status` — ARC-F03/CVR-F02 — ✅ LANDED (P10a)
- **DEC-P10a-1 (premise gãy → PO ruling):** scout phát hiện installer CỐ TÌNH loại `MANIFEST.json` khỏi cây cài (`install.sh:359-363` grep loại; install.ps1 `$ExcludeNames`) và KHÔNG ghi stamp/receipt nào → không có nguồn dữ liệu trong cây PO. PO chốt **build-age qua MANIFEST stamp** (không phải install-age): installer (sh+ps1) copy `MANIFEST.json` → `<target>/.claude/MANIFEST.json`; `status.py` đọc `<root>/.claude/MANIFEST.json`.
- `status.py._bundle_age` đọc `bundle_version`+`built_at` → key JSON `bundle_age {bundle_version, built_at, age_days}` (age = ngày kể từ **đóng gói**, clamp tương lai→0); LLM render 1 dòng VI "bản X, **đóng gói** N ngày trước — hỏi người phát hành bản mới hơn" theo `references/workflow-status.md`. KHÔNG network. Build-age = tín hiệu cũ-kỹ trung thực hơn install-age (bắt được case cài bản đã cũ).
- Fail-silent: thiếu/hỏng/non-string/empty MANIFEST → `bundle_age: null` (key luôn có, không raise, không gate).
- Tương tác upgrade (P09): upgrade planner là **allowlist** (chỉ duyệt `legacy_map.entries`), KHÔNG scan-xoá file lạ → stamp không bị sweep; upgrade chạy install.sh mới refresh stamp.
- TDD: 12 test `test_status_bundle_age.py` (build-age N ngày, baseline-path, future-clamp, absent/malformed/missing-built_at/unparseable/non-string/empty-version/empty-built_at silent, read-only, CLI) + 1 e2e `test_install_drops_manifest_stamp_for_build_age_beacon` (stamp byte-identical, không rơi root, có 2 key beacon).

### #12 AC-readable surface (discoverability) — POX-F05 — ✅ LANDED (P10a)
- Công cụ ĐÃ CÓ (`workflow-export.md` + `render_export.py`) — chọn option **nudge sau approve** (không phải render-only block): SKILL.md `--approve` row + GUIDE B4 (EN/VI) trỏ `--export` → AC vừa duyệt thành mặt tài liệu mang-đi/chia-sẻ. Framed "a suggestion, never automatic" (GATE-NEVER-ASSUME). DRY: trỏ tool export sẵn có, không logic mới.
- TDD: 3 test `test_approve_export_nudge.py` (SKILL approve row có `--export`; GUIDE-EN/VI B4 trỏ export). Footprint SKILL.md +10 → regen baseline (chỉ product-spec, GUIDE không đo).

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
- [x] Age-beacon (build-age) hiện theo tuổi đóng gói; thiếu MANIFEST im lặng. (DEC-P10a-1)
- [x] AC nudge sau approve + GUIDE mục. (P10a)
- [ ] `--decision --list PRD-X` đúng `affects` + chain supersede.
- [ ] `--snapshot`/`--restore` đúng; VCS warn ngoài git.

## Risk Assessment
- spec-validate.yml cần PyYAML runner. Mitigate: `pip install` + smoke.
- Nhiều deliverable nhỏ → trôi scope. Mitigate: TDD từng cái, tick độc lập; cái nào quá thì tách phase con.
