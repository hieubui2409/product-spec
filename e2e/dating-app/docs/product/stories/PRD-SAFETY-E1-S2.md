---
id: PRD-SAFETY-E1-S2
type: story
epic: PRD-SAFETY-E1
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: core-value
moscow: must
size: S
horizon: next
metrics: [mau-monthly]
acceptance_criteria:
  - "Giả sử người dùng đang xem một hồ sơ, khi chọn 'Báo cáo' và chọn lý do lừa đảo/catfish, thì báo cáo được ghi nhận và hiển thị xác nhận trong vòng 3 giây."
  - "Giả sử một báo cáo được gửi, khi hệ thống tiếp nhận, thì báo cáo vào hàng đợi kiểm duyệt kèm ID hồ sơ bị báo cáo, lý do, và thời điểm, trong vòng 10 giây."
  - "Giả sử một hồ sơ nhận từ 5 báo cáo lừa đảo độc lập trở lên trong 24 giờ, khi đạt ngưỡng, thì hồ sơ tự động bị ẩn khỏi khám phá và được đánh dấu ưu tiên kiểm duyệt khẩn."
  - "Giả sử người dùng đã báo cáo một hồ sơ, khi họ xem lại hồ sơ đó, thì hệ thống không cho gửi trùng báo cáo cho cùng hồ sơ trong 24 giờ."
---

# Báo cáo hồ sơ lừa đảo/catfish — Story PRD-SAFETY-E1-S2

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** người dùng độc thân (P-URBAN / P-PROVINCE / P-RETURNEE)
**I want** | **Tôi muốn** báo cáo một hồ sơ nghi lừa đảo hoặc catfish
**so that** | **để** đội kiểm duyệt xử lý và cộng đồng được bảo vệ khỏi tài khoản giả.

## Acceptance Criteria | Tiêu chí chấp nhận

- Giả sử người dùng đang xem một hồ sơ, khi chọn "Báo cáo" và chọn lý do lừa đảo/catfish, thì báo cáo được ghi nhận và hiển thị xác nhận trong vòng 3 giây.
- Giả sử một báo cáo được gửi, khi hệ thống tiếp nhận, thì báo cáo vào hàng đợi kiểm duyệt kèm ID hồ sơ bị báo cáo, lý do, và thời điểm, trong vòng 10 giây.
- Giả sử một hồ sơ nhận từ 5 báo cáo lừa đảo độc lập trở lên trong 24 giờ, khi đạt ngưỡng, thì hồ sơ tự động bị ẩn khỏi khám phá và được đánh dấu ưu tiên kiểm duyệt khẩn.
- Giả sử người dùng đã báo cáo một hồ sơ, khi họ xem lại hồ sơ đó, thì hệ thống không cho gửi trùng báo cáo cho cùng hồ sơ trong 24 giờ.
