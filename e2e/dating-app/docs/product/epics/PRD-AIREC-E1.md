---
id: PRD-AIREC-E1
type: epic
prd: PRD-AIREC
brd_goals: [BRD-G2]
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: in
moscow: could
horizon: later
metrics: [weekly-match-rate]
risks:
  - description: "Chưa đủ dữ liệu tương tác thật để mô hình gợi ý vượt thứ tự theo-khoảng-cách hiện có; rủi ro tốn công mà không cải thiện rõ rệt"
    impact: med
    likelihood: high
    mitigation: "Chỉ khởi động sau khi lõi ghép đôi và nhắn tin tích đủ tín hiệu; đặt mốc đo cải thiện so với thứ tự mặc định trước khi mở rộng"
    status: open
---

# Gợi ý ghép đôi bằng AI — Epic PRD-AIREC-E1

## Goal | Mục tiêu

Xếp hạng hồ sơ trên màn khám phá theo điểm gợi ý do mô hình tính (thay cho thứ tự chỉ-theo-khoảng-cách)
và thu thập tín hiệu tương tác để mô hình học, nhằm tăng tỉ lệ tạo match mỗi tuần mà không kéo lệch khỏi
north-star kết nối duy trì.

## Business Context | Bối cảnh kinh doanh

- **PRD requirement | Yêu cầu PRD:** PRD-AIREC — gợi ý ghép đôi bằng AI (xếp hạng khám phá theo điểm gợi ý + thu thập tín hiệu huấn luyện). Tính năng me-too, đặt `could`/`later`.
- **BRD goal | Mục tiêu BRD:** BRD-G2 — 20% người dùng hoạt động tạo >=1 match mỗi tuần (`weekly-match-rate`).

## Success Criteria | Tiêu chí thành công

Màn khám phá có thể xếp hồ sơ theo điểm gợi ý của mô hình khi có đủ dữ liệu, và quay về thứ tự mặc định
hợp lý khi thiếu dữ liệu — đo qua tỉ lệ tạo match mỗi tuần so với thứ tự chỉ-theo-khoảng-cách.

## Scope | Phạm vi

Trong phạm vi: xếp hạng khám phá theo điểm gợi ý, thu thập tín hiệu tương tác làm dữ liệu huấn luyện, thứ
tự mặc định cho người mới. Ngoài phạm vi: hạ tầng/mô hình ML cụ thể (đội build chọn), giải thích lý do gợi
ý, và gợi ý dựa trên dữ liệu ngoài app (lý do an toàn & riêng tư).
