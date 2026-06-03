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
level: 5
---
# Critique: all · level 5 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 12 · minor 4

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** — North-star của sản phẩm ("số cặp đôi duy trì nhắn tin >= 7 ngày", PRODUCT.md:15 / VISION:51) không có mặt trong Success Metrics của BRD; cả bộ chỉ số chỉ là mau-monthly, weekly-match-rate, premium-conversion-rate, arpu, và mọi story đều bám match-count. Chết ở chỗ: sản phẩm có thể đạt 100k MAU, 20% match/tuần và vẫn thất bại ở đúng lý do nó tồn tại vì không một cặp nào trò chuyện thật. Differentiator duy nhất so với Tinder/Bumble không được đo, nên không chứng minh được, không tối ưu được, và đội build sẽ tối ưu match-count y hệt đối thủ. Riskiest assumption của cả sản phẩm không có instrument nào để kiểm chứng. Sửa cho đàng hoàng: thêm metric north-star tường minh vào BRD Success Metrics (vd sustained-7day-conversation-rate), gắn nó làm metric chính cho PRD-CHAT và ít nhất PRD-CHAT-E1-S1; xem lại BRD-G2 để thay weekly-match-rate bằng chỉ số kết nối duy trì, hoặc nói rõ match-rate chỉ là leading indicator. **[DEC-worthy]**

2. **[blocker][market] BRD:22** — BRD-G3 đặt mục tiêu hoà vốn vận hành năm 2 từ doanh thu premium nhưng cả spec không có một con số nào: không giá gói, không tỉ lệ chuyển đổi, không ARPU, không ước tính chi phí vận hành. Chết ở chỗ: thị trường hẹn hò online Việt Nam chỉ khoảng 6,44M USD/năm 2025 (Statista); Tinder mất nhiều năm mới đạt chuyển đổi xấp xỉ 10,7%. Một tân binh 100k MAU với chuyển đổi thực tế 3-5% ở giá Vietnam-tier (~3-5 USD/tháng) chỉ tạo ra khoảng 15-25k USD MRR. Chi phí thực mà cao hơn thì BRD-G3 vỡ mà không có cơ chế cảnh báo sớm nào trong spec. Sửa cho đàng hoàng: thêm vào BRD một bảng unit-economics tối thiểu (giá gói VND/tháng, tỉ lệ chuyển đổi mục tiêu %, ARPU mục tiêu, ước tính chi phí vận hành năm 2); từ đó PRD-PREMIUM mới định nghĩa được "hoà vốn" là gì. **[DEC-worthy]**

3. **[blocker][tech] PRD-CHAT-E1-S3:18 (+ PRD-CHAT-E1-S4:18)** — Cả hai AC dùng kết quả không đo được: "trải nghiệm phải mượt mà", "hiển thị nhanh không giật lag" (S3:18-19); "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn" (S4:18-19). Không ngưỡng số, không thiết bị tham chiếu, không tỉ lệ thất bại cho phép. Chết ở chỗ: không AC nào chuyển được thành test case thông/không thông. Kỹ sư không có điều kiện dừng để đóng sprint, QA không có ngưỡng để từ chối, story trượt vô hạn hoặc bị tick done tuỳ tiện. Sửa cho đàng hoàng: thay bằng ngưỡng đo được. S3: "cuộn/gõ phím trên Android tầm trung (RAM 3GB), frame rate >= 55fps, không jank frame > 16ms trong chuỗi 100 frame"; "mở cuộc trò chuyện 50 tin, tương tác được trong 1,5s ở p95". S4: liệt kê cơ chế bảo vệ cụ thể (cảnh báo link ngoài trước khi mở; quét CSAM trước khi lưu ảnh, từ chối với mã lỗi rõ ràng).

## Theo lăng kính

### Product

