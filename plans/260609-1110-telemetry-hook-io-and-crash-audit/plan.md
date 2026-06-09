---
title: "Project hook runtime: config-gate + crash audit (all 7 hooks)"
description: ""
status: complete
priority: P2
branch: "master"
tags: []
blockedBy: []
blocks: []
created: "2026-06-09T04:30:13.943Z"
createdBy: "ck:plan"
source: skill
---

# Project hook runtime: config-gate + crash audit (all 7 hooks)

## Overview

Refactor 7 project-authored hooks (NOT the 11 CK `.cjs` hooks). Source: `plans/reports/brainstorm-260609-1110-optimize-project-telemetry-hooks-report.md`.

**Brutal-honest framing:** exit-codes already correct across all 7 hooks — no bug to fix. This is a maintainability + observability + perf-controllability refactor, not a correctness patch. Article's exit-1-vs-2 trap does NOT apply here.

**Deliverables (A+B+C+D from brainstorm; red-team + validate revised 2026-06-09):**
- **One shared runtime module — `.claude/hooks/hook_runtime.py` (TOP-LEVEL, zero-dep, git-tracked via `!*.py`)** serving ALL 7 project hooks: `read_stdin_json()`, `emit_continue()`, `hook_enabled(name)` (reads `product-spec-hooks.json`), `log_hook_error(name, exc)` (crash audit), `run_telemetry_hook(name, core)` (telemetry convenience). Replaces the original two-module split (`hook_io.py` + `hook_audit_log.py`) — validate decision: config-gate covers all 7, so the config reader must be top-level reachable by every hook, making one module the DRY-est, most consistent home.
- **C (DRY)** — `run_telemetry_hook` collapses the read-stdin / parse / emit-`{"continue":true}` / fail-open skeleton (lapping 5× today) for the 5 telemetry hooks.
- **B (toggle) + A (controllability, NOT perf)** — own-config `.claude/hooks/product-spec-hooks.json` (committed, NOT `.ck.json`) gates **ALL 7 hooks** (validate decision: "wire-always + config-gate cả 7"). **Honest framing (red-team G):** controllability, not perf — for the common all-on PO it adds a tiny per-process config read. Do NOT sell as perf.
- **D (observability)** — `log_hook_error()` applied to ALL 7 hooks; silent crashes leave a trace in `.claude/hooks/.logs/hook-crashes.log`. **Always-on by default** (validate decision), disable via `CK_HOOK_AUDIT_DISABLED=1`.

**Validate decisions (2026-06-09, recorded in Validation Log):**
1. `mark_bash_start` default **true** (preserve `ms`/`avg_ms`).
2. Crash-log **always-on** + env disable.
3. **Wire-always + config-gate all 7** — the 2 enforcement hooks (`memory_gap_hook`, `product_spec_critique_nudge`) move from opt-in-by-wiring to **wired-in-bundle, gated by config (default false)**. Config can't enable an unwired hook (read happens inside the process), so the bundle must wire them; default-false preserves today's off behavior. **Scope expansion accepted:** touches `settings.json` (Stop wiring) + installer `--memory-hook`/`--critique-hook` semantics + release docs.
4. **Cut a release version** this round (Phase 5 bumps + cuts, not just stages).

**Hard boundaries:** do NOT touch CK `.cjs` hooks, do NOT touch `.ck.json`, keep `mark_bash_start` (toggleable, do NOT drop), preserve fail-open + `{"continue":true}` contract on the 5 telemetry hooks and the exit-2 BLOCK / exit-0 ALLOW contracts on the 2 enforcement hooks.

### Red-team blockers folded in (verified 2026-06-09)

