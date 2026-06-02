Now I have what I need. Let me apply both passes to the critique.

**Pass 1: mark the AI-tells in the draft.**

Issues spotted:
- "nghe nghiêm túc về bảo mật" is fine, keep it.
- "nghe thuyết phục nhưng" is fine, natural Vietnamese.
- Several sentences start with near-identical rhythms ("Vấn đề nằm ở:" always introduces a long compound sentence).
- "tính từ đang giả vờ làm yêu cầu kỹ thuật" is sharp, keep it.
- "Cached verdict gọi INVEST 'pass' nhưng đó là đánh giá structural; còn đây là Estimable thật" contains a semicolon that works fine (not an em dash).
- "không phải 'nếu' mà là 'khi nào'" is a negative parallelism ("not X but Y") pattern. Worth flattening.
- "sẽ vi phạm" vs. "có thể vi phạm" is hedging.
- "không có gì để test" is colloquial and sharp, keep it.
- The repeated label formula "Vấn đề nằm ở:" / "Hướng sửa:" is required structure, don't touch it.
- "Đây là phụ thuộc ẩn:" and "Đây là attack vector sybil rõ ràng" both read human, keep them.
- A few "một cách" or "nhằm mục đích" to watch for -- scanning... none found explicitly, but "được" passive constructions are heavy in places.
- "Giả sử" is the standard Given/When/Then phrasing, keep.
- The preamble before the `#` heading is just loose prose from the consolidator. It should either be dropped (it reads like meta-narration) or absorbed.
- The opening "No PRD-SAFETY findings... Now I'll consolidate." is pure consolidator process narration, not part of the critique. It must go.
- Sentence rhythm: many sentences in "Vấn đề nằm ở" blocks are uniformly long. Need one short punch before the explanation.
- "không phải 'nếu' mà là 'khi nào'" = negative parallelism, rephrase.
- "Cached verdict gọi INVEST 'pass' nhưng đó là đánh giá structural; còn đây là Estimable thật dựa trên nội dung kỹ thuật" is jargon-dense but factually grounded; simplify rhythm slightly.
- No em/en dashes found in the body. Good.
- "Đây là sự cố trust chứ không phải feature an toàn" is punchy, keep.

**Pass 2: rewrite.**

# Critique: PRD-SAFETY  ·  level 2  ·  lenses: tech, craft  [thiếu: product, market]

> Bảng severity: blocker 2 · major 2 · minor 3

## Top 3: sửa ngay

1. **[blocker][tech] PRD-SAFETY-E1-S1:345**, AC1 cam kết trả kết quả trong 60 giây nhưng cả PRD lẫn story không có một dòng nào về dịch vụ đối chiếu khuôn mặt hay liveness API, không vendor, không `depends_on`, không integration contract. Đây là phụ thuộc ẩn: người viết giả định một hệ thống phức tạp đã có sẵn và chỉ cần gọi ra là chạy. **Vấn đề nằm ở:** story không giao độc lập được. Đội phát triển mở file ra mà không biết gọi API nào, tích hợp vendor nào, xử lý timeout của bên thứ ba ra sao. Con số SLA 60 giây vô nghĩa khi chưa cam kết vendor nào; liveness trả về sau 90 giây thì spec im lặng. **Hướng sửa:** thêm vào PRD-SAFETY một AC hoặc NFR tường minh về loại tích hợp (in-house model hay third-party vendor), timeout phải xử lý (ví dụ "nếu không trả kết quả trong 60 giây, hiển thị lỗi có thể thử lại"), và thêm `depends_on: [vendor-selection-decision]` vào frontmatter S1. Vendor chưa chọn thì story phải ở trạng thái blocked, không phải draft-ready.

