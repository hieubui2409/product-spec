---
id: PRD-EVENTS
type: prd
brd_goals: [BRD-G1]
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: out
moscow: could
horizon: later
metrics: [mau-monthly]
risks:
  - description: "Sự kiện offline đòi hỏi vận hành thực địa (địa điểm, kiểm duyệt người tham dự, an toàn) vượt xa năng lực một app hẹn hò"
    impact: high
    likelihood: high
    mitigation: "Thử nghiệm quy mô nhỏ tại 1-2 thành phố trước khi mở toàn quốc"
    status: open
  - description: "Lệch north-star: north-star đo bằng nhắn tin duy trì >=7 ngày, không phải lượt tham dự sự kiện"
    impact: high
    likelihood: high
    mitigation: "Giữ moscow:could, horizon:later; chỉ đầu tư khi lõi nhắn tin đã chứng minh giá trị"
    status: open
competitive_parity: {}
---

# Sự kiện gặp mặt offline toàn quốc — PRD PRD-EVENTS

## Overview & Problem | Tổng quan và Vấn đề

PRD-EVENTS là tầm nhìn về một mạng lưới sự kiện gặp mặt offline toàn quốc — tiệc tối, workshop, chuyến
đi nhóm — để người dùng Ghép Đôi Việt gặp nhau ngoài đời thật tại mọi tỉnh thành. Ý tưởng định vị đây
như "tính năng flagship" biến app thành một cộng đồng kết nối thật ngoài màn hình.

**Lưu ý thẳng (gold-plating / solution-first):** north-star của sản phẩm đo bằng **số cặp đôi duy trì
nhắn tin qua lại >= 7 ngày**, KHÔNG phải số người tham dự sự kiện. Sự kiện offline là một giải pháp
được đề xuất trước khi vấn đề "match rồi nhưng không trò chuyện" được giải quyết qua PRD-CHAT. Vì vậy
PRD này được đặt `scope: out`, `moscow: could`, `horizon: later` — ghi nhận tầm nhìn nhưng không phải
trọng tâm đợt này.

**Mức gold-plating tăng thêm (concert toàn quốc):** PRD-EVENTS-E1-S3 đề xuất tổ chức và bán vé concert
âm nhạc toàn quốc bên trong app — đây là một mảng kinh doanh sự kiện giải trí riêng (vận hành nghệ sĩ,
bán vé, an ninh đám đông), càng xa north-star hơn nữa. Ghi nhận như tầm nhìn `could`/`later`; mọi quyết
định triển khai cần PO cân nhắc rõ ràng so với north-star trước.

## Personas | Nhóm người dùng

Phục vụ cả ba nhóm về mặt lý thuyết: P-URBAN (dễ tham dự ở HN/HCM), P-PROVINCE (khó tổ chức vì pool
mỏng ở tỉnh lẻ — đây là rủi ro vận hành lớn), P-RETURNEE (chỉ tham dự được khi về Việt Nam).

## Use Cases / Flows | Tình huống sử dụng / Luồng

1. Đội vận hành tạo một sự kiện (địa điểm, thời gian, số chỗ).
2. Người dùng duyệt danh sách sự kiện gần mình và đăng ký một chỗ.
3. Người dùng nhận xác nhận đăng ký và nhắc lịch trước sự kiện.

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

- (không có — toàn bộ PRD này là `could`, không có yêu cầu bắt buộc đợt này.)

### Should | Nên có

- (không có đợt này.)

### Could | Có thể có

- Hiển thị danh sách sự kiện sắp diễn ra theo khu vực.
- Đăng ký giữ chỗ cho một sự kiện.
- Khám phá và đặt vé concert âm nhạc toàn quốc do app tổ chức (gold-plating — xem lưu ý lệch trọng tâm bên dưới).

### Won't (this round) | Không (lần này)

- Thanh toán vé sự kiện (nếu có phí).
- Check-in tại địa điểm bằng QR.
- Tổ chức sự kiện do người dùng tự khởi xướng.

## Non-Functional Requirements | Yêu cầu phi chức năng

Nếu được triển khai, danh sách sự kiện phải tải được trên thiết bị di động phổ thông; quy trình đăng ký
không yêu cầu rời app. Nhưng ưu tiên thực tế: chỉ đầu tư sau khi lõi nhắn tin (PRD-CHAT) đã chứng minh
giá trị theo north-star.

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

- `mau-monthly` → BRD-G1 (sự kiện có thể kéo người dùng quay lại app hàng tháng — nhưng đây là chỉ số
  gián tiếp, KHÔNG đo kết nối thật theo north-star; đây chính là dấu hiệu lệch trọng tâm cần cân nhắc).
