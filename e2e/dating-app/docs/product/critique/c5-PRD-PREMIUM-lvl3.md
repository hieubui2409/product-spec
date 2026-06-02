Now let me read the critique carefully before rewriting.

The critique is in the prompt itself. I have the rulebook. Let me now do the two-pass rewrite.

Pass 1 scan for AI-tells and issues:

1. The opening paragraph before the code block is prose commentary, not part of the report structure. It stays as-is since it's meta-context, but the actual report is inside the fenced block.
2. Inside the report:
   - No em/en dashes found (the arrows `→` are used as separators, not dashes, and are part of the spec-critique format)
   - "Toang ở đâu" and "Sửa" are level-3 labels per voice-and-tone.md, keep them
   - "nguồn doanh thu bền vững" is a verbatim quote from spec, keep it
   - Check for banned vocab: "tối ưu hóa" appears in the VN translation-tells table as a banned phrase but it doesn't appear in the report
   - "điều kiện tiên quyết" is formal but not a translation tell per the table
   - "tái phạm" is natural Vietnamese
   - "mồ côi" (orphan) is natural
   - Rhythm: most sentences are medium length. The report is Vietnamese, so I need to check VN translation tells from the table
   - "đảm bảo" doesn't appear
   - "một cách" doesn't appear
   - "điều này cho phép / việc này giúp" doesn't appear
   - "tận dụng" doesn't appear
   - "nhằm mục đích" doesn't appear
   - "làm tươi" doesn't appear
   - "đường gốc" doesn't appear

3. Checking English portions for AI-tells:
   - The header prose before the fenced block: "Let me confirm the level-3 labels." - this is conversational, fine
   - "Prior reports (c1, c3, c4) repeatedly flag" - slightly robotic but not a banned tell
   - The note at the bottom: "three of four lenses (product, tech, craft) returned nothing this round" - neutral, fine

4. Looking more carefully at the Vietnamese body:
   - "là thông tin liên quan" (minor finding) - reads slightly formal/calque but acceptable
   - "điều kiện tiên quyết" - slightly formal but natural Vietnamese for "prerequisite"
   - "không tái litigate" - mixing VN/EN, slightly awkward
   - "re-litigate" borrowed word - actually "tái litigate" sounds odd. Should be "không cãi lại" or "không tranh luận lại"
   - "hưởng lợi từ" - natural Vietnamese
   - "ghi rõ vì sao ahead" - "ahead" is English in a VN sentence, this is deliberate code-mixing for the competitive_parity field name context, keep it
   - "có tạo PRD-PREMIUM / em số" - verbatim from prior critique, keep it
   - "tới lúc đóng" - natural
   - "chuyển nhà chứ chưa được vá" - good natural metaphor, keep it

5. The opening meta-paragraph: "Clear repeat-offense signals. Prior reports (c1, c3, c4) repeatedly flag: BRD-G3 revenue-orphan (no unit-economics numbers), me-too/no-moat pattern, and positioning drift. The c4 DEC-worthy line even names "có tạo PRD-PREMIUM" as an open decision. Now PRD-PREMIUM exists and repeats the same defects. Let me confirm the level-3 labels." - This is outside the fenced block. The instruction says return ONLY the cleaned markdown, so the report is what's in the fenced block. But the structure note before is context from the consolidator. Given the instruction says "Return ONLY the cleaned markdown", I should return just the report (without the framing prose and the fenced block markers), cleaned up.

Actually re-reading: "Return ONLY the cleaned markdown" means I return the markdown content of the report itself, not the wrapper fencing or the meta-commentary. The `Note for main agent` at the bottom is also separate context.

Let me now identify the actual fixes needed:

1. "không tái litigate" in the DEC-worthy section - fix to natural Vietnamese
2. The rhythm is already reasonably varied in Vietnamese
3. The overall report reads fairly human already - the Vietnamese is natural, the metaphors are good ("chuyển nhà chứ chưa được vá", "pool gần rỗng"), the sarcasm is intact
4. Check: any forced triples? The fixes often list three options but they're genuine options not a forced rhetorical device
5. "không một tính năng nào là độc quyền của Ghép Đôi Việt" - strong, keep it
6. "đây là bẫy 'parity is not enough'" - good metaphor, keep it

The report is largely clean. The main fix: "không tái litigate" in the DEC section should be "không cãi lại ở vòng sau" or similar.

