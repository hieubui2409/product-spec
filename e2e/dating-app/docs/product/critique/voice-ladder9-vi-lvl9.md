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
level: 9
register:
  dialect: bac
  gender: m
  profanity: strong
---
# Critique: all · level 9 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 3

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** — North-star là "cặp đôi duy trì nhắn tin >= 7 ngày" (PRODUCT.md:15, VISION:51), mà Success Metrics của BRD (BRD:62-65) đếm MAU, weekly-match-rate, premium-conversion, ARPU. Cái lý do app này tồn tại không có lấy một thước đo. Banh xác vì: app đạt đủ 100k MAU, 20% match/tuần, đội ăn mừng "thành công" trong khi không một cặp nào trò chuyện thật. Đm cái differentiator duy nhất so với Tinder thì không đo, không chứng minh được, đội build cắm đầu tối ưu match-count y hệt đối thủ, riskiest assumption của cả sản phẩm không có một instrument nào để kiểm chứng. Gõ lại, đừng để tao nhắc lại: thêm metric north-star tường minh (sustained-7day-conversation-rate) vào BRD Success Metrics, gắn làm metric chính cho PRD-CHAT và story PRD-CHAT-E1-S1; xét lại BRD-G2 để hoặc thay weekly-match-rate bằng chỉ số kết nối duy trì, hoặc ghi rõ match-rate chỉ là leading indicator phụ thuộc north-star.

2. **[blocker][tech] PRD-CHAT-E1-S3:18 + PRD-CHAT-E1-S4:18** — AC viết "trải nghiệm phải mượt mà", "hiển thị nhanh không giật lag", "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn". Rỗng vl, không một ngưỡng số, không thiết bị tham chiếu, không tiêu chí vượt/không. Banh xác vì: không AC nào trong đây chuyển được thành test case thông/không thông. Kỹ sư không có definition of done để đóng sprint, QA không có ngưỡng để từ chối, story treo vô thời hạn hoặc bị tick done theo cảm tính. Gõ lại, đừng để tao nhắc lại: S3 cần "Khi cuộn danh sách tin nhắn hoặc gõ phím trên Android tầm trung (RAM 3 GB), frame rate >= 55 fps, không jank frame nào vượt 16 ms trong 100 frame liên tiếp" và "Khi mở cuộc trò chuyện 50 tin nhắn, UI tương tác được trong 1,5 giây ở p95". S4 cần liệt kê cơ chế bảo vệ cụ thể: cảnh báo link ngoài trước khi mở URL; quét CSAM trước khi lưu ảnh, từ chối với mã lỗi rõ nếu phát hiện.

