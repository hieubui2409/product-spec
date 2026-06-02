# Hướng dẫn dùng `cleanmatic:spec-critique` (Tiếng Việt)

Tài liệu này dành cho người làm sản phẩm (product owner). Mỗi tình huống được kể lại như một đoạn hội thoại mẫu, chạy
trên bộ spec ví dụ `product-spec/examples/acme-shop`. Bạn cứ nói bằng lời bình thường là được; phần ghi kèm cú pháp cờ
chỉ là cách viết tương đương cho ai thích gõ lệnh.

## spec-critique là gì, và khác `--validate` ở chỗ nào

`--validate` của `product-spec` là một bài kiểm tra cấu trúc. Nó soi xem có thiếu tiêu chí nghiệm thu không, có hạng mục
nào mồ côi không, có lệch giá trị cốt lõi không, rồi trả về đạt hoặc không đạt. Giọng của nó trung tính, ấm áp, và vì
chạy được trong quy trình tích hợp tự động (CI) nên kết quả phải ổn định, lần nào cũng như lần nào.

`spec-critique` cố tình đi ngược lại. Nó không chấm đạt hay trượt, nó chê. Nó có quan điểm, châm biếm, và còn tra cứu cả
thị trường bên ngoài, nên nó không bao giờ được đưa vào cổng CI. Cách nó làm việc là mượn lại các phát hiện cấu trúc của
`--validate` làm đạn, rồi nói thêm những điều mà `--validate` cố tình không nói: vì sao thứ này sẽ chết, nó đứng ở đâu
trên thị trường, chữ nghĩa có rõ ràng không, và bốn lăng kính soi chéo nhau ra sao.

> ⚠️ **Lằn ranh công kích cá nhân.** Từ mức 1 đến mức 4, công kích người viết là điều cấm. Mọi câu mỉa đều nhắm vào hiện
> vật, không nhắm vào bạn. Mức 5 (`--no-mercy`) mới gỡ lằn ranh đó và cho phép đá xéo cả người viết. Mức 6 (`--roast`)
> thì không chỉ cho phép mà bắt buộc chửi thẳng người viết, kiểu "lười tới mức không thêm nổi một con số". Mức 6 nguy
> hiểm, nghiêm cấm dùng ở bất cứ nơi nào có tính chuyên nghiệp, và chỉ chạy sau khi trợ lý cảnh báo rõ ràng rồi bạn xác
> nhận. Dù ở mức nào, mỗi dòng vẫn phải có bằng chứng và cách sửa. Riêng mức 6, cơn chửi chỉ được nhắm vào sự lười và
> cẩu thả trên chính bộ spec này, tuyệt đối không đụng tới danh tính, đặc điểm cá nhân, hay phẩm giá của một con người.

## Khi nào nên dùng

Hãy dùng khi bạn muốn một góc nhìn thật lòng và gắt gao về việc bộ spec có đáng làm hay không, chứ không phải một bài
kiểm tra đạt hay trượt. Những câu như "xé cái PRD này ra giúp tôi", "một nhà đầu tư hay một kỹ sư khó tính sẽ nói gì",
hay "cái này có phải đồ nhái không" là lúc nó phát huy tác dụng.

Đừng dùng nó để viết, để kiểm tra cấu trúc, để tách nhỏ, hay để vẽ sơ đồ spec. Tất cả những việc đó thuộc về
`cleanmatic:product-spec`.

---

## Theo từng tình huống

### 1. Chê toàn bộ spec

> **Bạn:** "Chê thẳng toàn bộ spec Acme Shop giúp tôi."
> **Trợ lý:** Quét lại cấu trúc ngay tại chỗ, đọc thêm các phán quyết đã lưu sẵn, cho bốn lăng kính soi song song, gộp
> lại thành một báo cáo, rồi ghi vào `docs/product/critique/<thời-gian>-all.md`. Lưu ý là quét toàn bộ khá tốn kém vì
> phải chạy hai lượt mô hình opus cộng với tra cứu thị trường.
>
> Cách gõ tương đương: `/spec-critique all`, hoặc gọn hơn là `/spec-critique`.

### 2. Chê một nhánh: một PRD, một epic, hay một story

> **Bạn:** "Soi cái PRD thanh toán xem có gì dở."
> **Trợ lý:** `/spec-critique PRD-CHECKOUT`. Kể cả khi bạn chỉ định đúng một story, toàn bộ chuỗi tổ tiên của nó (epic,
> rồi PRD, rồi mục tiêu kinh doanh, rồi tầm nhìn) đều được kéo lên làm bối cảnh. Lý do là một story chỉ có nghĩa khi
> được soi cùng với ý đồ ở các tầng phía trên.

