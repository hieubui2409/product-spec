# Báo cáo rà soát mã nguồn harness product-spec v2.4.0

**Ngày:** 2026-06-13 · **Phạm vi:** toàn bộ 4 skill của bộ công cụ (KHÔNG phải spec bogo) ·
**Đối tượng đọc:** PO sở hữu bộ công cụ (viết ngôn ngữ dễ hiểu, hạn chế thuật ngữ)

> Đây là lần quét bạn yêu cầu: không chỉ soi spec bogo, mà soi **chính bộ công cụ v2.4.0** để tìm
> lỗi, lỗ hổng, chỗ làm dở, chỗ trùng lặp. Báo cáo này là kết quả đó.

---

## 1. Tóm tắt nhanh (đọc cái này là đủ nắm)

Tôi đã quét **121 file mã (~22.600 dòng) + 117 file kiểm thử** trên 4 skill: `product-spec` (lớn nhất,
~14.900 dòng), `product-spec-critique`, `release`, `telemetry`.

**Điều quan trọng nhất:** bộ công cụ về cơ bản **lành mạnh**. Không có lỗi nào làm hỏng dữ liệu spec,
không có lỗ hổng bảo mật, không có cổng an toàn (GATE) nào bị thủng. Cả 4 bộ kiểm thử đều xanh **trừ
đúng 1 test đang đỏ** ngay lúc này.

| Mức độ | Số lượng | Ý nghĩa |
|--------|---------|---------|
| 🔴 Nghiêm trọng (blocker) | **0** | Không có gì làm hỏng dữ liệu / thủng cổng an toàn / hỏng lệnh cho mọi người |
| 🟠 Cao (high) | **2** | 1 test đang ĐỎ + 1 lời hứa "chạy không cần cài đặt" bị một file phá vỡ |
| 🟡 Trung bình (medium) | **11** | Lỗi tình huống hiếm, trùng lặp dễ trôi dạt, chỗ làm chưa kín |
| ⚪ Thấp (low) | **8** | Mã chết, thiếu timeout, lệch ranh giới nhỏ, thiếu 1 test |

**Hai việc đáng làm sớm:**
1. Sửa test telemetry đang đỏ (`test_lens_artifact_heat`) — và sửa luôn **nguyên nhân gốc mang tính hệ
   thống**: cả họ "lens" của telemetry đọc đồng hồ thật `datetime.now()` mà không cho tiêm giờ giả → không
   test được chính xác, sớm muộn cũng rớt (xem §5).
2. Sửa `lens_workflow_chains.py` đang `import yaml` — vi phạm cam kết "chạy bằng python hệ thống, không cần
   cài thêm gì" mà telemetry/SKILL.md ghi rõ. Máy người nhận không có PyYAML sẽ lỗi khi chạy `--lens workflow`.

**Một điểm trung thực quan trọng:** đợt quét tự động đề xuất 35 phát hiện. Sau khi **tôi tự kiểm chứng lại
từng cái nặng nhất bằng cách đọc mã thật**, tôi đã **loại 3 phát hiện sai** (kể cả cái duy nhất được gắn nhãn
"nghiêm trọng") và **hạ mức 5 cái khác**. Chi tiết ở §6 — phần này quan trọng vì nó cho thấy bộ công cụ
*kín hơn* so với báo cáo thô tưởng.

---

## 2. Cách tôi quét (ngắn gọn)

- **Lớp tất định (tôi tự chạy):** liệt kê toàn bộ file theo cây thật (không tin MANIFEST), chạy cả 4 bộ test,
  và grep các mẫu lỗi hay gặp (đồng hồ thật trong test, `eval`/`shell=True`, nuốt lỗi, đối số mặc định nguy hiểm…).
