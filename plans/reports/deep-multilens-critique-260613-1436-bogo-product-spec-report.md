# Phê bình sâu spec sản phẩm BoGo — báo cáo tổng hợp

*Ngày: 2026-06-13 · Đối tượng spec: `bogo-product-spec` (BoGo — nền tảng SaaS quản trị SME)
· Phương pháp: 4 lăng kính (sản phẩm / kỹ thuật / thị trường / câu chữ) + spine, chạy qua ~34 trợ lý Ac đọc độc lập, có vòng phản biện và đối chiếu phiên bản công cụ.*

> **Đọc trong 30 giây.** Cây spec **lành mạnh về cấu trúc** (không lỗi truy nguyên, không liên kết chết, không vòng lặp). Nhưng phần "thịt" còn ba vấn đề lớn: (1) **lời hứa lớn nhất của VISION — tổ chức tự dựng sơ đồ phòng ban, tự nhập nhân viên, tự kích hoạt — vẫn KHÔNG có story nào xây**, dù đã bị 4 lượt phê bình trước nhắc; (2) **điểm khác biệt AI tiếng Việt đã bị đối thủ lấp đầy** và chi phí AI chưa ai đo; (3) **một loạt lỗ kỹ thuật/pháp lý ở mảng tiền và dữ liệu** (chống khóa nhà cung cấp, ký webhook thanh toán, cô lập dữ liệu giữa các tổ chức) đủ để chặn ra mắt. Đây không phải spec tồi — đây là spec tốt còn thiếu đúng những mảnh sống còn.

---

## 1. Tóm tắt cho Product Owner

### Tình trạng tổng thể
BoGo có một bộ khung tài liệu **trưởng thành hiếm thấy** với một PO không chuyên kỹ thuật: tầm nhìn rõ, BRD có mục tiêu đo được, 9 phân hệ, 80 story, sổ quyết định tới DEC-55+, đã chạy validate và **4 lượt phê bình** trước. Vấn đề không nằm ở sự lộn xộn — nằm ở **khoảng cách giữa lời hứa và phần đã đặc tả**. Cây story khỏe, nhưng vài cây cột chống đỡ cả ngôi nhà thì còn để trống.

### 3 điểm mạnh (giữ nguyên, đừng đụng)
1. **Cấu trúc sạch.** Máy quét không tìm thấy lỗi truy nguyên, liên kết chết, hay vòng phụ thuộc nào. Ma trận đầy đủ. Đây là nền tốt để build.
2. **Quy trình kỷ luật.** PO đã dùng validate + 4 vòng critique + sổ quyết định. Rất nhiều phát hiện trong báo cáo này là bằng chứng cho thấy *bạn đã hỏi đúng câu* — chỉ là một số câu chưa được trả lời bằng story.
3. **Hiểu bối cảnh Việt Nam.** Chiều sâu về lương/chấm công, ý thức về HĐĐT và NĐ13/2023, hiểu hành vi dùng Zalo — cho thấy spec bám thực địa SME Việt, không phải copy nước ngoài.

### 3 điều nguy hiểm nhất (đối mặt ngay)
1. **GAP-ORG vẫn mở — và nó chặn cả phễu kích hoạt.** VISION hứa ORG_ADMIN "buổi sáng đầu tiên dựng xong sơ đồ 5 phòng ban, nhập 40 nhân viên từ file" (`VISION:64`). **Không story nào trong 80 story build màn hình tạo phòng ban, cũng không có nhập nhân viên hàng loạt.** Chấm công, giao việc theo phòng, chat hệ thống, luồng duyệt — tất cả giả định phòng ban đã tồn tại. Mục tiêu kích hoạt ≥70% (BRD-G3) và 100 tổ chức/12 tháng (BRD-G1) đứng trên một bước setup không ai sở hữu. **Đã bị nhắc 4 lần trước, vẫn chưa fix.**
2. **AI hết độc quyền + kinh tế AI chưa đo.** Luận điểm "AI tiếng Việt gắn dữ liệu vận hành chỉ BoGo có" (`PRD-AI:36`) không còn đúng: Tanca đã có 6 AI agent tiếng Việt, Base có "Hey Base AI", 1Office có "1AI". Đồng thời, **không trigger mua nào trong BRD liên quan tới AI** (`BRD:192`) — AI là lý do ở lại, không phải lý do mua. Và trần chi phí LLM ≤15% doanh thu (`BRD:179`) **chưa có con số thật, chưa có cơ chế quota/throttle** — rủi ro âm margin khi scale.
3. **Cụm lỗ "tiền + dữ liệu" đủ để chặn go-live.** Không có story cho tổ chức **chủ động rời đi** (xuất dữ liệu, chuyển quyền ORG_ADMIN) → đúng nỗi sợ khóa nhà cung cấp của SME (`PRD-PLATFORM-E1-S1:30`). Webhook thanh toán **không xác thực chữ ký** → giả mạo gạch nợ (`PRD-PLATFORM-E2-S3:25`). Tìm kiếm toàn văn **không có điều kiện cô lập giữa các tổ chức** → rủi ro rò dữ liệu chéo, phá cam kết lõi của VISION (`PRD-COMM-E3-S1:28`).

### 3 việc nên làm đầu tiên
1. **Mở epic "Quản trị cơ cấu tổ chức"** (tạo/sửa phòng ban nhiều cấp + nhập nhân viên hàng loạt + tự đăng ký tổ chức), đánh **must / now**, xếp **trước mọi phân hệ khác**. Đây là viên gạch đáy của cả tòa nhà.
2. **Chạy 1 tuần đo chi phí LLM thật (shadow mode)** và **chốt định vị AI** (giữ chân hay thu hút) *trước khi* khóa giá 89k. Nếu vượt trần 13k/user, thêm quota AI vào gói.
3. **Thêm cụm AC "an toàn tiền + chống khóa dữ liệu"** vào PLATFORM: ký webhook, xử lý hoàn tiền/chargeback, xuất dữ liệu, chuyển quyền admin, cô lập tìm kiếm theo tổ chức, quy trình báo cáo sự cố dữ liệu NĐ13.

---

## 2. Bối cảnh & độ tin cậy của báo cáo này

| Thông số | Giá trị |
|----------|---------|
| Trợ lý AI đã chạy | ~34 (18 lăng kính + 9 lô phản biện + 5 rà sót + tổng hợp) |
| Phát hiện thô | 184 |
| Sau vòng phản biện | **111 giữ nguyên · 24 hạ mức (phóng đại) · 7 loại bỏ (sai)** |
| Sau gộp trùng + tách nhiễu phiên bản | **171 phát hiện thật** |
| Phân bố mức độ | 10 Chặn · 67 Cao · 72 Trung bình · 22 Thấp |
| Nhiễu phiên bản (gộp thành 2 việc) | 12 (xem §6) |

**Độ trung thực — đọc kỹ phần này:** PO đã chạy **4 bản phê bình trước** (`docs/product/critique/`, các ngày 10–11/06). Vòng này chạy **độc lập** (không đọc 4 bản đó), nên:
- Nhiều phát hiện ở đây **trùng/lặp lại** bản trước → đây là **bằng chứng độc lập** rằng vấn đề có thật **và chưa được fix** (xem §5). Không nên coi 171 là "171 lỗi mới".
- Một lớp lớn là **mới thật** (lỗ kỹ thuật NFR, câu chữ, phụ thuộc ẩn) mà các vòng trước chưa chạm.
- Vòng này thêm **đối chiếu phiên bản công cụ** (§6) và **vòng phản biện** để cắt phát hiện yếu — thứ các bản trước không có.

---

## 3. Phát hiện theo mức độ nghiêm trọng

### 🔴 BLOCKER (10 — gộp thành 6 nhóm)

**B1. Không có "nhà" cho cơ cấu tổ chức — xương sống bị trống (GAP-ORG leo thang).**
`VISION:62` · `PRD-PLATFORM-E1-S1:26` · `PRD-AI-E2-S5:10`
- ⚠️ VISION cam kết "sơ đồ tổ chức là xương sống" và mô tả kịch bản dựng phòng ban + nhập 40 nhân viên ngày đầu. Nhưng không story nào build màn hình tạo/sửa/xóa phòng ban hay nhập nhân viên hàng loạt. `HR-E1-S6` chỉ gán nhân viên vào trường "phòng ban", không định nghĩa phòng ban sinh ra từ đâu. `DEC-50` đã hứa "sơ đồ phòng ban, tài khoản, phân quyền" nhưng khi triển khai chỉ ra được vòng đời thuê bao. Chat hệ thống (`COMM-E1-S2`), giao việc theo phòng (`TASK-E1-S2`), duyệt đa cấp (`APPROVAL-E1-S2`) đều giả định phòng ban đã có.
- 🔧 Tạo epic "Quản trị cơ cấu tổ chức" (must/now): tạo cây phòng ban nhiều cấp, gán trưởng phòng, nhập nhân viên hàng loạt từ Excel/CSV. Phải go-live **trước** mọi phân hệ khác.

**B2. Đường kích hoạt (BRD-G3 ≥70%) treo trên một story "should" có thể bị cắt.**
`PRD-AI-E2-S5:10`
- ⚠️ Trợ lý onboarding dẫn ORG_ADMIN qua setup là đòn bẩy trực tiếp của G3, nhưng gán `moscow: should`. Với 33 must trong "now", áp lực cắt should rất cao. Cắt → tổ chức mới chỉ thấy "checklist tĩnh", tự mò.
- 🔧 Nâng lên **must**. Nếu lo khối lượng, tách: (a) must — checklist tĩnh tự cập nhật theo dữ liệu (không cần LLM); (b) should — trợ lý LLM trả lời câu hỏi setup.

**B3. Không có lối cho tổ chức chủ động rời đi (chống khóa nhà cung cấp).**
`PRD-PLATFORM-E1-S1:29-30`
- ⚠️ Vòng đời hiện chỉ xử lý khách **không trả tiền** (dunning). Không có: tự đóng tài khoản, **xuất toàn bộ dữ liệu** (lương/chấm công/việc/tin nhắn) ra định dạng mở, **chuyển quyền ORG_ADMIN** khi người phụ trách nghỉ. SME sợ nhất bị khóa dữ liệu — đây là rào cản mua trực tiếp, và BoGo tự lặp lại đúng nỗi đau "nhân viên nghỉ là mất dữ liệu" mà VISION thề xóa.
- 🔧 Thêm 3 AC: xuất dữ liệu CSV/Excel trong 24h trước khi xóa; chuyển quyền admin trong nội bộ tổ chức (không cần PLATFORM_ADMIN); ghi cam kết data portability vào hợp đồng điện tử như điểm bán chống lock-in.

**B4. Điểm khác biệt AI đã bị đối thủ vô hiệu hóa trước khi BoGo ra mắt.**
`PRD-AI:36`
- ⚠️ Spec định vị "AI tiếng Việt gắn dữ liệu vận hành" là moat và đòn bẩy G3. Thực tế: Tanca đã có HR Chatbot + 5 AI agent tiếng Việt đang chạy; Base có "Hey Base AI"; 1Office có "1AI" nút đăng ký đang hoạt động. Luận điểm "chỉ BoGo có" sụp.
- 🔧 Viết một câu đặc tả CỤ THỂ điều BoGo làm mà đối thủ không: AI gắn đồng thời HR+TASK+COMM của chính tổ chức trong một phiên, phân quyền tới từng cấp phòng ban theo sơ đồ thật. Nếu đó là moat, viết thành AC kiểm chứng được. Nếu không, hạ kỳ vọng BRD-G3 xuống "AI là tính năng giữ chân, không phải lý do mua đầu".

**B5. Cụm hợp đồng kỹ thuật tham chiếu phân hệ đã bị xóa + chính sách xóa dữ liệu không ai sở hữu.**
`PRD-COMM-E1-S1:53` · `PRD-PLATFORM-E1-S1:30`
- ⚠️ (a) Hợp đồng ERP-link liệt kê `entity_type: order → SALES`, nhưng `PRD-SALES` đã bị loại theo DEC-45 → deep-link đơn hàng thành stub ngay khi build, mất chính tính năng "ERP-native" là lý do BoGo xây COMM thay vì dùng Lark. (b) "Dữ liệu giữ 60 ngày trước khi xử lý theo chính sách lưu trữ" — không story nào định nghĩa "chính sách" đó làm gì; dữ liệu chứa vector sinh trắc (NĐ13), không spec pipeline xóa = vi phạm quyền người dùng không có cửa thoát.
- 🔧 Gỡ `order` khỏi danh sách entity_type cho tới khi có PRD sở hữu; chỉ giữ `shift|task`. Định nghĩa pipeline offboarding bằng AC cụ thể (cảnh báo → xóa vector sinh trắc ngay theo NĐ13 → xóa nội dung → log xác nhận từng loại).

**B6. Lỗ "tiền": hoàn tiền/chargeback và moat hai chiều chỉ spec một phía.**
`PRD-PLATFORM-E2-S3:28` · `PRD-TASK-E1-S2:26`
- ⚠️ (a) Không AC nào xử lý khi ngân hàng **chargeback/reversal SAU khi đã gạch nợ** — phổ biến ở VN; hệ thống không biết hạ gói hay giữ → xử lý ad-hoc, mất doanh thu hoặc hạ gói nhầm. (b) Tính năng "moat" task↔ca làm hai chiều: `TASK-E1-S2:26` nói "ca phản ánh ngược danh sách việc", nhưng `PRD-HR-E1-S3` (story sở hữu ca làm) **không có AC nào nhận sự kiện này** → moat chỉ tồn tại một nửa trong sản phẩm thật.
- 🔧 Thêm AC chargeback (gắn cờ vào hàng đợi PLATFORM_ADMIN, không tự hạ gói, log audit). Thêm AC vào `PRD-HR-E1-S3` để phía HR nhận & hiển thị danh sách việc gắn ca + tỉ lệ hoàn thành.

