# Hướng dẫn sử dụng `product-spec` cho Product Owner

> Tài liệu này dành cho **Product Owner (PO)** — người sở hữu sản phẩm, không cần biết lập trình.
> Bạn sẽ học cách dùng skill `product-spec` để biến những ý tưởng trong đầu thành một bộ tài liệu sản phẩm
> mạch lạc, có thể truy vết được, mà không phải viết một dòng code nào.
>
> Bản tiếng Anh: [`GUIDE-EN.md`](./GUIDE-EN.md).

---

## 1. Skill này giúp bạn điều gì?

Hãy hình dung bạn vừa có một ý tưởng sản phẩm. Trong đầu bạn có rất nhiều thứ: vấn đề muốn giải quyết,
khách hàng là ai, những tính năng cần làm, cái nào ưu tiên trước. Nhưng tất cả còn rời rạc, nằm trong các
ghi chú, cuộc họp, file Google Docs khác nhau.

`product-spec` giúp bạn **gom tất cả lại thành một cây tài liệu có trật tự**:

```
Tầm nhìn (Vision)
   └── 1 tài liệu mục tiêu kinh doanh (BRD)
          └── nhiều tài liệu tính năng (PRD)
                 └── các nhóm việc lớn (Epic)
                        └── các câu chuyện người dùng (Story) kèm tiêu chí nghiệm thu
```

Mỗi tầng đều liên kết với tầng trên bằng một mã định danh, nên bạn luôn trả lời được câu hỏi
*"Story này phục vụ mục tiêu kinh doanh nào?"* hay *"Mục tiêu này đã có tính năng nào gánh chưa?"*.

Điểm cốt lõi cần nhớ: **bạn nói chuyện với skill bằng ngôn ngữ sản phẩm bình thường.** Bạn mô tả mong muốn,
skill phỏng vấn lại bạn vài câu, rồi tự sinh ra tài liệu. Bạn không cần nhớ bất kỳ câu lệnh kỹ thuật nào.

---

## 2. Hai cách ra lệnh — và cách nào nên ưu tiên

Có hai cách để yêu cầu skill làm việc. **Cách ưu tiên là cách thứ nhất — nói bằng lời tự nhiên.**

### Cách 1 (ưu tiên): Nói bằng lời tự nhiên

Bạn chỉ cần mô tả điều bạn muốn, như đang nói chuyện với một trợ lý sản phẩm:

> *"Tôi muốn bắt đầu viết tài liệu cho một sản phẩm mới."*
>
> *"Giúp tôi thêm một tính năng thanh toán vào sản phẩm."*
>
> *"Kiểm tra giúp tôi bộ tài liệu hiện tại có chỗ nào còn thiếu không."*

Skill sẽ tự hiểu ý định của bạn và chạy đúng quy trình. Đây là cách tự nhiên nhất và được khuyến khích,
vì bạn không phải nhớ gì cả.

### Cách 2 (tương đương): Gõ "cờ lệnh" (flag)

Nếu bạn đã quen và muốn đi thẳng vào việc, mỗi hành động có một "cờ lệnh" ngắn gọn tương đương. Ví dụ:

```
/cleanmatic:product-spec --validate
```

Hai cách này **làm ra kết quả y hệt nhau**. Cờ lệnh chỉ là lối tắt cho người đã thạo. Trong suốt tài liệu
này, mỗi tình huống đều ghi rõ cả hai cách để bạn đối chiếu.

> 💡 **Mẹo:** Nếu không chắc nên làm gì, chỉ cần gõ `/cleanmatic:product-spec` (không kèm gì cả). Skill sẽ
> nhìn vào tình trạng tài liệu hiện tại của bạn và hiện một **bảng chọn (menu)** các hành động hợp lý tiếp theo.

---

## 3. Toàn bộ tình huống sử dụng — sắp theo thứ tự ưu tiên

Dưới đây là mọi việc skill làm được, sắp xếp **từ việc bạn cần làm trước đến việc làm sau**. Mỗi tình huống
gồm: khi nào dùng, một **kịch bản hội thoại mẫu** đầy đủ, và dòng cờ lệnh tương đương.

