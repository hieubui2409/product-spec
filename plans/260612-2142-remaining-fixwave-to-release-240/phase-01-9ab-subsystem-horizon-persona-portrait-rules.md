---
phase: 1
title: '#9ab subsystem-horizon + persona-portrait rules'
status: completed
priority: P2
effort: 0.75d
dependencies: []
---

# Phase 1: #9ab subsystem-horizon + persona-portrait rules

## Overview
Two new consistency rules catching real PO defects validate missed: (a) PRODUCT.md subsystem table
horizon disagreeing with the matching PRD's frontmatter `horizon` (POX-F02); (b) a persona named in
VISION/BRD frontmatter with no body portrait/heading (POX-F06, "DEC applied half-way"). New **sibling
module** `check_consistency_product.py` (matches existing `check_consistency_schema.py` pattern) — NOT a
rule-engine refactor.

## Requirements
- Functional: parse PRODUCT.md subsystem table **by ID** (not heading — brittle); for each subsystem with
  a horizon, compare vs the matching PRD node frontmatter `horizon`; mismatch → WARN finding. Collect personas
  from VISION/BRD frontmatter; if a persona has no `## <persona>` / `### <persona>` body heading → WARN.
- Non-functional: reuse `spec_graph.build_graph` (already loads PRODUCT node) + `frontmatter_parser.parse_file`;
  findings via `make_finding`/`spec_graph._f` (single home). Fail-soft: missing/garbled table → no crash, emit nothing.

## Architecture
- New `check_consistency_product.py`:
  - `check_product_subsystems(graph, root) -> List[Dict]` — parse PRODUCT.md body subsystem table, key by ID,
    compare row horizon vs PRD frontmatter horizon (lookup by ID in graph).
  - `check_persona_portraits(graph, root) -> List[Dict]` — personas from VISION/BRD frontmatter; scan each
    artifact body for matching heading; missing → warn.
- Wire both into `check_consistency.check()` dispatch tail (after `_check_competitors`, ~L215), same shape as
  existing graph-level checks.
- Severity: WARN (not error) — advisory, does not fail validate gate hard unless PO config says so.

## Related Code Files
- Create: `.claude/skills/product-spec/scripts/check_consistency_product.py`
- Modify: `.claude/skills/product-spec/scripts/check_consistency.py` (2 dispatch calls only — keep main near-flat)
- Create: `.claude/skills/product-spec/scripts/tests/test_check_consistency_product.py`
- Modify: `docs/audit-trail/REVIEW.md` (tick POX-F02, POX-F06 when landed) + `EVIDENCE.md`

## TDD — tests first
1. `test_subsystem_horizon_mismatch_warns` — fixture PRODUCT.md table row `PAYMENT … horizon: later` but PRD-PAYMENT
   frontmatter `horizon: now` → exactly one WARN naming PAYMENT.
2. `test_subsystem_horizon_aligned_clean` (negative/no-over-report) — all rows match PRD horizon → 0 findings.
3. `test_persona_in_frontmatter_without_body_warns` — VISION frontmatter persona `CSKH`, no `## CSKH` body → WARN.
4. `test_persona_with_body_portrait_clean` (negative) — persona present in body → 0 findings.
5. `test_malformed_subsystem_table_no_crash` (fail-soft) — garbled/no table → empty list, no exception.
Fixtures via `_scaffold()` (existing conftest style: minimal PRODUCT/BRD/PRD/VISION).

## Implementation Steps
1. Write the 5 RED tests (fail: rules absent).
2. Implement `check_consistency_product.py` (2 functions + table parser keyed by ID).
3. Wire 2 dispatch calls into `check_consistency.check()`.
4. GREEN; run product-spec suite + `CONTRIBUTING.md:69` suite.
5. Tick POX-F02/F06 in REVIEW.md; record DEC + EVIDENCE before/after.

## Success Criteria
- [x] 5 tests green incl. 2 negative + 1 fail-soft. (6 total: added extra no-horizon-column test.)
- [x] `check_consistency.py` grows only 2 dispatch lines (logic in sibling).
- [x] product-spec suite + CONTRIBUTING:69 suite green. (728 passed / 1 pre-existing; 219 gate passed.)
- [x] POX-F02, POX-F06 ticked; DEC + EVIDENCE recorded.

## Decisions (DEC-P1)

- **DEC-P1-1 — Table parser keyed by ID column (not heading position), fail-soft on no-table/missing-column.** The
  subsystem table may appear anywhere in PRODUCT.md body, columns may be reordered, and a horizon may be absent for
  a given row. Parser scans for the first table that has both `id` and `horizon` columns (case-insensitive); rows
  with an empty horizon are skipped; rows whose subsystem ID matches neither the bare ID nor the `PRD-<ID>` form are
  also skipped (traceability checker handles dangling refs). Fail-soft = return [] on any missing/garbled input,
  no exception. Owner: hieubt · 2026-06-12.
- **DEC-P1-2 — Persona portrait check is heading-based + conservative (absent-only).** Only warns when a persona
  appears in `personas:` frontmatter AND has NO `##`/`###` heading matching that persona text (case-insensitive) in
  the same artifact's body. A persona mentioned in prose (not a heading) is not flagged. This avoids false positives
  on prose-only portraits while still catching the most common defect (DEC applied half-way: persona listed but
  section never written). Owner: hieubt · 2026-06-12.

## Risk Assessment
- Markdown table parsing brittle → bind to **ID column**, tolerate column reorder/whitespace; fail-soft on no-match.
- False positives on personas referenced obliquely → match heading text case-insensitively; only warn when persona
  in frontmatter AND no heading at all (conservative).