### 🟠 CAO (67 — gộp thành các nhóm chính; chi tiết đầy đủ ở Phụ lục)

**C1. Phễu kích hoạt thiếu mảnh (lặp lại GAP-ORG ở mức story).** Hàng loạt story dẫn người dùng tới màn hình chưa có: `PRD-AI-E2-S5:24` (onboarding trỏ tới dựng phòng ban không tồn tại), `PRD-HR-E1-S6` & `VISION:64` (nhập 40 nhân viên từ file — không có AC import), `PRD-PLATFORM-E1-S1:24` (dựng sơ đồ phòng ban). → Tất cả quy về B1.

**C2. Kinh tế AI & enforcement chi phí.** `BRD:179-180` đặt trần LLM ≤15% doanh thu nhưng `PRD-AI-E2-S6` chỉ có nút bật/tắt — **không đo lượng query/tổ chức, không ngưỡng cảnh báo, không throttle**. `PRD-AI-E2:50`: giá trị AI phụ thuộc kho tài liệu tổ chức tải lên, nhưng `S5` onboarding không có bước bắt buộc tải tài liệu → kho rỗng lúc go-live, AI "biết ít quá". → Thêm AC đo + quota per-org; thêm bước tải ≥1 tài liệu vào onboarding.

**C3. Định vị thị trường lỗi thời + GTM vô chủ.** `BRD:147-148`: Tanca đã có **gói free vĩnh viễn không giới hạn nhân viên** + mua-một-lần → phân khúc SME nhỏ nhất có thể chọn Tanca free thay vì 89k/user. `BRD:183`: cả 3 kênh GTM ghi "đề xuất — gán owner khi vận hành" → **không ai chịu trách nhiệm đạt 100 tổ chức**. `BRD:192`: 5 trigger mua không cái nào là AI. → Cập nhật so sánh đối thủ; chốt ≥1 kênh GTM có owner+ngân sách+KPI trước go-live; tách rõ AI là retention hay acquisition hook.

**C4. Dư âm pivot Cleanmatic chưa dọn (câu chữ — rủi ro hiểu sai khi build).** `PRD-REPORT:8` và cả cụm REPORT vẫn `approved_by: Nhóm sản phẩm Cleanmatic`, persona `ZONE_MGR/SYS_ADMIN`, phân hệ `FINANCE/SALES/INVENTORY/PAYMENT/CARE` — không cái nào tồn tại trong BoGo. `PRD-HR-E1-S1:40` dùng vai "nhân viên giao nhận/xử lý" (vai chuỗi giặt là cũ). `PRD-HR-E2:40` còn trỏ `PRD-FINANCE`. → Thêm callout "TÀI LIỆU LỊCH SỬ — không áp dụng cho BoGo" hoặc chuyển sang `archive/`; thay nhãn vai bằng persona BoGo chuẩn.

**C5. Hạ tầng dùng chung không ai sở hữu (phụ thuộc ẩn).** Push notification (`PRD-COMM:82` — "đội build lo"), email transactional (`PRD-TASK-E4-S5:25`), kho hướng dẫn cho AI hỗ trợ (`PRD-SUPPORT-E1-S1:25`) — đều bị ≥5 story đã approved phụ thuộc nhưng **không story/epic nào build**. → Tạo các story "tech enabler" trong PLATFORM, gán `depends_on` tường minh.

**C6. INVEST — story "khổng lồ" không ước lượng nổi.** `PRD-COMM-E1-S1` (9 AC, 5 chức năng: chat/đính kèm/ERP-link/voice/offline), `PRD-AI-E2-S4` (mini-LMS 4 hệ con), `PRD-APPROVAL-E1-S3` (4 luồng xác thực, size M nhưng thực tế L×3). → Tách mỗi story thành 2-3 story giao được độc lập, đánh lại size.

**C7. Lỗ NFR/bảo mật kỹ thuật (mới, các vòng trước chưa chạm).**
- `PRD-COMM-E3-S1:28` — tìm kiếm toàn văn không có AC cô lập theo tổ chức → rủi ro rò chéo, phá cam kết "không tổ chức nào thấy dữ liệu tổ chức khác".
- `PRD-HR-E1-S1:33` — chấm công offline dùng "timestamp thiết bị" → nhân viên chỉnh đồng hồ máy để gian lận, không AC chống.
- `PRD-PLATFORM-E2-S3:25` — webhook thanh toán không xác thực chữ ký HMAC → giả mạo gạch nợ.
- `PRD-COMM-E1-S1:25` — file/voice giữ "vô thời hạn", không quota → COGS storage phá vỡ kinh tế gói 89k.
- `PRD-APPROVAL-E1-S3:26` — ký trên web không đạt "bậc thường một chạm" vì passkey gắn phần cứng → mâu thuẫn ràng buộc web-parity DEC-66.

**C8. Persona EXEC gần như không được phục vụ.** `PRD-AI-E2-S3:45`, `PRD-TASK-E1:18`, `PRD-TASK:52`: EXEC là người ký ngân sách nhưng AI không phục vụ EXEC, E1/E2 TASK không cho EXEC giao việc, dashboard E4 không nằm trong "phạm vi" PRD-TASK. → Thêm EXEC vào personas E1/E2, mở rộng AC dashboard + tóm tắt AI cho EXEC.

**C9. Chỉ số kinh doanh không có cách đo.** `BRD:117` — G2 "giảm ≥50% thời gian hành chính" nhưng **không story nào định nghĩa khảo sát baseline** (ai đo, khi nào, đo gì). `BRD:130` — G3 churn ≤3% nhưng SUPPORT chỉ phản ứng (khách phải tự liên hệ), không có cảnh báo tổ chức sắp rời. → Thêm story "khảo sát baseline pilot" (must); thêm dashboard "tổ chức at-risk" cho PLATFORM_ADMIN.

