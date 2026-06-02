# Brainstorm → Design: `cleanmatic:spec-critique` (brutal product-spec critique skill)

**Date:** 2026-06-02 01:52 · **Branch:** feat/product-spec-guardrails-and-memory-layer
**Status:** design agreed, ready for `/ck:plan`
**Companion research:** `researcher-260602-0152-product-spec-critique-value-lenses-report.md`

---

## 1. Problem statement

PO muốn 1 skill kiểu ck-journal nhưng cho **output của product-spec**: đọc spec (Vision/BRD/PRD/Epic/Story+AC) và **phản biện phũ phàng, giọng mỉa mai** dưới nhiều góc — sản phẩm, kỹ thuật, thị trường/cạnh tranh/lợi nhuận, và craft (sai chính tả/thuật ngữ, vỡ bố cục, mô tả lười/thiếu trực quan, lỗi lặp lại). Có thể so đối thủ qua websearch. Default chạy mọi góc bằng dedicated sub-agents; có cờ + `--interactive` để chọn. Cần **skill + agents + hook**. Không đụng ck (claudekit) hook/agent/skill.

### Yêu cầu chốt (5 mục)
1. **Expected output:** 1 file markdown critique report trong `docs/product/critique/<ts>-<scope>.md`, mỗi finding = trích dẫn (ID+dòng) → câu mỉa → vì sao chết → cách sửa.
2. **Acceptance:** chạy `/spec-critique [scope]` → fan-out 4 lăng kính + 1 consolidator → 1 report tiếng Việt (default) giọng "chửi+mỉa" có dẫn chứng; không sửa artifact; không gate CI.
3. **Scope OUT (v1):** HTML output, GUIDE-VI/EN, `--savage`/`--gentle` có thể v1.1 (xem §7), edit-from-report, PDF.
4. **Constraints:** tách riêng product-spec; tái dùng venv + scripts product-spec; non-deterministic (không reproducible-gate); read-only với spec + `.memory`.
5. **Touchpoints:** `.claude/skills/spec-critique/` (mới), `.claude/agents/spec-critique-*` (mới), `.claude/hooks/spec_critique_nudge.py` (mới), đọc `docs/product/` + scripts product-spec.

---

## 2. Quyết định kiến trúc (đã chốt qua phỏng vấn)

| # | Quyết định | Chốt | Lý do |
|---|---|---|---|
| D1 | Tách hay gộp | **Tách skill riêng** | `--validate` phải reproducible + gate CI; critique non-deterministic + websearch → nhét vào sẽ phá hợp đồng tái-lập của validate. Giọng phũ trái identity "ấm áp PO-facing" của product-spec. |
| D2 | Agent granularity | **N agent chuyên biệt theo lăng kính** + 1 consolidator | Mỗi persona sắc theo 1 khung; fan-out song song. |
| D3 | Output | **`docs/product/critique/<ts>-<scope>.md`** | Spec-scoped, sibling exports/impact/visuals; không đụng `docs/journals/` (của ck). |
| D4 | Tên skill | **`cleanmatic:spec-critique`** | Phản ánh giọng phũ. |
| D5 | Bộ lăng kính | **4: product / tech / market+đối-thủ / craft** | Gom market+lợi-nhuận+cạnh-tranh (cùng cần web+góc KD). |
| D6 | Web research | **Default BẬT, cờ `--no-web`** | Đây là giá trị mới nhất vs validate. |
| D7 | Hook posture | **Soft opt-in nudge giống `memory_gap_hook`** | Không tự chạy (tốn token+web); recommend-and-ask; ghi `settings.local.json`. |
| D8 | Quan hệ validate | **critique_scan chạy full `--validate` (structural + LLM judgment) trước → lens agent ăn verdict làm đạn, không phân tích lại** | DRY; verdict sẵn cho mọi lens. |
| D9 | Ranh critique vs validate | **Siết: validate=có lỗi không; critique=tại sao nhục + góc validate không chạm; cấm chép label** | §4. |
| D10 | Lằn ranh giọng | **Thang 5 mức, default mức 3; mức 1–4 cấm công kích cá nhân, chỉ mức 5 tháo** | §5. |
| D11 | Điểm hook | **Sau `--validate`** | Đúng ngữ cảnh PO đang xem chất lượng. |
| D12 | Scope tối thiểu | **Node bất kỳ, lens tự điều tiết theo cấp** | Story lẻ → tech+craft nặng, product nhẹ, market mỏng/bỏ; consolidator cảnh báo scope nhỏ cho market. |
| D12b | Ngữ cảnh tổ tiên | **Luôn truy ngược lên gốc (story→epic→PRD→BRD→vision) làm khung; chỉ critique đích, nhưng đối chiếu intent thượng nguồn** | Giá trị/INVEST/core-value chỉ phán được khi có goal BRD + vision. assemble_digest prepend vision/BRD/PRODUCT + spec_graph parent-links. |
| D13 | Memory | **Thuần đọc; PO confirm → ghi `DEC` qua `decision_register.py`** | Không trộn ý kiến chủ quan vào memory deterministic; bridge qua writer sẵn có + GATE. |
| D14 | Đo drift (hook) | **Đếm node `body_hash` đổi so `last_critique.json`; vượt ngưỡng → nudge** | Tái dùng `body_hash` của `spec_graph`, deterministic. |

