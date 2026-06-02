# Critique: all  ·  mức 3 (blunt)  ·  lăng kính: product, tech, market, craft

> Đếm mức độ: chặn 0 · nặng 4 · nhẹ 3
>
> _Báo cáo mẫu chạy trên `product-spec/examples/acme-shop` ở mức mặc định. Soạn tay để minh hoạ hợp đồng đầu ra
> (bằng chứng `mã:dòng`, câu chê, vì sao chết, cách sửa, đủ trên mỗi dòng). Một lần chạy thật sẽ phản ánh spec sống cùng
> dữ liệu tra mạng._

## Top 3 sửa ngay

1. **[nặng][product · market] PRD-MOBILE:5**. Di động được đặt thành mục tiêu của năm thứ hai (`BRD-G5`), nhưng cả PRD
   lẫn story chỉ hứa hẹn một ứng dụng di động riêng "cho nhanh", chẳng nói được nhu cầu trên di động khác gì so với trên web. Vì sao
   chết: làm ứng dụng chỉ để cho có ứng dụng. Trường `competitive_parity` ghi `behind` cả Shopify lẫn Etsy mà mức ưu
   tiên vẫn để `moscow: could`, tức là đuổi cho bằng đối thủ chứ không có gì khác biệt. Sửa: nêu một nhu cầu chỉ di động
   mới đáp ứng được (đẩy thông báo khi cửa hàng ra mẫu mới, mua hàng lúc đang di chuyển), hoặc hạ kỳ vọng xuống và nói
   thẳng rằng đây chỉ là chạy theo cho bằng bạn bằng bè.
2. **[nặng][tech] PRD-MOBILE-E1-S1:18**. Story để `size: L` mà gộp cả việc xem hàng lẫn mua hàng vào hai tiêu chí
   nghiệm thu, lại còn dựa vào việc "tái dùng luồng thanh toán web nhúng trong vỏ ứng dụng". Toang ở đâu: nó không đạt
   INVEST vì không đủ nhỏ, và chuyện "luồng thanh toán web có nhúng được vào ứng dụng hay không" là một phụ thuộc bị
   giấu mà chưa ai xác nhận. Vỡ ở chỗ đó là vỡ cả story. Sửa: tách thành hai story riêng (xem hàng và mua hàng), thêm
   một tiêu chí kiểm chứng luồng thanh toán web hiển thị và hoàn tất được trong vỏ ứng dụng, hoặc khai một `depends_on`
   cho rõ ràng.
3. **[nặng][product] PRD-ANALYTICS:5**. Phần phân tích số liệu (`should`, `next`, `depends_on: PRD-PAYOUTS`) lại được
   đẩy lên làm trước, trong khi lộ trình nói rõ fan-CRM mới là mũi nhọn. Toang ở đâu: dồn sức của một đội nhỏ vào cái
   bảng số liệu mà ai cũng có, thay vì làm thứ đối thủ khó sao chép. Sửa: nói rõ vì sao phân tích số liệu phải đi trước
   fan-CRM, hoặc đảo lại thứ tự ưu tiên.

## Theo từng lăng kính

### Product
- **[nặng] PRD-MOBILE:5**. (xem Top 3 mục 1) Chưa có nhu cầu di động nào được nêu ra, story chỉ tả cơ chế chứ không tả
  nhu cầu.
- **[nặng] PRD-ANALYTICS:5**. (xem Top 3 mục 3) Chi phí cơ hội so với fan-CRM vẫn chưa được biện minh.
- **[nhẹ] PRD-ANALYTICS-E1-S1:17**. Tiêu chí thứ hai, "totals reconcile with payout statements", là một tiêu chí tốt.
  Giữ nguyên, và lấy nó làm mẫu cho các story khác vì nó có kết quả đo được. _(Đây là lời khen có căn cứ, không phải lỗi.)_

### Tech
- **[nặng] PRD-MOBILE-E1-S1:18**. (xem Top 3 mục 2) Không đạt INVEST, kèm một phụ thuộc bị giấu.
- **[nhẹ] PRD-ANALYTICS:15**. Rủi ro "dashboard query load degrades storefront latency" có kèm biện pháp giảm thiểu
  (dùng bản sao đọc cùng bảng tổng hợp), nhưng chưa có tiêu chí nghiệm thu hay yêu cầu phi chức năng nào ràng buộc rằng
  "không bao giờ chạm vào cơ sở dữ liệu chính". Toang ở đâu: biện pháp giảm thiểu chỉ nằm ở phần mô tả nên đội phát
  triển không bị buộc phải theo. Sửa: thêm một tiêu chí phi chức năng nói rằng truy vấn phân tích phải chạy trên bản sao
  đọc, và độ trễ p95 của cửa hàng không được đổi.

### Market
- **[nặng] PRD-MOBILE:28**. `competitive_parity: {COMP-SHOPIFY: behind, COMP-ETSY: behind}` đi kèm `moscow: could`:
  đang thua hai đối thủ ở mảng này mà lại xếp vào mức ưu tiên thấp nhất. Toang ở đâu: hoặc di động quan trọng, thì đừng
  để `could`; hoặc nó không quan trọng, thì đừng coi là mục tiêu của cả BRD. Sửa: chốt lấy một hướng, nâng ưu tiên kèm
  lý do, hoặc gỡ nó ra khỏi mục tiêu năm thứ hai.
- _(Lăng kính thị trường dựa vào danh sách `competitors:` trong BRD; nếu thiếu mà lại bật `--no-web` thì nó sẽ gắn cờ
  "thiếu căn cứ cạnh tranh".)_

### Craft
- **[nhẹ] PRD-MOBILE-E1-S1:29**. Cụm "a fast, native path" có chữ "fast", một tính từ không đo được, nằm ngay trong câu
  nói về giá trị. Toang ở đâu: nhanh tới đâu thì mỗi người hiểu một kiểu. Sửa: bỏ chữ "fast" khỏi câu giá trị, hoặc đẩy
  nó xuống thành một yêu cầu phi chức năng có con số, ví dụ p95 mở ứng dụng dưới 1 giây.
- **[nhẹ] PRD-ANALYTICS-E1-S1:21**. Câu "tell whether the business is growing" thì ổn, nhưng "which periods worked" lại
  mơ hồ, "worked" nghĩa là gì? Toang ở đâu: thước đo thành công không rõ ràng. Sửa: đổi thành "so sánh doanh thu giữa
  các kỳ đã chọn".

## Lỗi lặp lại từ lần trước

- Không có, vì chưa có báo cáo critique nào trước đây trong `docs/product/critique/`.

## Đáng ghi thành quyết định (DEC)

- **Mức ưu tiên `could` của PRD-MOBILE so với mục tiêu năm thứ hai `BRD-G5`.** Đây là một phán quyết về phạm vi và ưu
  tiên, mà `PRODUCT.md` cùng `BRD` thì đang ở trạng thái `approved`. Nếu người làm sản phẩm chốt được hướng đi, hãy ghi
  một bản ghi `DEC-<số>` (phần lý do mở đầu bằng `[nguồn: critique]`) qua `decision_register.py`. Tuyệt đối không tự sửa
  một hạng mục đã duyệt; hãy hỏi giữ nguyên, đổi, hay dung hòa trước đã.
