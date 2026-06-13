# Đối chiếu phê bình BoGo — bản cũ (4 vòng) vs vòng này

*Ngày: 2026-06-13 · Mục đích: xác định blocker nào đã ĐÓNG, còn MỞ, hay MỚI — gộp 4 bản critique trước (`docs/product/critique/`, 10–11/06) với 171 phát hiện vòng này.*

> **Đọc trong 20 giây.** Tin tốt: **PO đóng vòng critique rất tốt — ~70% blocker của các vòng trước đã được sửa qua DEC chỉ trong 1 ngày** (giá, offline, trial, ký số, mã hoá, reply/voice Zalo…). Phần còn lại bám dai chỉ là **GAP-ORG** (cần hẳn epic mới nên khó) cộng **3 lỗ "đường ống" dễ sửa nhưng cứ bị hoãn**: AC khi AI/LLM lỗi, công cụ kiểm soát chi phí AI, và chủ sở hữu hạ tầng thông báo. Vòng này thêm một lớp lỗ MỚI mà 4 vòng cũ chưa chạm (cô lập dữ liệu đa tổ chức, ký webhook, chargeback, gian lận giờ chấm công…).
>
> ⚠️ **Đính chính:** mục §5 của báo cáo chính (`deep-multilens-critique-...`) viết "vòng khắc phục chưa đóng" là **quá bi quan** — đối chiếu thực tế cho thấy vòng khắc phục CÓ chạy và chạy tốt. Bản này thay thế phần đánh giá đó.

---

## 1. Bức tranh tổng quát

| | Số lượng | Ghi chú |
|---|---|---|
| Phát hiện trích từ 4 bản cũ | 105 (16 blocker · 60 cao · 29 TB) | |
| Blocker cũ (gộp trùng) | ~13 vấn đề riêng | |
| ✅ Đã đóng hẳn | **9** | sửa qua DEC-53/54/55/57/60/62/69 |
| 🟡 Đóng một phần | **2** | GAP-ORG, PLATFORM_ADMIN |
| 🔴 Còn mở (lặp lại) | **2** + 3 high dai dẳng | AC lỗi LLM, dashboard chi phí AI, hạ tầng thông báo, owner GTM, dồn 33-must |

**Kết luận:** spec đang đi đúng hướng. Quy trình "phê bình → DEC → sửa story" của PO hoạt động. Việc còn lại không phải "PO lười sửa" mà là (a) một khoảng trống cấu trúc lớn cần quyết định mở epic (GAP-ORG), và (b) vài AC hạ tầng nhỏ dễ rơi khỏi tầm mắt.

---

## 2. Bảng đối chiếu 16 BLOCKER cũ → trạng thái hôm nay

