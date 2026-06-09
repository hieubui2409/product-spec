---
phase: 1
title: "Outcome register + record script"
status: done
priority: P1
effort: "1d"
dependencies: []
---

# Phase 1: Outcome register + record script

## Overview

Xương sống định lượng: register `outcomes.md` (append-only, `OUT-<n>`) + `record_outcome.py`
(append + tính verdict số theo `direction`). Không đụng schema goal. TDD.

## Requirements

- Functional:
  - **Storage = per-outcome fenced record block** (mẫu `decisions.md`/`decision-record.md`, KHÔNG phải
    `outcomes:` list-of-dicts). Lý do (red-team #1): `decision_register.py` append bằng **text concat**
    + regex `_RECORD_RE` (không YAML round-trip toàn file) → giữ "append-only, record cũ byte-unchanged"
    + không phá prose/comment trong `note`. Mỗi record mang field: `id`(OUT-<n>), `goal`(ref BRD-G<n>),
    `metric`, `target`(num|str), `actual`(num|str), `unit`, `direction`(higher|lower, default higher),
    `measured_on`(ISO date), `source`(nhãn), `verdict`(hit|partial|miss), `note`. Loader (Phase 4) iterate
    block (không parse frontmatter YAML) — đúng pattern register sẵn có.
  - `record_outcome.py` CLI mẫu `decision_register.py`: `--root`, `--alloc-id`, `--append`,
    `--append-alloc` (alloc+append trong 1 critical section atomic, reuse `_register_lock`), `--list`. Args dòng:
    `--goal --metric --target --actual --unit --direction --source --measured-on --verdict --note`.
  - **Verdict số (deterministic, 3-tier — KHỚP brainstorm OQ#3, red-team #2):** `higher` → ratio=actual/target;
    `lower` → ratio=target/actual. `ratio≥hit_floor`→hit · `partial_floor≤ratio<hit_floor`→partial · `<partial_floor`→miss.
    Mặc định `hit_floor=0.9`, `partial_floor=0.5`, **đọc override từ `preferences.py`** (key
    `outcome_hit_floor`/`outcome_partial_floor`) — **làm NGAY phase này** (validate decision: PO config được).
    Bad value (partial≥hit, ngoài [0,1]) → exit non-zero, không ghi (theo lệ preferences.py).
  - **Hybrid (B3):** target/actual không parse được số (hoặc target=0/rỗng) → verdict KHÔNG auto-tính; bắt buộc
    `--verdict` do PO khai (enum đóng hit|partial|miss); thiếu → exit non-zero.
  - Validate ref: `goal` phải tồn tại trong `brd.md` goals (load qua frontmatter_parser); ref hỏng → exit non-zero.
  - **Validate metric slug (red-team #4):** `--metric` phải nằm trong `metrics:` của goal được ref; lệch →
    cảnh báo + chặn (tránh typo `gmv-yr1` vs `gmv-year1` làm phân mảnh scorecard/trend). Có thể `--force` ghi đè (ghi cảnh báo).
  - **Zero-actual luôn ghi OUT row** (red-team #6a): actual=0 là phép-đo thật (miss), KHÁC "chưa đo" (không có OUT). Path `--learn` không được skip ghi khi actual=0.
- Non-functional: stdlib+pyyaml; atomic write (tempfile+os.replace); idempotent re-run an toàn;
  JSON output; `<200 LOC` (modularize nếu vượt).

## Architecture

```
record_outcome.py
  load brd goals (frontmatter_parser) ──► validate goal ref + metric ∈ goal.metrics
  parse target/actual ──► numeric & target≠0 ? ──yes─► compute_verdict(direction, target, actual, hit_floor, partial_floor)
                                              └─no──► require --verdict (PO-asserted)
  alloc OUT-<n> (scan blocks via _RECORD_RE) ──► render record block ──► text-append (atomic, locked)
```

Verdict math tách hàm thuần `compute_verdict()` (dễ test, không I/O). Append = text-concat 1 block mới
(KHÔNG re-serialize toàn file) → record cũ byte-unchanged.

## Related Code Files

- Create: `.claude/skills/product-spec/scripts/record_outcome.py`
- Create: `.claude/skills/product-spec/assets/templates/outcomes.md` (record-block format mẫu `decision-record.md`)
- Create: `.claude/skills/product-spec/scripts/tests/test_record_outcome.py`
- Modify: `.claude/skills/product-spec/references/frontmatter-and-id-spec.md` (thêm `OUT-<n>` grammar + outcome-record fields + `direction`)
- Study mẫu: `decision_register.py` (`_RECORD_RE`, `_register_lock`, `append_alloc`, `_render_record`), `assets/templates/decision-record.md`
- Modify: `preferences.py` (thêm key `outcome_hit_floor`/`outcome_partial_floor` vào allowed-keys + validate enum/range; load→merge→save giữ nguyên)
- Reuse (no edit): `frontmatter_parser.py`, `fs_guard.py`, `encoding_utils.py`

## Implementation Steps (TDD)

1. **Test trước** — `test_record_outcome.py`:
   - `compute_verdict` higher: ratio≥0.9→hit; 0.5≤r<0.9→partial; <0.5→miss (boundary 85%→partial, KHỚP brainstorm).
   - `compute_verdict` lower (latency): ratio=target/actual; actual≤target→hit; ngược lại partial/miss đúng chiều.
   - Hybrid: target phi-số HOẶC target=0 + thiếu `--verdict` → non-zero; có `--verdict` → ghi đúng (không chia 0).
   - Ref goal không tồn tại → non-zero. **Metric không ∈ goal.metrics → cảnh báo + chặn; `--force` → ghi + cảnh báo.**
   - `--append-alloc` cấp OUT id tăng dần (scan blocks), không trùng; atomic; record CŨ byte-unchanged sau append.
   - **Same goal+metric+measured_on 2 lần (red-team #5):** cả 2 ghi (id khác); ghi rõ "latest = id lớn nhất" cho Phase 4.
   - actual=0 → vẫn ghi OUT row (verdict miss), không skip.
   - **Threshold config (validate Q1):** preferences override `outcome_hit_floor=0.95` → verdict đổi đúng theo override; bad value (partial≥hit / ngoài [0,1]) → non-zero, không ghi.
2. `compute_verdict()` thuần → pass test math.
3. CLI alloc/append/append-alloc/list + atomic text-append (block model) → pass.
4. Goal-ref + metric-slug validation → pass.
5. Template `outcomes.md` (record-block format mẫu `decision-record.md`) + cập nhật frontmatter spec.

## Success Criteria

- [ ] Tests đỏ trước, xanh sau (math 3-tier + hybrid + goal-ref + metric-slug + atomic block-append + same-date + actual=0).
- [ ] `record_outcome.py --append-alloc …` ghi OUT record block hợp lệ; `--list` đọc lại đúng; record cũ byte-unchanged.
- [ ] Verdict số deterministic 2 chiều 3-tier; phi-số/target=0 bắt PO khai; ngưỡng override qua preferences.py (bad value chặn).
- [ ] `outcomes.md` parse pass; goal-ref + metric-slug lệch bị chặn (force ghi đè + cảnh báo).
- [ ] LOC < 200/ file (modularize nếu cần).

## Risk Assessment

- **Storage model lẫn (red-team #1)** → CHỐT per-outcome fenced block (text-append), KHÔNG list-of-dicts.
- **Ngưỡng verdict (red-team #2 / validate Q1)** → 3-tier default 0.9/0.5, override qua `preferences.py`; bad value bị chặn.
- **Chia 0 / target rỗng** → guard: coi như phi-số, require PO verdict.
- **Metric typo phân mảnh trend (red-team #4)** → validate slug ∈ goal.metrics.
- **`direction` sai mặc định** → default `higher` + test `lower` rõ; doc trong template.
