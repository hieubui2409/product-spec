Now let me scan the critique for specific AI-tells before rewriting.

The critique is largely in Vietnamese, so I need to check for:
- Em/en dashes (the `→` arrows are fine, those are not dashes used as em/en dash punctuation)
- Banned vocabulary
- Vietnamese translation tells
- Rhythm issues
- Forced triples or robotic patterns

Let me scan carefully. The `→` symbols are being used as arrows in a structured format ("Toang ở đâu" / "Sửa"), which is a consistent finding structure, not an em-dash tell. Those stay.

Key issues I find:
1. "đảm bảo" does not appear but I need to check for other tells
2. Some sentences are very long and uniform in structure
3. "tận dụng" does not appear
4. The phrase "chỉ là một dòng mitigation" is fine
5. "đóng vai trò" - not present
6. "nhằm mục đích" - not present
7. Some rhythm issues: many sentences start with the same structure
8. "Giả sử" in the AC fix suggestions is a GIVEN clause (spec language), not a Vietnamese tell
9. Check for em/en dashes: I see none in the markdown source

The report is actually quite clean. The main issues are:
- Some sentences run uniform in length and structure, especially in the "Toang ở đâu" sections
- A few spots read a bit stiff
- "một cách" - I need to check
- The phrase "tích luỹ sinh trắc học" in Top 3 #3 is fine (concrete)
- "đường-thành-công" và "đường-thất-bại" are hyphenated in a slightly robotic way
- The structure of each finding is uniform: finding statement, Toang, Sửa - this is intentional structural consistency, not a tell

Let me identify specific spots to rewrite:

1. "Đây đúng là trái tim khác biệt hoá của sản phẩm" - stiff, "trái tim" metaphor mixed with "khác biệt hoá" is corporate
2. Top 3 #1: "Đi kèm:" is a bit bureaucratic
3. "hệ thống tích luỹ sinh trắc học của người không đồng ý lưu" - slightly awkward word order
4. Market section: "Me-too với pool nhỏ hơn là điều kiện thua ngay từ đầu trong two-sided market" - this is punchy and good, keep it
5. "Lean Canvas thiếu dòng doanh thu" - good, concrete
6. Some of the "Toang ở đâu" explanations run the same sentence length repeatedly
7. "Đây là lỗi hệ thống của cả spec" - good punch line, keep as is
8. The "Giả sử ... khi ... thì" AC format is spec language, not a tell

The report is largely well-written. The main things to fix:
- Vary rhythm in a few dense paragraphs
- A couple of stiff Vietnamese constructions
- "đường-thành-công" / "đường-thất-bại" - these are readable but unusual hyphenation; keeping as they're internally coined terms
- One forced structure pattern: many bullet headings follow "→ **Toang ở đâu:**" then "→ **Sửa:**" uniformly, but this is the intentional finding format, not an AI tell

On second reading, the consolidator did a solid job. The prose reads like a sharp person for the most part. Let me make targeted fixes only where needed, not churn for the sake of churning.

Specific rewrites I'll make:
1. Top 3 #1: "Đi kèm:" start is bureaucratic - make it flow better
2. Top 3 #2: "Đây đúng là trái tim khác biệt hoá của sản phẩm, gói trong hai câu không ai chứng minh được" - the "Đây đúng là" opener is slightly stiff; rework
3. Top 3 #3: "Spec im lặng hoàn toàn về số phận" - this is actually good, keep
4. PRD-CHAT finding: "Tính năng định nghĩa thành công của cả sản phẩm bị xếp sau cùng trong sóng đầu" - good punch, keep
5. Market BRD-G1: "Lean Canvas thiếu Customer Channels, cold-start giết startup tốt hơn" - good, keep
6. The craft section "PRD-MATCH-E1-S1:949 vs PRD-MATCH-E1-S2:968" intro is fine
7. "Terminology drift này c1 đã nêu cho cùng cặp story, vẫn chưa chuẩn hoá" - this parenthetical at the end of craft findings is a slightly robotic closing formula that repeats; the rhythm of "(Lỗi hệ thống me-too: c1 MATCH, c3 CHAT, c4 EVENTS, c5 PREMIUM, nay lại MATCH; vẫn chưa có một điểm "ahead" nào.)" is actually punchy