3. **[blocker][tech] PRD-MATCH-E1-S2:21** — AC đặt kết quả A/B test thống kê (match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận của story. Đây là chỉ số đo SAU triển khai, cần nhiều tuần lưu lượng thật, không phải điều kiện bàn giao sprint. Đm nhét nhầm chỗ. Banh xác vì: story không đóng được cuối sprint vì lúc bàn giao chưa có dữ liệu A/B. Coi là điều kiện cứng thì story treo "chờ dữ liệu" vô thời hạn; bỏ qua thì AC thành cam kết trống. Hai đường đều giết tính xác định của bàn giao. Gõ lại, đừng để tao nhắc lại: tách đôi. (1) Story kỹ thuật giữ AC về lọc tiêu chí cứng, tỉ lệ hồ sơ active, thời gian tải, kiểm tra được tại bàn giao. (2) Story đo lường riêng "Thiết lập A/B framework đo tỉ lệ match nhóm AI vs nhóm ngẫu nhiên, báo cáo sau N ngày với mẫu M user", AC là "dashboard A/B có dữ liệu thực đọc được", không phải p < 0.05.

## Theo lăng kính

### Product

- **[blocker] BRD:62** — xem Top 3 #1.
- **[major] PRD-MATCH-E1-S1:30** — story must/core-value của lõi mà "so that" dừng ở "tạo match với người tôi quan tâm", bốn AC (dòng 34-37) đóng ở sự kiện tạo match + thông báo, metric gắn weekly-match-rate. Không AC nào nối lượt thích tới mục tiêu trò chuyện duy trì. Banh xác vì: story đáy phễu của lõi tối ưu đúng cho "match ảo" mà VISION:45-52 tuyên bố chống lại. Lõi đo và thưởng việc tạo match thì mọi quyết định hạ nguồn kéo về số match, ra đúng cái Tinder spec bảo không muốn xây. Gõ lại, đừng để tao nhắc lại: sửa "so that" và thêm AC nối tới hành trình kết nối (sau match dẫn thẳng vào luồng mở chat PRD-CHAT, ghi tín hiệu match-first-message), đổi metric story sang chỉ số kết nối duy trì. `DEC-worthy`
- **[major] PRD-CHAT-E1-S4:18** — "Nhắn tin an toàn tuyệt đối" có "so that" vòng tròn (dòng 28) và hai AC bất khả kiểm "an toàn tuyệt đối", "bảo vệ hoàn toàn" (dòng 18-19); phạm vi an toàn này đè lên PRD-SAFETY. Banh xác vì: AC "tuyệt đối/hoàn toàn" không bao giờ done. Build không biết khi nào xong, QA không có gì kiểm, lại nhân đôi phạm vi an toàn với PRD-SAFETY, phá một-nhà-một-sự-thật, đẻ ra yêu cầu mâu thuẫn giữa hai PRD. Gõ lại, đừng để tao nhắc lại: xoá S4, dồn an toàn về PRD-SAFETY; hoặc thu hẹp S4 thành job cụ thể của nhắn tin (chặn/báo cáo người trong cuộc trò chuyện) với AC đếm được (báo cáo gửi được, người bị chặn không gửi được tin trong X giây). `DEC-worthy`
- **[major] PRD-PREMIUM:37** — bán doanh thu lõi (BRD-G3) bằng đúng bộ cơ chế match-count mà spec tuyên bố chống: "xem ai đã thích mình", boost hồ sơ, thích không giới hạn (dòng 37-38), PRD tự nhận me-too sau Tinder ngang Bumble (dòng 42-45). Banh xác vì: động cơ doanh thu duy nhất tới hoà vốn xây trên incentive quẹt-vô-tận, đúng pain VISION:22-28 bảo là lý do người Việt chán app Tây. Pain có thật thì user không trả tiền cho thứ họ ghét. Họ trả thì giả định lõi của vision sai. Spec né luôn mâu thuẫn, value prop premium không ánh xạ tới gain/pain nào trong vision. Gõ lại, đừng để tao nhắc lại: định nghĩa ít nhất một gói/tính năng premium phục vụ trực tiếp kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng lượt hiển thị), ghi rõ trong PRD-PREMIUM Overview cách premium tránh tái lập match-vanity. Không làm được thì nêu thẳng đây là rủi ro giả định lõi. `DEC-worthy`
- **[minor] PRD-EVENTS-E1-S3:18** — đặc tả nguyên hệ thống bán vé concert toàn quốc trong app hẹn hò, năm AC đầy đủ, size L (dòng 18-22), spec tự nhận gold-plating, để scope out/could/later. Banh xác vì: dán nhãn out cũng vẫn là một mảng kinh doanh bán vé cỡ L với AC đầy đủ nằm trong backlog, ngốn chu kỳ review của PO, loãng tín hiệu trọng tâm cho build và nhà đầu tư, mời gọi đầu tư sớm vào lĩnh vực chẳng đo north-star. Tự nhận thức không khử được chi phí cơ hội. Gõ lại, đừng để tao nhắc lại: giáng S3 xuống một dòng ý tưởng trong mục "tầm nhìn xa" của PRD-EVENTS thay vì story có AC đầy đủ; chỉ nâng lại thành story khi north-star đã instrument và chứng minh, kèm một DEC tường minh so với north-star.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18** + **PRD-CHAT-E1-S4:18** — xem Top 3 #2.
- **[blocker] PRD-MATCH-E1-S2:21** — xem Top 3 #3.
- **[major] PRD-MATCH-E1-S2:22** — AC yêu cầu tính năng giải thích gợi ý ("Vì sao gợi ý người này?" hiện >= 2 tiêu chí khớp), nhưng PRD-AIREC:77 liệt kê tường minh chính tính năng này trong Won't this round. MATCH-E1-S2 (core-value/must/now) xung đột trực tiếp với AIREC (in/could/later) trên cùng tính năng, không depends_on nào nối. Nát bét vì: kỹ sư MATCH phải xây lớp giải thích trong khi AIREC, nơi nắm toàn bộ logic gợi ý, không xây trong cycle này. Story hoặc bị block chờ AIREC hoặc tự tái triển khai logic gợi ý trong MATCH, đẻ ra hai code path song song. Gõ lại ngay: bỏ AC dòng 22 khỏi MATCH-E1-S2. Cần tính năng giải thích thì chuyển thành story riêng trong PRD-AIREC (could/later) khớp quyết định Won't tại AIREC:77; thêm depends_on: [PRD-AIREC] vào MATCH-E1-S2 nếu có AC nào phụ thuộc logic ranking AIREC. `DEC-worthy`
- **[major] PRD-PREMIUM-E1-S1:20** — AC kiểm "giao dịch hoàn tất, mở khoá quyền xem trong 5 giây", giả định một luồng thanh toán đã có, nhưng PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào Won't this round, không depends_on nào nối tới story thanh toán. Nát bét vì: không payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm được trong môi trường tích hợp thật. Test buộc phải mock cả payment flow, mất giá trị end-to-end; chọn gateway sau thì viết lại AC kiểm lại từ đầu. Gõ lại ngay: thêm story/epic stub payment integration (dù chỉ placeholder), đặt PREMIUM-E1-S1 depends_on nó; sửa AC thành "Giả sử payment gateway trả webhook xác nhận thành công, khi nhận webhook, hệ thống cập nhật trạng thái gói và mở khoá quyền xem trong 5 giây", tách rạch ròi payment vs entitlement layer.
- **[major] PRD-SAFETY-E1-S1:21** — AC yêu cầu ảnh giấy tờ gốc bị xoá trong 24 giờ sau xác minh và "không bao giờ hiển thị cho người khác", yêu cầu tuân thủ riêng tư gần GDPR-tier, nhưng không cơ chế nào để QA/audit verify: không audit log, không API check, không retention policy reference. Nát bét vì: không có cách test thụ động từ user/QA rằng ảnh đã thực sự xoá khỏi storage sau 24 giờ. Cron job lỗi thì không ai biết tới khi breach. AC này cần một acceptance path quan sát được mới thật sự testable. Gõ lại ngay: tách hai AC. (1) "Khi truy vấn storage audit log sau 25 giờ, record ảnh giấy tờ gốc của user không còn trong bucket và deletion event được ghi với timestamp." (2) "Khi admin truy vấn retention report, không ảnh giấy tờ nào created_at cũ hơn 25 giờ còn trong storage." Thêm NFR PRD-SAFETY: deletion SLA 24h enforce bởi scheduled job, không on-demand.
- **[minor] PRD-AIREC-E1-S1:21** — ngưỡng "20 hồ sơ đầu hiển thị trong 2 giây trên thiết bị di động phổ thông tại Việt Nam", không định nghĩa "phổ thông" (CPU/RAM/OS), không percentile; story size L/could/later, phụ thuộc một mô hình ML chưa chọn. Banh xác vì: không thiết bị tham chiếu thì không cấu hình được môi trường test, threshold không reproducible. Khi mô hình thật được chọn, inference latency đo được, 2 giây có thể bất khả thi nếu thiếu caching. Kỹ sư không size nổi story khi cả hardware lẫn model đều chưa xác định. Gõ lại, đừng để tao nhắc lại: định nghĩa hardware reference profile ở NFR PRD-AIREC (Android tầm trung 2023+: Snapdragon 680 hoặc tương đương, RAM 4 GB, 4G 20 Mbps) cùng percentile p95; sửa AC "...20 hồ sơ đầu trong 2 giây ở p95, với scoring server-side và kết quả được cache". Không xác định được hardware trước khi chọn model thì bỏ AC khỏi delivery, chuyển thành spike/NFR kiểm sau.