Tất cả ví dụ đều dùng một sản phẩm thật trong bộ mẫu của skill: **Acme Shop** — một cửa hàng trực tuyến cho
các thương hiệu thời trang nhỏ (boutique), giúp họ bán hàng trực tiếp cho người hâm mộ mà không qua sàn trung gian.

---

### Ưu tiên 1 — Khởi tạo sản phẩm mới từ con số 0

**Khi nào dùng:** Bạn bắt đầu hoàn toàn mới, chưa có tài liệu gì.

Đây luôn là bước đầu tiên. Skill sẽ dẫn bạn qua một cuộc phỏng vấn ngắn về tầm nhìn sản phẩm: vấn đề bạn
giải quyết, khách hàng mục tiêu (gọi là *persona*), giá trị cốt lõi, và định hướng 1–3 năm.

#### Kịch bản hội thoại

> **Bạn:** Tôi muốn bắt đầu viết tài liệu sản phẩm cho một cửa hàng trực tuyến phục vụ các thương hiệu
> thời trang nhỏ.
>
> **Skill:** Tuyệt vời, ta sẽ bắt đầu từ tầm nhìn. Trước tiên, sản phẩm này giải quyết *vấn đề* gì, và cho ai?
>
> **Bạn:** Các thương hiệu boutique đang phải bán qua các sàn lớn ăn hoa hồng hơn 30% và bị chôn vùi giữa
> đối thủ. Người hâm mộ muốn ủng hộ họ trực tiếp nhưng không có cách nào dễ dàng.
>
> **Skill:** Rõ rồi. Vậy ta có ít nhất hai nhóm người dùng: người mua hàng (*shopper*) và người quản trị
> cửa hàng (*store-admin*). Đúng không? Và *giá trị cốt lõi* — câu một dòng — của sản phẩm là gì?
>
> **Bạn:** Đúng. Giá trị cốt lõi: giúp các thương hiệu boutique bán trực tiếp cho fan, không qua trung gian.
>
> **Skill:** Còn *chỉ số ngôi sao Bắc Đẩu* (north-star metric) — con số quan trọng nhất bạn theo đuổi?
>
> **Bạn:** Tỷ lệ mua lại trên mỗi thương hiệu.
>
> **Skill:** Đã đủ để dựng tầm nhìn. Tôi sẽ tạo hai file: `PRODUCT.md` (các thông tin sản phẩm cô đọng) và
> `vision.md` (bản tường thuật tầm nhìn). Bạn xem qua và chỉnh nếu cần nhé.

Sau bước này, bạn có thư mục `docs/product/` với `PRODUCT.md` và `vision.md` đầu tiên.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec                # không cờ → skill phát hiện chưa có gì → mời khởi tạo
/cleanmatic:product-spec --product      # đi thẳng vào tạo/làm mới PRODUCT.md
```

---

### Ưu tiên 2 — Đổ một "bãi ý tưởng" và để skill tự sắp xếp

**Khi nào dùng:** Bạn đã có sẵn nhiều ý tưởng viết lộn xộn (từ ghi chú họp, brainstorm) và muốn skill **tự
phân rã** chúng thành mục tiêu kinh doanh, tính năng, epic và story.

Đây là tính năng tiết kiệm thời gian nhất. Bạn dán cả đoạn văn dài, skill sẽ tự bóc tách thành cấu trúc và
**hỏi lại bạn ở những chỗ chia tách chưa rõ** trước khi chốt.

#### Kịch bản hội thoại

> **Bạn:** Tôi có một bãi ghi chú, giúp tôi sắp xếp lại nhé: *"Người mua cần thêm hàng vào giỏ, rồi thanh
> toán một trang gồm địa chỉ và thẻ. Trả tiền qua Stripe. Gửi email xác nhận đơn. Người mua quay lại nên
> được lưu địa chỉ. Mục tiêu kinh doanh: onboard 100 thương hiệu trong 12 tháng và đạt 80% tỷ lệ mua lại
> trong 90 ngày."*
>
> **Skill:** Tôi đọc được hai *mục tiêu kinh doanh*:
> - BRD-G1 — Onboard 100 thương hiệu boutique trong 12 tháng.
> - BRD-G2 — Đạt 80% tỷ lệ mua lại trong 90 ngày.
>
> Và một *vùng tính năng* lớn: **Thanh toán (Checkout)**. Trong đó tôi thấy có thể tách thành hai nhóm việc:
> 1. Đăng nhập + nhập địa chỉ.
> 2. Thanh toán qua Stripe + xác nhận đơn.
>
> Bạn muốn tôi tách thành hai epic như vậy, hay gộp làm một?
>
> **Bạn:** Tách làm hai, vì phần thanh toán phụ thuộc phần đăng nhập.
>
> **Skill:** Hợp lý. Tôi sẽ tạo PRD "Checkout", epic E1 (Đăng nhập + Địa chỉ), epic E2 (Thanh toán Stripe,
> phụ thuộc E1), kèm các story tương ứng. Tôi sẽ trình bạn duyệt theo từng lô trước khi ghi.

Skill **không bao giờ tự chốt** những chỗ chia tách mơ hồ — nó luôn hỏi bạn theo lô (confirm-batch).

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --auto
```