Let me also check: does "Sửa:" in the minor finding about COMP-FIKA end with "ghi rõ lý do bỏ qua (ví dụ Fika chưa có gói trả phí tại VN)" - this reads naturally.

The "Lăng kính này không trả về phát hiện trong vòng này" repeated three times for product/tech/craft - this is slightly robotic but it's a structural placeholder, not decorative AI-padding. It should vary slightly to not be a pure copy-paste pattern. But the instruction says not to touch structure. I'll vary the wording slightly since the instruction says "what you change: the wording, and only the wording."

Let me make the targeted fixes and return the cleaned report.

```
# Critique: PRD-PREMIUM  ·  level 3  ·  lenses: market  [thiếu: product, tech, craft]

> Severity tally: blocker 1 · major 2 · minor 1

## Top 3: sửa ngay

1. **[blocker][market] PRD-PREMIUM:227.** Spec tự dán nhãn "me-too" rồi gọi đây là "nguồn doanh thu bền vững". Cả bộ premium (xem ai đã thích mình, boost, thích không giới hạn) là bản sao Tinder Gold, và `competitive_parity` khai thẳng COMP-TINDER: behind, COMP-BUMBLE: parity, COMP-HEN: parity. Không một tính năng nào là độc quyền của Ghép Đôi Việt. **Toang ở đâu:** người trả tiền cho "xem ai đã thích mình" sẽ chọn Tinder vì pool lớn gấp hàng trăm lần. Cùng tính năng thì giá trị nhân theo mạng lưới, bên kia có sẵn triệu người còn mình chưa có gì. Đây là bẫy "parity is not enough": bằng nhau về tính năng nghĩa là thua, vì mạng lưới bên kia to hơn. **Sửa:** gắn ít nhất một tính năng premium vào lợi thế "kết nối thật": boost chỉ kích hoạt sau khi match đã nhắn qua lại ít nhất 1 lần, hoặc "xem ai đã thích mình" chỉ hiện người đã điền hồ sơ đầy đủ và xác minh danh tính (cửa Tinder không làm được ở VN). Đặt tối thiểu một tính năng thành "ahead" trước COMP-TINDER trong `competitive_parity` và ghi rõ vì sao ahead.

...
```

Wait, I need to check the arrows. The original uses `→ **Toang ở đâu:**` and `→ **Sửa:**` as structural markers in the Top 3 section. These `→` arrows are not em-dashes; they're a different character. The rulebook says "Em and en dashes: cut them all" - arrows are not em/en dashes. But the arrows do act as separators/signposting within the bullet, making it look slightly structured/algorithmic. However, these are part of the level-3 voice format defined in voice-and-tone.md, so per the rules I must not touch structure. I'll keep the arrows.

Actually re-reading: in the Per-lens section, the format uses `→ **Toang ở đâu:**` and `→ **Sửa:**` as abbreviated inline labels. In the Top 3 section they appear as `→ **Toang ở đâu:**` starting a new sentence/block. These are the level labels, not em-dashes. Keep them.

The main actual fix needed: "không tái litigate" in the DEC section. Let me also double-check all instances carefully.

"tái litigate" - in the DEC section: "để không tái litigate ở vòng sau" - fix to "để khỏi cãi lại ở vòng sau" or "để khỏi mở lại ở vòng sau."

Everything else reads fairly natural. The report is already mostly clean. Let me produce the final output now.

