---
title: "Telemetry usage-and-health skill (cleanmatic:telemetry) — port from com:skill-analytics"
description: ""
status: complete
priority: P2
branch: "master"
tags: []
blockedBy: []
blocks: []
created: "2026-06-07T08:40:58.896Z"
createdBy: "ck:plan"
source: skill
---

# Telemetry usage-and-health skill (cleanmatic:telemetry) — port from com:skill-analytics

## Overview

Give the (non-technical, Vietnamese) PO a one-command read on **how their skills are used + whether scripts/subagents are healthy + a thin effectiveness proxy**, narrated in plain Vietnamese, with ascii/md/mermaid/json reports.

**Origin = xia PORT, not from-scratch (DRY).** `human-analyzer`'s `com:skill-analytics` v1.3.0 already implements 11 read-only observability lenses on the SAME telemetry/transcript model. This plan PORTS the relevant lenses into cleanmatic (3 flat skills, no framework prefix), adds the genuine gap (**ascii + mermaid + Vietnamese non-tech narration**), and adds the two sinks cleanmatic lacks. Source skill: `~/Documents/human-analyzer/.claude/skills/com-skill-analytics/`.

**Architecture:** script gathers/renders (deterministic), skill narrates/judges (LLM) — the "GOLDEN RULE #4" split both repos already follow.
- **SCRIPTS** under `.claude/skills/_shared/scripts/` (siblings of `run_evals.py`) + lens modules in `_shared/lib/`. Local PO tooling, **NOT shipped**.
- **SKILL** `cleanmatic:telemetry` — non-tech VI face: runs the lenses, narrates, cross-references the catalog. Framed honestly as **"usage & health"**.

**Scope = Full (PO chose, twice, after seeing cost):** 8 lenses — usage+tokens, session-shape, coarse-health, forensics, memory-health, workflow-chains, reliability, script-duration/perf — plus the validate-pass effectiveness proxy. Two new sinks required (see below). **Effort is non-trivial (~2–3 days, ~300–400 LOC + 2 hooks).** Red-team (Phase 8) will re-challenge the Full scope; PO can still shrink at validate.

