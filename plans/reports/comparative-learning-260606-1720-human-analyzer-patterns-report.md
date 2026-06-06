# Comparative Learning — human-analyzer → cleanmatic-skills

**Date:** 2026-06-06 · **Scope:** 3 authored skills (`product-spec`, `product-spec-critique`, `claude-pack`) vs `/home/hieubt/Documents/human-analyzer/` · **Type:** brainstorm / learning analysis (no implementation)

---

## 0. Context — đây là quan hệ học HAI CHIỀU

`human-analyzer` (HA) là **project con đã học ngược từ cleanmatic-skills (CM)**. Bằng chứng trong repo HA:

- `BACKLOG.md`: "17 patterns mined from cleanmatic (3-skill reference repo)" — tất cả 17 đã áp dụng.
- `STANDARDIZE.md`: mỗi entry = source file ở CM → pattern học → cách triển khai ở HA.
- Pattern HA copy từ CM: **judgment cache (content-hash), decision register, fs_guard (write-jail), eval harness, check_fence**.

**Hệ quả:** phần lõi script-tooling **CM là nguồn — CM sâu hơn**. Cái đáng học là những thứ HA **xây thêm trên nền đó** mà CM chưa có (chủ yếu là runtime observability + quality-gate learning + audit-trail artifact). HA cũng to hơn nhiều về domain (59 skill / 6 framework) nên một số pattern của họ **không scale xuống** repo 3-skill — phải lọc.

---

## 1. Ba phần verdict (đúng câu hỏi gốc)

### ① CM làm TỐT HƠN — KHÔNG nên học theo HA

| Mảng | CM (ta) | HA | Ghi chú |
|---|---|---|---|
| Script lõi cache/decision/guard | **Nguồn gốc, sâu hơn** — `judgment_cache.py` 24K, `decision_register.py` 17K, consistency tách module `competition/risk/time` | Bản adapt nông hơn | HA's STANDARDIZE.md xác nhận học từ CM |
| Versioning skill | **Đúng semver** — 2.2.0 / 1.2.0 / 0.2.0 + manifest 1.4.0 | Tất cả 59 skill kẹt `1.0.0`, không bump | Đừng bắt chước implicit-version |
| Release determinism | **Đã ship thật** — PAX, mtime=0, tag-triggered CI, SHA256 verify (claude-pack v1.4.0) | Script release tồn tại, **chưa từng chạy** | CM là reference cho HA về điểm này |
| CI từ đầu | per-skill matrix + cross-skill `bug_class` gate + release, có ngay | Manual cycle 1-10 rồi mới thêm CI → ORC-08 regression lọt 10 cycle | Đừng copy "cycle thủ công trước CI" |
| CHANGELOG | per-skill (granular) | gộp cả framework → mất lịch sử per-skill | Giữ per-skill |
| Đối tượng | Distribution thật (install.sh, INSTALLATION.md, THIRD_PARTY_NOTICES, vendored Mermaid/marked) | App domain private | Khác mục tiêu — đừng đổi định vị |
| Critique tách non-deterministic khỏi CI | `product-spec-critique` report-only, cố ý OUT khỏi reproducible gate | SANTA/COUNCIL trộn vào hook hơi sâu | Ranh giới của CM sạch hơn |

### ② HA có mà CM CHƯA có — ĐÁNG học (lọc theo giá trị/3-skill)

