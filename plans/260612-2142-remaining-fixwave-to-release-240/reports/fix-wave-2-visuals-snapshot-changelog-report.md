# Fix Wave 2 — Visuals Banner, Snapshot Restore, Change-Log Dedup

Commit: f519009

---

## FIX 1 (CRITICAL): Staleness banner never injected into rendered HTML

**Bug:** `visuals_retention.staleness_banner()` was called nowhere in `render_html.write()`. The banner existed as a pure utility — computed, unit-tested in isolation, but never wired into the output file. Any page rendered while the graph had drifted silently showed no warning.

**Fix:** In `render_html.write()`, before assembling the final HTML, call `_vr.staleness_banner(root, view, graph)`. When the return value is non-empty (drift > 0), inject a yellow `<div>` banner immediately after `<body>`. The banner is injected into the `html` string before the content-hash reuse check, so drift forces a new file even when view_text is unchanged.

**Files:** `render_html.py` (+15 lines)

**Tests written first (TDD):**
- `test_rendered_html_contains_staleness_banner_on_drift` — renders 3-node baseline, re-renders 5-node graph; asserts `"stale —"` and `"2 nodes drifted"` appear in the written file bytes.
- `test_rendered_html_no_banner_when_in_sync` — same graph twice; asserts `"stale —"` absent.

Both were RED before the fix, GREEN after.

---

## FIX 2 (HIGH): Snapshot restore data-loss window + crash on absent spec_root

**Bugs:**
- (a) If `staging.rename(spec_root)` failed after `spec_root.rename(backup)` had already run, the original live tree was left in `_restore_backup_<ts>` and never restored. The `finally` block only cleaned staging.
- (b) When `spec_root` did not exist (primary recover-a-deleted-tree flow), `spec_root.rename(backup)` raised `FileNotFoundError`. The CLI only caught `RestoreDirtyError`/`SnapshotNotFoundError`, so users got a traceback on the most common recovery scenario.

**Fix:** In `restore_snapshot`:
1. Track `spec_root_existed = spec_root.exists()` before any rename.
2. Only `spec_root.rename(backup)` when `spec_root_existed` is True — absent tree skips to `staging.rename(spec_root)` directly.
3. Wrap in `except Exception:` block: if `spec_root` is missing and `backup` exists, call `backup.rename(spec_root)` (best-effort rollback) before re-raising. Net invariant: on failure the original tree is intact.

**Files:** `snapshot.py` (+20 lines)

**Tests written first (TDD):**
- `test_restore_into_deleted_tree_succeeds` — snapshot, `shutil.rmtree(spec_root)`, restore(confirm) → tree present, no exception.
- `test_restore_rolls_back_on_swap_failure` — monkeypatches `Path.rename` to raise on the 2nd call; asserts spec_root exists with original content after the error.
- `test_restore_unknown_ts_errors_tree_intact` — nonexistent timestamp raises `SnapshotNotFoundError`; live tree byte-unchanged.

All three were RED before fix, GREEN after.

---

## FIX 3 (HIGH): Change-log dedup suppresses distinct triples

**Bug:** `_already_present(existing_text, dedup_key)` tested `date in existing_text`, `artifact in existing_text`, and `action_pattern.search(existing_text)` independently. Two entries whose fields jointly covered a new triple's date + artifact + action would falsely suppress it — silent audit-trail data loss.

**Example:** file contains `(2026-01-05, PRD-AUTH, updated)` and `(2026-01-05, PRD-PAY, approved)`. Writing `(2026-01-05, PRD-AUTH, approved)` was wrongly blocked because date "2026-01-05" matched entry 1, artifact "PRD-AUTH" matched entry 1, and action "approved" matched entry 2.

**Fix:** Added `_parse_existing_triples(existing_text) -> set[tuple[str, str, str]]` which iterates over heading matches, extracts the artifact and action from each entry's block using the same `_ARTIFACT_RE`/`_ACTION_RE`, and returns the set of tuples. `_already_present` now checks `dedup_key in _parse_existing_triples(existing_text)` — tuple membership, not three independent substring scans.

**Files:** `change_log_writer.py` (+20 lines)

**Tests written first (TDD):**
- `test_distinct_triple_not_suppressed_by_field_contamination` — pre-populates month file with the contaminating pair, then writes the new distinct triple; asserts heading count increases.
- Existing `test_writer_dedup_idempotent` stays green (true-duplicate still suppressed).

Was RED before fix, GREEN after.

---

## Verification

```
python3 -m pytest .claude/skills/product-spec -q --tb=no
→ 1 failed, 779 passed  (only pre-existing test_dogfood_state_untracked)

python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q --tb=no
→ 241 passed
```

All Phase 1–8 tests + P12 ascii-truncation tests stay green.
