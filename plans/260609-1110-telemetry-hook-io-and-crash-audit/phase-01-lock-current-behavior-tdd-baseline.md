---
phase: 1
title: "Lock current behavior (TDD baseline)"
status: completed
priority: P1
effort: "2-3h"
dependencies: []
---

# Phase 1: Lock current behavior (TDD baseline)

## Overview

Before touching any hook, capture the CURRENT observable behavior of all 7 project hooks as executable tests. TDD anchor: these tests must stay green through Phases 2-4. This is the regression net for a refactor of fail-open instrumentation that runs on every Bash/Skill/Stop.

## Requirements

- Functional: characterize, per hook, (a) stdout is valid `{"continue": true}` for the 5 telemetry hooks, (b) process exit code (0 for telemetry/allow; `memory_gap` 2-on-block / 0-on-allow; `critique_nudge` always 0), (c) fail-open: malformed/empty stdin and a forced internal exception both still produce normal output + non-blocking exit.
- Functional: characterize the `ms` pairing — `mark_bash_start` write → `track_script_execution` read produces an `ms` field on the telemetry record for a skill-script command; a plain `git status` command produces NO marker/record.
- Non-functional: tests must not write into the real `.claude/telemetry/` — use `CK_TELEMETRY_DIR`/`tmp_path` (see existing test setup) so they are hermetic.

## Architecture

- Extend, do not replace, existing suites:
  - `.claude/hooks/__tests__/test_telemetry_hooks.py`
  - `.claude/hooks/__tests__/test_bash_duration_pairing.py`
  - `.claude/skills/telemetry/scripts/tests/test_lens_health.py` (already asserts `avg_ms is None → "—"` degrade — keep as the OFF-state contract).
- Run hooks as subprocesses via the venv python (`.claude/skills/.venv/bin/python3`) feeding JSON on stdin, asserting stdout JSON + `returncode`. Mirror the invocation style already in `test_telemetry_hooks.py`.

## Related Code Files

- Modify (add tests only): `.claude/hooks/__tests__/test_telemetry_hooks.py`, `.claude/hooks/__tests__/test_bash_duration_pairing.py`
- Read for context: all 7 hooks; `.claude/skills/telemetry/scripts/telemetry_paths.py`
- Create: none (extend existing suites; only add a new test file if a hook has no current coverage)

## Implementation Steps

1. Inventory existing test coverage per hook; list which of the 7 have zero behavioral test today.
2. For each telemetry hook (`mark_bash_start`, `track_script_execution`, `track_skill_invocation`, `track_subagent_outcome`, `emit_session_summary`): add/confirm a test asserting `{"continue": true}` stdout + exit 0 on (a) valid payload, (b) empty stdin, (c) payload that triggers the internal `except` path (e.g. monkeypatched sink raising). All must remain non-blocking.
3. For `memory_gap_hook`: add/confirm tests for ALLOW (exit 0, no decision) and a REAL BLOCK path (exit 2 + `decision:block` JSON) that actually drives a `fence_breach` signal — NOT a mock return. This exit-2 lock is the guard for Phase 2 (which adds a logger import into this file's except). Must exist BEFORE Phase 2 touches `memory_gap_hook`.
4. For `product_spec_critique_nudge`: confirm exit 0 + advisory-only on the nudge path; never exit 2.
5. Confirm the `ms` pairing test exists and asserts both presence (skill-script) and absence (non-skill command).
6. Run the full suite; record the green baseline (count + list).

## Success Criteria

- [ ] Every one of the 7 hooks has at least: a happy-path test + a fail-open test (bad stdin) + an exit-code assertion.
- [ ] `ms`-present and `ms`-absent both asserted.
- [ ] `avg_ms → "—"` degrade test present (OFF-state contract for Phase 3/4).
- [ ] Full telemetry suite green; baseline count recorded in the phase notes.
- [ ] Zero production hook code changed in this phase.

## Risk Assessment

- Risk: characterization test accidentally encodes a bug as "expected". Mitigation: each test comments WHY the behavior is correct (fail-open by design), not just WHAT.
- Risk: non-hermetic tests pollute real telemetry. Mitigation: existing tests already defuse this (red-team B, verified) — they `monkeypatch.delenv("PYTEST_CURRENT_TEST")` + set `CK_TELEMETRY_DIR=tmp_path` + `importlib.reload(telemetry_paths)`, then assert real sink lines (`test_telemetry_hooks.py:36,83`). So `disabled()` under pytest does NOT make the baseline hollow — `main()` runs fully, only the file-write is suppressed when not overridden. Reuse this fixture pattern for any new test.
