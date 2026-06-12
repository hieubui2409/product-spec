# Phase 8 Implementation Report — #15 change-log rotation + path check

## Phase
- Phase: phase-08-15-change-log-rotation-path-check
- Plan: plans/260612-2142-remaining-fixwave-to-release-240/
- Status: completed

## Files Modified

| File | Change |
|------|--------|
| `.claude/skills/product-spec/scripts/change_log_writer.py` | NEW — `write_change_log_entry(root, entry_md, *, when=None)` with monthly rotation, auto-mkdir, dedup guard, injectable `when` |
| `.claude/skills/product-spec/scripts/assemble_audit_trail.py` | ADDITIVE — `_change_log_paths`, `_parse_one_change_log_file`, `_parse_change_log` refactored for cross-file merge; `_live_artifact_ids` + orphan flag in `assemble()` |
| `.claude/skills/product-spec/scripts/generate_templates.py` | WIRE — `--type change_log_entry --write` now calls `write_change_log_entry` (previously a no-op) |
| `.claude/skills/product-spec/references/workflow-validate.md` | REWIRE — L266 + L320 (2 spots): change-log-append instruction references `write_change_log_entry` |
| `.claude/skills/product-spec/references/workflow-interview.md` | REWIRE — L18 + L301 (2 spots): change-log-append instruction references `write_change_log_entry` |
| `.claude/skills/product-spec/references/workflow-update.md` | REWIRE — L63 (1 spot): change-log entry instruction references `write_change_log_entry` |
| `.claude/skills/product-spec/scripts/tests/test_change_log_writer.py` | NEW — 8 tests |
| `.claude/skills/_shared/lib/context_footprint_baseline.json` | REGEN — +180 tokens product-spec (ref-doc growth, per documented protocol) |
| `docs/audit-trail/REVIEW.md` | LEDGER — P8-15 row ticked `[x]` |
| `docs/audit-trail/EVIDENCE.md` | LEDGER — P8-15 before/after entry |
| `docs/product/decisions.md` | LEDGER — DEC-6 appended |

## Tasks Completed

- [x] (A) Writer: `change_log_writer.py` with `write_change_log_entry`, monthly rotation, dedup, injectable `when`
- [x] (A) Wire: `generate_templates.py --write` for `change_log_entry` type calls the writer
- [x] (B) 4 ref-doc instruction spots in 3 files rewired to invoke `write_change_log_entry`
- [x] (C) `assemble_audit_trail._parse_change_log` reads legacy + rolled month files, merges chronologically, deduplicates
- [x] (D) Orphan-path check: deleted-artifact change-log entries flagged `reconciled=False`
- [x] DEC-6 + EVIDENCE.md + REVIEW.md ticked

## Tests

| Test name | Result |
|-----------|--------|
| `test_writer_appends_to_month_file` | PASS |
| `test_writer_rotates_across_months` | PASS |
| `test_writer_dedup_idempotent` (negative) | PASS |
| `test_assemble_reads_legacy_and_rolled` | PASS |
| `test_legacy_only_still_read` (negative/back-compat) | PASS |
| `test_missing_artifact_path_flagged` | PASS |
| `test_existing_path_not_flagged` (negative) | PASS |
| `test_ref_docs_invoke_writer` | PASS |
| P12 ascii: `test_ascii_lines_within_budget` | PASS |
| P12 ascii: `test_markdown_preserves_full_text` | PASS |
| P12 ascii: `test_ascii_truncation_uses_ellipsis` | PASS |

- Product-spec suite: **762 passed / 1 failed** (1 = pre-existing `test_dogfood_state_untracked`)
- CONTRIBUTING:69 gate: **237 passed** (after baseline regen)
- P12 ascii-truncation tests: **3 passed** (preserved, not clobbered)
- Back-compat legacy-only read: confirmed by `test_legacy_only_still_read`

## Design notes

- `change_log_writer.py` as a new sibling (not inlined into `generate_templates.py` which is already at 392 LOC).
- Orphan check uses `Optional[set]` sentinel: `None` = graph unavailable (skip, fail-soft); `set()` = no artifacts (check active).
- Context footprint baseline regenerated: ref-doc rewiring added +180 product-spec tokens. Documented protocol (same as P12).
- 4 ref-doc instruction spots: `workflow-validate.md` L266 + L320, `workflow-interview.md` L18 + L301, `workflow-update.md` L63. Surrounding prose byte-intact.

## Commit
See git log for hash.