- **Lớp phán đoán (workflow nhiều tác nhân, chạy song song tối đa 3):** chia mã thành 11 cụm; mỗi cụm có 1 tác
  nhân *soi lỗi* rồi 1 tác nhân *phản biện* (mặc định hoài nghi, cố bác bỏ phát hiện). Sau đó 4 tác nhân *soi
  độ hoàn chỉnh* theo từng skill (so SKILL.md với mã thật: có hứa mà thiếu? có viết mà không ai đọc?).
- **Lớp kiểm chứng của tôi (controller):** với mọi phát hiện mức cao/nghiêm trọng, tôi **tự mở file đọc lại**
  trước khi đưa vào báo cáo. Đây là lý do 3 phát hiện sai bị loại — không thể đưa cáo buộc chưa kiểm chứng vào
  báo cáo về chính công cụ của bạn.

---

## 3. 🟠 Mức CAO (2)

### H-1. Một test telemetry đang ĐỎ ngay bây giờ — và đó là triệu chứng của một vấn đề hệ thống
- **File:** `telemetry/scripts/tests/test_lens_artifact_heat.py:91` (test `test_heat_lens_respects_days_window`)
  + gốc rễ ở `telemetry/scripts/lens_artifact_heat.py:46`.
- **Chuyện gì:** test cố định mốc thời gian sự kiện là `2026-06-12T10:00:00`, rồi hỏi "trong 1 ngày gần nhất có
  nó không?". Nhưng mã tính mốc cắt bằng `datetime.now() - 1 ngày`. Hôm nay đã là 2026-06-13, nên sự kiện rơi ra
  **ngoài** cửa sổ → test **thất bại thật sự** (`assert 'docs/product/NEW.md' in []`).
- **Vì sao đáng quan tâm:** một test đỏ trong skill đã phát hành làm xói mòn niềm tin vào cả bộ test và sẽ làm
  đỏ CI. Quan trọng hơn: đây không phải lỗi lẻ — xem §5.
- **Cách sửa:** cho `gather()` nhận tham số giờ (`now=None`, mặc định `datetime.now(timezone.utc)`); trong test
  tiêm một mốc giờ cố định. Đây đúng là cách mà `product-spec` và `release` **đã làm ở mọi nơi khác** (xem §5).

### H-2. `lens_workflow_chains.py` nhập thư viện ngoài (PyYAML) — phá vỡ cam kết "không cần cài đặt"
- **File:** `telemetry/scripts/lens_workflow_chains.py:22` (`import yaml`).
- **Chuyện gì:** `telemetry/SKILL.md:36` và `:47` ghi rõ *"scripts are stdlib-only — no venv needed"* / *"chạy
  bằng python hệ thống, máy người nhận không cần cài venv"*. Nhưng đúng **1 file** trong 17 file telemetry lại
  `import yaml` (PyYAML — KHÔNG thuộc thư viện chuẩn), không có phương án dự phòng.
- **Vì sao đáng quan tâm:** trên máy người nhận chỉ có python hệ thống (không PyYAML), chạy `--lens workflow`
  (hoặc `--lens all`) sẽ **lỗi `ImportError`** — đúng kiểu lỗi "ship ra mới biết hỏng". 16 file còn lại sạch sẽ,
  nên đây là chỗ hỏng đơn lẻ, dễ vá.
- **Cách sửa:** thay `yaml.safe_load()` bằng một bộ đọc YAML tối giản dùng thư viện chuẩn — **mẫu này đã có sẵn**
  trong `lens_memory_health.py` (tự viết parser frontmatter). Chỉ cần đọc khóa `chains:` (danh sách của danh sách).

---

## 4. 🟡 Mức TRUNG BÌNH (11)

