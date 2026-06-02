Now I'll do a careful pass through the critique for every AI-tell:
- Em/en dashes (none visible in the text, but I'll check)
- Banned vocabulary: "crucial", "leverage", "highlight", "enhance", "align", "key", "landscape", "pivotal", "showcase", "underscore", "valuable", "vibrant", "intricate", "interplay", "delve", "foster", "garner", "seamless", "comprehensive"
- Vietnamese translation tells: "đảm bảo rằng", "nhằm mục đích", "một cách", "tận dụng", "tối ưu hóa"
- Forced triples, filler, signposting, passive voice

Reading through the input carefully. Let me note the issues:

1. "gói gọn trong" (Top 3 #1) - natural enough
2. "phục vụ" repetition - fine
3. "Toang ở đâu / Sửa" - level-3 labels, must keep
4. The preamble "Dedup analysis... Now let me draft." - this is consolidator scaffolding noise, not part of the report, should be stripped
5. "nối thẳng tới" - fine
6. "ghi rõ" - fine
7. The structure looks clean of em/en dashes
8. "đảm bảo" appears at PRD-MATCH:68 NFR section implicitly via the fix text - let me check... "đảm bảo 5 giây" - actually "không đảm bảo 5 giây" in the tech finding - this is in quotes describing the spec behavior, not the report's own prose, so it's fine
9. "tận dụng" - not present
10. Check "một cách" - not present
11. Check "nhằm mục đích" - not present
12. Check banned English words: "crucial" - not present. "leverage" - not present. "highlight" - not present. "align" - "aligned" appears at BRD-G2:66 finding but it's a verbatim frontmatter value, must keep. "enhance" - not present. "showcase" - not present. "underscore" - not present. "key" (adj) - not present in problematic usage. "landscape" - not present. "pivotal" - not present.
13. The preamble "Level 3 confirmed: why-label... Now let me draft." should be stripped - it's consolidator internal monologue leaking into the report.
14. "việc" nominalization - not present in obvious form
15. Rhythm check: most paragraphs are dense blocks. Could vary more but the findings are inherently detailed. The existing rhythm isn't obviously robotic - it has natural Vietnamese flow.
16. "đóng vai trò" - not present
17. "nó đóng vai trò như" - not present
18. "sống còn" used twice (BRD:85 and DEC section) - "sống còn" is a natural Vietnamese term, not a translation tell
19. "định vị" used a few times for "positioning" - natural
20. "không một PRD nào" - natural

The main issue is the preamble that must be stripped. Let me also check for any hidden stiffness or patterns I might have missed with a closer read of each section.

Looking at "Đặt tên một unfair advantage cụ thể" - mixing English "unfair advantage" in Vietnamese text. This is common in Vietnamese product/startup vocabulary and natural here, not a tell.

"zero bằng chứng" - mixing English, same, natural in this context.

"ARPU bằng 0 là bài toán không có nghiệm" - punchy and good.

"cold-start" - standard loan term, fine.

"pool zero-user chết vì cold-start" - natural startup Vietnamese.

The text is mostly clean. The one clear fix is stripping the consolidator scaffolding from the top. I'll also make small rhythm and naturalness improvements where the prose reads slightly stiff, and remove the word "đảm bảo" from the fix for S2 in tech section where I spot it.

Let me re-read the tech section fix for S2: "đảm bảo rằng" - not present. "đảm bảo" appears in "không đảm bảo 5 giây" but that's describing spec behavior. Fine.

One more check: "nhằm" - appears? No. "một cách" - no. "việc + verb nominalization" - "việc đăng nhập" style - I see "việc này" not used. Good.

I'll now produce the cleaned version, removing the preamble scaffolding and fixing any remaining stiffness:

---

# Critique: all · level 3 · lenses: product, tech, market, craft

> Bảng đếm mức độ: blocker 5 · major 6 · minor 3

## Top 3: sửa ngay

1. **[blocker][product · market] PRD-MATCH:307, PRD-MATCH:302.** Cycle 1 gói gọn trong "khám phá hồ sơ, quẹt thích/bỏ qua, tạo match" -- đúng cái vòng lặp quẹt vô tận mà VISION:38 thề từ bỏ -- và PRD tự khai `competitive_parity` chỉ "parity" với Tinder (PRD-MATCH:303). Bạn dựng lại đúng cỗ máy match ảo rồi dán nhãn "bước đầu tiên tới kết nối thật". Lõi sản phẩm ship lần này không khác Tinder một dòng AC nào.

Wait, the original uses "→" arrows as separators between the body, the "Toang" block, and the "Sửa" block. These are not em dashes; they are directional arrows used as labels. They're part of the level-3 structure. Keep them.

Also I notice the original uses "→ **Toang ở đâu:**" and "→ **Sửa:**" - these arrows are the level label markers, not em-dashes. Fine.

Let me produce the final output now, clean:

---

# Critique: all · level 3 · lenses: product, tech, market, craft

> Bảng đếm mức độ: blocker 5 · major 6 · minor 3

## Top 3: sửa ngay

1. **[blocker][product · market] PRD-MATCH:307, PRD-MATCH:302.** Cycle 1 gói gọn trong "khám phá hồ sơ, quẹt thích/bỏ qua, tạo match", đúng cái vòng lặp quẹt vô tận mà VISION:38 thề từ bỏ, và PRD tự khai `competitive_parity` chỉ "parity" với Tinder (PRD-MATCH:303). Bạn dựng lại đúng cỗ máy match ảo rồi dán nhãn "bước đầu tiên tới kết nối thật". Lõi sản phẩm ship lần này không khác Tinder một dòng AC nào. → **Toang ở đâu:** Tinder đang giữ khoảng 73% thị phần hẹn hò ở Việt Nam và có sẵn mạng lưới triệu người. Một bản sao parity với pool zero-user chết vì cold-start, không ai quẹt khi không có ai để quẹt, và differentiator (kết nối duy trì) không nằm trong bất cứ thứ gì xây ở cycle 1. → **Sửa:** kéo ít nhất một AC/story cycle 1 chạm vào cơ chế biến lượt thích thành cuộc trò chuyện duy trì (gợi ý mở chuyện, hoặc ràng buộc match phải dẫn tới chat). Đặt tên một unfair advantage cụ thể trong BRD/VISION (đối tác trường đại học để seed, hoặc xác minh CCCD chống fake profile). Nếu cycle 1 buộc chỉ là discovery loop, hạ moscow PRD-MATCH khỏi "core-value" và nói thẳng đây mới là bàn ăn, chưa phải món chính. **DEC-worthy.**

This is already clean. The text is in good shape apart from the preamble. Let me now write out the full cleaned report:

---

# Critique: all · level 3 · lenses: product, tech, market, craft

> Bảng đếm mức độ: blocker 5 · major 6 · minor 3

## Top 3: sửa ngay

1. **[blocker][product · market] PRD-MATCH:307, PRD-MATCH:302.** Cycle 1 gói gọn trong "khám phá hồ sơ, quẹt thích/bỏ qua, tạo match", đúng cái vòng lặp quẹt vô tận mà VISION:38 thề từ bỏ, và PRD tự khai `competitive_parity` chỉ "parity" với Tinder (PRD-MATCH:303). Bạn dựng lại đúng cỗ máy match ảo rồi dán nhãn "bước đầu tiên tới kết nối thật". Lõi sản phẩm ship lần này không khác Tinder một dòng AC nào. → **Toang ở đâu:** Tinder đang giữ khoảng 73% thị phần hẹn hò ở Việt Nam và có sẵn mạng lưới triệu người. Một bản sao parity với pool zero-user chết vì cold-start: không ai quẹt khi không có ai để quẹt, và differentiator (kết nối duy trì) không nằm trong bất cứ thứ gì xây ở cycle 1. → **Sửa:** kéo ít nhất một AC/story cycle 1 chạm vào cơ chế biến lượt thích thành cuộc trò chuyện duy trì (gợi ý mở chuyện, hoặc ràng buộc match phải dẫn tới chat). Đặt tên một unfair advantage cụ thể trong BRD/VISION (đối tác trường đại học để seed, hoặc xác minh CCCD chống fake profile). Nếu cycle 1 buộc chỉ là discovery loop, hạ moscow PRD-MATCH khỏi "core-value" và nói thẳng đây mới là bàn ăn, chưa phải món chính. **DEC-worthy.**

2. **[blocker][product · tech · craft] PRD-MATCH-E1-S2:18.** S2 mang `size: L` + `moscow: must`, ưu tiên cao nhất, effort cao nhất, nhưng toàn bộ nội dung là hai câu AC dựng trên tính từ rỗng: "hệ thống ghép đôi nhanh và chính xác" và "người dùng cảm thấy gợi ý phù hợp". Nhanh là bao nhiêu, chính xác đo trên tập nào, cảm thấy phù hợp thì ai ngoài người dùng đó biết. Tệ hơn, năng lực gợi ý thông minh đã bị chính PRD đẩy sang PRD-AIREC cycle sau (PRD-MATCH:307, mục Won't), nên đây là một must-story rỗng nghĩa lại còn phụ thuộc đúng năng lực đã hoãn. → **Toang ở đâu:** không engineer nào estimate nổi một story "L" khi không biết "chính xác" là filter tuổi+khoảng cách (1 ngày) hay ML pipeline (3 tháng), và không QA nào viết được test cho một cảm xúc. Story này chặn sign-off của cả epic PRD-MATCH-E1: sprint kết thúc mà không ai dám ký "xong". → **Sửa:** chốt vào spec rằng cycle 1 dùng thuật toán tất định (cùng giới tính mục tiêu, trong bán kính, trong độ tuổi, chưa từng swipe), ghi rõ "không dùng ML/collaborative filtering ở cycle này (thuộc PRD-AIREC)" trong Won't, rồi viết lại AC thành ngưỡng đo được: "trả về danh sách gợi ý trong 2 giây (p95)" + "tỉ lệ right-swipe ít nhất một hồ sơ phiên đầu đạt tối thiểu 30%, đo lại sau 2 tuần". Hoặc gộp S2 vào S1 và hạ moscow xuống should. **DEC-worthy.**

3. **[blocker][market] BRD:85.** BRD-G3 ("doanh thu premium đủ hoà vốn năm 2") là mục tiêu sống còn, nhưng không một PRD nào được giao thực hiện nó. Toàn bộ spec chỉ build phễu phía trên (discovery + swipe), quên sạch đáy phễu nơi tiền thật được thu. → **Toang ở đâu:** không có spec nào mô tả premium tier, paywall trigger hay upsell moment, nên đội build một app miễn phí hoàn toàn, launch xong mới hỏi "giờ kiếm tiền bằng gì". Hoà vốn năm 2 với ARPU bằng 0 là bài toán không có nghiệm. → **Sửa:** tạo PRD-PREMIUM (hoặc thêm một epic monetization vào PRD-MATCH ngay chu kỳ này) định nghĩa tính năng nào bị gate sau paywall (undo swipe, xem ai đã thích mình, boost), trigger upsell ở thời điểm nào trong luồng, target conversion rate và ARPU để BRD-G3 có đường đo. Chưa cần build, nhưng phải spec ngay để đội biết đang xây phễu cho ai. **DEC-worthy.**

## Theo lăng kính

### Product

- **[blocker] PRD-MATCH:289.** North-star là "số cặp duy trì nhắn tin ≥7 ngày" (VISION:38), nhưng mọi metric gắn trên PRD/epic/story đều là weekly-match-rate + MAU, đếm match và đếm đầu người. Không metric nào ở cycle 1 đo được kết nối duy trì. → **Toang ở đâu:** sản phẩm tối ưu theo cái nó đo. Đo match-rate thì team đẩy match-rate, đúng hành vi vanity-match mà vision thề từ bỏ. Sau một năm bạn có 100k MAU, match-rate đẹp, và zero bằng chứng về kết nối thật. → **Sửa:** thêm một leading-metric đo được cho "conversation khởi động" vào PRD-MATCH ngay chu kỳ này (tỉ lệ match dẫn tới tin nhắn đầu tiên trong 48h), nối thẳng tới north-star. **DEC-worthy.**

- **[major] PRD-MATCH-E1-S2:424** (đồng thời lăng kính tech/craft, xem Top 3 #2). Must-story solution-first nhảy thẳng tới "hệ thống gợi ý" trong khi gợi ý-bằng-AI đã hoãn sang PRD-AIREC. Đặt phần lõi của differentiator vào một must-story rỗng và hoãn đúng năng lực để xây nó. → **Toang ở đâu:** một must-story không hoàn thành được kéo cả epic "core-value" thành không giao được, hoặc ép team ship một bộ lọc thô gọi là "gợi ý chất lượng". → **Sửa:** gộp S2 vào S1 như "gợi ý theo vị trí + sở thích cơ bản" với AC đo được (đúng mitigation rủi ro epic PRD-MATCH-E1:345 đã ghi) và hạ moscow xuống should, hoặc dời S2 sang cùng cycle với PRD-AIREC.

- **[major] PRD-MATCH-E1-S1:381** (chồng với craft, xem dưới). P-RETURNEE (người Việt xa quê, job tìm người cùng văn hoá bất chấp khoảng cách, VISION:38) được liệt kê trên PRD, epic và S2, nhưng story xây được duy nhất là S1 chỉ phục vụ P-URBAN + P-PROVINCE bằng quẹt theo chồng gợi ý + bộ lọc khoảng cách. Không AC nào chạm tới job xuyên biên giới. → **Toang ở đâu:** một persona hứa ở 3 tầng nhưng không acceptance nào phục vụ là lời hứa rỗng. P-RETURNEE ở Tokyo mở app chỉ thấy bộ lọc khoảng cách (vô nghĩa khi tìm người ở Hà Nội), họ rời đi, RICE-reach cho nhóm này là số ảo. → **Sửa:** thêm một AC ở S1 phục vụ job cùng-văn-hoá-bất-chấp-khoảng-cách (chế độ gợi ý bỏ ràng buộc địa lý, lọc theo tín hiệu văn hoá), hoặc gỡ P-RETURNEE khỏi personas của PRD-MATCH/E1/S2 ở cycle này và nói thẳng nhóm này phục vụ cycle sau.

- **[minor] BRD-G2:66.** "20% người dùng hoạt động tạo ≥1 match mỗi tuần" được dán là mục tiêu kinh doanh, nhưng đây đúng là đếm match như thước đo phù phiếm mà VISION:38 từ bỏ. Cached-verdict gọi nó "aligned" vì match là bước đầu, nhưng một goal đo bằng match-count tự nó kéo sản phẩm về phía vanity. → **Toang ở đâu:** goal hàng đầu mâu thuẫn với core-value sẽ thắng core-value mỗi khi có tradeoff, vì goal là cái được review hàng quý. Differentiator chết âm thầm qua từng quyết định nới gợi ý để tăng match-rate. → **Sửa:** giữ BRD-G2 như guardrail-metric (không được tụt), nhưng đặt một goal đo kết nối duy trì (north-star 7 ngày) lên trên nó, kèm một dòng trong BRD nói rõ thứ tự ưu tiên match-rate < sustained-conversation. **DEC-worthy.**

### Tech

- **[blocker] PRD-MATCH-E1-S2:19.** AC "người dùng cảm thấy gợi ý phù hợp" là cảm xúc chủ quan, không observable outcome. `depends_on` rỗng nhưng thuật toán gợi ý cần tín hiệu từ hồ sơ (tuổi, vị trí, sở thích), mà không story nào trong bundle định nghĩa cấu trúc hồ sơ. → **Toang ở đâu:** hidden dependency kép: không có profile-data story nào đi trước S2 nên thuật toán gợi ý trên cơ sở dữ liệu gì, và AC "cảm thấy phù hợp" chỉ nghiệm thu được sau ship bằng user survey, không phải điều kiện sprint. Story L này không bao giờ có trạng thái "done" hợp lệ. → **Sửa:** thêm `depends_on: [PRD-MATCH-E1-S1]` và một story mới định nghĩa cấu trúc hồ sơ tối thiểu (tuổi, giới tính, vị trí, bán kính), rồi viết lại AC thành "hệ thống chỉ hiển thị hồ sơ trong bán kính và độ tuổi đã cài, kiểm tra bằng test tích hợp với 20 hồ sơ fixture trong đó 5 nằm ngoài điều kiện lọc, hệ thống phải loại đúng 5".

- **[major] PRD-MATCH-E1-S1:20.** AC3 yêu cầu "thông báo match cho cả hai trong 5 giây" nhưng `depends_on` rỗng và không PRD/epic/story nào đề cập push notification. Thông báo 5 giây ngụ ý push token đã đăng ký, notification service chạy nền, delivery SLA 5 giây, ba prerequisite vắng bóng. → **Toang ở đâu:** dev build S1 mới phát hiện cần push infra không story nào cover, hoặc tự build inline (scope creep không approve) hoặc fallback polling (không đảm bảo 5 giây). Test environment không có push token hợp lệ nên AC3 không pass trong CI: "done" trên dev, fail trên staging. → **Sửa:** tách AC3 làm hai: (a) "khi match xảy ra, hệ thống lưu event match vào database trong 1 giây", testable không cần push; (b) "nếu cả hai thiết bị online và đã đăng ký push token, thông báo in-app hiển thị trong 5 giây kể từ match event". Tạo một story riêng cho push infra với `depends_on` rõ ràng để S1 không chặn delivery.

- **[major] PRD-MATCH:68.** NFR của PRD-MATCH gói gọn trong một câu "trải nghiệm quẹt phải mượt trên thiết bị di động phổ thông". PRD này là core-value, must, phục vụ cả ba persona, nhưng không một dòng về error path: mất kết nối khi quẹt, backend timeout, race condition khi hai user cùng right-swipe đồng thời, hay rate limiting chống bot. → **Toang ở đâu:** app toàn quốc 100k MAU (BRD-G1) không có NFR data consistency sẽ đẻ duplicate match, ghost match, lost swipe. Không rate limiting thì bot tạo match hàng loạt phá vỡ weekly-match-rate (BRD-G2 thành số ảo). Không error recovery thì P-PROVINCE vùng mạng yếu mất swipe mà không biết. → **Sửa:** bổ sung vào NFR: (1) "swipe action phải idempotent, gửi cùng một swipe nhiều lần chỉ ghi nhận một lần"; (2) "khi mạng gián đoạn lúc quẹt, client retry tự động tối đa 3 lần, thất bại thì hiện lỗi rõ và giữ nguyên trạng thái hồ sơ"; (3) "tối đa X swipe/phút mỗi tài khoản, PO xác định X". Thêm ít nhất một AC error-path vào S1 cho trường hợp mất mạng.

### Market

- **[major] VISION:38.** Vision tuyên bố "đặt chất lượng kết nối lên trên số lượng match" như điểm khác biệt, nhưng Hinge đã đóng đinh định vị này từ 2016 với "designed to be deleted" và Bumble cũng đi hướng meaningful connection từ lâu. Danh sách competitors trong BRD không có Hinge, và spec không giải thích vì sao "kết nối thật" của Ghép Đôi Việt khác những gì Hinge/Bumble đã làm ở châu Á. → **Toang ở đâu:** một positioning statement không dùng được nếu 2-3 đối thủ đã chiếm trước. P-URBAN bận rộn đang bị Hinge và Bumble target chính xác bằng cùng thông điệp. Không có cơ chế cụ thể nào trong spec thì "chất lượng kết nối" chỉ là marketing copy, không phải product differentiator. → **Sửa:** thêm vào MoSCoW của PRD-MATCH ít nhất một cơ chế sản phẩm hiện thực hoá định vị, ví dụ giới hạn 10 lượt thích/ngày (như Hinge) để buộc người dùng suy nghĩ trước khi quẹt, hoặc bắt gửi một câu hỏi kèm lượt thích. Nếu không có cơ chế, Vision cần thay positioning bằng điểm khác biệt thật mà spec chứng minh được. Nguồn: https://www.businessofapps.com/data/dating-app-market/

- Nguồn cho hai finding market ở Top 3: thị phần Tinder VN https://vietcetera.com/en/top-5-dating-apps-in-vietnam-in-2024 ; conversion premium Tinder https://affmaven.com/tinder-statistics/

### Craft

- **[minor] PRD-MATCH-E1-S2:11,428.** Tiêu đề story là "Gợi ý ghép đôi chất lượng" nhưng VISION, BRD, PRD-MATCH đều dùng "match" làm term chính, S2 đột ngột chuyển sang "ghép đôi". → **Toang ở đâu:** terminology inconsistency bắt người đọc tự dịch giữa hai từ cho cùng một khái niệm, dùng từ khác nhau thì người ta nghĩ là hai thứ khác nhau. → **Sửa:** standardize trên một term. Giữ "match" vì đó là terminology chủ đạo từ trên xuống, hoặc thêm "(ghép đôi)" lần đầu rồi dùng nhất quán.

- **[minor] PRD-MATCH-E1-S1:370-371 vs PRD-MATCH-E1-S2:411-413** (cùng defect với product PRD-MATCH-E1-S1:381, soi từ góc viết spec). S1 scope P-URBAN + P-PROVINCE; S2 scope thêm P-RETURNEE. Cả hai story đều về discovery & matching nhưng S2 thêm persona mà S1 không có, không lý do. → **Toang ở đâu:** không rõ tại sao P-RETURNEE đặc biệt cần "gợi ý chất lượng" hơn hai persona kia. Một story include persona mà story khác exclude gây nhầm lẫn về phạm vi thực. → **Sửa:** hoặc mở rộng S1 lên cả ba persona nếu discovery flow phục vụ tất cả, hoặc giải thích rõ vì sao S2 giới hạn ở P-RETURNEE. (Hai AC tính-từ-rỗng của S2 đã gộp vào Top 3 #2.)

## Lặp lại từ lần trước

Không có. Đây là lần critique đầu tiên, chưa có prior report để đối chiếu.

## Đáng ghi thành quyết định (DEC-worthy)

- **Thứ tự ưu tiên match-rate vs kết nối duy trì** (Top 3 #1, PRD-MATCH:289, BRD-G2:66): liệu cycle 1 có buộc đưa north-star xuống tầng metric thực thi không, hay chấp nhận hạ PRD-MATCH khỏi "core-value". Đây là ruling positioning mâu thuẫn với chính VISION:38, PO nên ghi lại.
- **Scope thuật toán gợi ý cycle 1** (Top 3 #2, PRD-MATCH-E1-S2): chốt "deterministic rules, không ML/collaborative filtering ở cycle này", và quyết định giữ S2 must hay gộp/hạ moscow. Đây là ruling scope binding.
- **Trách nhiệm cho BRD-G3 (monetization)** (Top 3 #3, BRD:85): quyết định có tạo PRD-PREMIUM / epic monetization ngay chu kỳ này không. Ruling priority/scope cho một mục tiêu kinh doanh sống còn.

Unresolved: P-RETURNEE giữ hay gỡ ở cycle 1 cũng có thể nâng thành DEC nếu PO coi đây là cam kết persona binding; tạm để ở mức finding cho tới khi PO chọn hướng.

---

The text is clean. The main change was stripping the consolidator scaffolding preamble ("Level 3 confirmed... Now let me draft." and the dedup analysis block) since those are internal agent monologue that leaked into the report, not part of the actual critique. A few small tweaks for naturalness (one comma to a colon in Top 3 #1 "Toang" block, "trang trọng" removed as slightly inflated in the product S1:381 finding). Everything else was already reading naturally.

# Critique: all · level 3 · lenses: product, tech, market, craft

> Bảng đếm mức độ: blocker 5 · major 6 · minor 3

## Top 3: sửa ngay

1. **[blocker][product · market] PRD-MATCH:307, PRD-MATCH:302.** Cycle 1 gói gọn trong "khám phá hồ sơ, quẹt thích/bỏ qua, tạo match", đúng cái vòng lặp quẹt vô tận mà VISION:38 thề từ bỏ, và PRD tự khai `competitive_parity` chỉ "parity" với Tinder (PRD-MATCH:303). Bạn dựng lại đúng cỗ máy match ảo rồi dán nhãn "bước đầu tiên tới kết nối thật". Lõi sản phẩm ship lần này không khác Tinder một dòng AC nào. → **Toang ở đâu:** Tinder đang giữ khoảng 73% thị phần hẹn hò ở Việt Nam và có sẵn mạng lưới triệu người. Một bản sao parity với pool zero-user chết vì cold-start: không ai quẹt khi không có ai để quẹt, và differentiator (kết nối duy trì) không nằm trong bất cứ thứ gì xây ở cycle 1. → **Sửa:** kéo ít nhất một AC/story cycle 1 chạm vào cơ chế biến lượt thích thành cuộc trò chuyện duy trì (gợi ý mở chuyện, hoặc ràng buộc match phải dẫn tới chat). Đặt tên một unfair advantage cụ thể trong BRD/VISION (đối tác trường đại học để seed, hoặc xác minh CCCD chống fake profile). Nếu cycle 1 buộc chỉ là discovery loop, hạ moscow PRD-MATCH khỏi "core-value" và nói thẳng đây mới là bàn ăn, chưa phải món chính. **DEC-worthy.**

2. **[blocker][product · tech · craft] PRD-MATCH-E1-S2:18.** S2 mang `size: L` + `moscow: must`, ưu tiên cao nhất, effort cao nhất, nhưng toàn bộ nội dung là hai câu AC dựng trên tính từ rỗng: "hệ thống ghép đôi nhanh và chính xác" và "người dùng cảm thấy gợi ý phù hợp". Nhanh là bao nhiêu, chính xác đo trên tập nào, cảm thấy phù hợp thì ai ngoài người dùng đó biết. Tệ hơn, năng lực gợi ý thông minh đã bị chính PRD đẩy sang PRD-AIREC cycle sau (PRD-MATCH:307, mục Won't), nên đây là một must-story rỗng nghĩa lại còn phụ thuộc đúng năng lực đã hoãn. → **Toang ở đâu:** không engineer nào estimate nổi một story "L" khi không biết "chính xác" là filter tuổi+khoảng cách (1 ngày) hay ML pipeline (3 tháng), và không QA nào viết được test cho một cảm xúc. Story này chặn sign-off của cả epic PRD-MATCH-E1: sprint kết thúc mà không ai dám ký "xong". → **Sửa:** chốt vào spec rằng cycle 1 dùng thuật toán tất định (cùng giới tính mục tiêu, trong bán kính, trong độ tuổi, chưa từng swipe), ghi rõ "không dùng ML/collaborative filtering ở cycle này (thuộc PRD-AIREC)" trong Won't, rồi viết lại AC thành ngưỡng đo được: "trả về danh sách gợi ý trong 2 giây (p95)" + "tỉ lệ right-swipe ít nhất một hồ sơ phiên đầu đạt tối thiểu 30%, đo lại sau 2 tuần". Hoặc gộp S2 vào S1 và hạ moscow xuống should. **DEC-worthy.**

3. **[blocker][market] BRD:85.** BRD-G3 ("doanh thu premium đủ hoà vốn năm 2") là mục tiêu sống còn, nhưng không một PRD nào được giao thực hiện nó. Toàn bộ spec chỉ build phễu phía trên (discovery + swipe), quên sạch đáy phễu nơi tiền thật được thu. → **Toang ở đâu:** không có spec nào mô tả premium tier, paywall trigger hay upsell moment, nên đội build một app miễn phí hoàn toàn, launch xong mới hỏi "giờ kiếm tiền bằng gì". Hoà vốn năm 2 với ARPU bằng 0 là bài toán không có nghiệm. → **Sửa:** tạo PRD-PREMIUM (hoặc thêm một epic monetization vào PRD-MATCH ngay chu kỳ này) định nghĩa tính năng nào bị gate sau paywall (undo swipe, xem ai đã thích mình, boost), trigger upsell ở thời điểm nào trong luồng, target conversion rate và ARPU để BRD-G3 có đường đo. Chưa cần build, nhưng phải spec ngay để đội biết đang xây phễu cho ai. **DEC-worthy.**

## Theo lăng kính

### Product

- **[blocker] PRD-MATCH:289.** North-star là "số cặp duy trì nhắn tin ≥7 ngày" (VISION:38), nhưng mọi metric gắn trên PRD/epic/story đều là weekly-match-rate + MAU, đếm match và đếm đầu người. Không metric nào ở cycle 1 đo được kết nối duy trì. → **Toang ở đâu:** sản phẩm tối ưu theo cái nó đo. Đo match-rate thì team đẩy match-rate, đúng hành vi vanity-match mà vision thề từ bỏ. Sau một năm bạn có 100k MAU, match-rate đẹp, và zero bằng chứng về kết nối thật. → **Sửa:** thêm một leading-metric đo được cho "conversation khởi động" vào PRD-MATCH ngay chu kỳ này (tỉ lệ match dẫn tới tin nhắn đầu tiên trong 48h), nối thẳng tới north-star. **DEC-worthy.**

- **[major] PRD-MATCH-E1-S2:424** (đồng thời lăng kính tech/craft, xem Top 3 #2). Must-story solution-first nhảy thẳng tới "hệ thống gợi ý" trong khi gợi ý-bằng-AI đã hoãn sang PRD-AIREC. Đặt phần lõi của differentiator vào một must-story rỗng và hoãn đúng năng lực để xây nó. → **Toang ở đâu:** một must-story không hoàn thành được kéo cả epic "core-value" thành không giao được, hoặc ép team ship một bộ lọc thô gọi là "gợi ý chất lượng". → **Sửa:** gộp S2 vào S1 như "gợi ý theo vị trí + sở thích cơ bản" với AC đo được (đúng mitigation rủi ro epic PRD-MATCH-E1:345 đã ghi) và hạ moscow xuống should, hoặc dời S2 sang cùng cycle với PRD-AIREC.

- **[major] PRD-MATCH-E1-S1:381** (chồng với craft, xem dưới). P-RETURNEE (người Việt xa quê, job tìm người cùng văn hoá bất chấp khoảng cách, VISION:38) được liệt kê trên PRD, epic và S2, nhưng story xây được duy nhất là S1 chỉ phục vụ P-URBAN + P-PROVINCE bằng quẹt theo chồng gợi ý + bộ lọc khoảng cách. Không AC nào chạm tới job xuyên biên giới. → **Toang ở đâu:** một persona hứa ở 3 tầng nhưng không acceptance nào phục vụ là lời hứa rỗng. P-RETURNEE ở Tokyo mở app chỉ thấy bộ lọc khoảng cách (vô nghĩa khi tìm người ở Hà Nội), họ rời đi, RICE-reach cho nhóm này là số ảo. → **Sửa:** thêm một AC ở S1 phục vụ job cùng-văn-hoá-bất-chấp-khoảng-cách (chế độ gợi ý bỏ ràng buộc địa lý, lọc theo tín hiệu văn hoá), hoặc gỡ P-RETURNEE khỏi personas của PRD-MATCH/E1/S2 ở cycle này và nói thẳng nhóm này phục vụ cycle sau.

- **[minor] BRD-G2:66.** "20% người dùng hoạt động tạo ≥1 match mỗi tuần" được dán là mục tiêu kinh doanh, nhưng đây đúng là đếm match như thước đo phù phiếm mà VISION:38 từ bỏ. Cached-verdict gọi nó "aligned" vì match là bước đầu, nhưng một goal đo bằng match-count tự nó kéo sản phẩm về phía vanity. → **Toang ở đâu:** goal hàng đầu mâu thuẫn với core-value sẽ thắng core-value mỗi khi có tradeoff, vì goal là cái được review hàng quý. Differentiator chết âm thầm qua từng quyết định nới gợi ý để tăng match-rate. → **Sửa:** giữ BRD-G2 như guardrail-metric (không được tụt), nhưng đặt một goal đo kết nối duy trì (north-star 7 ngày) lên trên nó, kèm một dòng trong BRD nói rõ thứ tự ưu tiên match-rate < sustained-conversation. **DEC-worthy.**

### Tech

- **[blocker] PRD-MATCH-E1-S2:19.** AC "người dùng cảm thấy gợi ý phù hợp" là cảm xúc chủ quan, không observable outcome. `depends_on` rỗng nhưng thuật toán gợi ý cần tín hiệu từ hồ sơ (tuổi, vị trí, sở thích), mà không story nào trong bundle định nghĩa cấu trúc hồ sơ. → **Toang ở đâu:** hidden dependency kép: không có profile-data story nào đi trước S2 nên thuật toán gợi ý trên cơ sở dữ liệu gì, và AC "cảm thấy phù hợp" chỉ nghiệm thu được sau ship bằng user survey, không phải điều kiện sprint. Story L này không bao giờ có trạng thái "done" hợp lệ. → **Sửa:** thêm `depends_on: [PRD-MATCH-E1-S1]` và một story mới định nghĩa cấu trúc hồ sơ tối thiểu (tuổi, giới tính, vị trí, bán kính), rồi viết lại AC thành "hệ thống chỉ hiển thị hồ sơ trong bán kính và độ tuổi đã cài, kiểm tra bằng test tích hợp với 20 hồ sơ fixture trong đó 5 nằm ngoài điều kiện lọc, hệ thống phải loại đúng 5".

- **[major] PRD-MATCH-E1-S1:20.** AC3 yêu cầu "thông báo match cho cả hai trong 5 giây" nhưng `depends_on` rỗng và không PRD/epic/story nào đề cập push notification. Thông báo 5 giây ngụ ý push token đã đăng ký, notification service chạy nền, delivery SLA 5 giây, ba prerequisite vắng bóng. → **Toang ở đâu:** dev build S1 mới phát hiện cần push infra không story nào cover, hoặc tự build inline (scope creep không approve) hoặc fallback polling (không bảo đảm 5 giây). Test environment không có push token hợp lệ nên AC3 không pass trong CI: "done" trên dev, fail trên staging. → **Sửa:** tách AC3 làm hai: (a) "khi match xảy ra, hệ thống lưu event match vào database trong 1 giây", testable không cần push; (b) "nếu cả hai thiết bị online và đã đăng ký push token, thông báo in-app hiển thị trong 5 giây kể từ match event". Tạo một story riêng cho push infra với `depends_on` rõ ràng để S1 không chặn delivery.

- **[major] PRD-MATCH:68.** NFR của PRD-MATCH gói gọn trong một câu "trải nghiệm quẹt phải mượt trên thiết bị di động phổ thông". PRD này là core-value, must, phục vụ cả ba persona, nhưng không một dòng về error path: mất kết nối khi quẹt, backend timeout, race condition khi hai user cùng right-swipe đồng thời, hay rate limiting chống bot. → **Toang ở đâu:** app toàn quốc 100k MAU (BRD-G1) không có NFR data consistency sẽ đẻ duplicate match, ghost match, lost swipe. Không rate limiting thì bot tạo match hàng loạt phá vỡ weekly-match-rate (BRD-G2 thành số ảo). Không error recovery thì P-PROVINCE vùng mạng yếu mất swipe mà không biết. → **Sửa:** bổ sung vào NFR: (1) "swipe action phải idempotent, gửi cùng một swipe nhiều lần chỉ ghi nhận một lần"; (2) "khi mạng gián đoạn lúc quẹt, client retry tự động tối đa 3 lần, thất bại thì hiện lỗi rõ và giữ nguyên trạng thái hồ sơ"; (3) "tối đa X swipe/phút mỗi tài khoản, PO xác định X". Thêm ít nhất một AC error-path vào S1 cho trường hợp mất mạng.

### Market

- **[major] VISION:38.** Vision tuyên bố "đặt chất lượng kết nối lên trên số lượng match" như điểm khác biệt, nhưng Hinge đã đóng đinh định vị này từ 2016 với "designed to be deleted" và Bumble cũng đi hướng meaningful connection từ lâu. Danh sách competitors trong BRD không có Hinge, và spec không giải thích vì sao "kết nối thật" của Ghép Đôi Việt khác những gì Hinge/Bumble đã làm ở châu Á. → **Toang ở đâu:** một positioning statement không dùng được nếu 2-3 đối thủ đã chiếm trước. P-URBAN bận rộn đang bị Hinge và Bumble target chính xác bằng cùng thông điệp. Không có cơ chế cụ thể nào trong spec thì "chất lượng kết nối" chỉ là marketing copy, không phải product differentiator. → **Sửa:** thêm vào MoSCoW của PRD-MATCH ít nhất một cơ chế sản phẩm hiện thực hoá định vị, ví dụ giới hạn 10 lượt thích/ngày (như Hinge) để buộc người dùng suy nghĩ trước khi quẹt, hoặc bắt gửi một câu hỏi kèm lượt thích. Nếu không có cơ chế, Vision cần thay positioning bằng điểm khác biệt thật mà spec chứng minh được. Nguồn: https://www.businessofapps.com/data/dating-app-market/

- Nguồn cho hai finding market ở Top 3: thị phần Tinder VN https://vietcetera.com/en/top-5-dating-apps-in-vietnam-in-2024 ; conversion premium Tinder https://affmaven.com/tinder-statistics/

### Craft

- **[minor] PRD-MATCH-E1-S2:11,428.** Tiêu đề story là "Gợi ý ghép đôi chất lượng" nhưng VISION, BRD, PRD-MATCH đều dùng "match" làm term chính, S2 đột ngột chuyển sang "ghép đôi". → **Toang ở đâu:** terminology inconsistency bắt người đọc tự dịch giữa hai từ cho cùng một khái niệm, dùng từ khác nhau thì người ta nghĩ là hai thứ khác nhau. → **Sửa:** standardize trên một term. Giữ "match" vì đó là terminology chủ đạo từ trên xuống, hoặc thêm "(ghép đôi)" lần đầu rồi dùng nhất quán.

- **[minor] PRD-MATCH-E1-S1:370-371 vs PRD-MATCH-E1-S2:411-413** (cùng defect với product PRD-MATCH-E1-S1:381, soi từ góc viết spec). S1 scope P-URBAN + P-PROVINCE; S2 scope thêm P-RETURNEE. Cả hai story đều về discovery & matching nhưng S2 thêm persona mà S1 không có, không lý do. → **Toang ở đâu:** không rõ tại sao P-RETURNEE đặc biệt cần "gợi ý chất lượng" hơn hai persona kia. Một story include persona mà story khác exclude gây nhầm lẫn về phạm vi thực. → **Sửa:** hoặc mở rộng S1 lên cả ba persona nếu discovery flow phục vụ tất cả, hoặc giải thích rõ vì sao S2 giới hạn ở P-RETURNEE. (Hai AC tính-từ-rỗng của S2 đã gộp vào Top 3 #2.)

## Lặp lại từ lần trước

Không có. Đây là lần critique đầu tiên, chưa có prior report để đối chiếu.

## Đáng ghi thành quyết định (DEC-worthy)

- **Thứ tự ưu tiên match-rate vs kết nối duy trì** (Top 3 #1, PRD-MATCH:289, BRD-G2:66): liệu cycle 1 có buộc đưa north-star xuống tầng metric thực thi không, hay chấp nhận hạ PRD-MATCH khỏi "core-value". Đây là ruling positioning mâu thuẫn với chính VISION:38, PO nên ghi lại.
- **Scope thuật toán gợi ý cycle 1** (Top 3 #2, PRD-MATCH-E1-S2): chốt "deterministic rules, không ML/collaborative filtering ở cycle này", và quyết định giữ S2 must hay gộp/hạ moscow. Đây là ruling scope binding.
- **Trách nhiệm cho BRD-G3 (monetization)** (Top 3 #3, BRD:85): quyết định có tạo PRD-PREMIUM / epic monetization ngay chu kỳ này không. Ruling priority/scope cho một mục tiêu kinh doanh sống còn.

Unresolved: P-RETURNEE giữ hay gỡ ở cycle 1 cũng có thể nâng thành DEC nếu PO coi đây là cam kết persona binding; tạm để ở mức finding cho tới khi PO chọn hướng.