Overall the report is good. I'll make targeted improvements to rhythm and a few stiff spots.

# Critique: all · level 3 · lăng kính: product, tech, market, craft

> Severity tally: blocker 4 · major 8 · minor 3

## Top 3: sửa ngay

1. **[blocker][product · market] PRD-MATCH:410, BRD-G1:63.** Cả spec đặt cược vào north-star "cặp nhắn tin qua lại >=7 ngày", nhưng giả định nguy hiểm nhất, đủ người để ghép, chỉ được xử lý bằng một dòng mitigation "pool mỏng ở tỉnh lẻ thì mở bán kính ra toàn quốc". Mà mở toàn quốc thì đâm thẳng vào value-prop văn hoá/địa phương của P-PROVINCE và P-RETURNEE. Và BRD-G1 nhắm 100k MAU năm 1 mà không một kênh acquisition nào được đặt tên. Không referral, không city-launch, không partnership.

   Toang ở đâu: dating là two-sided market. P-PROVINCE mở app thấy 5 hồ sơ rồi rời đi trước khi chạm tới match, chưa nói tới nhắn tin 7 ngày. "Mở bán kính" biến sản phẩm thành một Tinder toàn quốc khác, xoá đúng lý do tồn tại. Cold-start đã giết nhiều startup có sản phẩm tốt hơn; north-star sẽ không bao giờ có đủ dữ liệu để bắt đầu đo.

   Sửa: chốt một quyết định cold-start tường minh ở cấp BRD/PRD-MATCH: thành phố khởi điểm nào, ngưỡng mật độ pool tối thiểu trước khi mở rộng, ranh giới bán kính được phép tới đâu mà không phá value-prop văn hoá, cộng ít nhất một giả thuyết acquisition kiểm chứng được (city-launch HCM trước rồi đo density / referral loop / partnership cộng đồng độc thân). Gắn BRD-G1 với một channel-metric, không chỉ là MAU endpoint không có đường tới. **DEC-worthy.** (Đã nói ở c1 và c5; vẫn chưa sửa.)

2. **[blocker][tech · product · craft] PRD-MATCH-E1-S2:992.** Story `must / L / now`, ưu tiên cao nhất và effort lớn nhất, mà toàn bộ AC là hai tính từ rỗng: "hệ thống ghép đôi nhanh và chính xác" và "người dùng cảm thấy gợi ý phù hợp". Nhanh là bao nhiêu mili-giây. Chính xác đo trên tập nào. "Cảm thấy phù hợp" thì ngoài chính người đó ra ai biết. Đây là trái tim khác biệt hoá của sản phẩm, và nó được gói trong hai câu không ai chứng minh được.

   Toang ở đâu: không engineer nào estimate nổi một story L khi không biết "chính xác" là bộ lọc tuổi+khoảng cách (1 ngày) hay ML pipeline (3 tháng). Không QA nào viết test cho một cảm xúc. Story này chặn sign-off cả epic PRD-MATCH-E1: sprint kết thúc mà không ai dám ký "xong", và lời hứa "đưa đúng người tới trước mặt" sụp ngay tại tính năng đáng ra phải khác biệt.

   Sửa: chốt vào spec rằng cycle 1 dùng thuật toán tất định (trong bán kính, trong độ tuổi, đúng giới tính mục tiêu, chưa từng swipe), ghi "không dùng ML/collaborative filtering ở cycle này (thuộc PRD-AIREC)", rồi viết lại AC thành ngưỡng đo được: "trả gợi ý trong 500ms p95" + "tỉ lệ match dẫn tới >=1 lượt trả lời trong 48h đạt tối thiểu X%, nối thẳng tới weekly-match-rate và north-star". Nếu chưa đủ dữ liệu đặt ngưỡng, hạ `size: S` và tách thành hai story (latency / relevance). **DEC-worthy.** (Đã nói ở c1, vẫn chưa sửa.)