| # | File:dòng | Vấn đề | Vì sao | Cách sửa |
|---|-----------|--------|--------|----------|
| M-1 | `release/scripts/release.py:80` | `bump_version()` vỡ với phiên bản có hậu tố `+build.123` (vốn hợp lệ theo chính `SEMVER_RE` của bạn). `int("3+build")` → lỗi. | `--bump` sẽ sập nếu PO dùng build-metadata. Hiếm gặp nên xếp trung bình. | Tách cả `+` lẫn `-`: `version.split("+")[0].split("-")[0].split(".")`. |
| M-2 | `product-spec-critique/scripts/critique_inherit.py:151` | So sánh mốc thời gian theo kiểu chữ-cái trong khi nguồn mốc có thể trộn 2 định dạng (rút từ tên file vs ISO) → dedup có thể giữ phát hiện **cũ** thay vì mới. | Trạng thái critique bị "đọng" finding cũ. *(Cần đọc lại `critique_persist._report_ts` xác nhận 2 định dạng thật sự cùng xuất hiện trước khi sửa.)* | Chuẩn hóa mọi mốc về ISO 8601 trong `_report_ts()`, hoặc parse rồi so theo thời gian thật. |
| M-3 | `product-spec-critique/scripts/check_report_language.py:106` | Khớp chuỗi-con thay vì khớp-từ: một từ tiếng Việt đứng ngoài ngoặc bị nhầm là "đang trong ngoặc" nếu nó là chuỗi con của một cụm trong ngoặc. | Bộ kiểm tra "độ thuần ngôn ngữ" của báo cáo critique báo nhầm (false positive). | Đổi sang khớp theo ranh giới từ / so vị trí (offset) của từ với các vùng trong ngoặc. |
| M-4 | `release/scripts/verify_skill_versions.py:65` | `yaml.safe_load()` không bọc try/except. SKILL.md có YAML hỏng → ném ngoại lệ, **sập cả cổng CI** verify với traceback khó hiểu. | Kết quả vẫn là "release fail" (đúng), nhưng người dùng chỉ thấy traceback thay vì lỗi rõ ràng → khó sửa. | Bọc try/except `yaml.YAMLError`, trả lỗi dạng "YAML hỏng ở file X: …". |
| M-5 | `release/scripts/upgrade_apply.py:243` | Đường `rollback()` gọi `json.loads()` không bắt lỗi; `except` ở dòng 269 chỉ bắt `FileNotFoundError/OSError`, không bắt JSON hỏng. | Nếu file backup hỏng, **chính đường khôi phục lại sập** → kẹt: upgrade lỗi mà rollback cũng lỗi. | Thêm `json.JSONDecodeError` vào `except`, báo lỗi rõ để PO biết file backup nào hỏng. |
| M-6 | `product-spec/scripts/change_log_writer.py:42` | Regex ngày lỏng (`\d{4}-\d{2}-\d{2}`) chấp nhận ngày vô lý như `2026-13-32`. | Tạo ra file tháng méo (`2026-13.md`), bộ đọc audit-trail sau này có thể bỏ sót/đọc sai. | Dùng `datetime.fromisoformat()` trong try/except để xác thực ngày thật (giống `status.py:193`). |
| M-7 | `product-spec/scripts/preferences.py:216` | `save()` chỉ kiểm các khóa enum; 2 khóa kiểu số thực (`outcome_hit_floor`, `outcome_partial_floor`) không được kiểm khi gọi `save()` trực tiếp từ mã (không qua CLI). | Mã khác gọi `save()` có thể ghi giá trị số vô lý (vd 1.5) mà không cảnh báo. | Kiểm `isinstance(v, float) and 0<=v<=1` ngay trong `save()`, hoặc ghi rõ "save() yêu cầu giá trị đã kiểm". |
| M-8 | `telemetry/scripts/` (6 file) + `generate_templates.py:211`, `record_outcome.py:246` | Hàm `_parse_ts()` chép lặp **6 lần** y hệt trong các lens; và họ lens dùng đồng hồ thật không tiêm được (xem §5). | Sửa 1 lỗi múi giờ phải sửa 6 chỗ → dễ quên, dễ trôi dạt. | Gom `parse_ts()` về 1 file chung (vd `telemetry_paths.py`), các lens import dùng chung. |
| M-9 | `change_log_writer.py`, các `migrate_*.py` | Không gọi `fs_guard` dù có ghi vào `docs/product/`. Hiện **an toàn** vì đường dẫn cứng, nhưng lệch chuẩn so với phần còn lại. | Rủi ro hồi quy: mai mốt ai thêm đường dẫn do người dùng nhập mà quên rào chắn. | Thêm `assert_under_docs_product(...)` trước khi ghi, hoặc ghi chú "đường dẫn cứng, không cần rào". |
| M-10 | `telemetry/SKILL.md` (argument-hint) | Lens `artifact_heat` **đã cài và chạy được** nhưng **không** được liệt kê trong danh sách lens hợp lệ của SKILL.md. | Người dùng không biết lens này tồn tại; tài liệu lệch với thực tế. | Thêm `artifact_heat` vào argument-hint và bảng Lenses. |
| M-11 | `render_ascii.py` vs `render_ascii_board.py` | 3 hàm `_is_deferred/_inline/_mark` định nghĩa trùng ở 2 file. | Sửa 1 nơi quên nơi kia → 2 chỗ hiển thị khác nhau. (Lịch sử: `_hashable` từng bị vậy và đã gom về `render_common`.) | Gom vào `render_common.py`, import lại từ 2 nơi. |

