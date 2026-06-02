---
id: PRD-CHAT-E1-S1
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
size: M
horizon: next
metrics: [mau-monthly]
acceptance_criteria:
  - "Giả sử hai người đã match, khi một người gửi tin nhắn văn bản, thì người kia nhận được trong vòng 2 giây khi đang online."
  - "Giả sử tin nhắn đã gửi, khi máy chủ nhận, thì trạng thái 'đã gửi' hiển thị dưới 1 giây; khi người nhận đã mở, thì chuyển sang 'đã nhận'."
  - "Giả sử mất mạng tạm thời, khi người dùng gửi tin nhắn, thì tin được xếp hàng và tự gửi lại khi có mạng lại, không mất tin nhắn."
  - "Giả sử mở lại cuộc trò chuyện, khi tải, thì 50 tin nhắn gần nhất hiển thị theo đúng thứ tự thời gian."
---

# Gửi và nhận tin nhắn realtime — Story PRD-CHAT-E1-S1

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** người dùng đã match (P-URBAN / P-PROVINCE / P-RETURNEE)
**I want** | **Tôi muốn** gửi và nhận tin nhắn văn bản theo thời gian thực với người đã match
**so that** | **để** chúng tôi duy trì một cuộc trò chuyện thật thay vì chỉ dừng ở một match.

## Acceptance Criteria | Tiêu chí chấp nhận

- Giả sử hai người đã match, khi một người gửi tin nhắn văn bản, thì người kia nhận được trong vòng 2 giây khi đang online.
- Giả sử tin nhắn đã gửi, khi máy chủ nhận, thì trạng thái "đã gửi" hiển thị dưới 1 giây; khi người nhận đã mở, thì chuyển sang "đã nhận".
- Giả sử mất mạng tạm thời, khi người dùng gửi tin nhắn, thì tin được xếp hàng và tự gửi lại khi có mạng lại, không mất tin nhắn.
- Giả sử mở lại cuộc trò chuyện, khi tải, thì 50 tin nhắn gần nhất hiển thị theo đúng thứ tự thời gian.
