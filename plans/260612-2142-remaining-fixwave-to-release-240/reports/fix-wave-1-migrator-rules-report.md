# Fix Wave 1 — Migrator + Rules Report

Commit: `b603637`
Tests: 959 passed (product-spec + telemetry + _shared), 1 pre-existing red (test_dogfood_state_untracked)

---

## Bug → Fix → Test Mapping

### FIX 1 (CRITICAL): blanket --apply rewrote approved artifacts

**Bug**: `migrate` write loop iterated all `actionable` items with no approved-filter. `confirm_required` was computed for the report but never consulted before writing.

**Fix**: In `migrate()`, approved items are skipped unless their derived ID or file path appears in the `confirm_approved` allowlist (supplied via new `--confirm-approved <ID>` CLI flag, repeatable). Without that explicit opt-in, approved artifacts land in `confirm_required` and are left byte-identical.

**Tests added**:
- `test_apply_skips_approved_without_alllist`: approved brd.md + blanket `--apply` → file byte-unchanged, no .bak, item in confirm_required
- `test_apply_writes_approved_only_with_allowlist`: same + `--confirm-approved BRD` → id inserted, .bak created
- `test_apply_non_approved_still_backfills_under_blanket_flag`: draft brd.md → still backfilled normally

---

### FIX 2 (MEDIUM): id-backfill stamped/downgraded schema_version

**Bug**: `_transform()` unconditionally appended `schema_version: 1` when absent. A file with `schema_version: 2` would not be downgraded (had_marker guard), but a file with no schema_version would get one injected — orthogonal to id insertion.

**Fix**: Removed the `had_marker` check and the `schema_version` insertion line from `_transform()`. The migrator now inserts exactly one thing: the missing `id:` field.

**Tests added**:
- `test_apply_preserves_existing_schema_version`: file with `schema_version: 2` → after apply, schema_version still exactly 2
- `test_apply_does_not_inject_schema_version_when_absent`: file with no schema_version → after apply, schema_version not present
- Updated `test_apply_backfills_missing_id` assertion to assert `schema_version NOT in fm` (was asserting it was stamped)

---

### FIX 3 (LOW): skipped report mixed absolute and relative paths

**Bug**: `_scan_unrecognised` returned `str(path)` (absolute), while `_scan_artifacts` returns `item["file"]` (repo-relative). Mixed into same `report["skipped"]` list.

**Fix**: `_scan_unrecognised` now takes `repo_root: Path` parameter and normalises all entries via `path.relative_to(repo_root)`. `migrate()` passes `root` (the project root) as `repo_root`.

**Tests added**:
- `test_skipped_paths_are_relative`: project with exotic artifact → all skipped entries are non-absolute strings

---

### FIX 4 (MEDIUM): persona-portrait false positive on descriptive headings

**Bug**: `check_persona_portraits` checked `persona_lower not in headings` (exact equality). A heading like `## Alice — the busy admin` lowercases to `alice — the busy admin`, which != `alice`, so it fired a false warning.

**Fix**: Introduced `_persona_has_portrait(persona_lower, headings)` helper that accepts: (a) exact match, or (b) heading starts with persona name followed by a separator char (space, dash, en/em-dash, colon).

**Tests added**:
- `test_persona_portrait_descriptive_heading_no_false_positive`: `## Alice — the busy admin` for persona "Alice" → 0 findings
- `test_persona_portrait_no_heading_still_warns`: persona "Bob" with no heading mentioning Bob → warn fires

---

### FIX 5 (LOW): drop unused root param from product check functions

**Bug**: `check_product_subsystems(graph, root)` and `check_persona_portraits(graph, root)` both ignored `root` and re-derived it from `graph["root_path"]`. Inconsistent with sibling modules that accept `(graph)` only.

**Fix**: Removed `root: Path` from both signatures. Updated dispatch lines in `check_consistency.py` (removed the now-dead `_root` binding). Existing tests updated to call with `(graph)` only.

**Tests added**:
- `test_check_product_subsystems_accepts_graph_only`: single-arg call works
- `test_check_persona_portraits_accepts_graph_only`: single-arg call works

---

### FIX 6 (LOW): re-add BOM + comment round-trip test

**Bug**: `_PRODUCT_BOM_COMMENT` fixture existed but was dead (no test used it after phase-02 dropped `test_bom_and_comment_preserved`).

**Fix**: Added `test_bom_and_comment_preserved` — writes BOM+comment fixture, applies, asserts BOM byte sequence preserved, comment line present, id inserted.

---

## Files Modified

| File | Change |
|---|---|
| `migrate_backfill_ids.py` | FIX 1 (approved gate + `--confirm-approved`), FIX 2 (no schema_version), FIX 3 (relative paths), FIX 6 (BOM preserved already worked, test re-added) |
| `check_consistency_product.py` | FIX 4 (`_persona_has_portrait` helper), FIX 5 (drop root param) |
| `check_consistency.py` | FIX 5 (2 dispatch lines updated) |
| `tests/test_migrate_backfill_ids.py` | 8 new tests; 1 existing assertion updated (schema_version) |
| `tests/test_check_consistency_product.py` | 4 new tests; 6 existing call sites updated to `(graph)` |
