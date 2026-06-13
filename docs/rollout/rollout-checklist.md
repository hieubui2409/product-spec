# Checklist rollout — mời PO Cleanmatic lên 2.4.0

> **Dành cho chủ kit.** Đây là hiện vật *bàn giao*: skill chỉ soạn checklist, **không tự
> thao tác trên repo PO, không tự gửi**. Chủ kit chạy từng bước dưới đây (đồng hành cùng PO).

## 0. Điều kiện tiên quyết (gate — không mời PO nếu chưa đủ)

- [x] **Upgrade-path một-lệnh sẵn sàng** — `upgrade.sh`/`upgrade.ps1` (dry-run mặc định / `--apply` / `--rollback`) đã land.
- [x] **Bundle recipient sạch** — biến thể recipient (README/CLAUDE.md không brand dev, `rules: []`, không ship đồ test/dev).
- [x] **Docs/cleanup** — changelog tái-lập-từ-tag, GUIDE flag-inventory, state/cache untracked.
- [x] **PO-facing surfaces (P10a)** — build-age beacon, AC-nudge sau approve, spec-validate.yml CI.
- [ ] **Dry-run sạch trên sandbox-giống-PO** — chủ kit tự chạy `upgrade.sh --dry-run` trên một bản sao **1.x giống PO** và xác nhận kế hoạch hợp lý (không xoá nhầm, legacy-map khớp). **Bắt buộc trước khi mời.**

## 1. Sao lưu (bắt buộc)

- [ ] PO commit/ý đẩy hết thay đổi đang mở trên repo của họ (`git status` sạch hoặc đã stash).
- [ ] Sao lưu toàn bộ `docs/product/` của PO (bản chụp ngoài git, vd `tar`), phòng khi cần khôi phục thủ công.

## 2. Dry-run trên repo PO (xem trước, không đổi gì)

- [ ] Chạy `bash upgrade.sh` (mặc định dry-run) trong repo PO → đọc kế hoạch: file nào thêm/đè/xoá-với-backup, skill nào stale/same.
- [ ] PO + chủ kit cùng rà: không có file PO-edited bị đè ngoài ý muốn; legacy 1.x được nhận diện đúng.

## 3. Áp dụng nâng cấp

- [ ] `bash upgrade.sh --apply` → sweep atomic (all-or-nothing, tự rollback nếu lỗi giữa chừng).
- [ ] Nếu có sự cố → `bash upgrade.sh --rollback` khôi phục về trước-upgrade.

## 4. Migrate dữ liệu spec (GATE — không tự sửa approved)

- [ ] Nếu BRD còn dùng key `metric:` cũ → chạy `migrate_metric_to_metrics.py` **dry-run trước** (0 byte), rồi `--apply` kèm `--confirmed-by <PO> --date <ngày>`.
- [ ] Mọi thay đổi chạm tài liệu **approved** phải theo GATE: PO xác nhận / re-approve (owner + ngày). Không flip ngầm.

## 5. Bật quan trắc + CI (hỏi PO)

- [ ] Telemetry hooks: installer tự đăng ký (idempotent); `.claude/telemetry/` đã được thêm `.gitignore`.
- [ ] spec-validate GitHub Action: installer **hỏi** — nếu PO đồng ý, cài vào `.github/workflows/spec-validate.yml` (hoặc `INSTALL_SPEC_VALIDATE=1`). Nếu PO có `python-package.yml` stock → cân nhắc xoá.

## 6. Xác nhận sau nâng cấp

- [ ] Không còn skill cài đôi (mỗi skill 1 bản, version khớp).
- [ ] `metric:` đã migrate sang `metrics:` (nếu có) + spec validate xanh.
- [ ] Telemetry đang ghi (chạy vài lệnh skill → kiểm `.claude/telemetry/` có dữ liệu).
- [ ] Critique cache ghi được; `--status` hiện build-age beacon (bản + số ngày đóng gói).

## 7. Bàn giao

- [ ] Gửi PO: [thông điệp mời 2.4.0](po-invitation-2.4.0.md) + [notice license](license-notice-agpl-draft.md).
- [ ] Sau khi PO chạy ổn → cập nhật `docs/audit-trail/BACKLOG.md` mục "Thông báo PO Cleanmatic".

## Rủi ro & giảm thiểu

- **Rollout khi upgrade-path chưa thật-sự an toàn** → gate mục 0 (dry-run sạch trên sandbox-giống-PO) là bắt buộc.
- **PO thao tác sai khi tự upgrade** → dry-run-trước + backup bắt buộc + chủ kit đồng hành (mục 1-3).