### 3. Chọn lăng kính

> **Bạn:** "Chỉ soi mặt thị trường thôi."
> **Trợ lý:** `/spec-critique --market`. Có bốn cờ lăng kính: `--product`, `--tech`, `--market`, `--craft`. Không ghi cờ
> nào thì chạy cả bốn.

### 4. Hỏi đáp tương tác

> **Bạn:** "Tôi muốn tự chọn phạm vi và độ gắt trước khi chạy."
> **Trợ lý:** `/spec-critique --interactive`. Trợ lý sẽ hỏi ba câu ngắn: soi phạm vi nào, dùng lăng kính nào, và để mức
> mấy.

### 5. Đổi độ gắt của giọng

> **Bạn:** "Nhẹ nhàng thôi, tôi vừa viết xong." Dùng `--level 1` (hay `--warm`).
> **Bạn:** "Đừng nể nang gì cả." Dùng `--level 5` (`--no-mercy`). Trước khi chạy, trợ lý sẽ cảnh báo rằng mức này có thể
> đá xéo cả bạn, rồi hỏi bạn xác nhận.
> **Bạn:** "Chửi thẳng mặt tôi luôn, tôi chịu được." Dùng `--level 6` (`--roast`). Đây là mức sỉ nhục thẳng người viết.
> Trợ lý sẽ hiện cảnh báo nguy hiểm và hỏi xác nhận trước khi chạy, và mức này tuyệt đối không dành cho báo cáo chung hay
> môi trường công việc. Hãy coi nó như một chế độ "tự hành xác" riêng tư mà chỉ chính tác giả của bộ spec mới nên gọi.

### 6. Chạy ngoại tuyến, không tra mạng

> **Bạn:** "Đừng tra mạng, cứ dựa trên spec mà chê."
> **Trợ lý:** `/spec-critique --no-web`. Khi không tra mạng mà BRD lại không khai báo danh sách đối thủ, lăng kính thị
> trường sẽ gắn cờ "thiếu căn cứ cạnh tranh" chứ nhất quyết không bịa ra đối thủ.

### 7. Bắt lỗi lặp lại và đọc lại báo cáo cũ

> Mỗi lần chạy, bước hợp nhất đều đọc các báo cáo cũ trong `docs/product/critique/` để bắt những lỗi đã nhắc mà vẫn chưa
> sửa, kiểu "lần trước đã nói rồi đấy". Ngoài ra, sau mỗi lần bạn chạy `--validate`, nếu bộ spec đã thay đổi từ ba hạng
> mục trở lên kể từ lần chê gần nhất, một cái móc tự động (nếu bạn đã bật) sẽ nhắc bạn đúng một dòng. Nó chỉ nhắc nhẹ,
> không tự chạy và không chặn việc gì.

### 8. Cầu nối sang Quyết định (DEC)

> Nếu bước hợp nhất thấy một phát hiện đáng được ghi lại thành quyết định, chẳng hạn nó mâu thuẫn với một hạng mục đã
> được duyệt, trợ lý sẽ hỏi ý bạn theo ba hướng: giữ nguyên, đổi theo phát hiện, hay làm kiểu dung hòa. Chỉ khi bạn xác
> nhận, nó mới ghi một bản ghi `DEC-<số>` qua công cụ `decision_register.py`, kèm tiền tố `[nguồn: critique]` trong phần
> lý do để sau này phân biệt với quyết định sinh ra từ `--validate`. Nó không bao giờ tự ý sửa một hạng mục đã duyệt.

---

## Bốn lăng kính chê những gì

- **product** (chạy bằng opus): dùng các khung JTBD, Value Proposition Canvas, Kano, RICE, và truy ra giả định rủi ro
  nhất. Nó bắt những tính năng không ai cần, những chân dung người dùng dựng lên cho có, những chỗ làm dư thừa, và lối
  nhảy thẳng vào giải pháp khi chưa rõ vấn đề.
  > Ví dụ trên acme-shop: "`PRD-MOBILE` đặt di động thành mục tiêu của năm thứ hai, nhưng không có lấy một dòng nói rõ
  > nhu cầu của người mua trên di động khác gì so với trên web. Vì sao chết: làm ứng dụng chỉ để cho có ứng dụng. Sửa:
  > hãy nêu một nhu cầu chỉ di động mới đáp ứng được, ví dụ mua hàng lúc đang di chuyển."
