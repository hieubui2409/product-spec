---
id: BRD
type: brd
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
goals:
  - id: BRD-G1
    title: "Đạt 100k MAU trong năm đầu"
    metrics: [mau-monthly]
    status: draft
    owner: Trần Bảo Hiếu
  - id: BRD-G2
    title: "20% người dùng hoạt động tạo >=1 match mỗi tuần"
    metrics: [weekly-match-rate]
    status: draft
    owner: Trần Bảo Hiếu
  - id: BRD-G3
    title: "Doanh thu premium đủ hoà vốn vận hành vào năm 2"
    metrics: [premium-conversion-rate, arpu]
    status: draft
    owner: Trần Bảo Hiếu
competitors:
  - id: COMP-TINDER
    name: "Tinder"
    url: "https://tinder.com"
    threat: high
  - id: COMP-BUMBLE
    name: "Bumble"
    url: "https://bumble.com"
    threat: med
  - id: COMP-HEN
    name: "Hẹn"
    url: "https://hen.vn"
    threat: med
  - id: COMP-FIKA
    name: "Fika"
    url: "https://fika.app"
    threat: low
---

# Business Requirements Document | Tài liệu Yêu cầu Kinh doanh

## Problem / Opportunity | Vấn đề / Cơ hội

Thị trường hẹn hò Việt Nam đang bị thống trị bởi các ứng dụng phương Tây tối ưu cho lượt quẹt và
match ảo, để lại khoảng trống cho một sản phẩm bản địa đo bằng kết nối thật. Cơ hội: phục vụ ba nhóm
người Việt độc thân chưa được phục vụ tốt — người trẻ thành thị bận rộn, người ở tỉnh lẻ với nhóm
địa phương nhỏ, và người Việt xa quê — bằng một nền tảng toàn quốc đặt chất lượng kết nối lên hàng đầu.

## Business Goals | Mục tiêu kinh doanh

- **BRD-G1** — Đạt 100k MAU trong năm đầu. (chỉ số: `mau-monthly`)
- **BRD-G2** — 20% người dùng hoạt động tạo từ 1 match trở lên mỗi tuần. (chỉ số: `weekly-match-rate`)
- **BRD-G3** — Doanh thu premium đủ hoà vốn vận hành vào năm 2. (chỉ số: `premium-conversion-rate`, `arpu`)

## Success Metrics | Chỉ số thành công

- `mau-monthly` — Số người dùng hoạt động hàng tháng.
- `weekly-match-rate` — Tỉ lệ người dùng hoạt động tạo từ 1 match trở lên mỗi tuần.
- `premium-conversion-rate` — Tỉ lệ người dùng chuyển sang gói trả phí.
- `arpu` — Doanh thu trung bình trên mỗi người dùng.

## Stakeholders | Bên liên quan

Chủ sản phẩm, đội phát triển, đội vận hành cộng đồng & kiểm duyệt an toàn, đội tăng trưởng.

## Constraints | Ràng buộc

Sản phẩm phục vụ người Việt toàn quốc, ưu tiên tiếng Việt. Niềm tin và an toàn người dùng là điều
kiện tiên quyết trước khi đẩy mạnh tăng trưởng. Hoà vốn vận hành cần đạt trong năm 2.

## Market Context | Bối cảnh thị trường

Cạnh tranh trực tiếp với các nền tảng toàn cầu (Tinder, Bumble) và một số ứng dụng nội địa (Hẹn,
Fika). Khác biệt của Ghép Đôi Việt là đo bằng kết nối thật được duy trì, không phải số match.
