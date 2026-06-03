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
level: 2
---
# Critique: all · level 2 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 3

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** Core value và north-star của sản phẩm là "số cặp đôi duy trì nhắn tin qua lại >= 7 ngày" (PRODUCT.md:15, VISION:51), nhưng Success Metrics của BRD (BRD:62-65) chỉ liệt kê MAU-monthly, weekly-match-rate, premium-conversion-rate, ARPU. Không story nào mang chỉ số north-star; mọi story bám MAU-monthly hoặc weekly-match-rate, đúng các "con số match/quy mô" mà VISION:45-52 nói thẳng là muốn thoát. Vấn đề nằm ở: sản phẩm có thể đạt "thành công" theo bộ chỉ số của chính nó (100k MAU, 20% match/tuần) mà vẫn thất bại ở lý do tồn tại vì không cặp nào trò chuyện thật. Differentiator duy nhất so với Tinder/Bumble không được đo, nên cũng không chứng minh được, không tối ưu được; đội build sẽ tối ưu cho match-count y hệt đối thủ. Hướng sửa: thêm metric north-star tường minh vào BRD Success Metrics (ví dụ sustained-7day-conversation-rate), gắn làm metric chính cho PRD-CHAT và ít nhất PRD-CHAT-E1-S1; xem lại BRD-G2 để thay weekly-match-rate bằng chỉ số kết nối duy trì, hoặc nêu rõ match-rate chỉ là leading indicator. *(DEC-worthy)*

2. **[blocker][market] BRD:22** BRD-G3 đặt mục tiêu hoà vốn vận hành năm 2 từ doanh thu premium, nhưng cả spec không có con số nào: không mức giá gói, không tỉ lệ chuyển đổi mục tiêu, không ARPU, không ước tính chi phí vận hành. PRD-PREMIUM tự nhận là me-too đi sau Tinder. Vấn đề nằm ở: thị trường hẹn hò online Việt Nam ước ~6.44M USD năm 2025 (Statista); Tinder đạt tỉ lệ chuyển đổi ~10.7% sau nhiều năm có network effect. Một tân binh 100k MAU, chuyển đổi thực tế 3-5% ở mức giá ~3-5 USD/tháng, chỉ tạo ~15-25k USD MRR. Nếu chi phí cao hơn, BRD-G3 vỡ mà không có cơ chế cảnh báo sớm. Hướng sửa: thêm vào BRD một bảng unit-economics tối thiểu (mức giá gói VND/tháng, tỉ lệ chuyển đổi mục tiêu %, ARPU, ước tính chi phí vận hành năm 2); từ đó PRD-PREMIUM mới định nghĩa được "hoà vốn" là gì. *(DEC-worthy)*

3. **[blocker][tech] PRD-MATCH-E1-S2:21** AC dòng 21 đặt kết quả A/B test thống kê (tỉ lệ match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận của story. Đây là chỉ số đo sau triển khai, cần lưu lượng lớn và nhiều tuần để đạt p < 0.05, không phải điều kiện bàn giao sprint. Vấn đề nằm ở: story không thể đóng cuối sprint vì chưa có dữ liệu A/B. Coi là điều kiện cứng thì treo vô thời hạn ở trạng thái "chờ dữ liệu"; bỏ qua thì AC thành cam kết trống. Cả hai đều khiến bàn giao không còn xác định được. Hướng sửa: tách story làm hai. (1) Story kỹ thuật giữ AC kiểm tra được tại bàn giao (lọc tiêu chí cứng, tỉ lệ hồ sơ active, thời gian tải). (2) Story đo lường riêng "thiết lập A/B test framework đo tỉ lệ match nhóm AI vs ngẫu nhiên, báo cáo sau N ngày với mẫu M người dùng", AC là "dashboard A/B có dữ liệu thực, đọc được", không phải p < 0.05.

## Theo lăng kính

### Product

- **[major] PRD-MATCH-E1-S1:30** Story must/core-value của lõi, nhưng "so that" dừng ở "để tôi có thể tạo match" (dòng 30) và 4 AC (34-37) chỉ kết thúc ở sự kiện tạo match kèm thông báo; metric gắn [weekly-match-rate] (dòng 16). Không AC nào nối lượt thích tới cuộc trò chuyện duy trì. Vấn đề nằm ở: story đáy phễu tối ưu đúng cho "match ảo" mà VISION:45-52 chống lại; mọi thiết kế hạ nguồn sẽ kéo về số match, không phải kết nối thật. Hướng sửa: sửa "so that" và thêm AC nối tới hành trình kết nối (sau match dẫn thẳng vào luồng mở chat PRD-CHAT; ghi tín hiệu match-to-first-message), đổi metric sang chỉ số kết nối duy trì.

- **[major] PRD-CHAT-E1-S4:18** Story "Nhắn tin an toàn tuyệt đối" có "so that" vòng tròn (dòng 28) và 2 AC không kiểm chứng được: "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn" (18-19). Phạm vi "an toàn" trùng với PRD-SAFETY (core-value riêng). Vấn đề nằm ở: AC không đo được thì story không bao giờ done; phạm vi an toàn nhân đôi với PRD-SAFETY phá vỡ một-nhà-chứa-một-sự-thật, dễ sinh yêu cầu mâu thuẫn giữa hai PRD. Hướng sửa: xoá S4 dồn phạm vi an toàn về PRD-SAFETY, hoặc thu hẹp S4 thành job cụ thể của nhắn tin (chặn/báo cáo người trong chat) với AC đếm được. *(DEC-worthy)*

- **[major] PRD-PREMIUM:37** PRD-PREMIUM bán doanh thu lõi (BRD-G3) bằng đúng bộ cơ chế match-count mà sản phẩm tuyên bố chống: "xem ai đã thích mình", boost hồ sơ, thích không giới hạn (37-38); PRD tự nhận là me-too (42-45). Vấn đề nằm ở: động cơ doanh thu duy nhất hướng hoà vốn được xây trên incentive quẹt-vô-tận, đúng pain mà VISION:22-28 nói là lý do người Việt chán app phương Tây. Value proposition của premium chưa ánh xạ tới gain hay pain nào trong vision. Hướng sửa: định nghĩa ít nhất một gói/tính năng premium phục vụ kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng hiển thị), ghi rõ trong PRD-PREMIUM Overview cách premium tránh tái lập match-vanity; nếu không thể, nêu thẳng đây là rủi ro giả định lõi. *(DEC-worthy)*

