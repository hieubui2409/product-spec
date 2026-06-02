---
id: PRD-SAFETY-E1-S1
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
size: M
horizon: next
metrics: [mau-monthly]
acceptance_criteria:
  - "Giả sử người dùng ở bước xác minh, khi nộp một selfie sống và một ảnh giấy tờ tuỳ thân, thì hệ thống đối chiếu khuôn mặt và trả kết quả trong vòng 60 giây."
  - "Giả sử selfie khớp ảnh giấy tờ ở mức tin cậy >= 90%, khi đối chiếu hoàn tất, thì hồ sơ được gắn huy hiệu 'đã xác minh' và huy hiệu hiển thị trên hồ sơ trong vòng 5 giây."
  - "Giả sử mức khớp dưới 90% hoặc phát hiện giả mạo liveness, khi đối chiếu hoàn tất, thì hệ thống từ chối xác minh, hiển thị lý do, và cho phép nộp lại tối đa 3 lần mỗi 24 giờ."
  - "Giả sử xác minh thành công, khi quá trình kết thúc, thì ảnh giấy tờ gốc bị xoá khỏi lưu trữ trong vòng 24 giờ và không bao giờ hiển thị cho người dùng khác."
---

# Xác minh selfie–giấy tờ — Story PRD-SAFETY-E1-S1

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** người dùng độc thân (P-URBAN / P-PROVINCE / P-RETURNEE)
**I want** | **Tôi muốn** xác minh danh tính bằng selfie sống đối chiếu với giấy tờ tuỳ thân
**so that** | **để** tôi nhận huy hiệu "đã xác minh" và người khác tin tôi là người thật.

## Acceptance Criteria | Tiêu chí chấp nhận

- Giả sử người dùng ở bước xác minh, khi nộp một selfie sống và một ảnh giấy tờ tuỳ thân, thì hệ thống đối chiếu khuôn mặt và trả kết quả trong vòng 60 giây.
- Giả sử selfie khớp ảnh giấy tờ ở mức tin cậy >= 90%, khi đối chiếu hoàn tất, thì hồ sơ được gắn huy hiệu "đã xác minh" và huy hiệu hiển thị trên hồ sơ trong vòng 5 giây.
- Giả sử mức khớp dưới 90% hoặc phát hiện giả mạo liveness, khi đối chiếu hoàn tất, thì hệ thống từ chối xác minh, hiển thị lý do, và cho phép nộp lại tối đa 3 lần mỗi 24 giờ.
- Giả sử xác minh thành công, khi quá trình kết thúc, thì ảnh giấy tờ gốc bị xoá khỏi lưu trữ trong vòng 24 giờ và không bao giờ hiển thị cho người dùng khác.