3. **[blocker][tech] PRD-SAFETY-E1-S1:1119.** AC3 cho nộp lại tối đa 3 lần / 24 giờ khi xác minh thất bại; AC4 chỉ xoá ảnh giấy tờ khi xác minh thành công. Spec im lặng hoàn toàn về số phận ảnh selfie và face vector của các lần thất bại, tức dữ liệu sinh trắc học nhạy cảm nhất trong toàn bộ spec.

   Toang ở đâu: story `must / core-value` xử lý liveness của người dùng Việt Nam, đối tượng chịu điều chỉnh của Nghị định 13/2023/NĐ-CP. AC3 cho phép tới 3 lần thử nghĩa là có thể 3 bộ ảnh/vector bị giữ lại không hạn xoá. Hệ thống tích luỹ sinh trắc học của người không đồng ý lưu. Một audit bảo mật hoặc yêu cầu pháp lý bắt lỗi ngay chỗ này.

   Sửa: thêm AC: "Khi xác minh thất bại (khớp < 90% hoặc phát hiện giả mạo liveness), sau khi đối chiếu kết thúc, toàn bộ selfie, ảnh giấy tờ và dữ liệu biometric liên quan bị xoá khỏi lưu trữ trong vòng 1 giờ, bất kể có nộp lại hay không", và ghi vào NFR PRD-SAFETY rằng vòng đời dữ liệu sinh trắc học tuân thủ Nghị định 13/2023/NĐ-CP. **DEC-worthy.** (Cùng họ tuân thủ Nghị định 13 đã nêu ở c2; c2 lo đường thành công AC4, lần này lo đường thất bại, vẫn chưa được vá.)

## Theo lăng kính

### Product

