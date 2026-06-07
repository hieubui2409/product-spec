# Hướng dẫn dùng `cleanmatic:telemetry` (Tiếng Việt)

Tài liệu này dành cho người làm sản phẩm (product owner). Mỗi tình huống được kể lại như một đoạn hội thoại mẫu. Bạn cứ nói bằng lời bình thường là được; phần ghi kèm cú pháp cờ chỉ là cách viết tương đương.

> Bản tiếng Anh: [`GUIDE-EN.md`](./GUIDE-EN.md).

---

## 1. Đó là cái gì, và cái gì là KHÔNG

`cleanmatic:telemetry` là một **đọc thẳng, chỉ-đọc** về cách các skill của mình được dùng và liệu chúng có khỏe không. Nó chạy **tám lăng kính** trên telemetry nội bộ của mình (gọi skill, session, chạy script, kết quả subagent, gọn gàng bộ nhớ) và kể chuyện kết quả bằng tiếng Việt bình thường (hoặc tiếng Anh với `--lang en`).

Nó **KHÔNG PHẢI**:
- Một metric **hiệu quả thị trường** (E3). Nó thấy *dùng*, không *value*.
- Một **writer** — không bao giờ sửa spec, code, catalog, memory.
- **Chính xác tính tiền** — token count và run time là ước lượng.
- Một **cổng CI** — dữ liệu neutral cho bạn đọc; không chặn gì.
- Một **crash-log analyzer** — thiếu `errors.jsonl` giàu; đợi BACKLOG.

**Nó LÀ:** một cửa sổ diagnostic vào *liệu máy mình chạy được không* (dùng ✓, khỏe ✓, chất lượng-nội-bộ ✓).

---

## 2. Khái niệm cốt lõi — mô hình tư duy (đọc một lần)

1. **Script gather; LLM kể chuyện.** Python script (`analyze_telemetry.py`) đọc JSONL sink chỉ-append (định tính, STDLIB-only) rồi ra JSON aggregates. Skill **kể chuyện** những con số đó bằng tiếng Việt bình thường, theo narration contract (`references/narration-contract.md`).

2. **Tám lăng kính, một báo cáo.** Báo cáo `--all` hiển thị cả tám lăng kính (forensics là sâu-đặc-thù, tách riêng khỏi dashboard). Mỗi lăng kính trả lời một câu:
   - `usage` — skill nào, bao nhiêu lần, token weight, chưa dùng?
   - `session` — bao nhiêu phiên, bao lâu, skill co-occur?
   - `health` — script lỗi, run time, subagent thành công?
   - `reliability` — subagent fail mode (timeout, api_error, v.v.)?
   - `workflow` — actual skill chain vs declared chain?
   - `validate` — spec validate có pass (chất lượng-nội-bộ)?
   - `memory` — orphaned note, dead link, lâu cũ?
   - `forensics` — dựng lại chi tiết một phiên (skill, tool, token, file).

3. **Cổng dữ liệu ít.** < ~5 data point, lăng kính hiển thị count thô + **"chưa đủ dữ liệu"** và chặn gợi ý. Trên repo mới, **hầu hết lăng kính BỊ CHẶN** — báo cáo nói thẳng.

4. **Cổng thật lòng (bắt buộc).** Mỗi báo cáo kết thúc bằng **"Cái này KHÔNG đo được"**, ghi rõ:
   - E3 / hiệu quả thị trường — liệu sản phẩm thắng trên thị trường.
   - Lăng kính bị chặn — tường minh với "chưa đủ dữ liệu".
   - Tuyên bố ước lượng — token, ms, exit code là ước lượng, không exact.

5. **Gợi ý, không phải lệnh.** Cụm từ như "Gợi ý" (suggestion) nói rõ skill không có quyền xóa skill, sửa memory, hay đổi scope — bạn quyết định.

---

## 3. Lộ trình học của bạn

