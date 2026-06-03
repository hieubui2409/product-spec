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
level: 6
---
# Critique: all  ·  level 6  ·  lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 4

Bạn viết cái spec này kiểu gì mà cả sản phẩm xây quanh một lời hứa "kết nối thật" nhưng không có lấy một chỗ nào đo được nó? Đọc xong thấy rõ là viết cho xong, dán nhãn "core-value" lên rồi đi ngủ, để mặc cho đội build tự đoán. Bạn tuyên bố ghét match ảo của Tinder, rồi quay lại đo match, thưởng match, bán match. Bạn lười tới mức copy đúng cái app mình chê rồi gọi nó là khác biệt.

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** — North-star của chính bạn là "cặp đôi duy trì nhắn tin >= 7 ngày" (PRODUCT.md:15, VISION:51), nhưng cả Success Metrics của BRD (BRD:62-65) lẫn mọi story đều chỉ đo MAU/monthly, weekly-match-rate, premium-conversion, ARPU — đúng mấy con số match/quy mô mà VISION:45-52 nói thẳng là muốn thoát. Bạn dựng cả lý do tồn tại của sản phẩm rồi quên gắn đồng hồ đo nó. Sản phẩm có thể chạm 100k MAU, 20% match/tuần và vẫn chết sạch ở lý do tồn tại: không cặp nào trò chuyện thật, và đội build sẽ tối ưu match-count y hệt Tinder vì đó là thứ duy nhất bạn cho họ đo. Riskiest assumption của cả sản phẩm không có lấy một cây kim để chọc thử. Thêm metric north-star tường minh vào BRD (vd `sustained-7day-conversation-rate`), gắn làm metric chính cho PRD-CHAT và ít nhất PRD-CHAT-E1-S1; xem lại BRD-G2 để hoặc thay weekly-match-rate, hoặc nói rõ match-rate chỉ là leading indicator phụ thuộc north-star. *(DEC-worthy)*

2. **[blocker][market] BRD:22** — BRD-G3 hứa hoà vốn vận hành năm 2 từ premium nhưng cả spec không có lấy một con số: không giá gói, không tỉ lệ chuyển đổi, không ARPU, không chi phí vận hành. Bạn đặt một mục tiêu tài chính rồi để trống toàn bộ phép tính đằng sau nó. Thị trường hẹn hò VN khoảng 6.44M USD/năm (Statista 2025). Tinder mất nhiều năm mới đạt ~10.7% conversion. Tân binh 100k MAU × 3-5% × giá ~3-5 USD/tháng ra cỡ 15-25k USD MRR — nếu chi phí vượt mức đó, BRD-G3 vỡ và spec không có một cơ chế cảnh báo sớm nào. Thêm bảng unit-economics tối thiểu vào BRD (giá VND/tháng, conversion mục tiêu %, ARPU mục tiêu, ước tính chi phí vận hành năm 2). Từ đó PRD-PREMIUM mới định nghĩa nổi "hoà vốn" nghĩa là gì. *(DEC-worthy)*

3. **[blocker][tech] PRD-CHAT-E1-S3:18 + PRD-CHAT-E1-S4:18** — Hàng loạt AC dùng kết quả không đo được: "trải nghiệm phải mượt mà", "hiển thị nhanh không giật lag" (S3:18-19), "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn" (S4:18-19). Không ngưỡng số, không thiết bị tham chiếu, không tiêu chí vượt/không vượt. Đây là viết AC cho có, không phải để ai kiểm. Không AC nào chuyển nổi thành test case thông/không thông. Kỹ sư không có điều kiện dừng, QA không có ngưỡng từ chối, story để ngỏ vô hạn hoặc bị tick done tuỳ tiện. Thay bằng ngưỡng đo được: S3 — "cuộn/gõ trên Android tầm trung (RAM 3GB), frame rate >= 55 fps, không jank frame > 16ms trong 100 frame liên tiếp"; "mở hội thoại 50 tin, tương tác được trong 1,5s ở p95". S4 — liệt kê cơ chế cụ thể: cảnh báo link ngoài trước khi mở, quét CSAM trước khi lưu ảnh với mã lỗi rõ ràng.

## Theo lăng kính

### Product

