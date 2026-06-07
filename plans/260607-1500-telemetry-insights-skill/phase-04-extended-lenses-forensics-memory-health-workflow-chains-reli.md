---
phase: 4
title: "Extended lenses: forensics + memory-health + workflow-chains + reliability"
status: complete
priority: P2
effort: "6h"
dependencies: [2, 3]
---

# Phase 4: Extended lenses: forensics + memory-health + workflow-chains + reliability

## Overview

Port the four remaining lenses, adapted to cleanmatic. forensics + workflow-chains use existing data; memory-health targets cleanmatic's memory dir; reliability consumes the Phase-2 `subagent-outcomes.jsonl`. Per port-research, ~160 LOC total, low risk (read-only, deterministic).

## Requirements
- Functional:
  - **forensics** (port `parse-session-jsonl-forensics.py`): reconstruct a session from its transcript — skills, tools, tokens, files, subagents, duration. `--session ID` / `--all-sessions`. Uses `sessions_dir()`.
  - **memory-health** (port `check-memory-system-health.py`): validate `memory_dir()` — frontmatter present, MEMORY.md sync (orphan files / dead index entries), `[[links]]` resolve, staleness. `--fix` dry-run only this round (no `--apply` writes — keep read-only per skill boundary).
  - **workflow-chains** (port `analyze-workflow-chains.py`): per-session skill chains from `invocations.jsonl` vs declared chains in `.claude/rules/skill-workflow-routing.md`; deviation ranking. **Strip** framework prefix logic.
  - **reliability** (port `track-subagent-reliability.py`): from `subagent-outcomes.jsonl` — success/api_error/timeout/blocked/unknown per agent type + top failure modes; `--days`. Gated on volume.
- Non-functional: read-only; pure-function gathers; fail-soft; gate applied to reliability + workflow.

## Architecture
- Lens modules `_shared/lib/lens_forensics.py`, `lens_memory_health.py`, `lens_workflow_chains.py`, `lens_reliability.py`; each `gather(...) -> dict`; dispatched by `analyze_telemetry.py --lens`.
- memory-health adaptation: HA's memory layout vs cleanmatic's `~/.claude/projects/<root>/memory/` (MEMORY.md index + per-file frontmatter + `[[name]]` links) — port the validation logic, repoint paths to `memory_dir()`; keep `--apply` OUT of scope (skill is read-only; memory writes belong to the product-spec memory flow).
- reliability reuses HA's error taxonomy mapping (vendored inline as a small dict, not an import).

## Related Code Files
- Create: `.claude/skills/_shared/lib/lens_forensics.py`, `lens_memory_health.py`, `lens_workflow_chains.py`, `lens_reliability.py`
- Modify: `.claude/skills/_shared/scripts/analyze_telemetry.py` (dispatch the 4 lenses)
- Create tests: one per lens (fixture-based parity)
- Read for context: the 4 HA source scripts; cleanmatic memory dir + `skill-workflow-routing.md`

## Implementation Steps (TDD)
1. **Test first** per lens vs Phase-1 fixtures (transcript / memory dir / routing doc / subagent-outcomes) → red.
2. Port + adapt each lens to green, one at a time (forensics → workflow → reliability → memory-health).
3. Wire `--lens forensics|memory|workflow|reliability|all` dispatch.
4. memory-health: assert `--fix` is dry-run only (no writes), and `--apply` is rejected/absent this round.

## Success Criteria
- [ ] All 4 lenses produce correct aggregates on fixtures; flat-slug adaptation verified (workflow/reliability).
- [ ] memory-health is read-only (no writes even with `--fix`); reliability + workflow gated on volume.
- [ ] forensics reconstructs a fixture session's skills/tools/tokens/files/duration.
- [ ] No lens raises on missing/empty/corrupt input.

## Risk Assessment
- **memory-health path/layout drift** between HA and cleanmatic. Mitigation: repoint to `memory_dir()`, test against a fixture memory dir mirroring cleanmatic's real one.
- **reliability empty** until subagents run post-Phase-2. Mitigation: gate + "no data" path; fixture proves logic.
- **Scope is the heaviest phase.** Mitigation: lenses are independent → land + test individually; a struggling lens can be deferred without blocking others (shrink point).