- **[minor] PRD-EVENTS-E1-S3:18** Đặc tả hệ thống bán vé concert toàn quốc trong app hẹn hò (5 AC, kích cỡ L); spec đã tự ghi nhận gold-plating và đặt scope:out/could/later (41-48). Vấn đề nằm ở: dù gắn nhãn out, một story cỡ L với AC đầy đủ vẫn tiêu chu kỳ review của PO, làm loãng trọng tâm cho đội build lẫn nhà đầu tư, và mời đầu tư sớm vào lĩnh vực không đo north-star. Hướng sửa: giáng S3 xuống một dòng ý tưởng trong mục "tầm nhìn xa" của PRD-EVENTS thay vì story có AC đầy đủ; chỉ nâng lại khi north-star đã instrument và có số thực, kèm DEC tường minh.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18** Cả hai AC dùng kết quả không đo được: "trải nghiệm phải mượt mà" (18), "hiển thị nhanh không giật lag" (19); PRD-CHAT-E1-S4 (18-19) cùng lỗi với "an toàn tuyệt đối". Không ngưỡng số, không thiết bị tham chiếu, không % thất bại cho phép. Vấn đề nằm ở: không AC nào chuyển được thành test thông/không thông; kỹ sư không có definition of done, QA không có ngưỡng để từ chối, story để ngỏ vô thời hạn hoặc đóng theo cảm tính. Hướng sửa: thay bằng ngưỡng đo được. S3: "cuộn/gõ trên Android tầm trung (RAM 3 GB), frame rate >= 55 fps, không jank frame > 16 ms trong 100 frame liên tiếp" và "mở chat 50 tin, tương tác được trong 1,5 giây ở p95". S4: liệt kê cơ chế bảo vệ cụ thể (cảnh báo link ngoài trước khi mở, quét CSAM trước khi lưu ảnh).

- **[major] PRD-MATCH-E1-S2:22** AC dòng 22 yêu cầu tính năng giải thích gợi ý ("Vì sao gợi ý người này?", >= 2 tiêu chí khớp), nhưng PRD-AIREC:77 liệt kê tính năng này trong Won't this round. MATCH-E1-S2 là core-value/must/now; AIREC là in/could/later. Hai artifact xung đột trực tiếp, không có depends_on. Vấn đề nằm ở: kỹ sư phải xây lớp giải thích nhưng AIREC, nơi nắm logic gợi ý, không xây trong cycle này; story bị block hoặc tự tái triển khai logic, tạo hai code path song song. Hướng sửa: loại AC dòng 22 khỏi MATCH-E1-S2; nếu cần thì chuyển thành story trong PRD-AIREC (could/later) cho phù hợp với quyết định Won't tại AIREC:77; thêm depends_on: [PRD-AIREC] nếu AC nào phụ thuộc ranking của AIREC. *(DEC-worthy)*