- **[blocker] PRD-MATCH:410** (xem Top 3 #1): cold-start liquidity chỉ là một dòng mitigation "mở bán kính", mà mở rộng phá value-prop văn hoá.
  Toang ở đâu: pool mỏng thì north-star không khởi động.
  Sửa: chốt thành phố khởi điểm + ngưỡng mật độ + ranh giới bán kính, ghi như giả định cần kiểm chứng.

- **[major] PRD-MATCH-E1-S2:992** (xem Top 3 #2): AC trái tim khác biệt hoá rỗng, không thước đo JTBD "đưa đúng người".
  Toang ở đâu: đội build giao gợi ý bất kỳ rồi tự tuyên bố xong.
  Sửa: buộc S2 mang tín hiệu chất lượng gợi ý đo được, nối tới north-star.

- **[major] PRD-CHAT:303.** PRD-CHAT là nơi north-star "thực sự diễn ra" (lời tự bạch trong overview), nhưng horizon `next`, sau PRD-MATCH (`now`), còn `depends_on PRD-MATCH`. Tính năng định nghĩa thành công của cả sản phẩm bị xếp sau cùng trong sóng đầu.
  Toang ở đâu: nếu CHAT trượt lịch, người đã match từ MATCH/now không nhắn tin được, đúng tình trạng "match ảo" mà vision thề diệt. Sản phẩm ra mắt với chính cái bệnh nó hứa chữa.
  Sửa: nâng lõi nhắn tin tối thiểu (S1 gửi/nhận + S2 cổng chặn) lên cùng horizon `now` với MATCH, hoặc ghi rõ MATCH không ship cho người thật trước khi CHAT sẵn sàng. Đừng để khoảng trống match-không-chat tồn tại dù một sprint.

- **[major] PRD-SAFETY:506.** PRD-SAFETY (xác minh selfie-giấy tờ) là điều kiện tiên quyết theo ràng buộc BRD "niềm tin trước tăng trưởng", nhưng đặt horizon `next` trong khi MATCH (`now`) cho người chưa xác minh quẹt và match tự do. Mitigation "cho khám phá trước, chỉ bắt buộc xác minh trước khi nhắn tin" nghĩa là cả pha match đầu tiên diễn ra giữa những người chưa ai xác minh.
  Toang ở đâu: lịch để catfish quẹt-match thoải mái suốt cửa sổ MATCH/now trước khi SAFETY/next lên sóng. P-RETURNEE (mục tiêu lừa đảo dễ nhất theo chính persona note) gặp tài khoản giả ngay lần match đầu, mất niềm tin, rời đi, phá đúng điều kiện tiên quyết BRD đặt ra.
  Sửa: quyết định tường minh: nâng cổng xác minh tối thiểu lên `now` cùng MATCH, hoặc ghi rõ trong BRD rằng "niềm tin tiên quyết" chỉ áp trước-nhắn-tin chứ không trước-match. Đừng để ràng buộc BRD và lịch horizon mâu thuẫn ngầm.

- **[minor] PRD-PREMIUM-E1-S2:1074.** Boost "ưu tiên hiển thị 30 phút" bán như quyền lợi trả phí, nhưng chính risk register của epic thừa nhận "boost không tăng match thật".
  Toang ở đâu: trong pool mỏng (rủi ro cold-start ở trên), boost chỉ xáo lại thứ tự một nhóm nhỏ. Người trả tiền không thấy match thật tăng, huỷ gói, 1 sao, BRD-G3 (hoà vốn) tự bắn vào chân. Tệ hơn, nó dạy người dùng rằng kết nối mua được, phản value-prop "chất lượng trên số lượng".
  Sửa: gắn boost với tiêu chí kết quả ("hoàn boost nếu phiên không tạo ra >=N lượt xem hồ sơ mới") và đặt ngưỡng mật độ pool tối thiểu mới được bán; hoặc hạ boost xuống `could` tới khi north-star có dữ liệu giữ chân. (Cùng họ với c5: boost + P-PROVINCE pool mỏng.)

### Tech

- **[blocker] PRD-MATCH-E1-S2:992** (xem Top 3 #2): AC không-test-được trên story `must/L/now`.
  Toang ở đâu: không viết nổi test case, cột "done" thành nơi cãi nhau vô tận.
  Sửa: Given/When/Then với ngưỡng định lượng (500ms p95 + tỉ lệ trả lời 48h), hoặc tách story.

- **[blocker] PRD-SAFETY-E1-S1:1119** (xem Top 3 #3): biometric của các lần xác minh thất bại không có hạn xoá.
  Toang ở đâu: hệ thống gom sinh trắc học của người không đồng ý lưu, vướng Nghị định 13.
  Sửa: AC xoá trong 1 giờ cho mọi lần thất bại + NFR retention tuân thủ Nghị định 13/2023/NĐ-CP.

- **[major] PRD-CHAT-E1-S1:781.** AC1 cam kết tin nhắn tới tay người nhận "trong 2 giây khi đang online", nhưng "đang online" không được định nghĩa ở đâu, không story, không PRD-CHAT, không epic.
  Toang ở đâu: nếu "online" là có WebSocket mở thì test pass kiểu này; nếu là không offline-queued thì pass kiểu khác. QA tự giả định. AC3 cùng story xử lý offline-queue, ranh giới online/offline chưa định nghĩa nên hai AC mâu thuẫn nhau khi mạng chập chờn.
  Sửa: thêm định nghĩa vào đầu story hoặc NFR: "Online = thiết bị nhận duy trì kết nối WebSocket tại thời điểm gửi; Offline = không có WebSocket hoặc client timeout quá 3 giây", rồi viết lại AC1: "Khi người nhận duy trì WebSocket và người gửi gửi text, tin tới tay trong 2 giây tính từ khi máy chủ nhận."

- **[major] PRD-PREMIUM-E1-S1:1034.** AC4 nói premium "thích lại" từ danh sách "ai đã thích mình" thì "hệ thống tạo match ngay lập tức", nhưng story khai `depends_on` rỗng dù hành động tạo match chạy qua logic mutual-match định nghĩa ở PRD-MATCH-E1-S1, một story của PRD khác.
  Toang ở đâu: PREMIUM `horizon: later`, MATCH `now`, khoảng cách tưởng an toàn nhưng AC4 cần integration point với match-creation pipe không khai trong `depends_on`, không nêu scope, không có interface contract. PRD-MATCH-E1-S1 chưa xong thì AC4 không test được.
  Sửa: thêm `depends_on: [PRD-MATCH-E1-S1]` vào frontmatter, ghi vào Scope "thao tác thích gọi cùng API match-creation của PRD-MATCH, story này không tạo logic match riêng"; hoặc tách AC4 thành story riêng với interface spec rõ.

- **[minor] PRD-PREMIUM-E1-S2:1074.** AC1 boost cam kết "ưu tiên hiển thị trong đúng 30 phút" nhưng "ưu tiên hiển thị", tác dụng cốt lõi người dùng trả tiền mua, không có định nghĩa đo được.
  Toang ở đâu: QA không biết assert gì (top-N của chồng gợi ý? impression tăng %?). Nếu pool khu vực trống boost vẫn "pass" theo câu chữ, người dùng hoàn tiền + 1 sao.
  Sửa: viết lại AC1: "hồ sơ xếp trong top-[N] của chồng gợi ý cho mọi người dùng trong bán kính [R]km, trong đúng 30 phút; N và R do PO chốt trước development và ghi vào story". Chưa quyết được N/R thì tách thành một Spike trước khi estimate.

### Market

- **[blocker] BRD-G3:101.** Hoà vốn vận hành năm 2, nhưng toàn bộ PRD-PREMIUM `horizon: later` + `moscow: should`, tức không một đồng doanh thu nào trong năm 1. Không giá gói, không ARPU mục tiêu, không kênh thanh toán. Benchmark Đông Nam Á: conversion one-time ~3.5%, ARPU ~$4.20/giao dịch; 100k MAU × 3.5% × $4.20 xấp xỉ $14.7k/tháng, chưa đủ trả API liveness, chưa nói hosting + moderation.
  Toang ở đâu: Lean Canvas thiếu dòng doanh thu. Năm 1 đốt tiền acquisition không có revenue bù. BRD-G3 là ước vọng, không phải kế hoạch.
  Sửa: thêm vào BRD-G3/PRD-PREMIUM: giá gói cụ thể (VND/tháng), tỉ lệ chuyển đổi mục tiêu (% MAU), chi phí cận biên để serve một premium user; nếu con số không khép lại, cân nhắc revenue stream thứ hai trước `horizon: later`. (Nguồn: https://soulmatcher.app/blog/dating-app-revenue-and-usage-statistics-2025-market-trends-user-growth-key-data/) **DEC-worthy.** (Đã nói ở c5, vẫn chưa sửa; c4 cũng treo "có tạo PRD-PREMIUM / em số".)

- **[major] BRD:190.** Spec liệt kê 4 đối thủ (Tinder, Bumble, Hẹn, Fika) nhưng bỏ sót Facebook Dating, top 5 tại VN theo Vietcetera 2024, chạy trên social graph 84 triệu người Việt, miễn phí hoàn toàn, phục vụ đúng bài toán "kết nối qua người quen chung". Người dùng không sa thải Tinder để dùng sản phẩm này; họ sa thải Facebook Dating.
  Toang ở đâu: đối thủ thật người dùng phải bỏ là một sản phẩm miễn phí có social graph sẵn, không cần premium, không cần xác minh thêm. Không có lý do rõ để rời. P-URBAN (nhóm chuyển đổi premium chính) không chuyển sang.
  Sửa: thêm Facebook Dating vào `competitors:` với `threat: high`, viết một đoạn positioning vì sao stranger-pool chất lượng + xác minh danh tính thắng social-graph matching. (Nguồn: https://vietcetera.com/en/top-5-dating-apps-in-vietnam-in-2024)

- **[major] PRD-MATCH:382.** Lõi sản phẩm (`core-value / must / now`) tự khai `competitive_parity`: Tinder = parity, Bumble = behind; gợi ý AI đẩy sang PRD-AIREC cycle sau. Ra thị trường với swipe-stack 12 tuổi kém đối thủ số 1, chưa bằng số 2, không có algorithmic edge, đặt cược toàn bộ khác biệt vào claim "chất lượng kết nối" mà claim này không được implement cycle đầu.
  Toang ở đâu: zero switching cost, zero moat. Không gì ngăn Tinder ra "sustained conversation score" quý tới. Không gì buộc P-URBAN bỏ Tinder Gold đã quen. Me-too với pool nhỏ hơn là điều kiện thua ngay từ đầu trong two-sided market.
  Sửa: đặt một điểm khác biệt thật ở cycle đầu, không phải cycle sau: giới hạn số gợi ý/ngày có chủ đích (quality signal, kiểu Hinge), hoặc conversation starter curate sẵn giảm blank-page barrier, hoặc ưu tiên hiển thị hồ sơ đã xác minh (PRD-SAFETY) như moat bằng trust. Một trong ba phải có trong PRD-MATCH cycle 1. (Nguồn: https://www.kenresearch.com/vietnam-online-dating-application-market) (Lỗi hệ thống me-too: c1 MATCH, c3 CHAT, c4 EVENTS, c5 PREMIUM, nay lại MATCH; vẫn chưa có một điểm "ahead" nào.)

- **[major] BRD-G1:63** (gộp vào Top 3 #1): 100k MAU năm 1 không một kênh acquisition nào được đặt tên.
  Toang ở đâu: Lean Canvas thiếu Customer Channels, cold-start giết startup tốt hơn.
  Sửa: thêm ít nhất một giả thuyết acquisition kiểm chứng (city-launch / referral / partnership) và gắn BRD-G1 với channel-metric.

### Craft

- **[major] PRD-MATCH-E1-S2:992-994** (cùng defect với product/tech Top 3 #2, soi từ góc viết spec): AC "nhanh", "chính xác", "cảm thấy phù hợp", ba tính từ không định lượng.
  Toang ở đâu: không ai biết khi nào AC đạt, dẫn tới tranh cãi ký phí khi bàn giao.
  Sửa: "trả gợi ý trong 300-500ms khi online" + "tối thiểu X% trong 20 hồ sơ gợi ý đầu tạo match/trả lời trong 7 ngày".

- **[major] PRD-MATCH-E1-S1:949 vs PRD-MATCH-E1-S2:968.** Tiêu đề S1 "Khám phá & quẹt hồ sơ", S2 "Gợi ý ghép đôi chất lượng", cùng epic, dùng "quẹt hồ sơ" vs "gợi ý ghép đôi" cho cùng một bước.
  Toang ở đâu: người xây tự hỏi "ghép đôi" là sau quẹt hay sau khi hệ thống recommend. Không rõ S1 là UI quẹt còn S2 là algorithm hay cả hai.
  Sửa: chuẩn hoá: "khám phá & quẹt" cho S1 (giao diện), "thuật toán gợi ý" cho S2 (logic); hoặc đổi tên S2 thành "Thuật toán gợi ý match chất lượng cao" với AC định lượng. (Terminology drift này c1 đã nêu cho cùng cặp story, vẫn chưa chuẩn hoá.)

- **[major] PRD-SAFETY-E1-S1:1117-1129.** AC nói "mức tin cậy >= 90%" nhưng 90% là gì: confidence score của face-match? Hay "100 lần test khớp 90"? Không giải thích đơn vị hay cách tính.
  Toang ở đâu: engineer hỏi "dùng model nào, chuẩn hoá ra sao", con số 90% trôi nổi sẽ gây tranh cãi khi kiểm tra kết quả xác minh.
  Sửa: "mức tin cậy >= 90% = face-match confidence từ [tên model + vendor], cosine-distance giữa embedding selfie và embedding ảnh giấy tờ >= 0.90".

- **[minor] PRD-PREMIUM body:457-461.** Câu rủi ro dài 30 từ, lồng nhau: "tính năng trả phí có thể làm xói mòn trải nghiệm miễn phí (ví dụ giới hạn lượt thích quá chặt khiến người dùng mới rời app...)".
  Toang ở đâu: PO đọc xong vẫn không chắc rủi ro cụ thể là gì.
  Sửa: tách thành câu đơn: "Giới hạn lượt thích miễn phí quá chặt sẽ khiến người dùng mới bỏ app trước khi cảm nhận giá trị lõi (khám phá + match)."

- **[minor] PRD-CHAT body:308-312.** Risk dùng từ "đứt quãng" mơ hồ: là không trả lời, app lỗi, hay khoảng trống thời gian giữa hai tin?
  Toang ở đâu: PO không hiểu rủi ro cụ thể nên không đánh giá được mitigation.
  Sửa: "Tin nhắn gửi thất bại hoặc trễ hơn 30 giây sẽ làm người dùng cảm thấy cuộc trò chuyện bị gián đoạn, tăng xác suất không trả lời lại trong 7 ngày."

## Lặp lại từ lần trước

- **PRD-MATCH-E1-S2 AC tính từ rỗng** (Top 3 #2): đã nói ở **c1** (PRD-MATCH-E1-S2:18/19, blocker), vẫn chưa sửa. Cùng câu "nhanh và chính xác" / "cảm thấy phù hợp", giờ thêm lăng kính craft xác nhận lần ba.
- **Me-too / không có moat ở lõi sản phẩm** (market PRD-MATCH:382): lần thứ năm. c1 (MATCH), c3 (CHAT), c4 (EVENTS), c5 (PREMIUM), nay lại MATCH. Một feature-area khai parity/behind với COMP-TINDER mà chưa từng có một điểm "ahead". Đây là lỗi hệ thống của cả spec.
- **BRD-G3 thiếu unit-economics** (market BRD-G3:101): đã nói ở **c5** (BRD-G3:46, major) và treo từ **c4**, vẫn chưa có giá gói / conversion / ARPU.
- **Cold-start / acquisition** (Top 3 #1): c1 đã nêu pool zero-user, c5 đã nêu thiếu channel cho BRD-G1, vẫn chưa có quyết định khởi điểm hay giả thuyết acquisition.
- **Tuân thủ Nghị định 13 cho biometric** (Top 3 #3): c2 đã nêu cho AC4 đường thành công và NFR; lần này lỗ hổng nằm ở đường thất bại (selfie/vector của lần fail không có hạn xoá), cùng họ pháp lý, vẫn chưa được vá trọn.
- **Terminology "quẹt" vs "ghép đôi"** (craft S1 vs S2): c1 đã nêu cho cùng cặp story, vẫn chưa chuẩn hoá.

## Đáng ghi thành quyết định (DEC-worthy)

- **Cold-start + acquisition** (Top 3 #1, PRD-MATCH:410 / BRD-G1:63): thành phố khởi điểm, ngưỡng mật độ pool tối thiểu, ranh giới mở bán kính, và kênh acquisition. Ruling này định ranh giới positioning (văn hoá vs toàn quốc) và chạm BRD-G1 đã duyệt, PO nên ghi qua `--decision`.
- **Scope thuật toán gợi ý cycle 1** (Top 3 #2, PRD-MATCH-E1-S2): chốt "deterministic rules, không ML/collaborative filtering ở cycle này", giữ S2 `must` hay gộp/hạ moscow. Ruling scope binding.
- **Vòng đời dữ liệu sinh trắc học** (Top 3 #3, PRD-SAFETY-E1-S1:1119): retention/xoá cho cả lần thất bại + mức cam kết tuân thủ Nghị định 13/2023/NĐ-CP. Định nghĩa nghĩa vụ pháp lý cho cả luồng xác minh, không chỉ một câu AC.
- **Moat premium hay hạ kỳ vọng hoà vốn** (BRD-G3:101 + PRD-MATCH:382): hoặc cam kết ít nhất một tính năng "ahead" gắn vào "kết nối thật", hoặc hạ kỳ vọng BRD-G3 kèm con số kiểm tra được. Ruling này đụng BRD-G3 đã duyệt.
- **Horizon CHAT/SAFETY vs MATCH** (PRD-CHAT:303, PRD-SAFETY:506): MATCH `now` chạy trước CHAT/SAFETY `next` mâu thuẫn ngầm với cả north-star (match-không-chat) lẫn ràng buộc BRD niềm tin tiên quyết (catfish quẹt tự do). Quyết định nâng lõi chat + cổng xác minh lên `now`, hay ghi rõ ranh giới "tiên quyết chỉ trước-nhắn-tin", là ruling positioning/scope PO nên ghi lại.
