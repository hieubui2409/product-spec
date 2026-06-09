---
phase: 3
title: "Config gate + telemetry wrapper (in hook_runtime.py)"
status: completed
priority: P1
effort: "3-4h"
dependencies: [2]
---

# Phase 3: Config gate + telemetry wrapper (in hook_runtime.py)

## Overview

Extend the Phase-2 shared module `.claude/hooks/hook_runtime.py` with `hook_enabled(name)` (the per-hook toggle for ALL 7 — validate D3) and `run_telemetry_hook(name, core)` (the telemetry-only convenience wrapper, C/DRY). Author the own-config `product-spec-hooks.json` with all 7 keys. No hook is refactored yet — this phase only builds + tests the runtime so Phase 4 is a guarded swap. Note (red-team A): Phase 4 is a structural import rewrite, NOT a trivial mechanical swap — design so each telemetry hook's `core` can do a function-local `import telemetry_paths`.

## Requirements

- Functional: `hook_enabled(name) -> bool` reads `.claude/hooks/product-spec-hooks.json`. **Safety asymmetry (validate D3):** for the 5 telemetry stems missing key ⇒ ENABLED (mirror CK `isHookEnabled`); for the 2 enforcement stems (`memory_gap_hook`, `product_spec_critique_nudge`) missing key ⇒ **DISABLED** — a blocking hook must NEVER be fallback-enabled. Encode the enforcement set explicitly. Explicit `true`/`false` always wins. Global `CK_TELEMETRY_DISABLED` disables all telemetry stems (parity with `telemetry_paths.disabled()`); it does NOT force-enable enforcement.
- Functional: `name` is each hook's `Path(__file__).stem` (red-team F: single source = filename). Config keys == stems.
- Functional: `run_telemetry_hook(name, core_fn)` — reads stdin JSON, checks `hook_enabled(name)`; if disabled, `emit_continue()` and return WITHOUT importing `telemetry_paths`; else run `core_fn(data)` inside a fail-open guard routing exceptions to `log_hook_error`; always `emit_continue()` + exit 0.
- Functional: `read_stdin_json()`, `emit_continue()` helpers (the deduplicated skeleton) — may already exist from Phase 2.
- Non-functional: deferred import — `telemetry_paths` imported lazily inside `core_fn`; the runtime imports nothing heavy. **Honest framing (red-team G): controllability, not a perf win.**

## Architecture

- Everything lives in the SINGLE top-level `.claude/hooks/hook_runtime.py` (NOT a separate `hook_io.py` in telemetry/scripts) — validate D3 needs `hook_enabled` reachable by enforcement hooks too, and all 7 hooks already sit in `.claude/hooks/`, so one top-level module is the DRY-est, most consistent home.
- New config `.claude/hooks/product-spec-hooks.json` — 7 keys (5 telemetry = true, 2 enforcement = false) + a `"_README"` key documenting: missing telemetry key = enabled, missing enforcement key = disabled, `track_skill_invocation` gates both its event registrations.
- **Git-tracking (BLOCKER, in-phase):** `.gitignore:103` ignores this JSON (verified `git check-ignore`). Add `!/.claude/hooks/product-spec-hooks.json` in THIS phase; verify `git check-ignore` no longer ignores it.
- Config resolution: locate `.claude/hooks/` via `CLAUDE_PROJECT_DIR` with a module-ancestor-walk fallback. Config cache: parse once at module import into a module-level dict; expose `_reset_config_cache()` for tests. (Each hook is a fresh process, so a per-process cache always reflects the current file — toggles apply next invocation.)

## Related Code Files

- Modify: `.claude/hooks/hook_runtime.py` (add `hook_enabled`, `run_telemetry_hook`, helpers)
- Create: `.claude/hooks/product-spec-hooks.json`
- Create/extend: `.claude/hooks/__tests__/test_hook_runtime.py`
- Modify: `.gitignore` (re-include the JSON)
- Read for context: `.claude/skills/telemetry/scripts/telemetry_paths.py` (`disabled()`); CK `lib/` `isHookEnabled` semantics (reference only)

## Implementation Steps

1. Implement `read_stdin_json`, `emit_continue` if not already in Phase 2.
2. Implement `hook_enabled(name)` with the telemetry-vs-enforcement asymmetry; precedence: explicit key → (`CK_TELEMETRY_DISABLED` for telemetry) → default (telemetry enabled / enforcement disabled). Malformed config ⇒ fail to the SAFE default per class (telemetry enabled, enforcement disabled) AND `log_hook_error`.
3. Implement `run_telemetry_hook(name, core_fn)` using `hook_enabled` + `log_hook_error`; keep `telemetry_paths` out of the wrapper.
4. Author `product-spec-hooks.json` (5 true, 2 false, `_README`).
5. Add the `!` rule to `.gitignore`; verify `git check-ignore`.
6. Tests: telemetry enabled→core runs; telemetry disabled→core NOT called + `telemetry_paths` absent from `sys.modules` via SUBPROCESS (red-team MED) + still `{"continue":true}`; enforcement missing-key ⇒ disabled; enforcement explicit-true ⇒ enabled; malformed config ⇒ safe-default + crash-logged; `CK_TELEMETRY_DISABLED=1` ⇒ telemetry off, enforcement unaffected; `set(json keys) == set(all 7 stems)`.

## Success Criteria

- [ ] `hook_enabled` encodes the safety asymmetry (telemetry missing=on, enforcement missing=off); unit-proven both ways.
- [ ] `run_telemetry_hook` enforces `{"continue":true}` + exit-0 + fail-open centrally.
- [ ] Disabled telemetry hook proven (subprocess) to skip `telemetry_paths` import.
- [ ] `set(json keys) == set(all 7 stems)` test passes; keys derive from `__file__.stem`.
- [ ] Malformed config ⇒ safe per-class default + crash-log line.
- [ ] `git check-ignore product-spec-hooks.json` → NOT ignored. `.ck.json` untouched.

## Risk Assessment

- Risk: enforcement hook accidentally fallback-ENABLED → blocks everyone. Mitigation: explicit enforcement-set constant + a dedicated test asserting missing-key ⇒ disabled for both enforcement stems (this is the single most important test in the plan).
- Risk: config cache flakiness across tests. Mitigation: `_reset_config_cache()` + env-pointed config path in tests.
- Risk: empty `{}` config ambiguity. Mitigation: empty ⇒ telemetry enabled, enforcement disabled (documented in `_README`).
