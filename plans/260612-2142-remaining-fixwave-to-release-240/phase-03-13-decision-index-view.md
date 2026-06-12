---
phase: 3
title: '#13 decision index view'
status: completed
priority: P2
effort: 0.5d
dependencies: []
---

# Phase 3: #13 decision index view (POX-F11)

## Overview
Presentation layer over the existing `decision_register.py` data (data layer exists since 1.1.0). Lets a PO ask
"which DEC governs PRD-X" via `--list --affects PRD-X`, rendering the supersede chain + a dashboard row. New
**sibling** `decision_register_view.py` (keep main file flat — it's at 401 LOC).

## Requirements
- Functional: `decision_register.py --list --affects PRD-X` → filter `parse_decisions()` by `affects==PRD-X`,
  render each DEC with its supersede chain (newest→older→superseded) + a dashboard row (id, status, date, title,
  chain). JSON output (consumed by viz `dashboard`/`--decision` surface).
- Non-functional: reuse `parse_decisions()`, `_title_from_body()`, `sanitize_rationale()`. Append-only data model
  unchanged. No new write path.

## Architecture
- New `decision_register_view.py`:
  - `filter_by_affects(records, artifact_id) -> List[Dict]`
  - `render_supersede_chain(dec_id, records) -> str` (follow `supersedes` links into an ordered chain)
  - `render_dashboard_row(dec_id, record, chain_str) -> Dict`
- `decision_register.py` main: add `--affects` arg to the existing `--list` branch; when present, dispatch to the
  view sibling and `json.dumps` the rows. (~10 LOC in main.)

## Related Code Files
- Create: `.claude/skills/product-spec/scripts/decision_register_view.py`
- Modify: `.claude/skills/product-spec/scripts/decision_register.py` (`--affects` flag + dispatch, ~10 LOC)
- Create: `.claude/skills/product-spec/scripts/tests/test_decision_register_view.py`
- (Optional) Modify: `visualize.py` dashboard to surface a DEC row — only if it stays a thin call into the view sibling.
- Modify: REVIEW.md (tick POX-F11), EVIDENCE.md, DEC

## TDD — tests first
1. `test_list_affects_returns_matching_set` — seed decisions.md with DECs affecting PRD-X / PRD-Y → `--affects PRD-X`
   returns exactly the PRD-X set.
2. `test_supersede_chain_order` — DEC-3 supersedes DEC-2 supersedes DEC-1 → chain rendered newest→oldest, correct order.
3. `test_dashboard_row_shape` — row dict has id/status/date/title/chain keys with expected values.
4. `test_affects_no_match_empty` (negative) — `--affects PRD-Z` with no DEC → empty list, exit 0, valid JSON.
5. `test_supersede_cycle_terminates` (negative, red-team L1) — `supersedes: DEC-self` / mutual cycle → visited-set
   guard terminates, no infinite loop.
6. `test_dangling_supersedes_renders_broken_link` (negative) — `supersedes: DEC-999` (missing) → rendered as a
   broken-link note, no crash.
Fixtures via existing `_seed()`/`_record()` helpers.

## Implementation Steps
1. Write 4 RED tests.
2. Implement view sibling (3 functions).
3. Wire `--affects` into `decision_register.py --list`.
4. GREEN; product-spec suite + CONTRIBUTING:69.
5. Tick POX-F11; DEC + EVIDENCE.

## Success Criteria
- [ ] 6 tests green incl. empty-match + cycle + dangling-supersedes negatives.
- [ ] `--list --affects PRD-X` returns correct set + ordered supersede chain + dashboard row.
- [ ] main file grows ≤~10 LOC (logic in sibling).
- [ ] POX-F11 ticked; DEC + EVIDENCE.

## Risk Assessment
- Supersede cycle / dangling `supersedes` → guard against loops (visited-set), tolerate missing target (render as broken-link note).
- Low blast radius (read-only presentation).
