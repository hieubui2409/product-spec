# Rollout — mời PO Cleanmatic lên 2.3.0

Hiện vật **bàn giao cho chủ kit** để mời PO Cleanmatic nâng cấp. Đóng vòng
"fix → PO hưởng lợi" sau khi upgrade-path + bundle recipient + docs + PO-facing surfaces đã sạch.

> **Skill chỉ SOẠN, không GỬI/không THAO TÁC trên repo PO.** Mọi bước outward-facing (gửi
> thông điệp, PO chạy `upgrade.sh`, tag/push bản phát hành) là việc của **chủ kit**.

## Hiện vật

| File | Dùng để | Trạng thái |
|------|---------|------------|
| [rollout-checklist.md](rollout-checklist.md) | Chủ kit chạy từng bước nâng cấp (backup → dry-run → apply → migrate GATE → bật quan trắc → xác nhận) | Sẵn dùng |
| [po-invitation-2.3.0.md](po-invitation-2.3.0.md) | Thông điệp mời PO + 6 nhóm mở khoá | Bản nháp giọng văn |
| [license-notice-agpl-draft.md](license-notice-agpl-draft.md) | Notice AGPL-3.0 + đoạn release-notes hồi tố <2.2.1 | ⚠️ **DRAFT — cần rà pháp lý** |

## Trước khi mời (gate)

1. `upgrade.sh --dry-run` sạch trên một sandbox **1.x giống PO** (chủ kit tự chạy).
2. Bundle recipient không còn brand dev / skill thiếu (đã verify ở khâu đóng gói).
3. P10a PO-facing surfaces đã land (build-age beacon · AC-nudge · spec-validate.yml).

## Lưu ý phạm vi

Cycle 3 (field-audit) **chưa đóng**: P10b (#6/#13/#14) + P11 (#8/#11/#15) + #9 còn hoãn (làm
song song *sau* rollout theo quyết định PO). Rollout này ship phần value-critical của 2.3.0;
các năng lực hoãn sẽ vào bản 2.3.x/2.4 sau. Xem `docs/audit-trail/BACKLOG.md`.
