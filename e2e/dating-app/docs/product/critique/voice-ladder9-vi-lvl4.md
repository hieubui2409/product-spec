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
level: 4
---
# Critique: all  ·  level 4  ·  lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 3

## Top 3: sửa ngay

1. **[blocker][product] BRD:62** — North-star "số cặp duy trì nhắn tin >= 7 ngày" (PRODUCT.md:15, VISION:51) vắng mặt trong Success Metrics của BRD; cả bộ chỉ số chỉ đo MAU, weekly-match-rate, premium-conversion-rate, arpu, và mọi story đều bám match/quy mô -- đúng thứ VISION:45-52 nói muốn thoát. **Hỏng vì:** sản phẩm có thể cán 100k MAU, 20% match/tuần mà không một cặp nào trò chuyện thật. Differentiator duy nhất không được đo nên không chứng minh được, không tối ưu được; đội build sẽ tối ưu match-count y hệt đối thủ. Riskiest assumption của cả sản phẩm không có instrument nào kiểm chứng. **Sửa ngay:** thêm metric north-star tường minh vào BRD Success Metrics (vd sustained-7day-conversation-rate), gắn làm metric chính cho PRD-CHAT và ít nhất PRD-CHAT-E1-S1; xem lại BRD-G2 để thay weekly-match-rate bằng chỉ số kết nối duy trì, hoặc ghi rõ nó chỉ là leading indicator. *(DEC-worthy)*

2. **[blocker][tech] PRD-CHAT-E1-S3:18 + PRD-CHAT-E1-S4:18** — AC dùng kết quả không đo được: "trải nghiệm phải mượt mà", "nhanh và không giật lag" (S3:18-19), "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn" (S4:18-19). Không ngưỡng số, không thiết bị tham chiếu, không tiêu chí vượt/không vượt. **Hỏng vì:** không AC nào chuyển được thành test case thông/không thông. Kỹ sư không có điều kiện dừng để đóng sprint, QA không có ngưỡng để từ chối, story treo vô thời hạn hoặc bị tick done tùy tiện. **Sửa ngay:** thay bằng ngưỡng đo được -- S3: ">= 55 fps, không jank frame > 16 ms trong 100 frame liên tiếp khi cuộn/gõ trên Android tầm trung (RAM 3 GB)" và "mở cuộc trò chuyện 50 tin nhắn thì tương tác được trong 1,5 giây ở p95"; S4: liệt kê cơ chế cụ thể (cảnh báo link ngoài trước khi mở, quét CSAM trước khi lưu ảnh và từ chối với mã lỗi rõ).

3. **[blocker][market] BRD:22** — BRD-G3 đặt mục tiêu hòa vốn năm 2 từ premium nhưng cả spec không có con số nào: không mức giá, không tỉ lệ chuyển đổi mục tiêu, không ARPU, không ước tính chi phí vận hành. PRD-PREMIUM tự nhận là me-too đi sau Tinder và để `horizon: later`. **Hỏng vì:** thị trường hẹn hò online VN khoảng 6,44 triệu USD/năm 2025 (Statista); Tinder mất nhiều năm mới đạt chuyển đổi khoảng 10,7%. Tân binh 100k MAU x 3-5% chuyển đổi x giá khoảng 3-5 USD/tháng ra cỡ 15-25k USD MRR -- nếu chi phí cao hơn, BRD-G3 vỡ mà không có cơ chế cảnh báo sớm trong spec. **Sửa ngay:** thêm vào BRD một bảng unit-economics tối thiểu (giá gói VND/tháng, tỉ lệ chuyển đổi mục tiêu %, ARPU mục tiêu, ước tính chi phí vận hành năm 2); từ đó PRD-PREMIUM mới định nghĩa được "hòa vốn" là gì. *(DEC-worthy)*

## Theo lăng kính

### Product

- **[major] PRD-MATCH-E1-S1:30** — Story must/core-value của lõi, nhưng "so that" dừng ở "tạo match với người tôi quan tâm" và 4 AC (34-37) chỉ tới sự kiện tạo match + thông báo; metric gắn là weekly-match-rate (16). Không AC nào nối lượt thích tới mục tiêu trò chuyện duy trì. **Hỏng vì:** story đáy phễu của lõi tối ưu đúng cho "match ảo" mà VISION:45-52 chống. Lõi đo và thưởng cho tạo match thì mọi thiết kế hạ nguồn kéo về số match, không phải kết nối -- ra đúng sản phẩm Tinder mà spec nói không muốn xây. **Sửa ngay:** sửa "so that" + thêm AC nối tới hành trình kết nối (sau match dẫn thẳng vào luồng mở cuộc trò chuyện PRD-CHAT, ghi tín hiệu match-to-first-message), đổi metric story sang chỉ số kết nối duy trì. *(DEC-worthy)*