```
# Critique: PRD-PREMIUM  ·  level 3  ·  lenses: market  [thiếu: product, tech, craft]

> Severity tally: blocker 1 · major 2 · minor 1

## Top 3: sửa ngay

1. **[blocker][market] PRD-PREMIUM:227.** Spec tự dán nhãn "me-too" rồi gọi đây là "nguồn doanh thu bền vững". Cả bộ premium (xem ai đã thích mình, boost, thích không giới hạn) là bản sao Tinder Gold, và `competitive_parity` khai thẳng COMP-TINDER: behind, COMP-BUMBLE: parity, COMP-HEN: parity. Không một tính năng nào là độc quyền của Ghép Đôi Việt. → **Toang ở đâu:** người trả tiền cho "xem ai đã thích mình" sẽ chọn Tinder vì pool lớn gấp hàng trăm lần. Cùng tính năng thì giá trị nhân theo mạng lưới, và bên kia đã có sẵn triệu người. Đây là bẫy "parity is not enough": bằng nhau về tính năng nghĩa là thua, vì mạng lưới bên kia to hơn. → **Sửa:** gắn ít nhất một tính năng premium vào lợi thế "kết nối thật": boost chỉ kích hoạt sau khi match đã nhắn qua lại ít nhất 1 lần, hoặc "xem ai đã thích mình" chỉ hiện người đã điền hồ sơ đầy đủ và xác minh danh tính (cửa Tinder không làm được ở VN). Đặt tối thiểu một tính năng thành "ahead" trước COMP-TINDER trong `competitive_parity` và ghi rõ vì sao ahead.

2. **[major][market] BRD-G3:46.** BRD-G3 đặt mục tiêu "hoà vốn vận hành vào năm 2" với hai chỉ số premium-conversion-rate và arpu, nhưng PRD-PREMIUM không có một con số nào: không giá gói, không tỉ lệ chuyển đổi mục tiêu, không ARPU kỳ vọng. Spec nói "sẽ kiếm đủ tiền" mà không biết "đủ" là bao nhiêu hay "kiếm" theo cơ chế gì. → **Toang ở đâu:** lấy 100k MAU của BRD-G1, conversion 5% ra 5.000 người trả phí. ARPU 50.000đ/tháng cho 3 tỷ/năm; ARPU 200.000đ/tháng cho 14 tỷ/năm. Hai kịch bản lệch 4.5 lần và chính khoảng đó quyết định có hoà vốn hay không. Spec không có số nào để chạy phép tính này. → **Sửa:** thêm vào PRD-PREMIUM một bảng unit-economics tối thiểu làm điều kiện tiên quyết cho BRD-G3: dải giá gói, tỉ lệ chuyển đổi mục tiêu (ví dụ >=5% MAU trong năm 2), ARPU mục tiêu. Không cần chính xác, chỉ cần đủ để kiểm tra 100k MAU × X% × Y đồng có bằng chi phí vận hành không.

3. **[major][market] PRD-PREMIUM-E1-S2:339.** Story S2 (boost 30 phút) gắn ba persona P-URBAN, P-PROVINCE, P-RETURNEE. Body PRD nói P-PROVINCE hưởng lợi từ boost "trong cửa sổ thời gian ngắn", nhưng AC S2 (dòng 352) cho boost hiển thị tới "người dùng khác trong khu vực". P-PROVINCE sống nơi pool địa phương nhỏ và nhanh cạn. Boost vào pool gần rỗng không tăng match, chỉ tăng số lần bị bỏ qua bởi vài chục người đã thấy hồ sơ này. → **Toang ở đâu:** P-PROVINCE trả tiền boost, dùng xong không thấy kết quả, chấm tính năng là vô dụng rồi huỷ gói. Đúng cái risk đã ghi ở PRD-PREMIUM-E1 (người trả phí không thấy giá trị tương xứng) nhưng spec không nối risk đó vào persona này. ARPU bị kéo xuống bởi đám churner tỉnh lẻ không nhìn thấy kết quả. → **Sửa:** bỏ P-PROVINCE khỏi danh sách persona của S2 và thay bằng P-URBAN/P-RETURNEE (pool đủ dày), hoặc thêm một AC điều kiện: boost chỉ kích hoạt khi pool trong bán kính X km có tối thiểu N người hoạt động trong 7 ngày qua. Tối thiểu phải ghi giới hạn này vào risk register của S2.

## Theo lăng kính

### Market
- **[blocker] PRD-PREMIUM:227** (xem Top 3 #1): cả bộ premium là bản sao Tinder Gold, không tính năng nào tạo moat. → **Toang ở đâu:** parity với kẻ có mạng lưới lớn hơn là thua. → **Sửa:** một tính năng "ahead" gắn vào "kết nối thật" + cập nhật `competitive_parity`. Nguồn: thị phần Tinder VN https://vietcetera.com/en/top-5-dating-apps-in-vietnam-in-2024
- **[major] BRD-G3:46** (xem Top 3 #2): BRD-G3 có chỉ số nhưng PRD-PREMIUM không có con số nào. → **Toang ở đâu:** không có unit-economics để kiểm tra giả thuyết hoà vốn. → **Sửa:** thêm bảng giá/conversion/ARPU mục tiêu. Nguồn benchmark conversion freemium 3-8% https://firstpagesage.com/seo-blog/saas-freemium-conversion-rates/
- **[major] PRD-PREMIUM-E1-S2:339** (xem Top 3 #3): boost gắn P-PROVINCE nhưng pool tỉnh lẻ mỏng. → **Toang ở đâu:** churn vì trả tiền không thấy kết quả. → **Sửa:** đổi persona hoặc thêm AC ngưỡng mật độ pool.
- **[minor] PRD-PREMIUM:227.** `competitive_parity` liệt kê COMP-TINDER, COMP-BUMBLE, COMP-HEN nhưng bỏ trống COMP-FIKA, đối thủ đã khai trong BRD (dòng 152-156, threat: low). Fika định vị quality-over-quantity giống Ghép Đôi Việt nên vị trí so với Fika ở tầng premium là thông tin cần có. → **Toang ở đâu:** nếu Fika đang chạy premium tại VN với positioning "kết nối chất lượng", spec có thể đang đối đầu trực tiếp đối thủ gần nhất về định vị mà không nhận ra. Threat low không có nghĩa là không liên quan. → **Sửa:** thêm COMP-FIKA vào `competitive_parity` với verdict có căn cứ, hoặc ghi rõ lý do bỏ qua (ví dụ Fika chưa có gói trả phí tại VN).

### Product
Lăng kính này không có phát hiện trong vòng này.

### Tech
Lăng kính này không có phát hiện trong vòng này.

### Craft
Lăng kính này không có phát hiện trong vòng này.

## Lặp lại từ lần trước
- **BRD-G3 mồ côi con số (BRD-G3:46):** đã nói ở c1 (Top 3 #3, BRD:85) và c4 (BRD:130), vẫn chưa sửa. c4 còn để ngỏ "có tạo PRD-PREMIUM" như một việc cần chốt. Giờ PRD-PREMIUM đã có nhưng vẫn không kèm unit-economics, nên đúng cái lỗ hổng cũ chỉ chuyển nhà chứ chưa được vá.
- **Me-too / không có moat (PRD-PREMIUM:227):** cùng họ với me-too MATCH (c1), me-too CHAT (c3, PRD-CHAT:309), me-too EVENTS (c4, PRD-EVENTS:1). Lần thứ tư một feature-area khai parity/behind với COMP-TINDER mà không có một điểm "ahead" nào. Đây là lỗi hệ thống của cả spec, không riêng PRD-PREMIUM.
- **Định vị "kết nối thật" chưa thành đòn bẩy:** c1 và c3 đều flag định vị Hinge/quality bị bỏ trống ở tầng premium. PRD-PREMIUM tái phạm: vẫn không gắn tính năng trả phí nào vào lợi thế định vị.

## Đáng ghi thành quyết định (DEC-worthy)
- **Moat cho premium hay hạ kỳ vọng hoà vốn (PRD-PREMIUM:227, BRD-G3:46):** PO phải chốt một trong hai đường: hoặc cam kết ít nhất một tính năng premium "ahead" gắn vào "kết nối thật", hoặc hạ kỳ vọng của BRD-G3 kèm con số cụ thể để kiểm tra được. Ruling này đụng tới BRD-G3 (đang là mục tiêu đã duyệt) nên nên ghi vào Decision Register.
- **Unit-economics của PRD-PREMIUM (BRD-G3:46):** giá gói, tỉ lệ chuyển đổi mục tiêu, ARPU mục tiêu là số ràng buộc, một khi PO chốt thì nên khoá lại bằng DEC để khỏi mở lại ở vòng sau. Đây cũng là việc c4 đã treo ("có tạo PRD-PREMIUM / em số") nay tới lúc đóng.
- **P-PROVINCE trong scope boost (PRD-PREMIUM-E1-S2:339):** giữ hay bỏ P-PROVINCE khỏi S2 là một ruling về scope persona, PO quyết và nên ghi lại.
```