---

## 5. 🔎 Phát hiện hệ thống (giá trị nhất — vượt khỏi từng file lẻ)

**Cả họ "lens" của telemetry đọc đồng hồ thật mà không cho tiêm giờ giả.** 9 chỗ dùng
`datetime.now(timezone.utc) - timedelta(days=days)` nhưng hàm `gather(days=...)` **không** có tham số giờ:
`lens_reliability.py:31`, `lens_artifact_heat.py:46`, `lens_usage_tokens.py:38,65`, `lens_validate_proxy.py:57`,
`lens_memory_health.py:68`, `lens_product_memory.py:37`, `lens_workflow_chains.py:50`, `harvester.py:58`.

Hệ quả: **không test được chính xác ranh giới cửa sổ ngày**. Bằng chứng là các test khác né bằng cách dùng
`days=BIG` (cửa sổ khổng lồ) → **ranh giới gần như không được test**; còn test duy nhất chịu test ranh giới
(`test_lens_artifact_heat`) thì cố định ngày → **đang rớt** (H-1).

Đối chiếu: `product-spec` và `release` **làm đúng ở mọi nơi** — tiêm được giờ: `status.build_status(..., today=)`,
`record_outcome --measured-on`, `time_advisory.py:76` / `time_realism_anchors.py:108` (`args.today or date.today()`),
và `upgrade_apply.py:127` còn ghi chú thẳng *"NEVER call datetime.now() here — caller injects for determinism"*.

→ **Đề xuất một lần sửa gốc:** thêm tham số `now`/`today` (mặc định = đồng hồ thật) cho `gather()` của các lens,
truyền vào phép tính mốc cắt. Vừa hết test rớt, vừa kín lỗ hổng test ranh giới, vừa đồng bộ với phần còn lại.
`generate_templates.py:211` cũng thuộc nhóm này (thiếu `--today`).

---

## 6. ✅ Đã soi kỹ nhưng KHÔNG phải lỗi (phần trung thực)

### 6a. Tôi đã LOẠI 3 phát hiện sai (tự đọc mã kiểm chứng)

- **"Không có script ghi metadata phê duyệt" (bị gắn nhãn *nghiêm trọng*)** → **SAI.** Việc ghi `status: approved`
  vào frontmatter là **cố ý do LLM tự sửa**, được hướng dẫn rõ tại `workflow-validate.md:264`. Bản thân
  `generate_templates.py:245` còn **từ chối** tạo artifact ở trạng thái `approved`. Đây là thiết kế (script lo
  cấu trúc, LLM lo phê duyệt/phán đoán), không phải thiếu sót. → hạ xuống mức **thấp** (xem 6b).
