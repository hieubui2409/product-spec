---
body_hash:
  PRD-AIREC: c258d8fd
  PRD-AIREC-E1: a2c8a061
  PRD-AIREC-E1-S1: 917f7bc9
  PRD-CHAT: 1cfc4161
  PRD-CHAT-E1: eb20b520
  PRD-CHAT-E1-S1: 8943eb03
  PRD-CHAT-E1-S2: 8c751c9f
  PRD-CHAT-E1-S3: 0e54d9bf
  PRD-CHAT-E1-S4: 628c183c
  PRD-EVENTS: 1733e335
  PRD-EVENTS-E1: e3aabc84
  PRD-EVENTS-E1-S1: 40cb8605
  PRD-EVENTS-E1-S2: a8852e0b
  PRD-EVENTS-E1-S3: 3b04bb23
  PRD-MATCH: 6ef8ad25
  PRD-MATCH-E1: 982249bd
  PRD-MATCH-E1-S1: 0ebcb5e1
  PRD-MATCH-E1-S2: cfc87b23
  PRD-PREMIUM: 26b9a8eb
  PRD-PREMIUM-E1: 019f8b55
  PRD-PREMIUM-E1-S1: e5f44b06
  PRD-PREMIUM-E1-S2: 82cd5b3b
  PRD-SAFETY: 1b1dc2cb
  PRD-SAFETY-E1: afee85f3
  PRD-SAFETY-E1-S1: 1c73ea43
  PRD-SAFETY-E1-S2: 169b4b79
  PRODUCT: 12f8eb81
  VISION: 44634e30
bundle_version: 2
critique_scope: all
lang: vi
lens_findings_hash: 196b1f155bf4b30f
level: 1
---
# Critique: all · level 1 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 4

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** — north-star của sản phẩm là "số cặp đôi duy trì nhắn tin qua lại >= 7 ngày" (PRODUCT.md:15, VISION:51), nhưng Success Metrics của BRD (BRD:62-65) chỉ liệt kê MAU/monthly, weekly-match-rate, premium-conversion-rate, arpu. Không metric nào đo cuộc trò chuyện duy trì 7 ngày, và không story nào mang chỉ số north-star. North-star không có metric thì không thể chứng minh, không thể tối ưu; đội build sẽ tối ưu cho match-count y hệt đối thủ, và sản phẩm có thể đạt "thành công" theo bộ chỉ số BRD (100k MAU, 20% match/tuần) trong khi thất bại ở lý do nó tồn tại. Differentiator duy nhất so với Tinder/Bumble không được đo. Thêm metric north-star tường minh vào BRD (ví dụ sustained-7day-conversation-rate), gắn nó làm metric chính cho PRD-CHAT và ít nhất PRD-CHAT-E1-S1; xem lại BRD-G2 để hoặc thay weekly-match-rate, hoặc nêu rõ match-rate chỉ là leading indicator.

2. **[blocker][tech] PRD-CHAT-E1-S3:18** — cả hai AC dùng kết quả không đo được: "trải nghiệm phải mượt mà" (dòng 18), "giao diện hiển thị nhanh và không giật lag" (dòng 19). PRD-CHAT-E1-S4 mắc cùng lỗi: "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn". Không ngưỡng số, không thiết bị tham chiếu, không tiêu chí vượt/không vượt. Không AC nào chuyển được thành test thông/không thông. Kỹ sư không có điều kiện dừng để đóng sprint, QA không có ngưỡng để từ chối, story để ngỏ vô thời hạn hoặc tick done theo cảm tính. Thay bằng ngưỡng đo được: S3: "Khi cuộn danh sách tin nhắn trên thiết bị Android tầm trung (RAM 3 GB), frame rate >= 55 fps, không jank frame nào vượt 16 ms trong 100 frame liên tiếp" / "Khi mở cuộc trò chuyện 50 tin nhắn, giao diện tương tác được trong 1,5 giây (p95)"; S4: liệt kê cơ chế cụ thể (cảnh báo link ngoài trước khi mở, quét CSAM trước khi lưu ảnh).

