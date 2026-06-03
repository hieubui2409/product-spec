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
level: 3
---
# Critique: all · level 3 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 4

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** -- north-star của sản phẩm là "số cặp đôi duy trì nhắn tin qua lại >= 7 ngày" (PRODUCT.md:15, VISION:51), nhưng Success Metrics của BRD chỉ liệt kê MAU, weekly-match-rate, premium-conversion-rate, arpu. Không một chỉ số nào đo cuộc trò chuyện duy trì 7 ngày. Không story nào mang chỉ số north-star. **Toang ở đâu:** sản phẩm có thể đạt "thành công" theo bộ chỉ số của nó -- 100k MAU, 20% match/tuần -- mà vẫn chết đúng ở lý do tồn tại: không cặp nào trò chuyện thật. Differentiator duy nhất so với Tinder/Bumble không được đo nên không thể chứng minh, không thể tối ưu; đội build sẽ kéo match-count y hệt đối thủ. **Sửa:** thêm metric north-star tường minh vào BRD Success Metrics (ví dụ sustained-7day-conversation-rate), gắn làm metric chính cho PRD-CHAT và story PRD-CHAT-E1-S1; xem lại BRD-G2 để thay weekly-match-rate hoặc ghi rõ nó chỉ là leading indicator.

2. **[blocker][tech] PRD-MATCH-E1-S2:21** -- AC đặt kết quả A/B test thống kê (tỉ lệ match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận story. A/B test trên người dùng thật cần lưu lượng đủ lớn, thường mất nhiều tuần để đạt p < 0.05. Đây là chỉ số đo sau triển khai, không phải điều kiện bàn giao sprint. **Toang ở đâu:** story không thể đóng cuối sprint vì chưa có dữ liệu A/B test. Coi AC này là cứng thì story treo vô thời hạn ở trạng thái "chờ dữ liệu"; bỏ qua thì AC thành cam kết trống. Cả hai đều phá tính xác định của bàn giao. **Sửa:** tách thành hai story -- (1) story kỹ thuật giữ AC kiểm tra được tại bàn giao (lọc tiêu chí cứng, tỉ lệ hồ sơ active, thời gian tải); (2) story đo lường riêng với AC là "dashboard A/B test có dữ liệu thực và kết quả đọc được", không phải p < 0.05.

3. **[blocker][market] BRD:22** -- BRD-G3 đặt mục tiêu hoà vốn vận hành năm 2 từ doanh thu premium, nhưng cả spec không có một con số nào: không mức giá gói, không tỉ lệ chuyển đổi mục tiêu, không ARPU, không ước tính chi phí vận hành. **Toang ở đâu:** thị trường hẹn hò online Việt Nam khoảng 6.44M USD năm 2025 (Statista); Tinder đạt chuyển đổi ~10.7% sau nhiều năm network effect. Tân binh 100k MAU với chuyển đổi thực tế 3-5% ở mức giá ~3-5 USD/tháng chỉ ra ~15-25k USD MRR. Nếu chi phí cao hơn, BRD-G3 vỡ -- mà spec không có cơ chế cảnh báo sớm nào. **Sửa:** thêm vào BRD bảng unit-economics tối thiểu (mức giá VND/tháng, tỉ lệ chuyển đổi mục tiêu, ARPU mục tiêu, ước tính chi phí vận hành năm 2); từ đó PRD-PREMIUM mới định nghĩa được "hoà vốn" là gì.

## Theo lăng kính

### Product

- **[blocker] BRD:62** (xem Top 3 #1): north-star không có gì để đo, mọi story gắn match-count. **Toang ở đâu:** riskiest assumption của cả sản phẩm không có cách kiểm chứng. **Sửa:** thêm metric sustained-7day-conversation-rate, gắn vào PRD-CHAT.

- **[major] PRD-MATCH-E1-S1:30**: story must/core-value của lõi, nhưng "so that" dừng ở "để tạo match" và 4 AC chỉ kết thúc ở tạo match + thông báo; metric gắn weekly-match-rate. Không AC nào nối lượt thích tới mục tiêu trò chuyện duy trì. **Toang ở đâu:** story đáy phễu tối ưu đúng cho "match ảo" -- cái mà VISION:45-52 tuyên bố chống. Mọi quyết định hạ nguồn sẽ kéo về số match, không phải kết nối thật. **Sửa:** sửa "so that" và thêm AC nối tới luồng mở cuộc trò chuyện PRD-CHAT (ghi tín hiệu match→first-message), đổi metric sang chỉ số kết nối duy trì.

- **[major] PRD-CHAT-E1-S4:18**: "so that" vòng tròn (muốn an toàn để yên tâm) và 2 AC không kiểm chứng được ("an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn"); phạm vi an toàn trùng PRD-SAFETY. **Toang ở đâu:** AC không đo được thì không thể done -- đội build không biết khi nào xong, QA không có gì kiểm, story trượt vô hạn hoặc tick done tuỳ tiện; nhân đôi phạm vi an toàn phá một-nhà-chứa-một-sự-thật. **Sửa:** xoá S4 dồn về PRD-SAFETY, hoặc thu hẹp thành job cụ thể (chặn/báo cáo người trong cuộc trò chuyện) với AC đếm được. *(DEC-worthy: ranh giới scope S4 vs PRD-SAFETY)*

- **[major] PRD-PREMIUM:37**: bán doanh thu lõi (BRD-G3) bằng đúng cơ chế match-count ("xem ai đã thích mình", boost hồ sơ, thích không giới hạn) mà sản phẩm tuyên bố chống; PRD tự nhận me-too. **Toang ở đâu:** động cơ doanh thu duy nhất hướng hoà vốn xây trên incentive quẹt-vô-tận -- đúng pain VISION:22-28 nói người Việt chán app phương Tây. Nếu pain thật, người dùng không trả tiền cho cái họ ghét; nếu họ trả, giả định lõi của vision sai. **Sửa:** định nghĩa ít nhất một tính năng premium phục vụ kết nối duy trì, ghi rõ trong PRD-PREMIUM Overview cách premium tránh tái lập match-vanity; nếu không thể, nói thẳng đây là rủi ro giả định lõi. *(DEC-worthy)*

- **[minor] PRD-EVENTS-E1-S3:18**: đặc tả hệ thống bán vé concert toàn quốc cỡ L (5 AC đầy đủ) trong app hẹn hò; spec đã tự ghi nhận gold-plating và đặt scope out/could/later. **Toang ở đâu:** dù gắn nhãn out, một story cỡ L với AC đầy đủ vẫn tiêu thụ chu kỳ review của PO, làm loãng tín hiệu trọng tâm, mời đầu tư sớm vào lĩnh vực không đo north-star. **Sửa:** giáng S3 xuống một dòng ý tưởng trong mục "tầm nhìn xa" của PRD-EVENTS; chỉ nâng lại thành story khi north-star đã instrument, kèm DEC tường minh. *(DEC-worthy)*

### Tech

- **[blocker] PRD-CHAT-E1-S3:18** (S4 cùng lỗi): cả hai AC dùng kết quả không đo được ("trải nghiệm mượt mà", "hiển thị nhanh không giật lag"; S4: "an toàn tuyệt đối"). Không ngưỡng số, không thiết bị tham chiếu, không phần trăm thất bại. **Toang ở đâu:** không AC nào chuyển được thành test case thông/không thông; kỹ sư không có definition of done, QA không có ngưỡng từ chối, sản phẩm không bao giờ "xong". **Sửa:** thay bằng ngưỡng đo được -- S3: "cuộn/gõ trên Android tầm trung RAM 3GB, frame rate >= 55 fps, không jank frame > 16ms trong 100 frame"; "mở cuộc trò chuyện 50 tin, tương tác được trong 1,5s ở p95". S4: liệt kê cơ chế bảo vệ cụ thể (cảnh báo link ngoài, quét CSAM trước khi lưu).

- **[blocker] PRD-MATCH-E1-S2:21** (xem Top 3 #2). **Sửa:** tách story kỹ thuật khỏi story đo lường A/B.

- **[major] PRD-MATCH-E1-S2:22**: AC yêu cầu tính năng giải thích gợi ý (hiển thị >= 2 tiêu chí khớp), nhưng PRD-AIREC:77 liệt kê đúng tính năng này trong "Won't this round". MATCH là core-value/must/now; AIREC là could/later. Hai artifact xung đột trực tiếp, không có depends_on liên kết. **Toang ở đâu:** kỹ sư MATCH phải xây lớp giải thích nhưng AIREC -- nơi nắm logic gợi ý -- không xây trong cycle này; story bị block hoặc tự tái triển khai logic, tạo hai code path song song. **Sửa:** bỏ AC:22 khỏi MATCH-E1-S2; nếu cần, chuyển thành story trong PRD-AIREC (could/later) khớp với quyết định Won't; thêm depends_on: [PRD-AIREC] nếu có AC phụ thuộc ranking của AIREC. *(DEC-worthy: contradiction với Won't đã ghi tại PRD-AIREC:77)*

- **[major] PRD-PREMIUM-E1-S1:20**: AC giả định luồng thanh toán trả về "giao dịch hoàn tất", nhưng PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào "Won't this round"; không depends_on nào liên kết tới story thanh toán. **Toang ở đâu:** không payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm tra được trong môi trường tích hợp thực; test phải mock toàn bộ payment flow, mất giá trị end-to-end; khi chọn gateway sau phải viết lại AC. **Sửa:** thêm story/epic stub payment integration và depends_on; sửa AC thành "giả sử payment gateway trả webhook xác nhận, khi nhận webhook, hệ thống cập nhật trạng thái gói và mở khoá quyền xem trong 5s" -- tách rõ ranh giới payment vs entitlement.

- **[major] PRD-SAFETY-E1-S1:21**: AC yêu cầu xoá ảnh giấy tờ gốc trong 24h sau xác minh và "không bao giờ hiển thị cho người khác" (gần tương đương GDPR retention), nhưng không có cơ chế nào để QA/audit verify: không audit log, không API check, không retention policy. **Toang ở đâu:** không cách nào test từ phía người dùng/QA rằng ảnh đã thực sự bị xoá; nếu cron job lỗi không ai biết tới khi breach. **Sửa:** tách hai AC quan sát được -- (1) "truy vấn storage audit log sau 25h, record ảnh không còn trong bucket và có deletion event với timestamp"; (2) "admin truy vấn retention report, không ảnh giấy tờ nào created_at cũ hơn 25h"; thêm NFR: deletion SLA 24h enforce bởi scheduled job.

- **[minor] PRD-AIREC-E1-S1:21**: ngưỡng "20 hồ sơ đầu hiển thị trong 2 giây trên thiết bị di động phổ thông tại Việt Nam" -- không định nghĩa "thiết bị phổ thông" (CPU/RAM/OS), không percentile; story phụ thuộc mô hình ML chưa chọn. **Toang ở đâu:** không thiết bị tham chiếu thì không cấu hình được môi trường test, threshold không reproducible; khi chọn model thực, 2s có thể bất khả thi nếu không có caching. **Sửa:** định nghĩa hardware reference profile tại NFR PRD-AIREC (ví dụ Snapdragon 680, RAM 4GB, 4G 20Mbps) và p95; sửa AC kèm điều kiện "scoring server-side và kết quả được cache"; nếu chưa xác định được hardware, chuyển thành spike/NFR.

### Market

- **[blocker] BRD:22** (xem Top 3 #3): BRD-G3 hoà vốn năm 2 không có unit-economics. Nguồn: Statista (thị trường ~6.44M USD 2025), tỉ lệ chuyển đổi Tinder ~10.7%. **Sửa:** thêm bảng unit-economics tối thiểu vào BRD.

- **[major] BRD:26**: danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan -- app hẹn hò tập trung người dùng châu Á đang mở sang Đông Nam Á (TanTan Tribe ra mắt Singapore 12/2024, đang mở Malaysia/Thailand). **Toang ở đâu:** Tantan đang tái định vị sang "kết nối châu Á có chiều sâu văn hoá" với tập người dùng châu Á lớn hơn; nếu đẩy vào Việt Nam, luận điểm "bản địa hoá" của spec bị xói mòn mà không có kịch bản phòng thủ. **Sửa:** thêm Tantan (cân nhắc Facebook Dating) vào `competitors:` với threat level rõ; cập nhật `competitive_parity` trong PRD-MATCH và PRD-SAFETY.

- **[major] PRD-MATCH:22**: cơ chế lõi (khám phá, quẹt, tạo match hai chiều) được đánh giá `parity` Tinder, `behind` Bumble -- là toàn bộ trải nghiệm năm 1 (AI và premium đều later). Differentiator "kết nối thật" của VISION không thể hiện bằng tính năng must/should nào trong now/next, chỉ là cam kết đo lường nội bộ. **Toang ở đâu:** người dùng không chọn app vì north-star nội bộ mà vì trải nghiệm khác biệt ngay khi dùng. Nếu màn quẹt giống Tinder, premium chưa có, AI chưa có, không có lý do hành vi để rời Tinder -- đang dẫn top grossing Việt Nam (Similarweb 3/2026). **Sửa:** xác định ít nhất một tính năng must/should trong now/next thể hiện "kết nối thật" cảm nhận được ngay (icebreaker tự động sau match, giới hạn match đồng thời, badge "đang nhắn tin").

### Craft

- **[major] PRD-MATCH-E1-S1:20**: AC "tạo match và hiển thị thông báo match cho cả hai trong vòng 5 giây" -- "thông báo match" không rõ là gì, không rõ điều kiện "cả hai cùng thích" tức thì hay có độ trễ, 5 giây tính từ ai. **Toang ở đâu:** không rõ hành vi hệ thống; thông báo gửi bao giờ, mốc 5 giây nghĩa gì, tức thì từ nhìn của ai. **Sửa:** "Khi cả hai phía cùng thích, hệ thống tạo match và gửi push cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận."

- **[major] PRD-MATCH-E1-S1:19**: AC "cả hai phản hồi dưới 300ms" -- "phản hồi" không rõ là latency API, thời gian UI, hay người dùng cảm nhận; "ghi nhận" trừu tượng. **Toang ở đâu:** QA/dev không rõ cách đo "dưới 300ms", không kiểm chứng khách quan được. **Sửa:** "Quẹt phải: ghi nhận lượt thích (lưu DB); quẹt trái: ghi nhận bỏ qua (lưu DB). Cả hai hoàn thành trong 300ms tính từ lúc nhả tay khỏi màn hình" (hoặc "...và hiển thị phản hồi UI trong 300ms").

- **[major] VISION:24, PRD-MATCH:31**: "hàng triệu match ảo không bao giờ dẫn tới cuộc trò chuyện thật" là problem statement ở VISION:24, nhưng PRD-MATCH:31 tạo thêm match mà không có cơ chế nào dẫn tới trò chuyện thật. **Toang ở đâu:** mâu thuẫn này đặt dấu hỏi story có giải quyết core hay đang tái tạo đúng vấn đề; nếu north-star là duy trì 7 ngày nhưng AC chỉ tạo match, match sẽ bị bỏ quên. **Sửa:** thêm AC "Khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu trò chuyện", hoặc ghi rõ scope ở epic (story này: tạo match hai chiều; tiếp nối: PRD-CHAT biến match thành kết nối thật).

- **[minor] PRD-MATCH-E1-S1:29**: khuôn User Story dùng nhãn cột tiếng Anh ("As a | I want | so that") rồi bản dịch Việt ("Với vai trò | Tôi muốn | để") -- nhãn kép gây mất cân bằng khi đọc, các phần sau (AC) không có nhãn kép. **Toang ở đâu:** PO không kỹ thuật bị phân tán bởi nhãn kép, không rõ đọc tiếng Anh hay Việt, dòng 28 thành ngoại lệ. **Sửa:** bỏ nhãn tiếng Anh, dùng cấu trúc chỉ tiếng Việt (Với vai trò / Tôi muốn / Để) cho cân bằng với phần "Tiêu chí chấp nhận".

- **[minor] PRD-MATCH-E1-S1:18**: AC dùng "một chồng tối thiểu 10 hồ sơ gợi ý đã tải sẵn" -- "gợi ý" làm tính từ trong khi ancestry thường dùng làm danh từ/động từ; "hồ sơ gợi ý" không tự nhiên với tiếng Việt. **Toang ở đâu:** dễ hiểu nhầm "gợi ý" là loại hồ sơ đặc biệt thay vì "hồ sơ được hệ thống gợi ý"; không nhất quán với "hồ sơ được gợi ý" ở Vision:43. **Sửa:** "Khi mở màn khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn."

## Lặp lại từ lần trước

- không có (prior_reports: none).

## Đáng ghi thành quyết định (DEC-worthy)

- **PRD-CHAT-E1-S4 vs PRD-SAFETY** -- ranh giới scope an toàn nhắn tin (xoá S4 hay thu hẹp): PO cần ra một quyết định, vì nó định lại phạm vi giữa hai PRD core-value.
- **PRD-PREMIUM:37** -- premium có được phép dựa trên cơ chế match-vanity mà vision phủ nhận không: ruling positioning/scope binding với BRD-G3 và VISION.
- **PRD-MATCH-E1-S2:22 vs PRD-AIREC:77** -- AC giải thích gợi ý mâu thuẫn trực tiếp với quyết định "Won't this round" đã ghi tại AIREC; cần PO ra quyết định giữ/đổi (đây là contradiction với phạm vi đã chốt).
- **PRD-EVENTS-E1-S3** -- giữ ở mức story đầy đủ AC hay giáng xuống ý tưởng: quyết định ưu tiên/scope so với north-star.
