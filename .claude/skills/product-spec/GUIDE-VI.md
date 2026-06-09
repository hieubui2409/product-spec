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

## 2. Khái niệm cốt lõi — mô hình tư duy (đọc một lần)

Bảy ý sau giải thích *vì sao* skill hành xử như vậy. Nắm được chúng thì mọi thứ còn lại đều sáng ra.

1. **Cây năm tầng + truy vết.** Tầm nhìn → **một** BRD → **nhiều** PRD → Epic → Story. Mỗi tầng liên kết
   *lên* cha của nó bằng một mã, nên bạn luôn truy được một story về tận mục tiêu kinh doanh nó phục vụ — và
   phát hiện một mục tiêu chưa có tính năng nào gánh.
2. **Một nhà cho mỗi dữ kiện (DRY).** Mỗi dữ kiện sống đúng một chỗ, nơi khác tham chiếu bằng mã. Persona →
   `PRODUCT.md`; mục tiêu kinh doanh → BRD; **tiêu chí nghiệm thu → chỉ ở story** (PRD không lặp lại); đối
   thủ khai báo một lần ở BRD rồi trích theo mã. Đừng mong cùng một dữ kiện viết hai nơi — đó là chủ đích.
3. **Cấu trúc là dữ liệu; câu chữ là của bạn.** Máy đọc **frontmatter** (mã, `status`, `scope`, `moscow`,
   `metrics`) làm nguồn-sự-thật — không bao giờ đoán nghĩa từ tiêu đề. Còn phần văn tường thuật bạn viết thì
   skill **không bao giờ ghi đè**.
4. **Skill phỏng vấn; không tự suy diễn.** Skill hỏi trước khi quyết bất cứ điều gì thuộc về bạn — persona,
   phạm vi (trong / ngoài / giá trị-cốt-lõi), ký duyệt. Nó chỉ điền mặc định cho phần khuôn-mẫu sửa-được, và
   khi điền thì nói rõ.
5. **Không có gì được duyệt một cách lặng lẽ.** `status` chuyển `draft → approved` **chỉ khi** bạn duyệt
   tường minh và cung cấp người duyệt + ngày. Skill không tự đóng dấu.
6. **Không đảo ngược âm thầm.** Khi một khẳng định mới mâu thuẫn tài liệu đã **duyệt**, skill dừng lại và cho
   ba lựa chọn — **Giữ** (bác khẳng định mới), **Đổi** (và duyệt lại), hoặc **Kết hợp** (ghi cả hai, hẹn xử
   lý sau). Nó không lặng lẽ chọn phe.
7. **Tùy chọn được hỏi một lần.** Từ sớm, skill hỏi **ngôn ngữ**, **mức chi tiết**, và **hồ sơ tương tác**
   (vặn sâu tới đâu, gợi ý bao nhiêu), lưu lại, và **không hỏi lại**. Đổi bất cứ lúc nào bằng cách nói, hoặc
   qua `--lang` / `preferences.py --set`.

---

## 3. Lộ trình học của bạn

Đây là bộ tài liệu phức tạp — đừng cố học mọi cờ lệnh cùng lúc. Hãy đi theo lộ trình:

**Ngày 1 — dựng một lát cắt mỏng từ đầu đến cuối (xương sống):**
`khởi tạo` → `BRD` → một `PRD` → một `epic` → một `story` → `validate`. Khi đã đưa một mục tiêu xuống tận
một story có tiêu chí nghiệm thu rồi kiểm tra, bạn đã hiểu toàn bộ skill.

**Tuần 1 — giữ cho khỏe và chia sẻ:**
`ký duyệt` tài liệu đã chín, `cập nhật` khi có thay đổi, `status` để xem nhanh, rồi `trực quan hóa` /
`tóm tắt` / `xuất` để trình người khác. Cũng nên đặt **ngôn ngữ** và **hồ sơ tương tác** từ sớm (Tier D
dưới đây) để phần phỏng vấn còn lại hợp với cách bạn làm việc.

**Khi đã quen — quản trị & bộ nhớ (Tier E):**
`Sổ Quyết Định` (để chuyện đã chốt khỏi bàn lại), `--apply-critique` (đưa bản phê bình về thành quyết định),
**lượt Bộ nhớ** trong validate, `--reflect`, và lời nhắc cuối phiên tùy chọn. Những thứ này giữ một spec
chạy dài hạn cho trung thực; ngày đầu chưa cần.