---

### Ưu tiên 3 — Viết tài liệu mục tiêu kinh doanh (BRD)

**Khi nào dùng:** Bạn muốn ghi rõ các **mục tiêu kinh doanh**, chỉ số thành công, các bên liên quan, ràng
buộc và bối cảnh cạnh tranh. Mỗi sản phẩm chỉ có **một** BRD.

#### Kịch bản hội thoại

> **Bạn:** Giúp tôi viết tài liệu mục tiêu kinh doanh cho Acme Shop.
>
> **Skill:** Ta đã có hai mục tiêu từ trước (onboard 100 thương hiệu; 80% mua lại 90 ngày). Bạn muốn bổ
> sung *chỉ số thành công* cụ thể cho từng mục tiêu không?
>
> **Bạn:** Có: `brands-onboarded` mục tiêu 100, và `repeat-rate-90d` mục tiêu 80%.
>
> **Skill:** Còn *các bên liên quan* và *ràng buộc*?
>
> **Bạn:** Bên liên quan: nhà sáng lập, kỹ sư trưởng, 5 thương hiệu đối tác thiết kế. Ràng buộc: hạn ra mắt
> quý 3, ngân sách hạt giống ~300 nghìn đô.
>
> **Skill:** Và *bối cảnh cạnh tranh* — ai là đối thủ?
>
> **Bạn:** Shopify (mối đe dọa cao) và Big Cartel (trung bình).
>
> **Skill:** Đã đủ. Tôi sẽ ghi vào `brd.md`, khai báo đối thủ một lần ở đây để các PRD sau tham chiếu lại
> theo mã (COMP-SHOPIFY, COMP-BIGCARTEL) — tránh lặp lại thông tin.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --brd
```

---

### Ưu tiên 4 — Thêm một vùng tính năng (PRD)

**Khi nào dùng:** Bạn muốn mô tả chi tiết **một vùng tính năng** — ví dụ "Thanh toán", "Tìm kiếm", "Tài
khoản". Mỗi vùng tính năng là một PRD riêng. Một sản phẩm có nhiều PRD.

PRD là nơi bạn xác định: tính năng này phục vụ mục tiêu kinh doanh nào, dành cho persona nào, các yêu cầu
chức năng (sắp theo **MoSCoW**: Phải có / Nên có / Có thể có / Sẽ không làm lần này), yêu cầu phi chức năng,
rủi ro, và mức ngang bằng so với đối thủ.

#### Kịch bản hội thoại

> **Bạn:** Thêm cho tôi tính năng thanh toán.
>
> **Skill:** Tính năng "Checkout" này phục vụ mục tiêu kinh doanh nào?
>
> **Bạn:** Cả BRD-G1 và BRD-G2 — có thanh toán thì thương hiệu mới giao được đơn và khách mới mua lại.
>
> **Skill:** Dành cho persona nào, và mức ưu tiên?
>
> **Bạn:** Persona *shopper*. Đây là tính năng *Phải có*, thuộc giá trị cốt lõi, làm *ngay bây giờ*.
>
> **Skill:** Ta liệt kê yêu cầu theo MoSCoW nhé. *Phải có* gồm những gì?
>
> **Bạn:** Giỏ hàng thêm/xóa/đổi số lượng; form thanh toán một trang; trả tiền qua Stripe; email xác nhận đơn.
>
> **Skill:** *Nên có* / *Có thể có* / *Sẽ không làm lần này*?
>
> **Bạn:** Nên có: lưu địa chỉ cho khách quay lại. Có thể có: Apple/Google Pay. Sẽ không làm: đa tiền tệ.
>
> **Skill:** Có *rủi ro* nào cần ghi nhận không?
>
> **Bạn:** Có. Stripe xác minh KYC chậm có thể chặn ra mắt (tác động cao). Và form một trang dài trên di động
> dễ làm khách bỏ giỏ (tác động trung bình).
>
> **Skill:** Tôi ghi PRD `prds/checkout.md` với mã `PRD-CHECKOUT`, ngày mục tiêu 2026-09-30, kèm sổ rủi ro
> và bảng so sánh đối thủ (kém Shopify về hệ sinh thái nhưng ngang Big Cartel về sự đơn giản).

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --prd checkout
/cleanmatic:product-spec --prd            # skill sẽ hỏi tên vùng tính năng
```

