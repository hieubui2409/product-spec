---
phase: 8
title: '#15 change-log rotation + path check'
status: completed
priority: P3
effort: 1.5d
dependencies: []
---

# Phase 8: #15 change-log FULL rotation + path check (CVR-F10) — owner chose (b)

> **Resolved known-unknown (red-team C2):** there is NO programmatic change-log writer. Entries are appended by
> the LLM following workflow prose; `generate_templates.py` treats `change_log_entry` as a content-only type
> with **no file home** (emits text to stdout, `--write` is a no-op). Per `workflow-validate.md` / `workflow-interview.md`
> (×2) / `workflow-update.md`. **Owner chose full rotation (b):** build a real append+rotate writer AND rewire the
> 4 ref docs to call it. This edits kit reference prose (not PO artifacts) — allowed.

## Overview
Bound the unbounded change-log with real monthly rotation: give `change_log_entry` a true file home + rotation in
`generate_templates.py`, rewire the 4 workflow refs to call the writer, make `assemble_audit_trail.py` read across
rolled-over files (back-compat with legacy single `change-log.md`), and add an orphan-path check. P12 already added
ascii-truncation to `assemble_audit_trail.py` (render-only) → re-read, don't clobber.

## Requirements
- Functional: (1) new append-writer: `generate_templates.py` (or a small sibling) gains `write_change_log_entry(root,
  entry)` that appends to `change-log/<YYYY-MM>.md` (creates dir/file; rotates by calendar month). (2) The 4 workflow
  ref docs change "append a change-log entry" prose → call the writer (with the rendered template). (3)
  `assemble_audit_trail._parse_change_log` reads legacy `change-log.md` AND globs `change-log/*.md`, merged
  chronologically, dedup on (date,artifact,action). (4) orphan-path check: entry artifact id whose file no longer
  exists → flagged (fold into existing "unreconciled" detection).
- Non-functional: back-compat — legacy single `change-log.md` still fully read. Deterministic merge order. Idempotent
  writer (re-append identical entry guarded). Writer is kit code; the 4 ref-doc edits preserve their surrounding prose.

## Architecture
- Writer: `write_change_log_entry(root, entry_md)` — resolve `change-log/<YYYY-MM>.md` from entry date (or today),
  mkdir, append; dedup-guard on (date,artifact,action). Wire `generate_templates.py --type change_log_entry --write`
  to actually write (currently a no-op) OR expose the helper for the refs to call.
- 4 ref docs (rewire the "append change-log" instruction to invoke the writer):
  `references/workflow-validate.md` (~L266), `references/workflow-interview.md` (~L18 + ~L301),
  `references/workflow-update.md` (~L54). Edit only the change-log instruction lines; leave the rest intact.
- `assemble_audit_trail.py`: `_change_log_paths(root)` → `[change-log.md] + sorted(change-log/*.md)`; `_parse_change_log`
  merges + sorts by parsed date; add orphan flag. Re-read the P12 ascii-clip head first (additive change only).

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/generate_templates.py` (real write+rotate for `change_log_entry`)
- Modify: `.claude/skills/product-spec/scripts/assemble_audit_trail.py` (`_change_log_paths` + merge + orphan; re-read P12)
- Modify: `.claude/skills/product-spec/references/workflow-validate.md`, `workflow-interview.md`, `workflow-update.md`
  (rewire the change-log-append instruction — change-log lines only)
- Modify/Create: tests `test_audit_trail.py` (extend) + `test_change_log_writer.py`
- Modify: REVIEW.md (build-new → DEC), EVIDENCE.md

## TDD — tests first
1. `test_writer_appends_to_month_file` — `write_change_log_entry` with a June date → entry lands in `change-log/2026-06.md` (dir created).
2. `test_writer_rotates_across_months` — entries dated June + July → two month files, each with its entry.
3. `test_writer_dedup_idempotent` (negative) — same entry twice → single line (dedup on date,artifact,action).
4. `test_assemble_reads_legacy_and_rolled` — `change-log.md` + `change-log/2026-06.md` → merged, chronological, no dupes.
5. `test_legacy_only_still_read` (negative/back-compat) — only legacy file → full read unchanged.
6. `test_missing_artifact_path_flagged` — entry for a deleted artifact → orphan/unreconciled flag.
7. `test_existing_path_not_flagged` (negative) — entry for a live artifact → not flagged.
8. `test_ref_docs_invoke_writer` — grep the 3 ref docs assert they reference the writer call (not just prose).
Product-spec conftest helpers (`make_proj`, write helpers). P12 ascii tests must stay green.

## Implementation Steps
1. Write 8 RED tests.
2. Implement `write_change_log_entry` + wire `generate_templates.py --type change_log_entry --write`.
3. Rewire the 4 ref-doc change-log instructions to call the writer (edit only those lines).
4. `_change_log_paths` + merge + orphan check in `assemble_audit_trail.py` (re-read P12 head first).
5. GREEN; product-spec suite + CONTRIBUTING:69; confirm P12 ascii tests still green.
6. DEC + EVIDENCE.

## Success Criteria
- [ ] 8 tests green incl. 3 negatives (dedup, legacy-only back-compat, live-path not flagged).
- [ ] Writer appends+rotates monthly; `generate_templates.py --write` no longer a no-op for change_log_entry.
- [ ] 4 ref docs invoke the writer (grep-asserted); surrounding prose intact.
- [ ] assemble reads across rollover; orphan paths flagged; P12 ascii-truncation preserved.
- [ ] DEC + EVIDENCE.

## Risk Assessment
- Editing PO-facing ref prose in an autonomous run → touch ONLY the change-log-append instruction lines; grep-assert
  surrounding sections unchanged; the docs are kit references (not PO artifacts).
- Read-contract break vs P12 → re-read `assemble_audit_trail.py` head; merge additive; existing P12 tests must stay green.
- Date-sort ambiguity across files → sort by parsed date key, stable; dedup-guard on (date,artifact,action).
- Writer wired but refs not updated → `test_ref_docs_invoke_writer` gate.
