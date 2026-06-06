# Change Log — Sổ Quỹ | Nhật ký thay đổi

Append-only. Mỗi thay đổi cấu trúc spec được ghi một mục ở đây.

---

## 2026-06-06 — rename | đổi tên

- **Artifact | Tài liệu:** PRODUCT, VISION
- **Action | Hành động:** refined
- **Reason | Lý do:** PO đổi tên sản phẩm từ tên tạm "Quỹ Chung" → **"Sổ Quỹ"** (nhấn ẩn dụ 'cuốn sổ minh bạch', mở rộng được sang mọi nhóm).
- **Affected downstream | Ảnh hưởng phía dưới:** PRODUCT.md (name + heading), vision.md (heading + prose).
- **Author | Tác giả:** hieubt

---

## 2026-06-06 — init | khởi tạo

- **Artifact | Tài liệu:** PRODUCT, VISION (docs/product/PRODUCT.md, docs/product/vision.md)
- **Action | Hành động:** created
- **Reason | Lý do:** Khởi tạo sản phẩm Quỹ Chung — app mobile quản lý quỹ chung minh bạch cho người ở ghép (mô hình QUỸ/pot).
- **Affected downstream | Ảnh hưởng phía dưới:** PRODUCT.md, vision.md
- **Author | Tác giả:** hieubt

**Detail | Chi tiết:**

Vision interview V1–V7 hoàn tất: persona chính roommate; mô hình lõi QUỸ chung; north-star = số GD quỹ/tháng; giai đoạn Ý tưởng; deployment mobile.

---

## 2026-06-06 — created (BRD) | tạo BRD

- **Artifact | Tài liệu:** BRD (BRD-G1..G4), competitors COMP-SPLITWISE/MONEYLOVER/MANUAL, 4 risks (docs/product/brd.md)
- **Action | Hành động:** created
- **Reason | Lý do:** Hoàn tất tầng kinh doanh: 4 mục tiêu đo được (acquisition/retention/usage/virality), mô hình free/tăng-trưởng-trước, ràng buộc (ngân sách/thời gian/chỉ-mobile/bảo-mật), 3 đối thủ + 4 rủi ro.
- **Affected downstream | Ảnh hưởng phía dưới:** Chưa có PRD — 4 goal đang là orphan (warn, sẽ hết khi tạo PRD).
- **Author | Tác giả:** hieubt

**Detail | Chi tiết:**

Mục tiêu: G1 10.000 nhóm/12th (stretch) · G2 D30 ≥50% · G3 ≥8 GD quỹ/nhóm/th · G4 ≥3 thành viên/nhóm. Ràng buộc cứng: giai đoạn đầu KHÔNG giữ tiền thật (chỉ ghi sổ). Validate: 0 error, 4 warn (orphan_brd_goal).

---

## 2026-06-06 — created (PRD-FUND) | tạo PRD-FUND

- **Artifact | Tài liệu:** PRD-FUND "Quỹ phòng cốt lõi" (docs/product/prds/fund.md)
- **Action | Hành động:** created
- **Reason | Lý do:** PRD đầu tiên — mảng lõi mô hình QUỸ. scope_intent=mvp, scope=core-value, horizon=now, đẩy BRD-G1/G2/G3.
- **Affected downstream | Ảnh hưởng phía dưới:** Chưa có epic/story (unaddressed_parent — bước kế là decompose).
- **Author | Tác giả:** hieubt

**Detail | Chi tiết:**

MoSCoW: 5 MUST (tạo quỹ, ghi nộp, ghi chi, xem số dư, xem lịch sử) · 2 SHOULD (sửa/xóa, ghi chú) · 2 COULD (ảnh hóa đơn, phân loại) · 3 WON'T (hạn mức, nhắc đóng, xuất file). NFR: bảo mật, bản địa hóa VN, tin cậy số liệu, nhanh/nhẹ. Parity: Splitwise=ahead, Money Lover=none, Zalo+CK=ahead. Out-of-scope: giữ tiền thật/thanh toán, tạo nhóm (→PRD-GROUP), chia P2P. Validate: 0 error, 2 warn.

---

## 2026-06-06 — created (epics + stories) | tạo epic + story

- **Artifact | Tài liệu:** PRD-FUND-E1/E2/E3 + 5 story MUST (PRD-FUND-E1-S1, E2-S1, E2-S2, E3-S1, E3-S2)
- **Action | Hành động:** created
- **Reason | Lý do:** Decompose PRD-FUND (mvp) thành 3 epic (Thiết lập quỹ · Ghi giao dịch · Theo dõi quỹ) và 5 story MUST kèm AC (Given-When-Then).
- **Affected downstream | Ảnh hưởng phía dưới:** unaddressed_parent của PRD-FUND đã hết. Còn 1 warn duy nhất: orphan_brd_goal BRD-G4 (chờ PRD-GROUP).
- **Author | Tác giả:** hieubt

**Detail | Chi tiết:**

Mỗi story 2–3 AC dạng Cho/Khi/Thì. Open question ghi ở E2-S2: chính sách chi vượt số dư (quỹ âm/tạm ứng?) — cần PO quyết trước sign-off. Cây spec: 15 node, validate structural 0 error / 1 warn.

---

## 2026-06-06 — validated | kiểm định

- **Artifact | Tài liệu:** toàn spec (15 node)
- **Action | Hành động:** validated
- **Reason | Lý do:** --validate đầy đủ (structural scripts + LLM judgment).
- **Author | Tác giả:** hieubt

**Detail | Chi tiết:**

Structural: 0 error, 1 warn (orphan_brd_goal BRD-G4). LLM: INVEST 5/5 story PASS; core-value aligned; không gold-plating; không trùng lặp; không mâu thuẫn (chưa có artifact approved). 2 cảnh báo mơ hồ (NFR "nhanh/nhẹ" chưa lượng hóa; AC E3-S2 "rõ ràng" lỏng). Memory pass: contradiction→none, slip→none, memory_gap→validate_no_marker đã ghi marker.
