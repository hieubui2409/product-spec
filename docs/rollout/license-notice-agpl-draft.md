# Notice license AGPL-3.0 + release-notes (BẢN NHÁP)

> ⚠️ **DRAFT — CẦN CHỦ KIT RÀ PHÁP LÝ TRƯỚC KHI GỬI/CÔNG BỐ.**
> Văn bản dưới đây do skill soạn dựa trên file `LICENSE` (AGPL-3.0) sẵn có trong repo.
> Nó **không phải tư vấn pháp lý**. Chủ kit xác nhận câu chữ + hiệu lực hồi tố trước khi
> đính kèm gói nâng cấp hoặc đưa vào `CHANGELOG.md`.

## 1. Notice gửi kèm gói nâng cấp

Bộ kit này (`product-spec` và các skill đi kèm) được cấp phép theo **GNU Affero General
Public License v3.0 (AGPL-3.0)** — xem file `LICENSE` ở gốc bundle.

AGPL-3.0 yêu cầu: bất kỳ bản **phân phối** nào của phần mềm đều phải kèm theo giấy phép và
**mã nguồn tương ứng**; nếu bạn chỉnh sửa và cung cấp cho người khác (kể cả qua mạng), bạn
phải cung cấp mã nguồn bản đã sửa theo cùng giấy phép.

Từ bản **2.2.1** trở đi, mỗi bundle phân phối mang sẵn `LICENSE` + mã nguồn trong gói (đúng
yêu cầu AGPL-3.0). **Các bản phân phối trước 2.2.1** có thể đã được gửi mà **thiếu file
`LICENSE` đi kèm**; điều đó *không* đổi việc phần mềm vẫn ở giấy phép AGPL-3.0. Gói nâng cấp
2.4.0 đưa `LICENSE` (và mã nguồn) vào cây cài của bạn để bản bạn đang giữ tuân thủ đầy đủ.

*(Chủ kit: xác nhận cách diễn đạt "hiệu lực với bản trước 2.2.1" cho đúng ý định cấp phép.)*

## 2. Đoạn release-notes (để chủ kit dán vào `[Unreleased]` của `CHANGELOG.md` lúc tag 2.4.0)

> **Lưu ý**: KHÔNG tự sửa heading version trong `CHANGELOG.md` ở phiên này. Lúc phát hành,
> chủ kit dán đoạn dưới vào mục `## [Unreleased]` rồi chạy `release.py --release 2.4.0 --apply`
> (lệnh này tự khoá `[Unreleased]` → `[2.4.0]` + bump `pack.manifest.yaml`).

```markdown
### Licensing
- The bundle is licensed under AGPL-3.0; from 2.2.1 onward every distributed bundle
  carries `LICENSE` + corresponding source. Bundles distributed before 2.2.1 may have
  shipped without the `LICENSE` file — this does not change their AGPL-3.0 status. The
  2.4.0 upgrade pack adds `LICENSE` (and source) into the installed tree so an existing
  copy is fully compliant.
```

## 3. Bàn giao

- [ ] Chủ kit rà pháp lý mục 1 + 2 (đặc biệt câu "hiệu lực với bản trước 2.2.1").
- [ ] Đính mục 1 kèm [thông điệp mời PO](po-invitation-2.4.0.md).
- [ ] Dán mục 2 vào `CHANGELOG.md` `[Unreleased]` khi phát hành 2.4.0.