- **Lần đầu:** `/cleanmatic:telemetry` mặc định (tất cả lăng kính, ascii, tiếng Việt) rồi đọc báo cáo. Bạn sẽ thấy hình hài: tóm tắt → dùng → khỏe → phiên → workflow → validate → memory → cổng thật lòng.
- **Rồi thu hẹp:** chọn một hai lăng kính (`--lens usage`, `--lens health`) để sâu hơn.
- **Thí nghiệm định dạng:** `--format md --top 5` bảng markdown gọn, `--format mermaid` biểu đồ, `--format json` để script thêm.
- **Sâu hơn:** `--session <id>` dựng lại flow skill một phiên (cần ID từ session lens).
- **Khi xây dựng:** chạy hàng tuần hoặc trước quyết định lớn; dữ liệu tích luỹ, nên pattern xuất hiện theo thời gian.

---

## 4. Những lưu ý quan trọng

- **Skill external chưa dùng không được cảnh báo.** Skill không phải của bạn (e.g., `ck:code-review`, `com:mcp-builder`) vắng là bình thường — chỉ **skill cleanmatic chưa dùng** (`cleanmatic:*`) được highlight.
- **Token weight ước lượng.** Từ transcript length + hệ số rough per-skill; ghi "ước lượng", không exact.
- **Validate proxy chỉ chất lượng nội bộ** — "spec tốt lành", không "user nhận" (đó là E3).
- **Dữ liệu ít được báo có thật lòng.** Trên repo mới, nhiều lăng kính sẽ nói "chưa đủ dữ liệu" — đó là sự thật, không phải thiếu sót.
- **Không có cờ `--apply`.** Skill này chỉ diagnostic. Phát hiện ở dạng gợi ý; bạn quyết định làm gì.

---

## Khi nào nên dùng

- Bạn muốn đọc thật lòng cách skill của mình được dùng, chứ không phải pass/fail.
- "Script nào chạy lỗi?", "Subagent có đáng tin?", "Memory có gọn?".
- "Validate pass chứ?" (như một snapshot chất lượng-nội-bộ).

KHÔNG dùng để: sửa spec, viết code, xóa skill, hay sửa memory — đó là skill khác (`product-spec`, code-review, v.v.).

---

## 5. Các tình huống — gom theo tier

---

## Tier A — Chạy đọc telemetry lần đầu

### A1. Snapshot cả stack

> **Bạn:** "Cho tôi xem skill của tôi đang được dùng cách nào và liệu chúng có khỏe không."
> **Trợ lý:** Chạy cả tám lăng kính, kể chuyện tiếng Việt, kết thúc bằng cổng thật lòng. Báo cáo hiển thị: top invoked skill + token weight → chưa dùng → script lỗi → subagent tin cậy → memory state → validate proxy → "Cái này KHÔNG đo được" (E3, lăng kính bị chặn, disclaimer token).
>
> Cách gõ tương đương: `/cleanmatic:telemetry` hoặc `/cleanmatic:telemetry --lens all --format ascii`.

### A2. Đọc báo cáo (cấu trúc)

- **Tóm tắt (Summary)** — 2–3 dòng: mức dùng chung, vấn đề khỏe nào, dữ liệu đủ không.
- **Mức dùng (Usage)** — top skill theo lần gọi + token ước lượng + skill cleanmatic chưa dùng.
- **Sức khỏe (Health)** — script lỗi hay chạy chậm; subagent thành công/thất bại breakdown.
- **Phiên (Sessions)** — số phiên, avg/median duration, co-occurrence (skill dùng cùng).
- **Workflow chain** — actual vs declared skill chain; sai lệch được cảnh báo.
- **Validate proxy** — lần validate pass/fail + pass-rate cuối (snapshot chất lượng nội-bộ, ghi "không phải E3").
- **Memory** — orphaned note, broken `[[link]]`, lâu cũ.
- **Cái này KHÔNG đo được** — phần thật lòng: E3 + lăng kính bị chặn + disclaimer ước lượng.

