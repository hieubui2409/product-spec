---
id: PRD-AIREC-E1-S1
type: story
epic: PRD-AIREC-E1
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: in
moscow: could
size: L
horizon: later
metrics: [weekly-match-rate]
acceptance_criteria:
  - "Giả sử người dùng có đủ dữ liệu tương tác (đã quẹt từ 20 hồ sơ trở lên), khi mở màn khám phá, thì hệ thống xếp hồ sơ theo điểm gợi ý của mô hình giảm dần, và hồ sơ điểm cao nhất nằm ở vị trí đầu tiên."
  - "Giả sử người dùng mới chưa đủ dữ liệu (đã quẹt dưới 20 hồ sơ), khi mở màn khám phá, thì hệ thống xếp hồ sơ theo thứ tự mặc định (khoảng cách + độ hoạt động) và màn khám phá không bao giờ trống."
  - "Giả sử người dùng quẹt hoặc một match chuyển thành nhắn tin duy trì, khi sự kiện xảy ra, thì hệ thống ghi nhận tín hiệu tương tác đó để dùng làm dữ liệu huấn luyện cho gợi ý phiên sau."
  - "Giả sử mô hình tính điểm gợi ý cho một phiên khám phá, khi tải màn khám phá, thì 20 hồ sơ đầu tiên hiển thị trong vòng 2 giây trên thiết bị di động phổ thông tại Việt Nam."
---

# Xếp hạng khám phá theo gợi ý AI — Story PRD-AIREC-E1-S1

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** người dùng độc thân muốn gặp đúng người mà không phải lướt quá nhiều (P-URBAN / P-PROVINCE / P-RETURNEE)
**I want** | **Tôi muốn** màn khám phá ưu tiên những hồ sơ có khả năng hợp với tôi hơn
**so that** | **để** tôi tăng cơ hội tạo match phù hợp mỗi tuần mà không tốn nhiều thời gian.

## Acceptance Criteria | Tiêu chí chấp nhận

- Giả sử người dùng có đủ dữ liệu tương tác (đã quẹt từ 20 hồ sơ trở lên), khi mở màn khám phá, thì hệ thống xếp hồ sơ theo điểm gợi ý của mô hình giảm dần, và hồ sơ điểm cao nhất nằm ở vị trí đầu tiên.
- Giả sử người dùng mới chưa đủ dữ liệu (đã quẹt dưới 20 hồ sơ), khi mở màn khám phá, thì hệ thống xếp hồ sơ theo thứ tự mặc định (khoảng cách + độ hoạt động) và màn khám phá không bao giờ trống.
- Giả sử người dùng quẹt hoặc một match chuyển thành nhắn tin duy trì, khi sự kiện xảy ra, thì hệ thống ghi nhận tín hiệu tương tác đó để dùng làm dữ liệu huấn luyện cho gợi ý phiên sau.
- Giả sử mô hình tính điểm gợi ý cho một phiên khám phá, khi tải màn khám phá, thì 20 hồ sơ đầu tiên hiển thị trong vòng 2 giây trên thiết bị di động phổ thông tại Việt Nam.
