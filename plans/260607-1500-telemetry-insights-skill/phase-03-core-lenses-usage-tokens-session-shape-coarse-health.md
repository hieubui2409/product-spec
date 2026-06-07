---
phase: 3
title: "Core lenses: usage+tokens + session-shape + coarse-health"
status: complete
priority: P2
effort: "4h"
dependencies: [1]
---

# Phase 3: Core lenses: usage+tokens + session-shape + coarse-health

## Overview

Port the headline lens — `scan-skill-usage-and-tokens.py` (S1: invocation counts + per-skill token attribution + never-used) — adapted to flat slugs, plus two cheap lenses off existing sinks: session-shape (sessions.jsonl) and coarse-health (hook-telemetry exit + the new `ms`). This is the data spine the renderers and skill consume. Can run parallel to Phase 2 (uses only existing sinks; coarse-health's `ms` column degrades if Phase 2 not done).

## Requirements
- Functional:
  - **usage+tokens**: port `gather_invocations` (read `invocations.jsonl` {ts,skill}; honor `--days`/`--since`) + `gather_tokens` (walk transcripts, Skill-span model, sum `message.usage` input+output) + `never_used` (catalog − used) + the "_No data yet_"/gate path. **Strip** `framework_of`/`to_dir_id` → flat slug identity; catalog = `.claude/skills/*/SKILL.md` slugs.
  - **session-shape**: from `sessions.jsonl` — count, avg/median `duration_s`, total `files_modified`, subagents, skill co-occurrence.
  - **coarse-health**: from `hook-telemetry.jsonl` — per-script run/error counts (`exit`), and avg `ms` when present (Phase 2). Labelled "approx".
  - All gated: below-volume → counts + caveat, no recommendations.
- Non-functional: pure functions returning dicts (render-agnostic); fail-soft on bad/missing/unknown sinks; deterministic stable sort; <200 LOC per module.

## Architecture
- `analyze_telemetry.py` = CLI front (`--lens usage|session|health|all`, `--days/--since/--top/--min-volume/--format`).
- Lens modules in `_shared/lib/`: `lens_usage_tokens.py` (the port), `lens_session_shape.py`, `lens_health.py`. Each exposes `gather(...) -> dict`. Shared catalog loader + gate from Phase 1.
- Token attribution carries the port's "approximate, directional, not billing-exact" docstring caveat.

## Related Code Files
- Create: `.claude/skills/_shared/scripts/analyze_telemetry.py` (CLI dispatch)
- Create: `.claude/skills/_shared/lib/lens_usage_tokens.py` (ported+adapted), `lens_session_shape.py`, `lens_health.py`
- Create tests: `test_lens_usage_tokens.py`, `test_lens_session_shape.py`, `test_lens_health.py`
- Read for context: HA `scan-skill-usage-and-tokens.py` (the source), cleanmatic `telemetry_paths.py`

## Implementation Steps (TDD)
1. **Test first (parity):** `test_lens_usage_tokens.py` vs Phase-1 fixtures — assert counts, token sums (span model), never-used, below-gate suppression, flat-slug handling (no framework split). Run → red.
2. Port + adapt `lens_usage_tokens.py` → green.
3. **Test:** session-shape + health snapshots (incl. `ms` present/absent) → red; implement → green.
4. Wire `analyze_telemetry.py --lens … --format ascii` (ascii stub → full in Phase 5; md/json reuse formatters now).

## Success Criteria
- [ ] usage+tokens parity with fixtures incl. token attribution; flat slugs; never-used correct; gate honored.
- [ ] session-shape + coarse-health correct; `ms` column degrades gracefully when Phase 2 absent.
- [ ] Lens functions pure + render-agnostic; corrupt/missing/unknown sinks never raise.

## Risk Assessment
- **Transcript span sparsity** (Skill tool_use ≈0.17%) → thin token data. Mitigation: gate + the port's "no data" path; tokens shown as directional.
- **Catalog slug mismatch** (`cleanmatic:product-spec` vs dir `product-spec`). Mitigation: normalize once in the loader; test both forms.