- **[blocker] BRD:62** — Xem Top 3 #1. North-star không được đo bởi bất kỳ metric BRD hay story nào; differentiator duy nhất so với Tinder/Bumble không thể chứng minh, không thể tối ưu. *(DEC-worthy)*
- **[major] PRD-MATCH-E1-S1:30** — Story đáy phễu lõi (must/core-value) có "so that" dừng ở "tạo match với người tôi quan tâm", 4 AC kết ở sự kiện tạo match + thông báo, metric chỉ weekly-match-rate. Lõi đo và thưởng cho match ảo mà VISION:45-52 tuyên bố chống; mọi quyết định hạ nguồn sẽ kéo về số match, không phải kết nối. Sửa "so that", thêm AC nối match sang luồng mở hội thoại PRD-CHAT, ghi tín hiệu match-to-first-message, đổi metric sang chỉ số kết nối duy trì.
- **[major] PRD-CHAT-E1-S4:18** — "Nhắn tin an toàn tuyệt đối": "so that" vòng tròn (dòng 28), 2 AC không kiểm chứng được ("tuyệt đối", "hoàn toàn"), phạm vi an toàn trùng PRD-SAFETY. AC không done được, nhân đôi phạm vi với PRD-SAFETY phá vỡ nguyên tắc một nhà một sự thật, đẻ ra yêu cầu mâu thuẫn giữa hai PRD. Xoá S4 dồn về PRD-SAFETY, hoặc thu hẹp thành job cụ thể (chặn/báo cáo người trong hội thoại) với AC đếm được. *(DEC-worthy)*
- **[major] PRD-PREMIUM:37** — Động cơ doanh thu lõi (BRD-G3) xây trên đúng cơ chế match-count bạn chê: "xem ai đã thích mình", boost hồ sơ, thích không giới hạn (37-38), PRD tự nhận là me-too sau Tinder. Premium bán đúng cái pain VISION:22-28 nói là lý do người Việt chán app phương Tây. Nếu pain thật thì user không trả tiền cho thứ họ ghét; nếu họ trả thì giả định lõi của vision sai. Spec không giải mâu thuẫn này. Định nghĩa ít nhất một tính năng premium phục vụ trực tiếp kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng hiển thị), ghi rõ trong Overview cách premium tránh tái lập match-vanity; không thì nêu thẳng là rủi ro giả định lõi. *(DEC-worthy)*
- **[minor] PRD-EVENTS-E1-S3:18** — Một hệ thống bán vé concert toàn quốc cỡ L nhét trong app hẹn hò, đã tự gắn nhãn out/could/later. Dù gắn nhãn out, một mảng bán vé cỡ L với AC đầy đủ vẫn ngốn chu kỳ review của PO, làm loãng tín hiệu trọng tâm, mời gọi đầu tư sớm vào lĩnh vực không đo north-star. Giáng S3 xuống một dòng ý tưởng trong mục "tầm nhìn xa" của PRD-EVENTS; chỉ nâng lại thành story khi north-star đã có instrument, kèm DEC tường minh.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18 + PRD-CHAT-E1-S4:18** — Xem Top 3 #3. AC định tính không chuyển nổi thành test case.
- **[blocker] PRD-MATCH-E1-S2:21** — AC đặt kết quả A/B test thống kê (match cao hơn 20%, p<0.05) làm tiêu chí chấp nhận story. A/B test cần lưu lượng lớn, thường mất hàng tuần đạt p<0.05 — đây là metric sau triển khai, không phải điều kiện bàn giao sprint. Coi là AC cứng thì story treo vô hạn; bỏ qua thì AC thành cam kết trống. Tách ra: (1) story kỹ thuật giữ AC lọc tiêu chí cứng + tỉ lệ hồ sơ active + thời gian tải; (2) story đo lường riêng với AC "dashboard A/B test có dữ liệu thực, kết quả đọc được", không phải p<0.05.
- **[major] PRD-MATCH-E1-S2:22** — AC yêu cầu tính năng "Vì sao gợi ý người này?" nhưng PRD-AIREC:77 liệt kê tường minh tính năng này vào *Won't this round*. MATCH (core-value/must/now) xung đột trực tiếp với AIREC (in/could/later) trên cùng tính năng, không có depends_on. Kỹ sư MATCH phải xây lớp giải thích mà AIREC — nơi nắm logic gợi ý — không bao giờ xây cycle này. Story hoặc bị block hoặc tự tái triển khai logic, đẻ hai code path. Bỏ AC dòng 22 khỏi MATCH; nếu cần thì chuyển thành story riêng trong PRD-AIREC (could/later) đúng với quyết định Won't; thêm depends_on:[PRD-AIREC] nếu AC nào phụ thuộc ranking của AIREC. *(DEC-worthy: mâu thuẫn với artifact đã ghi Won't)*
- **[major] PRD-PREMIUM-E1-S1:20** — AC "giao dịch hoàn tất -> mở khoá quyền trong 5s" giả định một payment flow đã tồn tại, nhưng PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào *Won't this round*, không có depends_on nào. Không payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm được trong môi trường tích hợp thực; test phải mock toàn bộ payment, mất giá trị end-to-end. Thêm story/epic stub payment integration, đặt S1 depends_on; sửa AC thành "giả sử webhook xác nhận giao dịch thành công, khi nhận webhook thì cập nhật trạng thái gói + mở khoá trong 5s" để tách rõ payment khỏi entitlement layer.
- **[major] PRD-SAFETY-E1-S1:21** — AC yêu cầu xoá ảnh giấy tờ gốc trong 24h sau xác minh (gần GDPR retention) nhưng không có audit log, API check, hay retention policy nào để QA verify. Không cách nào test thụ động rằng ảnh đã thực sự bị xoá; nếu cron job lỗi không ai biết tới lúc breach. Tách 2 AC: (1) "truy vấn storage audit log sau 25h, record ảnh không còn tồn tại + deletion event ghi với timestamp"; (2) "admin truy vấn retention report, không ảnh nào created_at cũ hơn 25h còn trong storage"; thêm NFR: deletion SLA 24h enforce bởi scheduled job.
- **[minor] PRD-AIREC-E1-S1:21** — Ngưỡng "20 hồ sơ trong 2 giây trên thiết bị di động phổ thông tại VN" không định nghĩa "phổ thông" (CPU/RAM/OS) và không có percentile; story còn phụ thuộc mô hình ML chưa chọn. Không thiết bị tham chiếu thì môi trường test không cấu hình được, threshold không reproducible; khi model thật chọn xong, 2s có thể bất khả thi nếu không có caching. Định nghĩa hardware reference profile ở NFR (vd Snapdragon 680, RAM 4GB, 4G 20Mbps), gắn p95, sửa AC "scoring server-side + cache, 20 hồ sơ trong 2s ở p95"; nếu chưa chốt hardware thì chuyển thành spike/NFR kiểm sau khi chọn model.

### Market

- **[blocker] BRD:22** — Xem Top 3 #2. BRD-G3 hoà vốn năm 2 không có lấy một con số unit-economics. *(DEC-worthy)*
- **[major] BRD:26** — Danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan. App này đang tái định vị sang "kết nối châu Á có chiều sâu văn hoá" với tập user châu Á lớn hơn; TanTan Tribe ra mắt Singapore 12/2024, đang mở sang Malaysia, Thailand. Nếu Tantan đẩy vào VN, luận điểm "bản địa hoá" của spec bị xói mòn mà không có kịch bản phòng thủ. Thêm Tantan (cân nhắc Facebook Dating) vào `competitors:` với threat level rõ ràng; cập nhật `competitive_parity` trong PRD-MATCH và PRD-SAFETY.
- **[major] PRD-MATCH:22** — Cơ chế lõi (khám phá/quẹt/match) được đánh `parity` với Tinder, `behind` với Bumble — đây là toàn bộ trải nghiệm năm 1 (AI + premium đều `later`). Khác biệt "đo bằng kết nối thật" của VISION không thể hiện bằng bất kỳ tính năng must/should nào trong `now/next`; nó chỉ là cam kết đo lường nội bộ. User không chọn app vì north-star nội bộ, họ chọn vì trải nghiệm khác biệt cảm nhận ngay. Nếu màn quẹt giống Tinder (parity), premium/AI chưa có, không có lý do hành vi nào để rời Tinder (đang top grossing VN theo Similarweb 3/2026) với network effect lớn hơn. Xác định ít nhất một tính năng must/should trong `now/next` thể hiện "kết nối thật" mà user cảm nhận ngay (icebreaker tự động sau match, giới hạn số match đồng thời, badge "đang nhắn tin"). Không có hook trải nghiệm, tuyên bố định vị chỉ là marketing copy.

### Craft

- **[major] PRD-MATCH-E1-S1:20** — AC "tạo match và hiển thị thông báo match cho cả hai trong 5 giây" dùng "match" làm danh từ mơ hồ, không rõ loại thông báo, không rõ "cả hai cùng thích" xảy ra tức thì hay trễ, mốc 5s tính từ đâu. Hành vi hệ thống không rõ: push gửi khi nào, 5s tính từ ai. Sửa thành: "Khi cả hai phía cùng thích, hệ thống tạo match và gửi push cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận."
- **[major] PRD-MATCH-E1-S1:19** — AC "cả hai phản hồi dưới 300ms": "phản hồi" mơ hồ (API? UI? cảm nhận user?), "ghi nhận" trừu tượng. QA/dev không biết đo từ điểm nào, tiêu chuẩn không kiểm chứng khách quan. Sửa thành: "Quẹt phải: ghi nhận lượt thích (lưu DB); quẹt trái: ghi nhận bỏ qua (lưu DB). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc gắn rõ tới phản hồi UI nếu muốn đo phía user).
- **[major] VISION:24, PRD-MATCH:31** — VISION:24 nêu vấn đề "hàng triệu match ảo không bao giờ dẫn tới cuộc trò chuyện thật", còn PRD-MATCH:31 có AC chỉ tạo match mà không cơ chế nào dẫn tới trò chuyện thật. Mâu thuẫn này khiến story lõi chính là thứ đẻ ra cùng vấn đề mà vision tuyên bố giải; match sẽ bị lãng quên đúng như VISION mô tả. Thêm AC "khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu hội thoại"; hoặc ghi rõ scope ở epic: "story này tạo match hai chiều; PRD-CHAT xử lý việc biến match thành kết nối thật". *(Chồng lấn với product BRD:62 / PRD-MATCH-E1-S1:30 — cùng lỗ hổng "match không nối tới kết nối", craft soi ở tầng câu chữ, product ở tầng metric.)*
- **[minor] PRD-MATCH-E1-S1:29** — Khuôn User Story dùng nhãn tiếng Anh kép ("As a | I want | so that") rồi bản dịch tiếng Việt ("Với vai trò | Tôi muốn | để"), gây nhãn tiêu đề kép lệch với phần AC chỉ tiếng Việt bên dưới. PO không kỹ thuật bị phân tán, không rõ nên đọc bản nào. Bỏ nhãn tiếng Anh dòng 28, chỉ giữ cấu trúc tiếng Việt cho cân với "Tiêu chí chấp nhận".
- **[minor] PRD-MATCH-E1-S1:18** — Cụm "hồ sơ gợi ý" dùng "gợi ý" làm tính từ, lệch với cách dùng "hồ sơ được gợi ý" ở VISION:43. Người đọc dễ hiểu nhầm "gợi ý" là một loại hồ sơ đặc biệt, tạo bất nhất từ vựng. Sửa thành: "Khi mở màn khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

Không có (không có prior report).

## Đáng ghi thành quyết định (DEC-worthy)

- **BRD:62** — Thêm north-star metric đo lường kết nối duy trì, hoặc PO chốt tường minh rằng match-rate là metric thành công chính (mâu thuẫn trực tiếp với VISION:45-52, cần ruling).
- **BRD:22** — PO chốt bộ unit-economics (giá / conversion / ARPU / chi phí) định nghĩa "hoà vốn năm 2" của BRD-G3.
- **PRD-CHAT-E1-S4:18** — Quyết định scope an toàn nằm ở đâu: xoá S4 dồn về PRD-SAFETY, hay giữ với phạm vi thu hẹp (tránh nhân đôi phạm vi giữa hai PRD).
- **PRD-PREMIUM:37** — PO chốt premium phục vụ kết nối duy trì hay chấp nhận mô hình match-vanity me-too (mâu thuẫn với VISION:22-28).
- **PRD-MATCH-E1-S2:22** — Tính năng "giải thích gợi ý" mâu thuẫn với *Won't this round* đã ghi tại PRD-AIREC:77. Cần ruling Keep/Change/Hybrid trước khi build.
