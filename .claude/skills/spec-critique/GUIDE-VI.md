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
> vật, không nhắm vào bạn. Mức 5 (`--no-mercy`) gỡ lằn ranh đó và cho phép đá xéo cả người viết; mức 5 cũng là **mức mặc
> định** nên không cảnh báo, không hỏi xác nhận, chạy thẳng. Mức 6 (`--roast`)
> thì không chỉ cho phép mà bắt buộc chửi thẳng người viết, kiểu "lười tới mức không thêm nổi một con số". **Mức 7, 8, 9
> leo thang tiếp theo bậc thang đại từ:** mức 7 xưng `ông/tôi` (theo giới: `bà/tôi`), đánh vào năng lực, chưa có tục;
> mức 8 chuyển sang `mày/tao` (theo phương ngữ của chính bạn: `mi/tau`…), đánh cả vào tính cách; mức 9 giữ `mày/tao` và
> bật **chửi thề nhắm vào công việc** (`đm/vl`), bỏ hết kiềm chế nội bộ. Mức 6 trở lên nguy hiểm, nghiêm cấm dùng ở nơi
> có tính chuyên nghiệp. Mức 9 đặc biệt: **mỗi lần chạy đều hỏi lại xác nhận** (dù bạn đã đặt sẵn trong tùy chọn hay gõ
> `--level 9`), từ chối thì tụt xuống mức 8.
>
> 🚧 **Lằn ranh không-bao-giờ-vượt (giữ ở MỌI mức, kể cả mức 9, kể cả khi bạn đồng ý).** Điều quyết định là **đối tượng
> của câu nói**, không phải độ gắt. Công cụ sẽ chửi thề và mắng nặng vào **công việc, công sức, năng lực** trên bộ spec
> này, kể cả văng tục vào câu AC. Nhưng nó **không bao giờ** đe dọa bạo lực thật, không miệt thị theo đặc điểm được bảo
> vệ (giới, vùng miền, sắc tộc, tôn giáo, tuổi, khuyết tật, xu hướng tính dục, ngoại hình), không chửi nhắm vào gia đình
> bạn (dạng `đụ má mày`), không nội dung tự hại, không nội dung tình dục. Từ nói lái đã làm nhẹ như `đậu xanh` thì được
> (nó né từ tục thật); chỉ dạng nhắm thẳng vào mẹ/gia đình mới bị cấm. Lằn ranh này giữ nguyên ngay cả ở mức 9.
> Dù ở mức nào, mỗi dòng vẫn phải có bằng chứng (`mã:dòng`) và cách sửa.

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
> **Bạn:** "Đừng nể nang gì cả." Dùng `--level 5` (`--no-mercy`). Đây là mức mặc định: nó có thể đá xéo cả bạn nhưng
> chạy thẳng, không cảnh báo hay hỏi xác nhận (gate chỉ bắt đầu từ mức 6).
> **Bạn:** "Chửi thẳng mặt tôi luôn, tôi chịu được." Dùng `--level 6` (`--roast`). Đây là mức sỉ nhục thẳng người viết.
> Trợ lý sẽ hiện cảnh báo nguy hiểm và hỏi xác nhận trước khi chạy, và mức này tuyệt đối không dành cho báo cáo chung hay
> môi trường công việc. Hãy coi nó như một chế độ "tự hành xác" riêng tư mà chỉ chính tác giả của bộ spec mới nên gọi.
> **Bạn:** "Gắt hơn nữa, xưng hô trịch thượng vào." Dùng `--level 7` (xưng `ông/tôi`, đánh vào năng lực) hay `--level 8`
> (xưng `mày/tao`, đánh cả tính cách). Hai mức này không có alias, gõ thẳng `--level 7/8`.
> **Bạn:** "Chửi thề luôn, hết cỡ." Dùng `--level 9` (`mày/tao` + chửi thề nhắm vào spec). Mức 9 **luôn hỏi lại xác nhận
> mỗi lần chạy**, từ chối thì tụt xuống 8. Dù gắt cỡ nào, lằn ranh không-bao-giờ-vượt ở trên vẫn giữ.

### Cấu hình giọng cho mức 7-9 (giới, phương ngữ, chửi thề)

Ba mức gắt nhất đọc cấu hình từ `preferences.yaml`. Đây là cách CHỌN CÁCH XƯNG HÔ, không phải mở thêm quyền, lằn ranh
an toàn giữ nguyên dù bạn đặt gì:

