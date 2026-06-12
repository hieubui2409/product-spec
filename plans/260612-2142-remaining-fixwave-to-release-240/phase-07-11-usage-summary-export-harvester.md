---
phase: 7
title: '#11 usage-summary export + harvester'
status: completed
priority: P3
effort: 0.75d
dependencies:
  - 6
---

# Phase 7: #11 usage-summary export + harvester (ARC-F06)

## Overview
Close the feedback loop to the dev team WITHOUT the kit self-evolving (boundary A9). `telemetry --export-summary`
emits a markdown aggregate the PO reviews then sends on; a READ-ONLY harvester reads self-corrections +
repeat-findings and OUTPUTS suggestions (never writes skill/template). Opt-in per run.

## Requirements
- Functional: `analyze_telemetry.py --export-summary [PATH]` writes a markdown aggregate (reuse `gather_all`/`render_md`);
  `--auto-suggest` (opt-in) appends harvester suggestions. `harvester.py` reads `docs/product/.memory/self-corrections.json`
  + repeat-findings from artifact-events (P6) → returns suggestions (category/artifact/count/why).
- Non-functional (boundary A9): harvester is READ-ONLY — emits a report, NEVER writes any skill/template/SKILL.md.
  Opt-in gate (absent flag → no suggestions). PO reviews before sending (no auto-send).

## Architecture
- `analyze_telemetry.py`: add `--export-summary PATH` (default `.claude/telemetry/usage-summary.md`) + `--auto-suggest`
  (store_true). After `_render`, if export → write; if auto-suggest → append `harvester.harvest_suggestions()`.
- New `.claude/skills/telemetry/scripts/harvester.py`: `harvest_suggestions(days=30) -> {"suggestions":[...]}` reading
  self-corrections (via `behavioral_memory_self_corrections.load`) + artifact-events tallies. Pure read; returns dict.
- VI/EN labels in `telemetry_render.py` `_T`.

## Related Code Files
- Modify: `.claude/skills/telemetry/scripts/analyze_telemetry.py` (2 flags + wiring)
- Create: `.claude/skills/telemetry/scripts/harvester.py`
- Modify: `.claude/skills/telemetry/scripts/telemetry_render.py` (labels)
- Modify/Create: tests `test_analyze_telemetry_cli.py` (extend) + `test_harvester.py`
- Modify: REVIEW.md (build-new → DEC), EVIDENCE.md

## Dependencies
- **P6 (`blockedBy: [6]`)** — TWO reasons: (1) repeat-findings source is P6's artifact-events sink; (2) red-team
  C1 — P7 and P6 BOTH edit `telemetry_render.py` (`_T` dict) and `analyze_telemetry.py`. P7 runs AFTER P6 and
  **re-reads both files** before editing (grep the `_T` dict + the argparse block) to avoid clobbering P6's keys.

## TDD — tests first
1. `test_export_summary_writes_markdown` — `--export-summary out.md` → file exists, contains aggregate sections.
2. `test_harvester_returns_suggestions_only` — seeded self-corrections + repeat edits → suggestions list returned.
3. `test_harvester_never_writes_anything` (boundary A9, negative — red-team H3 hardened) — monkeypatch builtin
   `open` (and `Path.write_text`/`write_bytes`) to RAISE on any write-mode (`w`/`a`/`x`) call; run harvester →
   completes without triggering a write. Stronger than mtime-diff (catches write-then-restore + writes outside
   the `.claude/skills/**` glob).
4. `test_auto_suggest_opt_in_gate` (negative) — without `--auto-suggest` → output has no suggestions section.
5. `test_export_summary_no_telemetry_graceful` — empty telemetry dir → valid (empty) markdown, exit 0.
Telemetry inline-fixture style.

## Implementation Steps
1. Write 5 RED tests.
2. Implement `harvester.py` (read-only).
3. Wire `--export-summary` + `--auto-suggest` into `analyze_telemetry.py`.
4. GREEN; telemetry+hooks+_shared suite.
5. DEC + EVIDENCE.

## Success Criteria
- [ ] 5 tests green; boundary-A9 test uses a write-blocking guard (any write-mode `open` raises); opt-in gate enforced.
- [ ] `--export-summary` writes markdown aggregate; empty telemetry graceful.
- [ ] telemetry suite green; DEC + EVIDENCE.

## Risk Assessment
- Boundary A9 breach (self-edit) → harvester pure-read by construction + no-write assertion test.
- Privacy in export → aggregate counts only, PO reviews before send; no raw transcript content.