---

### Ưu tiên 5 — Thêm một nhóm việc lớn (Epic)

**Khi nào dùng:** Một PRD thường to và cần chia thành vài **epic** — nhóm việc lớn, mỗi nhóm tạo ra một
kết quả rõ ràng.

#### Kịch bản hội thoại

> **Bạn:** Trong PRD thanh toán, tách giúp tôi phần đăng nhập và nhập địa chỉ thành một epic.
>
> **Skill:** Epic này có mục tiêu gì, và đo bằng tiêu chí nào?
>
> **Bạn:** Mục tiêu: người mua đăng nhập (qua magic-link) và nhập địa chỉ giao hàng, sẵn sàng trả tiền. Tiêu
> chí: tỷ lệ đăng nhập thành công trên 90%, hoàn tất bước địa chỉ trên 80%.
>
> **Skill:** Có rủi ro riêng cho epic này không?
>
> **Bạn:** Email magic-link có thể rơi vào hộp spam, chặn đăng nhập. Tác động trung bình.
>
> **Skill:** Tôi tạo epic `PRD-CHECKOUT-E1` (Đăng nhập + Địa chỉ), ngày mục tiêu 2026-08-15. Phần thanh toán
> và xác nhận sẽ là epic kế tiếp `PRD-CHECKOUT-E2`, phụ thuộc epic này.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --epic PRD-CHECKOUT
/cleanmatic:product-spec --epic           # skill sẽ hỏi epic này thuộc PRD nào
```

---

### Ưu tiên 6 — Thêm câu chuyện người dùng (Story) kèm tiêu chí nghiệm thu

**Khi nào dùng:** Bạn chia một epic thành các **story** — đơn vị nhỏ nhất, kể từ góc nhìn người dùng, kèm
**tiêu chí nghiệm thu (Acceptance Criteria)** rõ ràng để biết khi nào "xong".

Story là nơi duy nhất chứa tiêu chí nghiệm thu (PRD không lặp lại chúng). Mỗi story mang một kích cỡ tương
đối: `S` / `M` / `L` — **không bao giờ** dùng story point hay giờ công.

#### Kịch bản hội thoại

> **Bạn:** Thêm story đăng nhập bằng magic-link tại bước thanh toán.
>
> **Skill:** Hãy phát biểu theo mẫu "Là một… tôi muốn… để…".
>
> **Bạn:** Là một người mua, tôi muốn đăng nhập bằng magic-link tại bước thanh toán, để khỏi phải nhớ mật
> khẩu và mua nhanh hơn.
>
> **Skill:** Tiêu chí nghiệm thu là gì? (Mỗi tiêu chí nên ở dạng "Cho trước… khi… thì…".)
>
> **Bạn:**
> 1. Cho trước người mua ở bước thanh toán, khi họ nhập email hợp lệ, thì email magic-link được gửi trong
>    vòng 30 giây.
> 2. Cho trước người mua đã bấm vào magic-link, khi họ quay lại tab, thì giỏ hàng được giữ nguyên và form
>    thanh toán điền sẵn địa chỉ đã lưu (nếu có).
>
> **Skill:** Kích cỡ ước lượng?
>
> **Bạn:** Cỡ M.
>
> **Skill:** Tôi ghi story `PRD-CHECKOUT-E1-S1` với hai tiêu chí nghiệm thu trên.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --story PRD-CHECKOUT-E1
/cleanmatic:product-spec --story          # skill sẽ hỏi story này thuộc epic nào
```

