---
phase: 3
title: "Drift nudge hook"
status: pending
priority: P2
effort: "0.5d"
dependencies: [1]
---

# Phase 3: Drift nudge hook

## Overview

An **opt-in** hook `spec_critique_nudge.py` that, after `--validate`/at Stop, nudges the PO to run `/spec-critique` when the spec has drifted ≥ `critique_drift_threshold` nodes (body_hash) since the last critique. Never auto-runs the critique (token + web cost). Mirrors `memory_gap_hook.py`'s posture: recommend-and-ask, nudge-once (honor `stop_hook_active`), cheap no-op early-exit, never registers itself.

## Requirements

- **Functional:** on the bound event, cheap-guard (spec tree exists?), call `critique_scan.py --drift` (via shared venv), and if `over == true` emit a one-line nudge: "spec đã đổi N node kể từ lần critique gần nhất — muốn nghe chửi thật? chạy `/spec-critique`". Nudge once per session per drift-state; honor `stop_hook_active`. Never blocks (advisory only — this is opinion, unlike `fence_breach`).
- **Non-functional:** Python via shared venv, stdlib only in the hook shim (it shells to critique_scan), always exits 0 (advisory). No writes to `docs/product/` from the hook itself (ephemeral markers in `$TMPDIR`, like memory_gap_hook). Reads `critique_drift_threshold` indirectly (critique_scan owns the read).

## Architecture

- **Template (corrected):** reuse from `.claude/hooks/memory_gap_hook.py` ONLY the SCAFFOLDING: the cross-dir `_import_*` / venv-shell pattern, the `$TMPDIR` session-keyed nudge marker, the no-op guard (early-exit if spec tree absent or session untouched), the `stop_hook_active` nudge-once logic. **Do NOT copy its output protocol** — memory_gap_hook emits `{decision:"block"}`+exit 2 (it is a BLOCKER). This hook is **advisory-only**: emit the nudge via Stop `hookSpecificOutput.additionalContext` + **exit 0** (the `.cjs` convention, e.g. `subagent-init.cjs`), NEVER `decision:block`, NEVER exit 2. This is a new output path, not a copy.
- **Event binding + CHEAP GATE (refined per validate gate):** event = Stop, but the hook does NOT build_graph on every Stop. Cheap gate first: compare timestamps of `last_validated.json` vs `last_critique.json` — only proceed if `last_validated` is NEWER (i.e., the PO ran `--validate` since the last critique). This makes the nudge fire "after --validate" (D11) with near-zero cost on ordinary stops (a 2-file stat, no graph build). If gate passes, then compute drift.
- **Drift source of truth:** the hook calls `critique_scan.py --drift --vs-validated --root <project>` which compares the validate-time body_hash snapshot against `last_critique.json` (marker-vs-marker; build_graph at most once, and only right after a validate — not every Stop). Reads `{over, changed_count, threshold}`. Single home for drift logic (DRY with Phase 1).
- **Throttle:** nudge-once per session (ephemeral marker keyed by session id + changed_count bucket). Optional ≤1/day passive recommend (mirror memory_gap_hook's recommend cadence) — keep minimal v1.

## Related Code Files

- Create: `.claude/hooks/spec_critique_nudge.py`
- Create: `.claude/skills/spec-critique/scripts/tests/test_spec_critique_nudge_hook.py` (load hook by path via `importlib.util.spec_from_file_location`, mirror `test_memory_gap_hook.py`)

## Implementation Steps

1. Read `memory_gap_hook.py` fully + `test_memory_gap_hook.py` for the load-by-path + tmp-tree fixture pattern.
2. Implement the Stop handler: no-op guard → shell `critique_scan.py --drift` → parse → if `over`, emit nudge (respecting `stop_hook_active` + session marker) → exit 0.
3. Implement ephemeral marker write/read in `$TMPDIR` (session-keyed); ensure idempotent nudge-once.
4. Ensure the hook NEVER writes under `docs/product/` and NEVER blocks (no exit 2 for this signal).
5. Tests: drift over threshold → nudge once (assert output is `hookSpecificOutput.additionalContext`, exit 0, **never `decision:block`/exit 2**); second call same session → silent; under threshold → silent; no spec tree → no-op exit 0; missing venv/critique_scan → graceful no-op (never crash the Stop event).

## Success Criteria

- [ ] Hook fires at Stop, calls `critique_scan --drift`, nudges only when `over==true`.
- [ ] Nudge appears at most once per session (honors `stop_hook_active` + marker); delivered via `hookSpecificOutput.additionalContext` + exit 0; **never `decision:block`, never exit 2** (test-asserted).
- [ ] No-op fast path when spec tree absent or session untouched; exit 0 in all paths.
- [ ] Graceful degrade if venv/critique_scan missing (no Stop-event crash).
- [ ] Hook writes nothing under `docs/product/`; markers only in `$TMPDIR`.
- [ ] Tests green.

## Risk Assessment

- **Stop-event noise:** nudge-once + threshold ≥3 keeps it rare. If still noisy, the passive ≤1/day cadence is the fallback (validate gate to confirm).
- **Hook crashing the Stop event:** wrap everything in try/except → exit 0; never raise. Mirror memory_gap_hook's defensive posture.
- **Coupling to critique_scan CLI:** the `--drift` contract is fixed in Phase 1; hook depends only on `{over}`. Low risk.