- **[major] PRD-PREMIUM-E1-S1:20** AC dòng 20 kiểm tra "giao dịch hoàn tất thì mở khoá quyền xem trong 5 giây", giả định luồng thanh toán đã tồn tại, nhưng PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào Won't this round; không có depends_on tới story thanh toán nào. Vấn đề nằm ở: không có payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm tra được trong môi trường tích hợp thực; mock toàn bộ payment flow làm mất giá trị end-to-end; chọn gateway sau phải viết lại AC. Hướng sửa: thêm story/epic stub payment integration và đặt S1 depends_on tới đó; sửa AC thành "giả sử gateway trả webhook xác nhận thành công, khi nhận webhook thì hệ thống cập nhật trạng thái gói và mở khoá quyền xem trong 5 giây", tách rõ ranh giới payment vs entitlement.

- **[major] PRD-SAFETY-E1-S1:21** AC dòng 21 yêu cầu ảnh giấy tờ gốc bị xoá trong 24 giờ sau xác minh và "không bao giờ hiển thị cho người khác" (gần tương đương GDPR retention), nhưng không có cơ chế nào để QA/audit verify: không audit log, không API check, không retention policy. Vấn đề nằm ở: QA không có cách test rằng ảnh thực sự bị xoá sau 24 giờ; nếu cron job lỗi không ai biết cho tới khi breach. Hướng sửa: tách hai AC. (1) "Truy vấn storage audit log sau 25 giờ, record ảnh không còn trong bucket, deletion event ghi trong audit trail kèm timestamp." (2) "Admin truy vấn retention report, không ảnh nào created_at cũ hơn 25 giờ còn trong storage." Thêm NFR PRD-SAFETY: deletion SLA 24h enforce bằng scheduled job.

- **[minor] PRD-AIREC-E1-S1:21** AC dòng 21 đặt ngưỡng "20 hồ sơ đầu hiển thị trong 2 giây trên thiết bị di động phổ thông tại Việt Nam", nhưng không định nghĩa "thiết bị phổ thông" (CPU/RAM/OS) và không có percentile; story size L, could/later, phụ thuộc mô hình ML chưa chọn. Vấn đề nằm ở: không thiết bị tham chiếu thì không cấu hình được môi trường test, ngưỡng không reproducible; khi chọn mô hình ML thực, 2 giây có thể bất khả thi nếu thiếu caching. Hướng sửa: định nghĩa hardware reference profile ở NFR PRD-AIREC (ví dụ Android tầm trung 2023+, Snapdragon 680, RAM 4 GB, 4G 20 Mbps) kèm p95; sửa AC bám profile đó với điều kiện scoring server-side và cache; nếu chưa xác định được hardware trước khi chọn mô hình, chuyển AC thành spike/NFR kiểm tra sau.

### Market

- **[major] BRD:26** Danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan, app hẹn hò tập trung người dùng châu Á đang mở sang Đông Nam Á (TanTan Tribe ra mắt Singapore 12/2024, đang mở rộng sang Malaysia, Thailand). Tantan chia sẻ đúng phân khúc người dùng châu Á mà spec xác định là lợi thế. Vấn đề nằm ở: Tantan đang tái định vị sang "kết nối châu Á có chiều sâu văn hoá"; nếu Tribe đẩy mạnh vào Việt Nam với định vị tương tự và tập người dùng lớn hơn, luận điểm "bản địa hoá" của spec bị xói mòn mà không có kịch bản phòng thủ. Hướng sửa: thêm Tantan (cân nhắc cả Facebook Dating) vào `competitors:` trong BRD kèm threat level; cập nhật `competitive_parity` trong PRD-MATCH và PRD-SAFETY. *(source: TanTan Tribe Singapore launch 12/2024)*

- **[major] PRD-MATCH:22** Cơ chế lõi (khám phá, quẹt, tạo match) được đánh giá `parity` Tinder và `behind` Bumble, đây là toàn bộ trải nghiệm năm 1 (AI và premium đều `later`). Điểm khác biệt VISION ("đo bằng kết nối thật") không thể hiện bằng tính năng `must/should` nào trong `now/next`; chỉ là cam kết đo lường nội bộ. Vấn đề nằm ở: người dùng không chọn app vì north-star nội bộ mà vì trải nghiệm khác biệt ngay khi dùng; nếu màn quẹt giống Tinder, premium/AI chưa có, không có lý do hành vi nào để rời Tinder (đang dẫn đầu top grossing VN, Similarweb 3/2026). Hướng sửa: xác định ít nhất một tính năng `must/should` trong `now/next` thể hiện "kết nối thật" cảm nhận được ngay (icebreaker tự động sau match, giới hạn số match đồng thời, badge "đang nhắn tin"). *(source: Similarweb top grossing VN 3/2026; Statista)*

### Craft