1. **Git-tracking (BLOCKER):** `.gitignore:103 /.claude/hooks/*` ignores everything except top-level `*.py` (`:104 !*.py`, non-recursive). So: `hook_runtime.py` MUST sit at `.claude/hooks/` top-level (verified tracked via `!*.py`); `product-spec-hooks.json` MUST get an explicit `!/.claude/hooks/product-spec-hooks.json` rule. `lib/` is ck-managed + fully untracked → forbidden home for our code. Git+manifest fixes land in the SAME phase that creates each file (Phase 2/3), not deferred to Phase 5.
2. **Test entrypoint (BLOCKER):** all existing tests call `mod.main(raw)` directly (e.g. `test_bash_duration_pairing.py:55-56`). Each telemetry hook MUST keep a `main(raw)`-compatible shim that delegates to `run_telemetry_hook`. Criterion is "zero behavioral-expectation changes" — NOT "zero test edits".
3. **Name drift (HIGH):** derive the config-key/name from `Path(__file__).stem` (single source) + a test asserting `json keys == hook stems`.

**TDD:** existing tests (`.claude/hooks/__tests__/test_telemetry_hooks.py`, `telemetry/scripts/tests/`) lock behavior. Phase 1 captures current behavior FIRST; later phases keep it green with zero behavioral-expectation changes — test call-sites/entrypoints may adapt (a `main(raw)` shim keeps them untouched), plus net-new tests for the new module/toggle/log.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Lock current behavior (TDD baseline)](./phase-01-lock-current-behavior-tdd-baseline.md) | Done (baseline verified — existing suites already covered all 7 hooks) |
| 2 | [Shared crash audit-log lib (all 7 hooks)](./phase-02-shared-crash-audit-log-lib-all-7-hooks.md) | Done |
| 3 | [Config gate + telemetry wrapper (in hook_runtime.py)](./phase-03-hook-io-wrapper-own-config-toggle.md) | Done |
| 4 | [Refactor 5 telemetry hooks + gate & wire 2 enforcement hooks](./phase-04-refactor-5-telemetry-hooks-onto-wrapper.md) | Done (wiring via register_telemetry_hooks.py — settings.json is gitignored/not shipped, see Deviation Log) |
| 5 | [Installer + docs + release cut](./phase-05-docs-release-manifest.md) | Done EXCEPT owner-gated release cut (D4: version + tag push) + blocked by unrelated manifest rule-drift |

## Dependencies

None blocking. Overlapping plans (`260601-1744-product-spec-memory-hook-scaling`, `260602-0026-strengthen-memory-write-enforcement` [completed], `260607-1500-telemetry-insights-skill` [complete], `260609-0847-learning-loop-outcome-tracking` [done]) PRODUCED the hooks being refactored — no forward dependency, no `blockedBy` needed.

## Acceptance Criteria (whole plan)

- [ ] All 7 hooks import the single top-level `hook_runtime.py`; 5 telemetry hooks route through `run_telemetry_hook` (via a kept `main(raw)` shim), each ≤ ~20 lines of hook-specific logic.
- [ ] All 7 hooks call `log_hook_error()` in their failure path; a forced exception leaves exactly one line in `.claude/hooks/.logs/hook-crashes.log` and the hook still emits its normal output + correct exit code (incl. `memory_gap` exit-2 BLOCK path unchanged).
- [ ] `product-spec-hooks.json` has all 7 keys; telemetry default **true**, enforcement default **false**. Setting a key `false` no-ops that hook (telemetry: before `telemetry_paths` import, proven by SUBPROCESS no-import test; enforcement: early ALLOW return before any detector/graph work).
- [ ] The 2 enforcement hooks are wired into `settings.json` Stop; with default-false config they no-op (exit 0) — verified they do NOT block when config-disabled.
- [ ] Config key derived from `Path(__file__).stem`; test asserts `set(json keys) == set(all 7 hook stems)`.
- [ ] `git ls-files` shows `hook_runtime.py` AND `product-spec-hooks.json` TRACKED; dry-run pack includes both; crash log + `__tests__` excluded.
- [ ] `mark_bash_start` ON → `ms`/`avg_ms` still rendered; OFF → health lens degrades to `—` (no crash).
- [ ] `CK_TELEMETRY_DISABLED` global kill-switch still works alongside per-hook config.
- [ ] Installer `--memory-hook`/`--critique-hook` updated to flip the config flag (now that wiring is permanent); release docs updated; version cut.
- [ ] All pre-existing telemetry tests pass with zero behavioral-expectation changes (call-site/entrypoint adaptation allowed).
- [ ] No `.cjs` hook and no `.ck.json` modified.