- **"Thiếu file `workflow-approve.md`"** → **SAI.** Quy trình `--approve` nằm trong `workflow-validate.md` (tiêu
  đề file là *"Validate / Approve / Summary"*). Không thiếu, chỉ là không có file riêng cùng tên.
- **"`migrate_metric_to_metrics` thiếu cổng cho artifact đã phê duyệt → vi phạm GATE"** → **SAI.** Mã **có rào
  cứng**: `:235-242` từ chối `--apply` trừ khi có **cả** `--confirmed-by <PO>` **và** `--date <ISO>`. Nó chỉ xử
  lý đúng 1 file (brd.md) nên 2 cờ toàn cục **chính là** sự xác nhận cho artifact đó — tương đương cơ chế
  allowlist của `migrate_backfill_ids`, chỉ khác cách làm vì phạm vi 1 file.

### 6b. Một lớp phát hiện hiểu nhầm "ranh giới script ↔ LLM" (ghi nhận, không phải lỗi)

Đợt quét tự động báo vài chỗ kiểu *"script Python không cưỡng chế bước phỏng vấn/phê duyệt"*. Nhưng các bước đó
(hỏi PO qua `AskUserQuestion`) **về bản chất do LLM điều phối, không thể nằm trong script Python**:
- không có `record_approval.py` (LLM tự ghi frontmatter phê duyệt — đúng thiết kế);
- `release.py` không cưỡng chế "phỏng vấn trước `--apply`";
- `pack/cli.py` không tự chạy phỏng vấn tương tác khi gọi không cờ.

**Dư địa hợp lệ duy nhất (mức thấp):** các cổng này chỉ dựa vào kỷ luật của LLM, **không có chốt chặn tất định**
nếu ai đó gọi thẳng script từ dòng lệnh. Nếu muốn chắc ăn, có thể thêm một dấu xác nhận nhẹ (vd biến môi trường
`PO_INTERVIEWED=1` mà LLM set sau khi hỏi xong). Không bắt buộc.

---

## 7. ⚪ Mức THẤP (8) — gộp ngắn

- `check_consistency_product.py:206` — regex `_SEP_RE` biên dịch nhưng không dùng (mã chết).
- `upgrade_planner.py:18` — import `field` thừa.
- `status_vcs.py:51,67` — gọi `git` qua subprocess không đặt `timeout` → có thể treo nếu git/NFS kẹt (nên thêm `timeout=5`).
- `ingest_raw_inputs.py:95` — ranh giới đệ quy lệch 1 (`max_depth=4` thực tế cho xuống 5 tầng); làm rõ ý định hoặc đổi `>` thành `>=`.
- `render_html_count_grid.py:24` vs `render_html_tooltip.py:25` — hàm `_tip_scalar` (4 dòng) trùng; gom nếu rảnh.
- `migrate_metric_to_metrics.py:248` — báo cáo trường hợp "không cần đổi" vs "bị từ chối" có cấu trúc hơi lệch (chỉ là mỹ quan).
- `release/scripts/tests/test_release.py` — thiếu test đầu-cuối cho cờ `--pre-release` (có cài, chưa có test).
- `spec_graph.py:346` + test ở `test_core_failsoft_and_sentinels.py:321` — nếu 2 artifact **cùng** hỏng id thì cái sau đè cái trước trong dict. **Cố ý fail-soft** (docstring ghi rõ) và `check_consistency` vẫn báo lỗi id riêng → gần như vô hại; chỉ nên thêm 1 test phơi bày hành vi.

---

## 8. Đề xuất thứ tự sửa (khi bạn duyệt)

