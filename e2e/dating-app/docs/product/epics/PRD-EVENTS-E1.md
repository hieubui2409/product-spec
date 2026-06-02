---
id: PRD-EVENTS-E1
type: epic
prd: PRD-EVENTS
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
  - description: "Vận hành sự kiện thực địa (địa điểm, an toàn người tham dự) vượt phạm vi một app hẹn hò ở giai đoạn này"
    impact: high
    likelihood: high
    mitigation: "Giới hạn ở danh sách + đăng ký giữ chỗ; mọi khâu tổ chức thực địa do đội vận hành xử lý thủ công khi thử nghiệm"
    status: open
---

# Mạng lưới sự kiện gặp mặt offline — Epic PRD-EVENTS-E1

## Goal | Mục tiêu

Cho phép người dùng khám phá các sự kiện gặp mặt offline theo khu vực và giữ chỗ tham dự — bước đầu
tiên (chỉ ở mức `could`, `later`) để thử ý tưởng cộng đồng offline mà KHÔNG kéo nguồn lực khỏi lõi
kết nối theo north-star.

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** PRD-EVENTS — mạng lưới sự kiện gặp mặt offline toàn quốc.
- **BRD goal | Mục tiêu BRD:** BRD-G1 — sự kiện có thể kéo người dùng quay lại app (chỉ số gián tiếp
  `mau-monthly`, không đo kết nối thật theo north-star).

## Success Criteria | Tiêu chí thành công

Người dùng có thể xem danh sách sự kiện gần mình và giữ một chỗ thành công, nhận xác nhận đăng ký.
Đây là tiêu chí cho lát thử nghiệm — không phải cam kết sản phẩm đợt này.

## Scope | Phạm vi

Trong phạm vi (mức `could`): hiển thị danh sách sự kiện theo khu vực, đăng ký giữ chỗ. Ngoài phạm vi:
thanh toán vé, check-in QR, sự kiện do người dùng tự tổ chức, và toàn bộ khâu vận hành thực địa.