**CRITICAL feasibility correction (planner judgment over the port-research's atexit suggestion):** HA captures script duration/errors via an `atexit`/`excepthook` inside `platform_lib/telemetry.py`, auto-imported by every script. **cleanmatic must NOT copy this**: product-spec scripts ARE shipped, and `_shared` is NOT bundled (`follow_shared:false`) → importing a telemetry module into a shipped script = `ModuleNotFoundError` on the recipient + telemetry behavior leaking into the bundle. This is the SAME class as the earlier red-team F1. Therefore:
- script-duration → **hook-only**, via PreToolUse+PostToolUse:Bash pairing (Pre stamps start, Post computes `ms`). Touches no script.
- subagent reliability → **hook-only**, a new SubagentStop hook → `subagent-outcomes.jsonl`.
- rich `errors.jsonl` crash-log (stack traces via excepthook) → **DROPPED** (can't instrument shipped scripts); script failures stay as the coarse `exit` already in `hook-telemetry.jsonl`.

## Key Decisions

| # | Decision | Driver |
|---|----------|--------|
| D1 | PORT `scan-skill-usage-and-tokens.py` + `formatters.py` + 4 lens scripts from `com:skill-analytics`; ADAPT: strip `skill_ids.framework_of`/`to_dir_id` → flat slugs. | xia DRY |
| D2 | **Token attribution INCLUDED** (reverses earlier "defer D7"): the port already implements the exact span model; it works on cleanmatic's transcripts. Sparse-data handled by the gate. | port |
| D3 | **Low-volume gate** = the port's existing `_No invocation data yet_` path, generalized: below N, show raw counts + "chưa đủ dữ liệu", suppress prune advice. | F2 |
| D4 | Formats = **ascii + md + mermaid + json**. md/json come free from the port; **ascii + mermaid are the new gap**. **No HTML** (avoids vendored-asset inline / shipped-render coupling). | PO Hybrid + F1 |
| D5 | New sinks are **hook-only** (no shipped-script instrumentation): `subagent-outcomes.jsonl` (SubagentStop) + `ms` added to `hook-telemetry.jsonl` (Pre/Post Bash pairing). atexit/excepthook REJECTED. | planner / F1-class |
| D6 | Skill named **"usage & health"** with an explicit "what this does NOT measure" section; VI narration default. | F4 |
| D7 | Effectiveness proxy = validate-pass-after-product-spec (internal quality), distinct from E3 market-outcome (stays deferred). | PO opt-in |
| D8 | A4: add `telemetry` to `DEFAULT_SKILLS` (semver), NOT `VERSION_SYNCED_SKILLS` (asserted). Bundle-exclude by manifest omission + test. New hooks are our `*.py` → already git-tracked via `!*.py`, but must NOT ship (not in manifest `hooks:`) → bundle-exclude test covers them. | R3 |
| D9 | New path helpers in `telemetry_paths.py`: `sessions_dir()`, `memory_dir()`, `TELEMETRY` const. | port |

**Source research:** `plans/reports/researcher-260607-1507-transcript-duration-token-attribution-report.md`, `…-1500-visualize-render-reuse-report.md`, `…-1500-skill-packaging-a4-gitignore-report.md`, `…-1528-ha-lens-port-specs-and-new-sinks-report.md`. **Red-team (round 1, on the pre-port plan):** `…-from-code-reviewer-to-planner-red-team-260607-1500-telemetry-insights-skill-report.md` (SHRINK; F1/F5→HTML dropped, F2→gate, F4→reframe).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Foundations: port formatters + extend telemetry_paths + fixtures + gate](./phase-01-foundations-port-formatters-extend-telemetry-paths-fixtures-.md) | ✅ Complete |
| 2 | [New observability sinks via hooks (subagent-outcomes + script-duration)](./phase-02-new-observability-sinks-via-hooks-subagent-outcomes-script-d.md) | ✅ Complete |
| 3 | [Core lenses: usage+tokens + session-shape + coarse-health](./phase-03-core-lenses-usage-tokens-session-shape-coarse-health.md) | ✅ Complete |
| 4 | [Extended lenses: forensics + memory-health + workflow-chains + reliability](./phase-04-extended-lenses-forensics-memory-health-workflow-chains-reli.md) | ✅ Complete |
| 5 | [Renderers: ascii + mermaid + overview](./phase-05-renderers-ascii-mermaid-overview.md) | ✅ Complete |
| 6 | [Effectiveness proxy: validate-pass signal](./phase-06-effectiveness-proxy-validate-pass-signal.md) | ✅ Complete |
| 7 | [cleanmatic-telemetry skill (usage and health) + VI narration](./phase-07-cleanmatic-telemetry-skill-usage-and-health-vi-narration.md) | ✅ Complete |
| 8 | [Packaging guards + docs + deferred + red-team apply](./phase-08-packaging-guards-docs-deferred-red-team-apply.md) | ✅ Complete |

## Implementation Outcome (2026-06-07)

**ALL 8 PHASES SHIPPED.** Tests: _shared+hooks+release **352 passed / 19 skipped**, product-spec **619**, critique **171** — no regressions. Deterministic build sha stable. Code-review: DONE_WITH_CONCERNS → 1 MEDIUM (M1: `never_used` dominated by vendored skills) **applied** (owned/external split in `catalog.py`+`lens_usage_tokens.py`); 3 LOW conscious-accepts. Both Phase-2 sinks proven live (`ms` + `subagent-outcomes`). Plan deviations (justified, surfaced): (a) bash-timer key = command-hash only (live Pre/Post `session_id` asymmetric); (b) `verify_skill_versions` made bundle-portable (skip missing DEFAULT skill dir) so the SHIPPED checker doesn't fail on a recipient bundle without the CM-local telemetry skill. Red-team triage: `plans/reports/from-code-reviewer-to-cook-red-team-triage-260607-1909-telemetry-port-full-scope.md`.

## Dependencies

- Builds on the SHIPPED A1 telemetry layer (plan `260606-2205-…`, complete) — consumes its sinks; Phase 2 adds two NEW hook-only sinks.
- Source: `human-analyzer` `com:skill-analytics` (read-only reference; we port + adapt, never depend on it at runtime).
- Cross-references E3 (BACKLOG, deferred) — must NOT flip its status.

## TDD Note

`--tdd`: tests first each phase via shared venv `./.claude/skills/.venv/bin/python3 -m pytest`. Ported scripts get a fixture-based parity test (same input → same aggregate as the adapted logic); hooks get fail-open + disabled-under-pytest tests; renderers get snapshot tests; packaging gets manifest/gitignore/tarball regression.

## Effort & Risk (honest)

Full scope is large for a single-user local tool. Biggest risks: (a) two hook changes (Phase 2) interacting with the live session — must be fail-open + pytest-silent; (b) sparse data making several lenses thin (gate mitigates); (c) scope vs value for a 3-skill repo (red-team Phase 8 + validate will re-test). PO chose Full knowingly; shrink points are pre-identified per phase.

## Validation Log

### Verification Results (2026-06-07, Full tier, 8 phases)
- Tier: Full. Claims checked: 8 load-bearing. **Verified: 8 | Failed: 0 | Unverified: 0.**
- `_shared` NOT bundled — `pack/selection.py:37` ships shared only via empty `_include_shared`. ✅ (D5/F1 holds)
- Bundle = manifest whitelist (`selection.py:36` slug walk + `match_hooks`). Omission ⇒ excluded. ✅ (D8)
- gitignore `!/.claude/hooks/*.py` (line 100) + `__tests__/*.py` (165) + `_shared/**` (minus pyc). New hooks auto-tracked; new SKILL dir still needs `!/.claude/skills/telemetry/**`. ✅ (D8)
- `emit_session_summary.py:34` session-dir resolver (`~/.claude/projects/<slug>`) → factorable. ✅ (Phase 1)
- **Hook events present** in settings.json: SubagentStart/SubagentStop/PreToolUse/PostToolUse. ✅ (Phase 2 feasible — was top uncertainty)
- Catalog: dir `product-spec` vs slug `cleanmatic:product-spec` → normalize in loader. ✅ (Phase 3)
- **Validate persists `docs/product/.memory/last_validated.json`** (`status.py:11`) → Phase 6 source #1 confirmed. ✅
- All settings hook keys available. ✅

### Decisions (validate interview, 2026-06-07)
- **Scope:** Full 8 phases, one pass (PO confirmed despite round-1 SHRINK). Per-phase shrink points retained as fallback.
- **Phase 2 hooks:** BOTH accepted (SubagentStop + Pre/Post:Bash duration). Overhead accepted (fail-open, pytest-silent).
- **memory-health (Phase 4):** THIS repo's memory dir only (`~/.claude/projects/<this-repo>/memory/`), read-only, no `--apply`.
- **Skill invocation name:** `/cleanmatic:telemetry` (matches cleanmatic: convention). Pinned in Phase 7.

### Whole-Plan Consistency Sweep
- Name pinned to `cleanmatic:telemetry` across plan + Phase 7 (removed "verify name" ambiguity).
- HTML stays dropped everywhere (D4); atexit stays rejected everywhere (D5); token attribution included (D2, reverses old D7-defer — no stale "defer token" text remains).
- E3 referenced as deferred only; status not flipped.
- No unresolved contradictions. **Eligible for `/ck:cook` (Failed: 0).**
