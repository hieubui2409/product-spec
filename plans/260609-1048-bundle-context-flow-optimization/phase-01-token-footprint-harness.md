---
phase: 1
title: "Token-footprint harness"
status: completed
priority: P1
effort: "0.5d"
dependencies: []
---

# Phase 1: Token-footprint harness

## Overview

Deterministic, offline harness that measures **per-skill SKILL.md + ref token sizes** (the honest,
parseable unit — red-team MAJOR-3: the per-flag load-set is flat prose, not a table, so a per-flag token
number is ADVISORY only, never a gate), emits before/after JSON, and — critically — enforces a mechanical
**GATE co-presence check** (red-team BLOCKER-2 guard): if a loaded ref states a GATE as a *pointer*, the
GATE's authoritative full-prose home MUST be in that flag's load-set ∪ the always-on layer, else the
check fails. This is the **(a)-gate** + the safety guard the plan relies on. TDD.

## Requirements

- Functional:
  - **Primary metric (the gate):** per-skill token proxy of `SKILL.md` + each `references/*.md`
    individually + the skill total. `--baseline`/`--compare`/`--gate` (exit non-zero if SKILL.md or skill
    total GREW). Token proxy = `ceil(chars/4)` — documented approximate, relative-only (PO set no hard %).
  - **GATE co-presence check (the safety guard):** parse the always-on layer (root `CLAUDE.md`) for the
    authoritative GATE homes; for every `references/*.md`, if it mentions a GATE as a pointer ("see … GATE
    …") rather than full prose, assert that GATE's full-prose home is always-on (root `CLAUDE.md`) OR in
    the same flag's load-set. Fail (exit non-zero) on a pointer whose home isn't reachable. This mechanically
    blocks the silent-GATE-deletion failure mode.
  - **Advisory only (NOT a gate):** a best-effort flag→ref map parsed from the flat-prose "Loads
    references" section, printed for human reading. Explicitly labeled approximate; never gated on.
  - Cover all 4 skills; a skill with no flag table degrades gracefully (SKILL.md size only).
- Non-functional: stdlib only; JSON output; deterministic; `<200 LOC` (modularize if over); lives under a
  SHARED location both core skills can call.

## Architecture

```
context_footprint.py
  for skill in skills:
     parse SKILL.md → flag_table[], on_demand_refs[]
     flag→refs map (declared)           ──► detect declared/actual mismatch (flow-waste)
     per flag: tokens(SKILL.md)+Σ tokens(ref)  ──► path_cost
  --baseline → write JSON {skill:{flag:{tokens, refs[]}}, totals}
  --compare  → diff two JSONs → per-flag Δ + gate (exit 1 on regression)
```

Token proxy: `ceil(chars/4)` (or word-count blend) — documented approximate; the goal is relative
before/after, not absolute truth.

## Related Code Files

- Create: `.claude/skills/_shared/lib/context_footprint.py` (shared — both core skills + release/telemetry)
- Create: `.claude/skills/_shared/lib/__tests__/test_context_footprint.py`
- Read (inputs, not modified this phase): each `SKILL.md` + `references/*.md`

## Implementation Steps (TDD)

0. **Verified baseline (red-team MAJOR-4):** run the suite with the venv interpreter directly (NOT through
   the rtk hook, which mangles pytest paths) → record the real pass count (was 656 at plan-time; now 658 after the telemetry-hook plan added 2 tests — Phase 0 re-verifies the live count), resolve
   any collection error, commit that as the literal green baseline before building the harness gate.
1. **Test first** — `test_context_footprint.py` with tiny fixtures:
   - token proxy: monotone (bigger file → bigger number); deterministic.
   - `--baseline`/`--compare`: a shrunk ref → negative Δ; SKILL.md/total grown under `--gate` → non-zero.
   - **co-presence check:** a ref with a GATE pointer whose home is always-on → pass; a pointer whose home
     is neither always-on nor in the load-set → FAIL (exit non-zero). The core safety test.
   - malformed SKILL.md (no flag table) → graceful (size only, no crash).
2. Token proxy + per-skill aggregation → pass.
3. GATE co-presence check (parse always-on GATE homes; scan refs for pointers) → pass.
4. baseline/compare/gate CLI → pass.
5. Run against the live bundle → commit the **baseline JSON**.

## Success Criteria

- [ ] Phase-0 verified green baseline (real pass count, venv interpreter, collection errors resolved).
- [ ] Tests red→green (proxy, baseline/compare/gate, **co-presence check**, malformed).
- [ ] `--compare … --gate` exits non-zero when SKILL.md or a skill total grows.
- [ ] **Co-presence check** exits non-zero on a GATE pointer with an unreachable home.
- [ ] Baseline JSON committed; per-flag map printed as ADVISORY (labeled approximate), not gated.
- [ ] LOC < 200/file.

## Risk Assessment

- **Token proxy ≠ real tokens** → relative-only; mis-ranks tables vs prose, so used only to confirm a
  given edit shrank, never to prioritize what to cut (red-team MINOR-6).
- **Per-flag prose parse is unreliable** → demoted to advisory; the gate is per-skill SKILL.md size +
  co-presence, both deterministic (red-team MAJOR-3).
- **Co-presence false-negative misses a GATE** → keyword list of GATEs is explicit + fixture-tested;
  conservative (a pointer with no resolvable home always fails).
