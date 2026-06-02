# Critique: all  ·  mức 1 (warm)  ·  lăng kính: product, tech, market, craft

> Đếm mức độ: chặn 0 · nặng 4 · nhẹ 3
>
> _Cùng bộ phát hiện với `critique-acme-shop-all-level3.md`, nhưng kể ở mức 1 (`--warm`) để bạn thấy sự khác biệt: vẫn
> đúng bằng chứng đó, vẫn đúng cách sửa đó, chỉ là giọng nhẹ nhàng hơn. Phần nền tảng không hề đổi giữa các mức, chỉ có
> tông giọng đổi._

## Top 3 nên ưu tiên

1. **[nặng][product · market] PRD-MOBILE:5**. Di động đang là mục tiêu của năm thứ hai (`BRD-G5`), đó là một hướng
   tốt. Để đội phát triển vững tin hơn, PRD và story nên nói thêm nhu cầu trên di động khác gì so với trên web. Chỗ này đáng lưu tâm: trường `competitive_parity` đang ghi `behind` cả Shopify lẫn Etsy nhưng ưu tiên lại để
   `moscow: could`, nên dễ thành làm cho có. Có thể thử: thêm một nhu cầu chỉ di động mới đáp ứng được (ví dụ đẩy thông báo
   khi cửa hàng ra mẫu mới), hoặc ghi rõ rằng đây là bước chạy theo cho bằng đối thủ để mọi người cùng đặt đúng kỳ vọng.
2. **[nặng][tech] PRD-MOBILE-E1-S1:18**. Story này (`size: L`) đang ôm cả việc xem hàng lẫn mua hàng. Chỗ này đáng lưu tâm: story lớn thì khó ước lượng, và việc nhúng luồng thanh toán web vào vỏ ứng dụng nên được nói rõ ngay từ
   đầu. Có thể thử: tách thành hai story và thêm một tiêu chí xác nhận luồng thanh toán web chạy được trong vỏ ứng dụng.
3. **[nặng][product] PRD-ANALYTICS:5**. Phần phân tích số liệu đang đi trước fan-CRM, trong khi theo lộ trình thì
   fan-CRM mới là mũi nhọn. Chỗ này đáng lưu tâm: đội còn nhỏ, nên thứ tự ưu tiên rất đáng cân nhắc. Có thể thử: ghi
   một câu lý do vì sao phân tích số liệu đi trước, hoặc cân nhắc đảo lại ưu tiên.

## Theo từng lăng kính

### Product
- **[nặng] PRD-MOBILE:5**. (xem Top 3 mục 1) Bổ sung nhu cầu di động sẽ giúp story thuyết phục hơn nhiều.
- **[nặng] PRD-ANALYTICS:5**. (xem Top 3 mục 3) Một câu biện minh cho thứ tự ưu tiên là đủ.
- **[nhẹ] PRD-ANALYTICS-E1-S1:17**. Tiêu chí "totals reconcile with payout statements" rất tốt, nên dùng làm mẫu cho
  các story khác.

### Tech
- **[nặng] PRD-MOBILE-E1-S1:18**. (xem Top 3 mục 2) Nên tách story và làm rõ phụ thuộc vào luồng thanh toán web.
- **[nhẹ] PRD-ANALYTICS:15**. Biện pháp giảm thiểu bằng bản sao đọc đang nằm trong phần mô tả; thêm một tiêu chí phi
  chức năng sẽ giúp đội phát triển chắc tay hơn.

### Market
- **[nặng] PRD-MOBILE:28**. Đang `behind` hai đối thủ mà lại để `could`; nên chốt một hướng, hoặc nâng ưu tiên, hoặc gỡ
  ra khỏi mục tiêu.

### Craft
- **[nhẹ] PRD-MOBILE-E1-S1:29**. Chữ "fast" trong câu nói về giá trị nên thay bằng một con số, ví dụ p95 mở ứng dụng
  dưới 1 giây.
- **[nhẹ] PRD-ANALYTICS-E1-S1:21**. Cụm "which periods worked" có thể nói rõ hơn thành "so sánh doanh thu giữa các kỳ".

## Lỗi lặp lại từ lần trước

- Không có.

## Đáng ghi thành quyết định (DEC)

- **Mức ưu tiên của PRD-MOBILE so với mục tiêu `BRD-G5`.** Nếu người làm sản phẩm chốt được hướng, có thể ghi lại thành
  một bản ghi `DEC-<số>` để lần sau khỏi phải bàn lại.
