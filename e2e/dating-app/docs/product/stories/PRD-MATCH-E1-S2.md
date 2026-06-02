---
id: PRD-MATCH-E1-S2
type: story
epic: PRD-MATCH-E1
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.2.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: core-value
moscow: must
size: L
horizon: now
metrics: [weekly-match-rate]
acceptance_criteria:
  - "Khi người dùng mở màn hình khám phá, danh sách gợi ý đầu tiên hiển thị trong vòng 1 giây (đo ở p95)."
  - "Mỗi hồ sơ gợi ý phải khớp tối thiểu 3/4 tiêu chí cứng người dùng đã đặt (khoảng tuổi, khoảng cách tối đa, giới tính mong muốn, mục đích nghiêm túc); hồ sơ vi phạm bất kỳ tiêu chí cứng nào không được hiển thị."
  - "Trong một phiên 20 hồ sơ gợi ý, tối thiểu 30% là người dùng đang hoạt động trong 14 ngày gần nhất (loại hồ sơ ngủ đông để tăng khả năng match thật)."
  - "Tỉ lệ quẹt-phải-thành-match trên các hồ sơ do hệ thống gợi ý phải cao hơn tối thiểu 20% so với nhóm đối chứng gợi ý ngẫu nhiên, đo qua A/B test với p < 0.05."
  - "Người dùng có thể chạm 'Vì sao gợi ý người này?' và thấy ít nhất 2 tiêu chí khớp cụ thể (ví dụ: cùng thành phố, cùng độ tuổi mong muốn)."
---

# Gợi ý ghép đôi chất lượng — Story PRD-MATCH-E1-S2

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** người dùng độc thân (P-URBAN / P-PROVINCE / P-RETURNEE)
**I want** | **Tôi muốn** được hệ thống gợi ý những người phù hợp
**so that** | **để** tôi dễ tạo match với người thật sự hợp với mình.

## Acceptance Criteria | Tiêu chí chấp nhận

- Khi người dùng mở màn hình khám phá, danh sách gợi ý đầu tiên hiển thị trong vòng 1 giây (đo ở p95).
- Mỗi hồ sơ gợi ý phải khớp tối thiểu 3/4 tiêu chí cứng người dùng đã đặt (khoảng tuổi, khoảng cách tối đa, giới tính mong muốn, mục đích nghiêm túc); hồ sơ vi phạm bất kỳ tiêu chí cứng nào không được hiển thị.
- Trong một phiên 20 hồ sơ gợi ý, tối thiểu 30% là người dùng đang hoạt động trong 14 ngày gần nhất (loại hồ sơ ngủ đông để tăng khả năng match thật).
- Tỉ lệ quẹt-phải-thành-match trên các hồ sơ do hệ thống gợi ý phải cao hơn tối thiểu 20% so với nhóm đối chứng gợi ý ngẫu nhiên, đo qua A/B test với p < 0.05.
- Người dùng có thể chạm "Vì sao gợi ý người này?" và thấy ít nhất 2 tiêu chí khớp cụ thể (ví dụ: cùng thành phố, cùng độ tuổi mong muốn).
