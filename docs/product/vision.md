---
id: VISION
type: vision
status: draft
lang: vi
owner: TBD
version: 0.1.0
created: 2026-06-06
updated: 2026-06-06
personas: ["roommate", "fund-keeper", "long-term-group", "trip-group"]
---
<!--
Note: vision.md intentionally omits `horizon`. The horizon enum (now/next/later)
describes WHEN work happens; vision is timeless strategy. Roadmap horizon lives
on PRDs/epics/stories. Keeping `horizon: TBD` here meant a fresh init
always landed `horizon: TBD` which fails the closed-enum check.
-->

# Vision — Sổ Quỹ | Tầm nhìn

## Problem Narrative | Câu chuyện vấn đề

Người ở ghép sống chung bằng tiền chung: điện, nước, internet, gas, giấy vệ sinh, nước rửa chén, đồ dùng phòng bếp — hàng chục khoản nhỏ mỗi tháng mà ai cũng phải gánh một phần. Hiện tại cách quản lý phổ biến nhất là một người đứng ra thu tiền rồi ghi vào một file Excel, một cuốn sổ tay, hoặc tệ hơn là nhớ trong đầu. Cách này hỏng ở ba điểm: (1) chỉ một người thấy được sổ, cả phòng còn lại phải tin lời người giữ quỹ; (2) khi có thắc mắc "tháng này tiền quỹ tiêu vào đâu mà hết nhanh thế", không ai tra cứu được nhanh; (3) người giữ quỹ bị áp lực vì luôn có nguy cơ bị nghi ngờ, dù họ trung thực.

Gốc rễ không phải là phép tính — cộng trừ thì Excel làm được. Gốc rễ là **minh bạch**: ai cũng cần thấy cùng một con số, cùng một lịch sử, ngay lập tức, mà không phải đi hỏi người giữ quỹ. Khi tiền chung mà thông tin lại không chung, lòng tin trong phòng bị bào mòn từng tháng.

Sổ Quỹ giải quyết đúng điểm đó: biến cuốn sổ quỹ của một người thành cuốn sổ quỹ của cả nhóm. Mọi khoản nộp vào và chi ra đều hiện ngay theo thời gian thực; ai cũng mở app lên là thấy số dư hiện tại và toàn bộ lịch sử thu chi. Người giữ quỹ thoát khỏi áp lực bị nghi ngờ; các thành viên thoát khỏi cảnh phải tin mù quáng.

## Personas | Nhóm người dùng

- **roommate** — *Thành viên ở ghép* (persona chính, phục vụ trước). Người trẻ (sinh viên, đi làm) thuê trọ hoặc ở ghép dài hạn, mỗi tháng cùng góp một khoản cho các chi phí sinh hoạt chung. Họ không phải người giữ quỹ, nhưng là người "phải tin" — và chính họ chịu thiệt khi thiếu minh bạch. Cái họ cần: mở app là thấy ngay mình đã nộp đủ chưa, quỹ còn bao nhiêu, tháng này tiêu vào những gì. Dùng mobile gần như tuyệt đối.
- **fund-keeper** — *Trưởng nhóm / người giữ quỹ*. Người đứng ra thu tiền và chi tiêu từ quỹ chung. Đây là "người mua" thực sự của sản phẩm: họ chịu trách nhiệm minh bạch và mệt mỏi vì luôn có thể bị nghi ngờ. Công cụ tốt giúp họ chứng minh sự trung thực mà không phải giải trình thủ công — và chính họ là người kéo cả phòng vào app.
- **long-term-group** — *Hội nhóm dài hạn* (ưu tiên sau persona chính). CLB, đội nhóm, gia đình góp quỹ định kỳ cho một mục đích chung (quỹ lớp, quỹ đội bóng, quỹ gia đình). Mô hình quỹ giống hệt phòng trọ nhưng quy mô thành viên lớn hơn, tần suất giao dịch thường thấp hơn.
- **trip-group** — *Nhóm bạn đi chơi* (ưu tiên thấp nhất). Nhóm du lịch/ăn nhậu ngắn hạn, gom tiền theo chuyến rồi giải tán. Lưu ý: nhóm này gần như không có "quỹ chung tồn tại liên tục", nên lệch với mô hình lõi QUỸ; giữ trong tầm nhìn dài hạn nhưng không định hình sản phẩm giai đoạn đầu.

## Value Proposition | Đề xuất giá trị

Đối với người ở ghép, Sổ Quỹ là cuốn sổ quỹ chung minh bạch duy nhất thay được Excel/ghi tay: mọi khoản nộp và chi đều hiện ngay theo thời gian thực, ai cũng xem được số dư và toàn bộ lịch sử — không còn cảnh một người ôm sổ còn cả phòng phải tin lời.

## North-Star | Sao Bắc Đẩu

Số giao dịch ghi vào quỹ mỗi tháng (nộp quỹ + chi từ quỹ). Đây là thước đo lượng sử dụng thực tế của tính năng cốt lõi: một nhóm thật sự dùng app để quản lý quỹ sẽ tạo giao dịch đều đặn; một nhóm bỏ app sẽ về 0. Đo trực tiếp giá trị lõi (minh bạch quỹ), không bị nhiễu bởi các tính năng phụ.

## 1–3 Year Direction | Hướng đi 1–3 năm

Năm 1: trở thành cuốn sổ quỹ chung mặc định cho người ở trọ Việt Nam — bản địa hóa sâu (tiếng Việt, khái niệm 'quỹ phòng' quen thuộc, VietQR). Năm 2–3: mở rộng từ phòng trọ sang mọi loại nhóm góp quỹ (CLB, đội nhóm, gia đình), và tiến tới tích hợp thanh toán (VietQR/chuyển khoản) để nộp và chi quỹ diễn ra ngay trong app — biến Sổ Quỹ từ 'cuốn sổ minh bạch' thành 'ví quỹ nhóm' thực thụ.