**Lối tắt khi đã quen hình hài:** thay vì đi tay BRD → PRD → epic → story, dán một "bãi ý tưởng" lộn xộn và
để `--auto` tự phân rã (Tier A2). Nó vẫn hỏi bạn ở mọi chỗ chia tách mơ hồ.

---

## 4. Hai cách ra lệnh — và cách nào nên ưu tiên

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

## 5. Những lưu ý quan trọng (để không bị bất ngờ)

- **Duyệt chỉ khi tường minh.** Không gì chuyển sang `approved` mà thiếu người duyệt + ngày. (§2.5)
- **Câu chữ của bạn không bị ghi đè.** Khi `cập nhật`, skill gắn cờ phần bị ảnh hưởng rồi hỏi — bạn cầm
  bút. (§2.3)
- **Mâu thuẫn thì dừng, không tự sửa.** Đụng với tài liệu đã duyệt được nêu ra dạng Giữ / Đổi / Kết hợp —
  skill không lặng lẽ hòa giải. (§2.6)
- **Mỗi mục tiêu BRD phải có chỉ số.** Mục tiêu không có chỉ số đo là **lỗi** validate (chặn khi `--strict`)
  — không đo được thì không chấm điểm được.
- **Tiêu chí nghiệm thu chỉ nằm ở story**, và kích cỡ story là **`S` / `M` / `L`** — không bao giờ story
  point hay giờ công.
- **Tùy chọn hỏi một lần, rồi thôi.** Muốn đổi ngôn ngữ, mức chi tiết, hay hồ sơ tương tác về sau, cứ nói,
  hoặc dùng `--lang` / `preferences.py --set` — skill sẽ không hỏi đi hỏi lại.
- **Chạy hoàn toàn ngoại tuyến sau khi cài.** Không cần Internet lúc chạy; tài liệu nằm trong `docs/product/`
  của chính dự án bạn.
- **Phê bình là một skill riêng.** `cleanmatic:product-spec-critique` mổ xẻ spec nhưng **không bao giờ sửa
  nó** — bạn tự đưa các phát hiện về bằng `--apply-critique` (Tier E1).

---

## 6. Toàn bộ tình huống sử dụng — gom theo tier, sắp theo thứ tự bạn sẽ cần đến

Dưới đây là mọi việc skill làm được, gom thành năm tier khớp với lộ trình học ở trên. Mỗi tình huống gồm:
khi nào dùng, một **kịch bản hội thoại mẫu** đầy đủ, và dòng cờ lệnh tương đương.

Tất cả ví dụ đều dùng một sản phẩm thật trong bộ mẫu của skill: **Acme Shop** — một cửa hàng trực tuyến cho
các thương hiệu thời trang nhỏ (boutique), giúp họ bán hàng trực tiếp cho người hâm mộ mà không qua sàn trung gian.

---

## Tier A — Dựng bộ tài liệu (xương sống chính)

### A1 — Khởi tạo sản phẩm mới từ con số 0

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

> 💡 **Đã có sẵn tư liệu thô?** Nếu bạn có bản ghi phỏng vấn, tổng hợp ticket hỗ trợ, hay ghi chú về đối thủ
> (dạng file `.md`/`.txt`), hãy trỏ skill vào chúng bằng **`--discover`** để **gợi mầm** buổi phỏng vấn này với
> các **ứng viên** persona và vấn đề, thay vì bắt đầu từ con số 0. Skill chỉ đọc đúng những file bạn chỉ định
> (giới hạn trong phạm vi dự án, bỏ qua file ẩn như `.env`, duyệt thư mục trong mức an toàn), đề xuất ứng viên,
> và **xác nhận từng mục với bạn trước khi ghi bất cứ thứ gì** — không bao giờ tự tạo persona.
>
> > **Bạn:** Khám phá persona từ thư mục `research/interviews/`.
> >
> > **Skill:** Tôi đã đọc 3 file `.md`. Các persona ứng viên tôi đề xuất (xác nhận / sửa / loại từng cái):
> > "người dùng ở tỉnh thấy nguồn ghép quanh mình trống trơn", "người trở về nước muốn chiều sâu hơn xã giao"…