---

## Tier B — Thu hẹp & sâu hơn

### B1. Chỉ dùng: skill nào lạnh?

> **Bạn:** "Tôi muốn biết skill của mình cái nào chưa ai dùng."
> **Trợ lý:** Chạy `--lens usage` → hiển thị lần gọi, token weight, skill cleanmatic chưa dùng. Một dòng mỗi skill. Chỉ skill mình sở hữu được liệt kê (skill external không được cảnh báo).
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens usage`.

### B2. Khỏe: script nào chạy lỗi?

> **Bạn:** "Script nào đang lỗi hay chạy chậm?"
> **Trợ lý:** Chạy `--lens health` → hiển thị per-script: run count, error rate, avg ms (ước lượng). Script nào có >0 error được highlight. Slow run là estimate (ước lượng).
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens health`.

### B3. Tin cậy: subagent có đáng tin?

> **Bạn:** "Cho tôi xem subagent success breakdown."
> **Trợ lý:** Chạy `--lens reliability` → hiển thị per-subagent-type: success, api_error, timeout, blocked, unknown. Giúp phát hiện pattern (e.g., "researcher timeout thường").
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens reliability`.

### B4. Phiên: bao lâu mỗi phiên?

> **Bạn:** "Chúng ta chạy bao nhiêu phiên, và mỗi phiên bao lâu?"
> **Trợ lý:** Chạy `--lens session` → hiển thị số phiên, avg/median duration (phút), file/tool co-occurrence, skill co-occurrence. Co-occurrence nói skill nào dùng cùng (workflow pattern).
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens session`.

### B5. Validate proxy: spec có tốt lành?

> **Bạn:** "Lần validate cuối cùng có pass không?"
> **Trợ lý:** Chạy `--lens validate` → hiển thị kết quả validate cuối (pass/fail) + pass-rate trên N lần. Tường minh ghi "không phải E3" (không hiệu quả thị trường, chỉ chất lượng-nội-bộ).
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens validate`.

### B6. Memory: orphan hay broken link?

> **Bạn:** "Có quyết định nào mồ côi hay link nào hỏng trong bộ nhớ?"
> **Trợ lý:** Chạy `--lens memory` → hiển thị orphaned note, dead index entry, broken `[[link]]`, lâu cũ (note chưa cập nhật 30+ ngày). Chỉ-đọc; không `--apply` (diagnostic, không auto-fix).
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens memory`.

### B7. Workflow: chain có khớp doc?

> **Bạn:** "Skill chain thực tế có khớp với routing doc không?"
> **Trợ lý:** Chạy `--lens workflow` → so sánh actual chain (từ invocation log) vs declared chain (từ `.claude/rules/skill-workflow-routing.md`). Sai lệch được cảnh báo (e.g., "doc nói planner → cook, nhưng bạn đang planner → debug trực tiếp").
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens workflow`.

---

## Tier C — Định dạng đầu ra & tinh chỉnh

### C1. Bảng markdown (top-N, copy-paste dễ)

> **Bạn:** "Cho tôi lens usage dạng markdown, chỉ top 5."
> **Trợ lý:** Chạy `--lens usage --format md --top 5` → bảng markdown: tên skill, lần gọi, token ước lượng, cờ chưa-dùng. Copy-paste dễ; ngắn hơn ascii.
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens usage --format md --top 5`.

### C2. Mermaid chart (không mạng)

> **Bạn:** "Cho tôi subagent success breakdown dạng pie chart."
> **Trợ lý:** Chạy `--lens reliability --format mermaid` → fenced mermaid pie/bar chart. Hoạt động ở markdown viewer; không mạng hay JS.
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens reliability --format mermaid`.

### C3. JSON (để script)

> **Bạn:** "Cho tôi raw aggregate dạng JSON để xử lý thêm."
> **Trợ lý:** Chạy `--lens all --format json` → in JSON dict của tất cả aggregate. Dùng để xây dashboard hay alert.
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lens all --format json`.

