---
id: PRD-AIREC
type: prd
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
  - description: "Gợi ý bằng AI là tính năng me-too: Tinder và Bumble đã có thuật toán gợi ý trưởng thành; làm sau mà không có dữ liệu tương tác đủ lớn thì chất lượng gợi ý kém, dễ thua trải nghiệm đối thủ"
    impact: med
    likelihood: high
    mitigation: "Đặt moscow:could và horizon:later; chỉ đầu tư sau khi lõi ghép đôi (PRD-MATCH) và nhắn tin (PRD-CHAT) tích đủ dữ liệu tương tác thật để mô hình có cái mà học"
    status: open
  - description: "AI gợi ý tối ưu cho số match có thể kéo lệch khỏi north-star (kết nối duy trì >=7 ngày) nếu huấn luyện theo lượt quẹt thay vì độ bền hội thoại"
    impact: med
    likelihood: med
    mitigation: "Nếu làm, đặt mục tiêu mô hình theo tỉ lệ match chuyển thành nhắn tin duy trì, không theo số match thô"
    status: open
competitive_parity:
  COMP-TINDER: behind
  COMP-BUMBLE: behind
---

# Gợi ý ghép đôi bằng AI — PRD PRD-AIREC

## Overview & Problem | Tổng quan và Vấn đề

PRD-AIREC đề xuất một lớp **gợi ý ghép đôi bằng AI**: thay vì chỉ xếp hồ sơ theo khoảng cách và độ
hoạt động, hệ thống học từ lịch sử quẹt và tương tác để ưu tiên những hồ sơ có khả năng dẫn tới kết
nối phù hợp hơn. Vấn đề cần giải: với P-PROVINCE pool địa phương mỏng và P-URBAN bận rộn không có
thời gian lướt nhiều, một thứ tự gợi ý thông minh hơn có thể tăng tỉ lệ tạo match mỗi tuần (BRD-G2).

**Định vị cạnh tranh (thẳng):** đây là tính năng **me-too**, không phải khác biệt. Tinder và Bumble
đã chạy gợi ý bằng thuật toán/AI nhiều năm trên tập dữ liệu khổng lồ, nên Ghép Đôi Việt **đi sau cả
hai** (COMP-TINDER: behind, COMP-BUMBLE: behind). Làm tính năng này sớm, khi sản phẩm chưa tích đủ
dữ liệu tương tác thật, gần như chắc chắn cho ra gợi ý kém hơn đối thủ — lý do nó được đặt `could` và
`horizon:later`, không phải ưu tiên đợt này. Đây không phải lợi thế cạnh tranh; tốt nhất là một cải
tiến chất lượng sau khi lõi đã chứng minh giá trị.

## Personas | Nhóm người dùng

Phục vụ cả ba nhóm nhưng giá trị khác nhau: P-PROVINCE (pool mỏng nên thứ tự gợi ý tốt giúp không bỏ
lỡ hồ sơ phù hợp hiếm hoi), P-URBAN (bận rộn, muốn ít lướt mà gặp đúng người hơn), P-RETURNEE (gợi ý
theo nền tảng văn hoá chung trong cửa sổ thời gian ngắn khi về Việt Nam).

## Use Cases / Flows | Tình huống sử dụng / Luồng

1. Người dùng mở màn khám phá và thấy các hồ sơ được sắp xếp theo điểm gợi ý của AI thay vì chỉ theo khoảng cách.
2. Người dùng quẹt và tương tác; hệ thống ghi nhận tín hiệu để cải thiện gợi ý ở phiên sau.

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

- (không có — gợi ý bằng AI là `could` đợt này, không chặn lõi ghép đôi.)

### Should | Nên có

- (không có đợt này.)

### Could | Có thể có

- Xếp hạng hồ sơ trên màn khám phá theo điểm gợi ý do mô hình tính, thay cho thứ tự chỉ-theo-khoảng-cách.
- Thu thập tín hiệu tương tác (quẹt, match chuyển thành nhắn tin duy trì) để dùng làm dữ liệu huấn luyện.

### Won't (this round) | Không (lần này)

- Mô hình học sâu tự huấn luyện / hạ tầng ML cụ thể (đội build chọn ở giai đoạn triển khai).
- Giải thích lý do gợi ý ("vì sao bạn thấy người này") — cân nhắc cycle sau.
- Gợi ý dựa trên dữ liệu ngoài app (mạng xã hội, danh bạ) — ngoài phạm vi vì lý do an toàn & riêng tư.

## Non-Functional Requirements | Yêu cầu phi chức năng

Thứ tự gợi ý không được làm chậm cảm nhận tải màn khám phá trên thiết bị di động phổ thông tại Việt
Nam. Khi chưa đủ dữ liệu cho một người dùng (người mới), hệ thống phải có cách xếp mặc định hợp lý
(ví dụ theo khoảng cách + độ hoạt động) thay vì để màn khám phá trống.

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

- `weekly-match-rate` → BRD-G2 (tỉ lệ người dùng hoạt động tạo từ 1 match trở lên mỗi tuần — gợi ý tốt hơn kỳ vọng nâng tỉ lệ này, nhưng phải canh để không kéo lệch khỏi north-star kết nối duy trì).