> 💡 **Tùy chọn lần đầu.** Ngay trong buổi phỏng vấn đầu tiên này, skill cũng hỏi — trong một lô ngắn — **mức
> chi tiết** của bạn (Gọn / Tiêu chuẩn / Đầy đủ) và **hồ sơ tương tác** (Cân bằng vs Đào sâu; xem Tier D2). Nó
> lưu lại và không hỏi nữa.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec                # không cờ → skill phát hiện chưa có gì → mời khởi tạo
/cleanmatic:product-spec --product      # đi thẳng vào tạo/làm mới PRODUCT.md
/cleanmatic:product-spec --discover research/interviews/   # gợi mầm buổi phỏng vấn từ file/thư mục thô
```

---

### A2 — Đổ một "bãi ý tưởng" và để skill tự sắp xếp

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

### A3 — Viết tài liệu mục tiêu kinh doanh (BRD)

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

### A4 — Thêm một vùng tính năng (PRD)

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

### A5 — Thêm một nhóm việc lớn (Epic)

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

### A6 — Thêm câu chuyện người dùng (Story) kèm tiêu chí nghiệm thu

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

## Tier B — Giữ cho bộ tài liệu khỏe mạnh

### B1 — Kiểm tra chất lượng bộ tài liệu (Validate)

**Khi nào dùng:** Bất cứ lúc nào bạn muốn biết bộ tài liệu có "lành" không: có story nào mồ côi (không gắn
epic)? có link gãy? có mục tiêu kinh doanh nào chưa tính năng nào gánh? story có viết tốt theo nguyên tắc
INVEST không? có chỗ nào lệch khỏi giá trị cốt lõi, hay mâu thuẫn với quyết định đã chốt?

Skill chạy **hai lớp**: lớp máy kiểm tra cấu trúc (mồ côi, link gãy, thiếu tiêu chí nghiệm thu, trùng mã,
**và bất kỳ mục tiêu kinh doanh nào không có chỉ số đo**), và lớp phán đoán (chất lượng story, sự mơ hồ,
lệch giá trị, trùng lặp ý nghĩa). Kết quả là một **báo cáo dễ đọc**.

> 💡 Kiểm tra mới — **mỗi mục tiêu BRD phải có ít nhất một chỉ số thành công.** Một mục tiêu mà `metrics`
> rỗng hoặc thiếu sẽ bị báo là lỗi (mục tiêu không đo được thì không chấm điểm được), nên nó hiện trong báo
> cáo và chặn lại khi chạy `--strict`.

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

### B2 — Hỏi "giờ tôi nên làm gì tiếp?" (Status)

**Khi nào dùng:** Bạn quay lại sau một thời gian và muốn xem nhanh "sức khỏe" bộ tài liệu — có gì đã đổi kể từ lần
kiểm tra chất lượng gần nhất, cái gì còn là bản nháp, cái gì chưa được kiểm tra. Đây là một lời nhắc chỉ-đọc; nó
không sửa gì cả.

Skill so sánh bộ tài liệu hiện tại với lần bạn chạy kiểm tra gần nhất rồi cho biết cái gì đã trôi lệch, cái gì chưa
kiểm tra, cái gì còn nháp — để bạn biết nên tập trung vào đâu. Nó KHÔNG chạy lại toàn bộ kiểm tra chất lượng (đó là
Validate); nó chỉ đọc dấu mốc lần-kiểm-tra-gần-nhất rồi báo cáo.

#### Kịch bản hội thoại

> **Bạn:** Bộ tài liệu của tôi đang ở trạng thái nào — có gì cần để mắt không?
>
> **Skill:** Trạng thái nhanh (chỉ đọc, không thay đổi gì):
> - 🕒 3 mục đã đổi kể từ lần kiểm tra gần nhất (`PRD-CHECKOUT`, `PRD-CHECKOUT-E1`, story `…-S2`) — nên kiểm tra lại.
> - 📝 2 mục còn *nháp*: `PRD-SEARCH`, epic `PRD-SEARCH-E1`.
> - ✅ Mọi thứ còn lại khớp với bản đã kiểm tra gần nhất.
>
> Bạn có muốn tôi chạy kiểm tra đầy đủ trên các mục đã đổi không?

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --status
```

---

### B3 — Áp dụng một thay đổi mà không mất công sức cũ (Update)

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

### B4 — Ký duyệt / chốt một tài liệu (Approve)

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

### B5 — Học từ kết quả thực tế (Learn)