| # | Pattern HA | CM hiện trạng | Giá trị cho CM |
|---|---|---|---|
| L1 | **Telemetry JSONL append-only sinks** (`skill-invocations`, `framework-signals`, `error-sink`) | Có hooks nhưng **0 observability sink** | Cao — biết skill nào chạy/lỗi, đo adoption thật |
| L2 | **Context-budget gauge** (đọc transcript tail, WARN 70% / FORCE-isolate 85%) | Chỉ `usage-context-awareness.cjs` một phần | Trung bình — CM skill (render_html 56K, spec_graph 31K) dễ ngốn context |
| L3 | **EVIDENCE.md / REVIEW.md cycle audit-trail** (finding-ID · cause · fix · evidence, root-cause) | Có *rule* `review-audit-self-decision.md` + Decision Register, **thiếu artifact ledger** | Cao — khớp đúng rule sẵn có, chỉ thiếu chỗ ghi |
| L4 | **Navigation docs auto-gen** (`MODULES.md` dependency graph, `distilled-principles.md`) sinh từ frontmatter `metadata.dependencies` | Không có | Thấp cho 3 skill, **cao nếu** số script/ref tiếp tục phình (product-spec đã ~45 script) |
| L5 | **PreCompact delta-digest hook** (emit summary khi compaction) | Không có | Trung bình — phiên product-spec dài hay bị compact |
| L6 | **run_evals.py runnable harness** (chạy nửa deterministic, no API key) | Có `evals.json` specs nhưng dùng pytest làm runner, **không có harness đọc evals.json** | Trung bình — evals.json hiện gần như trang trí |
| L7 | **Full e2e synthetic pipeline fixture** (no-PII, chạy cả pipeline) | Có `examples/acme-shop` + per-feature fixtures, **chưa có 1 e2e chạy trọn skill** | Trung bình |
| L8 | **Quality-gate learning** (SANTA/COUNCIL multi-run weighted vote + `instinct-store`) | `product-spec-critique` 4-lens + consolidator + humanizer (sạch hơn, report-only) nhưng **không học qua thời gian** | Thấp/thử nghiệm — đừng vội, ranh giới CM đang sạch |

### ③ Anti-pattern — KHÔNG bê về

- **34 hooks / over-instrument** → blast radius lớn, fail-open = blind spot khi hook chết im. CM giữ hook tinh gọn.
- **Doc sprawl**: EVIDENCE.md 50K + REVIEW.md 80K + release-manifest.json 355K — quá nặng cho repo 3-skill. Học *pattern* audit-trail (L3) nhưng **giữ nhỏ**.
- **KG tier dở dang** (parked 7b-7i) — đừng mở mặt trận chưa đóng được.
- **Character resolution = `os.listdir`** (không registry) → typo/stale folder im lặng chạy sai data.
- **Config/settings không versioned** → không có rollback story.

---

## 2. Đào sâu theo 4 lens

### Lens A — Observability / Telemetry (gap rõ nhất của CM)
HA: hooks ghi JSONL append-only vào `.claude/telemetry/*.jsonl` (invocation, signal, error, context-gauge, instinct). `cre:skill-analytics` đọc lại (test 642 LOC). CM: có hook nhưng không sink → **không biết** skill có được dùng không, lỗi ở đâu, cache hit-rate bao nhiêu. → **L1 + L2**.

### Lens B — Quality-gate architecture
HA: SANTA (5-persona veto) + COUNCIL (weighted vote nhiều run) + `instinct-store` học verdict. CM: `product-spec-critique` đã là analog **sạch hơn** (4 lens read-only subagent + consolidator + humanizer, không edit, OUT khỏi CI). CM **không thua** về kiến trúc; chỉ thiếu *learning loop* (L8 — thử nghiệm, ưu tiên thấp, rủi ro làm bẩn ranh giới). HA mạnh hơn ở **audit-trail của fix** (L3) — đây mới là thứ nên lấy.

### Lens C — Docs discipline
HA: tách `CLAUDE.md` (lean, mọi session) khỏi `GOAL.md` (state động <4000 chars) + nav-docs auto-gen + cycle audit-trail. CM: CLAUDE.md đã lean tốt; thiếu (a) nav/dependency view (L4 — thấp ở 3 skill) (b) cycle audit-trail (L3 — cao). **Đừng** copy doc-sprawl.

### Lens D — CI / Release / Eval
HA: deterministic-only gate (no API key) + skill-count==CLAUDE.md check + schema-validate-all. CM: đã có matrix + bug_class + release determinism **ship thật** → CM **dẫn trước**. Bổ sung nhỏ: (a) gate "skill count / version đồng bộ" kiểu HA, (b) biến `evals.json` thành runnable (L6), (c) e2e trọn skill (L7).