### Market

- **[blocker] BRD:22** — BRD-G3 đặt mục tiêu hoà vốn năm 2 từ doanh thu premium mà cả spec không một con số: không giá gói, không tỉ lệ chuyển đổi mục tiêu, không ARPU, không ước tính chi phí vận hành; PRD-PREMIUM để horizon later và tự nhận me-too sau Tinder. Banh xác vì: thị trường hẹn hò online Việt Nam khoảng 6.44M USD năm 2025 toàn ngành (Statista), Tinder đạt chuyển đổi khoảng 10.7% sau nhiều năm xây network effect. Tân binh 100k MAU với chuyển đổi thực 3-5% ở giá Vietnam-tier (3-5 USD/tháng) tạo khoảng 15-25k USD MRR; chi phí thực cao hơn thì BRD-G3 vỡ mà spec không một cơ chế cảnh báo sớm. Gõ lại, đừng để tao nhắc lại: thêm vào BRD bảng unit-economics tối thiểu (giá gói VND/tháng, tỉ lệ chuyển đổi mục tiêu, ARPU mục tiêu, ước tính chi phí vận hành năm 2); từ đó PRD-PREMIUM mới định nghĩa được "hoà vốn" là gì. `DEC-worthy`
- **[major] BRD:26** — danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan, app hẹn hò tập trung người dùng châu Á đang mở sang Đông Nam Á (TanTan Tribe ra mắt Singapore 12/2024, đang mở sang Malaysia, Thailand), chia sẻ đúng phân khúc châu Á mà spec coi là lợi thế. Nát bét vì: Tantan đang chủ động tái định vị sang "kết nối châu Á có chiều sâu văn hoá"; nếu Tantan Tribe đẩy vào Việt Nam với định vị tương tự và tập user châu Á lớn hơn, luận điểm "bản địa hoá" của spec bị xói mòn mà không có kịch bản phòng thủ nào. Gõ lại ngay: thêm Tantan (cân nhắc cả Facebook Dating) vào `competitors:` trong BRD với threat level rõ; cập nhật `competitive_parity` ở PRD-MATCH và PRD-SAFETY phản ánh vị thế so với đối thủ này.
- **[major] PRD-MATCH:22** — cơ chế lõi (khám phá, quẹt, tạo match) bị đánh giá `parity` Tinder và `behind` Bumble; đây là toàn bộ trải nghiệm năm 1 vì AI và premium đều later. Khác biệt tuyên bố trong VISION ("đo bằng kết nối thật") không thể hiện bằng một tính năng must/should nào trong now/next, chỉ là cam kết đo lường nội bộ. Nát bét vì: user không chọn app vì north-star metric nội bộ, họ chọn vì trải nghiệm khác biệt ngay khi dùng. Màn quẹt giống Tinder (parity), premium chưa có, AI chưa có thì không lý do hành vi nào để rời Tinder, đặc biệt khi Tinder đã dẫn đầu top grossing Việt Nam (Similarweb, 3/2026) với network effect lớn hơn nhiều. Gõ lại ngay: xác định ít nhất một tính năng must/should trong now/next thể hiện "kết nối thật" user cảm nhận ngay (icebreaker tự động sau match, giới hạn số match đồng thời, hoặc badge "đang nhắn tin"). Không có hook trải nghiệm rõ thì tuyên bố định vị chỉ là marketing copy. `DEC-worthy`

