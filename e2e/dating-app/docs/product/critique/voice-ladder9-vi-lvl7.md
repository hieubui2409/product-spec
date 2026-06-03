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
level: 7
register:
  dialect: bac
  gender: m
  profanity: strong
---
# Critique: all  ·  level 7  ·  lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 4

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** — Ông định nghĩa north-star là "số cặp đôi duy trì nhắn tin >= 7 ngày" (PRODUCT.md:15, VISION:51), rồi Success Metrics của BRD (BRD:62-65) không có nổi một chỉ số nào đo cái đó: chỉ toàn MAU, weekly-match-rate, premium-conversion, arpu. Rà hết story cũng vậy, không story nào mang north-star. Cái "đếm match" mà VISION:45-52 nói thẳng là muốn thoát thì lại chính là thứ ông đang đo.

   **Banh nóc vì:** sản phẩm của ông có thể đạt 100k MAU, 20% match/tuần, mọi người vỗ tay "thành công", mà không một cặp nào nói chuyện thật. Differentiator duy nhất so với Tinder/Bumble không đo được thì không chứng minh được, không tối ưu được, và đội build sẽ đi tối ưu match-count y chang đối thủ. Giả định rủi ro nhất của cả sản phẩm không có lấy một cái cân để đo.

   **Gõ lại cho tử tế:** thêm metric north-star tường minh vào BRD Success Metrics (ví dụ sustained-7day-conversation-rate), gắn nó làm metric chính cho PRD-CHAT và ít nhất PRD-CHAT-E1-S1; rà lại BRD-G2 để hoặc thay weekly-match-rate bằng chỉ số kết nối duy trì, hoặc nói rõ match-rate chỉ là leading indicator. *(DEC-worthy)*

2. **[blocker][market] BRD:22** — BRD-G3 đặt mục tiêu hoà vốn vận hành năm 2 từ premium, mà cả spec không có lấy một con số: không giá gói, không tỉ lệ chuyển đổi, không ARPU, không chi phí vận hành. PRD-PREMIUM thì đẩy `horizon: later` và tự nhận me-too đi sau Tinder.

   **Banh nóc vì:** thị trường hẹn hò online Việt Nam khoảng 6.44M USD/năm 2025 (Statista), Tinder mất nhiều năm mới đạt ~10.7% conversion. Tân binh 100k MAU với 3-5% conversion thực tế và giá Vietnam-tier (3-5 USD/tháng) ra cỡ 15-25k USD MRR. Chi phí mà nhỉnh hơn thế là BRD-G3 vỡ, và spec không có một cơ chế cảnh báo sớm nào.

   **Gõ lại cho tử tế:** thêm vào BRD một bảng unit-economics tối thiểu: giá gói (VND/tháng), tỉ lệ chuyển đổi mục tiêu, ARPU mục tiêu, chi phí vận hành năm 2. Có số rồi PRD-PREMIUM mới định nghĩa nổi "hoà vốn" là gì. *(DEC-worthy)*

3. **[blocker][tech] PRD-CHAT-E1-S3:18 · PRD-CHAT-E1-S4:18** — Cả hai AC của S3 viết "trải nghiệm phải mượt mà" và "hiển thị nhanh không giật lag"; S4 viết "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn". Không ngưỡng số, không thiết bị tham chiếu, không percentile, không tiêu chí thông/không.

   **Banh nóc vì:** không một AC nào chuyển được thành test thông/không thông. Kỹ sư không có điều kiện dừng để đóng sprint, QA không có ngưỡng để từ chối, và story sẽ treo vô hạn hoặc bị tick done tuỳ hứng.

   **Gõ lại cho tử tế:** S3: "Khi cuộn danh sách tin nhắn trên Android tầm trung (RAM 3 GB), frame rate >= 55 fps, không jank frame nào vượt 16 ms trong 100 frame liên tiếp" và "mở cuộc trò chuyện 50 tin nhắn, tương tác được trong 1,5 giây (p95)". S4: liệt kê cơ chế bảo vệ cụ thể, ví dụ "khi gửi URL, hệ thống cảnh báo link ngoài trước khi mở"; "khi tải ảnh, quét CSAM trước khi lưu, từ chối kèm mã lỗi nếu phát hiện".

## Theo lăng kính

### Product

