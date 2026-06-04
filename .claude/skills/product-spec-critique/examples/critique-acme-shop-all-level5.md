# Critique: all  ·  mức 5 (no-mercy)  ·  lăng kính: product, tech, market, craft

> Đếm mức độ: chặn 1 · nặng 4 · nhẹ 2
>
> _Báo cáo mẫu chạy trên `product-spec/examples/acme-shop` ở **mức mặc định (5, no-mercy)**. Mức 5 là baseline:
> được phép châm chọc cả tài liệu lẫn người viết ở khía cạnh CÔNG VIỆC (không có lằn ranh nhân thân như 1–4), nhưng
> chưa bắt buộc roast như mức 6. Mỗi dòng vẫn đủ bằng chứng `mã:dòng`, vì-sao-chết, cách-sửa. Soạn tay để minh hoạ
> hợp đồng đầu ra; một lần chạy thật sẽ phản ánh spec sống + dữ liệu tra mạng._

## Top 3 sửa ngay

1. **[chặn][product · market] PRD-MOBILE:13.** Di động là mục tiêu năm thứ hai (`BRD-G5`, brd.md:32) nhưng PRD-MOBILE để `moscow: could` (PRD-MOBILE:13), `competitive_parity` ghi `behind` cả Shopify lẫn Etsy, và metric chỉ là `mobile-mau` (PRD-MOBILE:15) — số lượt mở app, không phải doanh thu hay repeat-purchase. Tức là bạn đặt một mục tiêu năm-2 vào ngăn "làm cũng được", rồi đo nó bằng vanity metric. Vì sao chết: một mục tiêu có deadline mà ưu tiên `could` và đo bằng MAU sẽ không bao giờ được làm tới nơi — đội sẽ ship một cái vỏ app cho có, thua đối thủ ở đúng thứ họ mạnh, và `BRD-G5` thành lời hứa suông. Sửa: hoặc nâng `moscow` cho khớp với một mục tiêu BRD năm-2 và đổi metric sang GMV-trên-mobile / repeat-purchase, hoặc thú thật rằng mobile chưa phải ưu tiên và gỡ deadline năm-2 khỏi `BRD-G5`. _(DEC-worthy: chỉnh ưu tiên/metric của một mục tiêu BRD.)_

2. **[nặng][tech] PRD-MOBILE-E1-S1:18.** Story `size: L` gộp cả xem hàng lẫn mua hàng vào hai tiêu chí nghiệm thu và dựa trên "tái dùng luồng thanh toán web nhúng trong vỏ app" — một phụ thuộc bị giấu, `depends_on` để trống. Vì sao chết: không đạt INVEST (không đủ nhỏ, không độc lập), và chuyện luồng web có nhúng nổi vào WebView/app shell hay không là rủi ro chưa ai xác nhận; phát hiện giữa sprint là vỡ cả story. Sửa: tách thành hai story (xem hàng / mua hàng), thêm một tiêu chí kiểm chứng luồng thanh toán hiển thị + hoàn tất được trong vỏ app, và khai `depends_on` cho dịch vụ thanh toán.

3. **[nặng][product] PRD-ANALYTICS:13.** Phân tích số liệu để `moscow: should`, `horizon: next` (PRD-ANALYTICS:13-14), được kéo lên làm sớm trong khi lộ trình nói fan-CRM mới là mũi nhọn khó sao chép. Vì sao chết: dồn sức đội nhỏ vào một dashboard ai cũng có (`dashboard-dau` là metric — lại đo lượt xem, không đo quyết định kinh doanh), trong khi thứ tạo moat thì chờ. Sửa: nói rõ vì sao analytics phải đi trước fan-CRM, hoặc đảo thứ tự ưu tiên; đổi metric sang một hành vi có giá trị (số quyết định/điều chỉnh giá dựa trên dashboard), không phải DAU.

## Theo từng lăng kính

### Product

- **[nặng] BRD-G5:32.** Mục tiêu "Launch native mobile shopping by year 2" đo bằng `mobile-mau`. Một mục tiêu ra-mắt đo bằng số người mở app là cái bẫy vanity quen thuộc: ra mắt xong, MAU nhích lên nhờ thông báo đẩy, và không ai biết mobile có thực sự bán được hàng không. Vì sao chết: metric không nối với GMV hay repeat-purchase (BRD-G2/G3), nên `BRD-G5` "đạt" mà chẳng chứng minh được giá trị kinh doanh. Sửa: thêm một metric mobile gắn doanh thu (GMV-mobile hoặc tỉ lệ repeat-purchase trên mobile) làm thước đo chính.

- **[nhẹ] PRD-ANALYTICS:4.** PRD-ANALYTICS phục vụ cả `BRD-G3` (GMV) lẫn `BRD-G4` (payout latency) (PRD-ANALYTICS:4) nhưng bản thân chỉ là dashboard quan sát — nó không *làm* GMV tăng hay payout nhanh hơn, chỉ hiển thị chúng. Vì sao chết: dễ tự huyễn rằng "đã phục vụ 2 mục tiêu" trong khi chưa có story nào tác động lên hai con số đó. Sửa: hoặc tách rõ analytics là leading-indicator (không phải đòn bẩy), hoặc thêm story hành động (cảnh báo khi payout > 3 ngày) để nó thật sự đẩy `BRD-G4`.

### Tech

- **[nặng] PRD-MOBILE-E1-S1:18.** (xem Top 3 #2) — story L gộp 2 việc + phụ thuộc thanh toán bị giấu, không đạt INVEST.

### Market

- **[nặng] PRD-MOBILE:28.** `competitive_parity: behind` cả Shopify và Etsy trên mobile (PRD-MOBILE:28-29), nhưng PRD không nêu một lý do nào để một boutique brand chọn app của Acme thay vì mở Shopify trên điện thoại. Vì sao chết: vào sau, thua tính năng, không khác biệt — đó là định nghĩa của me-too; ngân sách mobile sẽ đốt vào việc đuổi cho bằng thay vì tạo lý do chuyển đổi. Sửa: nêu một nhu cầu chỉ-Acme-mới-đáp-ứng (đẩy thông báo khi brand yêu thích ra mẫu mới, mua nhanh lúc di chuyển cho `shopper`), rate `ahead` ở đúng chỗ đó, hoặc chấp nhận `behind` một cách tường minh và để moat ở fan-CRM.

### Craft

- **[nhẹ] PRD-MOBILE:37.** Lý do tồn tại của PRD-MOBILE (PRD-MOBILE:37-38) chỉ nói app cho "browse and buy faster" + push notification — đúng những gì mobile web cũng làm được, không một câu nào tách bạch nhu cầu native khác gì web. Vì sao chết: một PRD không phát biểu được "vì sao phải là native" sẽ khiến mọi story bên dưới trôi theo quán tính, không ai bác được vì chẳng có tiêu chí. Sửa: viết một câu định vị nhu cầu-native cụ thể (offline, home-screen re-engagement, drop push) ở đầu PRD để mọi story phải bám vào.
