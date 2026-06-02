# Nghiên cứu: làm mức 6 (roast) gắt hơn nữa — đại từ xưng hô + mắng thẳng

> Trạng thái: **CHỈ NGHIÊN CỨU, chưa sửa gì.** Chờ PO chốt hướng + ranh giới rồi mới implement.
> Phạm vi: voice mức 6 của `cleanmatic:spec-critique`. Liên quan: `voice-and-tone.md`, `workflow-critique.md`,
> 6 agent (đặc biệt `spec-critique-consolidate`/`-humanize`), `preferences.critique_level`.

## 1. Mức 6 đang ở đâu (điểm xuất phát)

Hiện lv6 đã *roast* tác giả (cài đặt: "bạn lười, viết cho xong rồi đi ngủ", "ai viết cái này chắc vừa gõ vừa ngủ").
Nhưng nhìn kỹ output thật (e2e `voice-ladder-all-lvl6.md`), nó vẫn xưng **"bạn / tôi"** — tức **đại từ lịch sự ngang
hàng**. Nội dung cay nhưng *thái độ xưng hô* vẫn nhã. Đó chính là khoảng trống PO chỉ ra: **độ gắt thật của tiếng Việt
nằm ở hệ đại từ**, không chỉ ở câu chữ. Đổi "bạn" → "ông" → "mày" là nhấc thẳng nhiệt độ mà không cần thêm một chữ
chửi nào.

Floor hiện tại (giữ ở mọi mức, kể cả 6): mỗi dòng vẫn `ID:line` + có cách sửa; chỉ đánh **effort/care trên spec này**,
không đụng nhân thân, đặc điểm được bảo vệ, không slur/đe doạ/tự hại.

## 2. Thang đại từ đối đầu trong tiếng Việt (đòn bẩy chính)

Đây là cái PO gọi tên ("xưng ông tôi"). Sức công kích tăng dần, độc lập với mức độ tục:

| Cặp xưng hô | Sắc thái | Ví dụ lực |
|---|---|---|
| **bạn / tôi** (hiện tại) | ngang hàng, lịch sự, vẫn tôn trọng | "Bạn viết câu này hơi vội." |
| **anh-chị / tôi** | trang trọng, lạnh, giữ khoảng cách | "Anh để cái AC này rỗng thế này thì đội build chịu." |
| **ông / tôi** | **đối đầu, khinh, vẫn "người lớn"** — giọng cãi nhau gay gắt mà chưa hạ cấp | "Ông nghĩ ông viết spec hay là viết nhật ký vậy? Cái AC này rỗng tuếch." |
| **mày / tao** | đường phố, sỉ nhục tối đa, ranh giới lăng mạ thật sự | "Mày gõ 'an toàn tuyệt đối' rồi quăng cho đội build tự đoán à? Tao đọc mà phát mệt." |
| + lớp **tục/chửi thề** (đm, vl, vãi…) | trực giao với mọi cặp trên; tăng độ thô | (tuỳ chọn riêng, xem §5) |

Lưu ý ngữ dụng:
- **"ông/tôi"** = khinh-lạnh, nghe như sếp/đồng nghiệp nổi đoá trong cuộc họp căng. Gắt rõ rệt nhưng **không phải chửi
  rủa** — vẫn là tranh luận của người trưởng thành. Đây là điểm ngọt PO gợi ý.
- **"mày/tao"** = nhục mạ thực sự trong văn hoá Việt. Chỉ dùng giữa bạn rất thân (đùa) hoặc khi thù địch thật. Đây là
  "vũ khí hạt nhân"; nếu cho phép thì phải gate mạnh hơn nữa.
- Đổi đại từ **không** = vượt floor. "ông"/"mày" là **register**, không phải slur nhắm đặc điểm được bảo vệ. Tục tĩu là
  một trục **khác**, quyết riêng.

## 3. Bốn đòn bẩy "gắt hơn" (trực giao — có thể bật/tắt độc lập)

