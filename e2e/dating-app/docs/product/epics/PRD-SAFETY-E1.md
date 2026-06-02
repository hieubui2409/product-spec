---
id: PRD-SAFETY-E1
type: epic
prd: PRD-SAFETY
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
  - description: "Người dùng e ngại nộp ảnh giấy tờ vì lo ngại quyền riêng tư"
    impact: med
    likelihood: med
    mitigation: "Nêu rõ ảnh giấy tờ chỉ dùng để xác minh, không hiển thị công khai; xoá sau khi đối chiếu"
    status: open
---

# Xác minh danh tính & Chống lừa đảo — Epic PRD-SAFETY-E1

## Goal | Mục tiêu

Cho phép người dùng chứng minh mình là người thật qua xác minh selfie–giấy tờ, và cho cộng đồng công
cụ báo cáo hồ sơ lừa đảo/catfish — nền tảng niềm tin để mỗi match có cơ hội trở thành kết nối thật.

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** PRD-SAFETY — xác minh danh tính + chống lừa đảo/catfish.
- **BRD goal | Mục tiêu BRD:** BRD-G1 — niềm tin tăng giữ chân người dùng hoạt động, hướng tới 100k MAU.

## Success Criteria | Tiêu chí thành công

Người dùng có thể hoàn tất xác minh selfie–giấy tờ và nhận huy hiệu "đã xác minh", và có thể báo cáo
hồ sơ nghi lừa đảo để chuyển sang kiểm duyệt — đo qua tỉ lệ hồ sơ đã xác minh và giữ chân hàng tháng.

## Scope | Phạm vi

Trong phạm vi: xác minh selfie sống đối chiếu giấy tờ, gắn huy hiệu đã xác minh, báo cáo hồ sơ nghi
lừa đảo. Ngoài phạm vi: khám phá & quẹt (PRD-MATCH), nhắn tin (PRD-CHAT), gói trả phí (PRD-PREMIUM).
