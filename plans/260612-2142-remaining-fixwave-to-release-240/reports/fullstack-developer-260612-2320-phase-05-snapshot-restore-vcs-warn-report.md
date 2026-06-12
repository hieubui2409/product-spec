# Phase 5 Implementation Report — #14 snapshot/restore engine + VCS-warn

## Executed Phase
- Phase: phase-05-14-snapshot-restore-engine-vcs-warn
- Plan: plans/260612-2142-remaining-fixwave-to-release-240/
- Status: completed

## Files Modified

| File | Change | Lines |
|---|---|---|
| `.claude/skills/product-spec/scripts/snapshot.py` | NEW — full snapshot/restore engine | +344 |
| `.claude/skills/product-spec/scripts/status_vcs.py` | NEW — VCS-state warning checks | +129 |
| `.claude/skills/product-spec/scripts/tests/test_snapshot.py` | NEW — 7 TDD tests | +235 |
| `.claude/skills/product-spec/scripts/status.py` | WIRING — import + 1 key in 2 branches + CLI dispatch | +37 |
| `.gitignore` | ADD `.product-spec-snapshots/` entry | +4 |
| `docs/audit-trail/REVIEW.md` | TICK — POX-F10 row added and ticked | +15 |
| `docs/audit-trail/EVIDENCE.md` | APPEND — P5-14 before/after entry | +24 |
| `docs/product/decisions.md` | APPEND — DEC-3 | +15 |

## Tasks Completed

- [x] Write 7 RED tests (all failed for the right reason: ModuleNotFoundError)
- [x] Implement `snapshot.py`: make_snapshot / restore_snapshot / list_snapshots / latest_snapshot
- [x] Implement `status_vcs.py`: vcs_warnings with spec_tree_untracked + large_uncommitted_diff
- [x] Wire `status_vcs.vcs_warnings()` into `status.py` both return branches (1 import + 1 key each)
- [x] Wire `--snapshot`/`--restore`/`--list-snapshots` CLI dispatch into `status.py` main() (opt-in only)
- [x] Add `.product-spec-snapshots/` to `.gitignore`
- [x] Tick REVIEW.md POX-F10 row
- [x] Append EVIDENCE.md P5-14 entry
- [x] Append DEC-3 to docs/product/decisions.md
- [x] Commit: `a962648`

## Tests Status
- 7 new tests: ALL PASSED
- Full product-spec suite: **754 passed, 1 failed** (pre-existing `test_dogfood_state_untracked` — unchanged)
- CONTRIBUTING.md:69 gate (telemetry + hooks + _shared): **219 passed**
- Combined: **973 passed, 1 failed**

### Test names
1. `test_snapshot_captures_spec_tree` — make_snapshot → dir + README + copied artifacts
2. `test_snapshot_timestamped_distinct` — two injected ts → two distinct dirs, both intact
3. `test_restore_brings_back_snapshot` — snapshot, mutate/delete, restore → tree matches snapshot
4. `test_restore_refuses_dirty_without_confirm` — git dirty tree, confirm=False → RestoreDirtyError, live tree untouched
5. `test_vcs_warn_when_spec_tree_untracked` — non-git dir → spec_tree_untracked warning
6. `test_vcs_warn_large_uncommitted_diff` — 6 uncommitted files → warn; 1 file → no warn (both directions)
7. `test_snapshot_list_empty_no_crash` — absent snapshots home → empty list, no exception

## VCS Thresholds + Retention Chosen

- `LARGE_DIFF_FILE_COUNT = 5` (hard integer in `status_vcs.py`) — ≥5 uncommitted files in spec tree triggers `large_uncommitted_diff` warning
- Snapshot retention: no automatic pruning in 2.4.0 (each snapshot is a timestamped dir; user runs `--list` and deletes manually). Retention/clean helper deferred — recorded in DEC-3 as follow-up if needed.
- Snapshots home: `.product-spec-snapshots/` at project root (gitignored). Separate from `docs/product/visuals/.snapshots/` (which stores validate-baseline JSON graphs — different purpose).

## GATE H2 Confirmation — Snapshot Stayed OPT-IN

- **snapshot.py** has zero imports of any migrator file.
- **status.py** dispatch is behind `if args.snapshot or args.restore or args.list_snapshots:` — only reached on explicit flag.
- **migrate_backfill_ids.py** and **migrate_metric_to_metrics.py** were NOT touched (confirmed by `git diff HEAD^ -- .claude/skills/product-spec/scripts/migrate_*.py` → empty).
- Auto-before-migrate hook is deferred; DEC-3 records the rationale.

## Issues Encountered

- `_make_git_proj` helper in test used `proj.mkdir()` without `parents=True` — broke when pytest created a nested `tmp_path / "large"` subdir. Fixed immediately (test-scaffolding bug, not a behavioral issue).

## Commit
`a962648` — feat(product-spec): add opt-in snapshot/restore engine and VCS-state warnings in status

## Unresolved Questions
None.