- **[major] PRD-CHAT-E1-S4:18** — "Nhắn tin an toàn tuyệt đối" có "so that" vòng tròn (28) và 2 AC không kiểm chứng được: "an toàn tuyệt đối", "bảo vệ người dùng hoàn toàn" (18-19). Phạm vi "an toàn" này trùng PRD-SAFETY (xác minh danh tính & chống lừa đảo), vốn là PRD core-value riêng. **Hỏng vì:** AC "tuyệt đối/hoàn toàn" không done được -- đội build không biết khi nào xong, QA không có gì kiểm, story trượt vô hạn hoặc bị tick tùy tiện. Nhân đôi phạm vi an toàn phá vỡ một-nhà-chứa-một-sự-thật, dẫn tới yêu cầu mâu thuẫn giữa hai PRD. **Sửa ngay:** xóa S4, dồn phạm vi an toàn về PRD-SAFETY; hoặc thu hẹp S4 thành job cụ thể của nhắn tin (chặn/báo cáo người trong cuộc trò chuyện) với AC đếm được (báo cáo gửi được, người bị chặn không gửi tin được trong X giây).

- **[major] PRD-PREMIUM:37** — Premium bán doanh thu lõi (BRD-G3) bằng đúng bộ cơ chế match-count mà sản phẩm tuyên bố chống: "xem ai đã thích mình", boost hồ sơ, thích không giới hạn (37-38); PRD tự nhận là me-too đi sau Tinder ngang Bumble (42-45). **Hỏng vì:** động cơ doanh thu duy nhất hướng tới hòa vốn được xây trên incentive quẹt-vô-tận/đếm-lượt-thích -- đúng pain mà VISION:22-28 nói khiến người Việt chán app phương Tây. Pain đó thật thì người dùng mục tiêu không trả tiền cho thứ họ ghét; họ trả thì giả định lõi của vision sai. Value proposition premium chưa ánh xạ tới gain/pain nào trong vision. **Sửa ngay:** định nghĩa ít nhất một gói/tính năng premium phục vụ trực tiếp kết nối duy trì (tăng tốc tìm người nghiêm túc, không phải tăng lượt hiển thị), ghi rõ trong PRD-PREMIUM Overview cách premium tránh tái lập match-vanity; không làm được thì nêu thẳng đây là rủi ro giả định lõi. *(DEC-worthy)*

- **[minor] PRD-EVENTS-E1-S3:18** — Đặc tả hệ thống bán vé concert toàn quốc trong app hẹn hò (5 AC: danh sách concert theo nghệ sĩ/hạng vé, đặt tối đa 4 vé, giữ chỗ 10 phút, vé QR, lọc thể loại -- 18-22), cỡ L. Spec đã tự ghi nhận gold-plating/solution-first (41-48) và đặt scope:out/could/later. **Hỏng vì:** dù gắn nhãn out/could, một mảng bán vé cỡ L với AC đầy đủ vẫn tiêu chu kỳ review của PO, làm loãng tín hiệu trọng tâm cho đội build và nhà đầu tư, mời gọi đầu tư sớm vào lĩnh vực (vận hành nghệ sĩ, an ninh đám đông) không đo north-star. **Sửa ngay:** giáng S3 xuống một dòng ý tưởng một câu trong mục "tầm nhìn xa" của PRD-EVENTS; chỉ nâng lại thành story khi north-star đã instrument và chứng minh, kèm quyết định PO tường minh so với north-star. *(DEC-worthy)*

### Tech

- **[blocker] PRD-MATCH-E1-S2:21** — AC đặt kết quả A/B test thống kê (match cao hơn 20%, p < 0.05) làm tiêu chí chấp nhận story. A/B test trên người dùng thật cần lưu lượng lớn, thường mất nhiều tuần để đạt p < 0.05 -- đây là chỉ số sau triển khai, không phải điều kiện bàn giao sprint. **Hỏng vì:** story không đóng được cuối sprint vì kết quả A/B test chưa có khi bàn giao. Coi là AC cứng thì story treo "chờ dữ liệu"; bỏ qua thì AC thành cam kết trống -- cả hai làm bàn giao mất tính xác định. **Sửa ngay:** tách hai phần -- (1) story kỹ thuật giữ AC về lọc tiêu chí cứng, tỉ lệ hồ sơ active, thời gian tải (kiểm tra được tại bàn giao); (2) story đo lường riêng "thiết lập A/B test framework, báo cáo sau N ngày với mẫu M người dùng", AC là "dashboard A/B test có dữ liệu thực và đọc được" thay vì p < 0.05.

