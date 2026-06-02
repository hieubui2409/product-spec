# Critique: PRD-MOBILE  ·  mức 7 (ông/tôi)  ·  lăng kính: product, tech, craft  [thiếu: market]

> Đếm mức độ: chặn 0 · nặng 2 · nhẹ 1
>
> _Báo cáo mẫu chạy trên `product-spec/examples/acme-shop`, phạm vi hẹp `PRD-MOBILE`, ở mức 7 (xưng `ông/tôi`, đánh vào
> năng lực, chưa có từ tục). Soạn tay để minh hoạ hợp đồng đầu ra + lằn ranh an toàn (mỗi dòng có `mã:dòng` + cách sửa;
> công kích nhắm vào công việc và năng lực, không nhắm vào con người)._

## Top 3 sửa ngay

1. **[nặng][product] PRD-MOBILE:13**. Ông đặt cả một ứng dụng di động làm mục tiêu năm thứ hai (`BRD-G5`) mà lại để
   `moscow: could`, rồi phần giá trị chỉ nói "browse and buy faster". Nhanh hơn web ở chỗ nào thì không thấy ông trả
   lời. Banh nóc vì: làm app chỉ để có app, đúng kiểu chạy theo cho bằng đối thủ chứ không có nhu cầu di động nào riêng.
   Tư duy sản phẩm tới đây là còn non. Gõ lại cho tử tế: nêu một nhu cầu chỉ di động mới đáp ứng được (đẩy thông báo khi
   thương hiệu ra mẫu mới, mua nhanh lúc đang di chuyển), hoặc hạ kỳ vọng và nói thẳng đây là đuổi cho kịp.
2. **[nặng][tech] PRD-MOBILE-E1-S1:18**. Story để `size: L` (`PRD-MOBILE-E1-S1:14`) mà gộp cả xem hàng lẫn mua hàng vào
   hai tiêu chí, lại dựa vào "the existing web checkout is presented in the app shell". Banh nóc vì: không đạt INVEST vì
   quá lớn, và chuyện luồng thanh toán web nhúng được vào vỏ app hay không là một phụ thuộc bị giấu, chưa ai xác nhận.
   Gõ lại cho tử tế: tách thành hai story (xem hàng / mua hàng), thêm một tiêu chí kiểm chứng luồng web hiển thị và hoàn
   tất được trong vỏ app, hoặc khai một `depends_on` cho rõ.
3. **[nhẹ][craft] PRD-MOBILE-E1-S1:26**. Câu giá trị "a fast, native path" có chữ "fast", một tính từ không đo được,
   nằm ngay chỗ quan trọng nhất. Banh nóc vì: nhanh tới đâu thì mỗi người hiểu một kiểu, đội phát triển không có gì để
   nghiệm thu. Gõ lại cho tử tế: bỏ "fast" khỏi câu giá trị, hoặc đẩy xuống thành một yêu cầu phi chức năng có số, ví dụ
   p95 mở app dưới 1 giây.

## Theo từng lăng kính

### Product
- **[nặng] PRD-MOBILE:13**. (xem Top 3 mục 1) Chưa nêu được nhu cầu di động nào, chỉ tả cơ chế.

### Tech
- **[nặng] PRD-MOBILE-E1-S1:18**. (xem Top 3 mục 2) Không đạt INVEST + một phụ thuộc bị giấu.

### Craft
- **[nhẹ] PRD-MOBILE-E1-S1:26**. (xem Top 3 mục 3) "fast" là tính từ không đo được trong câu giá trị.

## Lỗi lặp lại từ lần trước

- Không có, chưa có báo cáo critique nào trước đây.

## Đáng ghi thành quyết định (DEC)

- **Mức ưu tiên `could` của PRD-MOBILE so với mục tiêu năm thứ hai `BRD-G5`.** Đây là phán quyết về phạm vi và ưu tiên,
  mà `BRD` đang ở trạng thái `approved`. Nếu ông chốt được hướng, hãy ghi một `DEC-<số>` (lý do mở đầu `[nguồn: critique]`)
  qua `decision_register.py`. Không tự sửa hạng mục đã duyệt; hỏi giữ nguyên / đổi / dung hòa trước.
