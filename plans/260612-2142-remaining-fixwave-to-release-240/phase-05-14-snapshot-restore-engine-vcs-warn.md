---
phase: 5
title: '#14 snapshot-restore engine + VCS warn'
status: completed
priority: P2
effort: 1.5-2d
dependencies: []
---

# Phase 5: #14 snapshot-restore engine + VCS warn (POX-F10/CVR-M2)

## Overview
Full `--snapshot`/`--restore <ts>` engine (owner chose engine over nudge-only) + a VCS-warn surfaced in
`--status`/validate. Replaces the PO's hand `cp` backups (which leaked 88 tracked `*.bak-*` files to GitHub).
New `snapshot.py` module; VCS check via new `status_vcs.py` sibling (keep `status.py` near budget, 321 LOC).

> **Red-team H2 — snapshot is OPT-IN only for 2.4.0.** The original plan wired an auto-snapshot call INTO the
> P2 migrator files, creating a hidden P2/P5 file collision. Dropped: 2.4.0 ships explicit `--snapshot`/`--restore`
> only. The "auto-snapshot before migration/large-update" convenience hook is **deferred** (filed as DEC) — it
> can be added later in the phase that owns the migrator. P5 touches NO P2 files.

## Requirements
- Functional: `--snapshot` → timestamped copy of `docs/product` into a snapshot dir + a README; auto-snapshot before
  migration/large update; `--restore <ts>` → restore that snapshot (staging→swap, never partial). `status.py`/validate
  warn when `docs/product` is outside a git work-tree OR has a large uncommitted diff; commit nudge after approve.
- Non-functional: snapshots never overwrite (timestamped dirs); restore atomic; VCS warn fail-soft (no git → single warn,
  not crash). Snapshot dir gitignored (don't repeat the 88-file leak).

## Architecture
- New `snapshot.py`:
  - `make_snapshot(root, label=None) -> Path` (copy `docs/product` → `<root>/.snapshots/<ts>[-label]/` + README.md)
  - `restore_snapshot(root, ts) -> None` (validate ts exists → copy to staging → atomic swap of `docs/product`)
  - `list_snapshots(root) -> List[str]`
  - (deferred) auto-hook into migrators — NOT in 2.4.0 (see red-team H2 note above); snapshot is invoked
    explicitly via `--snapshot` only this round.
- New `status_vcs.py`:
  - `vcs_warnings(root) -> List[Dict]` using the `reflect_scan._is_git_work_tree` pattern (`git rev-parse
    --is-inside-work-tree`) + `git diff --name-only docs/product/` for large-diff detection (threshold = hard file count).
- `status.py`: add `"vcs_warnings": status_vcs.vcs_warnings(root)` to both baseline + no-baseline return branches
  (re-read current build_status first — age-beacon/open-questions/reflect already there; don't clobber).
- Ensure `.snapshots/` added to the product gitignore.

## Related Code Files
- Create: `.claude/skills/product-spec/scripts/snapshot.py`
- Create: `.claude/skills/product-spec/scripts/status_vcs.py`
- Modify: `.claude/skills/product-spec/scripts/status.py` (one key in 2 branches — re-read first)
- Modify: gitignore template / product gitignore (add `.snapshots/`)
- Create: tests `test_snapshot.py`, `test_status_vcs.py`
- Modify: REVIEW.md (tick POX-F10), EVIDENCE.md, DEC

## TDD — tests first
1. `test_snapshot_creates_dir_and_readme` — `make_snapshot` → `.snapshots/<ts>/` exists w/ README + copied tree.
2. `test_snapshot_never_overwrites` (negative) — two snapshots → two distinct ts dirs, first intact.
3. `test_restore_roundtrip` — snapshot, mutate, restore → tree matches snapshot byte-for-byte.
4. `test_restore_unknown_ts_errors_tree_intact` (negative) — bad ts → error, live tree unchanged.
5. `test_vcs_warn_outside_git` — non-git tmp tree → exactly one "outside git" warning.
6. `test_vcs_warn_large_uncommitted_diff` — git tree w/ N changed files over threshold → warning w/ count.
7. `test_vcs_clean_tree_no_warn` (negative) — committed clean tree → 0 warnings.
Fixtures: conftest `make_proj(git=True/False)`.

## Implementation Steps
1. Write 7 RED tests.
2. Implement `snapshot.py` (make/restore/list, atomic swap).
3. Implement `status_vcs.py`; wire one key into `status.py` (re-read build_status first).
4. Add `.snapshots/` to gitignore. (Auto-snapshot-into-migrator hook DEFERRED — not 2.4.0; record DEC.)
5. GREEN; product-spec suite + CONTRIBUTING:69.
6. Tick POX-F10; DEC + EVIDENCE.

## Success Criteria
- [ ] 7 tests green incl. 3 negatives.
- [ ] snapshot timestamped+README, never overwrites; restore atomic + round-trips; bad-ts safe.
- [ ] VCS warn fires outside-git + large-diff, silent on clean tree.
- [ ] `.snapshots/` gitignored; `status.py` grows only the one key.
- [ ] POX-F10 ticked; DEC + EVIDENCE.

## Risk Assessment
- Restore clobbers live tree mid-copy → staging dir + atomic swap; bad-ts test asserts tree intact.
- Snapshot blowup / re-leak to git → `.snapshots/` gitignored; document retention; reuse `--clean`-style pruning if needed (DEC if added).
- git shell-out on non-repo → `_is_git_work_tree` guard, fail-soft single warn.
