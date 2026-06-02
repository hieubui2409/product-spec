# Critique: PRD-AIREC · level 3 · lenses: market  [missing: product, tech, craft]

> Severity tally: blocker 0 · major 2 · minor 1

## Top 3: sửa ngay

1. **[major][market] PRD-AIREC:223**, spec tự khai `competitive_parity: behind` với cả Tinder lẫn Bumble rồi vẫn quyết xây tính năng me-too, mà không đặt tên nổi một unfair advantage nào. Tín hiệu ghi nhận ("quẹt + match chuyển thành nhắn tin duy trì") đúng thứ Tinder và Bumble đã có từ 2016, chỉ khác là dataset của Ghép Đôi Việt nhỏ hơn. **Toang ở đâu:** đến lúc PRD-AIREC được build (`horizon: later`), hai đối thủ có thêm vài năm dữ liệu nữa, mà Tinder cũng đang tối ưu trên hành vi người dùng Việt. Me-too với dataset nhỏ hơn không phải vị trí cạnh tranh, đó là thua mặc định. **Sửa:** hoặc (a) chỉ ra một tín hiệu dữ liệu Tinder/Bumble không có và mình thu được, ví dụ xác minh nghề/trường qua CCCD để dựng compatibility vector mà app phương Tây không dám đòi; hoặc (b) đổi framing từ "AI recommendation" sang "curated pool" quy mô nhỏ kiểm soát tay, vốn không phải đua ML scale; không làm được cả hai thì xóa PRD-AIREC khỏi roadmap, dồn effort vào thứ tạo được moat. **DEC-worthy.** *(Cùng họ lỗi me-too đã nói ở c1 MATCH, c3 CHAT, c4 EVENTS, c5 PREMIUM, c6 MATCH, vẫn chưa có một điểm "ahead" nào.)*

2. **[major][market] PRD-AIREC:204**, PRD-AIREC chỉ nối tới BRD-G2 (`weekly-match-rate`), không có đường nào chạm BRD-G3, mục tiêu duy nhất liên quan tới tiền (`premium-conversion-rate`, `arpu`, hòa vốn năm 2). Một tính năng `could`/`later` tốn effort L mà không ai giải thích nó kiếm tiền kiểu gì hay giúp ai trả tiền. **Toang ở đâu:** BRD-G3 là gate sinh tồn của sản phẩm. AIREC không nối tới premium conversion thì nó là gánh hạ tầng không sinh doanh thu, chi phí thuần trong giai đoạn chưa hòa vốn. **Sửa:** hoặc (a) chỉ rõ cơ chế monetization cụ thể, ví dụ "AI ranking chỉ ưu tiên hồ sơ verified-premium" để biến tính năng thành lý do nâng cấp, link thẳng BRD-G3; hoặc (b) nếu không có cơ chế nào hợp lý, drop AIREC và trả slot `later` cho tính năng có revenue path rõ. Chỉ thêm `brd_goals: [BRD-G3]` khi có cơ chế thật, đừng đánh dấu cho xong. **DEC-worthy.** *(BRD-G3 thiếu đường nối doanh thu đã treo từ c4, c5, c6, vẫn chưa khép con số.)*

3. **[minor][market] PRD-AIREC-E1-S1:303**, AC đặt ngưỡng cold-start 20 lượt quẹt; dưới ngưỡng thì người dùng thấy thứ tự khoảng-cách + độ-hoạt-động như mọi app khác. P-PROVINCE được nêu nhiều nhất như người hưởng lợi từ AI ranking, nhưng người ở tỉnh lẻ pool mỏng chưa chắc có nổi 20 hồ sơ để quẹt trong bán kính chấp nhận được. **Toang ở đâu:** AI ranking không đẻ ra hồ sơ mới. Pool địa phương cạn thì thứ tự xếp hạng vô nghĩa, không có hồ sơ để xếp. Spec giải sai bài: đổ tiền vào ranking algorithm trong khi JTBD thật của P-PROVINCE là supply/discovery expansion. Build xong, P-PROVINCE vẫn thấy pool rỗng, chỉ giờ được xếp đẹp hơn. **Sửa:** tách hai vấn đề trong PRD: (1) supply cho P-PROVINCE, giải bằng geo-expansion / matching toàn quốc / cross-city discovery trước khi ranking có nghĩa; (2) ranking quality cho P-URBAN pool dày, đây mới là persona thụ hưởng AI ranking. Viết lại persona mapping để đừng dùng P-PROVINCE biện minh cho AI ranking khi giải pháp thật của họ là khác.

## Theo lăng kính

### Market

- **[major] PRD-AIREC:223** -- me-too với Tinder/Bumble, không có unfair advantage được đặt tên (xem Top 3 #1). **DEC-worthy.**
- **[major] PRD-AIREC:204** -- không có đường nối tới BRD-G3, tính năng size L không có monetization path (xem Top 3 #2). **DEC-worthy.**
- **[minor] PRD-AIREC-E1-S1:303** -- cold-start 20-quẹt + P-PROVINCE bị dùng sai làm lý do, JTBD thật là supply chứ không phải ranking (xem Top 3 #3).

PRD-AIREC tự biết mình me-too, đặt `could`/`later` đúng chỗ, nhưng vẫn thiếu hai thứ không tính năng nào trên roadmap được phép thiếu: unfair advantage rõ so với Tinder/Bumble và đường nối tới doanh thu. Một feature size L, đi sau cả hai đối thủ lớn về data, không monetization, rồi được biện minh bằng persona mà vấn đề thật của họ không phải ranking. Đây là ứng cử viên để drop, không phải để defer.

### Product

Không có finding nào cho PRD-AIREC trong chu kỳ này.

### Tech

Chu kỳ này không phát sinh finding tech nào trên PRD-AIREC.

### Craft

PRD-AIREC sạch về craft trong chu kỳ này, không có gì để bắt.

## Lặp lại từ lần trước

- **Lỗi hệ thống me-too / không có điểm "ahead"** (PRD-AIREC:223): đã nói ở c1 (MATCH), c3 (CHAT), c4 (EVENTS), c5 (PREMIUM), c6 (MATCH, PRD-MATCH:382). Nay lặp lại trên PRD-AIREC, vẫn chưa có một điểm "ahead" nào trong toàn spec.
- **BRD-G3 không có đường nối doanh thu** (PRD-AIREC:204): cùng họ với gap đã nêu ở c4, c5 (BRD-G3:46) và c6 (BRD-G3:101, đánh dấu DEC-worthy). Lần này lỗ hổng nằm ở chỗ một tính năng size L tự cắt mình khỏi mọi revenue path. Đã nói ở các lần critique trước, vẫn chưa sửa.

## Đáng ghi thành quyết định (DEC-worthy)

- **Giữ hay drop PRD-AIREC** (PRD-AIREC:223 + :204): hoặc cam kết một unfair advantage thật (tín hiệu dữ liệu CCCD-based, hoặc đổi sang curated-pool) kèm một cơ chế monetization nối vào BRD-G3, hoặc xóa AIREC khỏi roadmap và trả slot `later`. Ruling này định ranh giới positioning (đua ML scale vs khác biệt bằng dữ liệu bản địa) và chạm BRD-G3 đã duyệt, PO nên ghi qua `--decision`.

## Câu hỏi chưa giải

- Chỉ market lens trả về finding; product/tech/craft trống cho chu kỳ này. Nếu đây là partial-failure chứ không phải "không có gì để phê", cần chạy lại ba lens kia trên PRD-AIREC để xác nhận không bỏ sót defect INVEST/khả thi kỹ thuật/diễn đạt.