- **tech** (chạy bằng sonnet): dùng INVEST, kiểm tra xem từng tiêu chí nghiệm thu có biến thành phép thử được không,
  truy các phụ thuộc bị giấu, và soi các yêu cầu phi chức năng. Nó bắt những tiêu chí không thể kiểm thử, những story
  không đạt INVEST, và những chỗ chỉ vẽ ra đường thuận lợi mà bỏ quên lỗi.
- **market** (chạy bằng sonnet, có tra mạng): dùng Lean Canvas, Porter, Blue Ocean, và phân tích đơn vị kinh tế. Nó bắt
  những thứ đi nhái, những chỗ không có đường ra tiền, và những sản phẩm không có lợi thế phòng thủ. Nó ưu tiên dùng
  danh sách đối thủ khai trong BRD, kèm trích dẫn từ web.
- **craft** (chạy bằng haiku): soi ngôn ngữ có dễ hiểu không, có đủ rõ ràng, gọn gàng, nhất quán và chính xác không,
  truy những tính từ không đo được, và bắt thuật ngữ dùng lung tung. Nó nhặt lỗi chính tả, tính từ mơ hồ, thuật ngữ
  trôi mỗi chỗ một kiểu, đoạn văn dài lê thê, và những chỗ nói suông không kèm ví dụ. Đây đúng là lớp mà `--validate`
  không bao giờ chạm tới.

---

## Cảm giác của từng mức giọng (cùng một lỗi)

Lấy ví dụ một tiêu chí nghiệm thu ghi "đăng nhập nhanh" mà không kèm ngưỡng đo được nào (`PRD-AUTH-E1-S1:16`). Dưới
đây là vài mức tiêu biểu để bạn cảm nhận; cả sáu mức (gồm mức 2 mỉa nhẹ và mức 4 mỉa nặng) nằm đầy đủ trong
`references/voice-and-tone.md`.

- **Mức 1 (`--warm`):** "Câu này dùng từ 'nhanh' nhưng chưa có con số đi kèm. Bạn thêm một ngưỡng cụ thể, chẳng hạn p95
  dưới 2 giây, để đội phát triển còn nghiệm thu được nhé."
- **Mức 3 (`--blunt`, mặc định):** "'Đăng nhập nhanh', nhanh là bao nhiêu? Không ai nghiệm thu được một tính từ. Vì sao
  chết: không có gì để đo thì chữ 'xong' thành chuyện ai muốn hiểu sao cũng được. Sửa: 'p95 dưới 2 giây trên mạng 4G'."
- **Mức 5 (`--no-mercy`):** "'Đăng nhập nhanh' là lời chúc chứ yêu cầu gì. Bạn gõ câu này ra thì chắc cũng tự biết nó
  rỗng tuếch. Đội phát triển nhận về chỉ còn nước xây theo tử vi. Vì sao chết: chữ 'xong' không ai định nghĩa nổi nên cứ
  sửa tới sửa lui không có điểm dừng. Sửa: 'p95 dưới 2 giây trên 4G'."
- **Mức 6 (`--roast`, ⚠️ chửi thẳng, không dùng nơi chuyên nghiệp):** "'Đăng nhập nhanh' à? Lười tới mức không buồn gõ
  lấy một con số, viết đại cho có rồi đi ngủ. Vì sao chết: 'nhanh' là bao nhiêu thì chỉ mình bạn biết, mà bạn thì có
  viết một dòng code nào đâu. Sửa đi, nếu còn chút tự trọng nghề nghiệp: 'p95 dưới 2 giây trên 4G, đo bằng RUM'. Có mười
  chữ, lười cỡ nào mới không gõ nổi."

---

## Đọc báo cáo

Mở đầu báo cáo là bảng đếm theo mức độ nghiêm trọng: chặn, nặng, nhẹ. Tiếp theo là phần "Top 3 sửa ngay", gom ba phát
hiện đáng sợ nhất từ mọi lăng kính. Phần thân chia theo từng lăng kính, mỗi phát hiện đi theo một mạch quen thuộc:
nhãn mức độ và lăng kính, vị trí `mã:dòng`, câu chê, lý do nó sẽ chết, rồi cách sửa. Cuối báo cáo là phần lỗi lặp lại từ
lần trước và phần các điểm đáng ghi thành quyết định.

## Ranh giới

spec-critique không sửa spec, nó chỉ ghi ra một báo cáo. Nó không phải cổng CI và không sinh ra mã nguồn. Mức 5 luôn
được cảnh báo và xác nhận trước khi chạy. Mức 6 (`--roast`) bắt buộc phải có cảnh báo nguy hiểm cùng lời xác nhận, và
không bao giờ được dùng trong môi trường chuyên nghiệp.
