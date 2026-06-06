---
id: PRD-FUND
type: prd
brd_goals: ["BRD-G1", "BRD-G2", "BRD-G3"]
status: draft
lang: vi
owner: TBD
version: 0.1.0
created: 2026-06-06
updated: 2026-06-06
personas: ["roommate", "fund-keeper"]
scope: core-value
moscow: must
horizon: now
metrics: ["groups-with-fund", "group-retention-d30", "fund-tx-per-active-group"]
risks: [{"description": "Số dư quỹ sai lệch so với thực tế sẽ làm sụp đổ niềm tin vào tính minh bạch", "impact": "high", "likelihood": "med", "status": "open", "mitigation": "Số dư luôn dẫn xuất = tổng nộp − tổng chi; mọi sửa/xóa giao dịch đều lưu vết; không cho chỉnh số dư trực tiếp"}, {"description": "Quỹ chỉ hữu ích khi cả nhóm cùng theo dõi; nếu chỉ fund-keeper ghi thì thành viên vẫn phải tin", "impact": "med", "likelihood": "med", "status": "open", "mitigation": "Cho mọi thành viên xem realtime số dư + lịch sử; đợt sau cho thành viên tự ghi khoản nộp của mình"}]
competitive_parity: {"COMP-SPLITWISE": "ahead", "COMP-MONEYLOVER": "none", "COMP-MANUAL": "ahead"}
scope_intent: mvp
---

# Quỹ phòng cốt lõi — PRD PRD-FUND

## Overview & Problem | Tổng quan và Vấn đề

Đây là trái tim của Sổ Quỹ: cuốn sổ quỹ chung mà cả nhóm cùng theo dõi. Hôm nay, một nhóm ở ghép quản lý tiền chung bằng cách một người ghi vào Excel/sổ tay — chỉ người đó thấy, các thành viên còn lại phải tin. Khi cần biết "quỹ còn bao nhiêu" hay "tháng này tiêu vào đâu", không ai tra được nhanh.

Sau khi có PRD-FUND: bất kỳ thành viên nào cũng mở app lên là thấy **số dư quỹ hiện tại** và **toàn bộ lịch sử thu chi** (ai nộp, chi vào việc gì, bao nhiêu, khi nào) — cập nhật ngay lập tức. Người giữ quỹ chỉ cần ghi mỗi khoản nộp/chi; phép tính số dư là tự động và không ai chỉnh tay được. Minh bạch chuyển từ "lời hứa của một người" thành "sự thật ai cũng kiểm chứng được".

## Personas | Nhóm người dùng

- **fund-keeper** — người ghi các khoản nộp và chi vào quỹ; cần thao tác nhanh và một bản ghi đáng tin để chứng minh minh bạch.
- **roommate** — thành viên xem số dư + lịch sử để biết mình đã nộp đủ chưa và quỹ đang được tiêu thế nào; là người hưởng lợi chính từ minh bạch.

## Use Cases / Flows | Tình huống sử dụng / Luồng

1. **Tạo quỹ:** fund-keeper tạo một quỹ cho nhóm (đặt tên quỹ, đơn vị tiền VNĐ).
2. **Ghi khoản nộp:** một thành viên góp tiền → fund-keeper ghi khoản nộp (ai nộp, số tiền, ngày).
3. **Ghi khoản chi:** quỹ chi cho việc chung (điện, nước, đồ dùng) → fund-keeper ghi khoản chi (chi việc gì, số tiền, ngày).
4. **Xem số dư:** bất kỳ thành viên nào mở app → thấy ngay số dư quỹ hiện tại.
5. **Xem lịch sử:** thành viên xem dòng thời gian thu chi để đối soát "tiền đi đâu".
6. **Sửa/xóa khi nhầm:** fund-keeper sửa hoặc xóa một giao dịch ghi sai, có lưu vết để vẫn minh bạch.

## Functional Requirements (MoSCoW) | Yêu cầu chức năng (MoSCoW)

### Must | Bắt buộc