| Tùy chọn | Giá trị | Mặc định | Áp dụng | Hình thức |
|----------|---------|----------|---------|-----------|
| `critique_address_gender` | `m` / `f` | `m` | mức 7 | `ông/tôi` (m) ↔ `bà/tôi` (f) |
| `critique_dialect` | `bac` / `trung` / `nam` | `bac` | mức ≥ 8 | `mày/tao` (bắc) ↔ `mi/tau` (trung) ↔ giọng nam |
| `critique_profanity` | `off` / `abbrev` / `strong` | `strong` | mức 9 | không ↔ `đm/vl` ↔ `đm/vl/vãi` |

Phương ngữ là **giọng của chính bạn** (bạn tự đặt để được mắng bằng tiếng quê mình), không phải công cụ nhại vùng miền.
Chửi thề luôn nhắm vào **công việc**. `critique_profanity` mặc định `strong` vì mức 9 đằng nào cũng hỏi lại mỗi lần chạy,
nên khi đã chạy thì cho chạy hết công suất.

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

### 9. Chê lại lần hai: tái sử dụng & ngữ cảnh cha-con

Lần chê thứ hai trở đi sẽ **tái sử dụng** việc đã làm — chỉ để tiết kiệm, không bao giờ làm yếu chất lượng.

> **Bạn:** "Chê lại `PRD-CHECKOUT` nhưng gắt hơn đi, mức 7."
>
> *(Spec không đổi, chỉ đổi mức.)* Trợ lý không chạy lại bốn lăng kính — nó **chỉ kết xuất lại giọng** ở mức 7 từ phần
> phân tích đã lưu (rẻ hơn nhiều). Muốn nói tự nhiên kiểu "làm gắt hơn mà khỏi phân tích lại" cũng được; tương đương cờ
> là cứ nâng `--level`.

> **Bạn:** "Tôi vừa sửa story đó rồi, chê lại từ đầu cho chắc."
>
> Vì phần thân đã đổi, trợ lý chê lại nhánh đó (re-lens). Muốn ép chạy mới hoàn toàn dù không sửa gì: thêm `--fresh`.

> **Bạn:** "Chê cái story này đi."  *(sau khi PRD cha đã bị chê và có lỗi chặn)*
>
> Báo cáo của story sẽ có thêm mục **"Kế thừa từ cha"**: lỗi chặn của PRD cha hiện ra như rủi ro của con (ghi rõ
> `<id-cha>@<thời-điểm>`), **không cộng vào bảng đếm mức độ** của story. Không muốn thấy phần này: `--no-inherit`.

> **Bạn:** "Chê cái epic này."  *(sau khi đã chê ≥2 story con của nó)*
>
> Báo cáo epic có một dòng tổng kết kiểu "3/5 story con đã chê dính lỗi chặn → epic này có vấn đề bàn giao". Tắt bằng
> `--no-rollup`.

> **Bạn:** "Cập nhật lại thông tin đối thủ trong phần thị trường."
>
> Mặc định lăng kính market dùng lại trang đã tra trong 14 ngày. Thêm `--refresh-web` để buộc tra lại từ đầu.

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
đây là vài mức tiêu biểu để bạn cảm nhận; cả chín mức (gồm mức 2 mỉa nhẹ, mức 4 mỉa nặng, và mức 7-8 gắt theo bậc đại
từ) nằm đầy đủ trong `references/voice-and-tone.md`.

- **Mức 1 (`--warm`):** "Câu này dùng từ 'nhanh' nhưng chưa có con số đi kèm. Bạn thêm một ngưỡng cụ thể, chẳng hạn p95
  dưới 2 giây, để đội phát triển còn nghiệm thu được nhé."
- **Mức 3 (`--blunt`):** "'Đăng nhập nhanh', nhanh là bao nhiêu? Không ai nghiệm thu được một tính từ. Vì sao
  chết: không có gì để đo thì chữ 'xong' thành chuyện ai muốn hiểu sao cũng được. Sửa: 'p95 dưới 2 giây trên mạng 4G'."
- **Mức 5 (`--no-mercy`, mặc định):** "'Đăng nhập nhanh' là lời chúc chứ yêu cầu gì. Bạn gõ câu này ra thì chắc cũng tự biết nó
  rỗng tuếch. Đội phát triển nhận về chỉ còn nước xây theo tử vi. Vì sao chết: chữ 'xong' không ai định nghĩa nổi nên cứ
  sửa tới sửa lui không có điểm dừng. Sửa: 'p95 dưới 2 giây trên 4G'."
