---
id: PRD-CHAT-E1
type: epic
prd: PRD-CHAT
brd_goals: [BRD-G1]
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: core-value
moscow: must
horizon: next
metrics: [mau-monthly]
risks:
  - description: "Cổng chặn theo match lỏng lẻo cho phép người chưa match nhắn tin, phá vỡ niềm tin"
    impact: high
    likelihood: low
    mitigation: "Kiểm tra trạng thái match ở phía máy chủ trước mỗi lần mở/gửi, không tin client"
    status: open
---

# Nhắn tin realtime giữa hai người đã match — Epic PRD-CHAT-E1

## Goal | Mục tiêu

Cho phép hai người đã match mở một cuộc trò chuyện 1-1, gửi và nhận tin nhắn văn bản theo thời gian
thực — biến mỗi match thành một kênh trò chuyện thật, nuôi north-star về cặp đôi nhắn tin qua lại từ
7 ngày trở lên.

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** PRD-CHAT — nhắn tin realtime, chỉ mở giữa hai người đã match.
- **BRD goal | Mục tiêu BRD:** BRD-G1 — đạt 100k MAU trong năm đầu; nhắn tin duy trì giữ chân người
  dùng hoạt động.

## Success Criteria | Tiêu chí thành công

Hai người đã match có thể trao đổi tin nhắn realtime với trạng thái gửi/nhận rõ ràng, và người chưa
match không thể nhắn tin cho nhau; mức độ giữ chân đo qua `mau-monthly`.

## Scope | Phạm vi

Trong phạm vi: mở cuộc trò chuyện 1-1 theo match, gửi/nhận tin nhắn văn bản realtime, cổng chặn theo
match phía máy chủ. Ngoài phạm vi: gửi ảnh / voice / video call, gợi ý ghép đôi (PRD-AIREC), gói trả
phí (PRD-PREMIUM).
