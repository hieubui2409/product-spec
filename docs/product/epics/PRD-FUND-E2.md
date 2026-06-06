---
id: PRD-FUND-E2
type: epic
prd: PRD-FUND
brd_goals: ["BRD-G3"]
status: draft
lang: vi
owner: TBD
version: 0.1.0
created: 2026-06-06
updated: 2026-06-06
personas: ["fund-keeper"]
scope: core-value
moscow: must
horizon: now
metrics: ["fund-tx-per-active-group"]
risks: []
# TIME (optional) — uncomment to set; absence parses cleanly as none/empty:
# target_date: 2026-09-30
# depends_on: [PRD-AUTH-E2]
---

# Ghi giao dịch quỹ — Epic PRD-FUND-E2

## Goal | Mục tiêu

Cho fund-keeper ghi các khoản nộp và chi, để quỹ luôn phản ánh đúng dòng tiền chung của nhóm — đây là nơi sinh ra giao dịch quỹ (north-star).

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** M2 (ghi nộp), M3 (ghi chi) — MUST; kèm S1/S2 (SHOULD) và C1/C2 (COULD) ở các đợt sau.
- **BRD goal | Mục tiêu BRD:** BRD-G3 (Usage) — gắn trực tiếp `fund-tx-per-active-group`.

## Success Criteria | Tiêu chí thành công

Ghi được khoản nộp và khoản chi; mỗi giao dịch cập nhật số dư đúng và xuất hiện trong lịch sử. Số tiền không hợp lệ bị từ chối.

## Scope | Phạm vi

**Trong:** ghi nộp, ghi chi (MUST đợt này); sửa/xóa + ghi chú (SHOULD), ảnh hóa đơn + phân loại (COULD) ở đợt sau. **Ngoài:** thanh toán/giữ tiền thật.




## Stories Overview | Tổng quan Stories

- **PRD-FUND-E2-S1** — Ghi khoản nộp quỹ (must)
- **PRD-FUND-E2-S2** — Ghi khoản chi từ quỹ (must)
- *(đợt sau)* Sửa/xóa giao dịch · Ghi chú — SHOULD; Ảnh hóa đơn · Phân loại — COULD

