# Brainstorm — Learning Loop (`--learn`): un-defer E3 + đóng cạnh định tính

- **Date:** 2026-06-09
- **Skill:** `cleanmatic:product-spec` (mode mới `--learn`)
- **Backlog:** un-defer **E3** (`BACKLOG.md:114`); feed **C9** audit trail
- **Status:** thiết kế PO-approved (brainstorm) → sẵn sàng `/ck:plan`

---

## 1. Problem statement

PO giờ ĐÃ có insight thực tế (monthly benefit report, firebase analytics tần-suất/hành-vi,
review khách, order data thành công, "product feedback" khác). `BACKLOG.md` E3 ("record actuals
vs BRD goal metrics; flag shipped-but-missed; close spec→build→measure→learn") đang `[defer]`
với **đúng 1 lý do**: *"product not in market yet."* Insight thật **vô hiệu hóa tiền đề defer** →
E3 mở khóa.

**Lỗ hổng data-model:** BRD goal chỉ có `metrics: [slug]` (chuỗi tự do) — KHÔNG lưu target/actual.
Target bị "nhốt" trong prose `title` ("Onboard 100 boutique brands in 12 months"). Muốn flag
hit/miss phải có chỗ cấu trúc.

**Phát hiện then chốt:** PO gộp **2 vòng học khác bản chất**:
- **Định lượng** — số thực vs target → hit/miss (E3-core).
- **Định tính** — review/feedback → vấn đề/persona/risk mới → quay lại `--update` ("discover-back").

---

## 2. Quyết định kiến trúc (PO-confirmed)

| # | Ngã rẽ | Chốt | Lý do |
|---|--------|------|-------|
| 1 | Độ sâu nạp data | **Light: PO khai verdict** | Skill KHÔNG parse analytics. Offline thuần, KISS, chống scope-creep BI. |
| 2 | Vòng học | **Cả hai** | "complete the learning cycle**s**" = định lượng + định tính. |
| 3 | Nhà | **Mode trên product-spec** | E-pattern §106: ưu tiên mode > skill mới. Sở hữu goal/metric/DEC/audit/discover → DRY. |
| 4 | Lưu target/actual | **Register `outcomes.md` riêng** | Không đụng schema goal (0 back-compat risk); tách actual (đo nhiều lần) khỏi goal (định nghĩa 1 lần) = DRY. |
| 5 | Tên flag (debate) | **`--learn` ô dù** | "learn" mô tả ý định đúng hơn "discover" (vốn = seed cold-start). DRY là về **script**, không phải tên → `--learn` vẫn gọi `ingest_raw_inputs.py`. Ô dù = 1 cửa PO non-tech, route 2 path code tách. |
| 6 | Verdict | **Hybrid (B3)**: số→script / phi-số→PO khai | Metric hỗn hợp (GMV số; "chất lượng review" định tính). |
| 7 | Quadrant feedback | **KHÔNG** | Kéo về NLP/BI, lệch scope. learning-map + insight-gap đã cho "matrix-feel". |

---

## 3. Giải pháp cuối

### 3.1 Mode `--learn` (ô dù)

```
PO gọi --learn (hoặc NL "có số liệu/phản hồi thực tế mới")
   └─ skill hỏi: SỐ LIỆU hay PHẢN HỒI? → route 2 path tách (deterministic, test được)
```

**Path A — Số liệu (vòng định lượng):**
1. Mỗi `BRD-G<n>` → PO khai `target`+`actual`+`unit`+`source`+`measured_on`.
2. **Hybrid verdict:** số → `record_outcome.py` tính `hit|partial|miss` (deterministic); phi-số → PO khai verdict.
3. Append dòng `OUT-<n>` vào `docs/product/outcomes.md`.
4. Goal `approved` mà **miss** → *surface* tín hiệu học (KHÔNG auto-sửa spec) → gợi ý `--update`/`DEC-<n>`. Mọi re-approval qua **GATE-NO-SILENT-REVERSAL**.

**Path B — Phản hồi (vòng định tính / discover-back):**
1. File text (review/feedback/insight) → `ingest_raw_inputs.py` (read-fence sẵn: `.md`/`.txt`, chặn dotfile, cap size, chặn traversal).
2. Echo accepted/rejected list cho PO confirm trước khi đọc nội dung.
3. LLM synth **candidate** problem/persona/risk MỚI (text vào → bullet ra; KHÔNG cluster/NLP gold-plating).
4. Feed `--update` delta (KHÁC `--discover` ở đích: update spec đang có, không seed Vision lạnh).
5. **GATE-NEVER-ASSUME** — không auto-commit; mỗi thay đổi PO nhận → 1 `DEC-<n>`.

### 3.2 Lưu trữ — `docs/product/outcomes.md`

Append-only register (mẫu `decisions.md`), frontmatter list-of-dicts, id `OUT-<n>`:

```yaml
outcomes:
  - id: OUT-1
    goal: BRD-G3              # ref BRD goal (DRY — goal vẫn định nghĩa ở brd.md)
    metric: gmv-year1
    target: 2000000
    actual: 1450000
    unit: USD
    measured_on: 2026-05-31
    source: "monthly-benefit-report 2026-05"   # nhãn, KHÔNG phải path fetch
    verdict: miss            # số → script tính; phi-số → PO khai
    note: "Q2 dưới kỳ vọng do ..."             # định tính, LLM/PO viết
```

Target chụp **tại thời điểm đo** nằm trong chính dòng outcome → không đụng schema goal NHƯNG
script vẫn tính hit/miss deterministic (đúng script-vs-LLM split).

### 3.3 Viz (`--viz <view>`) — 5 view, PO non-tech nhìn-là-hiểu

| View | Câu hỏi PO | Hình | Tái dùng |
|------|-----------|------|----------|
| **`scorecard`** ⭐ | "Có đạt mục tiêu không?" | Thẻ/goal: target vs actual + badge 🟢hit/🟡partial/🔴miss + xu hướng. Goal **chưa đo** = ô xám "blind spot" | render_html design-system (như `dashboard`) |
| **`outcome-trend`** | "Khá lên hay tệ đi?" | Heatmap goal × kỳ-đo, ô = màu verdict | reuse `heatmap` |
| **`insight-gap`** | "Khoảng cách lớn nhất ở đâu?" | Thanh delta (target−actual)/goal, xếp gap giảm dần | render_ascii/html bars |
| **`learning-map`** | "Đã LÀM GÌ với điều học được?" | Flow insight/outcome → node spec → `DEC-<n>` → thay đổi | mở rộng `assemble_audit_trail.py` (C9) |
| **`learning`** | "1 trang thấy hết" | Dashboard gộp scorecard+trend+gap+link map (HTML-only) | compose 4 view trên |

**Chuẩn bắt buộc:** viz từng là điểm XSS (cycle-1) → mọi field động **escape server-side**, body qua
DOMPurify, fail-closed về text.

---

## 4. Touchpoints (file)

**Mới:**
- `scripts/record_outcome.py` — append OUT row + tính verdict số (mẫu `decision_register.py`)
- `assets/templates/outcomes.md` — template register
- `references/workflow-learn.md` — luồng `--learn` (2 path) + GATEs
- viz: scorecard/trend/gap/learning-map/learning trong `visualize.py` + `render_ascii.py`/`render_html.py`/`render_mermaid.py`
- tests trong `scripts/tests/`

**Sửa:**
- `SKILL.md` — flag `--learn`, no-flag menu (mục "Học từ thực tế"), `--viz` list +5 view
- `assemble_audit_trail.py` — thêm nguồn `outcomes.md` cho learning-map
- `spec_graph.py`/`status.py` — load goals cho scorecard (read-only)
- `BACKLOG.md` — E3 `[defer]` → done; ghi quyết định
- `GUIDE-VI.md`/`GUIDE-EN.md` — use case PO
- `examples/acme-shop` — outcomes.md mẫu

**Tái dùng (không sửa lõi):** `ingest_raw_inputs.py` (path B), `decision_register.py` (DEC), `fs_guard.py`, `i18n_labels.py`.

---

## 5. Tuân chuẩn dự án

- ⛔ **No runtime network** — chỉ đọc file (firebase/order/report PO tự export ra file).
- **Frontmatter SoT** — outcomes parse được; verdict số deterministic.
- **Script vs LLM split** — script: append+tính số; LLM: synth candidate + note định tính.
- **DRY** — reuse ingest + audit; outcome tách khỏi goal.
- **GATEs** — NEVER-ASSUME (path B không auto-commit) · NO-SILENT-REVERSAL (re-approve goal).
- **YAGNI** — không live-connector, không parse analytics thô, không BI/quadrant/clustering.
- **PO-facing** — ngôn ngữ thường, bilingual EN/VI.

---

## 6. Phạm vi OUT (round này)

Live-connector firebase/DB · parse CSV/JSON analytics thô · BI dashboard · quadrant impact×effort ·
feedback clustering/NLP · migrate schema goal · auto-fetch insight.

---

## 7. Success metrics / validation

- `--learn` ghi được OUT row hợp lệ (schema validate pass) cho cả metric số lẫn phi-số.
- Verdict số = deterministic (cùng input → cùng output; CI-gate được).
- Path B không bao giờ commit candidate khi PO chưa confirm (test GATE-NEVER-ASSUME).
- Goal miss surface đúng + đề xuất update/DEC, KHÔNG auto-sửa spec (test GATE-NO-SILENT-REVERSAL).
- 5 viz render 3 format không vỡ; mọi field động escaped (test XSS-regression).
- `learning-map` join đúng outcomes + DEC từ audit trail.

---

## 8. Rủi ro

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Scope-creep thành BI | Light verdict + OUT-scope rõ; từ chối quadrant/clustering. |
| `--learn` ô dù làm 2 việc khó test | 2 path code TÁCH dưới 1 routing mỏng; test riêng từng path. |
| Viz mới → XSS regression | Escape discipline bắt buộc + test XSS như cycle-1. |
| Verdict phi-số (PO khai) mất deterministic | Chấp nhận có chủ đích (B3); chỉ phần số vào CI-gate. |
| Target chụp tại đo ≠ target gốc trong title | Note trong workflow: PO xác nhận target mỗi kỳ; title vẫn là prose tham chiếu. |

---

## 9. Next steps

1. `/ck:plan` — lập kế hoạch theo phase (gợi ý thứ tự: register+script số → viz scorecard → path B/discover-back → learning-map+dashboard → docs/backlog).
2. Cân nhắc `--tdd` cho `record_outcome.py` + GATE tests (logic deterministic + ranh giới an toàn).

---

## 10. Open questions

- **Đơn vị/định dạng `actual` phi-số:** enum verdict PO khai có cần chuẩn hóa (`hit/partial/miss`) hay cho free-text? *(Khuyến nghị: enum đóng, đồng nhất với verdict số.)*
- **`measured_on` nhiều kỳ cùng goal:** outcome-trend cần ≥2 lần đo mới có nghĩa — có cần nhắc PO nhịp đo (tháng/quý)? *(Để workflow gợi ý, không ép.)*
- **Ngưỡng `partial`:** số → bao nhiêu % target thì `partial` vs `miss`? *(Cần chốt ở plan: vd ≥90% hit, 50–90% partial, <50% miss — hay PO cấu hình qua `preferences.py`.)*