- **[major] PRD-MATCH-E1-S1:20** AC dòng 20 "hệ thống tạo match và hiển thị thông báo match cho cả hai trong vòng 5 giây" dùng "thông báo match" mơ hồ và không nêu điều kiện "cả hai phía cùng thích" xảy ra tức thì hay có độ trễ, tính từ góc nhìn của ai. Vấn đề nằm ở: hành vi hệ thống không rõ; nếu A và B thích cùng lúc hay A đã thích từ trước thì thông báo gửi khi nào, 5 giây tính từ đâu, AC không kiểm chứng khách quan được. Hướng sửa: "Khi cả hai phía cùng thích nhau, hệ thống tạo match và gửi thông báo push cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận."

- **[major] PRD-MATCH-E1-S1:19** AC dòng 19 "cả hai phản hồi dưới 300ms" dùng "phản hồi" mơ hồ (API? UI? cảm nhận người dùng?) và "ghi nhận" trừu tượng (lưu DB? gửi signal?). Vấn đề nằm ở: QA/dev không rõ cách đo "dưới 300ms", tính từ touch tới lưu xong hay tới UI cập nhật; tiêu chuẩn không kiểm chứng khách quan được nếu thiếu điểm đo. Hướng sửa: "Quẹt phải: ghi nhận lượt thích (lưu vào database); quẹt trái: ghi nhận bỏ qua (lưu vào database). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc nêu rõ phía UI: hiển thị hồ sơ tiếp theo).

- **[major] VISION:24, PRD-MATCH:31** "Hàng triệu match ảo không bao giờ dẫn tới cuộc trò chuyện thật" là problem statement ở VISION:24, nhưng AC PRD-MATCH:31 lại tạo thêm match mà không có cơ chế nào dẫn nó về chat thật. Vấn đề nằm ở: mâu thuẫn này gây hoài nghi story có giải quyết vấn đề core hay đang tái tạo chính nó; nếu north-star là "duy trì nhắn tin >= 7 ngày" mà AC chỉ tạo match thì match bị lãng quên. Hướng sửa: thêm AC "khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu cuộc trò chuyện"; hoặc nếu chat là PRD khác thì rõ ràng hoá scope ở epic ("story này: tạo match hai chiều; tiếp nối: PRD-CHAT biến match thành kết nối thật").

- **[minor] PRD-MATCH-E1-S1:29** Khuôn mẫu User Story dùng nhãn cột tiếng Anh ("As a | I want | so that") kèm bản dịch tiếng Việt ("Với vai trò | Tôi muốn | để"), tạo nhãn tiêu đề kép trên một dòng. Vấn đề nằm ở: PO không kỹ thuật bị phân tán vì nhãn kép; không rõ nên đọc tiếng Anh hay Việt. Phần Acceptance Criteria không có nhãn kép nên dòng 28 thành ngoại lệ. Hướng sửa: bỏ nhãn tiếng Anh ở dòng 28, dùng cấu trúc chỉ tiếng Việt (Với vai trò / Tôi muốn / Để) cho cân bằng với phần "Tiêu chí chấp nhận".

- **[minor] PRD-MATCH-E1-S1:18** AC dòng 18 dùng "hồ sơ gợi ý" (gợi ý làm tính từ), trong khi toàn ancestry "gợi ý" thường là danh từ hay động từ; "hồ sơ gợi ý" không tự nhiên trong tiếng Việt. Vấn đề nằm ở: dễ hiểu nhầm "gợi ý" là loại hồ sơ đặc biệt thay vì "hồ sơ được gợi ý"; không nhất quán với Vision (dòng 43 "hồ sơ được gợi ý"). Hướng sửa: "Khi mở màn hình khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

Không có (prior_reports rỗng).

## Đáng ghi thành quyết định (DEC-worthy)

- **[product] BRD:62** Thêm hay không một north-star metric (sustained-7day-conversation-rate) vào BRD và đổi BRD-G2 khỏi weekly-match-rate là quyết định về định hướng đo lường, đụng tới artifact đã có; PO nên ghi thành DEC.
- **[product] PRD-CHAT-E1-S4:18** Xoá S4 dồn về PRD-SAFETY hay thu hẹp phạm vi là quyết định về scope/ranh giới PRD; ghi DEC để không tái tranh luận.
- **[product] PRD-PREMIUM:37** Chấp nhận hay phủ nhận mô hình premium match-vanity là quyết định positioning lõi mâu thuẫn với VISION; PO nên record.
- **[tech] PRD-MATCH-E1-S2:22** Gỡ tính năng giải thích gợi ý khỏi MATCH (theo Won't tại PRD-AIREC:77) là quyết định về scope giữa hai PRD; ghi DEC.

## Unresolved

Một số dòng tham chiếu (VISION:51, PRODUCT.md:15, PRD-AIREC:77) chỉ được trích trong evidence của lens, chưa được kiểm chứng lại độc lập; nếu cần độ chắc, đối chiếu lại trước khi PO ký DEC.