---

### Ưu tiên 7 — Kiểm tra chất lượng bộ tài liệu (Validate)

**Khi nào dùng:** Bất cứ lúc nào bạn muốn biết bộ tài liệu có "lành" không: có story nào mồ côi (không gắn
epic)? có link gãy? có mục tiêu kinh doanh nào chưa tính năng nào gánh? story có viết tốt theo nguyên tắc
INVEST không? có chỗ nào lệch khỏi giá trị cốt lõi, hay mâu thuẫn với quyết định đã chốt?

Skill chạy **hai lớp**: lớp máy kiểm tra cấu trúc (mồ côi, link gãy, thiếu tiêu chí nghiệm thu, trùng mã),
và lớp phán đoán (chất lượng story, sự mơ hồ, lệch giá trị, trùng lặp ý nghĩa). Kết quả là một **báo cáo dễ đọc**.

#### Kịch bản hội thoại

> **Bạn:** Kiểm tra giúp tôi bộ tài liệu hiện tại có gì cần sửa không.
>
> **Skill:** Tôi đã quét. Tóm tắt:
> - ✅ Truy vết: mọi story đều gắn epic, mọi epic gắn PRD, mọi PRD gắn mục tiêu. Không có mục mồ côi.
> - ⚠️ Cảnh báo: epic `PRD-CHECKOUT-E1` đang ở trạng thái *nháp* trong khi PRD cha đã *duyệt* — bạn có muốn
>   nâng trạng thái epic không?
> - 💡 Góp ý chất lượng: story `PRD-CHECKOUT-E2-S1` viết tốt theo INVEST, tiêu chí nghiệm thu đo được. Không
>   thấy lệch giá trị cốt lõi.
>
> Bạn muốn tôi siết chặt (mọi cảnh báo đều chặn) hay chỉ liệt kê để bạn quyết?
>
> **Bạn:** Chỉ liệt kê thôi.

