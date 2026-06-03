---
phase: 2
title: "D12 cross-skill CI gate"
status: pending
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 2: D12 cross-skill CI gate

## Overview
Put product-spec (31 tests) + product-spec-critique (10 tests) under automated CI (today only
claude-pack has CI), and add a centralized shared bug-class test module asserting the cross-cutting
invariants that held across all 11 red-team cycles. Build BEFORE feature phases so new code is gated.

## Requirements
- Functional: PRs touching each skill run that skill's pytest suite in CI; a shared bug-class gate runs the symlink-escape / case-insensitive-bypass / untracked-asset assertions.
- Non-functional: fast + cheap — **1 OS × 2 Python** (3.11 + latest), NOT claude-pack's 3 OS × 3 Python. Deterministic only (no LLM/web — critique's opinion path stays out of CI).

## Key facts (from research)
- Workflows today: `claude-pack-ci.yml` (PR paths claude-pack/**, 3×3), `claude-pack-integration.yml` (weekly dogfood), `claude-pack-release.yml` (tag).
- 50 pytest files total: product-spec 31, critique 10, claude-pack 9. Existing bug-class tests: `test_fs_guard.py` (symlink escape), `test_safety_check.py` (case-insensitive `.lower()`), `test_core_failsoft_and_sentinels.py` (slug case-insensitive), `test_pack_determinism.py` (symlink reject + asset inclusion).
- "10-cycle red-team" = C9→C10→C11 chain (`plans/reports/cycle-11-…md`); symlink/case-insensitive/XSS held every cycle.

## Architecture
- Two PR-triggered workflows (or one matrix workflow with path filters) mirroring `claude-pack-ci.yml` shape but smaller matrix:
  - `product-spec-ci.yml` → paths `.claude/skills/product-spec/**`; run `pytest` in that skill's test dir.
  - `product-spec-critique-ci.yml` → paths `.claude/skills/product-spec-critique/**`; run its DETERMINISTIC tests only (exclude any that call web/LLM — confirm none do, or mark/skip).
- Shared bug-class gate: a thin pytest module (or a CI job) that imports/asserts the three invariant tests across skills. Prefer **referencing existing tests** via a named marker/job rather than duplicating logic (DRY) — e.g. a `bug_class` pytest marker applied to the existing tests + a CI job running `pytest -m bug_class` across all skills.

## Related Code Files
- Create: `.github/workflows/product-spec-ci.yml`
- Create: `.github/workflows/product-spec-critique-ci.yml`
- Create/Modify: add a `bug_class` pytest marker to existing invariant tests (`test_fs_guard.py`, `test_safety_check.py`, `test_core_failsoft_and_sentinels.py`, `test_pack_determinism.py`) + register marker in each skill's pytest config
- Reference: `.github/workflows/claude-pack-ci.yml` (shape to mirror, matrix to shrink)

## Implementation Steps
> **TDD:** this phase IS the test gate — validate it by making a workflow run red on a deliberately-broken invariant (e.g. temporarily un-mark a `bug_class` test or introduce a symlink-escape) and confirm CI catches it, then revert to green.
1. Confirm each skill's venv-based test invocation works headless in CI (`.claude/skills/.venv/bin/python3 -m pytest .claude/skills/<skill>/scripts/tests`). Reuse claude-pack-ci's install step.
2. Author `product-spec-ci.yml` (1 OS × 2 Python, path-filtered). Ensure venv bootstrap (install.sh) runs.
3. Author `product-spec-critique-ci.yml`; verify its 10 tests are deterministic (no network/LLM). If any reach web, exclude via marker/skip in CI.
4. Tag the 4 existing invariant tests with `@pytest.mark.bug_class`; register the marker; add a CI job (in one workflow or a small `cross-skill-bug-class.yml`) running `pytest -m bug_class` across all 3 skills.
5. Run all suites locally green before pushing; verify CI goes green on a no-op PR.

## Success Criteria
- [ ] product-spec + critique CI workflows exist, path-filtered, 1 OS × 2 Python, green on current tree.
- [ ] `pytest -m bug_class` selects the symlink / case-insensitive / untracked-asset tests across skills and passes.
- [ ] No test logic duplicated (marker references existing tests).
- [ ] critique CI runs deterministic tests only (no web/LLM).
- [ ] All 50 existing tests still pass; no flakiness introduced.

## Risk Assessment
- Risk: venv bootstrap in CI differs from local (sandbox `/tmp` venv caveat in README). Mitigate by running from project root + system python fallback as documented.
- Risk: a critique test secretly hits the network → CI flake. Mitigate by auditing the 10 tests in step 3.
- Keep matrix small; resist scope-creep into porting the manual 59-agent red-team (non-deterministic, not a gate).