---

## 3. Kiến trúc tổng thể

```
/spec-critique [scope] [--product|--tech|--market|--craft] [--interactive]
            [--lang vi|en] [--no-web] [--level 1..5]
   │
   ├─ 1. main agent chạy full --validate (structural + LLM judgment) → verdicts
   │      critique_scan.py --root --scope <id|all>
   │      → resolve scope · TRUY NGƯỢC tổ tiên lên gốc (story→epic→PRD→BRD→vision)
   │        = khung ngữ cảnh; đích critique = node scope (+ con)
   │        · gom validate findings/judgments · assemble_digest (bundle + ancestry)
   │        · đọc competitors: từ BRD · đọc critique/ cũ (repeat-offense) · 1 JSON bundle
   │
   ├─ 2. FAN-OUT 4 lăng kính song song (Task, read-only)
   │      spec-critique-product · -tech · -market(+web) · -craft
   │      mỗi agent ăn bundle → trả findings (evidence+mỉa+why+fix+severity)
   │
   ├─ 3. spec-critique-consolidate (opus, read-only)
   │      dedup/merge cross-lens · severity blocker/major/minor
   │      · top-3 "phải sửa trước khi đem khoe" · so report cũ (repeat)
   │      · giọng cuối theo --lang/level → trả markdown
   │
   ├─ 4. main agent GHI docs/product/critique/<ts>-<scope>.md
   │      + cập nhật .memory/last_critique.json (snapshot body_hash)
   │
   └─ 5. (tùy chọn) phản biện lớn PO đồng ý → decision_register.py --decision (DEC)
```

**Chiều tham chiếu:** skill → agents. SKILL.md + `workflow-critique.md` là nhạc trưởng; agent **không** spawn agent (không có `Task`). Main agent orchestrate scan → fan-out → consolidate → write.

---

## 4. Ranh giới critique vs `--validate` (D9 — chống "validate mặc áo chửi")

| Case | validate (enum, gate được) | spec-critique (góc mới + giọng) |
|---|---|---|
| Story đúng INVEST nhưng vô giá trị | `core-value: weak`, INVEST ✅ | *product*: "đổi màu nền login? user đăng nhập 4s rồi biến… cắt hoặc chỉ ra ai mất ngủ vì nó" |
| Có AC nhưng không test nổi | `vagueness: warn` | *tech*: "'phản hồi nhanh' = 200ms hay 2 ngày? viết GWT đo được hoặc đừng gọi là AC" |
| Persona hợp lệ nhưng không ai mua | persona label ✅ | *product+market*: "persona kế-toán-40t nhưng BRD ghi người trả tiền là CTO 55+…" |
| Craft | *(im lặng — validate không chấm prose)* | *craft*: "7 lần 'linh hoạt' 0 định nghĩa; 'khách hàng/người dùng/user' 3 tên 1 người; PRD-PAY 40 dòng 1 khối" |

**Luật khoá:** mỗi dòng critique phải là thứ validate **không thể** nói (prose tại-sao-chết / web / craft / cross-lens). Dòng chỉ chép lại label validate → consolidator cắt.

---

## 5. Voice & tone (D10) — `references/voice-and-tone.md`

- **Thang 5 mức, `--level 1..5`, default 3** (alias `--warm`/`--gentle`/`--blunt`/`--savage`/`--no-mercy`):