**Khi nào dùng:** Sản phẩm đã ra thị trường và bạn đã có **tín hiệu thật** — báo cáo tháng, số liệu phân tích,
dữ liệu đơn hàng, đánh giá khách hàng. Bạn muốn đưa tín hiệu đó ngược về đặc tả: mỗi mục tiêu có đạt chỉ tiêu
không, và người dùng phát lộ vấn đề mới nào?

`--learn` là một cửa, hai nhánh. Skill hỏi **"số liệu hay phản hồi?"**:

- **Số liệu (outcomes):** với mỗi mục tiêu kinh doanh, bạn khai chỉ tiêu và con số thực tế. Skill tính kết quả
  — 🟢 đạt / 🟡 một phần / 🔴 trượt — và ghi lại (không hề động vào mục tiêu). Mục tiêu chưa đo hiện ra dưới dạng
  **điểm mù**. Mục tiêu *trượt* sẽ được nêu lên để bạn quyết: **giữ** nguyên, **đổi** (mở lại phê duyệt — không
  tự lật ngầm), hoặc ghi một **quyết định**.
- **Phản hồi (discover-back):** trỏ skill vào các file review/feedback. Nó đề xuất **ứng viên** vấn đề/persona
  mới — không commit gì cho tới khi bạn xác nhận từng cái — rồi đưa vào luồng Update.

#### Hội thoại

> **Bạn:** Mình có số liệu tháng trước. Ghi lại kết quả so với mục tiêu nhé.
>
> **Skill:** Số liệu hay phản hồi? — **Bạn:** Số liệu.
>
> **Skill:** Với "Đạt $2M GMV trong năm đầu" — tiêu đề gợi ý chỉ tiêu **$2,000,000**. Đó có phải chỉ tiêu kỳ
> này không? Và thực tế bao nhiêu? — **Bạn:** Chỉ tiêu 2M, thực tế 760K.
>
> **Skill:** Đã ghi `OUT-2`: 🔴 **trượt** (38% chỉ tiêu). Mục tiêu này đang `approved` nên tôi không tự sửa.
> Bạn muốn **giữ** mục tiêu, **đổi** (cần phê duyệt lại), hay ghi một **quyết định** về lý do trượt? —
> **Bạn:** Giữ nguyên; ghi quyết định rằng Q3 cắt ngân sách marketing.
>
> **Skill:** Đã ghi `DEC-4`. Xem toàn cảnh bằng `--viz scorecard` (và `--viz learning` cho bảng tổng quan 1 trang).

#### Cờ tương đương

```
/cleanmatic:product-spec --learn
/cleanmatic:product-spec --viz scorecard      # chỉ tiêu vs thực tế, kèm điểm mù
/cleanmatic:product-spec --viz learning       # bảng tổng quan học hỏi 1 trang
```

---

## Tier C — Chia sẻ & trực quan hóa

### C1 — Lấy bản tóm tắt 1 trang cho lãnh đạo (Summary)

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

> 💡 **Chọn đối tượng đọc.** Cùng một `--summary` có thể nói với hai đối tượng: bản **một-trang cho lãnh đạo**
> (mặc định), hoặc một bản **ghi chú phát hành** — "có gì thay đổi kể từ lần ký duyệt gần nhất" — lấy từ nhật ký
> kiểm toán (bên dưới). Cứ nói "cho tôi ghi chú phát hành kể từ lần duyệt gần nhất" hoặc dùng `--audience release-notes`.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --summary                          # bản một-trang cho lãnh đạo (mặc định)
/cleanmatic:product-spec --summary --audience exec          # y hệt, ghi rõ
/cleanmatic:product-spec --summary --audience release-notes # có gì thay đổi kể từ lần duyệt gần nhất
```

---

### C2 — Vẽ bộ tài liệu thành hình ảnh trực quan (Visualize)

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
| **Nhật ký kiểm toán** quản trị — khi nào · việc gì · ai duyệt · gì đã đổi · quyết định nào | `audit` |

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
/cleanmatic:product-spec --viz audit                 # nhật ký kiểm toán quản trị (văn bản, mặc định)
/cleanmatic:product-spec --viz audit --format md     # bảng markdown (dán vào PR / tài liệu)
/cleanmatic:product-spec --viz audit --format html   # trang HTML khép kín (mở trên trình duyệt)
```