> ⚠️ **Quan trọng — skill không bao giờ tự đảo ngược quyết định đã duyệt.** Nếu một thông tin mới mâu thuẫn
> với tài liệu đã ở trạng thái *approved*, skill sẽ nêu rõ và cho bạn ba lựa chọn: **Giữ** bản cũ, **Đổi**
> sang bản mới (và duyệt lại), hoặc **Kết hợp** (ghi nhận cả hai, lên kế hoạch xử lý sau).

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --validate
/cleanmatic:product-spec --validate --strict   # cảnh báo lỗi sẽ CHẶN hành động (dùng trước khi chốt)
```

---

### Ưu tiên 8 — Áp dụng một thay đổi mà không mất công sức cũ (Update)

**Khi nào dùng:** Có gì đó thay đổi — mục tiêu, phạm vi, một quyết định — và bạn muốn cập nhật mà **không
ghi đè** lên những đoạn văn bạn đã chăm chút.

Skill sẽ hỏi cái gì đổi, tính ra những phần bên dưới **bị ảnh hưởng**, rồi **gắn cờ để bạn xem lại** —
chứ không tự viết lại. Việc sinh lại nội dung là tùy chọn, do bạn bật cho từng mục.

#### Kịch bản hội thoại

> **Bạn:** Hạn ra mắt thanh toán dời từ 30/9 sang 15/10. Cập nhật giúp tôi.
>
> **Skill:** Thay đổi này chạm tới PRD `PRD-CHECKOUT` (ngày mục tiêu) và có thể ảnh hưởng hai epic con E1, E2
> đang xếp lịch trước đó. Tôi sẽ:
> - Cập nhật ngày mục tiêu của PRD.
> - **Gắn cờ** E1 và E2 để bạn xem lại lịch — tôi *không* tự sửa phần mô tả bạn đã viết.
> - Ghi một dòng vào nhật ký thay đổi (`change-log.md`).
>
> Bạn có muốn tôi sinh lại đoạn lịch trong từng epic không, hay để bạn tự chỉnh?
>
> **Bạn:** Để tôi tự chỉnh E1, còn E2 thì nhờ skill sinh lại.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --update
```

---

### Ưu tiên 9 — Ký duyệt / chốt một tài liệu (Approve)

**Khi nào dùng:** Một BRD/PRD/Epic/Story đã chín và bạn muốn **đóng dấu phê duyệt** — ghi lại người duyệt và
ngày duyệt, chuyển trạng thái sang `approved`.

Trước khi đóng dấu, skill chạy kiểm tra (cảnh báo sẽ nhắc nhưng không chặn), rồi ghi nhận người + ngày. Skill
**không bao giờ** tự đặt `approved` nếu bạn không yêu cầu duyệt và không cung cấp người + ngày.

#### Kịch bản hội thoại

> **Bạn:** Tôi muốn ký duyệt PRD thanh toán.
>
> **Skill:** Tôi chạy kiểm tra nhanh trước. Có một cảnh báo: hai epic con còn ở trạng thái *nháp*. Cảnh báo
> này không chặn việc duyệt PRD. Bạn xác nhận duyệt chứ? Ai là người duyệt và ngày nào?
>
> **Bạn:** Người duyệt: Jane Doe, ngày hôm nay. Xác nhận duyệt.
>
> **Skill:** Đã ghi `owner: Jane Doe`, ngày duyệt, và chuyển `status: approved` cho `PRD-CHECKOUT`.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --approve
```

---

### Ưu tiên 10 — Lấy bản tóm tắt 1 trang cho lãnh đạo (Summary)

**Khi nào dùng:** Bạn cần một **bản tóm tắt một trang** để gửi nhà đầu tư, lãnh đạo, hoặc đối tác — gói gọn
tầm nhìn, mục tiêu, phạm vi và tiến độ.

#### Kịch bản hội thoại

> **Bạn:** Tạo cho tôi bản tóm tắt một trang về Acme Shop để gửi nhà đầu tư.
>
> **Skill:** Tôi tổng hợp từ tầm nhìn, BRD và các PRD thành `exec-summary.md`: giá trị cốt lõi, hai mục tiêu
> kinh doanh kèm chỉ số, vùng tính năng đang làm (Thanh toán, hạn quý 3), và bối cảnh cạnh tranh. Bạn muốn
> bản markdown thường hay kèm bản HTML đẹp để in?
>
> **Bạn:** Cả hai.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --summary
```

---

### Ưu tiên 11 — Vẽ bộ tài liệu thành hình ảnh trực quan (Visualize)

**Khi nào dùng:** Bạn muốn *nhìn thấy* bộ tài liệu thay vì đọc từng file — cây truy vết, lộ trình theo thời
gian, bảng kanban, lưới rủi ro, ma trận đối thủ…

Skill có nhiều "góc nhìn" (view). Mỗi góc nhìn xuất ra một trong ba dạng: **ASCII** (chữ thuần, xem ngay
trong cửa sổ chat), **Mermaid** (sơ đồ trong markdown), hoặc **HTML** (một file đẹp, mở thẳng trong trình
duyệt, không cần cài server).

