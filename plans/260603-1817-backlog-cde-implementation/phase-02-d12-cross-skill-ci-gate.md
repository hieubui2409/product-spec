---
phase: 2
title: "D12 cross-skill CI gate"
status: pending
priority: P1
effort: "1.5d"
dependencies: [1]
---

# Phase 2: D12 cross-skill CI gate

> **Revised after red-team (2026-06-03).** Folds H5 (marker registration), H6 (per-skill-dir scoping),
> offline enforcement, and the test-count re-baseline.

## Overview
Put product-spec + product-spec-critique under automated CI (today only claude-pack has CI), add a
shared `bug_class` selector over the cross-cutting invariants, and enforce offline + per-skill scoping.
Build BEFORE feature phases so new code is gated.

## Requirements
- Functional: PRs touching each skill run that skill's pytest in CI; `pytest -m bug_class` selects the symlink / case-insensitive / untracked-asset invariants across skills.
- Non-functional: fast + cheap — **1 OS × 2 Python** (3.11 + latest), NOT 3×3. Deterministic + **offline** (no LLM/web).

## Key facts (from research + red-team)
- Workflows today: `claude-pack-ci.yml` (3×3), `claude-pack-integration.yml` (weekly), `claude-pack-release.yml` (tag).
- **Test-count re-baseline (Scope F8):** anchor on *collected cases*, not files. Re-baseline via `pytest --co -q` per skill at implementation time; the headline "no reduction in passing cases" replaces "50 tests untouched". (File counts ≈ product-spec 30, critique 10, claude-pack 10 — informational only.)
- **H5 — marker config:** claude-pack `pyproject.toml:4-7` sets `--strict-markers` + registers only `integration`. product-spec + critique have **NO pytest config at all**. An unregistered `bug_class` marker = collection ERROR under `--strict-markers` → would turn existing claude-pack CI red.
- **H6 — import mechanism:** product-spec/critique imports resolve via each skill's `conftest.py` `sys.path.insert` (product-spec `conftest.py:24-25`, critique `:11-13`), NOT claude-pack's `install.sh` `.pth`. CI must run pytest **scoped to each skill's tests dir** so its conftest loads; a combined-root run races the two conftests.
- Existing invariant tests: `test_fs_guard.py:79` (symlink escape), `test_safety_check.py:95-118` (case-insensitive), `test_pack_determinism.py:145` (symlink dropped+WARN — wording note, not reject).

## Architecture
- Two PR-triggered workflows, path-filtered, **1 OS × 2 Python**, each running pytest **scoped to that skill's tests dir** (H6):
  - `product-spec-ci.yml` → paths `.claude/skills/product-spec/**` → `pytest .claude/skills/product-spec/scripts/tests`
  - `product-spec-critique-ci.yml` → paths `.claude/skills/product-spec-critique/**` → its deterministic tests dir
- **H5 — register `bug_class` everywhere before tagging:** add `bug_class` to claude-pack `pyproject.toml` markers; **create** `pyproject.toml` (or `pytest.ini`) for product-spec + critique registering `bug_class` (+ any markers their tests use). Only then tag the 4 invariant tests `@pytest.mark.bug_class`. A `cross-skill-bug-class.yml` job runs `pytest -m bug_class` per skill (not combined-root).
- **Offline enforcement (Security F7):** add an autouse socket-blocking conftest fixture (or `pytest-socket --disable-socket`) to the critique CI so any future net call fails loudly instead of silently exfiltrating. Audit the 10 critique tests are offline today (`example.com` strings are hash fixtures, no `requests`/`urllib`).

## Related Code Files
- Create: `.github/workflows/product-spec-ci.yml`, `.github/workflows/product-spec-critique-ci.yml`, `.github/workflows/cross-skill-bug-class.yml`
- Create: `product-spec/pyproject.toml` + `product-spec-critique/pyproject.toml` (register `bug_class` + existing markers)
- Modify: `claude-pack/pyproject.toml` (add `bug_class` to markers)
- Modify: tag `@pytest.mark.bug_class` on `test_fs_guard.py`, `test_safety_check.py`, `test_core_failsoft_and_sentinels.py`, `test_pack_determinism.py`
- Reference: `.github/workflows/claude-pack-ci.yml` (shape to mirror, matrix to shrink)

## Implementation Steps
> **TDD:** validate the gate by making a workflow go RED on a deliberately-broken invariant (un-mark a bug_class test / introduce a symlink-escape), confirm CI catches it, then revert to green.
1. Register `bug_class` in all 3 skills' pytest config FIRST (create 2 new configs); confirm claude-pack CI stays green after adding the marker.
2. Tag the 4 invariant tests `@pytest.mark.bug_class`.
3. Author `product-spec-ci.yml` + `product-spec-critique-ci.yml` (1 OS × 2 Python, path-filtered, **scoped to each skill's tests dir**); reuse claude-pack-ci's install for pyyaml/pytest only (not for module resolution).
4. Add socket-blocking offline enforcement to critique CI; audit the 10 tests are offline.
5. Author `cross-skill-bug-class.yml` running `pytest -m bug_class` per skill.
6. Re-baseline passing-case counts via `pytest --co -q`; record as the regression anchor.

## Success Criteria
- [ ] product-spec + critique CI workflows exist, path-filtered, 1 OS × 2 Python, scoped per-skill-dir, green on current tree.
- [ ] `bug_class` registered in all 3 configs; tagging does NOT break claude-pack `--strict-markers` CI.
- [ ] `pytest -m bug_class` selects symlink / case-insensitive / untracked-asset across skills, per-skill (not combined-root).
- [ ] critique CI is offline-enforced (socket-blocked); deliberate net call fails loudly.
- [ ] Regression anchor = collected passing-case counts (not "50 files"). No reduction. Full suite green.

## Risk Assessment
- Risk: forgetting marker registration → claude-pack CI collection error (H5). Mitigated by step-1 ordering.
- Risk: combined-root collection races conftests (H6) → per-skill-dir scoping only.
- Resist porting the manual 59-agent red-team (non-deterministic, not a gate).
