---
id: PRD-PREMIUM-E1
type: epic
prd: PRD-PREMIUM
brd_goals: [BRD-G3]
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: in
moscow: should
horizon: later
metrics: [premium-conversion-rate, arpu]
risks:
  - description: "Người dùng trả phí nhưng không thấy giá trị tương xứng (boost không tăng match thật) dẫn tới huỷ gói và đánh giá xấu"
    impact: med
    likelihood: med
    mitigation: "Đặt kỳ vọng rõ ràng về quyền lợi boost (tăng hiển thị, không hứa tăng match); đo và minh bạch hiệu quả"
    status: open
---

# Gói trả phí Premium — Epic PRD-PREMIUM-E1

## Goal | Mục tiêu

Cho người dùng nâng cấp lên gói trả phí để xem ai đã thích mình và boost hồ sơ — mở dòng doanh thu premium
phục vụ mục tiêu hoà vốn vận hành, trong khi giữ trải nghiệm miễn phí lõi còn dùng được.

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** PRD-PREMIUM — gói trả phí: xem ai đã thích mình, boost hồ sơ, thích không giới hạn.
- **BRD goal | Mục tiêu BRD:** BRD-G3 — doanh thu premium đủ hoà vốn vận hành vào năm 2 (`premium-conversion-rate`, `arpu`).

## Success Criteria | Tiêu chí thành công

Người dùng trả phí có thể xem đầy đủ danh sách những người đã thích hồ sơ của mình và kích hoạt boost hồ sơ
với quyền lợi rõ ràng — đo qua tỉ lệ chuyển đổi premium và ARPU.

## Scope | Phạm vi

Trong phạm vi: xem ai đã thích mình, boost hồ sơ có thời hạn, đồng bộ quyền lợi gói trả phí. Ngoài phạm vi:
khám phá & quẹt (PRD-MATCH), xác minh danh tính (PRD-SAFETY), nhắn tin (PRD-CHAT), tích hợp cổng thanh toán
cụ thể (đội build chọn ở giai đoạn triển khai).
