---
phase: 4
title: "Viz scorecard+gap+trend"
status: done
priority: P2
effort: "1.5d"
dependencies: [1]
---

# Phase 4: Viz scorecard+gap+trend

## Overview

3 view deterministic cho PO non-tech đọc outcomes: `scorecard` (headline, +blind-spot),
`insight-gap` (delta bars), `outcome-trend` (heatmap goal×kỳ). Escape discipline bắt buộc.

## Requirements

- Functional:
  - Loader: đọc `outcomes.md` (iterate record block) + `brd.md` goals → {goal, latest outcome, history}.
    `latest` = OUT id lớn nhất khi trùng goal+metric+date (red-team #5). Tách hàm `load_outcomes()` (reuse Phase 5).
    **Orphan ref (red-team #5b):** OUT trỏ goal đã xóa/đổi tên → render "goal đã gỡ", KHÔNG crash/drop âm thầm.
  - **`scorecard`** — mỗi goal: target vs actual + badge hit🟢/partial🟡/miss🔴 + xu hướng vs lần trước.
    Goal KHÔNG có OUT = ô xám "chưa đo / blind spot". **actual=0 = miss🔴 (KHÁC chưa đo)** — phân biệt bằng "có OUT row hay không", không bằng giá trị (red-team #6a).
  - **`insight-gap`** — thanh gap chuẩn hóa/goal, xếp giảm dần. **Công thức (red-team #6b):**
    higher → `gap=max(0,(target−actual)/target)`; lower → `gap=max(0,(actual−target)/target)`. Clamp≥0 → goal VƯỢT target gap=0 (không âm, không lên đầu danh sách).
  - **`outcome-trend`** — heatmap hàng=goal, cột=`measured_on`, ô=màu verdict. Cần **adapter `to_heatmap_graph()`**
    (red-team #9): outcomes → dict shape mà `render_*.heatmap` đang nhận (KHÔNG sửa heatmap renderer); verdict→màu là map mới.
  - Format: ascii (default) + html; mermaid downgrade về ascii nếu không biểu diễn được (theo pattern hiện tại).
- Non-functional: **escape mọi field động server-side** (verdict/note/source/title) trước khi vào HTML;
  body qua DOMPurify; fail-closed text. bilingual labels qua `i18n_labels.py`. LOC<200/file.

## Architecture

```
visualize.py: VIEWS += ("scorecard","insight-gap","outcome-trend")
  load_outcomes(root) ─► graph-like dict ─► render_ascii.* / render_html.* / (heatmap reuse)
HTML_DEFAULT cho scorecard (như dashboard-ish card); ascii default cho gap/trend.
```

## Related Code Files

- Modify: `.claude/skills/product-spec/scripts/visualize.py` (`VIEWS`, dispatch, HTML defaults)
- Create: `.claude/skills/product-spec/scripts/load_outcomes.py` (loader chung; tránh nhồi visualize.py >200 LOC)
- Modify: `render_ascii.py` (scorecard/gap ascii + reuse heatmap cho trend)
- Modify: `render_html.py` (scorecard cards + gap bars; escape chokepoint)
- Modify: `i18n_labels.py` (labels mới: hit/partial/miss/chưa-đo/gap/trend EN+VI)
- Create: `scripts/tests/test_outcome_viz.py`

## Implementation Steps (TDD)

1. **Test trước** — `test_outcome_viz.py`:
   - `load_outcomes` ghép latest(=id lớn nhất khi trùng date) + history đúng; goal không OUT → blind-spot; OUT orphan → "goal đã gỡ", không crash.
   - scorecard: badge đúng verdict; actual=0 → miss (KHÁC blind-spot); insight-gap xếp giảm dần đúng.
   - **gap formula:** lower-is-better VƯỢT target → gap=0 (không âm, không lên đầu); higher dưới target → gap dương đúng.
   - `to_heatmap_graph()` → render qua heatmap renderer SẴN CÓ không sửa; 2 kỳ đo → 2 cột; verdict→màu đúng.
   - **XSS-regression:** note/source chứa `<script>`/`"` → HTML output escaped (không raw payload). Mẫu test cycle-1.
2. `load_outcomes.py` → pass loader tests.
3. render ascii (scorecard/gap) + reuse heatmap (trend) → pass.
4. render html + escape → pass XSS test.
5. Wire vào `visualize.py` VIEWS + defaults.

## Success Criteria

- [ ] 3 view render ascii+html không vỡ; trend reuse heatmap.
- [ ] Blind-spot hiển thị cho goal chưa đo.
- [ ] Test XSS: mọi field động escaped (đỏ trước khi escape, xanh sau).
- [ ] bilingual labels; LOC<200/file (tách loader).

## Risk Assessment

- **XSS regression (viz là sink cũ)** → escape server-side + DOMPurify + test injection bắt buộc.
- **visualize.py phình** → tách `load_outcomes.py` riêng.
- **direction trong gap** → chuẩn hóa delta theo direction (lower-is-better không bị âm sai).