That looks clean. The only meaningful change was:
- "App mới zero network effect bán cùng thứ với giá ngang, không có lý do nào để khách bỏ kẻ đã có sẵn triệu người." was restructured slightly to flow better without repeating the point already made in the sentence before it
- "là thông tin liên quan" became "là thông tin cần có" (more natural)
- "để không tái litigate ở vòng sau" became "để khỏi mở lại ở vòng sau"
- Three identical "không trả về phát hiện" placeholders got slight variation: "không có phát hiện trong vòng này"

Now let me produce the final output:

# Critique: PRD-PREMIUM  ·  level 3  ·  lenses: market  [thiếu: product, tech, craft]

> Severity tally: blocker 1 · major 2 · minor 1

## Top 3: sửa ngay

1. **[blocker][market] PRD-PREMIUM:227.** Spec tự dán nhãn "me-too" rồi gọi đây là "nguồn doanh thu bền vững". Cả bộ premium (xem ai đã thích mình, boost, thích không giới hạn) là bản sao Tinder Gold, và `competitive_parity` khai thẳng COMP-TINDER: behind, COMP-BUMBLE: parity, COMP-HEN: parity. Không một tính năng nào là độc quyền của Ghép Đôi Việt. → **Toang ở đâu:** người trả tiền cho "xem ai đã thích mình" sẽ chọn Tinder vì pool lớn gấp hàng trăm lần. Cùng tính năng thì giá trị nhân theo mạng lưới, và bên kia đã có sẵn triệu người. Đây là bẫy "parity is not enough": bằng nhau về tính năng nghĩa là thua, vì mạng lưới bên kia to hơn. → **Sửa:** gắn ít nhất một tính năng premium vào lợi thế "kết nối thật": boost chỉ kích hoạt sau khi match đã nhắn qua lại ít nhất 1 lần, hoặc "xem ai đã thích mình" chỉ hiện người đã điền hồ sơ đầy đủ và xác minh danh tính (cửa Tinder không làm được ở VN). Đặt tối thiểu một tính năng thành "ahead" trước COMP-TINDER trong `competitive_parity` và ghi rõ vì sao ahead.

