---
id: BRD
type: brd
status: draft
lang: vi
owner: TBD
version: 0.1.0
created: 2026-06-06
updated: 2026-06-06
goals: [{"id": "BRD-G1", "title": "Đạt 10.000 nhóm tạo quỹ thật trong 12 tháng đầu", "metrics": ["groups-with-fund"], "status": "draft", "owner": "TBD"}, {"id": "BRD-G2", "title": "Giữ tỷ lệ nhóm còn hoạt động sau 30 ngày ≥ 50%", "metrics": ["group-retention-d30"], "status": "draft", "owner": "TBD"}, {"id": "BRD-G3", "title": "Đạt trung bình ≥ 8 giao dịch quỹ / nhóm hoạt động / tháng", "metrics": ["fund-tx-per-active-group"], "status": "draft", "owner": "TBD"}, {"id": "BRD-G4", "title": "Đạt trung bình ≥ 3 thành viên / nhóm", "metrics": ["members-per-group"], "status": "draft", "owner": "TBD"}]
competitors: [{"id": "COMP-SPLITWISE", "name": "Splitwise", "url": "https://www.splitwise.com", "threat": "med"}, {"id": "COMP-MONEYLOVER", "name": "Money Lover / Sổ Thu Chi", "url": "https://moneylover.me", "threat": "med"}, {"id": "COMP-MANUAL", "name": "Zalo/Messenger + chuyển khoản tay", "url": "private:manual-workflow", "threat": "high"}]
risks: [{"description": "Mục tiêu 10.000 nhóm/năm có thể bất khả thi nếu thiếu kênh phân phối lớn hoặc viral mạnh", "impact": "high", "likelihood": "high", "status": "open", "mitigation": "Đặt mốc trung gian (vd 500 → 2.000 → 10.000), xác định kênh phân phối cụ thể (cộng đồng trọ, trường ĐH); coi 10k là stretch goal, có mốc nền thấp hơn để không vỡ kế hoạch"}, {"description": "Chicken-and-egg: quỹ chung chỉ có giá trị khi cả nhóm cùng dùng, một người dùng lẻ không đủ", "impact": "high", "likelihood": "med", "status": "open", "mitigation": "Onboarding kéo cả nhóm trong một lần (fund-keeper mời hàng loạt); đảm bảo có giá trị ngay cả khi mới một người ghi sổ"}, {"description": "Thói quen Zalo/Messenger + chuyển khoản tay đã ăn sâu, đổi thói quen là rào cản lớn", "impact": "med", "likelihood": "high", "status": "open", "mitigation": "Giảm ma sát nhập liệu so với nhắn tay; nhắc nợ/tổng kết tự động mà nhắn tay không làm được"}, {"description": "Niềm tin dữ liệu tài chính: sai sót số liệu quỹ hoặc lộ dữ liệu làm mất niềm tin tức thì", "impact": "high", "likelihood": "med", "status": "open", "mitigation": "Bảo mật dữ liệu; giai đoạn đầu KHÔNG giữ tiền thật (chỉ ghi sổ); lịch sử minh bạch, bất biến để ai cũng đối soát được"}]
---

# Business Requirements Document | Tài liệu Yêu cầu Kinh doanh

## Problem / Opportunity | Vấn đề / Cơ hội

Việt Nam có một lượng lớn người ở trọ và ở ghép — sinh viên và người đi làm trẻ — mà mỗi nhóm là một "đơn vị tài chính chung" nhỏ: cùng góp, cùng chi, cùng cần minh bạch. Thị trường này hiện **chưa có công cụ quỹ chung được bản địa hóa**: các app quản lý chi tiêu phổ biến (Money Lover, Sổ Thu Chi) thiết kế cho cá nhân, còn app chia tiền quốc tế (Splitwise) thì xoay quanh mô hình chia nợ P2P, không có khái niệm "quỹ phòng" — cuốn sổ chung mà cả nhóm cùng theo dõi.

Cơ hội cốt lõi là **lấp khoảng trống bản địa**: là sản phẩm đầu tiên đưa mô hình QUỸ (nộp → chi → ai cũng thấy số dư) vào đúng ngữ cảnh người ở trọ VN, với tiếng Việt, VietQR và khái niệm quen thuộc. Ai chiếm được vị trí "sổ quỹ mặc định" sớm sẽ hưởng lợi thế thói quen và truyền miệng trong cộng đồng trọ.

Nếu không hành động: khoảng trống này sẽ để ngỏ cho một đối thủ bản địa hóa nhanh hơn chiếm lấy, và hàng triệu nhóm ở ghép tiếp tục chịu cảnh thiếu minh bạch — một người ôm sổ, cả phòng phải tin.

## Business Goals | Mục tiêu kinh doanh

Bốn mục tiêu cho 12 tháng đầu, bám theo phễu acquisition → retention → usage → virality. Đây là **giả thuyết mục tiêu** ở giai đoạn ý tưởng, sẽ hiệu chỉnh khi có dữ liệu thực:

- **BRD-G1 — Acquisition:** Đạt **10.000 nhóm** tạo quỹ thật trong 12 tháng đầu. *(Mục tiêu stretch — xem rủi ro tham vọng ở mục Giả định & Rủi ro.)*
- **BRD-G2 — Retention:** Giữ tỷ lệ nhóm còn hoạt động sau 30 ngày **≥ 50%** — bằng chứng app trở thành thói quen, không chỉ tải về rồi bỏ.
- **BRD-G3 — Usage:** Trung bình **≥ 8 giao dịch quỹ / nhóm hoạt động / tháng** (nộp + chi). Bám sát north-star "số GD quỹ/tháng" — đo lượng dùng thực của tính năng lõi.
- **BRD-G4 — Virality:** Trung bình **≥ 3 thành viên / nhóm** — fund-keeper kéo được cả phòng vào, điều kiện để mô hình quỹ chung có nghĩa.