## Top Risk (validate-surfaced)

**Wiring a BLOCKING hook (`memory_gap`, exit 2) always-on in the bundle.** With default-false config it no-ops, but a bug in `hook_enabled()` returning true-when-unset, or a config typo, could make `memory_gap` block Stop for EVERY user. Mitigations: (a) default-false is explicit + unit-tested; (b) `hook_enabled` fails to DISABLED for enforcement hooks specifically (enforcement opt-in must be a deliberate true, never a fallback-enabled); (c) the existing `_FENCE_BLOCK_CAP` backstop still caps self-blocks; (d) Phase 1 locks the no-op-when-disabled path before wiring.

## Validation Log

### Session 1 — 2026-06-09 (post red-team)

Verification pass: 0 failures. All cited paths confirmed — `.gitignore:103/104` ignore rules, test call-sites `mod.main(raw)`, `pack.manifest.yaml hooks:` is an EXPLICIT 7-file list (telemetry/scripts ships via `skills:` walk), telemetry tests dir exists.

Decisions:
- **D1 `mark_bash_start` default = true** — preserve `ms`/`avg_ms`; PO disables if unwanted.
- **D2 crash-log always-on** + `CK_HOOK_AUDIT_DISABLED` env off-switch.
- **D3 wire-always + config-gate all 7** — enforcement hooks move opt-in-by-wiring → wired-in-bundle + config-gated (default false). Constraint surfaced to PO: config cannot enable an unwired hook. Scope expansion to `settings.json` + installer + release docs ACCEPTED by PO. **Safety asymmetry:** `hook_enabled` defaults telemetry keys to ENABLED on missing, but enforcement keys to DISABLED on missing (a blocking hook must never be fallback-enabled).
- **D4 cut release version** this round.

Propagated to: plan deliverables + acceptance criteria + Phases 2-5 (hook_runtime.py consolidation, enforcement wiring/gating, installer change, version cut).

### Deviation Log — Implementation (2026-06-09)

**Wiring mechanism: registrar, not "shipped settings.json".** The plan prose (Phases 4-5)
assumed enforcement hooks wire into a *bundled* `settings.json`. That premise is false:
`.claude/settings.json` is gitignored (`.gitignore:76 /.claude/*`) and the manifest sets
`include_settings: false` — it is NEVER packed. Validate-decision **D3** ("wired-in-bundle,
config-gated default-false") was instead realized via `register_telemetry_hooks.py` (the
installer auto-runs it): it now wires both enforcement hooks (memory_gap on Stop +
PostToolUse:Edit|Write|MultiEdit `--post-tool-use`; critique on Stop), guarded by `ALL_CMDS`
so the reconcile pass can't strip them. This repo's local `settings.json` was wired by running
that registrar. Installers' `--memory-hook`/`--critique-hook` flip the config flag (default
false → no-op). Reviewed across 3 waves: faithfully delivers D3, no safety regression. The
`--*-hook-shared` flags became back-compat aliases (one committed config file now).

### Whole-Plan Consistency Sweep — Session 1

Swept all 6 files. Fixed: stale `hook_audit_log.py`/`hook_io.py` module refs → `hook_runtime.py`; plan title + phase 3/4/5 table titles synced to actual phase titles; version-defer language removed (now "cut"); "5 telemetry" vs "all 7" reconciled (telemetry-scoped vs all-7-scoped each stated explicitly). Remaining `hook_io.py` mentions are intentional ("consolidated, no hook_io"). Phase file titles == table titles. **0 unresolved contradictions.**
