---
id: PRD-PREMIUM
type: prd
brd_goals: [BRD-G3]
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: in
moscow: should
horizon: later
metrics: [premium-conversion-rate, arpu]
risks:
  - description: "Tính năng trả phí có thể làm xói mòn trải nghiệm miễn phí (ví dụ giới hạn lượt thích quá chặt khiến người dùng mới rời app trước khi cảm nhận giá trị)"
    impact: med
    likelihood: med
    mitigation: "Giữ hạn mức miễn phí đủ rộng để trải nghiệm lõi (khám phá + match) còn dùng được; chỉ tính phí các tăng tốc, không khoá kết nối thật"
    status: open
  - description: "Doanh thu premium phụ thuộc vào lõi kết nối đã chứng minh giá trị; bán gói trả phí trước khi PRD-CHAT chứng minh north-star có thể chuyển đổi thấp"
    impact: med
    likelihood: high
    mitigation: "Đặt horizon:later; chỉ đẩy mạnh sau khi nhắn tin duy trì >=7 ngày đã có dữ liệu giữ chân"
    status: open
competitive_parity:
  COMP-TINDER: behind
  COMP-BUMBLE: parity
  COMP-HEN: parity
---

# Gói trả phí Premium — PRD PRD-PREMIUM

## Overview & Problem | Tổng quan và Vấn đề

PRD-PREMIUM là lớp doanh thu của Ghép Đôi Việt: gói trả phí cho phép người dùng **xem ai đã thích mình**,
**boost hồ sơ** để được hiển thị nhiều hơn trong một khoảng thời gian, và **thích không giới hạn**. Vấn đề
cần giải: sản phẩm cần một nguồn doanh thu bền vững để hoà vốn vận hành (BRD-G3), trong khi vẫn giữ trải
nghiệm miễn phí đủ tốt để không cản trở north-star kết nối thật.

**Định vị cạnh tranh (thẳng):** đây là tập tính năng premium **me-too** — Tinder và Bumble đều đã có từ lâu.
Ghép Đôi Việt **đi sau** Tinder (COMP-TINDER: behind — Tinder có hệ sinh thái premium sâu hơn nhiều: Boost,
Super Boost, Top Picks, Passport), **ngang bằng** Bumble (COMP-BUMBLE: parity — bộ tính năng cốt lõi tương
đương) và Hẹn (COMP-HEN: parity). Premium ở đây không phải lợi thế cạnh tranh; mục tiêu là đạt ngang bằng tối
thiểu để mở dòng tiền, không phải vượt mặt.

## Personas | Nhóm người dùng

Phục vụ cả ba nhóm, nhưng giá trị chi trả khác nhau: P-URBAN (thu nhập cao hơn, sẵn lòng trả để tăng tốc tìm
mối quan hệ nghiêm túc — nhóm chuyển đổi chính), P-PROVINCE (pool mỏng nên "xem ai đã thích mình" giúp không
bỏ lỡ kết nối hiếm), P-RETURNEE (boost giúp được nhìn thấy trong cửa sổ thời gian ngắn khi về Việt Nam).

## Use Cases / Flows | Tình huống sử dụng / Luồng

1. Người dùng mở danh sách "ai đã thích mình" và xem hồ sơ những người đã thích trước khi quyết định.
2. Người dùng kích hoạt boost hồ sơ và được ưu tiên hiển thị trong 30 phút.
3. Người dùng đã hết hạn mức thích miễn phí nâng cấp gói để thích không giới hạn.

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

- (không có — premium là `should` đợt này, không chặn lõi.)

### Should | Nên có

- Cho người dùng trả phí xem danh sách những người đã thích hồ sơ của mình.
- Cho người dùng trả phí kích hoạt boost hồ sơ trong một khoảng thời gian giới hạn.

### Could | Có thể có

- Thích không giới hạn cho người dùng trả phí (gỡ hạn mức thích miễn phí hàng ngày).
- Gói dùng thử premium ngắn hạn cho người dùng mới.

### Won't (this round) | Không (lần này)

- Tích hợp cổng thanh toán cụ thể (do đội build chọn ở giai đoạn triển khai).
- Gói cao cấp nhiều tầng (Passport/Top Picks kiểu Tinder) — cân nhắc cycle sau.

## Non-Functional Requirements | Yêu cầu phi chức năng

Trạng thái gói trả phí và quyền lợi đồng bộ tức thời sau khi nâng cấp; danh sách "ai đã thích mình" tải được
trên thiết bị di động phổ thông tại Việt Nam. Hạn mức miễn phí phải đủ rộng để trải nghiệm lõi còn dùng được
mà không trả phí.

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

- `premium-conversion-rate` → BRD-G3 (tỉ lệ người dùng chuyển sang gói trả phí — đo trực tiếp khả năng hoà vốn).
- `arpu` → BRD-G3 (doanh thu trung bình trên mỗi người dùng — đo độ bền của dòng tiền premium).