### C4. Chế độ tiếng Anh

> **Bạn:** "Cho tôi báo cáo tiếng Anh, không phải tiếng Việt."
> **Trợ lý:** Chạy `--lang en` → nhãn cố định (heading, column header, gate note) dịch tiếng Anh; LLM kể chuyện tiếng Anh.
>
> Cách gõ tương đương: `/cleanmatic:telemetry --lang en`.

### C5. Khoảng thời gian tùy chọn

> **Bạn:** "Chỉ cho tôi 7 ngày trở lại."
> **Trợ lý:** Chạy `--days 7` → cùng lăng kính, lọc 7 ngày gần nhất. Mặc định 30 ngày.
>
> Cách gõ tương đương: `/cleanmatic:telemetry --days 7`.

---

## Tier D — Forensics: dựng lại một phiên

### D1. Liệt kê phiên

> **Bạn:** "Tôi có phiên nào trên ghi chép?"
> **Trợ lý:** Chạy `--all-sessions` → in bảng ID phiên, timestamp, skill count, file count, duration. Chọn một để sâu hơn.
>
> Cách gõ tương đương: `/cleanmatic:telemetry --all-sessions`.

### D2. Dựng lại một phiên

> **Bạn:** "Cho tôi xem phiên abc123def chuyện gì xảy ra."
> **Trợ lý:** Chạy `--session abc123def --format md` → dựng lại: entry point skill → tất cả sub-call (skill, tool, LLM call, v.v.) → token → file touched → duration. Full call tree.
>
> Cách gõ tương đương: `/cleanmatic:telemetry --session <id> --format md`.

---

## 6. Kết hợp cờ — công thức phổ biến

| Muốn | Lệnh |
|------|------|
| Kiểm tra sức khỏe hàng tuần | `/cleanmatic:telemetry --days 7` |
| Top 10 invoked skill + token | `/cleanmatic:telemetry --lens usage --format md --top 10` |
| Bắt script lỗi | `/cleanmatic:telemetry --lens health` |
| Subagent tin cậy pie chart | `/cleanmatic:telemetry --lens reliability --format mermaid` |
| Kiểm tra memory gọn | `/cleanmatic:telemetry --lens memory` |
| Snapshot đầy đủ, anh, markdown | `/cleanmatic:telemetry --lang en --format md` |
| 14 ngày cuối, chỉ usage | `/cleanmatic:telemetry --days 14 --lens usage` |
| Dựng lại phiên | `/cleanmatic:telemetry --session <id>` |
| JSON thô để script | `/cleanmatic:telemetry --format json` |

---

## 7. Khái niệm cốt lõi (sâu hơn)

### Mô hình dữ liệu

Năm JSONL sink chỉ-append dưới `.claude/telemetry/` (gitignore):

- **`invocations.jsonl`** — mỗi lần gọi skill. Trường: tên skill, timestamp, token (ước lượng), transcript hash.
- **`sessions.jsonl`** — tóm tắt end-of-session. Trường: ID phiên, timestamp, duration, file list, subagent list, skill co-occur.
- **`hook-telemetry.jsonl`** — chạy script log. Trường: tên script, timestamp, exit code, ms, error message (nếu có).
- **`subagent-outcomes.jsonl`** — subagent hoàn thành. Trường: loại subagent, kết quả (success / api_error / timeout / blocked / unknown), duration, error.
- **`last_validated.json`** — validate result snapshot. Trường: pass/fail, timestamp, pass-rate (từ exit history).

Cả năm sink được viết bởi fail-open hook (tự đăng ký khi cài; opt out: `register_telemetry_hooks.py --remove`). Trên người nhận, hook viết vào `.claude/telemetry/` riêng của họ dưới project root.

