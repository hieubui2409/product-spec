---
id: PRD-FUND-E2-S1
type: story
epic: PRD-FUND-E2
status: draft
lang: vi
owner: TBD
version: 0.1.0
created: 2026-06-06
updated: 2026-06-06
personas: ["fund-keeper"]
scope: core-value
moscow: must
size: S
horizon: now
metrics: ["fund-tx-per-active-group"]
acceptance_criteria: ["Cho fund-keeper, khi ghi khoản nộp với người nộp, số tiền và ngày, thì giao dịch nộp xuất hiện trong lịch sử và số dư tăng đúng bằng số tiền nộp.", "Cho một khoản nộp có số tiền không hợp lệ (≤ 0 hoặc để trống), khi lưu, thì hệ thống từ chối và báo lỗi rõ ràng."]
---

# Ghi khoản nộp quỹ — Story PRD-FUND-E2-S1

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** fund-keeper
**I want** | **Tôi muốn** ghi một khoản nộp vào quỹ (ai nộp, số tiền, ngày)
**so that** | **để** khoản góp được ghi nhận và số dư phản ánh đúng.

## Acceptance Criteria | Tiêu chí chấp nhận

- Cho fund-keeper, khi ghi khoản nộp với người nộp, số tiền và ngày, thì giao dịch nộp xuất hiện trong lịch sử và số dư tăng đúng bằng số tiền nộp.
- Cho một khoản nộp có số tiền không hợp lệ (≤ 0 hoặc để trống), khi lưu, thì hệ thống từ chối và báo lỗi rõ ràng.