| Mức | Giọng | Phạm vi |
|---|---|---|
| 1 | ấm áp, khuyên nhủ | spec |
| 2 | chỉ trích nhẹ nhàng | spec |
| **3** ⭐ default | chỉ trích thẳng thừng | spec |
| 4 | chỉ trích cay độc | spec |
| 5 | không kiêng nể ai kể cả PO, bất chấp tổn thương | **spec + cá nhân** |

- **Lằn ranh cá nhân:** mức 1–4 cấm công kích cá nhân (chỉ đả spec/quyết định); **chỉ mức 5** mới tháo, PO phải chủ động chọn + kèm cảnh báo rủi ro.
- **5 nguyên tắc giữ phũ-mà-uy-tín** (từ research, áp dụng MỌI mức): (1) mỗi câu phũ kèm bằng chứng ID+dòng; (2) đả failure mode không đả người viết (trừ mức 5); (3) tách quan-sát khỏi ý-kiến; (4) pre-mortem thay vì devil's-advocate suông; (5) luôn kèm cách sửa.
- Song ngữ: voice spec có **cả vi + en**; output localize theo `--lang` (**default vi**).

---

## 6. File inventory (cần tạo)

**Skill** `.claude/skills/spec-critique/`
- `SKILL.md` — lean skeleton (EN, LLM-facing), flags, workflow map, dùng chung venv.
- `references/workflow-critique.md` — luồng 5 bước, orchestration, scope-aware lens applicability.
- `references/voice-and-tone.md` — giọng vi+en, 5 nguyên tắc, thang 5 mức.
- `references/lens-frameworks.md` — bảng framework→câu hỏi→failure signature cho 4 lăng kính (từ research).
- `scripts/critique_scan.py` — orchestration mỏng (reuse-first): scope resolve + gom validate findings/judgments + assemble_digest + đọc BRD competitors + đọc critique/ cũ → 1 JSON bundle; ghi/đọc `last_critique.json`.
- `scripts/tests/test_critique_scan.py`.
- `install.sh` / `install.ps1` — idempotent; cờ opt-in hook (`--critique-hook`); reuse venv product-spec.

**Docs surface (ngang hàng product-spec — §6b)**
- `README.md` — pitch ngắn + quickstart + bảng flag (như product-spec README 2.6K).
- `GUIDE-VI.md` / `GUIDE-EN.md` — guide chi tiết PO-facing: **mỗi cờ · mỗi use-case · mỗi lăng kính** thành 1 đoạn hội thoại mẫu (cách tự nhiên ưu tiên + bản flag tương đương), chạy xuyên qua sample.
- `examples/` — sample critique **output** (xem §6c).

**Agents** `.claude/agents/` (read-only: Glob/Grep/Read/Bash; market +WebSearch/WebFetch; KHÔNG Write/Edit/Task)
- `spec-critique-product.md` (**opus** — judgment nặng nhất: JTBD/giá trị/persona) · `spec-critique-tech.md` (sonnet) · `spec-critique-market.md` (sonnet+web) · `spec-critique-craft.md` (haiku) · `spec-critique-consolidate.md` (opus).

**Hook** `.claude/hooks/spec_critique_nudge.py` — opt-in, sau `--validate`/Stop; đếm body_hash drift vs `last_critique.json`; nudge "chạy /spec-critique"; recommend-and-ask, ghi `settings.local.json`, không tự chạy.

**Reuse (không tạo mới):** `spec_graph.py`, `frontmatter_parser.py`, `check_traceability.py`, `check_consistency.py`, `assemble_digest.py`, `competitive_drift_anchors.py`, `decision_register.py`, `fs_guard.py`, `.memory/` readers.

**Output dir mới:** `docs/product/critique/` + marker `docs/product/.memory/last_critique.json`.

### 6b. Cấu trúc GUIDE-VI / GUIDE-EN (PO-facing, in scope v1)
Mỗi mục = 1 đoạn hội thoại mẫu (cách tự nhiên ưu tiên + bản flag tương đương), chạy xuyên qua `examples/`:
- **Mở đầu:** spec-critique là gì, khác `--validate` thế nào (bảng §4), khi nào nên dùng.
- **Theo use-case:** critique toàn spec · critique 1 nhánh (PRD/epic/story lẻ) · chọn lăng kính · `--interactive` · chỉnh mức giọng · offline `--no-web` · đọc lại report cũ / repeat-offense · biến phản biện thành `DEC`.
- **Theo cờ:** `[scope]` · `--product/--tech/--market/--craft` · `--interactive` · `--lang` · `--no-web` · `--level 1..5` (kèm mẫu output mỗi mức để PO cảm được giọng) — mỗi cờ 1 ví dụ vào/ra.
- **Theo lăng kính:** mỗi lăng kính (product/tech/market/craft) — soi gì, framework nào, 2–3 finding mẫu (trích dẫn→mỉa→why→fix).
- **Đọc report:** giải nghĩa severity blocker/major/minor, "top-3 phải sửa", callout repeat-offense.
- **Ranh giới:** không sửa spec, không gate CI, mức 5 cảnh báo.

