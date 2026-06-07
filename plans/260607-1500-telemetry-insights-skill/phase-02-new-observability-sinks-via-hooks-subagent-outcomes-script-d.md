---
phase: 2
title: "New observability sinks via hooks (subagent-outcomes + script-duration)"
status: complete
priority: P1
effort: "5h"
dependencies: [1]
---

# Phase 2: New observability sinks via hooks (subagent-outcomes + script-duration)

## Overview

Add the two data sources cleanmatic lacks, **hook-only** so no shipped script is instrumented (the F1-class trap). (a) subagent outcomes via a new SubagentStop hook; (b) per-Bash-script duration via PreToolUse+PostToolUse:Bash pairing. Both fail-open, pytest-silent.

## Requirements
- Functional:
  - **`subagent-outcomes.jsonl`**: a new hook on `SubagentStop` records `{ts, agent_type, outcome, session}` where outcome ∈ {success, api_error, timeout, blocked, unknown}, inferred from the Stop payload / transcript tail (reuse HA's error-taxonomy mapping). Powers the reliability lens.
  - **script-duration**: add `ms` to `hook-telemetry.jsonl`. A PreToolUse:Bash hook stamps a start time keyed by a stable id; the existing PostToolUse `track_script_execution.py` computes `ms = now - start` and includes it. If no start mark (Pre missed), emit without `ms` (degrade, don't guess).
- Non-functional: every hook fail-open (`{"continue": true}` always), no-op under `CK_TELEMETRY_DISABLED`/pytest, never block or slow the session perceptibly. All hooks are CM-local `*.py` (git-tracked via `!*.py`), NOT in the bundle manifest.

## Architecture
- **Hook events VERIFIED present (2026-06-07)** in `.claude/settings.json`: `SubagentStart`, `SubagentStop`, `PreToolUse`, `PostToolUse`. So both the SubagentStop logger and the Pre/Post:Bash duration pairing are supported by this Claude Code version. (SubagentStart is also available if subagent duration is later wanted.)
- **atexit/excepthook REJECTED** (D5): would require importing a telemetry module into shipped product-spec scripts → `ModuleNotFoundError` on recipients (`_shared` not bundled) + telemetry leak. Hooks live outside shipped code and only run on the author's machine.
- Start-mark store for duration: a tiny temp file under `telemetry_dir()/.bashtimers/<key>` (key from session + a hash of the command), pruned opportunistically. Keep it dumb and fail-open.
- Outcome inference: prefer an explicit field in the SubagentStop payload; fall back to transcript-tail scan (last error marker) like HA; default `unknown` rather than fabricating `success`.
- Register both in the local (ck-managed, gitignored) `.claude/settings.json` via `register_telemetry_hooks.py` — extend that script to add/repair/remove the 2 new registrations (idempotent), so settings regen is recoverable.

## Related Code Files
- Create: `.claude/hooks/track_subagent_outcome.py` (SubagentStop)
- Create: `.claude/hooks/mark_bash_start.py` (PreToolUse:Bash)
- Modify: `.claude/hooks/track_script_execution.py` (read start mark → add `ms`)
- Modify: `.claude/skills/_shared/lib/telemetry_paths.py` (start-mark helpers if needed)
- Modify: `.claude/skills/_shared/scripts/register_telemetry_hooks.py` (+ 2 registrations; `--check/--remove`)
- Create tests: `.claude/hooks/__tests__/test_track_subagent_outcome.py`, `test_bash_duration_pairing.py`, `test_register_new_hooks.py`
- Read for context: HA `platform_lib/telemetry.py` (taxonomy only), `track-subagent-reliability.py`; cleanmatic `track_script_execution.py`, `register_telemetry_hooks.py`

## Implementation Steps (TDD)
1. **Test first:** feed a synthetic SubagentStop payload → assert one `subagent-outcomes.jsonl` record with the right outcome enum; a timeout payload → `timeout`; a malformed payload → no raise + `{"continue":true}`. Under pytest → no write. Run → red.
2. Implement `track_subagent_outcome.py` → green.
3. **Test:** Pre stamps start, Post computes `ms` (monotonic, ≥0); missing Pre → record without `ms`; pytest → no write. Run → red.
4. Implement `mark_bash_start.py` + extend `track_script_execution.py` → green.
5. Extend `register_telemetry_hooks.py` (+2) with `--check/--remove` tests → green. Register into local settings.json.
6. Manual smoke: run a real bash skill-script + spawn a subagent; confirm both sinks gain a line locally.

## Success Criteria
- [ ] `subagent-outcomes.jsonl` populated with correct outcome enum from real SubagentStop (smoke) + fixtures; malformed → fail-open.
- [ ] `hook-telemetry.jsonl` gains `ms` when Pre/Post pair; degrades gracefully when not.
- [ ] All new hooks no-op under pytest/`CK_TELEMETRY_DISABLED`; always emit `{"continue":true}`.
- [ ] `register_telemetry_hooks.py` adds/repairs/removes the 2 new hooks idempotently (tested).
- [ ] No shipped script imports any telemetry module (grep-assert in Phase 8).

## Risk Assessment
- **Live-session interference** (hooks fire every Bash/subagent). Mitigation: fail-open + pytest-silent + cheap temp-file timer; smoke-test before trusting.
- **Outcome mis-classification.** Mitigation: default `unknown`, never fabricate `success`; reliability lens shows `unknown` honestly.
- **Start-mark leak/garbage** in `.bashtimers/`. Mitigation: opportunistic prune + size cap; it's under the gitignored telemetry dir.
- **Settings regen wipes hooks.** Mitigation: `register_telemetry_hooks.py` is the documented repair path.