### Craft

- **[major] PRD-MATCH-E1-S1:20** — AC "hệ thống tạo match và hiển thị thông báo match cho cả hai trong vòng 5 giây": "thông báo match" không rõ là gì, không rõ "cả hai phía cùng thích" xảy ra tức thì hay có trễ, 5 giây tính từ đâu. Nát bét vì: mơ hồ hành vi hệ thống, A và B thích cùng lúc hay đã thích từ trước thì thông báo gửi bao giờ, 5 giây tính từ nhìn của ai, không kiểm được. Gõ lại ngay: "Khi cả hai phía cùng thích nhau, hệ thống tạo match và gửi thông báo push cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận."
- **[major] PRD-MATCH-E1-S1:19** — AC "quẹt phải ghi nhận thích, quẹt trái ghi nhận bỏ qua, cả hai phản hồi dưới 300ms": "phản hồi" không rõ là latency API, render UI hay cảm nhận user; "ghi nhận" trừu tượng, hệ thống làm gì cụ thể. Nát bét vì: QA/dev không biết đo "phản hồi dưới 300ms" từ điểm nào, tiêu chuẩn không kiểm chứng khách quan được. Gõ lại ngay: "Quẹt phải: ghi nhận lượt thích (lưu vào database); quẹt trái: ghi nhận bỏ qua (lưu vào database). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc nêu rõ điểm đo phía UI nếu muốn).
- **[major] VISION:24, PRD-MATCH:31** — VISION:24 nêu "hàng triệu match ảo không bao giờ dẫn tới một cuộc trò chuyện thật" là problem statement, mà PRD-MATCH:31 có AC "khi cả hai cùng thích, hệ thống tạo match", tức story này TẠO thêm match không một cơ chế nào để đảm bảo dẫn tới trò chuyện thật. Nát bét vì: mâu thuẫn này gây hoài nghi story có giải vấn đề core hay đang đẻ lại đúng vấn đề match ảo. North-star là "duy trì nhắn tin >= 7 ngày" (VISION:51) mà AC chỉ yêu cầu tạo match thì match này bị lãng quên thế nào. Gõ lại ngay: thêm AC "Khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu cuộc trò chuyện", hoặc nếu nhắn tin là PRD-CHAT thì rõ scope ở epic: "Story này: tạo match hai chiều. Tiếp nối: PRD-CHAT xử lý mở đầu cuộc trò chuyện để biến match thành kết nối thật."
- **[minor] PRD-MATCH-E1-S1:29** — khuôn User Story dùng tiêu đề cột tiếng Anh ("As a | I want | so that") rồi mới tới bản dịch tiếng Việt, một dòng hai cặp nhãn. Banh xác vì: PO không kỹ thuật bị nhãn kép làm phân tán, không rõ đọc tiếng Anh hay Việt; phần Acceptance Criteria phía dưới không có nhãn kép nên dòng 28 thành ngoại lệ lệch chuẩn. Gõ lại, đừng để tao nhắc lại: bỏ nhãn tiếng Anh ở dòng 28, dùng cấu trúc chỉ tiếng Việt ("Với vai trò / Tôi muốn / Để") cho cân với phần "Tiêu chí chấp nhận".
- **[minor] PRD-MATCH-E1-S1:18** — AC dùng "một chồng tối thiểu 10 hồ sơ gợi ý đã tải sẵn"; "gợi ý" làm tính từ ở đây, trong khi toàn ancestry "gợi ý" thường là danh/động từ, "hồ sơ gợi ý" là cách ghép không tự nhiên. Banh xác vì: người đọc dễ hiểu nhầm "gợi ý" là một loại hồ sơ đặc biệt thay vì "hồ sơ được hệ thống gợi ý", lệch với Vision (dòng 43 "hồ sơ được gợi ý"). Gõ lại, đừng để tao nhắc lại: "Khi mở màn hình khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

