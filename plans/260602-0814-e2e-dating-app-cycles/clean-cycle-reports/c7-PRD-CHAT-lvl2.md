# Critique: PRD-CHAT  ·  level 2  ·  lăng kính: craft  [thiếu: product, tech, market]

> Bảng đếm mức độ: blocker 0 · major 2 · minor 1

## Top 3: sửa ngay

1. **[major][craft] PRD-CHAT-E1-S4:425-427** — Hai AC hứa "an toàn tuyệt đối" và "bảo vệ hoàn toàn", nhưng tuyệt đối so với cái gì thì không ai nói. An toàn không có điểm tuyệt đối. Đội build đọc xong mỗi người chọn một hướng hiểu, ship thiếu, rồi lỗi an toàn lộ ra lúc người dùng thật đã chịu trận. Sửa bằng cách liệt kê hành vi cụ thể: "Người A gửi URL lạ thì hệ thống cảnh báo người B trước khi click. Người A gửi hơn 50 tin một phút thì tạm khóa A một giờ và báo quản trị viên." Hoặc thu tiêu đề về "Bảo vệ người dùng khỏi lừa đảo và spam" để hạ phạm vi từ "toàn bộ" xuống loại mối nguy cụ thể.

2. **[major][craft] PRD-CHAT-E1-S3:362,386** — Tiêu đề "Trải nghiệm nhắn tin mượt mà" và AC đầu "trải nghiệm phải mượt mà" lặp y nguyên một cụm. Người đọc thấy AC đầu trùng tiêu đề thì coi như lời nhắc lại, bỏ qua luôn. Đội build không còn thước đo "mượt mà" nên làm theo cảm giác. Thay AC đầu bằng tiêu chí đo được: "Khi người dùng vừa cuộn vừa gõ phím thì FPS phải từ 50 trở lên." Hoặc đổi tiêu đề thành "Nhắn tin gõ phím không lag" để nó khác hẳn AC.

3. **[minor][craft] PRD-CHAT-E1-S3:386** — "cuộl" sai chính tả, phải là "cuộn", lỗi có ở cả AC lẫn body. Một lỗi gõ kéo tụt niềm tin vào cả spec. Khi đội build copy AC này vào thẻ việc, lỗi phơi ra công khai. Sửa "cuộl" thành "cuộn" ở cả hai chỗ.

## Theo lăng kính

### Craft

- **[major] PRD-CHAT-E1-S4:425-427** — Hai AC xài cụm "an toàn tuyệt đối" và "bảo vệ hoàn toàn": hứa trạng thái tuyệt đối thay vì chỉ rõ hành vi nào cần bảo vệ. Đội build không biết mục tiêu là chặn spam, chặn lừa đảo, hay chặn tấn công, nên mỗi người chọn một hướng, ship không trọn, lỗi lộ ra khi đã chạm người dùng thật. Liệt kê hành vi an toàn cụ thể kèm ví dụ (URL lạ thì cảnh báo trước khi click, gửi quá 50 tin một phút thì tạm khóa và báo quản trị), hoặc thu tiêu đề về "Bảo vệ người dùng khỏi lừa đảo và spam".

- **[major] PRD-CHAT-E1-S3:362,386** — Tiêu đề và AC đầu trùng nguyên cụm "mượt mà", vi phạm tiêu chí Consistent của CSI-4Cs. AC đọc như lời nhắc lại tiêu đề chứ không phải tiêu chí, mất hết giá trị thông tin. Đội build không có thước đo "mượt mà" nên xây theo cảm tính. Thay AC đầu bằng ngưỡng FPS từ 50 trở lên khi vừa cuộn vừa gõ, hoặc đổi tiêu đề thành "Nhắn tin gõ phím không lag".

- **[minor] PRD-CHAT-E1-S3:386** — "cuộl" là lỗi gõ của "cuộn", có ở cả AC lẫn body story. Một lỗi chính tả kéo tụt độ tin vào cả spec, lộ ra khi AC được copy vào thẻ việc. Sửa thành "cuộn" ở cả hai vị trí.

### Product

Lăng kính này không chạy lần này.

### Market

Lăng kính này không chạy lần này.

### Tech

Lăng kính này không chạy lần này.

## Lặp lại từ lần trước

Không có. Các lần critique trước (c6 ở level 3) nhắm PRD-CHAT ở chỗ khác hẳn: thứ tự horizon đẩy chat ra sau (PRD-CHAT:303), AC1 cam kết "trong 2 giây khi đang online" mà không định nghĩa "đang online" (PRD-CHAT-E1-S1:781), từ "đứt quãng" mơ hồ trong risk (body:308-312). Ba lỗi craft lần này ở S3/S4 (lặp tiêu đề, tính từ tuyệt đối, lỗi gõ "cuộl") chưa từng bị nêu.

## Đáng ghi thành quyết định (DEC-worthy)

Không có. Ba finding lần này thuần chất lượng câu chữ AC, không kéo theo ruling scope hay positioning nào. Ruling positioning về thứ tự horizon CHAT vs MATCH đã được nêu ở c6 và vẫn còn treo, nhưng nằm ngoài phạm vi lần consolidate này (chỉ có lăng kính craft).

---
Lưu ý: chỉ có lăng kính craft trả về kết quả; ba lăng kính product, tech, market vắng mặt nên bản critique này chỉ phủ một góc (chất lượng câu chữ AC), chưa đụng tới giá trị sản phẩm, khả thi kỹ thuật hay thị trường.
