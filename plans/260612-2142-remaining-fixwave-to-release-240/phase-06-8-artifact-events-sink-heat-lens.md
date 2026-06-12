---
phase: 6
title: '#8 artifact-events sink + heat lens'
status: completed
priority: P3
effort: 0.75d
dependencies: []
---

# Phase 6: #8 artifact-events sink + heat lens (ARC-F05)

## Overview
Record which spec artifacts get edited (path-only, NO content) and narrate "which PRD is edited most" in VI.
Reuses the existing PostToolUse `Edit|Write|MultiEdit` matcher + the `telemetry_paths.append_event` sink contract.
New hook `track_artifact_edits.py` + new `lens_artifact_heat.py`.

## Requirements
- Functional: a PostToolUse hook records `{ts, artifact_path, op, session}` to `.claude/telemetry/artifact-events.jsonl`
  for edits under `docs/product`; a new "artifact_heat" lens tallies edits/artifact and renders VI ("PRD-X sửa N lần").
- Non-functional (privacy): PATH + op ONLY — extract `tool_input.path`, never read file / never touch `tool_response`.
  Fail-open (telemetry never breaks the observed op). Disabled under pytest (`CK_TELEMETRY_DISABLED`). Sink gitignored (P8).

## Architecture
- New hook `.claude/hooks/track_artifact_edits.py` (sibling of `track_script_execution.py`): via
  `hook_runtime.run_telemetry_hook`, extract `tool_input.path`, filter to `docs/product`, `append_event("artifact-events.jsonl",
  {ts, artifact_path, op, session})`. Drop everything else explicitly.
- Register in `register_telemetry_hooks.py` `REGISTRATIONS` (PostToolUse `Edit|Write|MultiEdit` matcher already present).
- New `.claude/skills/telemetry/scripts/lens_artifact_heat.py`: `gather(days=30)` reads the sink, tallies per artifact,
  returns `{"lens":"artifact_heat","rows":[{"artifact","edits","last_edit"}]}`. Register in `analyze_telemetry.py` LENSES;
  add VI labels to `telemetry_render.py` `_T`.

## Related Code Files
- Create: `.claude/hooks/track_artifact_edits.py`
- Modify: `.claude/hooks/register_telemetry_hooks.py` (add registration)
- Create: `.claude/skills/telemetry/scripts/lens_artifact_heat.py`
- Modify: `.claude/skills/telemetry/scripts/analyze_telemetry.py` (register lens), `telemetry_render.py` (VI labels)
- Create: tests `test_track_artifact_edits.py`, `test_lens_artifact_heat.py`
- Modify: REVIEW.md (build-new → DEC), EVIDENCE.md

## TDD — tests first
1. `test_edit_records_exact_key_set_path_only` (red-team H3 — whitelist not blacklist) — feed the hook a
   **realistic PostToolUse payload that DOES contain `tool_input.new_string` + `tool_response.content`**, then
   assert the written record's key set is **EXACTLY** `{ts, artifact_path, op, session}` (proves content is
   stripped, and resists a future field like `new_string` slipping through a name-blacklist).
2. `test_three_edits_three_records` — 3 edits → 3 path-only records.
3. `test_non_product_edit_ignored` (negative) — edit outside docs/product → 0 records.
4. `test_hook_disabled_under_pytest` — `CK_TELEMETRY_DISABLED` set → no write (fail-open/test-safe).
5. `test_heat_lens_narrates_counts` — sink with PRD-X×3, PRD-Y×1 → lens rows ordered, VI render contains "PRD-X" + "3".
6. `test_registration_idempotent` (negative) — register twice → single settings entry, HEAD hook not clobbered.
Telemetry inline-fixture style (monkeypatch `CK_TELEMETRY_DIR` + reload modules).

## Implementation Steps
1. Write 6 RED tests.
2. Implement hook (path-only extraction) + register.
3. Implement heat lens + register + VI labels.
4. GREEN; run `CONTRIBUTING.md:69` suite (telemetry+hooks+_shared) — this phase touches hooks → broaden.
5. DEC + EVIDENCE.

## Success Criteria
- [ ] 6 tests green; privacy test asserts EXACT 4-key set against a content-bearing payload; idempotent registration.
- [ ] Heat lens narrates VI counts ordered by edits.
- [ ] telemetry+hooks+_shared suite green.
- [ ] DEC + EVIDENCE recorded.

## Risk Assessment
- Content leak → path-only extraction + explicit drop + assertion test; fail-open.
- Hook clobbers a HEAD registration on upgrade → idempotent registrar test (HEAD-not-clobbered).
- Sink growth → existing 8MB rotation in `append_event`; gitignored.
