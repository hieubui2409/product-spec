---
id: PRD-MATCH
type: prd
brd_goals: [BRD-G1, BRD-G2]
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: core-value
moscow: must
horizon: now
metrics: [weekly-match-rate, mau-monthly]
risks:
  - description: "Pool người dùng ban đầu mỏng ở tỉnh lẻ làm giảm chất lượng gợi ý"
    impact: high
    likelihood: med
    mitigation: "Mở rộng bán kính gợi ý ra toàn quốc khi pool địa phương cạn"
    status: open
competitive_parity:
  COMP-TINDER: parity
  COMP-BUMBLE: behind
---

# Khám phá & Ghép đôi — PRD PRD-MATCH

## Overview & Problem | Tổng quan và Vấn đề

PRD-MATCH là lõi của Ghép Đôi Việt: khám phá hồ sơ, quẹt thích/bỏ qua, và tạo match khi hai phía
cùng thích. Đây là bước đầu tiên trên hành trình kết nối thật. Vấn đề cần giải: đưa đúng người tới
trước mặt người dùng trên phạm vi toàn quốc, để mỗi lượt thích có cơ hội cao trở thành một cuộc trò
chuyện thật được duy trì — đúng theo north-star.

## Personas | Nhóm người dùng

Phục vụ cả ba nhóm: P-URBAN (cần gợi ý đúng để tiết kiệm thời gian), P-PROVINCE (cần mở rộng ra toàn
quốc khi pool địa phương nhỏ), P-RETURNEE (cần tìm người cùng văn hoá dù ở xa).

## Use Cases / Flows | Tình huống sử dụng / Luồng

1. Người dùng mở app, xem một chồng hồ sơ được gợi ý.
2. Quẹt phải để thích, quẹt trái để bỏ qua.
3. Khi cả hai phía cùng thích, hệ thống tạo match và thông báo cho cả hai.

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

- Hiển thị chồng hồ sơ gợi ý cho người dùng.
- Quẹt thích / bỏ qua và tạo match khi hai phía cùng thích.

### Should | Nên có

- Bộ lọc cơ bản (độ tuổi, khoảng cách / phạm vi toàn quốc).

### Could | Có thể có

- Hoàn tác lượt quẹt gần nhất.

### Won't (this round) | Không (lần này)

- Gợi ý bằng AI (thuộc PRD-AIREC, cycle sau).

## Non-Functional Requirements | Yêu cầu phi chức năng

Trải nghiệm quẹt phải mượt trên thiết bị di động phổ thông tại Việt Nam; phục vụ người dùng toàn quốc.

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

- `weekly-match-rate` → BRD-G2 (tỉ lệ tạo match mỗi tuần).
- `mau-monthly` → BRD-G1 (giữ chân người dùng hoạt động hàng tháng).
