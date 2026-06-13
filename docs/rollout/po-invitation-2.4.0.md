# Mời nâng cấp lên bản 2.4.0 — bạn mở khoá được gì

> **Bản nháp thông điệp gửi PO.** Chủ kit rà lại giọng văn rồi gửi.

Chào bạn,

Bản kit product-spec đã có phiên **2.4.0**. Bạn đang dùng một bản cũ hơn, và việc nâng cấp
mở khoá một loạt năng lực mà bản của bạn còn thiếu. Nâng cấp chạy **một lệnh** (`upgrade.sh`,
mặc định *xem trước* không đổi gì) và có sẵn đường lùi (`--rollback`). Mình sẽ đồng hành.

## Lên 2.4.0, bạn có thêm:

1. **Hành động theo bản phê bình (apply-critique).** Đi qua một báo cáo phê bình spec theo
   từng phát hiện — Giữ / Đổi (kèm re-approve) / Hoãn — mỗi quyết định ghi lại một mục, không
   tự sửa câu chữ của bạn.

2. **Hồ sơ sở thích + kế thừa (fingerprint/inherit).** Skill nhớ cách bạn muốn được hỗ trợ
   (ngôn ngữ, độ "thách thức", giọng) và áp dụng nhất quán qua các tài liệu con.

3. **Quan trắc sử dụng & sức khoẻ (telemetry).** Thấy được skill nào hay dùng, script nào lỗi
   hoặc chậm, validate có đang đạt theo thời gian — dữ liệu nằm cục bộ trên máy bạn.

4. **Học từ thực tế (--learn).** Sau khi ra mắt: ghi kết quả thật so với mục tiêu, hoặc nạp
   phản hồi thô → gợi ý vấn đề mới. Một mục tiêu "trượt" được nêu ra, không bao giờ tự sửa.

5. **Giấy phép đi kèm đúng chuẩn (LICENSE).** Bản phân phối mang theo giấy phép AGPL-3.0 + mã
   nguồn như giấy phép yêu cầu (xem [notice license](license-notice-agpl-draft.md)).

6. **Bản gửi bạn gọn hơn.** Bộ cài cho người nhận không còn kèm bộ test/đồ phát triển nội bộ —
   chỉ phần chạy thật + giấy phép.

7. **Tinh chỉnh từ kiểm toán thực tế (mới ở 2.4.0).** Bản 2.4.0 gộp thêm một loạt sửa từ đợt
   field-audit: `--validate` cảnh báo thêm khi mốc thời gian của một mảng lệch với PRD của nó,
   và khi một persona được nêu tên ở đầu tài liệu nhưng chưa được mô tả; một công cụ điền lại
   `id:` còn thiếu (chạy thử trước, không bao giờ tự đụng tài liệu đã duyệt); tra cứu quyết định
   theo tài liệu bị ảnh hưởng kèm chuỗi "quyết định này thay thế quyết định kia"; và phần trực
   quan thông minh hơn (link `*-latest.html` luôn trỏ sơ đồ mới nhất, cờ "sơ đồ đã cũ", dọn bớt
   bản render cũ).

Ngoài ra: một dòng nhắc nhẹ trong `--status` cho biết bản bạn đang chạy **đóng gói bao lâu rồi**
(để biết khi nào nên hỏi bản mới), nhắc xuất bản tài liệu sau khi ký duyệt để dễ chia sẻ, và một
GitHub Action tuỳ chọn tự kiểm spec trên CI.

## Cách nâng cấp (an toàn, có đường lùi)

1. Sao lưu `docs/product/` + commit/stash thay đổi đang mở.
2. `bash upgrade.sh` — **xem trước** kế hoạch, không đổi gì.
3. Rà kế hoạch cùng mình → `bash upgrade.sh --apply`.
4. Nếu cần: `bash upgrade.sh --rollback`.

Mình sẽ cùng bạn chạy bước đầu. Khi nào bạn sẵn sàng?