| # | Blocker (vòng cũ) | Trạng thái | Bằng chứng / DEC |
|---|-------------------|-----------|------------------|
| 1 | GAP-ORG: tự đăng ký + dựng sơ đồ phòng ban + nhập NV hàng loạt | 🟡 **Đóng một phần** | Tự đăng ký ĐÃ có (`PRD-PLATFORM-E1-S1`); **dựng phòng ban + nhập hàng loạt VẪN thiếu** → blocker B1 báo cáo này |
| 2 | Không có giá / mô hình doanh thu | ✅ **Đã đóng** | BRD §Mô hình doanh thu, 89k (DEC-54/55) |
| 3 | Chấm công offline không có AC | ✅ **Đã đóng** *(nảy vấn đề mới)* | `HR-E1-S1:33` AC offline (DEC-53). MỚI: gian lận timestamp thiết bị (C7) |
| 4 | PLATFORM_ADMIN persona giả | 🟡 **Đóng một phần** | PLATFORM có E1/E2/E3, 8 story vòng đời/billing; **công cụ chủ động (at-risk, can thiệp) vẫn thiếu** |
| 5 | AI thiếu AC khi LLM lỗi/timeout | 🔴 **Còn mở** | `AI-E2-S1` vẫn không có AC timeout/fallback (kiểm tra: rỗng) → C7 |
| 6 | Trial 14 ngày vs kỳ lương tháng | ✅ **Đã đóng** | `PLATFORM-E1-S1:27` gia hạn có điều kiện lên 30 ngày = trọn kỳ lương (DEC-55) |
| 7 | Cụm an toàn tiền PLATFORM (webhook/race/thuế/eContract) | ✅ **Đóng phần lõi**, 🔴 **2 hở mới** | `E2-S3:27/29/30` polling + idempotent + đối soát tay; `E3-S2:25` ký HAI bên (Luật GDĐT 2023). MỚI: **chưa xác thực chữ ký webhook (HMAC)** + **chưa xử lý chargeback** → C7/B6 |
| 8 | Neo giá sai tầng (89k vs 1Office) | ✅ **Đã đóng** | `BRD:176` so "đúng tầng" 1Office all-in vs module, Fiine, fCheckin (DEC-55) |
| 9 | Hai cửa nạp tài liệu AI (S6 vs RESOURCE) | ✅ **Đã đóng** | `RESOURCE-E1-S3:25` định tuyến qua `AI-E2-S6` (nguồn duy nhất) |
| 10 | RESOURCE mã hoá vs xem trước mâu thuẫn | ✅ **Đã đóng** | `RESOURCE-E1-S1:31` phiên giải mã hẹp, không ghi plaintext |
| 11 | Gộp 2 phân hệ v2 vào giá phẳng | ✅ **Đã đóng** | DEC-60/62: RESOURCE/APPROVAL bán add-on, không gộp 89k |
| 12 | Phạm vi hash chữ ký không rõ | ✅ **Đã đóng** | `APPROVAL-E1-S3:28` hash phủ cả chữ LẪN tệp đính kèm |
| 13–16 | COMM thiếu reply/quote + voice message | ✅ **Đã đóng** *(nảy vấn đề mới)* | `COMM-E1-S1:28,29` + `S2:27` (DEC-69). MỚI: trần lưu trữ voice/media (C7) |

> **Điểm sáng quy trình:** mỗi mục "Đã đóng" đều gắn với một DEC ghi rõ — PO không sửa lén, mà ra quyết định có truy vết (đúng tinh thần GATE-NO-SILENT-REVERSAL). Đây là điều nên giữ.

---

## 3. Phát hiện cao (high) còn mở — đã xác minh

Không kiểm từng cái trong 60 high cũ (artifact trùng nhau nhiều, trùng artifact ≠ cùng lỗi). Đã xác minh các high *lặp lại* quan trọng nhất:

| Vấn đề cũ | Bản nêu | Trạng thái | Bằng chứng |
|-----------|---------|-----------|------------|
| Dashboard/quota chi phí LLM (S6) không có AC | R1, R2 | 🔴 **Còn mở** | `AI-E2-S6` chỉ có ngưỡng tự tin + kill switch, **không có AC chi phí/quota** |
| Hạ tầng thông báo chung không ai sở hữu | R3 | 🔴 **Còn mở** | Không story push/notification trong PLATFORM (kiểm tra: rỗng) → C5 |
| GTM không có owner/ngân sách | R1, R2 | 🔴 **Còn mở** | `BRD:183` vẫn ghi "đề xuất — gán owner khi vận hành" → C3 |
| 33 must dồn vào horizon "now" | R2 | 🔴 **Còn mở** | Chưa có phân đợt sprint trong "now" → C/§3 báo cáo chính |

> Còn lại ~56 high + 29 medium cũ: **chưa đối chiếu từng cái** (xem §6 hạn chế). Vì tỉ lệ blocker đã đóng cao, không nên mặc định chúng còn mở — cần một bước rà từng mục nếu PO muốn con số chính xác.

---

## 4. Phát hiện MỚI vòng này (không có trong 4 bản cũ) — giá trị gia tăng

Đây là lớp mà phương pháp sâu hơn (kỹ thuật NFR + phản biện + đối chiếu phiên bản) mang lại:

