---
id: PRD-EVENTS-E1-S3
type: story
epic: PRD-EVENTS-E1
status: draft
lang: vi
owner: Trần Bảo Hiếu
version: 0.1.0
created: 2026-06-02
updated: 2026-06-02
personas: [P-URBAN, P-PROVINCE, P-RETURNEE]
scope: out
moscow: could
size: L
horizon: later
metrics: [mau-monthly]
acceptance_criteria:
  - "Khi người dùng mở mục 'Concert toàn quốc', hệ thống hiển thị danh sách các đêm nhạc do Ghép Đôi Việt tổ chức theo từng thành phố, kèm nghệ sĩ biểu diễn, ngày giờ và hạng vé."
  - "Khi người dùng chọn một concert còn vé, hệ thống cho phép đặt tối đa 4 vé một lần và giữ chỗ tạm thời trong 10 phút trước khi xác nhận."
  - "Sau khi đặt vé thành công, người dùng nhận vé điện tử kèm mã QR check-in và lịch nhắc trước đêm diễn 24 giờ."
  - "Khi một concert đã bán hết vé ở mọi hạng, mục concert đó hiển thị nhãn 'cháy vé' và nút đặt vé bị vô hiệu hoá."
  - "Người dùng có thể lọc danh sách concert theo thành phố và theo thể loại nhạc (pop, indie, EDM, nhạc trẻ)."
---

# Đặt vé concert âm nhạc toàn quốc — Story PRD-EVENTS-E1-S3

## User Story | Câu chuyện người dùng

**As a** | **Với vai trò** người dùng Ghép Đôi Việt yêu âm nhạc (P-URBAN / P-PROVINCE / P-RETURNEE)
**I want** | **Tôi muốn** khám phá và đặt vé các đêm nhạc concert toàn quốc do app tổ chức
**so that** | **để** tôi vừa đi xem nhạc vừa có cơ hội gặp gỡ những người dùng khác ngoài đời.

## Acceptance Criteria | Tiêu chí chấp nhận

- Khi người dùng mở mục "Concert toàn quốc", hệ thống hiển thị danh sách các đêm nhạc do Ghép Đôi Việt tổ chức theo từng thành phố, kèm nghệ sĩ biểu diễn, ngày giờ và hạng vé.
- Khi người dùng chọn một concert còn vé, hệ thống cho phép đặt tối đa 4 vé một lần và giữ chỗ tạm thời trong 10 phút trước khi xác nhận.
- Sau khi đặt vé thành công, người dùng nhận vé điện tử kèm mã QR check-in và lịch nhắc trước đêm diễn 24 giờ.
- Khi một concert đã bán hết vé ở mọi hạng, mục concert đó hiển thị nhãn "cháy vé" và nút đặt vé bị vô hiệu hoá.
- Người dùng có thể lọc danh sách concert theo thành phố và theo thể loại nhạc (pop, indie, EDM, nhạc trẻ).

## Lưu ý lệch trọng tâm (gold-plating, ghi nhận để cân nhắc)

Story này đẩy PRD-EVENTS đi xa hơn nữa khỏi north-star: tổ chức và bán vé **concert âm nhạc toàn quốc**
bên trong một app hẹn hò là một mảng kinh doanh sự kiện giải trí riêng — vận hành nghệ sĩ, bán vé, an
ninh đám đông — không hề đo "số cặp đôi duy trì nhắn tin qua lại >= 7 ngày". Đây là solution-first ở mức
nghiêm trọng hơn cả việc giữ chỗ gặp mặt. Story được giữ `scope: out`, `moscow: could`, `horizon: later`
để ghi nhận tầm nhìn mà không kéo nguồn lực khỏi lõi kết nối; quyết định triển khai (nếu có) cần PO cân
nhắc rõ ràng so với north-star trước.
