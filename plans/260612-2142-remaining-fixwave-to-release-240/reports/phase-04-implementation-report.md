# Phase 4 Implementation Report — #6 Visuals Latest-Alias, Staleness Banner, Content-Hash Reuse, Clean Retention

## Phase
- Phase: phase-04-6-visuals-latest-staleness-retention
- Plan: plans/260612-2142-remaining-fixwave-to-release-240/
- Status: completed
- Commit: c8d2d32

## Files Modified

| File | Change |
|---|---|
| `.claude/skills/product-spec/scripts/visuals_retention.py` | NEW — 130 exec-LOC sibling |
| `.claude/skills/product-spec/scripts/tests/test_visuals_retention.py` | NEW — 6 tests |
| `.claude/skills/product-spec/scripts/render_html.py` | +20 LOC wiring in `write()` |
| `.claude/skills/product-spec/scripts/visualize.py` | +16 LOC: `import`, `--clean` arg + dispatch |
| `docs/audit-trail/REVIEW.md` | POX-F04 row ticked [x] |
| `docs/audit-trail/EVIDENCE.md` | EVIDENCE P4-6 appended |
| `docs/product/decisions.md` | DEC-2 appended |

## Tasks Completed

- [x] 6 RED tests written first (confirmed: `ModuleNotFoundError` collection fail)
- [x] `visuals_retention.py` implemented (`latest_alias`, `staleness_banner`, `save_render_signature`, `content_hash`, `record_content_hash`, `reuse_if_unchanged`, `clean_old_renders`)
- [x] `render_html.write` wired: reuse check → skip if identical; after fresh write → alias + hash + signature
- [x] `visualize.py` wired: `import visuals_retention`, `--clean` argparse flag, early dispatch returning JSON list of deleted paths
- [x] 6 tests GREEN
- [x] Full product-spec suite: 747 passed, 1 pre-existing failure (`test_dogfood_state_untracked`)
- [x] CONTRIBUTING:69 suite: 219 passed, 0 failed
- [x] POX-F04 ticked in REVIEW.md
- [x] EVIDENCE P4-6 appended
- [x] DEC-2 recorded in decisions.md

## Test Names and Count

6 tests in `tests/test_visuals_retention.py`:

1. `test_latest_alias_points_to_newest_render`
2. `test_staleness_banner_when_graph_drifts`
3. `test_no_banner_when_in_sync` (negative)
4. `test_content_hash_reuse_skips_rerender`
5. `test_clean_prunes_old_keeps_latest`
6. `test_clean_on_empty_dir_no_crash` (negative)

## Tests Status

- Retention tests: 6 passed
- Product-spec suite: 747 passed, 1 failed (pre-existing `test_dogfood_state_untracked` — allowed)
- CONTRIBUTING:69 gate: 219 passed

## Retention keep-N chosen

`RETENTION_KEEP = 5` — keep 5 most recent timestamped renders per view. Rationale: enough history for audit trail (5 prior renders), prevents unbounded accumulation. Constant lives at a single source in `visuals_retention.RETENTION_KEEP`. DEC-2 records the choice and reasoning.

## Issues Encountered

None. Clean implementation — sibling pattern matched existing codebase convention (`check_consistency_schema.py`, `decision_register_view.py`). Alias uses `shutil.copy2` (copy-based, not symlink) for filesystem portability.

## Architecture Notes

- `render_html.write` imports `visuals_retention` lazily (inside the function body) to avoid any circular-import risk at module-load time.
- Missing sidecar → treated as "changed" (safe default: forces fresh render).
- `--clean` dispatch exits 0 with JSON `{"cleaned": [...]}` before any graph-build or render, so it works without a full spec tree.
- `staleness_banner` returns `""` when no baseline signature exists (treat as fresh, not stale).
