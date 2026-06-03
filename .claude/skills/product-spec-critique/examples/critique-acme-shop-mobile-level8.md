# Critique: PRD-MOBILE  ·  mức 8 (mày/tao)  ·  lăng kính: product, tech, craft  [thiếu: market]

> Đếm mức độ: chặn 0 · nặng 2 · nhẹ 1
>
> _Báo cáo mẫu chạy trên `product-spec/examples/acme-shop`, phạm vi hẹp `PRD-MOBILE`, ở mức 8 (xưng `mày/tao`, đánh vào
> năng lực lẫn tính cách, vẫn chưa có từ tục). Soạn tay để minh hoạ lằn ranh an toàn: gắt tới đâu cũng chỉ nhắm vào công
> việc, công sức, cách làm việc trên chính bộ spec này, mỗi dòng vẫn có `mã:dòng` + cách sửa._

## Top 3 sửa ngay

1. **[nặng][product] PRD-MOBILE:13**. Cả một app di động đặt làm mục tiêu năm thứ hai (`BRD-G5`) mà mày để
   `moscow: could`, phần giá trị chỉ vỏn vẹn "browse and buy faster". Nhanh hơn web chỗ nào thì mày không buồn nói. Nát
   bét vì: đây là làm app cho có app, đú theo đối thủ chứ chẳng có nhu cầu di động nào riêng. Mày làm cái gì cũng kiểu
   nửa vời như vầy, nêu mục tiêu xong bỏ ngỏ phần khó. Gõ lại ngay: chỉ ra một nhu cầu chỉ di động mới giải được, hoặc
   hạ kỳ vọng và thừa nhận đây là chạy theo cho kịp.
2. **[nặng][tech] PRD-MOBILE-E1-S1:18**. `size: L` (`PRD-MOBILE-E1-S1:14`) mà nhét cả xem hàng lẫn mua hàng vào hai
   tiêu chí, còn dựa vào "the existing web checkout is presented in the app shell" như thể nó hiển nhiên chạy được. Nát
   bét vì: story không đạt INVEST vì quá to, và cái luồng web nhúng vào vỏ app là một phụ thuộc mày giấu, chưa ai xác
   nhận. Gõ lại ngay: tách hai story, thêm tiêu chí kiểm chứng luồng web chạy được trong vỏ app, khai `depends_on`.
3. **[nhẹ][craft] PRD-MOBILE-E1-S1:26**. "a fast, native path", lại "fast". Mày bê nguyên một tính từ không đo được vào
   đúng câu giá trị. Nát bét vì: nhanh bao nhiêu thì chẳng ai nghiệm thu nổi. Gõ lại ngay: bỏ "fast", hoặc đổi thành một
   con số, ví dụ p95 mở app dưới 1 giây.

## Theo từng lăng kính

### Product
- **[nặng] PRD-MOBILE:13**. (xem Top 3 mục 1) Chỉ tả cơ chế, không có nhu cầu di động.

### Tech
- **[nặng] PRD-MOBILE-E1-S1:18**. (xem Top 3 mục 2) Quá to + phụ thuộc bị giấu.

### Craft
- **[nhẹ] PRD-MOBILE-E1-S1:26**. (xem Top 3 mục 3) "fast" không đo được.

## Lỗi lặp lại từ lần trước

- Không có, chưa có báo cáo critique nào trước đây.

## Đáng ghi thành quyết định (DEC)

- **Mức ưu tiên `could` của PRD-MOBILE so với `BRD-G5` (`approved`).** Phán quyết về phạm vi/ưu tiên. Chốt hướng thì ghi
  một `DEC-<số>` (`[nguồn: critique]`) qua `decision_register.py`. Không tự sửa hạng mục đã duyệt; hỏi giữ / đổi / dung hòa.