2. **[blocker][tech] PRD-SAFETY-E1-S1:348**, AC4 nói "ảnh giấy tờ gốc bị xoá khỏi lưu trữ trong vòng 24 giờ", nghe nghiêm túc nhưng không có gì để test. QA viết assertion gì, dựa vào đâu: storage bucket check, audit log, hay deletion event? Spec im lặng về observable outcome. **Vấn đề nằm ở:** không có evidence thì đây không phải AC, đây là lời hứa. Đội kiểm thử không nghiệm thu được vì không biết "xoá thành công" trông thế nào từ phía hệ thống. Với dữ liệu sinh trắc học của người Việt, "xoá rồi nhưng không ai xác nhận" có thể vi phạm Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân. **Hướng sửa:** viết lại AC4 thành "Giả sử xác minh thành công, khi 24 giờ trôi qua, thì hệ thống ghi một deletion event vào audit log (kèm timestamp và storage reference), ảnh không còn truy xuất được qua bất kỳ API nào, và deletion event này kiểm tra được bởi kiểm duyệt viên nội bộ." Thêm NFR: "Audit log xoá ảnh giấy tờ lưu tối thiểu 90 ngày phục vụ kiểm tra tuân thủ." `DEC-worthy`

3. **[major][tech+craft] PRD-SAFETY:270 (và craft PRD-SAFETY:75)**, NFR gói toàn bộ yêu cầu phi chức năng cho một luồng dữ liệu sinh trắc học vào một câu rưỡi: "ảnh được xử lý an toàn, không lộ cho người dùng khác; hoạt động trên thiết bị di động phổ thông." PRD này `scope: core-value`, `moscow: must`, xử lý ảnh khuôn mặt và CMND, nhóm dữ liệu nhạy cảm nhất có trong sản phẩm. NFR không nhắc encryption-at-rest, TLS, SLA hàng đợi kiểm duyệt, hay chuyện gì xảy ra khi liveness không khả dụng. **Vấn đề nằm ở:** "an toàn" là tính từ, không phải yêu cầu kỹ thuật. Đội phát triển không biết "an toàn" nghĩa là AES-256, TLS 1.3, hay chỉ cần không ai nhìn thấy màn hình. Khi có sự cố rò rỉ ảnh CMND của hàng trăm nghìn người Việt (và sự cố này sẽ xảy ra, câu hỏi chỉ là khi nào), spec không cung cấp baseline bảo mật nào để truy trách nhiệm hay phòng thủ pháp lý. **Hướng sửa:** thêm vào NFR tối thiểu bốn điểm: (1) "Ảnh selfie và giấy tờ mã hoá AES-256 khi lưu trữ, chỉ truyền qua TLS 1.3+, không lưu trên client sau upload"; (2) "Dịch vụ đối chiếu khuôn mặt uptime SLA 99.5%; khi không khả dụng, luồng xác minh trả lỗi rõ và cho thử lại sau tối đa 1 giờ"; (3) "Hàng đợi kiểm duyệt xử lý bởi người trong tối đa 48 giờ làm việc"; (4) "Toàn bộ luồng dữ liệu sinh trắc học tuân thủ Nghị định 13/2023/NĐ-CP." `DEC-worthy`

## Theo lăng kính

### Tech

- **[major][tech] PRD-SAFETY-E1-S2:390**, AC3 dùng "5 báo cáo lừa đảo độc lập" để kích hoạt auto-hide. "Độc lập" nghe thuyết phục nhưng spec không định nghĩa theo tiêu chí kỹ thuật nào: cùng thiết bị, cùng IP, hay cùng tài khoản đã xác minh? Một tính từ đang giả vờ làm yêu cầu kỹ thuật. **Vấn đề nằm ở:** năm tài khoản từ cùng một IP ẩn bất kỳ hồ sơ nào họ muốn. Đây là attack vector sybil rõ ràng. QA không viết được test case cho "độc lập" vì không biết hệ thống phân biệt bằng gì. Hồ sơ hợp lệ bị ẩn oan, người dùng bị loại khỏi khám phá không lý do, đây là sự cố trust chứ không phải feature an toàn. **Hướng sửa:** định nghĩa tường minh trong AC3: "Giả sử một hồ sơ nhận từ 5 báo cáo lừa đảo, mỗi báo cáo từ một tài khoản đã xác minh khác nhau, IP khác nhau, chênh lệch thời gian tối thiểu 5 phút giữa hai báo cáo liên tiếp, khi đạt ngưỡng, thì hồ sơ bị ẩn khỏi khám phá và đánh dấu ưu tiên kiểm duyệt." Thêm NFR: "Hồ sơ bị auto-hide phải kiểm duyệt thủ công trong tối đa 24 giờ; không có kết quả thì khôi phục tự động."

