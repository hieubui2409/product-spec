---
phase: 13
title: "Rollout PO Cleanmatic (mời lên 2.3.0 + notice license)"
status: pending
priority: P2
effort: "0.5d"
dependencies: [8, 9, 10, 12]
---

# Phase 13: Rollout PO Cleanmatic (Q7=a)

> **Dep thêm P10** (red-team): rollout checklist bật `spec-validate.yml` — file đó build ở P10. Không rollout khi P10 chưa xong.

## Overview
Khép vòng "fix → PO hưởng lợi". Sau khi upgrade-path (P9) + recipient bundle (P8) + docs (P12) sạch:
mời PO Cleanmatic lên 2.3.0 (mở khoá apply-critique/fingerprint/telemetry/`--learn`/LICENSE/tests-never-ship)
+ gửi notice license AGPL hồi tố cho bundle 1.1.0. Đây là phase TÀI LIỆU/GIAO TIẾP, không code mới.

## Mapping
- **Q7=a** — notice AGPL kèm gói nâng cấp + release-notes về hiệu lực với bundle trước 2.2.1 (CVR-F12).
- **Tiền đề số 0** (report mục 4) — chỉ-cần-PO-upgrade là mở khoá: `--apply-critique` (CVR-F05), fingerprint+inherit (CVR-F04), telemetry sinks (CVR-F06), `--learn` (CVR-F14), LICENSE (CVR-F12), tests-never-ship (CVR-F08).

## Requirements
- Functional: checklist rollout (điều kiện tiên quyết: P9 upgrade-path xanh, P8 bundle recipient, leg e2e bash3); soạn notice license AGPL + release-notes; hướng dẫn PO chạy `upgrade.sh` (dry-run trước); xác nhận sau-upgrade (no skill đôi, metric→metrics migrate, telemetry sống).
- Non-functional: không tự gửi/không tự thao tác trên repo PO — chỉ soạn hiện vật + checklist để chủ kit gửi.

## Architecture
- **Checklist rollout** (markdown trong plan/docs): (1) verify P9 dry-run sạch trên bản giống PO; (2) backup PO; (3) chạy `upgrade.sh`; (4) migrate BRD (confirm/re-approve theo GATE P5); (5) bật telemetry + spec-validate.yml (hỏi PO); (6) xác nhận telemetry sống + critique cache ghi được.
- **Notice license**: văn bản AGPL + release-notes hiệu lực với bundle <2.2.1; đính kèm gói nâng cấp.
- **Mời PO**: thông điệp ngắn nêu PO mở khoá gì khi lên 2.3.0 (6 nhóm năng lực ở drift table).

## Related Code Files
- Create: checklist rollout (docs hoặc plan), văn bản notice license (assets release hoặc docs)
- Modify: root `CHANGELOG.md`/release-notes (hiệu lực license hồi tố)
- Modify: `BACKLOG.md` (đánh dấu "Thông báo PO Cleanmatic" + Wave HIGH/MED/LOW done khi tới)
- Modify: REVIEW.md (đóng Cycle 3 khi 31 row `[x]` → roll vào `## Archive`)

## TDD — tests first
Phase tài liệu — không code. Thay TDD bằng **kiểm tra điều kiện tiên quyết** (gate):
1. Assert P9 `upgrade.sh --dry-run` sạch trên sandbox-giống-PO.
2. Assert 31/31 row REVIEW.md Cycle 3 = `[x]` trước khi đóng cycle.
3. Assert bundle recipient (P8) không còn brand/`-ck:`/skill thiếu.

## Implementation Steps
1. Verify tiền đề (P8/P9/P12 done). 2. Soạn checklist rollout. 3. Soạn notice license + release-notes. 4. Soạn thông điệp mời PO (drift → mở khoá). 5. Cập nhật BACKLOG + đóng Cycle 3 REVIEW (roll Archive). 6. Bàn giao chủ kit gửi.

## Success Criteria
- [ ] Checklist rollout đầy đủ, an toàn (backup + dry-run + GATE migrate).
- [ ] Notice license AGPL + release-notes hồi tố soạn xong.
- [ ] Thông điệp mời PO nêu rõ mở khoá gì.
- [ ] 31/31 row Cycle 3 `[x]`; cycle đóng vào Archive; BACKLOG cập nhật.

## Risk Assessment
- Rollout trước khi upgrade-path thật-sự-an-toàn. Mitigate: gate tiên quyết P9 dry-run sạch + leg bash3; KHÔNG mời PO nếu P9 chưa xanh.
- PO thao tác sai khi tự upgrade. Mitigate: checklist dry-run-trước + backup bắt buộc + chủ kit đồng hành.
