---
phase: 2
title: "Shared crash audit-log lib (all 7 hooks)"
status: completed
priority: P1
effort: "2-3h"
dependencies: [1]
---

# Phase 2: Shared crash audit-log lib (all 7 hooks)

## Overview

Create the single shared runtime module **`.claude/hooks/hook_runtime.py`** (top-level, zero-dep) and land its first responsibility: **D (observability)** for ALL 7 project hooks. A fail-open crash logger so a swallowed `except` leaves a trace instead of dying silently — the "crash âm thầm" pitfall. (Phase 3 adds `hook_enabled` + `run_telemetry_hook` to this SAME module.) This module is the consistency backbone validate decision D3 requires: every hook imports it.

## Requirements

- Functional: `log_hook_error(hook_name: str, exc: BaseException) -> None` appends one line (UTC ts, hook name, exception type, message, short traceback tail) to `.claude/hooks/.logs/hook-crashes.log`.
- Functional: the logger is itself fail-open — if IT cannot write (disk full, missing dir), it swallows and returns; it must NEVER raise into a hook's failure path.
- Non-functional: ZERO third-party imports and ZERO import of telemetry/skill code (the 2 enforcement hooks must stay decoupled from the telemetry skill). Stdlib only.
- Non-functional: size cap / coarse rotation so the log cannot grow unbounded across long sessions (truncate-or-rotate at a fixed byte ceiling, e.g. 256 KB — confirm value at impl).
- Non-functional: honor a disable env (e.g. `CK_HOOK_AUDIT_DISABLED=1`) and the pytest gate so tests stay clean.

## Architecture

- New module **`.claude/hooks/hook_runtime.py` (TOP-LEVEL — NOT `lib/`)**. Red-team D-bis (verified): `.gitignore:103 /.claude/hooks/*` ignores all except top-level `*.py` (`:104 !*.py`, non-recursive); `lib/` is ck-managed + fully untracked. A module under `lib/` would never ship and every hook's import would break on recipient/CI. Top-level placement is auto-tracked by `!*.py` (verified: `git check-ignore` re-includes a top-level `.py`).
- This phase implements ONLY `log_hook_error()` (+ the trivial `read_stdin_json`/`emit_continue` helpers if convenient). `hook_enabled` + `run_telemetry_hook` are added to the same file in Phase 3.
- All 7 hooks (5 telemetry + 2 enforcement) live in `.claude/hooks/` → they import via `sys.path.insert(0, _HOOKS_DIR)` (each already computes `_HOOKS_DIR = dirname(abspath(__file__))`), then `import hook_runtime`. One identical 3-line snippet in all 7 (red-team C: no 7 hand-rolled variants).
- Ordering hazard (red-team C): enforcement hooks already `sys.path.insert(0, <skill-scripts>)` (`memory_gap_hook.py:111`). Insert the hooks-dir path with `sys.path.append` (or insert AFTER, never index-0-shadowing the skill path) and import the logger LAZILY inside the `except` so the hot allow-path pays nothing.
- Log dir `.claude/hooks/.logs/` already exists (used by `lib/hook-logger.cjs`). New filename `hook-crashes.log`.
- Enforcement hooks already have `try/except → return ALLOW_EXIT` in `main()`; insert one fail-open `log_hook_error("<stem>", e)` call inside that `except` before the return. No control-flow change; the logger call is itself wrapped so it can never raise back into the except (red-team E).

## Related Code Files

- Create: `.claude/hooks/hook_runtime.py` (top-level)
- Create: `.claude/hooks/__tests__/test_hook_runtime.py`
- Modify: `.claude/hooks/memory_gap_hook.py` (lazy `log_hook_error` in `main()` except)
- Modify: `.claude/hooks/product_spec_critique_nudge.py` (same)
- Modify: `.gitignore` (add `!/.claude/hooks/hook_runtime.py` defensively even though `!*.py` already covers it; document intent) — and fix the broken `:121 claude/hooks/.logs/` → `/.claude/hooks/.logs/` so the crash log is explicitly ignored
- Modify: `.claude/pack.manifest.yaml` (ensure `hook_runtime.py` is selected for the bundle)
- Read for context: `.claude/hooks/lib/hook-logger.cjs` (`.logs/` conventions, byte-cap parity)

## Implementation Steps

1. Write `hook_runtime.py`: resolve `.logs/` relative to the file; `log_hook_error` formats one JSON-ish line; wrap all IO in try/except-pass; apply byte-cap (stat → if over ceiling, truncate/rotate to `.1`).
2. Add disable gate (`CK_HOOK_AUDIT_DISABLED` + `PYTEST_CURRENT_TEST`).
3. Tests: forced exception → exactly one new line; unwritable dir → no raise, hook unaffected; over-cap → rotation/truncation happens; disabled env → no write.
4. Confirm git-tracking + shipping NOW (not Phase 5): `git add -n` shows `hook_runtime.py` trackable; fix `.gitignore:121`; add manifest entry; assert `git check-ignore` does NOT ignore it.
5. Wire into `memory_gap_hook.py`: lazy `import hook_runtime` + `hook_runtime.log_hook_error("memory_gap_hook", e)` inside the `main()` except branch (keep `return ALLOW_EXIT`); the call itself is fail-open.
6. Wire into `product_spec_critique_nudge.py`: same pattern in its `main()` except branch.
7. Re-run Phase 1 baseline — enforcement-hook exit codes (0 allow / 2 block for memory_gap; 0 for critique_nudge) MUST be unchanged; the real BLOCK-path test (Phase 1 step 3) must still pass.

## Success Criteria

- [ ] `hook_runtime.py` at top-level, stdlib-only, fail-open, byte-capped, env-disablable.
- [ ] `git check-ignore .claude/hooks/hook_runtime.py` → NOT ignored; manifest selects it; `.gitignore:121` fixed.
- [ ] Forced exception in `memory_gap_hook` / `critique_nudge` → one line in `.logs/hook-crashes.log`, exit code unchanged (incl. exit-2 BLOCK), normal output unchanged.
- [ ] Logger IO failure never propagates into a hook (unwritable-dir test).
- [ ] Phase 1 baseline still green (BLOCK-path test included).

## Risk Assessment

- Risk: adding sys.path/import to enforcement hooks perturbs their import resolution order. Mitigation: insert `lib` path AFTER their existing skill-scripts path insert; import lazily inside the except if needed to avoid any import-time cost on the hot allow-path.
- Risk: the logger itself becomes a new silent-failure point. Mitigation: it is intentionally write-only + swallow; covered by the unwritable-dir test.
- Risk: log line leaks sensitive payload. Mitigation: log exception type/message/traceback ONLY — never the stdin payload.