không có

## Đáng ghi thành quyết định (DEC-worthy)

- **BRD:62 / BRD:22** — north-star không có metric đo lường và unit-economics của BRD-G3 trống: cả hai chạm thẳng tới định nghĩa "thành công" và mục tiêu hoà vốn của BRD (artifact mức cao), PO nên ghi DEC chốt north-star metric + bảng unit-economics tối thiểu.
- **PRD-MATCH-E1-S1:30 / VISION:24 / PRD-MATCH:22** — lõi sản phẩm đo và thưởng match-count, mâu thuẫn trực tiếp với positioning "kết nối thật" trong VISION; PO nên ghi DEC chốt lõi cam kết hook trải nghiệm kết nối duy trì nào trong now/next.
- **PRD-CHAT-E1-S4:18** — chồng lấn phạm vi an toàn với PRD-SAFETY phá DRY một-nhà-một-sự-thật; PO ghi DEC chốt PRD nào sở hữu phạm vi an toàn.
- **PRD-PREMIUM:37** — mô hình doanh thu premium tái lập match-vanity mà vision phủ nhận; PO ghi DEC chốt premium có phục vụ north-star hay chấp nhận rủi ro giả định lõi.
- **PRD-MATCH-E1-S2:22** — AC giải thích gợi ý mâu thuẫn với quyết định Won't this round tại PRD-AIREC:77 (artifact đã chốt phạm vi); PO ghi DEC chốt tính năng giải thích thuộc cycle nào.