- **[blocker] BRD:62** — north-star định nghĩa nhưng không có metric nào trong BRD đo nó; mọi story bám MAU/weekly-match-rate. (Xem Top 3 #1.)

- **[major] PRD-MATCH-E1-S1:30** — Story must/core-value của lõi, nhưng "so that" dừng ở "để tạo match với người tôi quan tâm" (dòng 30), 4 AC (34-37) kết thúc ở sự kiện tạo match và thông báo, metric chỉ [weekly-match-rate] (dòng 16). Không AC nào nối lượt thích tới cuộc trò chuyện duy trì.

  **Banh nóc vì:** story đáy phễu của lõi đang tối ưu đúng cho "match ảo" mà VISION:45-52 tuyên bố chống. Mọi quyết định hạ nguồn (xếp hồ sơ, thông báo) sẽ kéo về phía số match, đúng cái Tinder mà spec nói không xây.

  **Gõ lại cho tử tế:** sửa "so that", thêm AC nối tới hành trình kết nối (sau match dẫn thẳng vào luồng mở chat PRD-CHAT, ghi tín hiệu match→first-message), đổi metric story sang chỉ số kết nối duy trì.

- **[major] PRD-CHAT-E1-S4:18** — "so that" vòng tròn (dòng 28: muốn an toàn để yên tâm) và 2 AC không kiểm chứng được ("an toàn tuyệt đối", "bảo vệ hoàn toàn", dòng 18-19). Phạm vi "an toàn" này lại đè lên PRD-SAFETY (xác minh danh tính, chống lừa đảo), vốn là PRD core-value riêng.

  **Banh nóc vì:** AC không đo được thì không bao giờ done, QA không có gì để kiểm, story trượt vô hạn hoặc tick bừa. Nhân đôi phạm vi an toàn với PRD-SAFETY phá vỡ một-nhà-một-sự-thật, dẫn tới yêu cầu mâu thuẫn giữa hai PRD.

  **Gõ lại cho tử tế:** hoặc xoá S4 và dồn phạm vi an toàn về PRD-SAFETY, hoặc thu hẹp S4 thành job nhắn tin cụ thể (chặn/báo cáo người trong cuộc trò chuyện) với AC đếm được (báo cáo gửi được, người bị chặn không gửi tin được trong X giây). *(DEC-worthy)*

- **[major] PRD-PREMIUM:37** — Premium bán doanh thu lõi (BRD-G3) bằng đúng cơ chế match-count mà sản phẩm tuyên bố chống: "xem ai đã thích mình", boost hiển thị, thích không giới hạn (37-38). PRD tự nhận me-too, đi sau Tinder, ngang Bumble (42-45).

  **Banh nóc vì:** động cơ doanh thu duy nhất hướng tới hoà vốn xây trên incentive quẹt-vô-tận, đúng cái pain mà VISION:22-28 nói là lý do người Việt chán app phương Tây. Người dùng không trả tiền cho cái họ ghét; nếu họ trả thì giả định lõi của vision sai. Spec không giải quyết mâu thuẫn này ở đâu cả.

  **Gõ lại cho tử tế:** định nghĩa ít nhất một tính năng premium phục vụ trực tiếp kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng lượt hiển thị), ghi rõ ở PRD-PREMIUM Overview cách premium tránh tái lập match-vanity. Không làm được thì nêu thẳng đây là rủi ro giả định lõi. *(DEC-worthy)*