### 6c. examples/ (sample output, DRY)
- **Tái dùng** `product-spec/examples/acme-shop` làm spec đầu vào (không tạo sample spec mới).
- Ship **sample critique report** `examples/critique-acme-shop-<lens|all>.md` ở vài mức giọng (vd mức 3 default + mức 1 ấm áp để đối chiếu) → PO thấy ngay output thật. Đây cũng là vật liệu cho eval.

---

## 7. Out of scope v1 (YAGNI)
- HTML/PDF report (markdown đủ). · Edit-from-report. · Ghi memory tự động (chỉ bridge `DEC` khi PO confirm). · NLP assumption-detection (product agent tự suy bằng judgment). · Sample spec mới (tái dùng acme-shop).
- **In scope (theo yêu cầu PO):** README + GUIDE-VI + GUIDE-EN + examples/ + cả 5 mức `--level`.

---

## 8. Risks & mitigations
- **R1 — critique = validate chửi lại:** consolidator cắt dòng chỉ chép label validate (§4 luật khoá). Test: report không được lặp nguyên văn finding.
- **R2 — chửi suông vô căn cứ:** voice-and-tone bắt mỗi dòng có ID+dòng+fix; consolidator drop dòng thiếu evidence.
- **R3 — token cost (5 agent + web):** opt-in, không auto-run; scope-aware (story lẻ bỏ market); craft = haiku.
- **R4 — market bịa đối thủ:** ưu tiên `competitors:` của BRD + web có cite; thiếu cả hai → flag "thiếu căn cứ" thay vì bịa.
- **R5 — đụng ck:** chỉ tạo file mới namespace spec-critique; hook ghi `settings.local.json`, không sửa hook ck.
- **R6 — non-deterministic làm bẩn validate marker:** critique dùng marker riêng `last_critique.json`, không đụng `last_validated.json`.

---

## 9. Success criteria
- `/spec-critique PRD-AUTH` → report tiếng Việt, mỗi finding có ID+dòng+mỉa+fix, severity, top-3.
- Không sửa bất kỳ artifact/`.memory` nào (trừ ghi report + last_critique.json).
- Craft bắt được lỗi validate không bắt (chính tả/thuật ngữ/bố cục).
- Market có cite đối thủ thật (web on) hoặc flag thiếu-căn-cứ (no-web).
- Repeat-offense: chạy lần 2 không sửa → consolidator bêu "đã chửi mà chưa sửa".
- Hook nudge xuất hiện sau validate khi ≥ngưỡng node đổi; không tự chạy.

---

## 10. Open questions — ĐÃ GIẢI QUYẾT
1. **Ngưỡng drift hook:** đọc từ **`preferences.yaml`** (key critique riêng, vd `critique_drift_threshold`), **default 3** node body_hash đổi. Tái dùng `preferences.py`.
2. **Model lens:** **product=opus**, tech=sonnet, market=sonnet+web, craft=haiku, consolidator=opus.
3. **Giọng:** thang **5 mức, default 3**; mức 1–4 cấm công kích cá nhân, chỉ **mức 5** tháo (PO chủ động + cảnh báo). Cờ `--level 1..5`. Xem §5.
4. **DEC bridge:** **consolidator gắn cờ "đáng thành DEC"** → main agent hỏi PO → ghi qua `decision_register.py --decision` (GATE-NEVER-ASSUME).
5. **critique_scan input:** **chạy full `--validate`** (structural + LLM judgment) trước; lens agent ăn verdict làm đạn (D8).

*Còn lại cho `/ck:plan`:* chia phase (scripts+test → agents → hook → skill+references → docs/README/GUIDE/examples → install), wiring `last_critique.json` schema (snapshot body_hash), key `critique_drift_threshold` trong `preferences.py` (default 3).