3. **[blocker][market] BRD:22** — BRD-G3 đặt mục tiêu hoà vốn vận hành năm 2 từ doanh thu premium, nhưng spec không có con số nào: không giá gói, không tỉ lệ chuyển đổi mục tiêu, không ARPU, không ước tính chi phí vận hành. PRD-PREMIUM đặt `horizon: later` và tự nhận là me-too sau Tinder. Thị trường hẹn hò trực tuyến Việt Nam khoảng 6,44 triệu USD năm 2025 (Statista); Tinder đạt chuyển đổi ~10,7% sau nhiều năm network effect. Một tân binh 100k MAU, chuyển đổi thực 3-5% ở giá Vietnam-tier (~3-5 USD/tháng) cho ra khoảng 15-25k USD MRR. Nếu chi phí cao hơn, BRD-G3 vỡ mà không có cơ chế cảnh báo sớm. Thêm vào BRD một bảng unit-economics tối thiểu (giá gói VND/tháng, tỉ lệ chuyển đổi mục tiêu %, ARPU mục tiêu, ước tính chi phí vận hành năm 2); từ đó PRD-PREMIUM mới định nghĩa được "hoà vốn" là gì.

## Theo lăng kính

### Product

- **[major] PRD-MATCH-E1-S1:30** — story must/core-value của lõi nhưng "so that" dừng ở "để tôi tạo match", 4 AC chỉ kết thúc ở tạo match + thông báo, metric gắn [weekly-match-rate]. Story đáy phễu tối ưu đúng cho "match ảo" mà VISION:45-52 chống lại; mọi thiết kế hạ nguồn sẽ kéo về số match, không phải kết nối thật. Sửa "so that", thêm AC nối tới hành trình kết nối (sau match dẫn thẳng vào luồng mở chat PRD-CHAT, ghi tín hiệu match→first-message), đổi metric sang chỉ số kết nối duy trì.

- **[major] PRD-CHAT-E1-S4:18** — "so that" vòng tròn (dòng 28: an toàn để yên tâm), 2 AC không kiểm chứng được ("an toàn tuyệt đối", "bảo vệ hoàn toàn"); phạm vi an toàn trùng PRD-SAFETY. AC không đo được thì không thể done, và nhân đôi phạm vi với PRD-SAFETY phá vỡ một-nhà-chứa-một-sự-thật. Xoá S4 dồn về PRD-SAFETY, hoặc thu hẹp S4 thành job cụ thể của chat (chặn/báo cáo) với AC đếm được.

- **[major] PRD-PREMIUM:37** — premium bán doanh thu lõi (BRD-G3) bằng đúng cơ chế match-count mà sản phẩm chống: "xem ai đã thích mình", boost hồ sơ, thích không giới hạn; PRD tự nhận là me-too. Động cơ doanh thu duy nhất hướng hoà vốn xây trên incentive quẹt-vô-tận, đúng pain VISION:22-28 nói người Việt chán. Nếu pain thật, người dùng không trả cho cái họ ghét; nếu họ trả, giả định vision sai. Định nghĩa ít nhất một tính năng premium phục vụ kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng hiển thị), ghi rõ cách premium tránh match-vanity; nếu không thể, nêu thẳng là rủi ro giả định lõi.

- **[minor] PRD-EVENTS-E1-S3:18** — đặc tả hệ thống tổ chức + bán vé concert toàn quốc trong app hẹn hò (5 AC, size L); đã tự nhãn gold-plating, scope out/could/later. Dù gắn out/could, mảng bán vé cỡ L vẫn tiêu chu kỳ review của PO, làm loãng tín hiệu trọng tâm, mời gọi đầu tư sớm vào lĩnh vực không đo north-star. Giáng S3 xuống một dòng ý tưởng trong "tầm nhìn xa" của PRD-EVENTS, chỉ nâng lại thành story khi north-star đã instrument, kèm một quyết định PO tường minh.

### Tech

