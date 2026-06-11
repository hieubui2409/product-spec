---
phase: 7
title: "Session staleness + supersede sweep + open-questions"
status: pending
priority: P2
effort: "1d"
dependencies: [1, 5, 6]
---

# Phase 07: Session staleness + open-questions (đề xuất #4, Q5=a)

> **Serialize:** đụng `check_consistency.py` + `status.py` chung P5/P6/P10 → thứ tự P5→P6→P7→P10; RE-READ 2 file trước khi sửa.

## Overview
`.session.md` đóng băng 06-02 chứa 4 fact bị supersede, nằm ĐÚNG nguồn GATE-NEVER-ASSUME cho phép assume
→ một phiên mới có thể silent-reversal đúng nghĩa. Thêm staleness guard + supersede-sweep + sổ open-questions.

## Mapping
- **CVR-F03 + POX-F03** (High) — `.session.md` đóng băng chứa 4 fact bị supersede (metric 30-vs-50 ngược DEC-43, "Sepay VÀ Casso" ngược DEC-4, "toàn draft" vs 134 approved, đếm artifact cũ). HEAD không có staleness check.
- **POX-M2** (Med) — 3 câu hỏi kinh doanh "Vẫn còn mở" từ 06-02 không có nhà; story `must` mang tham số treo approved với ghi chú "cần PO xác định"; 0/44 DEC đụng; không workflow theo dõi open-questions.

## Requirements
- Functional (Q5=a): khi 2 nguồn lệch → `decisions.md` THẮNG; validate warn khi `.session.md.last_updated` < max(`updated` của artifact); supersede-sweep quét session/PRODUCT.md tìm fact bị DEC thay; sổ open-questions trong `--status`; `--approve` cảnh báo marker "cần PO xác định".
- Non-functional: false-positive warn nhẹ chấp nhận được; KHÔNG loại `.session.md` khỏi nguồn (giữ giá trị resume).

## Architecture
- **Staleness**: validate so `.session.md` last_updated vs max(updated) các artifact → warn "session ôi thiu N ngày, fact có thể bị supersede".
- **Decisions-priority**: khi assume từ `.session.md` mà `decisions.md` có ruling khác → ưu tiên decisions.md + báo lệch (không tự ghi đè session).
- **Supersede-sweep**: quét `.session.md`/`PRODUCT.md` đối chiếu DEC register → liệt kê fact bị thay (vd DEC-43 metric, DEC-4 payment).
- **Open-questions first-class**: scan marker "cần PO xác định"/"Vẫn còn mở" trong story `must` → sổ trong `--status`; `--approve` cảnh báo nếu artifact mang marker chưa giải.

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/check_consistency.py` (staleness warn) hoặc rule riêng
- Modify: `.claude/skills/product-spec/scripts/status.py` (sổ open-questions)
- Create: supersede-sweep script (đọc decision_register + session/PRODUCT) + test
- Modify: `.claude/skills/product-spec/SKILL.md` (`--approve` cảnh báo marker; ưu tiên decisions.md)
- Modify: REVIEW.md (không có row ledger — đây là build-new #4; ghi DEC), EVIDENCE nếu chạm data PO

## TDD — tests first
1. Staleness RED: `.session.md` last_updated < artifact updated → warn. RED hiện tại (0 staleness check).
2. Decisions-priority RED: session nói metric=30, DEC-43 nói 50 → assume trả 50 + báo lệch.
3. Supersede-sweep RED: fixture session chứa fact bị DEC thay → sweep liệt kê đúng.
4. Open-questions RED: story `must` có "cần PO xác định" → `--status` liệt kê; `--approve` cảnh báo.

## Implementation Steps
1. Viết RED tests. 2. Staleness warn. 3. Decisions-priority resolver. 4. Supersede-sweep script. 5. Open-questions sổ + approve-warn. 6. GREEN. 7. Ghi DEC; EVIDENCE nếu chạm data PO.

## Success Criteria
- [ ] `.session.md` ôi thiu → validate warn.
- [ ] Lệch session↔decisions → ưu tiên decisions.md + báo.
- [ ] Supersede-sweep liệt kê đúng 4 fact bị thay của PO.
- [ ] Open-questions hiện trong `--status`; `--approve` cảnh báo marker treo.

## Risk Assessment
- False-positive staleness gây nag. Mitigate: warn-only, ngưỡng theo ngày, không block.
- Parse marker "cần PO xác định" miss biến thể chữ. Mitigate: tập marker mở rộng + test biến thể.