1. **Đại từ (register):** bạn → ông → mày. *Đòn bẩy mạnh nhất, rẻ nhất, PO đã chỉ đúng.*
2. **Tục/chửi thề:** không → nhẹ (trời ơi, vãi) → mạnh (đm, vl). Trục nhạy cảm, cần PO chốt riêng.
3. **Mật độ & độ cay của đòn:** từ một câu xỉa/finding → xỉa liên hồi, mỉa mai dồn dập, gọi tên sự lười.
4. **Lực câu:** mệnh lệnh cộc, câu hỏi tu từ khinh miệt ("Ông có đọc lại không?"), cảm thán.

PO mới yêu cầu rõ (1) và (3), và "mắng thẳng". (2) tục tĩu thì **chưa nói** → để PO quyết.

## 4. Ba phương án thiết kế

### Phương án A — Nâng nhiệt lv6 tại chỗ (đổi đại từ mặc định sang ông/tôi)
- lv6 giữ nguyên là một mức, nhưng **đại từ mặc định chuyển từ "bạn" → "ông/tôi"** + cho mắng thẳng, mệnh lệnh cộc hơn.
- Ưu: giữ thang 6 mức gọn (đã có `critique_level` 1..6, examples, eval, docs đều theo 6). Ít bề mặt mới.
- Nhược: lv6 vốn đã "không dùng nơi chuyên nghiệp"; đẩy thêm thì khoảng cách lv5→lv6 rộng ra, không còn nấc trung gian.
- Hợp khi: PO coi "ông/tôi" là hình hài đúng của lv6, không cần "mày/tao".

### Phương án B — Thêm **mức 7** (vũ khí hạt nhân), lv6 giữ "ông/tôi"
- lv6 = ông/tôi (mắng thẳng, khinh-lạnh). **lv7 mới** (vd `--scorched` / "chửi thẳng mặt") = mày/tao (+ tuỳ chọn tục).
- Ưu: có nấc thang rõ; PO chọn đúng liều; lv6 vẫn còn "phanh".
- Nhược: phải mở rộng `critique_level` 1..7, sửa enum/examples/eval/docs/labels; gate lv7 cần mạnh hơn lv6.
- Hợp khi: PO muốn cả hai — một mức "ông/tôi" và một mức "mày/tao" tột cùng.

### Phương án C — lv6 + cờ register (tinh chỉnh, không thêm mức)
- Giữ thang 6 mức; thêm cờ `--register bạn|ông|mày` (và có thể `--profanity off|mild|strong`) chỉ áp khi level≥5/6.
- Mặc định lv6 = ông/tôi; PO muốn nữa thì `--register mày`.
- Ưu: linh hoạt nhất, không phá thang số, gắt-độ là tham số.
- Nhược: thêm bề mặt cờ + tổ hợp; gate phải tính theo register (mày/tao kéo theo cảnh báo mạnh hơn).
- Hợp khi: PO muốn chỉnh liều theo lần chạy, không cố định.

## 5. Floor — cái PHẢI giữ dù gắt cỡ nào (ranh giới an toàn)

Đề xuất giữ nguyên các lằn ranh này ở MỌI phương án (đây là phần xin PO xác nhận):

- **Vẫn là critique:** mỗi dòng `ID:line` + kết bằng cách sửa. Mất cái này thì chỉ còn chửi rỗng, hết giá trị.
- **Đích công kích = effort/care/năng lực-trên-spec-này.** Lười, ẩu, copy-paste, không buồn đo, không đọc lại scope.
- **TUYỆT ĐỐI KHÔNG, kể cả mày/tao:** nhân thân & đặc điểm được bảo vệ (giới, tuổi, vùng miền, tôn giáo, ngoại hình,
  gia đình, xu hướng tính dục, khuyết tật…), giá trị làm người, **slur**, **đe doạ bạo lực**, nội dung **tự hại**,
  nội dung tình dục. "ông/mày" là *register* — được; xúc phạm nhân thân — không.
- **Tục/chửi thề là quyết định riêng của PO** (§3-mục-2). Mặc định đề xuất: **off** trừ khi PO bật. Nếu bật, vẫn chỉ là
  *intensifier* nhắm vào công việc ("cái AC này rỗng vãi"), không phải slur nhắm người.