> 💡 View **`audit`** chỉ-đọc, hiện được dạng văn bản thuần (mặc định), markdown, hoặc một trang HTML khép
> kín — mọi giá trị đều được thoát ký tự (escape) an toàn, nên kể cả tên người ký duyệt có ký tự lạ cũng
> không làm vỡ trang. Nó ghép change-log, các lần ký duyệt, các phê duyệt đã cũ, và các quyết định vào một
> dòng thời gian. Nếu một lần ký duyệt không có change-log hay quyết định nào khớp, nó hiện thành một dòng
> **`unreconciled`** (chưa đối soát) tường minh thay vì bị giấu đi — để một lỗ hổng quản trị không bao giờ
> bị âm thầm quét dưới thảm.

> 💡 Muốn ẩn các mục đã hoãn (đánh dấu "sẽ không làm")? Thêm ý "ẩn các mục đã hoãn" — tương đương cờ
> `--filter-wont`.

---

### C3 — Xuất một tài liệu đọc-một-lần để chia sẻ (Export)

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

## Tier D — Chỉnh skill cho hợp với bạn (đặt sớm)

### D1 — Làm việc bằng tiếng Việt (hoặc tiếng Anh)

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

### D2 — Điều chỉnh mức độ skill "thử thách" và "gợi ý" (Hồ sơ tương tác)

**Khi nào dùng:** Bạn thấy skill hỏi quá kỹ (hoặc chưa đủ kỹ), hoặc gợi ý bước tiếp theo quá nhiều (hoặc quá ít). Hai
"núm vặn" cho phép bạn chỉnh **cách AI tương tác** — tách biệt với độ dài nội dung (`detail_level`):

- **`interview_rigor`** (`light` / `standard` / `deep`, mặc định `standard`) — mức độ skill **chất vấn các khẳng định
  và đào sâu tìm lỗ hổng / ca biên / tiêu chí nghiệm thu còn thiếu**. Áp dụng ở **mọi cấp** phỏng vấn (tầm nhìn / BRD /
  PRD / epic / story).
- **`action_prompting`** (`minimal` / `standard` / `proactive`, mặc định `standard`) — **số lượng gợi ý bước tiếp theo**
  skill đưa ra ở mỗi lượt.

**Quan trọng — đây là hai trục độc lập:** `detail_level` = *độ dài* (viết dài hay ngắn); `interview_rigor` = *độ sâu*
(chất vấn nông hay sâu). "Ngắn gọn nhưng đào sâu" là hoàn toàn hợp lệ (`detail_level: concise` + `interview_rigor:
deep`). Đừng hiểu `deep` thành "viết dài hơn".

Mặc định trung tính là `standard`, nên skill **không bao giờ tự ý** đặt bạn vào chế độ khắt khe. Nó hỏi một lần ở đầu
phiên — **một câu gộp chung vào lô `detail_level`** ở buổi phỏng vấn đầu tiên — mời chọn **Cân bằng** (mặc định) vs
**Đào sâu** (`interview_rigor: deep` + `action_prompting: proactive`), và chỉ ghi khi bạn xác nhận. Nếu bạn chỉ phác
thảo và muốn nhẹ hơn, cứ nói "nhẹ". Cuối phiên, nếu có bằng chứng thực (ví dụ bạn liên tục gạt phần đào sâu là "nhiễu"),
skill có thể đề xuất **siết hoặc nới** một núm — bạn đồng ý thì nó mới ghi.

#### Cờ lệnh tương đương

```
# Đào sâu:
./.claude/skills/.venv/bin/python3 scripts/preferences.py --root . \
  --set interview_rigor=deep --set action_prompting=proactive
# Nhẹ hơn:
./.claude/skills/.venv/bin/python3 scripts/preferences.py --root . \
  --set interview_rigor=light --set action_prompting=minimal
```

Lệnh này **giữ nguyên mọi tùy chọn khác** (đọc → trộn → ghi); một key lạ hoặc một giá trị sai sẽ thoát với lỗi và
**không ghi gì cả**. Muốn tách riêng hai núm — ví dụ ngắn-gọn-nhưng-vặn-kỹ là chỉ `--set interview_rigor=deep`.

---

## Tier E — Quản trị & bộ nhớ (khi spec đã chín)

### E1 — Ghi lại một quyết định để khỏi phải bàn lại (Sổ Quyết Định)

