---
phase: 7
title: "#11 usage-summary export + harvester"
status: completed
date: 2026-06-12
commit: f2cbaee
---

# Phase 7 Implementation Report

## Phase

Phase 7 — #11 usage-summary export + harvester (ARC-F06)
Plan: plans/260612-2142-remaining-fixwave-to-release-240/

## Status: completed

## Files Modified

| File | Change |
|---|---|
| `.claude/skills/telemetry/scripts/harvester.py` | NEW — 173 lines |
| `.claude/skills/telemetry/scripts/tests/test_harvester.py` | NEW — 277 lines (5 tests) |
| `.claude/skills/telemetry/scripts/analyze_telemetry.py` | +53 lines (2 flags + wiring helpers) |
| `.claude/skills/telemetry/scripts/telemetry_render.py` | +6 lines (VI/EN suggest_h/suggest_none) |
| `docs/audit-trail/REVIEW.md` | +15 lines (P7 row ticked) |
| `docs/audit-trail/EVIDENCE.md` | +27 lines (P7-11 before/after) |
| `docs/product/decisions.md` | +25 lines (DEC-5) |

## Tasks Completed

- [x] 5 RED tests written first (test_harvester.py); confirmed 4 fail for the right reasons
- [x] `harvester.py` implemented — pure READ, returns dict, zero write-mode opens anywhere
- [x] `--export-summary [PATH]` wired into `analyze_telemetry.py` (append only, P6 lines untouched)
- [x] `--auto-suggest` (store_true, opt-in) wired — absent → no suggestions section
- [x] VI/EN `suggest_h`/`suggest_none` labels appended to `telemetry_render.py` `_T` dict
- [x] 5 tests GREEN
- [x] REVIEW.md P7 row ticked; EVIDENCE.md P7-11 entry; DEC-5 recorded
- [x] Commit created

## Test Names (5 new)

1. `TestExportSummaryWritesMarkdown::test_export_summary_writes_markdown`
2. `TestHarvesterReturnsSuggestionsOnly::test_harvester_returns_suggestions_only`
3. `TestHarvesterNeverWritesAnything::test_harvester_never_writes_anything` ← boundary A9 / H3
4. `TestAutoSuggestOptInGate::test_auto_suggest_absent_produces_no_suggestions_section`
5. `TestExportSummaryNoTelemetryGraceful::test_export_summary_empty_telemetry_writes_valid_markdown`

## Tests Status

- Primary gate (`python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q`): **237 passed** (232 baseline + 5 new)
- Product-spec regression (`python3 -m pytest .claude/skills/product-spec -q`): **1 failed** — `test_dogfood_state_untracked` (pre-existing, unchanged)

## Boundary A9 / H3 Confirmation

`test_harvester_never_writes_anything` monkeypatches:
- builtin `open` → raises `IOError` on any write-mode (`w`, `a`, `x`, `w+`, `wb`, `ab`, `xb`)
- `pathlib.Path.write_text` → raises `IOError`
- `pathlib.Path.write_bytes` → raises `IOError`

`harvest_suggestions()` completes and returns `{"suggestions": [...]}` without triggering any write. Stronger than mtime-diffing: catches writes to ANY path (not just `.claude/skills/**`).

## P6 Shared-File Lines Verification

P6's lines in `telemetry_render.py` and `analyze_telemetry.py` stayed byte-identical:
- `artifact_heat` key in LENSES dict (line 50): untouched
- `artifact_heat` in OVERVIEW_ORDER (line 55): untouched
- `heat_h`/`heat_total`/`heat_cols`/`heat_none`/`a_heat` in `_T` (lines 120-125, 222-224): untouched
- P7 labels (`suggest_h`, `suggest_none`) appended after P6's block in both EN and VI sections

## Commit

`f2cbaee` — feat(telemetry): add usage-summary export and read-only suggestion harvester

## Unresolved Questions

None.