2. **[major][market] BRD-G3:46.** BRD-G3 đặt mục tiêu "hoà vốn vận hành vào năm 2" với hai chỉ số premium-conversion-rate và arpu, nhưng PRD-PREMIUM không có một con số nào: không giá gói, không tỉ lệ chuyển đổi mục tiêu, không ARPU kỳ vọng. Spec nói "sẽ kiếm đủ tiền" mà không biết "đủ" là bao nhiêu hay "kiếm" theo cơ chế gì. → **Toang ở đâu:** lấy 100k MAU của BRD-G1, conversion 5% ra 5.000 người trả phí. ARPU 50.000đ/tháng cho 3 tỷ/năm; ARPU 200.000đ/tháng cho 14 tỷ/năm. Hai kịch bản lệch 4.5 lần và chính khoảng đó quyết định có hoà vốn hay không. Spec không có số nào để chạy phép tính này. → **Sửa:** thêm vào PRD-PREMIUM một bảng unit-economics tối thiểu làm điều kiện tiên quyết cho BRD-G3: dải giá gói, tỉ lệ chuyển đổi mục tiêu (ví dụ >=5% MAU trong năm 2), ARPU mục tiêu. Không cần chính xác, chỉ cần đủ để kiểm tra 100k MAU × X% × Y đồng có bằng chi phí vận hành không.

3. **[major][market] PRD-PREMIUM-E1-S2:339.** Story S2 (boost 30 phút) gắn ba persona P-URBAN, P-PROVINCE, P-RETURNEE. Body PRD nói P-PROVINCE hưởng lợi từ boost "trong cửa sổ thời gian ngắn", nhưng AC S2 (dòng 352) cho boost hiển thị tới "người dùng khác trong khu vực". P-PROVINCE sống nơi pool địa phương nhỏ và nhanh cạn. Boost vào pool gần rỗng không tăng match, chỉ tăng số lần bị bỏ qua bởi vài chục người đã thấy hồ sơ này. → **Toang ở đâu:** P-PROVINCE trả tiền boost, dùng xong không thấy kết quả, chấm tính năng là vô dụng rồi huỷ gói. Đúng cái risk đã ghi ở PRD-PREMIUM-E1 (người trả phí không thấy giá trị tương xứng) nhưng spec không nối risk đó vào persona này. ARPU bị kéo xuống bởi đám churner tỉnh lẻ không nhìn thấy kết quả. → **Sửa:** bỏ P-PROVINCE khỏi danh sách persona của S2 và thay bằng P-URBAN/P-RETURNEE (pool đủ dày), hoặc thêm một AC điều kiện: boost chỉ kích hoạt khi pool trong bán kính X km có tối thiểu N người hoạt động trong 7 ngày qua. Tối thiểu phải ghi giới hạn này vào risk register của S2.

## Theo lăng kính

