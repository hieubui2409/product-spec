---
id: PRD-SAFETY
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
horizon: next
metrics: [mau-monthly, weekly-match-rate]
risks:
  - description: "Bước xác minh thêm rào cản, làm rớt người dùng trong onboarding"
    impact: med
    likelihood: med
    mitigation: "Cho phép khám phá trước, chỉ bắt buộc xác minh trước khi nhắn tin/match sâu; huy hiệu đã xác minh tạo động lực tự nguyện"
    status: open
  - description: "Kẻ lừa đảo dùng ảnh/giấy tờ giả vượt qua xác minh tự động"
    impact: high
    likelihood: med
    mitigation: "Đối chiếu selfie sống (liveness) với ảnh giấy tờ; chuyển các trường hợp nghi ngờ sang kiểm duyệt thủ công"
    status: open
competitive_parity:
  COMP-TINDER: parity
  COMP-BUMBLE: parity
  COMP-HEN: ahead
---

# Xác minh danh tính & Chống lừa đảo — PRD PRD-SAFETY

## Overview & Problem | Tổng quan và Vấn đề

PRD-SAFETY xây dựng lớp niềm tin của Ghép Đôi Việt: xác minh người thật qua selfie sống đối chiếu
với giấy tờ tuỳ thân, và phát hiện/chặn hành vi catfish và lừa đảo. Vấn đề cần giải: kết nối thật chỉ
được duy trì khi người dùng tin rằng người ở đầu kia là thật. Theo ràng buộc BRD, niềm tin và an
toàn là điều kiện tiên quyết trước khi đẩy mạnh tăng trưởng — hồ sơ đã xác minh nâng chất lượng match
và giữ chân người dùng hoạt động, phục vụ trực tiếp north-star kết nối thật.

## Personas | Nhóm người dùng

Phục vụ cả ba nhóm: P-URBAN (muốn mối quan hệ nghiêm túc, kỳ vọng đối phương là thật), P-PROVINCE
(pool nhỏ nên mỗi tương tác cần đáng tin), P-RETURNEE (kết nối ở khoảng cách xa, dễ thành mục tiêu lừa đảo).

## Use Cases / Flows | Tình huống sử dụng / Luồng

1. Người dùng nộp một selfie sống và ảnh giấy tờ tuỳ thân để xác minh danh tính.
2. Hệ thống đối chiếu khuôn mặt selfie với ảnh giấy tờ, gắn huy hiệu "đã xác minh" khi khớp.
3. Người dùng báo cáo một hồ sơ nghi lừa đảo/catfish; hệ thống tiếp nhận và chuyển sang kiểm duyệt.

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

- Xác minh danh tính qua selfie sống đối chiếu với ảnh giấy tờ tuỳ thân, gắn huy hiệu "đã xác minh".
- Cho phép người dùng báo cáo hồ sơ nghi lừa đảo/catfish và đưa vào hàng đợi kiểm duyệt.

### Should | Nên có

- Hiển thị huy hiệu "đã xác minh" trên hồ sơ ở màn hình khám phá để người dùng ưu tiên kết nối thật.

### Could | Có thể có

- Xác minh lại định kỳ với hồ sơ lâu không hoạt động.

### Won't (this round) | Không (lần này)

- Xác thực qua giấy tờ chính phủ tích hợp API bên thứ ba (cân nhắc cycle sau).

## Non-Functional Requirements | Yêu cầu phi chức năng

Ảnh selfie và giấy tờ được xử lý an toàn, không lộ cho người dùng khác; luồng xác minh hoạt động trên
thiết bị di động phổ thông tại Việt Nam.

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

- `mau-monthly` → BRD-G1 (niềm tin tăng giữ chân người dùng hoạt động hàng tháng).
- `weekly-match-rate` → BRD-G2 (hồ sơ đã xác minh nâng chất lượng và tỉ lệ match thật mỗi tuần).