- **[major] PRD-MATCH-E1-S2:22** — AC yêu cầu tính năng giải thích gợi ý ("Vì sao gợi ý người này?", >= 2 tiêu chí khớp), nhưng PRD-AIREC:77 liệt kê tường minh tính năng này trong Won't this round ("cân nhắc cycle sau"). S2 là core-value/must/now; AIREC là in/could/later. Hai artifact xung đột trực tiếp trên cùng tính năng, không depends_on nào liên kết. **Hỏng vì:** kỹ sư làm S2 phải xây lớp giải thích nhưng AIREC -- nơi nắm logic gợi ý -- không xây trong cycle này. Story hoặc bị block (chờ AIREC) hoặc tự tái triển khai logic gợi ý trong MATCH, đẻ ra hai code path song song. **Sửa ngay:** loại AC dòng 22 khỏi S2; nếu cần, chuyển thành story riêng trong PRD-AIREC (could/later) khớp quyết định Won't tại AIREC:77; thêm depends_on: [PRD-AIREC] vào S2 nếu AC nào phụ thuộc logic ranking của AIREC. *(DEC-worthy)*

- **[major] PRD-PREMIUM-E1-S1:20** — AC kiểm tra "giao dịch hoàn tất thì quyền xem mở khóa trong 5 giây", giả định một luồng thanh toán đã tồn tại trả về sự kiện "giao dịch hoàn tất". Nhưng PRD-PREMIUM:78 đặt tích hợp cổng thanh toán vào Won't this round, và không depends_on nào trong chuỗi PRD-PREMIUM -> E1 -> S1 liên kết tới story thanh toán nào. **Hỏng vì:** không payment gateway thì không có sự kiện "giao dịch hoàn tất", AC không kiểm tra được trong môi trường tích hợp thực. Test phải mock toàn bộ payment flow, mất giá trị end-to-end; khi gateway chọn sau, story phải viết lại AC và kiểm lại từ đầu. **Sửa ngay:** thêm story/epic stub payment integration (dù chỉ placeholder) và để S1 depends_on tới đó; sửa AC thành "giả sử payment gateway trả webhook xác nhận thành công, khi nhận webhook thì hệ thống cập nhật trạng thái gói và mở khóa quyền xem trong 5 giây" -- tách rõ ranh giới payment vs entitlement layer.

- **[major] PRD-SAFETY-E1-S1:21** — AC yêu cầu ảnh giấy tờ gốc bị xóa khỏi lưu trữ trong 24 giờ sau xác minh và "không bao giờ hiển thị cho người khác" (gần tương đương GDPR retention), nhưng không xác định cơ chế nào để QA/audit verify: không audit log, không API check, không retention policy reference. **Hỏng vì:** không có cách test thụ động từ phía user/QA rằng ảnh đã thật sự bị xóa sau 24 giờ. Có sự cố (cron job lỗi không xóa) thì không ai biết cho đến khi breach. AC cần một acceptance path quan sát được mới thật sự testable. **Sửa ngay:** tách hai AC -- (1) "truy vấn storage audit log sau 25 giờ thì record ảnh giấy tờ của user không còn trong bucket và deletion event được ghi với timestamp"; (2) "admin truy vấn retention report thì không ảnh giấy tờ nào created_at cũ hơn 25 giờ còn trong storage"; thêm vào NFR PRD-SAFETY: deletion SLA 24h được enforce bởi scheduled job, không phải on-demand.

- **[minor] PRD-AIREC-E1-S1:21** — AC đặt ngưỡng "20 hồ sơ đầu hiển thị trong 2 giây trên thiết bị di động phổ thông tại VN" nhưng không định nghĩa "phổ thông" (CPU tier, RAM, OS) và không percentile. Story size L, could/later, phụ thuộc mô hình ML chưa chọn. **Hỏng vì:** không thiết bị tham chiếu thì không cấu hình được môi trường test, threshold không reproducible. Khi mô hình ML thực được chọn và đo latency, 2 giây có thể không khả thi nếu không có caching riêng; kỹ sư không size chính xác được khi cả hardware lẫn model đều chưa xác định. **Sửa ngay:** định nghĩa hardware reference profile tại NFR PRD-AIREC (vd Android tầm trung 2023+: Snapdragon 680 hoặc tương đương, RAM 4 GB, 4G 20 Mbps) + percentile p95; sửa AC thành "tải màn khám phá trên thiết bị reference thì 20 hồ sơ đầu hiển thị trong 2 giây ở p95, với scoring server-side và kết quả được cache"; không xác định được hardware trước khi chọn model thì chuyển AC này thành spike/NFR kiểm tra sau.