| Mức | Phát hiện mới | Vị trí |
|-----|---------------|--------|
| 🔴 Chặn | Hợp đồng ERP-link còn trỏ `order→SALES` (phân hệ đã xoá) | `PRD-COMM-E1-S1:53` |
| 🔴 Chặn | Không có lối tổ chức tự rời đi / xuất dữ liệu / chuyển quyền admin | `PRD-PLATFORM-E1-S1:30` |
| 🔴 Chặn | Moat task↔ca làm chỉ spec một phía (HR không nhận sự kiện) | `PRD-TASK-E1-S2:26` |
| 🔴 Chặn | Chargeback/hoàn tiền sau gạch nợ không có AC | `PRD-PLATFORM-E2-S3:28` |
| 🟠 Cao | Tìm kiếm toàn văn không cô lập theo tổ chức (rủi ro rò chéo) | `PRD-COMM-E3-S1:28` |
| 🟠 Cao | Webhook thanh toán không xác thực chữ ký HMAC | `PRD-PLATFORM-E2-S3:25` |
| 🟠 Cao | Gian lận giờ chấm công offline (timestamp thiết bị) | `PRD-HR-E1-S1:33` |
| 🟠 Cao | Tanca có gói FREE vĩnh viễn — phân khúc nhỏ nhất bị mất | `BRD:147` |
| 🟠 Cao | Dư âm Cleanmatic trong cụm REPORT (approved + brand cũ) | `PRD-REPORT:8` |
| 🟠 Cao | Hạ tầng email transactional không story nào sở hữu | `PRD-TASK-E4-S5:25` |
| 🟠 Cao | Quy trình báo cáo vi phạm dữ liệu NĐ13 (72h) không ai sở hữu | `BRD:204` |
| 🟠 Cao | Khảo sát baseline G2 (giảm 50%) không story nào định nghĩa | `BRD:117` |
| 🟠 Cao | EXEC (người ký ngân sách) gần như không được phục vụ | `PRD-TASK-E1:18`, `PRD-AI-E2-S3:45` |

*(Danh sách đầy đủ ở báo cáo chính, Phụ lục B.)*

---

## 5. Việc còn lại để "đóng nốt" (gộp từ cũ + mới)

**Ưu tiên P0 — mở/sửa ngay:**
1. **GAP-ORG** (cũ #1, một phần): mở epic "Quản trị cơ cấu tổ chức" (dựng phòng ban + nhập NV hàng loạt). Đây là blocker dai dẳng nhất.
2. **AC lỗi LLM** (cũ #5): thêm AC timeout/fallback cho `AI-E2-S1/S2/S3` — dễ, đã nêu 2 lần.
3. **Kiểm soát chi phí AI** (cũ, high): thêm AC dashboard + quota/throttle vào `AI-E2-S6`.
4. **Hạ tầng thông báo** (cũ R3): tạo story tech-enabler trong PLATFORM, gán `depends_on`.
5. **2 hở tiền mới**: xác thực chữ ký webhook + AC chargeback (`PLATFORM-E2-S3`).

**P1:**
6. GTM owner (cũ): gán owner+ngân sách+KPI ≥1 kênh.
7. Cô lập tìm kiếm đa tổ chức + dư âm Cleanmatic + email infra + NĐ13 breach + baseline G2 (mới).
8. Phân đợt 33-must trong "now" (cũ).

---

## 6. Hạn chế & câu hỏi chưa giải đáp
1. **Chưa đối chiếu từng cái 56 high + 29 medium cũ.** Chỉ verify blocker + các high lặp lại trọng yếu. Trùng artifact không kết luận được "cùng lỗi". Nếu PO cần con số đóng/mở chính xác cho toàn bộ, cần một vòng rà từng mục (có thể tự động hoá một phần).
2. **Một số "đã đóng" có thể đẻ vấn đề mới** (như #3 offline → gian lận timestamp; #13-16 voice → trần lưu trữ). "Đóng" nghĩa là lỗ cũ hết, không phải khu vực đó hoàn hảo.
3. **Đề xuất quy trình:** gắn mỗi blocker của báo cáo chính với một DEC hoặc story ID ngay bây giờ, để vòng critique sau chỉ cần kiểm trạng thái DEC thay vì phê bình lại từ đầu — PO đã làm tốt việc này với 4 vòng trước, chỉ cần tiếp tục.

---

*Nguồn: 4 bản cũ tại `bogo-product-spec/docs/product/critique/`; phát hiện vòng này tại `plans/260613-1436-bogo-spec-deep-critique/findings/` + báo cáo chính `plans/reports/deep-multilens-critique-260613-1436-bogo-product-spec-report.md`.*
