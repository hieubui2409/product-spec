---
phase: 5
title: "learning-map + dashboard (C9)"
status: done
priority: P2
effort: "1d"
dependencies: [1, 4]
---

# Phase 5: learning-map + dashboard (C9)

## Overview

`learning-map` (flow insight/outcome → node spec → `DEC-<n>` → thay đổi) bằng cách mở rộng
`assemble_audit_trail.py` (C9, DRY) + `learning` dashboard gộp HTML-only (scorecard+trend+gap+link map).

## Requirements

- Functional:
  - Mở rộng `assemble_audit_trail.py`: thêm nguồn `outcomes.md` vào trail. **Map vào 6 key SẴN CÓ
    (red-team #3 — KHÔNG thêm cột, KHÔNG bump schema):** `date=measured_on`, `artifact=goal`,
    `action="outcome: <verdict>"`, `what_drifted="target X / actual Y (metric)"`, `dec_ref=` ruling nếu có,
    `reconciled` theo lệ. `_rows`/render_ascii/render_markdown KHÔNG đổi → `audit` view back-compat nguyên.
  - **`learning-map`** view: flow outcome/insight → goal/node bị chạm → `DEC-<n>` → thay đổi spec.
    Format mermaid (flow) + html; ascii downgrade text-summary.
  - **`learning`** view: dashboard HTML-only (như `dashboard`), compose scorecard + trend + gap + link learning-map.
  - `learning-map` + `learning` vào `visualize.py` (HTML_ONLY cho `learning`; mermaid/html cho `learning-map`).
- Non-functional: escape discipline; reuse loader Phase 4 (`load_outcomes`) + audit assembler (no dup); LOC<200/file.

## Architecture

```
assemble_audit_trail.assemble() += outcomes source ─► rows {when, artifact, action, outcome, DEC}
visualize.py:
  learning-map ─► render_mermaid.learning_map(trail) / render_html
  learning     ─► render_html.learning_dashboard(load_outcomes + scorecard/gap/trend frags)  [HTML_ONLY]
```

## Related Code Files

- Modify: `.claude/skills/product-spec/scripts/assemble_audit_trail.py` (+nguồn outcomes; giữ API cũ)
- Modify: `visualize.py` (`VIEWS`+=learning-map; `HTML_ONLY_VIEWS`+=learning; dispatch)
- Modify: `render_mermaid.py` (learning_map flow) + `render_html.py` (learning_map + learning_dashboard)
- Reuse: `load_outcomes.py` (P4), frags scorecard/gap/trend (P4)
- Modify: `scripts/tests/test_outcome_viz.py` hoặc thêm `test_learning_map.py`

## Implementation Steps (TDD)

1. **Test trước:**
   - `assemble_audit_trail` với outcomes → trail chứa outcome events map vào 6 key cũ + ref DEC; `schema_version` GIỮ "1.0".
   - **Back-compat 2 chiều (red-team #3):** (a) không outcomes → output byte cũ nguyên; (b) CÓ outcomes → `audit` view (`_rows`) vẫn render đúng 6 cột, không vỡ.
   - learning-map mermaid: outcome→goal→DEC tạo node/edge đúng; escape nhãn (mermaid injection).
   - learning dashboard html: chứa cả 3 frag + link map; escape; fail-closed.
2. Mở rộng assembler (giữ API `assemble/since_last_approved`).
3. render learning-map (mermaid+html) + learning dashboard (compose).
4. Wire visualize.py.

## Success Criteria

- [ ] `--viz learning-map` + `--viz learning` render đúng; back-compat audit trail giữ nguyên khi không có outcomes.
- [ ] learning-map join outcome→DEC từ audit trail (DRY, không assembler mới).
- [ ] Test escape cho cả 2 view.
- [ ] LOC<200/file.

## Risk Assessment

- **Phá back-compat audit-trail** → test snapshot output cũ khi outcomes rỗng.
- **Dashboard gộp phình HTML** → compose từ frag P4, không viết lại render.
- **Mermaid escape** → escape nhãn node (mermaid injection); theo pattern render_mermaid hiện tại.