- **[minor] PRD-EVENTS-E1-S3:18** — Đặc tả nguyên một hệ thống bán vé concert toàn quốc trong app hẹn hò (5 AC: danh sách theo nghệ sĩ/hạng vé, đặt tối đa 4 vé, giữ chỗ 10 phút, vé QR, lọc theo thể loại, dòng 18-22), size L. Spec tự ghi nhận gold-plating, đặt scope:out/could/later (41-48).

  **Banh nóc vì:** dán nhãn out vẫn không khử được chi phí. Một mảng bán vé cỡ L với AC đầy đủ vẫn ngốn chu kỳ review của PO, làm loãng tín hiệu trọng tâm cho đội build lẫn nhà đầu tư, và mời đầu tư sớm vào lĩnh vực (vận hành nghệ sĩ, an ninh đám đông) chẳng liên quan tới north-star.

  **Gõ lại cho tử tế:** giáng S3 xuống một dòng ý tưởng trong mục "tầm nhìn xa" của PRD-EVENTS thay vì story có AC đầy đủ. Chỉ nâng lại thành story khi north-star đã instrument và chứng minh, kèm DEC tường minh.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18 · PRD-CHAT-E1-S4:18** — AC kết quả không đo được ở cả hai story. (Xem Top 3 #3.)

- **[blocker] PRD-MATCH-E1-S2:21** — AC dòng 21 đặt kết quả A/B test thống kê (match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận story. A/B test cần lưu lượng lớn, thường mất nhiều tuần để đạt p < 0.05 — đây là chỉ số đo sau triển khai, không phải điều kiện bàn giao sprint.

  **Banh nóc vì:** coi AC này là cứng thì story treo vô hạn ở trạng thái "chờ dữ liệu"; bỏ qua thì AC thành cam kết trống. Cả hai đều làm bàn giao mất tính xác định.

  **Gõ lại cho tử tế:** tách hai phần: (1) story kỹ thuật giữ AC về lọc tiêu chí cứng, tỉ lệ hồ sơ active, thời gian tải; (2) story đo lường riêng "thiết lập A/B framework đo tỉ lệ match nhóm AI vs ngẫu nhiên, báo cáo sau N ngày với mẫu M", AC là "dashboard A/B có dữ liệu thực đọc được", không phải p < 0.05.

- **[major] PRD-MATCH-E1-S2:22** — AC dòng 22 yêu cầu tính năng giải thích gợi ý ("Vì sao gợi ý người này?", >= 2 tiêu chí khớp). PRD-AIREC:77 liệt kê tường minh tính năng này trong Won't this round. MATCH-E1-S2 là core-value/must/now; AIREC là in/could/later. Hai artifact xung đột trực tiếp trên cùng tính năng, không depends_on nào liên kết.

  **Banh nóc vì:** kỹ sư MATCH phải xây lớp giải thích trong khi AIREC, nơi nắm toàn bộ logic gợi ý, không xây nó cycle này. Story hoặc bị block chờ AIREC, hoặc tự tái triển khai ranking trong MATCH và đẻ ra hai code path song song.

  **Gõ lại cho tử tế:** bỏ AC dòng 22 khỏi MATCH-E1-S2; nếu cần thì chuyển thành story riêng trong PRD-AIREC (could/later) đúng với quyết định Won't ở AIREC:77; thêm depends_on: [PRD-AIREC] nếu AC nào phụ thuộc ranking của AIREC. *(DEC-worthy)*

- **[major] PRD-PREMIUM-E1-S1:20** — AC dòng 20 kiểm tra "giao dịch hoàn tất → mở khoá quyền xem trong 5 giây", giả định một luồng thanh toán đã tồn tại và trả về sự kiện "giao dịch hoàn tất". PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào Won't this round, không depends_on nào liên kết.

  **Banh nóc vì:** không payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm tra được trong môi trường tích hợp thực. Test phải mock cả luồng thanh toán và mất giá trị end-to-end. Khi chọn gateway sau, AC phải viết lại từ đầu.

  **Gõ lại cho tử tế:** thêm story/epic stub payment integration (dù chỉ placeholder), cho S1 phụ thuộc qua depends_on; sửa AC thành "giả sử gateway trả webhook xác nhận thành công, khi nhận webhook, hệ thống cập nhật trạng thái gói và mở khoá quyền trong 5 giây" để tách rõ ranh giới payment vs entitlement.

- **[major] PRD-SAFETY-E1-S1:21** — AC dòng 21 yêu cầu ảnh giấy tờ gốc bị xoá trong 24h sau xác minh và "không bao giờ hiển thị cho người khác", yêu cầu tuân thủ riêng tư gần GDPR retention, nhưng không cơ chế nào để QA/audit verify: không audit log, không API check, không retention policy reference.

  **Banh nóc vì:** không có cách test thụ động rằng ảnh đã thực sự bị xoá sau 24h. Cron job lỗi không xoá thì không ai biết cho đến lúc breach.

  **Gõ lại cho tử tế:** tách hai AC: (1) "khi truy vấn storage audit log sau 25h, record ảnh gốc của user không còn trong bucket và deletion event được ghi kèm timestamp"; (2) "khi admin truy vấn retention report, không ảnh giấy tờ nào created_at cũ hơn 25h còn trong storage"; thêm vào NFR PRD-SAFETY: deletion SLA 24h enforce bằng scheduled job, không on-demand.

- **[minor] PRD-AIREC-E1-S1:21** — AC dòng 21 đặt ngưỡng "20 hồ sơ đầu hiển thị trong 2 giây trên thiết bị di động phổ thông tại Việt Nam", không định nghĩa "thiết bị phổ thông" (CPU/RAM/OS), không percentile. Story size L, could/later, phụ thuộc mô hình ML chưa chọn.

  **Banh nóc vì:** không thiết bị tham chiếu thì không cấu hình nổi môi trường test, threshold không reproducible. Model thực chọn xong, 2 giây có thể bất khả thi nếu không có caching riêng.

  **Gõ lại cho tử tế:** định nghĩa hardware reference profile ở NFR PRD-AIREC (ví dụ Android tầm trung 2023+: Snapdragon 680, RAM 4 GB, 4G 20 Mbps) cùng percentile p95; sửa AC kèm điều kiện "scoring server-side và cache". Nếu chưa xác định được hardware trước khi chọn model thì bỏ AC khỏi delivery, chuyển thành spike/NFR.

### Market

- **[blocker] BRD:22** — BRD-G3 hoà vốn năm 2 mà không một con số unit-economics. (Xem Top 3 #2.) *(nguồn: Statista — thị trường ~6.44M USD/2025; Tinder conversion ~10.7%)*

- **[major] BRD:26** — Danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan, app hẹn hò tập trung người dùng châu Á đang mở rộng sang Đông Nam Á (ra mắt TanTan Tribe tại Singapore 12/2024, đang mở sang Malaysia, Thailand). Tantan chia sẻ đúng phân khúc người dùng châu Á mà spec coi là lợi thế.

  **Banh nóc vì:** Tantan đang chủ động tái định vị sang "kết nối châu Á có chiều sâu văn hoá". Nếu TanTan Tribe đẩy vào Việt Nam với định vị tương tự và tập người dùng châu Á lớn hơn, luận điểm "bản địa hoá" của spec bị xói mòn mà không có kịch bản phòng thủ nào.

  **Gõ lại cho tử tế:** thêm Tantan (và cân nhắc Facebook Dating) vào `competitors:` trong BRD với threat level rõ; cập nhật `competitive_parity` ở PRD-MATCH và PRD-SAFETY. *(nguồn: TanTan Tribe Singapore 12/2024)*

- **[major] PRD-MATCH:22** — Cơ chế lõi (khám phá, quẹt, tạo match hai chiều) đánh giá `parity` với Tinder, `behind` với Bumble. Đây là toàn bộ trải nghiệm năm 1: AI và premium đều `horizon: later`. Differentiator "đo bằng kết nối thật" không thể hiện bằng bất kỳ tính năng must/should nào trong now/next, chỉ là cam kết đo nội bộ.

  **Banh nóc vì:** người dùng không chọn app vì north-star nội bộ, họ chọn vì trải nghiệm khác biệt ngay khi dùng. Màn quẹt giống Tinder (parity), premium chưa có, AI chưa có thì không lý do hành vi nào để rời Tinder, vốn đang dẫn đầu top grossing Việt Nam với network effect lớn hơn.

  **Gõ lại cho tử tế:** xác định ít nhất một tính năng must/should trong now/next thể hiện "kết nối thật" mà người dùng cảm nhận ngay (icebreaker tự động sau match, giới hạn số match đồng thời, badge "đang nhắn tin"). Không có hook trải nghiệm thì tuyên bố định vị chỉ là copy marketing. *(nguồn: Similarweb 03/2026 — Tinder top grossing VN)*

### Craft

- **[major] PRD-MATCH-E1-S1:20** — AC dòng 20 "hệ thống tạo match và hiển thị thông báo match cho cả hai trong 5 giây" dùng "match" mơ hồ, không rõ thông báo gì, không nói điều kiện "cả hai cùng thích" xảy ra tức thì hay trễ, tính từ ai.

  **Banh nóc vì:** 5 giây tính từ lúc nào? Từ lần thích thứ hai của A, hay từ lúc B nhìn thấy match? AC giả định tức thì nhưng không rõ tức thì từ nhìn của ai.

  **Gõ lại cho tử tế:** "Khi cả hai phía cùng thích nhau, hệ thống tạo match và gửi push notification cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận."

- **[major] PRD-MATCH-E1-S1:19** — AC dòng 19 "cả hai phản hồi dưới 300ms", "phản hồi" mơ hồ (latency API? cập nhật UI? người dùng cảm nhận?), "ghi nhận" trừu tượng (lưu DB? gửi signal?).

  **Banh nóc vì:** QA/dev không biết đo từ điểm nào, touch tới lưu xong, hay touch tới UI cập nhật? Không điểm đo thì không kiểm chứng khách quan được.

  **Gõ lại cho tử tế:** "Quẹt phải: ghi nhận lượt thích (lưu DB); quẹt trái: ghi nhận bỏ qua (lưu DB). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc "...hoàn thành và hiển thị phản hồi UI, hồ sơ tiếp theo lên sân, trong 300ms").

- **[major] VISION:24,PRD-MATCH:31** — VISION:24 nêu vấn đề "hàng triệu match ảo không bao giờ dẫn tới cuộc trò chuyện thật"; PRD-MATCH:31 AC lại "khi cả hai cùng thích, hệ thống tạo match", story chỉ TẠO thêm match mà không cơ chế nào dẫn tới chat thật.

  **Banh nóc vì:** mâu thuẫn này gây hoài nghi thật sự. Story này giải quyết vấn đề core hay đang tái tạo chính nó? North-star là 7 ngày nhắn tin liên tục, AC chỉ yêu cầu tạo match. Cái match đó bị lãng quên ra sao thì spec im lặng.

  **Gõ lại cho tử tế:** thêm AC "khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu cuộc trò chuyện"; hoặc ghi rõ scope ở epic: "story này tạo match hai chiều; PRD-CHAT xử lý việc bắt đầu cuộc trò chuyện để biến match thành kết nối thật". *(trùng hướng với product PRD-MATCH-E1-S1:30, cùng một lỗ hổng match→chat nhìn từ góc craft)*

- **[minor] PRD-MATCH-E1-S1:29** — Khuôn User Story dùng nhãn cột tiếng Anh ("As a | I want | so that") kèm bản dịch tiếng Việt ("Với vai trò | Tôi muốn | để") trên cùng một dòng.

  **Banh nóc vì:** PO không kỹ thuật bị phân tán bởi nhãn kép, không rõ đọc tiếng Anh hay Việt. Phần Acceptance Criteria phía dưới không có nhãn kép nên dòng 28 thành ngoại lệ lạc lõng.

  **Gõ lại cho tử tế:** bỏ nhãn tiếng Anh ở dòng 28, dùng cấu trúc chỉ tiếng Việt (Với vai trò / Tôi muốn / Để) cho cân với phần "Tiêu chí chấp nhận".

- **[minor] PRD-MATCH-E1-S1:18** — AC dòng 18 "một chồng tối thiểu 10 hồ sơ gợi ý đã tải sẵn", "gợi ý" dùng như tính từ, trong khi toàn ancestry "gợi ý" là danh từ/động từ. "Hồ sơ gợi ý" không tự nhiên với tiếng Việt.

  **Banh nóc vì:** dễ hiểu nhầm "gợi ý" là một loại hồ sơ đặc biệt thay vì "hồ sơ được hệ thống gợi ý". Không nhất quán với "hồ sơ được gợi ý" ở Vision dòng 43.

  **Gõ lại cho tử tế:** "Khi mở màn hình khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

- không có

## Đáng ghi thành quyết định (DEC-worthy)

- **BRD:62** — north-star không được đo bởi bất kỳ metric/story nào: bổ sung sustained-7day-conversation-rate là một ruling về định vị và ưu tiên đo lường, mâu thuẫn ngầm với bộ metric đang chạy theo match-count. PO nên ghi DEC.
- **BRD:22** — bảng unit-economics và định nghĩa "hoà vốn" cho BRD-G3 là một ruling tài chính/scope cần PO chốt thành DEC.
- **PRD-PREMIUM:37** — premium dựng trên match-vanity mâu thuẫn trực diện với VISION:22-28: cần PO ra quyết định Keep/Change/Hybrid (định nghĩa lại gói premium phục vụ kết nối duy trì, hoặc chấp nhận rủi ro giả định lõi).
- **PRD-CHAT-E1-S4:18** — phạm vi "an toàn" trùng PRD-SAFETY: PO cần chốt xoá S4 hay thu hẹp, một ruling scope/DRY.
- **PRD-MATCH-E1-S2:22** — AC giải thích gợi ý mâu thuẫn với Won't this round đã ghi tại PRD-AIREC:77: PO chốt giữ Won't hay đảo quyết định (DEC).