- **[blocker] BRD:62** — (xem Top 3 #1) north-star không có trong Success Metrics, mọi story bám match-count. **[DEC-worthy]**
- **[major] PRD-MATCH-E1-S1:30** — Story must/core-value của lõi nhưng "so that" dừng ở "tạo match với người tôi quan tâm", 4 AC chỉ kết thúc ở sự kiện tạo match + thông báo, metric gắn weekly-match-rate. Chết ở chỗ: story đáy phễu của lõi tối ưu đúng cho "match ảo" mà VISION:45-52 tuyên bố chống; mọi quyết định thiết kế hạ nguồn sẽ kéo về số match, chính là Tinder mà spec nói không muốn xây. Sửa cho đàng hoàng: sửa "so that", thêm AC nối tới hành trình kết nối (sau match dẫn thẳng vào luồng PRD-CHAT, ghi tín hiệu match-to-first-message), đổi metric sang chỉ số kết nối duy trì.
- **[major] PRD-CHAT-E1-S4:18** — "so that" vòng tròn (an toàn để yên tâm) cộng 2 AC "an toàn tuyệt đối"/"bảo vệ hoàn toàn", lại trùng phạm vi với PRD-SAFETY. Chết ở chỗ: AC "tuyệt đối"/"hoàn toàn" không bao giờ xong; nhân đôi phạm vi an toàn với PRD-SAFETY phá vỡ nguyên tắc một-nhà-chứa-một-sự-thật, dẫn tới yêu cầu mâu thuẫn giữa hai PRD. Sửa cho đàng hoàng: xoá S4 và dồn an toàn về PRD-SAFETY, hoặc thu hẹp S4 thành một việc cụ thể (chặn/báo cáo người trong cuộc trò chuyện) với AC đếm được. **[DEC-worthy]**
- **[major] PRD-PREMIUM:37** — Doanh thu lõi (BRD-G3) bán bằng đúng cơ chế match-count mà sản phẩm tuyên bố chống: "xem ai đã thích mình", boost hồ sơ, thích không giới hạn; PRD tự nhận là me-too sau Tinder. Chết ở chỗ: động cơ doanh thu duy nhất dẫn tới hoà vốn lại xây trên incentive quẹt-vô-tận, đúng pain mà VISION:22-28 nói người Việt đã chán. Người dùng không trả tiền cho cái họ ghét; còn nếu họ trả thì giả định lõi của vision sai. Spec không giải quyết mâu thuẫn này. Sửa cho đàng hoàng: định nghĩa ít nhất một gói premium phục vụ trực tiếp kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng hiển thị), ghi rõ trong PRD-PREMIUM Overview; nếu không thể, nêu thẳng đây là rủi ro giả định lõi. **[DEC-worthy]**
- **[minor] PRD-EVENTS-E1-S3:18** — Hệ thống bán vé concert toàn quốc trong app hẹn hò (5 AC, size L), spec đã tự ghi nhận gold-plating và đặt out/could/later. Chết ở chỗ: dù gắn nhãn out, một mảng kinh doanh cỡ L với AC đầy đủ vẫn tiêu thụ chu kỳ review của PO, làm loãng tín hiệu trọng tâm, mời đầu tư sớm vào lĩnh vực không đo north-star. Tự nhận thức không khử được chi phí cơ hội. Sửa cho đàng hoàng: giáng S3 xuống một dòng ý tưởng trong mục "tầm nhìn xa" của PRD-EVENTS; chỉ nâng lại thành story khi north-star đã có instrument và chứng minh, kèm DEC tường minh.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18** — (xem Top 3 #3) AC không đo được trên S3 và S4.
- **[blocker] PRD-MATCH-E1-S2:21** — AC đặt kết quả A/B test (match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận story. Chết ở chỗ: A/B test cần lưu lượng lớn, thường nhiều tuần mới đạt p < 0.05, đây là chỉ số sau triển khai chứ không phải điều kiện bàn giao sprint. Coi đây là AC cứng thì story treo vô thời hạn chờ dữ liệu; bỏ qua thì AC thành cam kết trống. Sửa cho đàng hoàng: tách hai phần. (1) Story kỹ thuật giữ AC lọc tiêu chí cứng, tỉ lệ hồ sơ active, thời gian tải. (2) Story đo lường riêng với AC "dashboard A/B test có dữ liệu thực và đọc được", không phải p < 0.05.
- **[major] PRD-MATCH-E1-S2:22** — AC yêu cầu tính năng giải thích gợi ý ("Vì sao gợi ý người này?") nhưng PRD-AIREC:77 liệt kê tường minh tính năng này trong Won't this round. MATCH-S2 là core-value/must/now; AIREC là in/could/later, xung đột trực tiếp trên cùng tính năng, không depends_on. Chết ở chỗ: kỹ sư MATCH phải xây lớp giải thích nhưng AIREC, nơi nắm logic gợi ý, không xây trong cycle này; story bị block hoặc tự tái triển khai logic gợi ý và tạo hai code path song song. Sửa cho đàng hoàng: loại AC dòng 22 khỏi MATCH-S2; nếu cần, chuyển thành story trong PRD-AIREC (could/later) đúng quyết định Won't tại AIREC:77; thêm depends_on: [PRD-AIREC] nếu AC nào phụ thuộc ranking của AIREC. **[DEC-worthy]**
- **[major] PRD-PREMIUM-E1-S1:20** — AC "giao dịch hoàn tất, mở khoá quyền xem trong 5s" giả định luồng thanh toán đã tồn tại, nhưng PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào Won't this round; không depends_on nào liên kết. Chết ở chỗ: không payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm tra được end-to-end; test phải mock toàn bộ payment flow, và khi gateway được chọn sau thì viết lại AC từ đầu. Sửa cho đàng hoàng: thêm story/epic stub payment integration và đặt S1 depends_on nó; sửa AC thành "khi nhận webhook xác nhận thành công từ payment gateway, cập nhật trạng thái gói và mở khoá quyền xem trong 5s", tách rõ ranh giới payment và entitlement layer.
- **[major] PRD-SAFETY-E1-S1:21** — AC yêu cầu xoá ảnh giấy tờ gốc trong 24h sau xác minh và "không bao giờ hiển thị cho người khác" (gần tương đương GDPR retention) nhưng không có cơ chế verify: không audit log, không API check, không retention policy reference. Chết ở chỗ: không cách nào test thụ động rằng ảnh đã thực sự bị xoá sau 24h; có bug trong cron job thì không ai biết tới khi breach. Sửa cho đàng hoàng: tách hai AC. (1) "Truy vấn storage audit log sau 25h, record ảnh không còn trong bucket và deletion event được ghi với timestamp." (2) "Admin truy vấn retention report, không ảnh giấy tờ nào có created_at cũ hơn 25h còn trong storage." Thêm vào NFR PRD-SAFETY: deletion SLA 24h enforce bởi scheduled job.
- **[minor] PRD-AIREC-E1-S1:21** — Ngưỡng "20 hồ sơ đầu hiển thị trong 2s trên thiết bị di động phổ thông tại Việt Nam" không định nghĩa thiết bị (CPU/RAM/OS) và không percentile; story size L, could/later, phụ thuộc model ML chưa chọn. Chết ở chỗ: không thiết bị tham chiếu thì không cấu hình được môi trường test, threshold không reproducible; khi model thực được chọn, 2s có thể bất khả thi nếu không có caching layer. Sửa cho đàng hoàng: định nghĩa hardware reference profile trong NFR PRD-AIREC (vd Android tầm trung 2023+, Snapdragon 680, RAM 4GB, 4G 20Mbps), gắn p95, thêm điều kiện scoring server-side + cache; nếu chưa xác định được hardware trước khi chọn model, chuyển AC thành spike/NFR kiểm sau.

### Market (cite source urls where present)

- **[blocker] BRD:22** — (xem Top 3 #2) BRD-G3 hoà vốn năm 2 không có một con số unit-economics nào. Nguồn: Statista (quy mô thị trường ~6,44M USD/2025), tỉ lệ chuyển đổi Tinder ~10,7%. **[DEC-worthy]**
- **[major] BRD:26** — Danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan, app hẹn hò tập trung người dùng châu Á, ra mắt TanTan Tribe tại Singapore 12/2024, đang mở sang Malaysia/Thailand, chia sẻ đúng phân khúc châu Á mà spec coi là lợi thế. Chết ở chỗ: Tantan đang tái định vị sang "kết nối châu Á có chiều sâu văn hoá"; nếu Tantan Tribe đẩy vào Việt Nam với định vị tương tự và tập người dùng lớn hơn, luận điểm "bản địa hoá" của spec bị xói mòn mà không có kịch bản phòng thủ nào. Sửa cho đàng hoàng: thêm Tantan (và cân nhắc Facebook Dating) vào `competitors:` trong BRD với threat level rõ; cập nhật `competitive_parity` trong PRD-MATCH và PRD-SAFETY.
- **[major] PRD-MATCH:22** — Cơ chế lõi (khám phá, quẹt, tạo match hai chiều) là `parity` với Tinder, `behind` với Bumble; AI và premium đều later. Differentiator "kết nối thật" trong VISION không thể hiện bằng bất kỳ tính năng must/should nào trong now/next, chỉ là cam kết đo lường nội bộ. Chết ở chỗ: người dùng không chọn app vì north-star metric nội bộ; màn quẹt giống Tinder (parity), premium chưa có, AI chưa có, thì không có lý do hành vi để rời Tinder, nhất là khi Tinder đã top grossing Việt Nam (Similarweb, 3/2026) với network effect lớn hơn nhiều. Sửa cho đàng hoàng: xác định ít nhất một tính năng must/should trong now/next thể hiện được "kết nối thật" mà người dùng cảm nhận ngay (icebreaker tự động sau match, giới hạn số match đồng thời, hoặc badge "đang nhắn tin"). Không có hook trải nghiệm rõ ràng thì tuyên bố định vị chỉ là marketing copy.

### Craft

- **[major] PRD-MATCH-E1-S1:20** — AC "hệ thống tạo match và hiển thị thông báo match cho cả hai trong 5 giây" dùng "thông báo match" mơ hồ: không nói thông báo gì, không nói "cả hai cùng thích" xảy ra tức thì hay có trễ, mốc 5s tính từ đâu. Chết ở chỗ: hành vi hệ thống không rõ; A và B thích cùng lúc hay đã thích từ trước thì gửi thông báo khi nào, 5s tính từ ai. Sửa cho đàng hoàng: "Khi cả hai phía cùng thích, hệ thống tạo match và gửi thông báo push cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận."
- **[major] PRD-MATCH-E1-S1:19** — AC "quẹt phải ghi nhận thích; quẹt trái ghi nhận bỏ qua; cả hai phản hồi dưới 300ms": "phản hồi" không rõ là latency API, UI, hay cảm nhận; "ghi nhận" trừu tượng. Chết ở chỗ: QA và dev không biết đo "dưới 300ms" từ đâu tới đâu; tiêu chí không kiểm chứng được. Sửa cho đàng hoàng: "Quẹt phải: ghi nhận thích (lưu DB); quẹt trái: ghi nhận bỏ qua (lưu DB). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc "...hoàn thành và hiển thị phản hồi UI, hồ sơ tiếp theo lên, trong 300ms").
- **[major] VISION:24, PRD-MATCH:31** — "Hàng triệu match ảo không bao giờ dẫn tới cuộc trò chuyện thật" là problem statement ở VISION:24, nhưng AC PRD-MATCH:31 lại tạo match mà không có cơ chế nào dẫn tới trò chuyện thật. Chết ở chỗ: mâu thuẫn này khiến người đọc hoài nghi story có giải quyết vấn đề lõi hay đang tái tạo chính nó; north-star là cặp duy trì nhắn tin >= 7 ngày nhưng AC chỉ tạo match thì match đó sẽ bị lãng quên. Sửa cho đàng hoàng: thêm AC "khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu cuộc trò chuyện"; hoặc làm rõ scope ngay ở epic: "story này tạo match hai chiều; PRD-CHAT xử lý mở cuộc trò chuyện để biến match thành kết nối thật".
- **[minor] PRD-MATCH-E1-S1:29** — Khuôn User Story dùng nhãn cột tiếng Anh ("As a | I want | so that") rồi kèm bản tiếng Việt, tạo nhãn kép trên một dòng, lệch với phần Acceptance Criteria không có nhãn kép. Chết ở chỗ: PO không kỹ thuật bị phân tán bởi nhãn kép, không rõ đọc dòng tiếng Anh hay tiếng Việt; dòng 28 thành ngoại lệ duy nhất. Sửa cho đàng hoàng: bỏ nhãn tiếng Anh, dùng cấu trúc chỉ tiếng Việt ("Với vai trò / Tôi muốn / Để") cho cân với phần "Tiêu chí chấp nhận".
- **[minor] PRD-MATCH-E1-S1:18** — AC dùng "một chồng tối thiểu 10 hồ sơ gợi ý đã tải sẵn"; "gợi ý" ở đây là tính từ, trong khi toàn ancestry dùng "gợi ý" làm danh từ/động từ; "hồ sơ gợi ý" không tự nhiên trong tiếng Việt. Chết ở chỗ: dễ hiểu nhầm "gợi ý" là một loại hồ sơ đặc biệt thay vì "hồ sơ được hệ thống gợi ý"; lệch với cách dùng "hồ sơ được gợi ý" ở Vision:43. Sửa cho đàng hoàng: "Khi mở màn hình khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

- Không có (prior_reports rỗng).

## Đáng ghi thành quyết định (DEC-worthy)

- **BRD:62** — north-star không nằm trong Success Metrics, mọi story bám match-count: PO cần quyết chọn metric chính của sản phẩm (đụng tới định nghĩa thành công, có thể mâu thuẫn artifact đã approved). Ghi qua `--decision`.
- **BRD:22** — BRD-G3 hoà vốn năm 2 không có unit-economics: PO cần ghi nhận bảng giá/chuyển đổi/ARPU/chi phí làm ràng buộc.
- **PRD-PREMIUM:37** — mô hình doanh thu premium dựa trên cơ chế match-vanity mà vision phủ nhận: PO cần quyết giữ mô hình hiện tại hay tái định nghĩa premium quanh kết nối duy trì.
- **PRD-CHAT-E1-S4:18** — chồng lấn phạm vi an toàn với PRD-SAFETY: PO cần quyết một-nhà-chứa cho phạm vi "an toàn".
- **PRD-MATCH-E1-S2:22** — AC giải thích gợi ý mâu thuẫn trực tiếp với quyết định Won't this round tại PRD-AIREC:77: PO cần quyết giữ Won't hay nâng tính năng vào cycle (đụng artifact đã ấn định scope).