- **[blocker] PRD-MATCH-E1-S2:21** — AC đặt kết quả A/B test thống kê (match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận; A/B test cần lưu lượng lớn, thường nhiều tuần để đạt p < 0.05, tức là đo sau triển khai, không phải điều kiện bàn giao. Story không đóng được cuối sprint vì kết quả chưa có; coi là điều kiện cứng thì treo vô thời hạn, bỏ qua thì AC thành cam kết trống. Tách hai phần: (1) story kỹ thuật giữ AC về lọc tiêu chí cứng/tỉ lệ hồ sơ active/thời gian tải; (2) story đo lường riêng với AC "dashboard A/B test có dữ liệu thực, đọc được kết quả", không phải p < 0.05.

- **[major] PRD-MATCH-E1-S2:22** — AC yêu cầu tính năng giải thích gợi ý ("Vì sao gợi ý người này?", >= 2 tiêu chí khớp), nhưng PRD-AIREC:77 liệt kê tường minh tính năng này trong Won't this round. MATCH-E1-S2 (core-value/must/now) xung đột trực tiếp với AIREC (in/could/later) trên cùng tính năng, không có depends_on. Kỹ sư phải xây lớp giải thích nhưng AIREC, nơi nắm logic gợi ý, không xây trong cycle này; story bị block hoặc tự tái triển khai logic, tạo hai code path. Loại AC dòng 22 khỏi MATCH-E1-S2; nếu cần, chuyển thành story riêng trong PRD-AIREC (could/later) đúng quyết định Won't; thêm depends_on: [PRD-AIREC] nếu AC nào phụ thuộc ranking của AIREC.

- **[major] PRD-PREMIUM-E1-S1:20** — AC kiểm tra "giao dịch hoàn tất thì mở khoá quyền xem trong 5 giây", giả định luồng thanh toán đã tồn tại, nhưng PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào Won't this round; không depends_on tới story thanh toán nào. Không có payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm tra được trong môi trường tích hợp thực; mock toàn bộ payment flow mất giá trị end-to-end. Thêm story/epic stub payment integration, đặt PREMIUM-E1-S1 phụ thuộc qua depends_on; sửa AC thành "Giả sử payment gateway trả webhook xác nhận thành công, khi webhook được nhận, hệ thống cập nhật trạng thái gói và mở khoá quyền xem trong 5 giây" để tách payment khỏi entitlement layer.

- **[major] PRD-SAFETY-E1-S1:21** — AC yêu cầu ảnh giấy tờ gốc bị xoá trong 24 giờ sau xác minh và "không bao giờ hiển thị cho người khác" (gần tương đương GDPR retention), nhưng không có cơ chế verify: không audit log, không API check, không retention policy reference. Không có cách test thụ động rằng ảnh đã xoá khỏi storage sau 24 giờ; nếu cron job lỗi, không ai biết cho đến khi breach. Tách hai AC: (1) "sau 25 giờ, truy vấn storage audit log thì record ảnh không còn, deletion event ghi trong audit trail với timestamp"; (2) "admin truy vấn retention report thì không ảnh giấy tờ nào created_at cũ hơn 25 giờ còn trong storage"; thêm NFR: deletion SLA 24h enforce bởi scheduled job.

- **[minor] PRD-AIREC-E1-S1:21** — AC đặt ngưỡng "20 hồ sơ đầu hiển thị trong 2 giây trên thiết bị di động phổ thông tại Việt Nam", nhưng không định nghĩa "thiết bị phổ thông" (CPU/RAM/OS) và không percentile; story size L, could/later, phụ thuộc mô hình ML chưa chọn. Không thiết bị tham chiếu thì không cấu hình được môi trường test, threshold không reproducible; khi model thực được chọn, 2 giây có thể không khả thi nếu thiếu caching. Định nghĩa hardware reference profile ở NFR (ví dụ Snapdragon 680, RAM 4 GB, 4G 20 Mbps), gắn p95, sửa AC để nêu rõ scoring server-side + cache; nếu chưa xác định được hardware, chuyển thành spike/NFR kiểm sau khi chọn model.

### Market

- **[major] BRD:26** — danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan, app hẹn hò tập trung người dùng châu Á đang mở sang Đông Nam Á (ra mắt TanTan Tribe tại Singapore tháng 12/2024, đang mở Malaysia/Thailand). Tantan đang tái định vị sang "kết nối châu Á có chiều sâu văn hoá"; nếu đẩy vào Việt Nam với định vị tương tự và tập người dùng châu Á lớn hơn, luận điểm "bản địa hoá" của spec bị xói mòn mà không có kịch bản phòng thủ. Thêm Tantan (cân nhắc Facebook Dating) vào `competitors:` của BRD với threat level rõ ràng; cập nhật `competitive_parity` trong PRD-MATCH và PRD-SAFETY.

- **[major] PRD-MATCH:22** — cơ chế lõi (khám phá, quẹt thích/bỏ qua, tạo match hai chiều) đánh giá `parity` với Tinder, `behind` với Bumble; AI gợi ý và premium đều `horizon: later`. Khác biệt "đo bằng kết nối thật" của VISION không thể hiện bằng tính năng must/should nào trong now/next, chỉ là cam kết đo lường nội bộ. Người dùng không chọn app vì north-star nội bộ mà vì trải nghiệm khác biệt ngay khi dùng; nếu màn quẹt giống Tinder, premium chưa có, AI chưa có, không có lý do hành vi để rời Tinder (top grossing Việt Nam, Similarweb tháng 3/2026). Xác định ít nhất một tính năng must/should trong now/next thể hiện "kết nối thật" cảm nhận được ngay (icebreaker tự động sau match, giới hạn số match đồng thời, badge "đang nhắn tin"); không có hook trải nghiệm rõ ràng thì tuyên bố định vị chỉ là marketing copy.

### Craft

- **[major] PRD-MATCH-E1-S1:20** — AC "hệ thống tạo match và hiển thị thông báo match cho cả hai trong vòng 5 giây" dùng "thông báo match" mơ hồ (thông báo gì), không nêu "cả hai phía cùng thích" xảy ra tức thì hay có độ trễ, mốc 5 giây tính từ ai. Hành vi hệ thống không rõ: gửi thông báo bao giờ, mốc thời gian tính từ nhìn của ai. Sửa thành: "Khi cả hai phía cùng thích nhau, hệ thống tạo match và gửi thông báo push cho cả hai người dùng trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận."

- **[major] PRD-MATCH-E1-S1:19** — AC "quẹt phải ghi nhận lượt thích; quẹt trái ghi nhận bỏ qua; cả hai phản hồi dưới 300ms" dùng "phản hồi" mơ hồ (latency API? hiển thị UI? cảm nhận người dùng?) và "ghi nhận" trừu tượng. QA/dev không rõ cách đo "phản hồi dưới 300ms", không thể kiểm chứng khách quan khi không có điểm đo rõ ràng. Sửa thành: "Quẹt phải: ghi nhận lượt thích (lưu vào database); quẹt trái: ghi nhận bỏ qua (lưu vào database). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc nêu rõ mốc UI cập nhật nếu muốn đo phía người dùng).

- **[major] VISION:24, PRD-MATCH:31** — "hàng triệu match ảo không bao giờ dẫn tới cuộc trò chuyện thật" là problem statement ở VISION:24, nhưng PRD-MATCH:31 có AC tạo thêm match mà không cơ chế nào đảm bảo dẫn tới trò chuyện thật. Mâu thuẫn này đặt câu hỏi liệu story giải quyết vấn đề lõi hay tái tạo chính nó; north-star (VISION:51) là duy trì nhắn tin >= 7 ngày nhưng AC chỉ yêu cầu tạo match. Thêm AC "Khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu trò chuyện", hoặc làm rõ scope ở epic ("story này: tạo match hai chiều; tiếp nối PRD-CHAT biến match thành kết nối thật").

- **[minor] PRD-MATCH-E1-S1:29** — khuôn User Story dùng tiêu đề cột tiếng Anh ("As a | I want | so that") rồi bản dịch tiếng Việt ("Với vai trò | Tôi muốn | để"), một dòng hai cặp nhãn song ngữ. PO không kỹ thuật bị phân tán bởi nhãn kép, không rõ đọc tiếng nào; các phần sau (AC) không có nhãn kép nên dòng 28 thành ngoại lệ. Bỏ nhãn tiếng Anh, chỉ dùng "Với vai trò / Tôi muốn / Để" cho cân bằng với phần "Tiêu chí chấp nhận".

- **[minor] PRD-MATCH-E1-S1:18** — AC "một chồng tối thiểu 10 hồ sơ gợi ý đã tải sẵn" dùng "gợi ý" như tính từ, trong khi toàn ancestry "gợi ý" thường là danh/động từ; "hồ sơ gợi ý" không tự nhiên với tiếng Việt. Người đọc có thể hiểu nhầm "gợi ý" là một loại hồ sơ đặc biệt thay vì "hồ sơ được gợi ý"; không nhất quán với cách Vision dùng "hồ sơ được gợi ý". Sửa thành: "Khi mở màn hình khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

Không có (không có prior_reports).

## Đáng ghi thành quyết định (DEC-worthy)

- **BRD:62 (north-star không có metric)** — quyết định instrument north-star (sustained-7day-conversation-rate) ràng buộc định vị và ưu tiên, PO nên ghi DEC; nó cũng định hình lại metric của BRD-G2.
- **PRD-MATCH-E1-S2:22 vs PRD-AIREC:77** — AC tạo xung đột trực tiếp với quyết định "Won't this round" đã ghi ở PRD-AIREC; cần một ruling PO (giữ Won't và bỏ AC, hay đổi horizon của AIREC).
- **PRD-PREMIUM:37 (premium dựng trên match-vanity)** — mâu thuẫn với định vị VISION; PO nên ghi quyết định premium phục vụ kết nối duy trì hay chấp nhận rủi ro giả định lõi.
- **PRD-EVENTS-E1-S3 (giáng cấp khỏi story)** — giáng một mảng kinh doanh scope:out khỏi story đầy đủ là quyết định phạm vi, nên ghi DEC so với north-star.