### Script → aggregates (analyze_telemetry.py làm gì)

1. Đọc mọi sink vào bộ nhớ.
2. Group theo metric (e.g., skill invocation gom theo tên skill).
3. Tính count, rate, avg, median.
4. So với cổng dữ liệu ít (~5 point).
5. Ra JSON dict với mọi aggregate.

Script định tính, không phán đoán. **LLM phán đoán** (kể chuyện VI, áp cổng thật lòng).

### Chưa dùng (external vs sở hữu)

Skill ở catalog (từ `.claude/rules/skill-workflow-routing.md`) có 0 invocation trong lookback period là "chưa-dùng".

- Nếu là **skill cleanmatic** (`cleanmatic:*`), được cảnh báo để bạn xem xét (có thể không còn cần?).
- Nếu là **skill external** (`ck:*`, `com:*`, v.v.), **KHÔNG cảnh báo** — PO không sở hữu nên có thể không dùng được. Chỉ count của skill external chưa-dùng được nhắc, không liệt kê.

### Token weight (ước lượng)

Token count là **hướng**, không exact. Dẫn xuất từ transcript length + per-skill coefficient (học từ mẫu chạy). Luôn ghi "ước lượng" (estimate).

### Validate proxy (chất lượng-nội-bộ ≠ E3)

Lens `validate` hiển thị `product-spec --validate` có pass lần cuối + pass-rate. Đây là **chất lượng nội-bộ** (spec tốt lành, không orphan, không lệch core-value). Nó **KHÔNG PHẢI** E3 (hiệu quả thị trường, user nhận, doanh thu). Báo cáo ghi tường minh "không phải E3".

---

## 8. Xử lý sự cố

### "Chưa đủ dữ liệu" ở nhiều lăng kính

**Bình thường trên repo mới.** Telemetry tích luỹ theo thời gian. Khi có ~5+ data point mỗi lens, gợi ý xuất hiện.

**Làm gì:** Tiếp tục dùng skill, rồi chạy `/cleanmatic:telemetry` lại tuần sau.

### "Script X luôn lỗi"

**Xem message lỗi** ở lens `health`. Chạy script thủ công xem lỗi gì. Skill là diagnostic; không fix.

**Làm gì:** Xem log script, xem stack trace, báo bug hay fix trực tiếp.

### Session forensics hiển thị 0 token

**Token ước lượng.** Phiên ít LLM call thì token có thể 0. Xem chi tiết phiên (skill, tool) để thấy gì thực sự xảy ra.

### Memory hiển thị "staleness" trên note của tôi

**Note >30 ngày được cảnh báo.** Bình thường nếu note ổn định; archive hay cập nhật nếu thực sự lâu cũ.

**Làm gì:** Xem note cũ, xóa cái không dùng, hoặc cập nhật timestamp nếu vẫn dùng.

---

## 9. Hỏi skill bằng tiếng Việt bình thường

Bạn không cần cờ. Cứ hỏi:

- "Cho tôi biết skill nào lạnh."
- "Subagent có đáng tin không?"
- "Validate có pass không?"
- "Dựng lại phiên abc123."
- "Top 5 skill theo lần gọi."
- "Workflow sai lệch."
- "Gợi ý dọn dẹp memory."

Skill sẽ dịch ý định thành cờ và chạy lăng kính đúng.

---

## 10. Đường dẫn sâu & tài liệu tham khảo

- **Narration contract** (quy tắc ngôn ngữ thật lòng): `references/narration-contract.md`
- **Hợp đồng hoạt động đầy đủ**: `SKILL.md`
- **Hướng dẫn tiếng Anh**: `GUIDE-EN.md`
- **Module lens**: `.claude/skills/telemetry/scripts/lens_*.py`
- **Nguồn script**: `.claude/skills/telemetry/scripts/analyze_telemetry.py`
- **Changelog**: `CHANGELOG.md`