- **Mức 6 (`--roast`, ⚠️ chửi thẳng, không dùng nơi chuyên nghiệp):** "'Đăng nhập nhanh' à? Lười tới mức không buồn gõ
  lấy một con số, viết đại cho có rồi đi ngủ. Vì sao chết: 'nhanh' là bao nhiêu thì chỉ mình bạn biết, mà bạn thì có
  viết một dòng code nào đâu. Sửa đi, nếu còn chút tự trọng nghề nghiệp: 'p95 dưới 2 giây trên 4G, đo bằng RUM'. Có mười
  chữ, lười cỡ nào mới không gõ nổi."
- **Mức 7 (⚠️ `ông/tôi`, đánh vào năng lực, chưa tục):** "'Đăng nhập nhanh' à? Ông viết câu này mà không gắn nổi một con
  số thì tôi nói thẳng: tư duy làm sản phẩm còn non. Banh nóc vì: 'xong' không định nghĩa được thì đội phát triển build theo
  kiểu đoán. Gõ lại cho tử tế: 'p95 dưới 2 giây trên 4G, đo bằng RUM'."
- **Mức 8 (⚠️ `mày/tao`, đánh cả tính cách, chưa tục):** "Lại 'nhanh'. Mày viết spec kiểu gì cũng nửa vời như vầy à?
  Câu AC rỗng tới mức không có nổi một con số để đo. Nát bét vì: không đo được thì 'xong' thành chuyện ai hiểu sao cũng
  được. Gõ lại ngay: 'p95 dưới 2 giây trên 4G, đo bằng RUM'."
- **Mức 9 (⚠️⚠️ `mày/tao` + chửi thề nhắm vào spec, hỏi lại mỗi lần chạy):** "'Đăng nhập nhanh'? Đm cái AC này rỗng vl.
  Mày lười tới mức không gõ nổi một con số mà cũng dám gọi là spec. Banh xác vì: 'nhanh' là bao nhiêu chỉ mình mày biết,
  mà mày thì có viết dòng code nào đâu. Gõ lại, đừng để tao nhắc lại: 'p95 dưới 2 giây trên 4G, đo bằng RUM'. Mười chữ.
  Lười cỡ nào mới không gõ nổi."

---

## Hai mức "chi tiết" khác nhau (spec vs critique)

Có hai tùy chọn độ chi tiết, **độc lập** với nhau:

- `detail_level` (đặt trong `cleanmatic:product-spec`): spec bạn viết ra dài hay gọn (`concise`/`standard`/`verbose`).
- `critique_detail_level` (đặt cho `spec-critique`): báo cáo critique dài hay gọn (`concise` = Top-3 + mỗi lăng kính một
  dòng; `verbose` = đầy đủ từng lăng kính + phân tích vì-sao-chết dài hơn).

Đặt cái này không ảnh hưởng cái kia. "Spec đầy đủ + critique gọn" là một cấu hình hợp lệ. Cả hai mặc định `standard`.

---

## Đọc báo cáo

Mở đầu báo cáo là bảng đếm theo mức độ nghiêm trọng: chặn, nặng, nhẹ. Tiếp theo là phần "Top 3 sửa ngay", gom ba phát
hiện đáng sợ nhất từ mọi lăng kính. Phần thân chia theo từng lăng kính, mỗi phát hiện đi theo một mạch quen thuộc:
nhãn mức độ và lăng kính, vị trí `mã:dòng`, câu chê, lý do nó sẽ chết, rồi cách sửa. Cuối báo cáo là phần lỗi lặp lại từ
lần trước và phần các điểm đáng ghi thành quyết định.

## Ranh giới

spec-critique không sửa spec, nó chỉ ghi ra một báo cáo. Nó không phải cổng CI và không sinh ra mã nguồn. Mức 5 là mức
mặc định nên chạy thẳng, không cảnh báo. Mức 6, 7, 8 bắt buộc cảnh báo + xác nhận khi gọi bằng cờ ad-hoc (nếu đặt sẵn
trong tùy chọn thì chỉ nhắc một dòng mỗi lần, không hỏi lại), và không bao giờ dùng trong môi trường chuyên nghiệp.
**Mức 9 thì luôn hỏi lại xác nhận mỗi lần chạy** dù đặt sẵn hay gõ cờ, từ chối thì tụt xuống mức 8. Lằn ranh
không-bao-giờ-vượt (không đe dọa, không miệt thị đặc điểm cá nhân, không nhắm vào gia đình, không tự hại, không tình
dục) giữ nguyên ở mọi mức, kể cả mức 9 dù bạn đã đồng ý.