---

## 3. Adoption Backlog (ưu tiên)

| ID | Pattern | Prio | Effort | Phụ thuộc | DoD tóm tắt |
|---|---|---|---|---|---|
| **A1** | Telemetry sink tối giản: hook ghi `skill-invocation` + `error-sink` JSONL (gitignored), 1 helper chung trong `_shared/` | **P0** | S | — | Mỗi lần chạy script skill → 1 dòng JSONL (ts, skill, flag, exit). Đọc được bằng `jq`. |
| **A2** | Cycle audit-trail artifact: 1 file `docs/product/review-log.md` (finding-ID · cause · fix · evidence:file\:line), nối Decision Register | **P0** | S | — | Mỗi fix review ghi 1 dòng root-cause; KHÔNG để phình kiểu REVIEW.md 80K. |
| **A3** | `run_evals.py` harness đọc `evals.json` chạy nửa deterministic, exit 0/1 | **P1** | M | A1 (tái dùng helper) | `evals.json` thành gate thật, chạy được local + CI no-API-key. |
| **A4** | CI invariant gate kiểu HA: skill version ↔ CHANGELOG ↔ manifest đồng bộ; fail nếu lệch | **P1** | S | — | PR đổi SKILL.md mà quên bump/CHANGELOG → CI đỏ. |
| **A5** | Context-budget gauge nâng cấp từ `usage-context-awareness.cjs`: WARN ngưỡng + emit telemetry | **P2** | M | A1 | Phiên dài cảnh báo trước khi compact; advisory-only, không block. |
| **A6** | e2e trọn skill từ `examples/acme-shop`: 1 script chạy init→validate→viz→export, assert artifact | **P2** | M | A3 | 1 lệnh dựng lại toàn pipeline trên fixture no-PII. |
| **A7** | PreCompact delta-digest hook (emit tóm tắt state trước compaction) | **P2** | M | A1 | Sau compact vẫn giữ context spec đang làm. |
| **A8** | Nav/dependency doc auto-gen (`MODULES.md` từ frontmatter) | **P3** | M | — | Chỉ làm nếu số script/ref tiếp tục phình. Hiện 3 skill → giá trị thấp. |
| **A9** | Quality-gate learning loop (instinct-store cho critique) | **P3** | L | — | **Hoãn** — rủi ro làm bẩn ranh giới report-only/non-deterministic. Chỉ thử khi có nhu cầu rõ. |

**Không làm (anti-pattern):** 34-hook sprawl · doc 50-80K · KG tier · listdir-resolution · gộp CHANGELOG.

---

## 4. Khuyến nghị thứ tự

1. **P0 trước (A1+A2)** — effort nhỏ, lấp đúng 2 gap thật (observability + audit-trail), khớp rule sẵn có. Mỗi cái 1 phase.
2. **P1 (A3+A4)** — siết eval/CI, tái dùng helper từ A1.
3. **P2 (A5-A7)** — observability nâng cao + e2e, khi P0/P1 ổn định.
4. **P3 (A8-A9)** — chỉ khi có trigger (phình script / nhu cầu learning).

---

## 5. Unresolved questions

1. Telemetry sink (A1): chấp nhận ghi file runtime trong repo distribution không? (gitignored, nhưng recipient có sink riêng?) — ảnh hưởng claude-pack safety catalog.
2. Audit-trail (A2): để ở `docs/product/` (per-project, theo PO spec) hay `plans/reports/` (per-dev)? Hai đối tượng khác nhau.
3. A3/A6: `evals.json` hiện có đang phản ánh đúng acceptance muốn gate, hay cần định nghĩa lại metric trước khi xây harness?
4. Có muốn mở `STANDARDIZE.md`-ngược (CM ghi lại pattern học từ HA) để khép vòng hai chiều không?