1. **H-1 + §5 cùng lúc:** thêm tham số giờ tiêm được cho `gather()` của các lens telemetry → hết test đỏ + kín lỗ test ranh giới. (1 lần sửa gốc)
2. **H-2:** bỏ `import yaml` trong `lens_workflow_chains.py`, thay bằng parser stdlib (mẫu có sẵn ở `lens_memory_health.py`).
3. **Cụm "thêm try/except" rẻ và an toàn:** M-4 (verify YAML), M-5 (rollback JSON), M-6 (ngày changelog). Cùng kiểu, ít rủi ro.
4. **M-1** (bump_version `+build`), **M-3** (khớp-từ ngôn ngữ), **M-7** (validate float), **M-10** (khai báo lens), **M-9** (fs_guard).
5. **M-2** (timestamp dedup) — **đọc lại mã xác nhận 2 định dạng cùng xuất hiện trước khi sửa.**
6. Dọn mức thấp + gom code trùng (M-8, M-11) khi tiện.

Tôi đề xuất sửa **theo đợt sau khi bạn duyệt danh sách** (đúng lựa chọn "gộp vào audit, sửa sau khi có báo cáo"
của bạn), bắt đầu từ #1 vì nó đang làm CI đỏ.

---

## 9. Cập nhật — các sửa đã áp dụng (2026-06-13, sau khi PO duyệt)

PO duyệt sửa đợt 1. Đã làm, test xanh:

| Mục | Đã sửa | Kết quả |
|-----|--------|---------|
| **H-1 + §5** | Thêm tham số đồng hồ tiêm được (`now`) cho cả họ lens telemetry: `lens_artifact_heat`, `lens_reliability`, `lens_validate_proxy`, `lens_usage_tokens`, `lens_workflow_chains`, `harvester` (+ `_age_days` của `lens_memory_health` & `lens_product_memory`). Sửa test `test_heat_lens_respects_days_window` tiêm `now` cố định. | **137/137 test telemetry xanh**; test đang-đỏ nay xanh và hết phụ thuộc ngày thật. |
| **H-2** | PO chọn **giữ `import yaml`** → cập nhật 12 chỗ tài liệu (SKILL.md ×2, README ×8, GUIDE-VI/EN) từ "stdlib-only / không cần venv" → "cần PyYAML (phụ thuộc runtime duy nhất, đi kèm product-spec)". | Tài liệu hết sai; không còn claim "stdlib-only" giả. |
| **M-2** | Thêm `_ts_key()` trong `critique_inherit.py` — so sánh mốc thời gian theo thời gian thật (chịu được mọi định dạng `YYMMDD` / `YYMMDD-HHMM` / `YYYYMMDDThhmmssZ` / ISO), thay so sánh chữ-cái. Thêm test hồi quy. | **189/189 test critique xanh** (gồm test hồi quy mới). |
| **Memory** | Sửa `bogo-spec-revealed-tooling-gaps.md` + `MEMORY.md`: bỏ nhầm "thiếu craft-linter / INVEST" (thực ra đã có `vagueness`/`invest_quality`); 4 gap script-level còn lại + ghi nhận self-audit 0 blocker. | Xong. |

**Lưu ý H-2 (đã báo PO trước khi sửa):** ban đầu tôi nói "chỉ sửa 1 dòng tài liệu" — sai. Thực tế claim
"stdlib-only" nằm ở 12 chỗ, và `lens_workflow_chains` được import sớm nên TOÀN BỘ lệnh telemetry cần PyYAML
(không chỉ `--lens workflow`). Tôi đã báo lại dữ kiện này; PO vẫn chọn hướng giữ `import yaml` + sửa tài liệu.

**Chưa làm (chờ duyệt tiếp):** toàn bộ mục 🟡 Trung bình còn lại (M-1, M-3..M-11) và ⚪ Thấp ở §4/§7.

## 10. Câu hỏi mở (cần bạn quyết)

1. **Sửa tiếp cụm "thêm try/except" rẻ & an toàn (M-4 verify-YAML, M-5 rollback-JSON, M-6 ngày changelog)** không?
2. Có muốn tôi **commit** các thay đổi đợt 1 này (telemetry + critique) theo conventional-commit
   (`fix(telemetry): …`, `fix(critique): …`) không? (Tôi chưa commit gì.)
3. Các mục Trung bình/Thấp còn lại: làm tiếp theo đợt, hay để bạn chọn từng mục?
