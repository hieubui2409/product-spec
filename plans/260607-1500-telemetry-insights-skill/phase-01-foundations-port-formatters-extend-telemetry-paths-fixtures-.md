---
phase: 1
title: "Foundations: port formatters + extend telemetry_paths + fixtures + gate"
status: complete
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Foundations: port formatters + extend telemetry_paths + fixtures + gate

## Overview

Shared groundwork every later phase imports: port HA's generic `formatters.py`, extend `telemetry_paths.py` with the path helpers the lenses need, author fixtures, and add the low-volume gate. No shipped-code touch; no lens logic yet.

## Requirements
- Functional:
  - Port `formatters.py` (markdown_table / json_output / summary_block / severity_badge) verbatim to `_shared/lib/` — it is framework-agnostic and already handles Vietnamese display-width (NFC + east-asian width), a bonus for VI output.
  - Extend `telemetry_paths.py`: add `sessions_dir()` (Claude Code transcripts: `~/.claude/projects/<encoded-root>/`), `memory_dir()` (`…/memory/`), and a `TELEMETRY` constant. Honor env overrides for tests (`CK_SESSIONS_DIR`, `CK_MEMORY_DIR`) mirroring HA.
  - `low_volume_gate(count, threshold)` + default constant.
  - Fixtures: the 3 existing sinks + the 2 NEW sinks (`subagent-outcomes.jsonl`, `hook-telemetry.jsonl` with `ms`) + a fake transcript dir + a fake memory dir, all with hand-verifiable contents. Include a stray/unknown sink to test ignore-unknown.
- Non-functional: <120 LOC per file; no network; fail-soft; zero dependency on `product-spec`.

## Architecture
- `formatters.py` is a clean lift (no skill_ids dep). Keep its public API identical so ported lens scripts import it unchanged.
- Path resolution: reuse HA `paths.py` logic for `sessions_dir()` (encode project root → `~/.claude/projects/<slug>`); cleanmatic already does this in `emit_session_summary.py` (`resolve_transcript`/`_sessions_dir`) — factor that into `telemetry_paths.py` so both the hook and the lenses share ONE resolver (DRY).

## Related Code Files
- Create: `.claude/skills/_shared/lib/formatters.py`
- Modify: `.claude/skills/_shared/lib/telemetry_paths.py` (+ `sessions_dir`, `memory_dir`, `TELEMETRY`)
- Modify: `.claude/hooks/emit_session_summary.py` (use the shared `sessions_dir()` instead of its private copy — DRY)
- Create: `.claude/skills/_shared/scripts/tests/fixtures/telemetry/…` + `fixtures/sessions/…` + `fixtures/memory/…`
- Create: `.claude/skills/_shared/scripts/tests/test_formatters.py`, `test_telemetry_paths_helpers.py`, `test_low_volume_gate.py`, `test_fixtures_sane.py`
- Read for context: HA `platform_lib/formatters.py`, `paths.py`; cleanmatic `emit_session_summary.py`

## Implementation Steps (TDD)
1. **Test first:** `test_formatters.py` (markdown_table alignment + VI width), `test_telemetry_paths_helpers.py` (sessions_dir/memory_dir honor env override; TELEMETRY points at `.claude/telemetry`), `test_low_volume_gate.py` (boundary). Run → red.
2. Port `formatters.py`; extend `telemetry_paths.py`; implement gate → green.
3. Refactor `emit_session_summary.py` onto the shared `sessions_dir()`; assert its existing tests still pass (no behavior change).
4. Author fixtures (5 invocations/3 skills incl. `via=prompt-expansion`; 4 script runs incl. 1 `exit!=0` + `ms`; 2 sessions; 3 subagent-outcomes incl. 1 timeout; a transcript with a Skill span + usage; a memory dir with 1 orphan + 1 dead link; 1 stray sink). `test_fixtures_sane.py` asserts counts.

## Success Criteria
- [ ] `formatters.py` ported; tests green; VI width correct.
- [ ] `sessions_dir()`/`memory_dir()`/`TELEMETRY` added + env-overridable (asserted).
- [ ] `emit_session_summary.py` uses shared resolver; its prior tests still green (no regression).
- [ ] Fixtures exist with asserted counts incl. the 2 new sinks + transcript + memory dirs.

## Risk Assessment
- **Refactoring the session hook** could regress session summaries. Mitigation: its existing tests are the gate; keep the resolver behavior identical.
- **Path encoding mismatch** (`~/.claude/projects/<slug>`). Mitigation: copy cleanmatic's proven encoding from `emit_session_summary.py`, don't reinvent.
