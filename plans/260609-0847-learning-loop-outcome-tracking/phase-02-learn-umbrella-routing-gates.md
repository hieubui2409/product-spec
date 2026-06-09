---
phase: 2
title: "--learn umbrella routing + GATEs"
status: done
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 2: --learn umbrella routing + GATEs

## Overview

Mode ô dù `--learn`: vào → hỏi "số liệu hay phản hồi?" → route. Phase này wire **path số liệu**
(dùng `record_outcome.py` Phase 1) + 2 GATE an toàn. Path phản hồi để Phase 3.

## Requirements

- Functional:
  - Flag `--learn` trong SKILL.md (bảng flag + no-flag menu mục "Học từ thực tế / Learn from reality").
  - Routing ô dù: AskUserQuestion "Số liệu (outcomes) hay Phản hồi (feedback)?" → 2 path code TÁCH.
  - **Path số liệu:** với mỗi `BRD-G<n>` đang `approved`/`review`, hỏi target/actual/unit/direction/source/measured_on
    → gọi `record_outcome.py --append-alloc`.
  - **Target suggestion (validate Q3):** LLM đọc goal `title` (vd "Onboard 100 brands") → **đề xuất** target số
    cho PO confirm/sửa. Vẫn **GATE-NEVER-ASSUME**: chỉ là gợi ý, PO chốt; không tự ghi target khi PO chưa xác nhận.
  - **GATE-NO-SILENT-REVERSAL:** goal `approved` mà verdict=miss → KHÔNG auto-sửa spec/goal. Surface
    "goal X trượt" + đề xuất 3 nhánh: giữ goal / đổi goal (→`--update`, re-approve owner+date) / mở `DEC-<n>`.
    Đổi goal `approved` PHẢI qua re-approval tường minh.
  - **GATE-NEVER-ASSUME:** không tự gán target/verdict; thiếu dữ liệu → hỏi, không đoán.
  - `references/workflow-learn.md` (mới): mô tả luồng 2 path + GATEs + load-on-demand theo flag.
- Non-functional: bilingual EN/VI; PO-facing (không jargon); load `workflow-learn.md` chỉ khi `--learn`.

## Architecture

```
--learn ──► AskUserQuestion {outcomes|feedback}
   ├─ outcomes ─► per goal: LLM suggest target từ title ─► PO confirm ─► collect actual/… ─► record_outcome.py ─► verdict
   │                miss & approved? ─► GATE-NO-SILENT-REVERSAL surface (keep/change/DEC)
   └─ feedback ─► (Phase 3)
```

## Related Code Files

- Create: `.claude/skills/product-spec/references/workflow-learn.md`
- Modify: `.claude/skills/product-spec/SKILL.md` (flag `--learn`, no-flag menu, Loads references-on-demand list)
- Reuse: `record_outcome.py` (P1), `decision_register.py` (`--append-alloc` cho DEC), `guardrails-and-boundaries.md` (GATE refs)

## Implementation Steps (TDD)

1. **Test trước** — kịch bản GATE (script-checkable phần deterministic):
   - Goal approved + verdict miss → `record_outcome.py` chỉ ghi outcomes.md, `brd.md` byte-unchanged (invariant; thành thật: đây là invariant ghi-tách-biệt, KHÔNG phải bằng chứng GATE — enforcement GATE thực nằm ở eval Phase 6, red-team #8).
   - Đổi goal → đi qua `--update`/re-approve path (record owner+date), không flip status ngầm.
   - (LLM-routing + GATE surfacing "Keep/Change/DEC": eval Phase 6, không unit-test được.)
   - **Cadence nudge (red-team #7):** workflow-learn.md PHẢI chứa gợi ý nhịp đo lặp (trend cần ≥2 lần đo mới có nghĩa) — kiểm bằng success criterion bên dưới.
2. Viết `workflow-learn.md` (path A đầy đủ; path B stub trỏ Phase 3).
3. Cập nhật SKILL.md flag + menu.
4. Đảm bảo record outcome KHÔNG chạm artifact goal (chỉ ghi outcomes.md) — test invariant.

## Success Criteria

- [ ] `--learn` xuất hiện ở SKILL.md flag table + no-flag menu, bilingual.
- [ ] Path số liệu chạy: thu thập → `record_outcome.py` → outcomes.md.
- [ ] Test: miss trên goal approved KHÔNG sửa `brd.md` (invariant ghi-tách-biệt; GATE thực ở eval Phase 6).
- [ ] `workflow-learn.md` mô tả 2 path + GATEs + **gợi ý nhịp đo lặp (cadence)**, load-on-demand.

## Risk Assessment

- **Ô dù làm 2 việc khó test** → 2 path code tách dưới routing mỏng; test invariant deterministic, phần LLM để eval.
- **GATE bị bỏ khi đổi goal** → bắt buộc re-approval owner+date qua `--update`; test status không flip ngầm.