Các góc nhìn chính:

| Bạn muốn thấy… | Tên góc nhìn |
|---|---|
| Cây truy vết toàn bộ (mục tiêu → PRD → epic → story) | `tree` |
| Lộ trình theo thời gian (Bây giờ / Tiếp theo / Sau này) | `roadmap`, `time` |
| Bảng kanban kéo theo trạng thái / lộ trình / ưu tiên | `board` |
| Trình khám phá ba chế độ (Cây / Thẻ phẳng / Bảng cây) | `explorer` |
| Mức độ phủ mục tiêu, chỗ còn trống | `gap`, `heatmap` |
| Ưu tiên theo MoSCoW (Phải/Nên/Có thể/Không) | `moscow` |
| Lưới rủi ro (tác động × khả năng xảy ra) | `risk` |
| Ma trận so đối thủ + bản đồ nhiệt đe dọa | `competition` |
| Trang tổng hợp nhiều chiều trên một mặt | `dashboard` |
| Bản đồ theo persona, phạm vi, thay đổi so với mốc cũ | `persona`, `scope`, `delta` |

#### Kịch bản hội thoại

> **Bạn:** Cho tôi xem cây truy vết của Acme Shop.
>
> **Skill:** Đây là góc nhìn `tree` dạng chữ:
> ```
> [goal:BRD-G1] Onboard 100 boutique brands · approved
>   [prd:PRD-CHECKOUT] Checkout PRD · approved
>     [epic:PRD-CHECKOUT-E1] Sign-In + Address · draft
>       [story:PRD-CHECKOUT-E1-S1] Magic-link sign-in · draft
>     [epic:PRD-CHECKOUT-E2] Stripe Payment · draft
>       [story:PRD-CHECKOUT-E2-S1] Pay with Stripe · draft
> ```
> Bạn muốn bản HTML đẹp hơn để chia sẻ không?
>
> **Bạn:** Có, và cho tôi luôn bảng kanban theo trạng thái.
>
> **Skill:** Tôi xuất hai file HTML vào `docs/product/visuals/`: một cây truy vết và một bảng kanban nhóm
> theo trạng thái. Mở thẳng bằng trình duyệt, có ô tìm kiếm và bộ lọc, bấm vào thẻ để xem chi tiết.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --viz tree
/cleanmatic:product-spec --viz tree --format html
/cleanmatic:product-spec --viz board --group-by status
/cleanmatic:product-spec --viz roadmap
/cleanmatic:product-spec --viz risk
/cleanmatic:product-spec --viz competition
/cleanmatic:product-spec --viz dashboard
/cleanmatic:product-spec --viz explorer
```

> 💡 Muốn ẩn các mục đã hoãn (đánh dấu "sẽ không làm")? Thêm ý "ẩn các mục đã hoãn" — tương đương cờ
> `--filter-wont`.

---

### Ưu tiên 12 — Xuất một tài liệu đọc-một-lần để chia sẻ (Export)

**Khi nào dùng:** Bạn muốn gói một lát cắt của bộ tài liệu thành **một file duy nhất, tự chứa** để gửi cho
ai đó đọc — không cần họ mở từng file.

Bạn chọn lấy toàn bộ hay một nhánh (theo mã), chọn các tầng muốn đưa vào, độ chi tiết, và định dạng (markdown
hoặc HTML in được).

#### Kịch bản hội thoại

> **Bạn:** Xuất cho tôi toàn bộ nhánh thanh toán thành một tài liệu để gửi cho team thiết kế.
>
> **Skill:** Tôi gom PRD Checkout cùng các epic và story con thành một file tự chứa trong
> `docs/product/exports/`. Bạn muốn độ chi tiết nào: *gọn* (chỉ tiêu đề + tóm tắt), *vừa* (kèm bối cảnh),
> hay *đầy đủ*? Và định dạng markdown hay HTML để in?
>
> **Bạn:** Mức vừa, bản HTML in được.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --export PRD-CHECKOUT --format html
/cleanmatic:product-spec --export all                       # xuất toàn bộ
/cleanmatic:product-spec --export PRD-CHECKOUT --layers prd,epic,story --depth full
```