## Success Metrics | Chỉ số thành công

Mỗi mục tiêu gắn đúng một chỉ số đo được:

- `groups-with-fund` — số nhóm đã tạo quỹ và có ≥ 1 giao dịch (BRD-G1). Mục tiêu: 10.000 / 12 tháng.
- `group-retention-d30` — % nhóm còn ghi giao dịch trong khoảng ngày 23–30 sau khi tạo (BRD-G2). Mục tiêu: ≥ 50%.
- `fund-tx-per-active-group` — trung bình số giao dịch quỹ/nhóm-hoạt-động/tháng (BRD-G3). Mục tiêu: ≥ 8.
- `members-per-group` — trung bình số thành viên đã tham gia mỗi nhóm (BRD-G4). Mục tiêu: ≥ 3.

## Stakeholders | Bên liên quan

- **Founder (hieubt)** — người quyết định sản phẩm; chịu trách nhiệm định hướng và phê duyệt cuối.
- **Nhà đầu tư / mentor** — cần được thuyết phục ở các mốc quan trọng (gọi vốn, mở rộng). Mục tiêu kinh doanh trong tài liệu này chính là ngôn ngữ chung với họ.
- **Người dùng đại diện** (gián tiếp) — các nhóm ở ghép thử nghiệm sớm; tiếng nói của họ định hình ưu tiên qua phản hồi thực tế.

## Constraints | Ràng buộc

- **Ngân sách hạn chế** — bootstrap, ít vốn; phải ưu tiên thứ rẻ/miễn phí, làm gọn, tránh hạ tầng đắt đỏ.
- **Thời gian / nhân lực** — đội nhỏ (có thể làm bán thời gian); phạm vi từng đợt phải thật tinh gọn, ưu tiên đúng việc cốt lõi.
- **Chỉ mobile** — giai đoạn đầu chỉ làm app mobile (iOS & Android), chưa có web.
- **Niềm tin & bảo mật dữ liệu tài chính** *(ràng buộc cứng)* — dữ liệu tiền bạc nhạy cảm: phải bảo mật và minh bạch. **Giai đoạn đầu KHÔNG giữ tiền thật** (app chỉ ghi sổ quỹ, không phải ví/thanh toán) để tránh rủi ro pháp lý và rào cản niềm tin.

## Market Context | Bối cảnh thị trường

Không gian "tiền chung của nhóm" hiện được lấp tạm bằng bốn lựa chọn, không cái nào trúng đích:

- **COMP-SPLITWISE (Splitwise)** — mạnh ở chia nợ P2P quốc tế, nhưng không có mô hình quỹ pot và không bản địa hóa VN (không VietQR, không khái niệm quỹ phòng). *Đe dọa: trung bình.*
- **COMP-MONEYLOVER (Money Lover / Sổ Thu Chi)** — app quản lý chi tiêu cá nhân VN, mạnh cho một người, không chuyên quỹ nhóm minh bạch. *Đe dọa: trung bình.*
- **Excel / Google Sheets** — cách thủ công phổ biến nhất; chính là "status quo" mà Sổ Quỹ thay thế (không tự nhắc, không realtime, dễ sai).
- **COMP-MANUAL (Zalo/Messenger + chuyển khoản tay)** — hành vi mặc định của rất nhiều nhóm: nhắn tin nhắc nợ + chuyển khoản tay. *Đe dọa: cao* — không phải vì tính năng, mà vì đây là thói quen ăn sâu, đối thủ thật sự cần đánh bại.

**Khác biệt của Sổ Quỹ:** mô hình QUỸ (pot) minh bạch realtime cho cả nhóm + bản địa hóa sâu cho người ở trọ VN — thứ không lựa chọn nào ở trên cung cấp trọn vẹn.

## Assumptions & Risks | Giả định và Rủi ro

Bốn rủi ro chính (chi tiết enum + cách giảm thiểu trong frontmatter `risks:`):

1. **Tham vọng acquisition** — 10.000 nhóm/năm có thể bất khả thi nếu thiếu kênh phân phối lớn/viral mạnh *(ảnh hưởng: cao · khả năng: cao)*. Giảm thiểu: mốc trung gian + xác định kênh cụ thể; coi 10k là stretch.
2. **Chicken-and-egg** — quỹ chung chỉ có giá trị khi cả nhóm cùng dùng *(cao · trung bình)*. Giảm thiểu: onboarding kéo cả nhóm một lần; có giá trị ngay cả khi mới một người ghi.
3. **Thói quen Zalo + CK tay** — đổi thói quen là rào cản lớn *(trung bình · cao)*. Giảm thiểu: giảm ma sát nhập liệu + nhắc nợ/tổng kết tự động.
4. **Niềm tin dữ liệu tài chính** — sai số liệu hoặc lộ dữ liệu mất niềm tin tức thì *(cao · trung bình)*. Giảm thiểu: bảo mật + không giữ tiền thật giai đoạn đầu + lịch sử minh bạch, đối soát được.

## Goal → Metric Table | Bảng Mục tiêu → Chỉ số

| Goal ID | Goal | Metric | Target |
|---------|------|--------|--------|
| BRD-G1 | Số nhóm tạo quỹ (acquisition) | `groups-with-fund` | 10.000 / 12 tháng |
| BRD-G2 | Nhóm còn hoạt động sau 30 ngày (retention) | `group-retention-d30` | ≥ 50% |
| BRD-G3 | GD quỹ / nhóm hoạt động / tháng (usage) | `fund-tx-per-active-group` | ≥ 8 |
| BRD-G4 | Thành viên / nhóm (virality) | `members-per-group` | ≥ 3 |