**Khi nào dùng:** Bạn đã có một quyết định rõ ràng — giữ cách diễn đạt cũ, chấp nhận một đánh đổi đã biết, hoặc giải
quyết một mâu thuẫn — và muốn nó được ghi nhớ để skill không nêu lại nữa. Hoặc đơn giản bạn muốn xem danh sách các
quyết định đã ghi.

Mỗi quyết định rõ ràng được lưu thành `DEC-<n>` trong `docs/product/decisions.md` (một nhật ký chỉ-thêm). Khi một
khẳng định mới mâu thuẫn với tài liệu đã *duyệt*, skill sẽ nêu ra (Giữ / Đổi / Kết hợp) và ghi lại lựa chọn của bạn ở
đây; bạn cũng có thể ghi trực tiếp. Một khi quyết định đã được lưu, skill coi đó là đã chốt và không nhắc lại cùng một
vấn đề trôi lệch nữa — trừ khi nội dung gốc thật sự thay đổi, lúc đó nó sẽ hỏi quyết định cũ của bạn còn áp dụng không.

#### Kịch bản hội thoại

> **Bạn:** Cho tôi xem các quyết định đã chốt.
>
> **Skill:** Các quyết định đã ghi:
> - **DEC-1** — Để luồng thanh toán cho khách vãng lai ra ngoài phạm vi v1 (chấp nhận 2026-05-20).
> - **DEC-2** — Cho phép cửa sổ đổi trả 7 ngày dù đối thủ cho 30 ngày (đánh đổi có chủ đích).
>
> **Bạn:** Ghi lại là tạm thời chúng ta vẫn dùng đăng nhập chỉ bằng email.
>
> **Skill:** Đã ghi thành **DEC-3** kèm ngày hôm nay và lý do của bạn. Tôi sẽ không nêu lại "chỉ đăng nhập email" như một thiếu sót nữa.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --decision         # liệt kê các quyết định đã ghi
/cleanmatic:product-spec --decision DEC-2    # xem một quyết định
```

#### Biến một bản phê bình thành quyết định — `--apply-critique`

Nếu bạn đã chạy **`cleanmatic:product-spec-critique`** (bản mổ xẻ thẳng-tay-nhưng-có-căn-cứ) và nhận được một
báo cáo, đây là cách bạn đưa các phát hiện của nó *trở lại spec dưới dạng quyết định*. Skill phê bình chỉ ghi
báo cáo; nó không bao giờ động vào spec của bạn. `--apply-critique` đi qua từng phát hiện **cùng bạn** — **Giữ**
(bác phát hiện, ghi lý do), **Đổi + ký duyệt lại** (chấp nhận; skill chạy lượt rà ảnh hưởng và không bao giờ tự
viết lại câu chữ của bạn), hoặc **Hoãn** (xem lại sau) — và ghi một `DEC-<n>` cho mỗi phát hiện đã xử lý để không
phải bàn lại.

Nó được thiết kế an toàn: báo cáo chỉ được đọc từ `docs/product/critique/`, mỗi phát hiện được khớp với tài liệu
của nó và gắn nhãn **mới / cũ / không rõ** (để bạn biết spec có dịch chuyển kể từ lúc phê bình không), một lần
*Đổi* trên tài liệu đã duyệt vẫn đi qua đúng cổng ký duyệt Giữ/Đổi/Lai, và một lượt bị ngắt giữa chừng sẽ chạy
tiếp mà không ghi trùng. Nếu một báo cáo có trước cơ chế theo dõi độ mới, skill nói thẳng thay vì đoán mò.

> **Bạn:** Áp dụng bản phê bình sáng nay.
>
> **Skill:** Tôi đã đọc `docs/product/critique/260604-all.md` — 6 phát hiện. Đi từng cái:
> 1. `[chặn] BRD-G2` — chỉ số north-star. Giữ, Đổi + ký duyệt lại, hay Hoãn?
>
> **Bạn:** Đổi — thêm chỉ số cuộc-trò-chuyện-duy-trì.
>
> **Skill:** Đã ghi **DEC-1** (ảnh hưởng BRD-G2). Tôi đã đánh dấu mục tiêu để bạn tự sửa (tôi không tự viết lại
> câu chữ). Sang phát hiện 2…

```
/cleanmatic:product-spec --apply-critique docs/product/critique/<báo-cáo>.md
```

---

### E2 — Đảm bảo không bỏ sót điều quan trọng (lượt "Bộ nhớ" trong Validate)

**Khi nào dùng:** Bạn không cần yêu cầu việc này — nó tự diễn ra mỗi lần bạn chạy kiểm tra chất lượng (Validate). Biết
nó tồn tại sẽ giúp bạn hiểu vì sao báo cáo luôn kết thúc bằng một ghi chú ngắn "ta đã nhớ ghi lại những gì?".

Quyết định, chỉnh sửa, và những lần vượt ranh giới chỉ hữu ích về sau nếu chúng thật sự được *ghi lại*. Vì vậy mỗi báo
cáo Validate đều kết thúc bằng một **lượt Bộ nhớ**: trả lời rõ ràng, nhanh gọn ba câu hỏi — có mâu thuẫn nào đã trở
thành một quyết định được ghi không? có lỗi cấu trúc nào được ghi chú để khỏi lặp lại không? có tín hiệu "trông như chưa
ghi" nào đáng xử lý không? Ngay cả câu trả lời "không có gì để ghi" cũng là một câu trả lời thành thật, có chủ đích —
không phải một bước bị bỏ qua. Nó chỉ *nhắc*; nó không bao giờ ghi gì sau lưng bạn, và không bao giờ tuyên bố đã ghi một
lỗi khi bạn đã quyết định lỗi đó không đáng ghi.

#### Kịch bản hội thoại

> **Bạn:** Kiểm tra bộ tài liệu của tôi.
>
> **Skill:** Báo cáo chất lượng: truy vết sạch, hai ghi chú chất lượng (đã liệt kê ở trên). Và một **lượt Bộ nhớ** nhanh:
> - 🧠 Quyết định: mâu thuẫn về phạm vi thanh toán mà ta giải quyết trước đó đã có trên hồ sơ là **DEC-4** — không có gì mới.
> - 🧠 Chỉnh sửa: lần này không có lỗi cấu trúc nào.
> - 🧠 Tín hiệu: một ghi chú — có vẻ một tệp đã được sửa bên ngoài `docs/product/`. Bạn muốn tôi ghi lại như một
>   tự-chỉnh-sửa, hay đó là điều bình thường?
>
> **Bạn:** Bình thường thôi, cứ để vậy.
>
> **Skill:** Đã hiểu — tôi sẽ đánh dấu là đã xác nhận để không nhắc lại cùng một việc nữa.

#### Cờ lệnh tương đương

Lượt Bộ nhớ nằm sẵn trong Validate — không có cờ riêng. Chỉ cần chạy:

```
/cleanmatic:product-spec --validate
```

---

### E3 — Thu hồi những "ký ức" bạn đã bỏ lỡ trước đó (Reflect)

**Khi nào dùng:** Sau một quãng làm việc dài — một lần nhập liệu lớn, nhiều thay đổi mà không chạy Validate, hoặc một bộ
tài liệu cũ vừa được đưa vào — bạn nghi ngờ một số quyết định hay chỉnh sửa chưa từng được ghi lại. Reflect quay lại và
*thu hoạch* chúng.

Skill quét những gì **đã được ghi xuống** — lịch sử git (nếu có) và trạng thái tài liệu/bộ nhớ hiện tại — rồi đề xuất
những quyết định và chỉnh sửa trông như đã được đưa ra nhưng chưa từng được ghi. Mỗi mục chỉ là một **đề xuất**: bạn
**chấp nhận**, **sửa câu chữ**, hoặc **từ chối**, và chỉ những mục bạn chấp nhận mới được lưu. Nó chỉ chạy khi bạn yêu
cầu (vì nó bỏ thêm công sức để suy nghĩ kỹ), và vẫn hoạt động cả khi không có git — khi đó nó thu hoạch từ tệp của bạn.
Một giới hạn thành thật: nó chỉ bắt được những gì *đã ghi xuống*, không bao giờ bắt được điều bạn chỉ *nói* trong hội thoại.

#### Kịch bản hội thoại

> **Bạn:** Tôi vừa nhập một bộ tài liệu lớn và sửa rất nhiều mà chưa validate. Bạn rà giúp xem có gì lẽ ra cần ghi lại không?
>
> **Skill:** Tôi đã quét lịch sử và trạng thái hiện tại. Ba thứ trông như chưa được ghi:
> - Một commit "revert phạm vi guest-checkout" — trông như một quyết định. Ghi lại thành một quyết định nhé?
> - Một bản sửa "siết câu chữ cửa sổ đổi trả" — trông như một tự-chỉnh-sửa. Ghi chú lại không?
> - Mọi thứ khác đã có trên hồ sơ — không có gì để đề xuất lại.
>
> **Bạn:** Đồng ý ghi mục đầu thành quyết định, bỏ qua mục thứ hai.
>
> **Skill:** Đã ghi quyết định phạm vi thành **DEC-5** kèm lý do của bạn. Để nguyên bản sửa câu chữ. Không còn gì để thu hồi.

#### Cờ lệnh tương đương

```
/cleanmatic:product-spec --reflect
```

---

### E4 — Bật lời nhắc bộ nhớ tự động (Stop hook tùy chọn)

**Khi nào dùng:** Bạn (hoặc đội kỹ thuật) muốn skill **nhắc bạn vào cuối phiên** nếu một quyết định, một chỉnh sửa, hay
một lần vượt ranh giới trông như chưa được ghi — mà không phải tự nhớ đi kiểm tra. Đây là một bước cài đặt tùy chọn, làm
một lần.

Lời nhắc này **mặc định tắt** và **không bao giờ tự bật giúp bạn** — tự ý đổi cài đặt của bạn là vi phạm lòng tin. Bạn
chủ động bật bằng một lệnh cài đặt, và có thể tắt bất cứ lúc nào. Khi bật, nó nhẹ nhàng nhắc vào cuối hội thoại nếu có gì
trông như chưa được ghi; chỉ một lần vượt ranh giới ra ngoài thư mục (một lỗi rõ ràng) mới yêu cầu bạn sửa trước khi kết thúc.

#### Kịch bản hội thoại

> **Bạn:** Skill có thể nhắc tôi vào cuối phiên nếu tôi quên ghi một quyết định không?
>
> **Skill:** Có — đó là một lời nhắc tùy chọn, mặc định tắt. Chạy lệnh cài đặt một lần ở dưới để bật (nó chỉ đổi cài đặt
> cục bộ của bạn, không bao giờ đụng tới phần dùng chung, và bạn gỡ được bất cứ lúc nào). Sau đó, tôi sẽ nhắc nhanh vào
> cuối phiên mỗi khi có gì trông như chưa được ghi.

#### Cờ lệnh tương đương

Đây là một tùy chọn khi cài đặt, không phải cờ trong skill. Chạy một lần trong dự án:

```
./install.sh --memory-hook          # bật lời nhắc (chỉ cài đặt cục bộ)
./install.sh --memory-hook-shared   # bật cho cả đội (cài đặt được commit)
```

Một lệnh `./install.sh` thường sẽ không bao giờ đụng tới hook của bạn. Để tắt, xóa các mục `memory_gap_hook.py` khỏi tệp
cài đặt của bạn.

---

## 7. Quy trình điển hình từ đầu đến cuối

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

## 8. Những điều skill này KHÔNG làm (để bạn yên tâm)

- **Không viết code.** Đây là skill tài liệu sản phẩm. Nếu bạn cần code, đội kỹ thuật sẽ viết dựa trên story + tiêu chí nghiệm thu.
- **Không ước lượng bằng story point hay giờ công.** Story chỉ mang kích cỡ `S` / `M` / `L`.
- **Không ghi đè đoạn văn bạn viết tay.** Khi cập nhật, skill gắn cờ và hỏi trước khi sinh lại.
- **Không tự đảo ngược quyết định đã duyệt.** Mâu thuẫn luôn được nêu ra để bạn chọn Giữ / Đổi / Kết hợp.
- **Không cần Internet khi chạy.** Sau khi cài đặt một lần, mọi thứ chạy trên máy bạn. Tài liệu nằm gọn
  trong `docs/product/` của dự án.

---

## 9. Gặp khó? Cứ hỏi thẳng skill

Cách dễ nhất khi bí: **mở skill và hỏi bằng lời.** Ví dụ *"Tôi nên làm gì tiếp theo?"* hoặc *"Bộ tài liệu
của tôi còn thiếu gì?"*. Skill sẽ nhìn vào tình trạng hiện tại và gợi ý bước hợp lý.

Để biết chi tiết kỹ thuật sâu hơn (dành cho người vận hành), xem `SKILL.md` và thư mục `references/` trong
thư mục skill, hoặc `README.md` ở gốc dự án.