---

### Ưu tiên 13 — Làm việc bằng tiếng Việt (hoặc tiếng Anh)

**Khi nào dùng:** Bạn muốn cuộc phỏng vấn và phần nội dung được viết bằng tiếng Việt (hoặc tiếng Anh).

Skill song ngữ. Khi bạn chọn tiếng Việt, các câu hỏi phỏng vấn, phần mô tả tầm nhìn, mô tả story, tiêu chí
nghiệm thu, và nhãn trên hình trực quan đều bằng tiếng Việt. Riêng **mã định danh** (`BRD-G1`, `PRD-CHECKOUT`)
và **các khóa cấu trúc** (`personas`, `scope`, `moscow`…) luôn giữ tiếng Anh để cấu trúc ổn định, dùng chung
được giữa hai ngôn ngữ.

#### Kịch bản hội thoại

> **Bạn:** Từ giờ hãy phỏng vấn và viết tài liệu bằng tiếng Việt.
>
> **Skill:** Đã chuyển sang tiếng Việt. Các mã như `PRD-CHECKOUT` và các nhãn cấu trúc vẫn giữ tiếng Anh để
> đảm bảo tính nhất quán; còn lại tôi sẽ viết bằng tiếng Việt tự nhiên.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --lang vi
/cleanmatic:product-spec --lang en
```

---

## 4. Quy trình điển hình từ đầu đến cuối

Nếu bạn mới bắt đầu, đây là trình tự khuyên dùng:

1. **Khởi tạo** sản phẩm (tầm nhìn + persona + giá trị cốt lõi).
2. **Viết BRD** — chốt mục tiêu kinh doanh và chỉ số.
3. **Thêm PRD** cho từng vùng tính năng quan trọng nhất.
4. **Chia epic và story**, kèm tiêu chí nghiệm thu (hoặc dùng "bãi ý tưởng" để skill tự phân rã).
5. **Kiểm tra** (validate) để bắt lỗi cấu trúc và chất lượng.
6. **Trực quan hóa** để nhìn toàn cảnh và phát hiện chỗ trống.
7. **Cập nhật** khi có thay đổi, **ký duyệt** khi đã chín.
8. **Tóm tắt / xuất** để chia sẻ với lãnh đạo và các đội khác.

Bạn không buộc phải đi đúng thứ tự này — nhưng đây là lối đi mượt nhất.

---

## 5. Những điều skill này KHÔNG làm (để bạn yên tâm)

- **Không viết code.** Đây là skill tài liệu sản phẩm. Nếu bạn cần code, đội kỹ thuật sẽ viết dựa trên story + tiêu chí nghiệm thu.
- **Không ước lượng bằng story point hay giờ công.** Story chỉ mang kích cỡ `S` / `M` / `L`.
- **Không ghi đè đoạn văn bạn viết tay.** Khi cập nhật, skill gắn cờ và hỏi trước khi sinh lại.
- **Không tự đảo ngược quyết định đã duyệt.** Mâu thuẫn luôn được nêu ra để bạn chọn Giữ / Đổi / Kết hợp.
- **Không cần Internet khi chạy.** Sau khi cài đặt một lần, mọi thứ chạy trên máy bạn. Tài liệu nằm gọn
  trong `docs/product/` của dự án.

---

## 6. Gặp khó? Cứ hỏi thẳng skill

Cách dễ nhất khi bí: **mở skill và hỏi bằng lời.** Ví dụ *"Tôi nên làm gì tiếp theo?"* hoặc *"Bộ tài liệu
của tôi còn thiếu gì?"*. Skill sẽ nhìn vào tình trạng hiện tại và gợi ý bước hợp lý.

Để biết chi tiết kỹ thuật sâu hơn (dành cho người vận hành), xem `SKILL.md` và thư mục `references/` trong
thư mục skill, hoặc `README.md` ở gốc dự án.