### Market

- **[major] BRD:26** — Danh sách đối thủ (Tinder, Bumble, Hẹn, Fika) bỏ sót Tantan -- app hẹn hò tập trung người dùng châu Á đang mở sang ĐNÁ (ra mắt TanTan Tribe tại Singapore 12/2024, đang mở sang Malaysia, Thailand). Tantan có mặt trong các danh sách app hẹn hò VN hiện tại và chia sẻ đúng phân khúc người dùng châu Á mà spec coi là lợi thế. **Hỏng vì:** Tantan đang chủ động tái định vị sang "kết nối châu Á có chiều sâu văn hóa". Nếu Tantan Tribe đẩy vào VN với định vị tương tự và sẵn tập người dùng châu Á lớn hơn, luận điểm "bản địa hóa" của spec bị xói mòn mà không có kịch bản phòng thủ. **Sửa ngay:** thêm Tantan (và cân nhắc Facebook Dating) vào `competitors:` trong BRD với threat level rõ; cập nhật `competitive_parity` trong PRD-MATCH và PRD-SAFETY để phản ánh vị thế so với đối thủ này. *(nguồn: TanTan Tribe Singapore launch 12/2024)*

- **[major] PRD-MATCH:22** — Cơ chế lõi (khám phá, quẹt thích/bỏ qua, tạo match hai chiều) được đánh giá `parity` với Tinder, `behind` Bumble. Đây là toàn bộ trải nghiệm năm 1 -- AI gợi ý và premium đều `horizon: later`. Điểm khác biệt VISION tuyên bố ("đo bằng kết nối thật") không thể hiện bằng tính năng `must/should` nào trong `now/next`; chỉ là cam kết đo lường nội bộ, không phải trải nghiệm người dùng cảm nhận được. **Hỏng vì:** người dùng không chọn app vì north-star metric nội bộ, họ chọn vì trải nghiệm khác biệt ngay khi dùng. Màn quẹt giống Tinder (parity), premium chưa có, AI chưa có thì không lý do hành vi nào để rời Tinder sang -- nhất là khi Tinder đang dẫn đầu top grossing VN (Similarweb 3/2026) với network effect lớn hơn nhiều. **Sửa ngay:** xác định ít nhất một tính năng `must/should` trong `now/next` thể hiện khác biệt "kết nối thật" cảm nhận được ngay (icebreaker tự động sau match, giới hạn số match đồng thời, hoặc badge "đang nhắn tin"); không có hook trải nghiệm rõ thì tuyên bố định vị chỉ là marketing copy. *(nguồn: Similarweb top grossing VN 3/2026)*

### Craft

- **[major] PRD-MATCH-E1-S1:20** — AC "hệ thống tạo match và hiển thị thông báo match cho cả hai trong vòng 5 giây": "thông báo match" dùng "match" như danh từ nhưng không rõ thông báo gì cụ thể, và không nói điều kiện "cả hai phía cùng thích" xảy ra cách nào (tức thì hay có độ trễ). **Hỏng vì:** không rõ hành vi hệ thống -- A và B thích cùng lúc hay đã thích từ trước thì thông báo gửi bao giờ, 5 giây tính từ đâu, tức thì từ nhìn của ai. **Sửa ngay:** "Khi cả hai phía cùng thích nhau, hệ thống tạo match và gửi thông báo push cho cả hai trong vòng 5 giây kể từ lần thích thứ hai được ghi nhận" -- rõ loại thông báo (push) và điểm tính thời gian.

- **[major] PRD-MATCH-E1-S1:19** — AC "quẹt phải ghi nhận lượt thích; quẹt trái ghi nhận bỏ qua; cả hai phản hồi dưới 300ms": "phản hồi" không rõ là thời gian xử lý API, hiển thị UI, hay người dùng cảm nhận; "ghi nhận" trừu tượng (lưu DB? gửi signal?). **Hỏng vì:** QA/dev không rõ cách đo "phản hồi dưới 300ms" -- từ touch đến lưu xong, hay đến khi UI cập nhật? Không kiểm chứng khách quan được nếu không định nghĩa điểm đo. **Sửa ngay:** "Quẹt phải: ghi nhận lượt thích (lưu vào database); quẹt trái: ghi nhận bỏ qua (lưu vào database). Cả hai hoàn thành trong 300ms tính từ lúc người dùng nhả tay khỏi màn hình" (hoặc "hoàn thành và hiển thị phản hồi UI -- hồ sơ tiếp theo lên sân -- trong 300ms").