**C10. Tuân thủ pháp lý vận hành.** `BRD:204` — không story nào sở hữu **quy trình báo cáo vi phạm dữ liệu NĐ13/2023** (72 giờ); `PRD-PLATFORM-E1-S2:24` — ORG_ADMIN không có màn tra cứu nhật ký hoạt động toàn tổ chức (cần khi thanh tra — đúng trigger mua #3). → Thêm AC quy trình sự cố + màn audit log.

### 🟡 TRUNG BÌNH (72) & 🟢 THẤP (22)
Phần lớn là: câu chữ chưa đo được ("trả lời ngắn gọn" `AI-E2-S5`, "≤15 phút" ghi "đề xuất" ngay trong AC đã approved `SUPPORT-E1-S2`); dư âm pivot rải rác (`PRD-COMM` còn nhắc SALES); luồng đăng ký khuôn mặt để ORG_ADMIN upload ảnh trong khi NĐ13 đòi chính nhân viên ký consent (`HR-E1-S6`); nhiều story gộp nhiều hành vi nên khó nghiệm thu; định giá so sánh đối thủ dùng số cũ (Fiine 59k, 1Office tier). **Chi tiết đầy đủ ở Phụ lục** — gợi ý gom thành các đợt dọn dẹp theo phân hệ, không cần xử từng cái rời rạc.

---

## 4. Lỗ hổng & phần chưa hoàn thiện (story còn thiếu hẳn)

Đây là danh sách những thứ **VISION/BRD hứa nhưng không story nào xây** — quan trọng hơn cả lỗi trong story đã có, vì máy quét cấu trúc không thấy được:

| # | Lời hứa | Thiếu story gì | Ảnh hưởng |
|---|---------|----------------|-----------|
| G1 | "Sơ đồ tổ chức là xương sống" (VISION:32) | Màn tạo/sửa phòng ban nhiều cấp | Chặn ~5 phân hệ phụ thuộc |
| G2 | "Nhập 40 nhân viên từ file" (VISION:64) | Nhập nhân viên hàng loạt Excel/CSV | Phá trial 14 ngày + activation |
| G3 | "Tổ chức tự đăng ký" (VISION:33) | Luồng self-signup tổ chức mới | G1 100 tổ chức không có cửa vào |
| G4 | Tổ chức rời đi an toàn | Xuất dữ liệu + chuyển quyền admin | Rào cản mua (sợ khóa dữ liệu) |
| G5 | Thông báo realtime (8+ story dùng) | Hạ tầng push notification | 8 story approved thành giả định |
| G6 | AI hỗ trợ tuyến đầu (SUPPORT-E1-S1) | Kho hướng dẫn chính thức | AI hỗ trợ rỗng lúc go-live |
| G7 | Gửi báo cáo qua email (TASK-E4-S5) | Hạ tầng email transactional | Story không build/test được |
| G8 | G2 "giảm 50% thời gian" (BRD:117) | Khảo sát baseline trước/sau | Không có số chứng minh giá trị |
| G9 | Tuân thủ NĐ13 (BRD:204) | Quy trình báo cáo vi phạm 72h | Rủi ro pháp lý khi thanh tra |
| G10 | Đo phí AppROVAL theo tờ trình (DEC-60) | Đo đếm & hạn mức tờ trình | Không phát hành hóa đơn add-on được |

---

## 5. Lặp lại từ các bản phê bình trước (đã đối chiếu)

PO đã chạy 4 vòng critique (10–11/06). Đã đối chiếu đầy đủ trong báo cáo riêng:
**`plans/reports/reconciliation-bogo-critique-260613-1715-prior-vs-current-report.md`**.

> **Đính chính (so với bản nháp đầu của mục này):** vòng khắc phục của PO **CÓ chạy và chạy tốt** — **~70% blocker của các vòng trước đã đóng qua DEC** (giá DEC-54/55, offline DEC-53, trial 30 ngày DEC-55, ký số DEC-57, mã hoá/preview, reply+voice DEC-69, hash, gộp giá add-on DEC-60/62). Không phải "vòng khắc phục chưa đóng".

Chỉ còn các mục sau **thật sự lặp lại / chưa đóng** (đã xác minh trên spec hiện tại):

| Vấn đề | Trạng thái | Tham chiếu |
|--------|-----------|------------|
| GAP-ORG: dựng phòng ban + nhập NV hàng loạt | 🟡 Đóng một phần (tự đăng ký đã có) | B1 |
| PLATFORM_ADMIN: công cụ chủ động (at-risk) | 🟡 Đóng một phần (vòng đời/billing đã có) | C8 lân cận |
| AI thiếu AC khi LLM lỗi/timeout | 🔴 Còn mở | C7 |
| Dashboard/quota chi phí LLM (S6) | 🔴 Còn mở | C2 |
| Hạ tầng thông báo chung không ai sở hữu | 🔴 Còn mở | C5 |
| GTM không owner/ngân sách | 🔴 Còn mở | C3 |
| 33 must dồn vào "now" | 🔴 Còn mở | §3 |

> Lưu ý: vài mục "đã đóng" lại **đẻ vấn đề mới sâu hơn** — offline AC (đã thêm) nay lộ gian lận timestamp (C7); voice message (đã thêm) nay thiếu trần lưu trữ (C7). "Đóng lỗ cũ" ≠ "khu vực đó hoàn hảo".

---

## 6. Góc nhìn công cụ product-spec (đối chiếu v2.0.0 → v2.4.0)

Spec BoGo được viết bằng **product-spec v2.0.0** (MANIFEST ghi "1.1.0" là nhãn bản phát hành, không phải phiên bản skill — đã kiểm chứng từ mã thật). Bản hiện tại là **v2.4.0**.

### Cái bản mới (v2.4.0) bắt được mà v2.0.0 mù
Chạy máy quét v2.4.0 trên spec ra **145 cảnh báo**, nhưng **140 là nhiễu phiên bản, KHÔNG phải lỗi sản phẩm** — và quy về **đúng 2 việc gộp**, không phải 140 báo động:
- **`bad_version_format` (60):** spec dùng phiên bản 2 số (`0.4`, `0.5`); v2.4.0 đòi 3 số (`0.4.0`). → **1 lệnh chuẩn hóa.**
- **`misplaced_parent_field` (80):** mỗi story mang `prd:` + `brd_goals:` ở frontmatter; v2.4.0 quy ước story chỉ trỏ cha `epic`. → **1 lệnh dọn.**
- 5 cảnh báo còn lại (3 `risk_high_ratio`, 2 `persona_cap`) là thứ **cả hai phiên bản đều thấy** — và đã được chấp nhận từ vòng validate trước.

> Máy quét v2.0.0 (cái PO thực sự có) chỉ thấy **5** trong số này. Tức là **lớp kiểm tra tự động — kể cả bản mới nhất — chỉ chạm < 5% số vấn đề đáng giá.** Cấu trúc đúng là cần, nhưng không đủ.

### Cái CẢ HAI phiên bản đều SÓT (đây là backlog cho người bảo trì skill)
171/171 phát hiện thật trong báo cáo này **không máy nào bắt được** — vì chúng là phán đoán, không phải cấu trúc. Những lỗ công cụ rõ nhất:
1. **Không có kiểm tra "lời hứa → story".** GAP-ORG, nhập hàng loạt, self-signup — VISION hứa nhưng không story nào xây. Đề xuất: một check đối chiếu cam kết VISION/BRD với độ phủ story.
2. **Không phát hiện dư âm pivot.** Tên thương hiệu cũ (Cleanmatic), persona/phân hệ đã xóa còn nằm trong prose & frontmatter `owner/approved_by`. `check_consistency` bắt liên kết ID chết, **không** bắt tham chiếu prose tới phân hệ đã loại.
3. **Không có linter câu chữ.** "Ngắn gọn", "rõ ràng", "đề xuất — PO chốt" nằm ngay trong AC đã approved — không máy nào cảnh báo.
4. **Không đo INVEST.** Story gộp 9 AC / 4 hệ con không bị gắn cờ "quá tải, nên tách".
5. **Không phát hiện phụ thuộc ẩn.** "Đội build lo", AC dùng dữ liệu phân hệ khác mà không khai `depends_on`.
6. **Không nối chỉ số → cách đo.** BRD-G2 có metric nhưng không story baseline — không check nào thấy.

> **Lưu ý quy trình quan trọng:** spec đóng gói sẵn skill `spec-critique`, và PO **đã dùng** (4 bản). Nhưng các blocker vẫn mở — cho thấy điểm yếu không phải "thiếu công cụ phê bình" mà là **thiếu vòng đóng** giữa "phát hiện" và "story khắc phục".

---

## 7. Backlog ưu tiên

### Việc cho PRODUCT OWNER (nội dung spec) — theo thứ tự
| Ưu tiên | Việc | Liên quan |
|---------|------|-----------|
| P0 | Mở epic "Quản trị cơ cấu tổ chức" (phòng ban + nhập hàng loạt + self-signup), must/now | B1, G1-G3 |
| P0 | Thêm cụm AC an toàn tiền + chống lock-in (webhook ký, chargeback, xuất dữ liệu, chuyển quyền, cô lập tìm kiếm) | B3, B5, B6, C7 |
| P0 | Chạy 1 tuần đo chi phí LLM thật; chốt định vị AI; thêm quota/throttle | B4, C2 |
| P1 | Nâng onboarding (AI-E2-S5) lên must; tách phần tĩnh không cần LLM | B2 |
| P1 | Dọn dư âm Cleanmatic (cụm REPORT + nhãn vai HR) | C4 |
| P1 | Gán owner + ngân sách + KPI cho ≥1 kênh GTM trước go-live | C3 |
| P1 | Thêm story khảo sát baseline (G2) + dashboard at-risk (G3) | C9 |
| P2 | Tách các story khổng lồ (COMM-E1-S1, AI-E2-S4, APPROVAL-E1-S3) | C6 |
| P2 | Thêm quy trình NĐ13 (báo cáo sự cố + consent khuôn mặt + audit log) | C10 |
| P2 | Phục vụ EXEC (AI tóm tắt + giao việc từ dashboard) | C8 |
| P3 | Dọn câu chữ chưa đo được + đồng bộ trạng thái draft/approved | TB/Thấp §3 |

### Việc cho NGƯỜI BẢO TRÌ SKILL (công cụ product-spec)
| Ưu tiên | Việc | Lý do |
|---------|------|-------|
| Cao | Thêm check "độ phủ lời hứa" (VISION/BRD → story) | Bắt được GAP-ORG sớm |
| Cao | Thêm check dư âm pivot (tên/persona/phân hệ đã xóa trong prose + owner/approved_by) | Bắt được C4 |
| TB | Linter câu chữ (tính từ không đo được, "đề xuất" trong AC approved) | Bắt được phần lớn craft |
| TB | Heuristic INVEST (đếm AC/độ phức tạp story) | Bắt được C6 |
| TB | Phát hiện phụ thuộc ẩn ("đội build lo", dùng dữ liệu phân hệ khác) | Bắt được C5 |
| Thấp | Check "chỉ số → story đo" | Bắt được C9 |
| Quy trình | Cơ chế "đóng vòng" critique→DEC/story để không lặp lại | §5 |

---

## 8. Câu hỏi chưa giải đáp (cần PO quyết)
1. **GAP-ORG là PRD mới hay epic trong PRD-PLATFORM/PRD-HR?** Cần một phiên phỏng vấn riêng — đây là quyết định cấu trúc lớn.
2. **AI là "lý do mua" hay "lý do ở lại"?** Quyết định này đổi cả BRD-G3 metric lẫn cách định vị GTM.
3. **Giữ trial 14 ngày hay đổi mốc kích hoạt thành "hoàn tất 1 kỳ lương"?** (Bản phê bình vòng 2 đã nêu — đụng DEC-54, vẫn treo.)
4. **Một số phát hiện đụng artifact đã `approved`** (vd `PRD-AI-E2-S6` về kho tài liệu, định giá 89k DEC-54, web-parity DEC-66). Theo GATE-NO-SILENT-REVERSAL: cần PO chọn **Giữ / Đổi+phê duyệt lại / Lai** — báo cáo này KHÔNG tự sửa.
5. **Báo cáo chạy độc lập, chưa đối chiếu cơ học với 4 bản critique cũ.** Nên có một bước gộp trùng chính thức để theo dấu blocker nào đã đóng.

---

*Phụ lục bên dưới: bảng đầy đủ 171 phát hiện (ID:dòng · mức · lăng kính · vấn đề · cách sửa) + 2 việc gộp nhiễu phiên bản. Dữ liệu thô: `plans/260613-1436-bogo-spec-deep-critique/findings/`.*

---

## Phụ lục A — 2 việc gộp từ nhiễu phiên bản (v2.4.0)

| # | Việc | Phạm vi | Mức | Cách làm |
|---|------|---------|-----|----------|
| D1 | Chuẩn hóa định dạng phiên bản về 3 số (semver) | 60 artifact dùng `0.4` → `0.4.0` | Cosmetic | 1 lệnh migrate hàng loạt |
| D2 | Dọn trường cha thừa ở story | 80 story mang `prd:`+`brd_goals:` (v2.4.0 chỉ cần `epic:`) | Thấp (DRY) | 1 lệnh migrate; giữ `epic:` |

> Hai việc này là quy ước mới của công cụ, KHÔNG phải lỗi PO. Đừng để 140 cảnh báo này che mất 171 phát hiện thật ở trên.

---

## Phụ lục B — Bảng đầy đủ 171 phát hiện thật

*Mức: CHẶN = blocker · CAO = high · TB = trung bình · THẤP = thấp. Vị trí `ID:dòng` trỏ thẳng vào file spec BoGo.*

| # | Mức | Lăng kính | Vị trí (ID:dòng) | Vấn đề | Cách sửa (tóm tắt) |
|---|-----|-----------|------------------|--------|--------------------|
| 1 | CHẶN | market | PRD-AI:36 | Điểm khác biệt AI tiếng Việt đang bị đối thủ lấp đầy trước khi BoGo ra mắt | Cần bổ sung một câu đặc tả CỤ THỂ vào PRD-AI về điều BoGo làm mà Base AI/1AI/Tanca không làm được: ví dụ AI gắn đồng thời dữ liệu HR + TASK + COMM của chính tổ … |
| 2 | CHẶN | spine | PRD-AI-E2-S5:10 | Đường kích hoạt tổ chức (BRD-G3, ≥70%) phụ thuộc vào một story 'should' có thể bị cắt | Nâng PRD-AI-E2-S5 từ 'should' lên 'must'. Nếu lo ngại về khối lượng build của AI, tách thành hai phần: (a) must — checklist tĩnh tự cập nhật theo dữ liệu thật (… |
| 3 | CHẶN | tech | PRD-COMM-E1-S1:53 | Hợp đồng ERP-link có entity_type 'order→SALES' nhưng PRD-SALES đã bị loại khỏi sản phẩm | Gỡ 'order' ra khỏi danh sách entity_type ban đầu trong hợp đồng ERP-link ở S1 cho đến khi có PRD sở hữu đơn hàng. Danh sách khởi động thực tế chỉ là shift/task.… |
| 4 | CHẶN | spine | VISION:62 | Không có story nào xây màn hình quản lý phòng ban — xương sống của toàn hệ thống bị trống | Thêm một story mới vào PRD-HR hoặc tạo epic 'Quản trị cơ cấu tổ chức' (moscow: must, now): AC tối thiểu gồm ORG_ADMIN tạo/sửa/xoá phòng ban (nhiều cấp, không gi… |
| 5 | CHẶN | product | PRD-PLATFORM-E1-S1:26 | PRD-PLATFORM giải quyết thanh toán nhưng vẫn bỏ trống màn hình dựng phòng ban — GAP-ORG chưa đóng | Thêm ít nhất 2 story vào PRD-PLATFORM-E1 hoặc tạo epic mới: (1) ORG_ADMIN tạo/sửa/xoá phòng ban nhiều cấp, gán trưởng phòng; (2) ORG_ADMIN nhập hàng loạt nhân v… |
| 6 | CHẶN | tech | PRD-PLATFORM-E1-S1:30 | Chính sách xóa dữ liệu khi tổ chức đóng ('theo chính sách lưu trữ') không có story sở hữu — không kiểm thử được | Thêm AC vào PRD-PLATFORM-E1-S1 hoặc tạo story riêng mô tả pipeline offboarding: (1) 60 ngày sau tạm ngưng → gửi email cảnh báo xóa cuối cùng tới ORG_ADMIN; (2) … |
| 7 | CHẶN | product | PRD-PLATFORM-E1-S1:30 | Không có story nào cho tổ chức CHỦ ĐỘNG rời đi: huỷ gói, xuất dữ liệu, chuyển quyền ORG_ADMIN | Thêm ba AC vào PRD-PLATFORM: (1) ORG_ADMIN tự đóng gói và nhận link xuất toàn bộ dữ liệu tổ chức ra CSV/Excel trong 24 giờ trước khi xoá; (2) ORG_ADMIN chuyển q… |
| 8 | CHẶN | spine | PRD-PLATFORM-E1-S1:29 | Không có story nào cho phép tổ chức chủ động rời BoGo và lấy lại dữ liệu của mình | Thêm ít nhất một story vào PRD-PLATFORM-E1 cho ORG_ADMIN: (1) tự đóng gói / rời dịch vụ có xác nhận kèm AC xuất toàn bộ dữ liệu ra định dạng mở (CSV/Excel) trướ… |
| 9 | CHẶN | tech | PRD-PLATFORM-E2-S3:28 | Không có AC cho trường hợp hoàn tiền/chargeback ngân hàng sau khi gạch nợ đã chạy | Thêm AC: 'Nếu cổng thanh toán hoặc dịch vụ đối soát thông báo giao dịch bị hoàn/reversal sau khi đã gạch nợ → hệ thống gắn cờ đơn vào hàng đợi xử lý tay của PLA… |
| 10 | CHẶN | tech | PRD-TASK-E1-S2:26 | Tính năng "moat" HAI CHIỀU task↔ca làm chỉ được mô tả ở một phía | Thêm một AC vào PRD-HR-E1-S3 (hoặc tạo AC trong một story HR phù hợp) với nội dung có thể kiểm thử: "Khi công việc gắn vào ca làm chuyển trạng thái Hoàn thành, … |
| 11 | CAO | market | BRD:147 | Tanca ra mắt gói miễn phí vĩnh viễn — so sánh đối thủ trong BRD đã lỗi thời | Bổ sung vào BRD §Bối cảnh thị trường: ghi nhận gói free của Tanca và giải thích rõ BoGo nhắm vào phân khúc nào không bị gói free đó phủ (ví dụ: tổ chức ≥20 nhân… |
| 12 | CAO | market | BRD:183 | Ba kênh GTM đều chưa có người chịu trách nhiệm, không ngân sách, không mốc thời gian | Trước khi ra mắt thương mại, mỗi kênh GTM phải có: (1) tên người/nhóm chịu trách nhiệm, (2) ngân sách ước tính hoặc cam kết thời gian, (3) KPI đầu tiên và mốc k… |
| 13 | CAO | market | BRD:179 | AI là điểm bán chính nhưng kinh tế AI chưa được đo — bán trước, kiểm sau là rủi ro mô hình doanh thu | Trước pilot chính thức, chạy một bài đo chi phí LLM nhỏ (mock hoặc internal sandbox): số token trung bình/câu hỏi × giá API hiện tại × ước lượng query/user/thán… |
| 14 | CAO | market | BRD:179 | Trần chi phí LLM 13k/user/tháng chưa có con số thật — nếu sai thì margin âm hoặc AI bị cắt khỏi gói | Trước khi lock giá 89k cho pilot trả phí đầu tiên: chạy 1 tuần shadow mode trên tổ chức nội bộ, đếm thực tế số query/user/ngày × token/query × giá token (GPT-4o… |
| 15 | CAO | market | BRD:192 | Năm trigger mua trong BRD không có trigger nào liên quan đến AI — AI không phải lý do tổ chức quyết định mua | Tách rõ trong BRD: AI là 'lý do ở lại' (retention hook) hay 'lý do mua' (acquisition hook)? Nếu là retention: thì BRD-G3 metric nên đo tỉ lệ tổ chức có dùng AI … |
| 16 | CAO | market | BRD:183 | Toàn bộ GTM ghi 'đề xuất — gán owner khi vận hành': không có ai chịu trách nhiệm đạt G1 (100 tổ chức/12 tháng) | BRD cần ghi ít nhất: kênh nào BoGo sẽ làm TRƯỚC (chỉ 1), ngân sách CAC kỳ vọng cho kênh đó, và ai trong team chịu trách nhiệm đo. Nếu hiện tại thực sự chưa có đ… |
| 17 | CAO | spine | BRD:117 | Chỉ số BRD-G2 'admin-time-reduction ≥50%' không có story nào định nghĩa cách đo baseline | Thêm AC đo baseline vào PLATFORM-E1-S1 hoặc tạo story riêng 'Khảo sát baseline pilot' (moscow: must, gắn BRD-G2): định nghĩa rõ template khảo sát (loại task, th… |
| 18 | CAO | market | BRD:148 | Tanca ra mô hình mua-một-lần + Starter miễn phí không giới hạn nhân viên — so sánh trong BRD đã lỗi thời về mô hình kinh doanh, không chỉ giá | Cập nhật phần so sánh Tanca trong BRD: ghi nhận mô hình mua-một-lần và free tier; tái định vị BoGo không phải ở AI (Tanca đã có) hay giá thấp hơn (Tanca free ti… |
| 19 | CAO | market | BRD:130 | BRD-G3 đặt mục tiêu churn ≤3%/tháng nhưng không có tính năng chủ động giảm churn — toàn bộ phụ thuộc vào SUPPORT phản ứng sau khi tổ chức đã bỏ | Thêm vào PLATFORM_ADMIN dashboard (PRD-PLATFORM-E1) tối thiểu: (1) danh sách tổ chức có dấu hiệu giảm hoạt động (% nhân viên active/tuần giảm >20% so tuần trước… |
| 20 | CAO | spine | BRD:204 | Không có story nào sở hữu quy trình thông báo vi phạm dữ liệu cá nhân theo NĐ13/2023 | Thêm AC vào PRD-PLATFORM-E1-S2 (PLATFORM_ADMIN quản vòng đời) hoặc tạo story riêng: (1) PLATFORM_ADMIN xác nhận và ghi nhận sự cố vi phạm dữ liệu; (2) hệ thống … |
| 21 | CAO | market | PRD-AI:36 | Tuyên bố 'AI tiếng Việt gắn dữ liệu vận hành' không còn độc quyền — Tanca đã có 6 AI agent tiếng Việt | Làm rõ lại điểm khác biệt AI thực sự của BoGo: không phải 'có AI tiếng Việt' (Tanca cũng có) mà là 'AI trả lời trên TÀI LIỆU NỘI BỘ của chính tổ chức đó + dữ li… |
| 22 | CAO | product | PRD-AI-E2:48 | BRD đặt ràng buộc cứng chi phí LLM ≤15% doanh thu — nhưng không có AC nào trong E2 đo hoặc enforce điều này | Thêm vào S6 ít nhất 2 AC: (1) PLATFORM_ADMIN xem được chi phí LLM ước tính per-tổ-chức theo tuần/tháng; (2) Khi chi phí LLM của một tổ chức vượt ngưỡng cảnh báo… |
| 23 | CAO | market | PRD-AI-E2:50 | Giá trị AI phụ thuộc kho tri thức tổ chức tải lên — nhưng spec không có cơ chế buộc tổ chức làm điều này | Thêm vào S5 (onboarding) một bước bắt buộc trong checklist: tải lên ít nhất 1 tài liệu quy chế trước khi hoàn thành onboarding (AC kiểm chứng: tổ chức chưa tải … |
| 24 | CAO | market | PRD-AI-E2:43 | Rủi ro NĐ13 về PII gửi qua API LLM bên thứ ba được 'chấp nhận tạm' nhưng không có ngưỡng quy mô cụ thể để bắt buộc xử lý | Thêm vào BRD hoặc PRD-AI một ngưỡng cứng: ví dụ 'khi đạt 30 tổ chức trả phí hoặc trước vòng gọi vốn đầu tiên — phải có ý kiến luật sư + chính sách che PII tối t… |
| 25 | CAO | tech | PRD-AI-E2-S1:27 | AC hiệu năng '95% câu hỏi ≤ 10 giây' không đo được trong thực tế | Thêm điều kiện đo vào AC: 'Đo trên kho tài liệu ≤ X trang, với ≤ Y org dùng đồng thời, trên kết nối 4G/WiFi bình thường, hệ thống đạt p95 ≤ 10 giây. Nếu vượt ng… |
| 26 | CAO | tech | PRD-AI-E2-S1:24 | Không có AC cho trường hợp dịch vụ LLM hoặc vector-store bị lỗi hoặc timeout | Thêm một AC lỗi cụ thể: 'Giả sử dịch vụ LLM hoặc pipeline tài liệu không phản hồi trong vòng 15 giây hoặc trả về lỗi, thì trợ lý hiển thị thông báo rõ ràng bằng… |
| 27 | CAO | product | PRD-AI-E2-S3:45 | EXEC — persona có pain rõ ràng trong VISION — không được phục vụ bởi bất kỳ story AI nào trong MVP | Thêm một AC cho S3: trợ lý cho phép EXEC hỏi 'tóm tắt tình hình tổ chức hôm nay' và nhận bản tóm tắt cấp tổ chức (% đi làm, số việc trễ, phòng nào quá tải) — đú… |
| 28 | CAO | tech | PRD-AI-E2-S4:10 | S4 'Đào tạo nội bộ & bài kiểm tra' (size L, should) gộp 4 hệ con khác nhau trong một story | Tách S4 thành ít nhất hai story: S4a 'AI sinh bài kiểm tra từ tài liệu — có người duyệt trước khi phát' (phần AI, must) và S4b 'Phát bài, chấm tự động và xem kế… |
| 29 | CAO | product | PRD-AI-E2-S4:44 | Tính năng đào tạo & bài kiểm tra không có nguồn gốc từ pain point trong BRD/VISION | Hạ moscow xuống 'could' và dời sang horizon 'next'. Trước khi đưa trở lại backlog, kiểm chứng bằng câu hỏi cụ thể với ít nhất 3 SME pilot: 'Bạn có đang soạn đề … |
| 30 | CAO | tech | PRD-AI-E2-S5:24 | S5 phụ thuộc ngầm vào PRD-PLATFORM-E1-S1 (workspace creation) nhưng không khai báo depends_on | Thêm `depends_on: [PRD-PLATFORM-E1-S1]` vào frontmatter của S5. Bổ sung ghi chú thiết kế: 'Story này chỉ có thể nghiệm thu sau khi workspace provisioning (PLATF… |
| 31 | CAO | product | PRD-AI-E2-S5:24 | S5 hướng dẫn ORG_ADMIN tới các màn hình chưa có story nào build (dựng phòng ban, bulk import nhân viên) | Thêm ít nhất 2 story trong PRD-HR hoặc PRD-PLATFORM (horizon: now, moscow: must): (1) ORG_ADMIN tạo và chỉnh sửa cây phòng ban (tên phòng, cấp bậc, gán trưởng p… |
| 32 | CAO | product | BRD:180 | BRD đặt ràng buộc cứng chi phí LLM ≤15% doanh thu/tổ chức nhưng không có cơ chế quota hay throttle per-org trong bất kỳ story AI nào | Thêm vào PRD-AI-E2-S6 hoặc PRD-PLATFORM: (1) PLATFORM_ADMIN thấy lượng AI query/tổ chức/tháng và chi phí ước tính; (2) cấu hình ngưỡng cảnh báo và throttle per-… |
| 33 | CAO | product | PRD-APPROVAL:65 | Trigger mua của APPROVAL chưa được kiểm chứng, nhưng toàn bộ 5 story đã approved và coi là must | Trước khi spec APPROVAL ở trạng thái 'sẵn sàng build', thêm một câu hỏi kiểm chứng cụ thể vào kế hoạch pilot: hỏi trực tiếp 3–5 tổ chức pilot xem họ có bị thanh… |
| 34 | CAO | tech | PRD-APPROVAL:66 | APPROVAL tính phí theo 'lượng tờ trình/tháng' nhưng không có story nào đo đếm và giới hạn số lượng tờ trình | Tạo story mới PRD-PLATFORM-E2-S5 'Hạn mức và đo đếm tờ trình theo gói add-on APPROVAL' (tương đương S4 cho RESOURCE): PLATFORM_ADMIN cấu hình hạn mức tờ trình/t… |
| 35 | CAO | tech | PRD-APPROVAL-E1-S2:27 | Luồng duyệt đa cấp (S2) phụ thuộc sơ đồ tổ chức từ PRD-HR nhưng không có AC kiểm thử khi sơ đồ thiếu dữ liệu hoặc không hợp lệ | Thêm AC edge path: 'Tờ trình được tạo cho phòng ban chưa có trưởng phòng trong sơ đồ → hệ thống chặn trình và thông báo rõ lý do ngay khi bấm Trình; ORG_ADMIN n… |
| 36 | CAO | tech | PRD-APPROVAL-E1-S3:11 | Story ký xác nhận (S3) được đánh size M nhưng thực tế phải build 4 luồng xác thực riêng biệt | Tách S3 thành ít nhất 2 story: (S3a) cơ chế passkey + PIN + bản ghi ký bất biến với hash; (S3b) OTP/khuôn mặt camera bậc CAO + đăng ký/thu hồi thiết bị tin cậy.… |
| 37 | CAO | tech | PRD-APPROVAL-E1-S3:26 | Ký xác nhận trên web không đạt 'bậc thường mặc định' vì passkey phụ thuộc phần cứng thiết bị — mâu thuẫn với ràng buộc web parity DEC-66 | Thêm AC riêng cho web: 'Trên web, bậc Thường = PIN (không có passkey); bậc Cao = OTP email/SMS. Đây là ngoại lệ DEC-66 được phép vì passkey gắn phần cứng thiết … |
| 38 | CAO | craft | PRD-APPROVAL-E1-S5:26 | Lỗi đánh máy 'AI duyệt' trong AC kanban — đội build sẽ hiểu sai | Thay 'đang chờ AI duyệt (cấp mấy)' bằng 'đang chờ ai duyệt (tên người, cấp mấy)' — chữ thường, có thêm 'tên người' để rõ nghĩa hiển thị. |
| 39 | CAO | product | PRD-COMM:95 | Không có story nào xây dựng 'cơ chế kéo' Zalo-switch — giả định trung tâm của COMM thiếu bằng chứng thực thi | Thêm ít nhất một story cho ORG_ADMIN: thiết lập policy 'kênh giao tiếp chính thức' (ví dụ: thông báo nội bộ phải qua COMM, không qua Zalo) và xem báo cáo adopti… |
| 40 | CAO | tech | PRD-COMM:82 | Hạ tầng push notification không có PRD sở hữu — 5 story COMM phụ thuộc trực tiếp vào nó mà không có spec | Thêm một story kỹ thuật (tech enabler) vào PRD-PLATFORM hoặc một epic mới, sở hữu spec hạ tầng thông báo chung: SLA in-app ≤5 giây + push ≤30 giây, offline queu… |
| 41 | CAO | tech | PRD-COMM-E1-S1:23 | S1 nhắn tin 1-1 gộp 9 AC thuộc 5 chức năng riêng biệt — khó ước lượng và khó nghiệm thu từng phần | Tách S1 thành ít nhất 3 story: (1) Chat cơ bản (text + trạng thái + real-time + reconnect); (2) Đính kèm file + voice message (storage, liên kết tự làm mới, ghi… |
| 42 | CAO | tech | PRD-COMM-E1-S1:25 | File và voice message được hứa giữ 'bất kỳ lúc nào trong suốt vòng đời hội thoại' nhưng không có chính sách lưu trữ hay trần chi phí | Thêm AC vào S1: (1) Định nghĩa 'vòng đời hội thoại' — file giữ bao lâu (ví dụ: 12 tháng hoặc tới khi hội thoại bị lưu trữ/xoá); (2) Đặt quota storage/tổ chức cấ… |
| 43 | CAO | tech | PRD-COMM-E1-S1:25 | Voice message và file đính kèm giữ 'bất kỳ lúc nào trong suốt vòng đời hội thoại' nhưng không có trần dung lượng per-org cho media COMM — mâu thuẫn với kinh tế gói 89k | Thêm AC vào E1-S1: 'Dung lượng lưu trữ media (ảnh, file, voice) của COMM nằm trong hạn mức tổng theo gói, quản lý cùng cơ chế [[PRD-PLATFORM-E2-S4]]; chạm trần … |
| 44 | CAO | product | PRD-COMM-E1-S7:10 | S7 (màu + tag tin nhắn) giữ 'must' — tính năng hoàn toàn mới với người dùng Zalo — chặn go-live cả cụm COMM nếu chậm | Thêm AC đo tỉ lệ dùng S7 trong pilot (% tin nhắn được gán màu/tag sau 4 tuần); nếu dưới 20% thì đây là gold-plating và nên rút khỏi core scope v1. Ít nhất, thêm… |
| 45 | CAO | product | PRD-COMM-E2:9 | Broadcast (kênh thông báo chính của quản lý) bị xếp 'should' trong khi các tính năng chat phụ trợ lại là 'must' | Nâng PRD-COMM-E2-S1 (broadcast có phân quyền) lên 'must'. Đây là tính năng cốt lõi của vai ORG_ADMIN/DEPT_MGR/EXEC trong COMM — không có broadcast thì các vai n… |
| 46 | CAO | tech | PRD-COMM-E3-S1:28 | Full-text search index tin nhắn không có AC phân tách theo tenant — lọc quyền sau khi đã lập index chung là mô hình rủi ro cross-tenant | Thêm AC vào E3-S1: 'Kết quả tìm kiếm của tổ chức A không bao giờ chứa bất kỳ nội dung nào từ tổ chức B — bao gồm metadata (tên người, tên nhóm) của tổ chức khác… |
| 47 | CAO | spine | VISION:32 | VISION cam kết 2 'sơ đồ tổ chức là xương sống' — spec không có màn hình nào xây xương sống đó | Xem fix của finding spine-gap-org-escalated — cùng vấn đề, cần story 'Quản lý cơ cấu tổ chức' với AC: tạo/sửa/xoá phòng ban nhiều cấp; gán vai trò cho từng vị t… |
| 48 | CAO | product | PRD-HR-E1-S1:40 | Story dùng nhãn vai trò của Cleanmatic cũ, không phải persona BoGo | Thay tất cả nhãn 'nhân viên giao nhận hoặc nhân viên xử lý' bằng 'nhân viên (STAFF)'; thay 'quản lý hệ thống' bằng 'quản trị tổ chức (ORG_ADMIN)'. Rà toàn bộ 14… |
| 49 | CAO | tech | PRD-HR-E1-S1:33 | Chấm công offline dùng 'timestamp thiết bị' — không có AC chống giả mạo đồng hồ thiết bị | Bổ sung AC: 'Khi đồng bộ offline record, hệ thống so sánh timestamp thiết bị với server time tại thời điểm nhận sync; nếu chênh lệch > [ngưỡng cấu hình, mặc địn… |
| 50 | CAO | tech | PRD-HR-E1-S1:32 | Không có AC cho trường hợp nhân viên từ chối đồng ý sinh trắc — hệ thống bị kẹt | Thêm AC: 'Nếu nhân viên từ chối ký đồng ý sinh trắc → hệ thống KHÔNG block onboarding; nhân viên được cấu hình dùng PIN/mã NV làm phương thức chấm công chính (p… |
| 51 | CAO | tech | PRD-HR-E1-S1:32 | Quyền yêu cầu xóa vector sinh trắc không có luồng thực thi — nhân viên biết quyền nhưng không có nút/màn hình nào để thực hiện | Thêm AC vào PRD-HR-E1-S6: 'STAFF xem và rút đồng ý dữ liệu sinh trắc từ hồ sơ cá nhân của mình bất kỳ lúc nào; gửi yêu cầu xóa → ORG_ADMIN nhận thông báo; xóa h… |
| 52 | CAO | product | VISION:64 | Không có story nào build tính năng nhập hàng loạt nhân viên từ file, trong khi VISION đặt đây là kịch bản thành công ngày đầu tiên | Thêm AC vào PRD-HR-E1-S6 (hoặc tạo story riêng) cho phép ORG_ADMIN import nhân viên hàng loạt từ file Excel/CSV: template tải sẵn, validate lỗi theo dòng, hiển … |
| 53 | CAO | tech | PRD-HR-E1-S6:24 | Không có AC cho nhập hàng loạt nhân viên — VISION đặt kịch bản '40 nhân viên từ file trong buổi sáng đầu tiên' nhưng story không bao gồm bulk import | Thêm AC vào PRD-HR-E1-S6 hoặc tạo story riêng: 'ORG_ADMIN tải lên file (Excel/CSV mẫu) nhập hàng loạt nhân viên; hệ thống validate từng dòng (trùng mã, thiếu tr… |
| 54 | CAO | product | PRD-HR-E2:40 | Epic E2 vẫn tham chiếu 'PRD-FINANCE' đã bị loại bỏ — luồng phiếu chi lương không còn ai sở hữu | Xóa dòng 'Liên kết phiếu chi: Khi bảng lương approved → tạo phiếu chi lương tại PRD-FINANCE' khỏi phần Phạm vi của PRD-HR-E2. Thay bằng: 'Chi lương: kết xuất Ex… |
| 55 | CAO | tech | PRD-HR-E2:40 | Epic E2 scope vẫn đề cập 'tạo phiếu chi lương tại PRD-FINANCE' — PRD-FINANCE đã bị loại hoàn toàn | Sửa dòng 40 trong PRD-HR-E2.md: xoá 'Liên kết phiếu chi: Khi bảng lương approved → tạo phiếu chi lương tại PRD-FINANCE.' và thay bằng: 'Xuất Excel/CSV bảng lươn… |
| 56 | CAO | tech | PRD-HR-E2-S4:26 | Thưởng KPI (must) phụ thuộc vào story TASK-E3-S2 chỉ là 'should' — không có ràng buộc build ordering | Hoặc nâng PRD-TASK-E3-S2 lên `moscow: must` (khớp với tầm quan trọng của KPI payroll), hoặc thêm AC vào PRD-HR-E2-S4 mô tả rõ hành vi khi TASK data chưa khả dụn… |
| 57 | CAO | market | PRD-PLATFORM-E1-S1:30 | Không có story xuất dữ liệu / offboarding tổ chức — SME Việt Nam lo khóa vendor khi quyết định mua SaaS | Thêm story PRD-PLATFORM (hoặc story con trong E1) cho phép ORG_ADMIN xuất toàn bộ dữ liệu tổ chức (nhân viên + bảng công + bảng lương + danh sách công việc) dướ… |
| 58 | CAO | spine | PRD-PLATFORM-E1-S2:24 | ORG_ADMIN không có màn hình tra cứu log hoạt động thống nhất cho toàn tổ chức mình | Thêm story vào PRD-PLATFORM-E1 hoặc PRD-TASK-E4: ORG_ADMIN tra cứu nhật ký hoạt động toàn tổ chức (thao tác quan trọng: thay đổi lương, phê duyệt, sửa chấm công… |
| 59 | CAO | tech | PRD-PLATFORM-E1-S1:30 | Máy trạng thái thuê bao mâu thuẫn: trial hết hạn không qua ân hạn, nhưng spec gói có trả phí thì có | Bổ sung một AC tường minh trong E1-S1 (hoặc E2-S2): trial hết hạn CÓ hay KHÔNG có ân hạn 7 ngày trước khi vào KHOÁ GHI — PO chốt một con số rõ. Ví dụ AC: 'Trial… |
| 60 | CAO | tech | PRD-PLATFORM-E1-S1:27 | Điều kiện gia hạn trial '60% nhân viên chấm công' không định nghĩa mẫu số — không kiểm thử được | Sửa AC thành: 'Mẫu số = tổng nhân viên có tài khoản ACTIVE trong tổ chức tại thời điểm kiểm tra (không tính tài khoản bị vô hiệu hoá); điều kiện chỉ trigger khi… |
| 61 | CAO | tech | PRD-PLATFORM-E1-S1:29 | Không có story nào định nghĩa cách PLATFORM_ADMIN hỗ trợ khôi phục tài khoản ORG_ADMIN duy nhất mà không vi phạm ranh giới dữ liệu | Thêm AC vào PRD-PLATFORM-E1-S2 hoặc PRD-SUPPORT-E1-S3: 'Khôi phục tài khoản ORG_ADMIN qua kênh hỗ trợ: PLATFORM_ADMIN gửi magic-link một lần tới email đã đăng k… |
| 62 | CAO | product | PRD-PLATFORM-E1-S1:24 | Không có story nào xây dựng màn hình dựng sơ đồ phòng ban — bước đầu tiên của kịch bản thành công ORG_ADMIN trong VISION | Tạo story mới trong PRD-PLATFORM-E1 (hoặc PRD-HR nếu sơ đồ tổ chức thuộc về HR): ORG_ADMIN tạo cây phòng ban nhiều cấp, đặt tên phòng, gán trưởng phòng (DEPT_MG… |
| 63 | CAO | tech | PRD-PLATFORM-E2-S2:24 | Lịch nhắc hạn (14/7/3/1 ngày) không xác định có áp cho trial 14 ngày không — và nếu áp thì ngày nhắc đầu tiên trùng ngày đăng ký | Thêm một AC trong E2-S2 (hoặc E1-S1) chỉ rõ lịch nhắc trial: ví dụ 'Trial: nhắc vào ngày [PO chọn, ví dụ 7/3/1 ngày trước hết hạn, KHÔNG nhắc ở mốc 14 ngày vì t… |
| 64 | CAO | tech | PRD-PLATFORM-E2-S3:25 | Webhook thanh toán không có AC xác thực chữ ký (HMAC/secret) — mở cổng giả mạo gạch nợ | Thêm AC bắt buộc: 'Mọi webhook nhận vào (VietQR bank/đối soát và cổng thanh toán) phải được xác thực trước khi xử lý: kiểm tra chữ ký HMAC (hoặc cơ chế secret c… |
| 65 | CAO | craft | PRD-REPORT:8 | PRD-REPORT và toàn bộ epic/story con vẫn mang tên thương hiệu Cleanmatic và persona/phân hệ không tồn tại trong BoGo | Thêm ghi chú đầu file rõ ràng vào mỗi file REPORT: `> ⛔ TÀI LIỆU LỊCH SỬ — Cleanmatic. Không áp dụng cho BoGo.` Cập nhật `approved_by` và `owner` thành `(Lưu tr… |
| 66 | CAO | craft | PRD-REPORT-E1-S1:25 | AC của PRD-REPORT-E1-S1 đặt tên persona Cleanmatic (ZONE_MGR, SYS_ADMIN) và phân hệ không có trong BoGo (FINANCE, SALES, INVENTORY, PAYMENT, CARE) | Thêm ghi chú `> ⚠️ LỊCH SỬ CLEANMATIC — AC bên dưới không áp dụng cho BoGo` ngay trước phần acceptance_criteria. Không cần sửa nội dung AC (giữ để tra cứu lịch … |
| 67 | CAO | product | PRD-RESOURCE-E1-S2:27 | Theme màu/biểu tượng thư mục được đánh moscow=must trong khi rủi ro adoption 'kho rỗng' vẫn OPEN | Tách theme màu/icon ra khỏi moscow=must, hạ xuống should hoặc could. Đầu tư phần story đó vào cơ chế kéo adoption thực sự: ví dụ một màn onboarding gợi ý tổ chứ… |
| 68 | CAO | product | PRD-SUPPORT-E1-S1:25 | AI hỗ trợ tuyến đầu phụ thuộc kho hướng dẫn chính thức của BoGo — nhưng không có story nào xây kho này | Thêm một story hoặc task rõ ràng cho PLATFORM_ADMIN: 'Biên soạn và xuất bản kho hướng dẫn sử dụng BoGo trước go-live' — liệt kê số bài tối thiểu cần có (ít nhất… |
| 69 | CAO | product | PRD-TASK:52 | E4 (dashboard điều hành) không xuất hiện trong phần 'Trong phạm vi' của PRD-TASK | Thêm E4 ('Dashboard tổng quan điều hành: nhân sự + công việc, báo cáo định kỳ') vào phần 'Trong phạm vi' của PRD-TASK. Đồng thời ghi rõ E4 là lớp trình bày đọc … |
| 70 | CAO | spine | VISION:76 | EXEC chỉ có 1 must story trong horizon now — kịch bản thành công của lãnh đạo gần như trống | Rà lại EXEC story coverage trước khi go-live MVP: ít nhất cần (1) TASK-E4-S1 dashboard EXEC có thể drill-down đến phòng ban cụ thể và giao việc nhanh từ điểm nó… |
| 71 | CAO | product | PRD-TASK-E1:18 | EXEC không có trong E1/E2/E3 — lãnh đạo không tạo hoặc giao việc được theo spec | Bổ sung EXEC vào personas của E1 và E2. Làm rõ trong E1-S2 AC rằng EXEC giao việc xuyên phòng ban được (hiện chỉ có 1 dòng ngoại lệ ở AC line 31 nhưng persona k… |
| 72 | CAO | tech | PRD-TASK-E1-S1:20 | STAFF được liệt kê là persona tạo việc nhưng quyền tạo task của STAFF không được định nghĩa | Làm rõ trong E1-S1: hoặc (a) xóa STAFF khỏi personas nếu chỉ DEPT_MGR/ORG_ADMIN/EXEC tạo được task; hoặc (b) thêm AC cụ thể: "STAFF chỉ tạo task tự giao cho bản… |
| 73 | CAO | product | PRD-TASK-E2-S4:27 | Ai là 'người duyệt' trong luồng Chờ duyệt chưa được định nghĩa rõ | Làm rõ trong E1-S1 hoặc E1-S2: khi bật 'cần duyệt', người tạo có chọn người duyệt cụ thể không, hay mặc định là người giao? Nếu có thể chọn riêng, bổ sung AC và… |
| 74 | CAO | tech | PRD-TASK-E4-S1:24 | Dashboard tổng quan cần HR expose số liệu đi làm/vắng theo phòng ban nhưng không có story HR nào định nghĩa endpoint này | Bổ sung AC vào PRD-HR-E1-S4 (hoặc thêm story mới): "HR expose endpoint tổng hợp trả về: số nhân viên đi làm/vắng/chưa chấm công theo phòng ban cho ngày hiện tại… |
| 75 | CAO | tech | PRD-TASK-E4-S5:25 | Gửi báo cáo qua email phụ thuộc hạ tầng email không được spec trong bất kỳ story nào | Thêm NFR rõ ràng vào E4-S5 hoặc PRD-PLATFORM: "Hệ thống dùng dịch vụ email transactional [provider cụ thể, vd: SendGrid/AWS SES/Mailgun]; cấu hình domain xác th… |
| 76 | CAO | spine | VISION:19 | 37 must story dồn vào horizon 'now' (0–3 tháng) — không có phân chia sprint nội bộ, rủi ro trượt toàn bộ | Thêm trường 'sprint' hoặc 'wave' (wave-1, wave-2, wave-3 trong horizon now) vào frontmatter của các story now, hoặc ít nhất thêm một bảng thứ tự go-live vào PRO… |
| 77 | CAO | spine | VISION:64 | VISION đặt 'nhập 40 nhân viên từ file' là kịch bản thành công ngày đầu tiên nhưng không có story nào build tính năng import hàng loạt | Tạo story cho PRD-HR-E1 hoặc PRD-PLATFORM-E1: ORG_ADMIN import danh sách nhân viên từ file Excel/CSV với template chuẩn (tên, mã NV, SĐT, phòng ban, chức danh, … |
| 78 | TB | market | BRD:176 | Fiine PRO 59k có chấm công + giao việc + chat — khoảng cách giá 30k/user/tháng chưa được biện hộ đủ | Thêm vào BRD một dòng so sánh Fiine rõ ràng hơn: BoGo khác ở độ sâu tính lương (payroll rules + BHXH), tích hợp HĐĐT/eContract pháp lý, và AI trên kho tài liệu … |
| 79 | TB | market | BRD:201 | Rào cản 'đổi từ Zalo' được ghi nhận là rủi ro nhưng không có cơ chế giảm chuyển đổi cụ thể trong spec | Thêm vào BRD hoặc PRD-COMM một chiến lược chuyển đổi cụ thể: ví dụ ORG_ADMIN có thể bật 'chế độ song song Zalo' (thông báo giao việc gửi đồng thời qua Zalo tron… |
| 80 | TB | market | BRD:178 | Mục tiêu 100 tổ chức / 3,2 tỷ ARR chưa được đối chiếu với năng lực bán hàng thực tế của team | Bổ sung vào BRD một dòng năng lực bán hàng: số nhân sự GTM + CS hiện có, số tổ chức tối đa có thể phục vụ song song, và mốc nào sẽ tuyển thêm. Nếu mô hình hoàn … |
| 81 | TB | market | BRD:176 | So sánh giá với 1Office trong BRD dùng con số cũ — giá thực tế 1Office all-in-one là 100k/user (Standard/Pro) hoặc 150k/user (gói đầy đủ) | Cập nhật mục Mô hình doanh thu BRD: thêm ghi chú rằng 1Office yêu cầu cam kết tối thiểu 1 năm, BoGo chu kỳ tháng là lợi thế cho SME nhỏ chưa chắc chắn. Đồng thờ… |
| 82 | TB | spine | BRD:158 | Ràng buộc web parity (DEC-66) không kèm bất kỳ yêu cầu nào về khả năng tiếp cận (accessibility) | Thêm ràng buộc vào BRD hoặc PRODUCT.md: 'Giao diện web tuân thủ tối thiểu WCAG 2.1 cấp AA cho các luồng nghiệp vụ cốt lõi (đăng nhập, chấm công web, giao việc, … |
| 83 | TB | tech | PRD-AI-E2.md:34 | Không có AC nào yêu cầu kiểm thử rằng context window LLM không chứa dữ liệu của hai org khác nhau trong cùng một request | Thêm một AC vào S6: 'Trước go-live, đội build chạy test xuyên tổ chức: gửi đồng thời câu hỏi từ 2 org khác nhau, xác nhận prompt gửi đến LLM của mỗi request chỉ… |
| 84 | TB | tech | PRD-AI-E2-S2:23 | S2 không làm rõ dữ liệu lương của chính người hỏi có nằm trong phạm vi trả lời không | Bổ sung một AC làm rõ biên giới: 'Phiên bản MVP trả lời về phép, bảng công, trạng thái xin nghỉ của chính người hỏi. Dữ liệu lương (số tiền, bảng lương) KHÔNG n… |
| 85 | TB | product | PRD-AI-E2-S2:45 | Rủi ro NĐ13 được chấp nhận nhưng điều kiện rà soát pháp lý không phải AC — không có cổng kiểm tra trước go-live | Thêm một AC cứng vào S2 (hoặc vào điều kiện hoàn thành E2): 'Trước go-live pilot, có văn bản xác nhận của tư vấn pháp lý rằng việc gửi dữ liệu nhân sự qua API L… |
| 86 | TB | tech | PRD-AI-E2-S3:24 | S3 không có AC cho trường hợp phân hệ Giao việc (PRD-TASK) không phản hồi | Thêm một AC lỗi vào S3: 'Giả sử phân hệ Giao việc không phản hồi khi trợ lý truy vấn, thì trợ lý thông báo rõ ràng bằng tiếng Việt và gợi ý mở trực tiếp màn hìn… |
| 87 | TB | market | PRD-AI-E2-S4:1 | S4 đào tạo nội bộ (should) mở thêm thị trường LMS — phân tán focus và giảm moat AI cốt lõi | Hạ S4 xuống horizon next hoặc later. Tập trung horizon now vào S1 + S2 + S5 (onboarding + hỏi đáp + tra cứu HR) — đây mới là 'AI gắn dữ liệu vận hành' thực sự. … |
| 88 | TB | market | PRD-AI-E2-S4:19 | Fastdo fTrain (đào tạo + kiểm tra + chứng chỉ) đã là module riêng trên thị trường — AI-E2-S4 không tạo được lợi thế cạnh tranh trong mảng LMS | Xem lại lý do giữ S4 (should) trong MVP: nếu trigger mua 'đào tạo nội bộ' chưa kiểm chứng tại pilot thì đẩy S4 xuống horizon next cùng với RESOURCE (kho tài liệ… |
| 89 | TB | craft | PRD-AI-E2-S5:25 | AC 'trợ lý trả lời ngắn gọn' không đo được — không có ngưỡng cụ thể nào để QA pass/fail | Thay 'trả lời ngắn gọn' bằng một tiêu chí đo được, ví dụ: 'trả lời ≤ 3 câu hoặc ≤ 100 từ, kèm liên kết mở đúng màn hình thao tác tương ứng'. PO chốt ngưỡng cụ t… |
| 90 | TB | tech | PRD-AI-E2-S6:24 | AC 'thay đổi áp dụng ngay' khi cập nhật kho tri thức không định nghĩa được 'ngay' là bao lâu | Sửa AC thành: 'Sau khi ORG_ADMIN tải lên/cập nhật/gỡ tài liệu, hệ thống hoàn tất đánh chỉ mục trong tối đa [X phút] và trợ lý dùng phiên bản mới nhất cho mọi câ… |
| 91 | TB | tech | PRD-AI-E2-S6:24 | DEC-59 yêu cầu migrate tài liệu từ cơ chế tạm sang RESOURCE nhưng không có story nào sở hữu việc đó | Tạo một story migration tại PRD-RESOURCE với AC: 'Tài liệu đã tải trực tiếp qua AI-E2-S6 (giai đoạn now) được tự động chuyển sang kho RESOURCE của đúng tổ chức … |
| 92 | TB | tech | PRD-APPROVAL-E1-S2:24 | Luồng phê duyệt lấy cơ cấu tổ chức từ PRD-HR nhưng không có AC kiểm thử khi sơ đồ tổ chức thay đổi trong khi tờ trình đang chờ duyệt | Thêm AC: 'Nếu trong khi tờ trình đang chờ duyệt cấp X, người duyệt cấp X đổi vai trò không còn thẩm quyền → tờ trình gắn cờ CẦN XỬ LÝ và thông báo ORG_ADMIN kèm… |
| 93 | TB | product | PRD-APPROVAL-E1-S3:47 | S3 phụ thuộc 'rà pháp lý trước khi bật' camera ký duyệt nhưng không có dependency hay story theo dõi việc này | Thêm một task pháp lý explicit vào điều kiện DoD của APPROVAL-E1-S3: 'Xác nhận của tư vấn pháp lý rằng vector khuôn mặt dùng cho ký duyệt nằm trong phạm vi cons… |
| 94 | TB | product | PRD-APPROVAL-E1-S4:10 | Nhắc hạn & leo thang (S4) là should trong khi đây là điều kiện cần thiết để lời hứa 'không tờ trình nào mất tích' thành sự thật | Nâng moscow của S4 lên must. Nếu size S và phạm vi đơn giản (nhắc + leo thang theo sơ đồ tổ chức sẵn có), đây không phải gánh nặng build lớn và là điều kiện để … |
| 95 | TB | product | PRD-COMM:82 | COMM ủy thác push notification cho 'hạ tầng thông báo nội bộ chung' nhưng không có PRD hoặc story nào trong toàn spec build hạ tầng đó | Thêm story vào PRD-PLATFORM (hoặc PRD-COMM nếu phù hợp) cho 'Hạ tầng thông báo nội bộ chung' (in-app notification + push FCM/APNs): ai sở hữu, AC tối thiểu (del… |
| 96 | TB | craft | PRD-COMM:82 | PRD-COMM còn nhắc 'SALES...' như một PRD đang hoạt động trong ranh giới DRY | Dòng 82: xoá '...SALES...)'; thay bằng '(TASK-E1-S2, HR...)'. Dòng 106: thay 'việc/đơn/ca' bằng 'việc/ca' — 'đơn' không còn là thực thể trong BoGo v1. |
| 97 | TB | product | PRD-COMM:82 | Thông báo per-event (giao việc, duyệt phép, bảng lương) được uỷ thác cho 'hạ tầng thông báo chung' nhưng PRD-COMM dòng 82 đánh rõ đây KHÔNG thuộc COMM — và không có PRD nào sở hữu hạ tầng này | Thêm một story vào PRD-PLATFORM hoặc tạo epic kỹ thuật riêng: xây hạ tầng push notification xuyên suốt (FCM/APNs cho mobile, WebSocket/SSE cho web) phục vụ mọi … |
| 98 | TB | product | PRD-COMM-E1:18 | EXEC được liệt kê trong personas của E1 và E2 nhưng không có story nào giải quyết job-to-be-done riêng của EXEC trong COMM | Hoặc xoá EXEC khỏi personas COMM nếu thực sự không có story riêng (trung thực về scope), hoặc thêm AC vào E2-S1 cho EXEC broadcast toàn tổ chức với thống kê đọc… |
| 99 | TB | tech | PRD-COMM-E1-S1:30 | AC 'không rơi tin khi mất mạng' không định nghĩa giới hạn queue phía client — thời gian offline dài hoặc nhiều tin gây hành vi không rõ | Thêm AC: (1) Client giữ hàng đợi tin chưa gửi tối thiểu X phút (đề xuất: 2 giờ) hoặc cho đến khi app bị force-quit; (2) Tối đa Y tin trong hàng đợi (đề xuất: 50… |
| 100 | TB | craft | PRD-COMM-E1-S1:53 | Hợp đồng ERP-link vẫn liệt kê 'order→SALES' dù SALES đã bị loại (DEC-45) | Xoá `order` khỏi danh sách `entity_type` ban đầu; cập nhật ví dụ thành `entity_type: shift/task`; bỏ dòng `order→SALES`. Nếu PO có ý định thêm loại thực thể khá… |
| 101 | TB | market | PRD-COMM-E1-S1:29 | Voice message lưu 'suốt vòng đời hội thoại' tạo COGS audio storage không được tính trong mô hình kinh tế đơn vị của BRD | Thêm vào mô hình unit economics của BRD ước tính riêng cho COGS storage (audio + file đính kèm) tách khỏi COGS compute. Hoặc thêm chính sách lưu trữ vào COMM-E1… |
| 102 | TB | tech | PRD-COMM-E1-S2:28 | AC cam kết SLA ≤5 phút cập nhật nhóm hệ thống nhưng ghi chú thiết kế ngay trong story cảnh báo SLA này có thể không đạt nếu HR chạy batch | Tách SLA thành hai AC: (1) Nếu HR phát sự kiện real-time (≤1 phút per DEC-34): COMM cập nhật nhóm trong ≤5 phút sau khi nhận sự kiện — testable khi chạy stub HR… |
| 103 | TB | product | PRD-COMM-E1-S4:10 | S4 (tạo việc từ tin nhắn) là 'must' nhưng phụ thuộc hoàn toàn vào TASK-E1 sẵn sàng — nếu TASK trượt thì 'must' COMM thành stub không dùng được | Tách S4 thành 2 phần: (a) điểm vào UI 'Tạo việc từ tin' — có thể build và ship độc lập (show form, nhập tiêu đề + người nhận); (b) liên kết hai chiều tin↔việc +… |
| 104 | TB | product | PRD-COMM-E1-S5:25 | Poll 'ẩn danh' hệ thống vẫn lưu liên kết người–phiếu — khoảng cách giữa cam kết và thực tế tạo rủi ro niềm tin | Thêm AC: trước khi tạo poll ẩn danh, hiện modal giải thích rõ 'ẩn danh = không ai xem được ai bầu gì; hệ thống chỉ lưu 1 phiếu/người để chặn bầu trùng, không lộ… |
| 105 | TB | tech | PRD-COMM-E1-S5:25 | Poll 'ẩn danh' chỉ được bảo vệ ở lớp giao diện người dùng — không có AC ngăn admin xem liên kết người-phiếu ở tầng dữ liệu | Thêm AC: (1) Không có màn hình nào trong hệ thống (bao gồm admin dashboard của ORG_ADMIN) hiện liên kết người-phiếu cho poll ẩn danh; (2) API không trả về user_… |
| 106 | TB | craft | PRD-COMM-E1-S7:25 | Lỗi đánh máy 'AI gán' trong AC gán màu — đội build đọc thành tính năng AI | Sửa thành 'chạm vào màu thấy ai gán, lúc nào' (chữ thường). |
| 107 | TB | tech | PRD-COMM-E1-S8:24 | Nhắc hẹn lặp (S8) không có AC về idempotency khi server khởi động lại — nguy cơ gửi trùng hoặc bỏ sót | Thêm AC: 'Mỗi lần nhắc hẹn kích hoạt chính xác một lần cho mỗi thời điểm — kể cả khi server khởi động lại; scheduler dùng idempotency key = (reminder_id + sched… |
| 108 | TB | tech | PRD-HR-E1-S1:24 | Không có AC nào về web parity cho toàn cụm HR (DEC-66) — đặc biệt nghiêm trọng với chức năng quản lý | Thêm vào ít nhất 3 story quản lý trọng yếu (PRD-HR-E2-S2, PRD-HR-E1-S6, PRD-HR-E3-S4) một AC web parity theo pattern: 'Mọi chức năng trong story này khả dụng đầ… |
| 109 | TB | product | PRD-HR-E1-S1:50 | Luồng đăng ký khuôn mặt mâu thuẫn: ORG_ADMIN upload ảnh, nhưng NĐ13 yêu cầu chính nhân viên ký đồng ý — không story nào mô tả kịch bản này | Làm rõ luồng chuẩn: ORG_ADMIN tạo hồ sơ trước (không có vector); nhân viên nhận link/thông báo, tự mở app, tự chụp khuôn mặt và ký đồng ý điện tử — SAU ĐÓ mới c… |
| 110 | TB | tech | PRD-HR-E1-S1:24 | AC không định nghĩa hành vi khi nhân viên chưa được phân ca — nút chấm công sẽ làm gì | Thêm AC: 'Nếu nhân viên không có ca nào được phân công cho ngày hiện tại → nút Chấm công vào bị khoá (disabled) kèm thông báo: [Bạn chưa được phân ca hôm nay. L… |
| 111 | TB | tech | PRD-HR-E1-S1:27 | AC 'thông báo lỗi rõ ràng' là untestable — không phân biệt các loại lỗi nhận diện | Tách AC thành 3 trường hợp kiểm thử được: (1) 'Confidence < 50% → hiển thị: Ánh sáng có thể quá tối — hãy di chuyển đến vùng sáng hơn rồi thử lại'; (2) 'Confide… |
| 112 | TB | craft | PRD-HR-E1-S1:40 | User story dùng role name 'giao nhận / xử lý / bán hàng' — đặc ngữ Cleanmatic cũ, không tồn tại trong BoGo | Thay tất cả 'nhân viên giao nhận hoặc nhân viên xử lý' bằng 'nhân viên (STAFF)' trong câu 'Là...'. Trong PRD-HR-E2-S1:40, xoá ví dụ '(giao nhận, xử lý, bán hàng… |
| 113 | TB | tech | PRD-HR-E1-S1:33 | Đồng bộ chấm công offline không có AC xử lý xung đột khi server đã có dữ liệu chấm công khác cho cùng khoảng thời gian (ví dụ: DEPT_MGR chỉnh thủ công trong lúc nhân viên offline) | Thêm AC vào HR-E1-S1 AC offline: 'Khi đồng bộ, nếu server đã có bản ghi chấm công cho cùng nhân viên + cùng ca + cùng khoảng thời gian (chỉnh thủ công): hệ thốn… |
| 114 | TB | craft | PRD-HR-E1-S2:38 | User story dùng 'quản lý hệ thống' thay vì persona chuẩn của spec | Thay 'quản lý hệ thống' bằng 'ORG_ADMIN' ở cả hai story: PRD-HR-E1-S2 dòng 38, PRD-HR-E2-S1 dòng 39. Frontmatter personas của cả hai đã đặt đúng — chỉ cần sửa c… |
| 115 | TB | product | PRD-HR-E1-S6:27 | ORG_ADMIN upload ảnh nhân viên để đăng ký khuôn mặt nhưng NĐ 13/2023 yêu cầu chính chủ thể dữ liệu ký đồng ý — luồng đang vi phạm quyền consent | Sửa luồng đăng ký khuôn mặt thành: (1) ORG_ADMIN tạo hồ sơ nhân viên và gửi link đăng ký sinh trắc cho chính nhân viên đó qua SMS/email; (2) nhân viên tự chụp ả… |
| 116 | TB | craft | PRD-HR-E2:40 | Epic PRD-HR-E2 dẫn link đến PRD-FINANCE đã bị loại khỏi BoGo | Trong PRD-HR-E2:40, xoá dòng 'Liên kết phiếu chi' và thay bằng: 'v1 không chi lương tự động; ORG_ADMIN xuất Excel bảng lương (PRD-HR-E2-S2) để kế toán chi qua n… |
| 117 | TB | product | PRD-HR-E2-S2:31 | Story tạo bảng lương gộp 4 hành vi độc lập vào một story, làm mờ ranh giới nghiệm thu và tăng rủi ro trễ toàn bộ chu trình lương | Tách E2-S2 thành ít nhất 2 story: (A) tạo nháp + approve + xuất Excel (core payroll path); (B) hiệu chỉnh thủ công + khóa đồng thời + cảnh báo tạo lại + gắn cờ … |
| 118 | TB | tech | PRD-HR-E2-S2:24 | Không có AC cho hành vi khi bảng lương được chạy đồng thời hai lần (duplicate run) | Thêm AC: 'Nếu bảng lương kỳ X đã tồn tại (dù là nháp hay đã duyệt) → bấm Tạo bảng lương kỳ X lần nữa sẽ hiển thị cảnh báo: Bảng lương kỳ này đã được tạo. Bạn có… |
| 119 | TB | product | PRD-HR-E2-S2:27 | Bảng lương approve xong không có luồng thông báo/chi lương điện tử — ORG_ADMIN phải tự chuyển khoản từng người qua internet banking | Spec v1 có thể giữ 'không tự chuyển tiền' nhưng cần thêm AC cho ORG_ADMIN xuất file chuẩn định dạng ngân hàng (Vietcombank, MB Bank, BIDV batch payment template… |
| 120 | TB | product | PRD-HR-E2-S4:46 | KPI bonus được nâng lên must trong MVP khi giả định nhu cầu chưa được kiểm chứng và nguồn dữ liệu quá hẹp sau khi SALES/FINANCE bị loại | Hạ E2-S4 xuống moscow: should và thêm điều kiện cổng: chỉ nâng lại must sau khi ít nhất 2 tổ chức pilot xác nhận họ cần KPI-linked bonus tính từ dữ liệu TASK+ch… |
| 121 | TB | tech | PRD-HR-E3-S1:29 | Cân bằng phép (leave balance) bị trừ ngay sau khi approve — không có AC cho trường hợp hủy/từ chối sau khi đã trừ | Thêm AC: 'Nhân viên có thể huỷ yêu cầu nghỉ phép đã được duyệt trong vòng [X giờ trước ngày nghỉ, cấu hình mặc định 24 giờ] → số ngày phép năm được hoàn lại tự … |
| 122 | TB | spine | PRD-PLATFORM-E1-S2:25 | North Star metric chỉ đo được từ phía PLATFORM_ADMIN — ORG_ADMIN không thấy vị trí tổ chức mình trên thang kích hoạt | Tách AC 'ORG_ADMIN thấy tỉ lệ nhân viên dùng hằng tuần so với mốc 60%' ra khỏi AI-E2-S5 (should) và đặt vào PLATFORM-E1-S1 hoặc tạo một widget/widget nhỏ trong … |
| 123 | TB | market | PRD-PLATFORM:40 | PLATFORM_ADMIN chỉ có dashboard mức-dùng (xem) — không có công cụ chủ động can thiệp vào vòng đời tổ chức để đạt G1 | Thêm vào E1 (PLATFORM_ADMIN vòng đời) tối thiểu hai AC: (1) danh sách tổ chức trial sắp xếp theo điểm ưu tiên outreach (dựa trên % activation + ngày còn lại + s… |
| 124 | TB | tech | PRD-PLATFORM-E1-S1:45 | Ghi chú thiết kế của story đã approved vẫn ghi 'là đề xuất — PO chốt khi duyệt PRD' cho hai mốc quan trọng trong AC | PO cần xác nhận rõ ràng: (a) 30 ngày KHOÁ GHI và 60 ngày giữ dữ liệu là đã chốt → xoá câu 'là đề xuất' trong note và ghi lý do chốt vào DEC; hoặc (b) đây thực s… |
| 125 | TB | craft | PRD-PLATFORM-E1-S1:45 | Ghi chú thiết kế của story đã approved vẫn nêu 'đề xuất — PO chốt khi duyệt PRD' cho hai mốc đã nằm trong AC được phê duyệt | Xoá câu 'Các mốc khoá ghi 30 ngày / giữ dữ liệu 60 ngày là đề xuất — PO chốt khi duyệt PRD' khỏi design note. Story đã approved, các mốc đã nằm trong AC được ph… |
| 126 | TB | spine | PRD-PLATFORM-E1-S2:23 | PLATFORM_ADMIN chỉ có công cụ thao tác từng tổ chức một — thiếu công cụ vận hành hàng loạt khi nền tảng có 100 tổ chức | Mở rộng E1-S2 hoặc thêm story mới cho PLATFORM_ADMIN: (1) thông báo hàng loạt theo segment (tổ chức active / trial / sắp hết hạn) với nội dung tùy chỉnh; (2) xu… |
| 127 | TB | tech | PRD-PLATFORM-E2-S1:26 | Pro-rata khi HẠ gói/giảm user chỉ nói 'hiệu lực kỳ kế tiếp, không hoàn tiền' — không có AC cho trường hợp tổ chức giảm user xuống dưới số user đang active | Thêm AC: 'Khi ORG_ADMIN hạ gói hoặc giảm số user xuống thấp hơn số user đang active → hệ thống CẢNH BÁO và yêu cầu ORG_ADMIN chọn tài khoản nào bị vô hiệu hóa; … |
| 128 | TB | tech | PRD-PLATFORM-E2-S2:24 | Lịch nhắc hạn (14/7/3/1 ngày) không có AC xử lý trường hợp tổ chức gia hạn điều kiện +16 ngày (trial 30 ngày) — mốc nhắc đầu tiên có thể trùng hoặc gần ngày đăng ký | Thêm AC vào E2-S2: 'Lịch nhắc hạn (14/7/3/1 ngày) chỉ áp dụng cho GÓI TRẢ PHÍ, không cho giai đoạn trial; trong trial chỉ gửi thông báo gia hạn điều kiện (E1-S1… |
| 129 | TB | tech | PRD-PLATFORM-E2-S4:9 | Story E2-S4 (horizon: next) nằm trong epic E2 (horizon: now) — tạo nhập nhằng về thứ tự build | Hoặc: (a) tách E2-S4 ra epic riêng PRD-PLATFORM-E2b (horizon: next, depends_on PRD-RESOURCE-E1) để ranh giới sprint rõ ràng; hoặc (b) ghi chú DoD của epic E2 rõ… |
| 130 | TB | tech | PRD-PLATFORM-E3-S2:27 | Hợp đồng điện tử treo không có đường leo thang: chỉ gắn cờ PLATFORM_ADMIN nhưng không có AC xử lý hợp đồng chưa ký vô hạn | Thêm AC: 'Hợp đồng chưa ký sau [PO điền, ví dụ 30 ngày]: PLATFORM_ADMIN được phép [PO chọn: (a) tạm dừng tự động sau cảnh báo trước 7 ngày; hoặc (b) chỉ ghi nhậ… |
| 131 | TB | craft | PRD-REPORT:78 | PRD-REPORT dẫn con số '≤ 30 phút hành chính/ngày/hub' như ngưỡng BRD-G2 nhưng con số này không có trong BRD | Sửa dòng 78 thành: '—nối thẳng BRD-G2 (giảm ≥ 50% thời gian xử lý hành chính; con số 30 phút/ngày/hub là ước tính từ DEC, đo tại pilot)' để rõ nguồn gốc con số. |
| 132 | TB | craft | PRD-REPORT:47 | Phần 'Vai trò & ranh giới DRY' của PRD-REPORT liệt kê 5 phân hệ đã bị loại như phân hệ đang hoạt động mà không có cảnh báo | Thêm callout cảnh báo ngay trên section 'Vai trò & ranh giới DRY': '> ⚠️ NỘI DUNG DƯỚI ĐÂY MÔ TẢ PHÂN HỆ CLEANMATIC ĐÃ LOẠI — chỉ giữ làm lịch sử; phân hệ kế nh… |
| 133 | TB | tech | PRD-REPORT-E1-S2:22 | Các story PRD-REPORT (moscow: wont) vẫn chứa AC tham chiếu phân hệ và persona không tồn tại trong BoGo — nếu đọc nhầm sẽ implement sai | Vì toàn bộ cây PRD-REPORT đã được đánh moscow:wont và có banner DEC-48 rõ ràng, không cần sửa nội dung AC — nhưng nên thêm một NOTE đầu mỗi file REPORT (epic và… |
| 134 | TB | craft | PRD-RESOURCE:29 | PRD-RESOURCE frontmatter ghi 'approved' nhưng tiêu đề trạng thái trong thân ghi '🔄 Draft' | Chuẩn hóa về một chỗ: nếu PO đã ký duyệt nội dung spec nhưng chưa build, giữ status: approved và đổi prose thành '✅ Approved — phân hệ v2, horizon next. Build c… |
| 135 | TB | tech | PRD-RESOURCE-E1-S1:26 | Quản lý phiên bản tài liệu không định nghĩa chính sách giữ/xoá lịch sử phiên bản — ảnh hưởng trực tiếp COGS lưu trữ | Thêm AC: 'Chính sách giữ phiên bản cấu hình được theo gói: mặc định giữ N bản gần nhất hoặc trong X tháng (PO chốt N và X khi duyệt sprint); phiên bản ngoài chí… |
| 136 | TB | tech | PRD-RESOURCE-E1-S3:41 | DEC-59 yêu cầu migrate tài liệu từ PRD-AI-E2-S6 vào kho RESOURCE khi v2 ra mắt nhưng không có story nào build công cụ migration này | Tạo story kỹ thuật PRD-RESOURCE-E1-S5 'Migration tài liệu từ AI-E2-S6 sang kho RESOURCE' (size S-M, can-be-should): AC gồm idempotent migration script, xác nhận… |
| 137 | TB | craft | PRD-SUPPORT:70 | Sign-off của PRD-SUPPORT sao chép nguyên văn ghi chú từ PRD-PLATFORM kể cả các open item thanh toán không liên quan | Thay notes của PRD-SUPPORT bằng nội dung phù hợp: 'Giá trị chốt-trước-sprint: nhà cung cấp hạ tầng chat hỗ trợ (dịch vụ thuê ngoài hoặc build — xem E1-S2 design… |
| 138 | TB | tech | PRD-SUPPORT-E1-S1:25 | AI hỗ trợ tuyến đầu phụ thuộc 'kho hướng dẫn chính thức BoGo' nhưng không có story nào build công cụ biên soạn và quản lý kho hướng dẫn đó | Thêm AC vào S1: 'PLATFORM_ADMIN cập nhật được nội dung kho hướng dẫn (thêm/sửa/xoá bài) mà không cần deploy; cập nhật có hiệu lực với AI trong ≤ X giờ'. Hoặc tạ… |
| 139 | TB | product | PRD-SUPPORT-E1-S2:41 | Hạ tầng chat hỗ trợ chưa xác định nhà cung cấp/giải pháp — spec tự nhận biết nhưng không resolve trước go-live now | Trước sprint, PO cùng đội build đánh giá tối thiểu 2–3 giải pháp chat hỗ trợ (ví dụ: Crisp, Chatwoot self-hosted, hoặc tự xây trên COMM infra có rào kỹ) theo ti… |
| 140 | TB | tech | PRD-SUPPORT-E1-S2:41 | Hạ tầng chat hỗ trợ được ghi nhận là 'hạng mục riêng chưa spec' ngay trong ghi chú thiết kế của story M | Trước sprint: (1) PO quyết build hay thuê ngoài hạ tầng chat; (2) nếu thuê ngoài — thêm AC 'tiêu chí nhà cung cấp (latency, data residency VN, giá/phiên, SLA up… |
| 141 | TB | craft | PRD-SUPPORT-E1-S2:26 | Giá trị SLA '≤ 15 phút' ghi là 'đề xuất, PO chốt' ngay trong AC đã approved — không kiểm được | PO quyết định một con số hoặc để trống và ghi rõ 'TBD — chốt trước sprint'. Cách viết AC: 'Phản hồi đầu tiên của người hỗ trợ trong ≤ [X] phút giờ hành chính (8… |
| 142 | TB | tech | PRD-SUPPORT-E1-S2:41 | Hạ tầng chat hỗ trợ (SUPPORT) không được phép dùng COMM — nhưng spec không xác định hạ tầng thay thế cụ thể là gì, ai sở hữu, và thời điểm phải chốt trước sprint | Thêm AC kỹ thuật tối thiểu: 'Hạ tầng chat hỗ trợ phải: (1) tách biệt hoàn toàn với PRD-COMM để không vi phạm ranh giới tenant; (2) hỗ trợ gửi text + ảnh đính kè… |
| 143 | TB | product | PRD-TASK-E1-S3:24 | Story công việc định kỳ có mức độ phức tạp kỹ thuật nặng cho một story moscow:should trong MVP | Tách E1-S3 thành hai phần rõ ràng có AC riêng và cột milestone riêng: (1) lập mẫu + tạo công việc từ mẫu (đơn giản, đủ dùng); (2) job chống trùng + bù kỳ lỡ. Ph… |
| 144 | TB | tech | PRD-TASK-E1-S3:29 | Task bù kỳ lỡ khi hệ thống phục hồi không nêu rõ có gửi thông báo không | Thêm một clause vào AC dòng 29: "Task bù kỳ lỡ tạo ra KHÔNG gửi push notification tới người nhận (vì task đã quá hạn khi tạo); hệ thống chỉ ghi log và hiển thị … |
| 145 | TB | product | PRD-TASK-E3-S2:29 | KPI công việc được tham chiếu vào thưởng lương nhưng rủi ro cốt lõi (nhân viên gian lận trạng thái) chưa được đặt ra | Thêm ghi chú thiết kế cảnh báo rõ rằng KPI công việc chỉ đáng tin khi tỉ lệ công việc 'cần duyệt' đủ cao (khuyến nghị DEPT_MGR bật cần-duyệt cho các công việc q… |
| 146 | TB | tech | PRD-TASK-E4-S1:27 | Yêu cầu bảo mật "tuyệt đối không hiển thị dữ liệu tổ chức khác" không có AC kiểm thử ở tầng dashboard | Thêm một AC kiểm thử ranh giới đa tổ chức dành riêng cho dashboard: "Khi người dùng Tổ chức A mở dashboard, toàn bộ chỉ số nhân sự và công việc trả về đều thuộc… |
| 147 | TB | product | PRD-TASK-E4-S3:24 | E4-S3 (danh mục báo cáo) giải quyết bài toán điều hướng thay vì bài toán thông tin — gold-plating MVP | Đánh moscow:wont cho E4-S3 trong MVP. Đưa vào horizon next khi số phân hệ có báo cáo tăng lên (APPROVAL, RESOURCE). Trong MVP, mỗi phân hệ tự có link báo cáo là… |
| 148 | TB | tech | PRD-TASK-E4-S3:24 | Danh mục báo cáo tham chiếu "báo cáo của phân hệ Nhân sự" nhưng HR không có story định nghĩa danh sách báo cáo của mình | Thêm AC vào PRD-HR-E1-S4 (hoặc HR story phù hợp): "HR expose danh sách báo cáo chuẩn gồm: [liệt kê cụ thể, vd: Bảng chấm công theo kỳ, Bảng lương theo kỳ, v.v.]… |
| 149 | TB | product | PRD-TASK-E4-S5:25 | E4-S5 ngầm đưa hạ tầng email transactional vào MVP mà không có story nào trong PRD khác đặt nền | Bổ sung phụ thuộc (depends_on) của E4-S5 vào một story hoặc task hạ tầng email transactional. Nếu PRD-PLATFORM chưa có story này, tạo story hạ tầng email ở PRD-… |
| 150 | THẤP | market | BRD:176 | Tanca mô hình one-time purchase tạo JTBD khác với subscription — segment 'tránh subscription dài hạn' chưa được nhận diện trong trigger mua | Tại pilot, khảo sát thêm câu hỏi: 'Điều gì khiến bạn chần chừ khi trả 89k/user/tháng?' — nếu 'ngại subscription' xuất hiện nhiều thì xem xét thêm tùy chọn trả n… |
| 151 | THẤP | product | PRD-AI-E1-S1:20 | 7 story E1 giữ `scope: in` dù `moscow: wont` — tín hiệu xây dựng mâu thuẫn | Đổi `scope: out` (hoặc `scope: wont`) cho tất cả 7 story E1 và epic E1 để khớp với `moscow: wont`. Thêm comment ngắn trong epic E1 giải thích đây là lịch sử Cle… |
| 152 | THẤP | craft | PRD-AI-E1-S1:35 | User story E1-S1 (wont/lịch sử) có prose body đặt tên Cleanmatic như sản phẩm còn hiệu lực | Thêm một dòng chú thích đầu phần ## User Story: `> 📦 Lịch sử Cleanmatic — story này đã wont (DEC-47). Không áp dụng cho BoGo.` Không cần sửa prose body. |
| 153 | THẤP | tech | PRD-AI-E2-S4:26 | AC chấm tự động S4 không định nghĩa hành vi khi nhân viên nộp bài sau deadline hoặc muốn làm lại | Thêm điều kiện biên vào AC3: 'Hệ thống ghi nhận lần làm bài đầu tiên là kết quả chính thức; nếu bài đã đóng (hết hạn do người tạo thiết lập) thì không cho nộp t… |
| 154 | THẤP | product | PRD-COMM-E1-S1:29 | Các story COMM dùng framing mobile-first; DEC-66 yêu cầu web parity nhưng không có AC nào trong COMM verify web equivalent cho voice message và typing indicator | Thêm một AC vào S1 và S9: 'Trên web, voice message có đường thay thế tương đương (ví dụ: upload file âm thanh, hoặc record qua browser API nếu hỗ trợ); typing i… |
| 155 | THẤP | craft | PRD-COMM-E1-S2:25 | Hai AC còn dùng 'hiện lỗi rõ ràng' mà không định nghĩa nội dung lỗi | Cụ thể hoá: ví dụ 'hiện thông báo lỗi inline bên dưới nút gửi, nội dung: "Bạn chỉ được gửi thông báo trong phạm vi [tên phòng/tổ chức của bạn]"' — một câu mẫu đ… |
| 156 | THẤP | craft | PRD-HR-E1-S1:27 | 'Thông báo lỗi rõ ràng' trong AC chấm công không đủ điều kiện để kiểm thử | Viết lại: 'Thông báo lỗi phải nêu rõ lý do bằng tiếng Việt, vd: "Khuôn mặt không nhận diện được — vui lòng hướng về ánh sáng và thử lại" hoặc "Bạn đang ở ngoài … |
| 157 | THẤP | craft | PRD-HR-E1-S1:41 | User story body dùng job title Cleanmatic ('nhân viên giao nhận', 'nhân viên xử lý') không tồn tại trong BoGo | Sửa thành 'Là nhân viên (STAFF) làm việc tại địa điểm của tổ chức,' để khớp persona BoGo. |
| 158 | THẤP | product | PRD-HR-E1-S3:31 | AC expose endpoint cho ERP-link COMM được nhúng vào story phân công ca làm việc, che khuất mục tiêu chính của story | Chuyển AC endpoint này ra khỏi thân story E1-S3, đặt vào phần 'Ghi chú thiết kế' hoặc tạo một integration-contract riêng dưới dạng ghi chú kỹ thuật. Story E1-S3… |
| 159 | THẤP | craft | PRD-HR-E2:37 | Phạm vi epic PRD-HR-E2 ghi 'nửa tháng hoặc tháng' mâu thuẫn với quyết định đã chốt 'chỉ tháng' | Sửa dòng 37 của PRD-HR-E2: thay 'nửa tháng hoặc tháng' bằng 'theo THÁNG (v1 chỉ hỗ trợ kỳ tháng — xem PRD-HR-E2-S1 AC4)'. |
| 160 | THẤP | tech | PRD-HR-E2-S1:50 | Design note vẫn tham chiếu PRD-FINANCE-E3 (đã loại) làm nơi cấu hình hoa hồng | Sửa design note: xoá tham chiếu PRD-FINANCE-E3 và ghi rõ quyết định: 'Thưởng hoa hồng theo doanh thu không có trong v1 (phân hệ SALES/FINANCE đã loại — DEC-45).… |
| 161 | THẤP | tech | PRD-HR-E2-S1:50 | Ghi chú thiết kế HR-E2-S1 vẫn tham chiếu 'PRD-FINANCE-E3' (đã loại) là nơi cấu hình hoa hồng — chưa có AC cập nhật | Cập nhật ghi chú thiết kế: thay 'cấu hình riêng tại PRD-FINANCE-E3' bằng 'cấu hình hoa hồng nằm ngoài phạm vi v1 (PRD-FINANCE đã loại — DEC-45); nếu cần hoa hồn… |
| 162 | THẤP | craft | PRD-HR-E3-S4:39 | Mục tiêu '2 giờ' trong câu 'Để...' không có AC kiểm chứng tương ứng | Thêm AC: 'Nếu yêu cầu chờ duyệt quá X giờ (cấu hình, gợi ý 2 giờ), hệ thống gửi nhắc nhở tự động cho DEPT_MGR.' Hoặc xoá khỏi câu Để và đưa vào chỉ số thành côn… |
| 163 | THẤP | tech | PRD-PLATFORM-E1-S1:24 | Story E1-S1 kích thước L có 8 AC bao phủ 4 mối quan tâm khác nhau — khó estimate và khó debug khi xảy ra lỗi | Tách thành 2 story nhỏ hơn: (a) E1-S1a: Đăng ký, OTP, provisioning multi-tenant nguyên tử, anti-abuse — core signup (AC 1,2,5,8); (b) E1-S1b: Trial lifecycle — … |
| 164 | THẤP | spine | PRD-REPORT:8 | PRD-REPORT vẫn ghi owner 'Cleanmatic' — dấu hiệu pivot DEC-45 chưa được dọn dẹp hoàn toàn | Cập nhật PRD-REPORT: owner → 'Nhóm sản phẩm BoGo', approved_by → 'Product Owner (đại diện nhóm sản phẩm BoGo)' (giữ note DEC-45/DEC-48 trong body). Một dòng sửa… |
| 165 | THẤP | product | PRD-REPORT-E1-S1:18 | STAFF được liệt kê là persona của các story dashboard/báo cáo gộp chéo — sai JTBD | Nếu REPORT được tái sinh cho BoGo, xoá STAFF khỏi personas của E1 và E2. Persona đúng là EXEC (bức tranh toàn cảnh theo thời gian thực — khớp VISION:76) và DEPT… |
| 166 | THẤP | tech | PRD-RESOURCE-E1-S2:25 | Story xem kanban tài liệu (S2) ghép 3 tính năng độc lập vào một story M — khó tách sprint nếu cần cắt scope | Ghi nhận trong spec rằng ba yêu cầu này đến từ DEC-56 (chỉ đạo trực tiếp PO) và không tách được vì PO đã xác nhận cả ba là must. Hoặc nếu muốn giữ tính negotiab… |
| 167 | THẤP | product | PRD-RESOURCE-E1-S4:10 | Bình luận trên tài liệu (S4) là should — ưu tiên phù hợp, nhưng cần rõ ràng về giá trị khi kho có thể rỗng | Không cần thay đổi moscow của S4. Nhưng PO nên xác định rõ: cơ chế kéo nào sẽ giúp kho không rỗng trước khi bắt đầu build S3/S4 — nếu chỉ dựa vào 'tài liệu đính… |
| 168 | THẤP | craft | PRD-SUPPORT-E1:52 | Mô tả phạm vi epic dùng 'chuyển tiếp thông minh' — tính từ không đo được | Thay 'chuyển tiếp thông minh' bằng 'chuyển tiếp kèm ngữ cảnh khi AI không giải được' — mô tả đúng cơ chế đã spec ở AC S1. |
| 169 | THẤP | tech | PRD-SUPPORT-E1-S2:26 | SLA phản hồi '≤ 15 phút giờ hành chính' được đánh dấu là đề xuất chưa PO chốt — không thể viết test nghiệm thu | PO chốt con số SLA trước khi story vào sprint: thay 'đề xuất' bằng giá trị xác định, ví dụ '≤ 15 phút'. Đây là thông số có thể đo được bằng timestamp phiên — th… |
| 170 | THẤP | product | PRD-TASK-E4:20 | E4 (dashboard tổng quan) đặt trong PRD-TASK nhưng phụ thuộc nặng vào dữ liệu PRD-HR — ranh giới sở hữu sản phẩm mờ | Ghi rõ trong E4 header hoặc ghi chú thiết kế E4-S1: contract dữ liệu HR mà E4 phụ thuộc (endpoint tổng hợp chấm công theo phòng ban) do PRD-HR sở hữu và maintai… |
| 171 | THẤP | tech | PRD-TASK-E4-S5:27 | E4-S5 tuyên bố "tái dùng hạ tầng lập lịch của E1-S3" nhưng hai use case có điều kiện timeout/retry khác nhau chưa được reconcile | Làm rõ trong ghi chú thiết kế E4-S5: "Tái dùng PATTERN (idempotent job per period) — không nhất thiết cùng code module; nếu đội build chọn share job runner thì … |