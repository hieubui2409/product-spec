---
phase: 11
title: "Product-insight + self-learning"
status: pending
priority: P3
effort: "2d"
dependencies: [2, 3, 12]
---

# Phase 11: Product-insight + self-learning (#8, #11, #15)

> **Serialize:** #15 đổi contract đọc `assemble_audit_trail.py` chung P12 (truncate ascii) → P12 đi TRƯỚC; P11 RE-READ file + test rollover end-to-end SAU khi cả 2 sửa land.

## Overview
Lớp insight sản phẩm còn thiếu: không sink nào ghi artifact-events; vòng phản hồi về dev đứt; change-log
không cap/rotate. Thêm 3 lớp — đều report-only/advisory, giữ boundary A9 (kit không tự sửa từ học máy).

## Deliverables
### #8 Artifact-events sink + lens "artifact heat" — ARC-F05
- Tái dùng matcher PostToolUse `Edit|Write|MultiEdit` đã đăng ký → ghi `{ts, artifact_path, op, session}` (PATH-only, local, không nội dung); invocations ghi tóm tắt flag; lens kể VI "PRD nào bị sửa nhiều".
- Privacy: chỉ path + op, KHÔNG nội dung diff.
- TDD: edit 1 artifact 3 lần → sink 3 record path-only; lens narrate "PRD-X sửa 3 lần"; assert KHÔNG nội dung trong record.

### #11 Usage-summary export + self-learning slice (report-only) — ARC-F06
- `telemetry --export-summary` markdown aggregate (PO duyệt rồi tự gửi dev); harvester read-only đọc self-corrections + repeat-findings → report "đề nghị chỉnh interview/template", KHÔNG tự sửa (giữ boundary A9).
- Privacy: PO duyệt tay, opt-in từng lần.
- TDD: export trả markdown aggregate; harvester trả ĐỀ NGHỊ (không ghi vào skill/template); opt-in gate.

### #15 change-log rotation + path-exists check — CVR-F10
- Archive theo tháng (`change-log/2026-06.md`) hoặc cap+rollover script-side; check nhẹ "đường dẫn nhắc trong change-log có tồn tại"; vá `assemble_audit_trail` đọc theo contract mới.
- TDD: change-log vượt cap → rollover sang file tháng; `assemble_audit_trail` đọc đủ qua rollover; path-exists check báo path chết.

## Requirements
- Functional: artifact-events sink path-only; usage export markdown PO-duyệt; self-learning chỉ report; change-log rotate + path-check.
- Non-functional: **giữ boundary A9** (kit không tự tiến hoá từ học máy — chỉ đề nghị); privacy path-only + opt-in; fail-open.

## Related Code Files
- Modify: `.claude/skills/telemetry/scripts/register_telemetry_hooks.py` (artifact-events PostToolUse) + sink + lens
- Create: `telemetry --export-summary` + harvester read-only (report) + test
- Modify: `assemble_audit_trail.py` (contract rollover), change-log writer + rotation + path-check
- Modify: REVIEW.md (không row ledger — build-new; ghi DEC), EVIDENCE

## TDD — tests first
Mỗi deliverable RED test riêng (ở từng mục). Đặc biệt assert privacy (path-only) + boundary A9 (không tự ghi skill/template).

## Implementation Steps
1. Viết RED tests. 2. artifact-events sink path-only + heat lens. 3. export-summary + harvester report-only + opt-in. 4. change-log rotation + path-check + vá assemble_audit_trail. 5. GREEN. 6. Ghi DEC + EVIDENCE.

## Success Criteria
- [ ] Artifact-events ghi path-only (test khẳng định KHÔNG nội dung); heat lens narrate VI.
- [ ] `--export-summary` markdown PO-duyệt; harvester chỉ ĐỀ NGHỊ, không tự sửa (boundary A9 giữ).
- [ ] change-log rotate theo tháng; assemble_audit_trail đọc đủ; path-check báo path chết.

## Risk Assessment
- **[red-team] Self-learning dễ vượt boundary A9 (tự sửa template).** Mitigate: harvester READ-ONLY, output là report đề-nghị; test khẳng định không ghi skill/template.
- Privacy artifact-events. Mitigate: path+op only, opt-in, gitignore (P8), test no-content.
- Đổi contract change-log đọc. Mitigate: vá assemble_audit_trail CÙNG LÚC + test rollover end-to-end.
