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
level: 8
register:
  dialect: bac
  gender: m
  profanity: strong
---
# Critique: all · level 8 · lăng kính: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 4

## Top 3: gõ lại ngay

1. **[blocker][product] BRD:62** — Mày dựng cả sản phẩm trên north-star "cặp đôi nhắn tin qua lại >= 7 ngày" (PRODUCT.md:15, VISION:51), rồi bộ Success Metrics ở BRD:62-65 lại không có một chỉ số nào đo cái đó: chỉ mau-monthly, weekly-match-rate, premium-conversion-rate, arpu. Lý do tồn tại của sản phẩm không có cái đồng hồ nào đo. Nát bét vì: mày đạt 100k MAU, 20% match/tuần là "thành công" trên giấy mà không một cặp nào trò chuyện thật. Cái differentiator duy nhất so với Tinder/Bumble không đo được thì không chứng minh được, không tối ưu được, đội build sẽ tối ưu match-count y hệt đối thủ. Riskiest assumption của cả sản phẩm chạy mù. Gõ lại ngay: thêm metric north-star tường minh vào BRD (sustained-7day-conversation-rate), gắn làm metric chính cho PRD-CHAT và PRD-CHAT-E1-S1; xem lại BRD-G2 để thay weekly-match-rate hoặc nói rõ nó chỉ là leading indicator. `DEC-worthy`