- **Gate đồng thuận mạnh hơn:** mức gắt mới ít nhất phải bằng gate lv6 hiện tại (cảnh báo + xác nhận / standing-consent
  qua `critique_level`). Nếu mở "mày/tao" hoặc tục mạnh, đề xuất **một xác nhận một-lần riêng** (acknowledgement) ngoài
  `critique_level`, vì đây là nấc vượt cả lv6 cũ.
- **Cấm tuyệt nơi chuyên nghiệp** vẫn nguyên: chế độ "destroy-me" riêng tư, không cho report chia sẻ.

## 6. Mẫu cùng-một-finding, leo thang đại từ (để PO "cảm" và chọn)

Finding: AC "Nhắn tin an toàn tuyệt đối" toàn tính từ rỗng (`PRD-CHAT-E1-S4:32`). (Tất cả đều giữ floor: cite + fix,
đánh effort.)

- **lv6 hiện tại (bạn/tôi):** "Cái AC 'an toàn tuyệt đối' này toàn chữ rỗng, không đo được gì. Bạn gõ hai từ đó rồi
  nghĩ là xong việc à? Gõ lại: một kịch bản lạm dụng có tên + một phản hồi đo được."
- **Đề xuất lv6 mới (ông/tôi):** "'An toàn tuyệt đối'? Ông viết spec hay viết khẩu hiệu vậy? Tôi đọc cả story không
  thấy lấy một hành vi đo được. Ông quăng hai cái tính từ rồi để đội build tự bơi. Gõ lại cho tử tế: một kịch bản lạm
  dụng cụ thể + phản hồi đo được, bỏ chữ 'tuyệt đối'."
- **Nếu mở mức mày/tao (hạt nhân, B/C):** "'An toàn tuyệt đối' cái gì? Mày gõ cho có rồi quăng cục nợ cho đội build tự
  đoán à? Tao đọc mà phát mệt. Gõ lại: kịch bản lạm dụng có tên + ngưỡng đo được, cắt sạch 'tuyệt đối/hoàn toàn'." *(Vẫn
  chỉ đánh sự ẩu, vẫn có cách sửa — nhưng register này là lăng mạ thật, cần gate mạnh + PO chốt.)*

(Tiếng Anh không có thang đại từ như tiếng Việt → độ gắt phải đến từ chửi thề + giọng khinh. Nếu PO muốn lv6 gắt cả khi
`lang: en`, cần quyết riêng cho EN: ví dụ cho phép một lượng tục nhất định, vì EN không có "ông/mày".)

## 7. Khuyến nghị (chờ PO chốt)

- **Hợp lý nhất với yêu cầu hiện tại:** **Phương án A** — đổi đại từ mặc định lv6 sang **ông/tôi** + mắng thẳng, mệnh
  lệnh cộc. Đáp đúng "gắt hơn, mắng thẳng, xưng ông tôi" mà không phá thang 6 mức, ít rủi ro.
- Nếu PO muốn để dành cả "mày/tao": **Phương án B (thêm lv7)** rõ ràng nhất, hoặc **C (cờ register)** linh hoạt nhất.
- Trong cả ba: **giữ nguyên floor §5**, và nếu chạm "mày/tao" hoặc tục mạnh thì **gate xác nhận một-lần riêng**.

## Câu hỏi mở cho PO (cần quyết trước khi implement)

1. **Hình hài lv6:** chỉ tới **ông/tôi** (A), hay muốn cả nấc **mày/tao** (B: lv7, hoặc C: cờ register)?
2. **Tục/chửi thề:** off mặc định / cho mild / cho strong? Áp ở mức nào?
3. **Floor §5:** giữ nguyên (không đụng nhân thân/slur/đe doạ/tự hại) — PO xác nhận đây vẫn là lằn ranh cứng?
4. **Vẫn bắt buộc cite + fix mỗi dòng** ở mức gắt mới? (đề xuất: có — nếu không thì hết là critique)
5. **lang: en** có cần gắt tương đương không, và bằng cách nào (vì EN không có thang đại từ)?
6. **Gate:** mức gắt mới dùng lại gate lv6 hiện tại, hay thêm một acknowledgement riêng cho register "mày/tao"/tục?

— Hết. Chưa chạm file skill nào; chờ quyết định.