- **[minor][tech] PRD-SAFETY-E1-S2:383**, story S2 gán `size: S` nhưng bốn AC đòi bốn subsystem riêng: UI báo cáo phía client, backend ghi hàng đợi trong 10 giây, logic đếm ngưỡng và auto-hide theo thời gian thực, dedup 24 giờ per-user per-profile. **Vấn đề nằm ở:** estimate S nhưng chứa bốn concern kỹ thuật thì sprint planning thành trò đoán số. Threshold engine gặp race condition hay dedup store cần Redis thì story phình thành M hoặc L, sprint vỡ. Đây là Estimable thật dựa trên nội dung kỹ thuật, không phải structural check. **Hướng sửa:** tách S2 thành S2a "Gửi báo cáo và xác nhận" (UI + ingestion, size S, gồm AC1+AC2+AC4) và S2b "Ngưỡng auto-hide hồ sơ bị báo cáo" (threshold engine + ưu tiên kiểm duyệt, size M, gồm AC3). S2b cần `depends_on: [S2a]` tường minh. S2a ship trước khi threshold logic sẵn sàng.

### Craft

- **[minor][craft] PRD-SAFETY:41**, "north-star" là thuật ngữ tiếng Anh lẫn vào câu tiếng Việt ở một khái niệm quan trọng, làm mất tính thống nhất ngôn ngữ. **Vấn đề nằm ở:** khi truyền đạt lại cho PO hoặc dịch tài liệu, khái niệm này dễ bị hiểu không rõ hoặc giải thích lại không nhất quán. **Hướng sửa:** thay "north-star kết nối thật" bằng "Sao Bắc Đẩu kết nối thật" (lấy thuật ngữ Việt từ vision.md hoặc định nghĩa tạm cụ thể).

- **[minor][craft] PRD-SAFETY:58, S1:30, S1:35**, "huy hiệu" (badge) và "đã xác minh" dùng xen kẽ cho cùng một khái niệm, tạo mơ hồ nhỏ. **Vấn đề nằm ở:** nếu UI copy hoặc kiểm duyệt tìm theo từ khoá, sự không nhất quán này dẫn tới mô tả UI lệch với spec. **Hướng sửa:** chuẩn hoá một thuật ngữ, chọn 'huy hiệu "đã xác minh"' (badge kèm nhãn rõ) và dùng nhất quán qua toàn bộ tài liệu.

> Lưu ý: tech `PRD-SAFETY:270` và craft `PRD-SAFETY:75` cùng bắt lỗi NFR "an toàn" rỗng nghĩa nên đã gộp lên Top 3 (#3). Lăng kính market và product không có dữ liệu trong vòng này.

## Lặp lại từ lần trước

Không có. Báo cáo critique trước (c1-all-lvl3.md) chỉ chạm tới PRD-MATCH, không đụng PRD-SAFETY, nên đây là lần đầu các lỗi này được nêu.

## Đáng ghi thành quyết định (DEC-worthy)

**PRD-SAFETY-E1-S1:348 (AC4 xoá ảnh) và PRD-SAFETY:270 (NFR bảo mật).** Cả hai chạm tới tuân thủ Nghị định 13/2023/NĐ-CP cho dữ liệu sinh trắc học. Baseline bảo mật (mã hoá, audit log xoá, thời hạn lưu log) và mức cam kết tuân thủ là ruling ràng buộc PO nên ghi lại qua `--decision`, vì nó định ra nghĩa vụ pháp lý cho cả luồng xác minh chứ không chỉ một câu AC.