2. **[blocker][tech] PRD-MATCH-E1-S2:21** — AC dòng 21 lấy kết quả A/B test thống kê (match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận story. A/B test trên dữ liệu thật cần lưu lượng lớn, mất hàng tuần mới đạt p < 0.05. Đây là chỉ số đo SAU triển khai, không phải điều kiện bàn giao sprint. Nát bét vì: đóng story cuối sprint thì kết quả A/B test chưa có. Coi AC này là điều kiện cứng thì story treo vô thời hạn ở trạng thái "chờ dữ liệu"; bỏ qua thì AC thành cam kết rỗng. Cả hai đều giết tính xác định của quy trình bàn giao. Gõ lại ngay: tách đôi. (1) Story kỹ thuật giữ AC lọc tiêu chí cứng, tỉ lệ hồ sơ active, thời gian tải (kiểm tra được tại bàn giao). (2) Story đo lường riêng với AC "dashboard A/B test có dữ liệu thực và đọc được kết quả", không phải p < 0.05.

3. **[blocker][tech] PRD-CHAT-E1-S3:18** — Cả hai AC dùng kết quả không đo được: "trải nghiệm phải mượt mà" (dòng 18), "giao diện hiển thị nhanh và không giật lag" (dòng 19). Không ngưỡng số, không thiết bị tham chiếu, không phần trăm thất bại. PRD-CHAT-E1-S4 dính y hệt: "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn". Nát bét vì: không AC nào chuyển được thành test thông/không thông. Kỹ sư không có definition of done để đóng sprint, QA không có ngưỡng để từ chối, sản phẩm không bao giờ "xong" mà chỉ tick done theo cảm tính. Gõ lại ngay: thay bằng ngưỡng đo được. S3: "cuộn danh sách / gõ phím trên Android tầm trung (RAM 3 GB), frame rate >= 55 fps, không jank frame nào vượt 16 ms trong 100 frame liên tiếp" và "mở cuộc trò chuyện 50 tin, tương tác được trong 1,5 giây ở p95". S4: liệt kê cơ chế bảo vệ cụ thể (cảnh báo link ngoài trước khi mở, quét CSAM trước khi lưu ảnh, từ chối với mã lỗi rõ ràng).

## Theo lăng kính

### Product

- **[blocker] BRD:62** — (xem Top 3 #1) North-star không có metric nào đo; mọi story gắn mau-monthly hoặc weekly-match-rate, đúng bộ "con số match/quy mô" mà VISION:45-52 nói thẳng muốn thoát. `DEC-worthy`
- **[major] PRD-MATCH-E1-S1:30** — Story đáy phễu lõi sản phẩm mà "so that" dừng ở "tạo match với người tôi quan tâm" (dòng 30), 4 AC (34-37) chỉ tới sự kiện tạo match và thông báo, metric chỉ weekly-match-rate (dòng 16). Nát bét vì: lõi tối ưu đúng cho "match ảo" mà VISION:45-52 tuyên bố chống; mọi quyết định hạ nguồn kéo về số match, không phải kết nối. Đúng con Tinder mày bảo không muốn xây. Gõ lại ngay: sửa "so that", thêm AC nối tới luồng mở cuộc trò chuyện PRD-CHAT (ghi tín hiệu match-to-first-message), đổi metric sang chỉ số kết nối duy trì.
- **[major] PRD-CHAT-E1-S4:18** — "So that" vòng tròn (dòng 28: muốn an toàn để yên tâm) và 2 AC không kiểm chứng nổi: "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn" (18-19). Phạm vi "an toàn" lại trùng PRD-SAFETY (xác minh danh tính và chống lừa đảo), vốn là PRD core-value riêng. Nát bét vì: AC "tuyệt đối / hoàn toàn" không bao giờ done, lại nhân đôi phạm vi với PRD-SAFETY, phá vỡ một-nhà-một-sự-thật, đẻ ra yêu cầu mâu thuẫn giữa hai PRD. Gõ lại ngay: xoá S4 dồn về PRD-SAFETY, hoặc thu hẹp thành job cụ thể của nhắn tin (chặn/báo cáo người trong cuộc) với AC đếm được. (tech cũng bắt cùng AC này, xem "not testable")
- **[major] PRD-PREMIUM:37** — Động cơ doanh thu lõi (BRD-G3) bán bằng đúng bộ cơ chế match-count mà sản phẩm tuyên bố chống: "xem ai đã thích mình", boost hồ sơ, thích không giới hạn (37-38); PRD tự nhận me-too sau Tinder, ngang Bumble (42-45). Nát bét vì: động cơ duy nhất tới hoà vốn xây trên incentive quẹt-vô-tận, đúng pain mà VISION:22-28 bảo là lý do người Việt chán app Tây. Nếu pain thật thì user không trả tiền cho thứ họ ghét; nếu họ trả thì giả định lõi của vision sai. Spec không gỡ mâu thuẫn này. Gõ lại ngay: định nghĩa ít nhất một gói premium phục vụ trực tiếp kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng hiển thị), ghi rõ trong Overview cách premium tránh tái lập match-vanity; không làm được thì nêu thẳng là rủi ro giả định lõi. `DEC-worthy`
- **[minor] PRD-EVENTS-E1-S3:18** — Đặc tả hẳn một hệ thống bán vé concert toàn quốc trong app hẹn hò (5 AC: danh sách theo nghệ sĩ/hạng vé, đặt tối đa 4 vé, giữ chỗ 10 phút, vé QR, lọc thể loại), size L. Spec tự nhận gold-plating (41-48), đặt out/could/later. Nát bét vì: dù dán nhãn out, mảng bán vé cỡ L với AC đầy đủ vẫn ăn chu kỳ review của PO, làm loãng tín hiệu trọng tâm, mời gọi đầu tư sớm vào lĩnh vực không đo north-star. Tự nhận thức không khử được chi phí cơ hội. Gõ lại ngay: giáng S3 thành một dòng ý tưởng trong mục "tầm nhìn xa" của PRD-EVENTS; chỉ nâng lại thành story khi north-star đã instrument và chứng minh, kèm DEC tường minh.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18** — (xem Top 3 #3) AC "mượt mà / không giật lag", không ngưỡng, không thiết bị tham chiếu; S4 dính kèm "tuyệt đối / hoàn toàn".
- **[blocker] PRD-MATCH-E1-S2:21** — (xem Top 3 #2) p < 0.05 làm điều kiện bàn giao sprint.
- **[major] PRD-MATCH-E1-S2:22** — AC dòng 22 yêu cầu tính năng giải thích gợi ý ("Vì sao gợi ý người này?", >= 2 tiêu chí khớp). PRD-AIREC:77 liệt kê tường minh tính năng này trong Won't this round. MATCH-E1-S2 là core-value/must/now; AIREC là in/could/later. Xung đột trực tiếp trên cùng tính năng, không depends_on nào liên kết. Nát bét vì: kỹ sư MATCH phải xây lớp giải thích nhưng AIREC (nơi nắm logic gợi ý) không xây cycle này. Story hoặc bị block, hoặc tự tái triển khai logic gợi ý trong MATCH, đẻ hai code path song song. Gõ lại ngay: bỏ AC dòng 22 khỏi MATCH-E1-S2; cần thì chuyển thành story trong PRD-AIREC (could/later) khớp với Won't đã ghi ở AIREC:77; thêm depends_on: [PRD-AIREC] nếu có AC phụ thuộc ranking của AIREC. `DEC-worthy`
- **[major] PRD-PREMIUM-E1-S1:20** — AC dòng 20 kiểm tra "giao dịch hoàn tất thì mở khoá quyền xem trong 5 giây", giả định luồng thanh toán đã tồn tại. PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào Won't this round; không depends_on nào trong chuỗi liên kết tới story thanh toán. Nát bét vì: không payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm tra được trong tích hợp thực; test phải mock cả luồng, mất giá trị end-to-end; chọn gateway sau thì viết lại AC. Gõ lại ngay: thêm story/epic stub payment integration (dù placeholder), đặt PREMIUM-E1-S1 depends_on; sửa AC thành "giả sử gateway trả webhook xác nhận thành công, khi nhận webhook thì cập nhật trạng thái gói và mở khoá trong 5 giây", tách rõ ranh giới payment vs entitlement.
- **[major] PRD-SAFETY-E1-S1:21** — AC dòng 21 yêu cầu xoá ảnh giấy tờ gốc trong 24h sau xác minh, "không bao giờ hiển thị cho người dùng khác" (gần GDPR retention), nhưng không cơ chế nào để QA/audit verify: không audit log, không API check, không retention policy reference. Nát bét vì: không cách nào test từ phía user/QA rằng ảnh đã thực sự xoá khỏi storage sau 24h; nếu cron job bug không xoá, không ai biết cho tới khi breach. Gõ lại ngay: tách 2 AC. (1) "Truy vấn storage audit log sau 25h, record ảnh gốc không còn và deletion event ghi trong audit trail có timestamp." (2) "Admin truy vấn retention report, không ảnh giấy tờ nào created_at cũ hơn 25h còn trong storage." Thêm NFR: deletion SLA 24h enforce bởi scheduled job, không on-demand.
- **[minor] PRD-AIREC-E1-S1:21** — AC dòng 21 đặt ngưỡng "20 hồ sơ đầu hiển thị trong 2 giây trên thiết bị di động phổ thông tại Việt Nam", không định nghĩa "phổ thông" (CPU/RAM/OS), không percentile. Story size L, could/later, phụ thuộc mô hình ML chưa chọn. Nát bét vì: không thiết bị tham chiếu thì không có cấu hình môi trường test, ngưỡng không reproducible; khi model thật chọn xong, 2 giây có thể bất khả thi nếu thiếu caching layer. Gõ lại ngay: định nghĩa hardware reference profile trong NFR của AIREC (vd Android tầm trung 2023+, Snapdragon 680/tương đương, RAM 4 GB, 4G 20 Mbps) và percentile p95; sửa AC kèm điều kiện scoring server-side và cache; không xác định nổi hardware trước khi chọn model thì bỏ AC khỏi delivery, chuyển thành spike/NFR kiểm tra sau.

### Market

- **[blocker] BRD:22** — BRD-G3 đặt mục tiêu hoà vốn vận hành năm 2 từ doanh thu premium nhưng toàn spec không một con số: không giá gói, không tỉ lệ chuyển đổi mục tiêu, không ARPU, không ước tính chi phí vận hành. PRD-PREMIUM để later, tự nhận me-too sau Tinder, không luận cứ định lượng nào cho thấy 100k MAU × X% × Y ARPU đủ cover chi phí năm 2. Nát bét vì: thị trường hẹn hò online VN khoảng 6,44M USD/năm 2025 toàn ngành (Statista, https://www.statista.com/outlook/dmo/eservices/dating-services/online-dating/vietnam); Tinder khoảng 10,7% chuyển đổi sau nhiều năm network effect. Tân binh 100k MAU, chuyển đổi thực 3-5%, giá VN khoảng 3-5 USD/tháng tạo khoảng 15-25k USD MRR. Chi phí thực cao hơn thì BRD-G3 vỡ, không cơ chế cảnh báo sớm nào trong spec. Gõ lại ngay: thêm bảng unit-economics tối thiểu vào BRD (giá gói tính theo VND/tháng, tỉ lệ chuyển đổi mục tiêu, ARPU mục tiêu, ước tính chi phí vận hành năm 2); từ đó PRD-PREMIUM mới định nghĩa được "hoà vốn" là gì. `DEC-worthy`
- **[major] BRD:26** — Danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan, app hẹn hò tập trung user châu Á, ra mắt TanTan Tribe tại Singapore 12/2024, đang mở sang Malaysia/Thailand/láng giềng, chia sẻ đúng phân khúc châu Á mà spec coi là lợi thế. Nát bét vì: Tantan đang tái định vị sang "kết nối châu Á có chiều sâu văn hoá"; nếu đẩy vào VN với định vị tương tự và tập user châu Á sẵn lớn hơn, luận điểm "bản địa hoá" của spec bị xói mòn, không kịch bản phòng thủ. Gõ lại ngay: thêm Tantan (cân nhắc Facebook Dating) vào `competitors:` trong BRD với threat level rõ; cập nhật `competitive_parity` ở PRD-MATCH và PRD-SAFETY.
- **[major] PRD-MATCH:22** — Cơ chế lõi (khám phá, quẹt thích/bỏ qua, tạo match hai chiều) đánh giá `parity` với Tinder, `behind` với Bumble. Đây là toàn bộ trải nghiệm năm 1, AI và premium đều later. Khác biệt tuyên bố trong VISION ("đo bằng kết nối thật") không thể hiện bằng bất kỳ tính năng must/should nào trong now/next; chỉ là cam kết đo lường nội bộ. Nát bét vì: user không chọn app vì north-star metric nội bộ, họ chọn vì trải nghiệm khác biệt ngay khi dùng. Màn quẹt giống Tinder (parity), premium chưa có, AI chưa có thì không lý do hành vi nào để rời Tinder, vốn dẫn đầu top grossing VN (Similarweb 3/2026, https://www.similarweb.com/top-apps/google/vietnam/lifestyle/) với network effect lớn hơn nhiều. Gõ lại ngay: xác định ít nhất một tính năng must/should trong now/next thể hiện "kết nối thật" mà user cảm nhận ngay (icebreaker tự động sau match, giới hạn số match đồng thời, badge "đang nhắn tin"); không có hook trải nghiệm thì tuyên bố định vị chỉ là marketing copy.

### Craft

- **[major] PRD-MATCH-E1-S1:20** — AC dòng 20 "hệ thống tạo match và hiển thị thông báo match cho cả hai trong vòng 5 giây": "thông báo match" không rõ là thông báo gì, và không nói điều kiện "cả hai cùng thích" xảy ra tức thì hay có độ trễ, tính từ ai. Nát bét vì: A và B thích cùng lúc hay A đã thích từ trước thì thông báo gửi bao giờ? 5 giây tính từ nhìn của ai? AC giả định tức thì nhưng không xác định mốc. Gõ lại ngay: "Khi cả hai phía cùng thích nhau, hệ thống tạo match và gửi thông báo push cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận", rõ loại thông báo (push) và mốc tính giờ.
- **[major] PRD-MATCH-E1-S1:19** — AC dòng 19 "cả hai phản hồi dưới 300ms": "phản hồi" không rõ là latency API, thời gian render UI, hay cảm nhận người dùng; "ghi nhận" trừu tượng (lưu DB? gửi signal?). Nát bét vì: QA/dev không biết đo "300ms" ở đâu, từ touch tới lưu xong hay từ touch tới UI cập nhật. Không kiểm chứng khách quan được. Gõ lại ngay: "Quẹt phải: ghi nhận lượt thích (lưu DB); quẹt trái: ghi nhận bỏ qua (lưu DB). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc kèm mốc UI: hồ sơ tiếp theo lên sân trong 300ms).
- **[major] VISION:24, PRD-MATCH:31** — VISION:24 nêu vấn đề "hàng triệu match ảo không bao giờ dẫn tới một cuộc trò chuyện thật"; PRD-MATCH:31 AC lại "khi cả hai cùng thích, hệ thống tạo match", tức story này TẠO thêm match mà không cơ chế gì kéo nó về trò chuyện thật. Nát bét vì: mâu thuẫn lõi. Story này giải quyết vấn đề core hay đang đẻ lại đúng vấn đề (match ảo)? North-star là cặp duy trì nhắn tin >= 7 ngày (VISION:51) mà AC chỉ yêu cầu tạo match thì match đó bị lãng quên y như cũ. Gõ lại ngay: thêm AC "khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu cuộc trò chuyện"; hoặc rõ scope ở epic "story này: tạo match hai chiều; tiếp nối PRD-CHAT biến match thành kết nối thật". (Cùng họ với product BRD:62 và PRD-MATCH-E1-S1:30, north-star không nối tới hành vi.)
- **[minor] PRD-MATCH-E1-S1:29** — Khuôn User Story dùng tiêu đề cột tiếng Anh ("As a | I want | so that") rồi kèm bản dịch Việt ("Với vai trò | Tôi muốn | để"), một dòng hai cặp nhãn song ngữ, lệch hẳn với phần Acceptance Criteria bên dưới không có nhãn kép. Nát bét vì: PO không kỹ thuật bị phân tán bởi nhãn kép, không rõ đọc Anh hay Việt; dòng 28 thành ngoại lệ format. Gõ lại ngay: bỏ nhãn tiếng Anh ở dòng 28, chỉ giữ "Với vai trò / Tôi muốn / Để" cho cân với phần "Tiêu chí chấp nhận".
- **[minor] PRD-MATCH-E1-S1:18** — AC dòng 18 "một chồng tối thiểu 10 hồ sơ gợi ý đã tải sẵn": "gợi ý" dùng như tính từ trong khi toàn ancestry dùng "gợi ý" là danh/động từ; "hồ sơ gợi ý" là cấu trúc không tự nhiên với tiếng Việt. Nát bét vì: dễ hiểu nhầm "gợi ý" là một loại hồ sơ đặc biệt thay vì "hồ sơ được hệ thống gợi ý"; lệch với Vision (dòng 43: "hồ sơ được gợi ý"). Gõ lại ngay: "Khi mở màn hình khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

Không có (prior_reports rỗng).

## Đáng ghi thành quyết định (DEC-worthy)

- **BRD:62** — Chọn north-star metric đo kết nối duy trì và quan hệ với weekly-match-rate là ruling về định hướng đo lường sản phẩm, mâu thuẫn với bộ Success Metrics đang dùng. PO nên ghi DEC.
- **PRD-PREMIUM:37** — Mô hình kiếm tiền (kết nối-duy-trì vs match-vanity me-too) là ruling positioning và doanh thu, có thể mâu thuẫn với vision đã approve. PO nên ghi DEC.
- **BRD:22** — Định nghĩa "hoà vốn" và bảng unit-economics (giá/chuyển đổi/ARPU/chi phí) là binding business ruling cho BRD-G3. PO nên ghi DEC.
- **PRD-MATCH-E1-S2:22** — Tính năng giải thích gợi ý xung đột giữa MATCH (must/now) và AIREC Won't (PRD-AIREC:77). PO nên ghi DEC chốt nó thuộc cycle nào.
