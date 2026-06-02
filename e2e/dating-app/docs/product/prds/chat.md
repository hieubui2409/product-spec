---
id: PRD-CHAT
type: prd
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
  - description: "Tin nhắn không gửi được hoặc trễ làm cuộc trò chuyện đứt quãng, giảm số cặp duy trì 7 ngày"
    impact: high
    likelihood: med
    mitigation: "Cơ chế gửi lại tự động + báo trạng thái gửi/nhận rõ ràng; hàng đợi offline"
    status: open
competitive_parity:
  COMP-TINDER: parity
  COMP-BUMBLE: parity
depends_on: [PRD-MATCH]
---

# Nhắn tin — PRD PRD-CHAT

## Overview & Problem | Tổng quan và Vấn đề

PRD-CHAT là nơi north-star của Ghép Đôi Việt thực sự diễn ra: hai người đã match nhắn tin qua lại để
kết nối trở nên thật. Vấn đề cần giải: sau khi có match, người dùng cần một kênh nhắn tin realtime,
tin cậy, chỉ mở giữa hai người đã match — để mỗi match có cơ hội trở thành một cuộc trò chuyện được
duy trì từ 7 ngày trở lên. Match mà không nhắn tin được thì chỉ là match ảo — đúng thứ sản phẩm muốn
tránh.

## Personas | Nhóm người dùng

Phục vụ cả ba nhóm: P-URBAN (nhắn nhanh giữa lịch bận), P-PROVINCE (giữ liên lạc với người ở xa sau
khi mở rộng pool toàn quốc), P-RETURNEE (trò chuyện với người cùng văn hoá dù lệch múi giờ).

## Use Cases / Flows | Tình huống sử dụng / Luồng

1. Sau khi có match, hai người mở cuộc trò chuyện từ màn hình match.
2. Gửi và nhận tin nhắn văn bản theo thời gian thực, thấy trạng thái đã gửi / đã nhận.
3. Hai người chưa match với nhau KHÔNG thể nhắn tin — cổng chặn dựa trên trạng thái match.

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

- Mở cuộc trò chuyện 1-1 chỉ giữa hai người đã match.
- Gửi / nhận tin nhắn văn bản realtime với trạng thái gửi / nhận.

### Should | Nên có

- Hàng đợi gửi lại khi mất mạng tạm thời, không mất tin nhắn.

### Could | Có thể có

- Báo "đang nhập…" (typing indicator).

### Won't (this round) | Không (lần này)

- Gửi ảnh / voice / video call (cycle sau).

## Non-Functional Requirements | Yêu cầu phi chức năng

Độ trễ gửi tin nhắn thấp trên mạng di động phổ thông tại Việt Nam; cuộc trò chuyện đồng bộ trên các
phiên đăng nhập của cùng một người dùng.

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

- `mau-monthly` → BRD-G1 (nhắn tin duy trì giữ chân người dùng hoạt động hàng tháng — trực tiếp nuôi
  north-star về số cặp nhắn tin qua lại từ 7 ngày trở lên).
