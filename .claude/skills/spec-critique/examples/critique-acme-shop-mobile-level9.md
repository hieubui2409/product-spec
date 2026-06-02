# Critique: PRD-MOBILE  ·  mức 9 (mày/tao + chửi thề nhắm vào spec)  ·  lăng kính: product, tech, craft  [thiếu: market]

> Đếm mức độ: chặn 0 · nặng 2 · nhẹ 1
>
> _Báo cáo mẫu chạy trên `product-spec/examples/acme-shop`, phạm vi hẹp `PRD-MOBILE`, ở mức 9 (`mày/tao` + chửi thề
> `profanity=strong`, bỏ hết kiềm chế nội bộ). Soạn tay để minh hoạ lằn ranh không-bao-giờ-vượt: chửi thề văng thẳng vào
> CÔNG VIỆC, không một chữ nào nhắm vào con người, gia đình, vùng miền hay sự an toàn của người viết. Mỗi phát hiện vẫn
> có `mã:dòng` + cách sửa; câu khinh miệt có thể chen vào nhưng luôn nằm trong một phát hiện có căn cứ._

## Top 3 sửa ngay

1. **[nặng][product] PRD-MOBILE:13**. Đm, cả một app di động đặt làm mục tiêu năm hai (`BRD-G5`) mà để `moscow: could`,
   giá trị thì độc một câu "browse and buy faster". Nhanh hơn web chỗ nào? Không có. Banh xác vì: làm app cho có app,
   đú theo Shopify với Etsy chứ chẳng có lấy một nhu cầu di động nào riêng, viết kiểu này thì đội phát triển build xong
   cũng chẳng biết để làm gì. Gõ lại, đừng để tao nhắc lại: nêu một nhu cầu chỉ di động giải được, hoặc hạ kỳ vọng và
   ghi thẳng đây là chạy theo cho kịp.
2. **[nặng][tech] PRD-MOBILE-E1-S1:18**. `size: L` (`PRD-MOBILE-E1-S1:14`) mà nhồi cả xem hàng lẫn mua hàng vào hai
   dòng AC, lại còn tỉnh bơ dựa vào "the existing web checkout is presented in the app shell" như thể nó tự chạy. Đậu
   xanh, cái story này vừa to vl vừa giấu một phụ thuộc chưa ai xác nhận. Banh xác vì: không đạt INVEST, mà cái luồng web
   nhúng vô vỏ app hỏng thì hỏng cả story. Gõ lại, đừng để tao nhắc lại: tách hai story, thêm tiêu chí kiểm chứng luồng
   web chạy được trong vỏ app, khai `depends_on`.
3. **[nhẹ][craft] PRD-MOBILE-E1-S1:26**. "a fast, native path", lại "fast" vl. Bê nguyên một tính từ không đo được vào
   đúng câu giá trị. Banh xác vì: nhanh bao nhiêu thì chẳng ai nghiệm thu nổi, đội QA ngồi nhìn. Gõ lại, đừng để tao
   nhắc lại: bỏ "fast" hoặc thay bằng số, ví dụ p95 mở app dưới 1 giây.

## Theo từng lăng kính

### Product
- **[nặng] PRD-MOBILE:13**. (xem Top 3 mục 1) Chỉ tả cơ chế, không có nhu cầu di động riêng.

### Tech
- **[nặng] PRD-MOBILE-E1-S1:18**. (xem Top 3 mục 2) Quá to + phụ thuộc bị giấu.

### Craft
- **[nhẹ] PRD-MOBILE-E1-S1:26**. (xem Top 3 mục 3) "fast" không đo được trong câu giá trị.

## Lỗi lặp lại từ lần trước

- Không có, chưa có báo cáo critique nào trước đây.

## Đáng ghi thành quyết định (DEC)

- **Mức ưu tiên `could` của PRD-MOBILE so với `BRD-G5` (`approved`).** Phán quyết về phạm vi/ưu tiên. Chốt hướng thì ghi
  một `DEC-<số>` (`[nguồn: critique]`) qua `decision_register.py`. Không tự sửa hạng mục đã duyệt; hỏi giữ / đổi / dung hòa.
