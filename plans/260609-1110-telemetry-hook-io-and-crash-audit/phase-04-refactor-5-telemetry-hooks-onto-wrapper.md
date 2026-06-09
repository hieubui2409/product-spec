---
phase: 4
title: "Refactor 5 telemetry hooks + gate & wire 2 enforcement hooks"
status: completed
priority: P1
effort: "3-4h"
dependencies: [3]
---

# Phase 4: Refactor 5 telemetry hooks + gate & wire 2 enforcement hooks

## Overview

Two parts. **(A)** Port the 5 telemetry hooks onto `run_telemetry_hook`, deleting their duplicated skeletons. **(B)** Bring the 2 enforcement hooks under the same config gate (validate D3) and WIRE them into `settings.json` Stop — default-false config makes them no-op until a PO opts in. Telemetry behavior stays identical (Phase 1 baseline green); enforcement default behavior stays "off" (today they're unwired; now wired-but-config-disabled = same observable effect).

## Requirements

- Functional: each hook = its hook-specific `core(data)` logic + an entrypoint `run_telemetry_hook(Path(__file__).stem, core)`.
- Functional (BLOCKER, red-team): **keep a `main(raw)`-compatible shim** in each hook. All existing tests call `mod.main(raw)` directly (`test_bash_duration_pairing.py:55-56`, `test_telemetry_hooks.py:74,93,134`, `test_track_subagent_outcome.py:49`). Provide `def main(raw): data = json.loads(raw or "{}"); core(data); emit_continue()` OR have tests call `core(data)` — pick ONE and apply consistently. Preferred: thin `main(raw)` shim so test call-sites stay untouched.
- Functional: `core(data)` no longer reads stdin nor owns the top-level fail-open try/except (the wrapper does). It may keep local try/except for fine-grained degrade (e.g. `mark_bash_start` regex/skip).
- Non-functional: per-file hook-specific logic ≤ ~20 lines; `telemetry_paths` imported lazily inside `core`.
- Non-functional: preserve every dedup/matcher detail (`track_skill_invocation` ship-both dedup bucket; shared `SCRIPT_RE`).
- Functional: `track_skill_invocation` is dual-registered (PreToolUse:Skill `settings.json:86` + UserPromptExpansion `:175`) — ONE config key (`track_skill_invocation`) gates BOTH registrations. Document this in the hook + config `_README`.

## Architecture

- Refactor order (lowest blast radius first): `mark_bash_start` → `track_skill_invocation` → `track_script_execution` → `track_subagent_outcome` → `emit_session_summary`.
- Keep each hook's module docstring; update the "Fail-open + non-blocking" note to point at `hook_runtime` as the now-shared owner of that contract.
- `mark_bash_start` stays (toggleable via config) — confirm `ms` pairing test still passes when enabled.

## Part B — enforcement hooks (gate + wire)

- Add an EARLY `hook_enabled(stem)` check at the top of each enforcement hook's `handle_stop`/`main` (after stdin parse, before any detector/graph/subprocess work): if disabled → return `ALLOW_EXIT` immediately (no block, no nudge). Import `hook_runtime` via the same shared snippet.
- WIRE both into `settings.json` under `Stop` (`memory_gap_hook` and `product_spec_critique_nudge`). They join the existing Stop chain (`session-state`, `emit_session_summary`). Order them AFTER `session-state` so state is written even if an enforcement hook later blocks.
- Critical: with `product-spec-hooks.json` default-false, both MUST no-op → exit 0, no `decision:block`. This is the safety-critical assertion (a mis-wired blocking hook on every Stop is the top plan risk).

## Related Code Files

- Modify: `.claude/hooks/mark_bash_start.py`, `track_skill_invocation.py`, `track_script_execution.py`, `track_subagent_outcome.py`, `emit_session_summary.py` (telemetry → wrapper)
- Modify: `.claude/hooks/memory_gap_hook.py`, `product_spec_critique_nudge.py` (early config-gate)
- Modify: `.claude/settings.json` (wire the 2 enforcement hooks into `Stop`)
- Read for context: `.claude/hooks/hook_runtime.py` (Phase 3)

## Implementation Steps

1. For each hook: extract current `main()` body into `core(data)`; drop the stdin read, the `{"continue":true}` print, and the outer `except: pass` (wrapper owns these).
2. Add the entrypoint `run_telemetry_hook(Path(__file__).stem, core)` AND keep a thin `main(raw)` shim delegating to it (test compatibility).
3. Move `from telemetry_paths import ...` to lazy position inside `core`.
4. Name is derived from `__file__.stem` (no manual string) → no drift; the `set(json keys)==stems` test (Phase 3) guards it.
5. After EACH hook, run the telemetry suite; do not proceed on red.
6. Add per-hook toggle integration tests: hook `false` in a tmp config → no telemetry record written + `{"continue":true}` emitted.

## Success Criteria

- [ ] All 5 telemetry hooks route through `run_telemetry_hook`; skeleton duplication gone; `main(raw)` shim kept.
- [ ] Phase 1 baseline green with zero behavioral-expectation changes (existing `mod.main(raw)` call-sites still work via shim).
- [ ] Toggling any of the 5 off (config) → that hook writes nothing, still continues.
- [ ] `mark_bash_start` ON → `ms` present; OFF → `avg_ms → "—"` degrade test green.
- [ ] No `core(data)` prints `{"continue":true}` itself (grep proves the contract is centralized).
- [ ] `track_skill_invocation` single key gates both event registrations.
- [ ] **Enforcement hooks wired into `settings.json` Stop; with default-false config BOTH no-op (exit 0, no block/nudge)** — dedicated test drives a real Stop payload and asserts exit 0.
- [ ] Enforcement explicit-true in config → original block/nudge behavior fires (exit-2 BLOCK path for `memory_gap` still works).

## Risk Assessment

- Risk: subtle behavior drift (e.g. dedup bucket key, name string typo) silently drops telemetry. Mitigation: name-match check (step 4) + per-hook suite run (step 5) + toggle integration test (step 6).
- Risk: lazy import moves a previously import-time failure into runtime. Mitigation: wrapper routes any such failure to `log_hook_error` and still continues — acceptable + now visible.
- Risk: `emit_session_summary` is the heaviest (Stop hook, aggregates session) — refactor last, extra scrutiny on the fail-open path.
