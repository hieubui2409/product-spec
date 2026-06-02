---
id: PRD-CHAT-E1-S2
type: story
epic: PRD-CHAT-E1
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
  - "Giả sử hai người đã match, khi một trong hai mở màn hình match, thì nút mở cuộc trò chuyện hiển thị và dẫn tới đúng cuộc trò chuyện 1-1."
  - "Giả sử hai người CHƯA match, khi cố gửi tin nhắn cho nhau, thì máy chủ từ chối và không có tin nhắn nào được lưu hay gửi đi."
  - "Giả sử một người gỡ match (unmatch), khi đó, thì cuộc trò chuyện bị đóng cho cả hai trong vòng 5 giây và không gửi thêm được tin nhắn."
---

# Cổng chặn nhắn tin theo match — Story PRD-CHAT-E1-S2

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** người dùng đã match (P-URBAN / P-PROVINCE / P-RETURNEE)
**I want** | **Tôi muốn** chỉ nhắn tin được với người đã match và không bị người lạ nhắn tin
**so that** | **để** không gian trò chuyện an toàn, đúng với cam kết kết nối thật.

## Acceptance Criteria | Tiêu chí chấp nhận

- Giả sử hai người đã match, khi một trong hai mở màn hình match, thì nút mở cuộc trò chuyện hiển thị và dẫn tới đúng cuộc trò chuyện 1-1.
- Giả sử hai người CHƯA match, khi cố gửi tin nhắn cho nhau, thì máy chủ từ chối và không có tin nhắn nào được lưu hay gửi đi.
- Giả sử một người gỡ match (unmatch), khi đó, thì cuộc trò chuyện bị đóng cho cả hai trong vòng 5 giây và không gửi thêm được tin nhắn.