- **M1 — Tạo quỹ nhóm:** đặt tên quỹ + đơn vị tiền (VNĐ).
- **M2 — Ghi khoản nộp quỹ:** ai nộp, số tiền, ngày.
- **M3 — Ghi khoản chi từ quỹ:** chi việc gì, số tiền, ngày.
- **M4 — Xem số dư quỹ hiện tại:** dẫn xuất tự động = tổng nộp − tổng chi.
- **M5 — Xem lịch sử thu chi:** dòng thời gian (ai / việc gì / bao nhiêu / khi nào).

### Should | Nên có

- **S1 — Sửa / xóa giao dịch:** chỉnh khoản ghi sai, có lưu vết thay đổi.
- **S2 — Ghi chú cho giao dịch:** thêm mô tả tự do cho mỗi khoản.

### Could | Có thể có

- **C1 — Đính kèm ảnh hóa đơn:** chụp/đính ảnh chứng từ cho khoản chi.
- **C2 — Gắn nhãn phân loại chi:** vd điện, nước, đồ ăn, đồ dùng.

### Won't (this round) | Không (lần này)

- Hạn mức / ngân sách quỹ (cảnh báo vượt mức).
- Nhắc đóng quỹ tự động.
- Xuất báo cáo ra file (PDF/Excel).

## Non-Functional Requirements | Yêu cầu phi chức năng

- **Bảo mật dữ liệu:** chỉ thành viên của nhóm xem được quỹ của nhóm mình; dữ liệu tiền bạc được bảo vệ (khớp ràng buộc niềm tin của BRD).
- **Bản địa hóa VN:** tiếng Việt, định dạng số tiền VNĐ, ngày tháng kiểu Việt Nam.
- **Tin cậy số liệu:** số dư luôn đúng bằng tổng nộp − tổng chi; không bao giờ lệch — đây là nền tảng của minh bạch.
- **Nhanh / nhẹ:** ghi một giao dịch nhanh, mượt trên điện thoại phổ thông cấu hình thấp.

## Success Metrics → BRD Goals | Chỉ số thành công → Mục tiêu BRD

- `fund-tx-per-active-group` (≥ 8/tháng) → **BRD-G3 Usage**: M2/M3 là nơi sinh ra giao dịch quỹ, gắn trực tiếp north-star.
- `group-retention-d30` (≥ 50%) → **BRD-G2 Retention**: M4/M5 (số dư + lịch sử minh bạch) là lý do nhóm quay lại mỗi tháng.
- `groups-with-fund` (10.000/12th) → **BRD-G1 Acquisition**: M1 (tạo quỹ dùng được) là điều kiện để giữ nhóm mới tạo.

## Scope In / Out | Phạm vi Trong / Ngoài

**In scope | Trong phạm vi:**

- Ghi sổ quỹ thuần túy: tạo quỹ, ghi nộp, ghi chi, xem số dư + lịch sử (chỉ là *bản ghi*, không phải dòng tiền thật).

**Out of scope | Ngoài phạm vi:**

- **Giữ tiền thật / thanh toán trong app** (VietQR, ví) — bị ràng buộc cứng của BRD chặn ở giai đoạn đầu; app chỉ ghi sổ.
- **Tạo nhóm & mời thành viên** — thuộc PRD-GROUP (PRD-FUND giả định nhóm đã tồn tại).
- **Chia tiền P2P (ai nợ ai)** — không thuộc mô hình QUỸ lõi.

## Dependencies & Risks | Phụ thuộc và Rủi ro

**Phụ thuộc:** cần có khái niệm "nhóm" và "thành viên" để gắn quỹ vào — phần tạo nhóm/mời thành viên nằm ở PRD-GROUP. Ở MVP, có thể tạm dùng một nhóm đơn giản; quan hệ phụ thuộc này sẽ ghi rõ khi PRD-GROUP ra đời.

**Rủi ro chính** (chi tiết enum trong frontmatter `risks:`):

1. **Số dư sai lệch** *(ảnh hưởng: cao · khả năng: trung bình)* → số dư luôn dẫn xuất tự động, mọi sửa/xóa lưu vết, không cho chỉnh số dư tay.
2. **Cả nhóm phải cùng theo dõi mới có giá trị** *(trung bình · trung bình)* → cho mọi thành viên xem realtime; đợt sau cho thành viên tự ghi khoản nộp.



