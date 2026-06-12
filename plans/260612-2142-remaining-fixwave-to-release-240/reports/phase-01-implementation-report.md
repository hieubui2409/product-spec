# Phase 1 Implementation Report — #9ab subsystem-horizon + persona-portrait rules

## Status: DONE

## Files Modified/Created

| File | Change |
|------|--------|
| `.claude/skills/product-spec/scripts/check_consistency_product.py` | NEW — 2 functions: `check_product_subsystems`, `check_persona_portraits` |
| `.claude/skills/product-spec/scripts/tests/test_check_consistency_product.py` | NEW — 6 tests |
| `.claude/skills/product-spec/scripts/check_consistency.py` | +5 lines: import block + 2 dispatch calls + 1 `_root` binding |
| `docs/audit-trail/REVIEW.md` | Appended P1-9ab section with 2 `[x]` rows |
| `docs/audit-trail/EVIDENCE.md` | Appended P1-9ab before/after entry |
| `plans/260612-2142-remaining-fixwave-to-release-240/phase-01-*.md` | Status → done; DEC-P1-1/2 added; success criteria ticked |

## Tests

| Test | Behavior | Result |
|------|----------|--------|
| `test_subsystem_horizon_mismatch_warns` | PAYMENT table=later vs PRD horizon=now → 1 WARN | PASS |
| `test_subsystem_horizon_aligned_clean` | All rows match → 0 findings | PASS |
| `test_malformed_subsystem_table_no_crash` | No table in body → [] no exception | PASS |
| `test_subsystem_no_horizon_column_no_crash` | Table without Horizon column → [] | PASS |
| `test_persona_in_frontmatter_without_body_warns` | Persona CSKH, no body heading → WARN | PASS |
| `test_persona_with_body_portrait_clean` | Persona has matching ## heading → 0 findings | PASS |

**Product-spec suite:** 728 passed, 1 failed (pre-existing `test_dogfood_state_untracked` — confirmed red before this phase via `git stash` baseline).

**CONTRIBUTING.md:69 gate:** 219 passed (telemetry + hooks + _shared).

## Commit Hash

See git log after commit.

## Decisions

- DEC-P1-1: Table parser keyed by ID column, fail-soft, tolerates column reorder.
- DEC-P1-2: Portrait check is heading-based + conservative (absent-only, no false positives on prose mentions).