### Market
- **[blocker] PRD-PREMIUM:227** (xem Top 3 #1): cả bộ premium là bản sao Tinder Gold, không tính năng nào tạo moat. → **Toang ở đâu:** parity với kẻ có mạng lưới lớn hơn là thua. → **Sửa:** một tính năng "ahead" gắn vào "kết nối thật" + cập nhật `competitive_parity`. Nguồn: thị phần Tinder VN https://vietcetera.com/en/top-5-dating-apps-in-vietnam-in-2024
- **[major] BRD-G3:46** (xem Top 3 #2): BRD-G3 có chỉ số nhưng PRD-PREMIUM không có con số nào. → **Toang ở đâu:** không có unit-economics để kiểm tra giả thuyết hoà vốn. → **Sửa:** thêm bảng giá/conversion/ARPU mục tiêu. Nguồn benchmark conversion freemium 3-8% https://firstpagesage.com/seo-blog/saas-freemium-conversion-rates/
- **[major] PRD-PREMIUM-E1-S2:339** (xem Top 3 #3): boost gắn P-PROVINCE nhưng pool tỉnh lẻ mỏng. → **Toang ở đâu:** churn vì trả tiền không thấy kết quả. → **Sửa:** đổi persona hoặc thêm AC ngưỡng mật độ pool.
- **[minor] PRD-PREMIUM:227.** `competitive_parity` liệt kê COMP-TINDER, COMP-BUMBLE, COMP-HEN nhưng bỏ trống COMP-FIKA, đối thủ đã khai trong BRD (dòng 152-156, threat: low). Fika định vị quality-over-quantity giống Ghép Đôi Việt nên vị trí so với Fika ở tầng premium là thông tin cần có. → **Toang ở đâu:** nếu Fika đang chạy premium tại VN với positioning "kết nối chất lượng", spec có thể đang đối đầu trực tiếp đối thủ gần nhất về định vị mà không nhận ra. Threat low không có nghĩa là không liên quan. → **Sửa:** thêm COMP-FIKA vào `competitive_parity` với verdict có căn cứ, hoặc ghi rõ lý do bỏ qua (ví dụ Fika chưa có gói trả phí tại VN).

### Product
Lăng kính này không có phát hiện trong vòng này.

### Tech
Lăng kính này không có phát hiện trong vòng này.

### Craft
Lăng kính này không có phát hiện trong vòng này.

## Lặp lại từ lần trước
- **BRD-G3 mồ côi con số (BRD-G3:46):** đã nói ở c1 (Top 3 #3, BRD:85) và c4 (BRD:130), vẫn chưa sửa. c4 còn để ngỏ "có tạo PRD-PREMIUM" như một việc cần chốt. Giờ PRD-PREMIUM đã có nhưng vẫn không kèm unit-economics, nên đúng cái lỗ hổng cũ chỉ chuyển nhà chứ chưa được vá.
- **Me-too / không có moat (PRD-PREMIUM:227):** cùng họ với me-too MATCH (c1), me-too CHAT (c3, PRD-CHAT:309), me-too EVENTS (c4, PRD-EVENTS:1). Lần thứ tư một feature-area khai parity/behind với COMP-TINDER mà không có một điểm "ahead" nào. Đây là lỗi hệ thống của cả spec, không riêng PRD-PREMIUM.
- **Định vị "kết nối thật" chưa thành đòn bẩy:** c1 và c3 đều flag định vị Hinge/quality bị bỏ trống ở tầng premium. PRD-PREMIUM tái phạm: vẫn không gắn tính năng trả phí nào vào lợi thế định vị.

## Đáng ghi thành quyết định (DEC-worthy)
- **Moat cho premium hay hạ kỳ vọng hoà vốn (PRD-PREMIUM:227, BRD-G3:46):** PO phải chốt một trong hai đường: hoặc cam kết ít nhất một tính năng premium "ahead" gắn vào "kết nối thật", hoặc hạ kỳ vọng của BRD-G3 kèm con số cụ thể để kiểm tra được. Ruling này đụng tới BRD-G3 (đang là mục tiêu đã duyệt) nên nên ghi vào Decision Register.
- **Unit-economics của PRD-PREMIUM (BRD-G3:46):** giá gói, tỉ lệ chuyển đổi mục tiêu, ARPU mục tiêu là số ràng buộc, một khi PO chốt thì nên khoá lại bằng DEC để khỏi mở lại ở vòng sau. Đây cũng là việc c4 đã treo ("có tạo PRD-PREMIUM / em số") nay tới lúc đóng.
- **P-PROVINCE trong scope boost (PRD-PREMIUM-E1-S2:339):** giữ hay bỏ P-PROVINCE khỏi S2 là một ruling về scope persona, PO quyết và nên ghi lại.