- **[major] VISION:24, PRD-MATCH:31** — "hàng triệu match ảo không bao giờ dẫn tới cuộc trò chuyện thật" là problem statement ở VISION:24, nhưng PRD-MATCH:31 AC lại nói "khi cả hai phía cùng thích, hệ thống tạo match" -- story này TẠO thêm match mà không cơ chế nào kéo nó tới trò chuyện thật. **Hỏng vì:** mâu thuẫn gây hoài nghi story có thật sự giải quyết vấn đề core hay đang tạo ra chính nó (match ảo). North-star (VISION:51) là cặp duy trì nhắn tin >= 7 ngày nhưng AC chỉ yêu cầu tạo match -- match này rồi bị lãng quên thế nào. **Sửa ngay:** thêm AC "khi match được tạo, cả hai nhận thông báo và được dẫn tới màn nhắn tin để bắt đầu cuộc trò chuyện"; hoặc nếu nhắn tin thuộc PRD-CHAT thì ghi rõ scope ở epic "story này: tạo match hai chiều; tiếp nối: PRD-CHAT biến match thành kết nối thật". *(Lưu ý: trùng hướng với PRD-MATCH-E1-S1:30 ở lăng kính Product; cùng một lỗi gốc -- lõi tạo match nhưng không nối tới trò chuyện.)*

- **[minor] PRD-MATCH-E1-S1:29** — Khuôn User Story dùng tiêu đề cột tiếng Anh ("As a | I want | so that") rồi bản dịch tiếng Việt ("Với vai trò | Tôi muốn | để"): một dòng hai cặp nhãn, một Anh một Việt. **Hỏng vì:** PO không kỹ thuật bị phân tán bởi nhãn kép, không rõ đọc Anh hay Việt; các phần sau (Acceptance Criteria) không có nhãn kép nên dòng 29 thành ngoại lệ. **Sửa ngay:** bỏ nhãn tiếng Anh, chỉ giữ cấu trúc tiếng Việt (**Với vai trò / Tôi muốn / Để**) cho cân bằng với phần "Tiêu chí chấp nhận" bên dưới.

- **[minor] PRD-MATCH-E1-S1:18** — AC dùng "một chồng tối thiểu 10 hồ sơ gợi ý đã tải sẵn": "gợi ý" ở đây làm tính từ, nhưng trong toàn ancestry "gợi ý" thường là danh từ/động từ ("đưa gợi ý", "chất lượng gợi ý"); "hồ sơ gợi ý" là cấu trúc không tự nhiên với tiếng Việt. **Hỏng vì:** dễ hiểu nhầm "gợi ý" là một loại hồ sơ đặc biệt thay vì "hồ sơ được hệ thống gợi ý"; không nhất quán với Vision (dòng 43: "hồ sơ được gợi ý"). **Sửa ngay:** "Khi mở màn hình khám phá, người dùng thấy một chồng tối thiểu 10 hồ sơ được gợi ý và đã tải sẵn" -- khớp cách dùng "được gợi ý" ở Vision.

## Lặp lại từ lần trước

Không có (không có prior_reports).

## Đáng ghi thành quyết định (DEC-worthy)

- **BRD:62** — north-star không nằm trong Success Metrics: PO cần ra quyết định bổ sung metric kết nối duy trì và hạ cấp weekly-match-rate. Đây là ruling về cách đo thành công của cả sản phẩm.
- **PRD-MATCH-E1-S1:30 / PRD-PREMIUM:37** -- lõi và động cơ doanh thu tối ưu cho match-count, mâu thuẫn trực tiếp với VISION:45-52 (artifact định vị). Cần quyết định Keep/Change/Hybrid: hoặc đổi positioning, hoặc nối lõi+premium tới north-star.
- **BRD:22** -- không có unit-economics cho BRD-G3 (hòa vốn năm 2). PO cần ghi quyết định về giả định giá / tỉ lệ chuyển đổi / chi phí.
- **PRD-EVENTS-E1-S3:18** -- giữ hay giáng story bán vé cỡ L; ruling về scope so với north-star.
- **PRD-MATCH-E1-S2:22** -- xung đột tính năng giải thích gợi ý với quyết định Won't tại PRD-AIREC:77; PO cần ra ruling artifact nào nắm tính năng này.

---

Unresolved: market lens dẫn vài nguồn ngoài (Statista, Similarweb 3/2026, TanTan Tribe) chưa kèm URL trong findings gốc -- nên verify nguồn trước khi dùng số trong quyết định đầu tư.
