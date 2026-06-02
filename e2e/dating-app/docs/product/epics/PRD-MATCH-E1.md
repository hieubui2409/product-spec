---
id: PRD-MATCH-E1
type: epic
prd: PRD-MATCH
brd_goals: [BRD-G2]
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
metrics: [weekly-match-rate]
risks:
  - description: "Chất lượng gợi ý thấp khi chưa đủ tín hiệu hành vi người dùng"
    impact: med
    likelihood: med
    mitigation: "Bắt đầu bằng gợi ý theo vị trí + sở thích cơ bản, tinh chỉnh dần"
    status: open
---

# Khám phá & Quẹt ghép đôi — Epic PRD-MATCH-E1

## Goal | Mục tiêu

Cho phép người dùng khám phá hồ sơ được gợi ý, quẹt thích/bỏ qua, và tạo match khi hai phía cùng
thích — nền tảng để mỗi match có cơ hội trở thành một kết nối thật.

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** PRD-MATCH — lõi khám phá + quẹt + ghép đôi.
- **BRD goal | Mục tiêu BRD:** BRD-G2 — 20% người dùng hoạt động tạo từ 1 match trở lên mỗi tuần.

## Success Criteria | Tiêu chí thành công

Người dùng có thể xem hồ sơ gợi ý, quẹt, và nhận match khi cả hai phía cùng thích, với tỉ lệ tạo
match mỗi tuần đo được qua `weekly-match-rate`.

## Scope | Phạm vi

Trong phạm vi: hiển thị chồng hồ sơ, quẹt thích/bỏ qua, tạo match hai chiều. Ngoài phạm vi: nhắn
tin (PRD-CHAT), xác minh danh tính (PRD-SAFETY), gợi ý AI (PRD-AIREC).
