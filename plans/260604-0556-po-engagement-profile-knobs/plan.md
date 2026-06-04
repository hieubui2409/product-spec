---
title: "PO Engagement Profile knobs for product-spec*"
description: ""
status: pending
priority: P2
branch: "claude/agent-naming-conventions-cd70n"
tags: []
blockedBy: []
blocks: []
created: "2026-06-04T06:01:44.396Z"
createdBy: "ck:plan"
source: skill
---

# PO Engagement Profile knobs for product-spec*

## Overview

Add a **learned-but-confirmed PO engagement profile** to `product-spec*`: **2 new closed-enum knobs** in the existing
`preferences.yaml` that modulate AI engagement (challenge/probe depth + next-action density). Captured via explicit
`--set` flag + a live end-of-session interview forcing-function — both PO-driven, **no auto-write**. **No breaking
changes** — additive keys; `load()` default-fills, `--set` does `load→merge→save`.

**Scope is the red-team-revised v1** — design source §13 is authoritative:
`plans/reports/brainstorm-design-260604-0556-po-engagement-profile-knobs-report.md`.

New keys (both default **`standard`**, mirroring `detail_level`) — **product-spec only**:
- `interview_rigor` — light/standard/deep (merges challenge + edge/gap probing) — applies at ALL interview levels.
- `action_prompting` — minimal/standard/proactive — product-spec next-action density.
- `detail_level` (existing) — referenced, never copied.

**Cut from v1 (red-team + validate):** `standing_reminders` (privacy/injection), `--reflect engagement-profile`
harvest (no deterministic signal), and **critique wiring** (validate: marginal value vs provenance-rebust cost —
Phase 3 deferred). Default posture is neutral `standard`; strict-first is a one-time Init-Flow `AskUserQuestion`
(combined into the existing `detail_level` batch when ≤4 questions), never a silent default (GATE-NEVER-ASSUME).
Mode: `--tdd`; red-team + validate gates done (see `## Red Team Review`, `## Validation Log`).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Schema and write-CLI in preferences](./phase-01-schema-and-write-cli-in-preferences.md) | Pending |
| 2 | [Product-spec interview/prose injection](./phase-02-product-spec-interview-prose-injection.md) | Pending |
| 3 | [Critique injection — DEFERRED (out of v1)](./phase-03-critique-injection-action-reminders-only.md) | Deferred |
| 4 | [Capture: --set flag + end-of-session forcing-function](./phase-04-capture-flag-hybrid-reflect-harvest.md) | Pending |
| 5 | [Docs sync](./phase-05-docs-sync.md) | Pending |

## Dependencies

Builds on (all `done`): `260601-1853-product-spec-guardrails-and-memory-layer` (preferences/3D/3E),
`260602-0026-strengthen-memory-write-enforcement` (memory_gap/reflect), `260602-1528-spec-critique-...split-detail-level`
(detail_level vs critique_detail_level split). No unfinished overlapping plans → no `blockedBy`/`blocks` set.

## Non-Breaking Invariant (applies to every phase)

- Additive only: 2 new keys in `preferences.py` `DEFAULTS` + `ENUMS`; never rename/remove existing keys.
- Old `preferences.yaml` (no new keys) must resolve to documented defaults — assert in `test_preferences.py`.
- **`save()` is a blind full-dict overwrite (`preferences.py:195-215`)** — any write path (esp. `--set`) MUST
  `load()→merge→save()`, else it silently destroys other keys (red-team finding A). Non-negotiable.
- Knobs are **referenced** at read points, never copied into another store (DRY).
- No auto-write: the only writers are PO-invoked (`--set`) or PO-confirmed (end-of-session forcing-function).

## Red Team Review

### Session — 2026-06-04
**Findings:** 19 accepted (deduped from 24), 0 rejected · **Severity:** 4 Critical, 7 High, 8 Medium.
Full adjudication: `reports/from-code-reviewer-to-planner-red-team-consolidated-plan-review-report.md`.

**PO rulings reshaping v1:** default posture = Hybrid (neutral `standard` + Init-Flow ask, like `detail_level`);
`standing_reminders` DROPPED; `--reflect` harvest CUT.

| # | Finding | Severity | Disposition | Applied To |
|---|---------|----------|-------------|------------|
| A | `save()` not load-merge → `--set` clobbers file (data loss) | Critical | Accept | Phase 1 |
| B | `test...==13` breaks (+2 keys → 15) | Critical | Accept | Phase 1 |
| O | `standing_reminders` free-text committed → privacy leak | Critical | Accept (drop key) | — (cut) |
| P | "PO-confirmed" doc-only, no script gate | Critical | Accept (no auto-write) | Phase 4 |
| C | Critique bundle is `critique_bundle.py`, not `critique_scan.py` | High | Accept (deferred — validate) | Phase 3 (cut) |
| F | `_existing_memory_index` shape/fallback break | High | Accept (moot — harvest cut) | — |
| G | `--reflect engagement-profile` has no anchor signal | High | Accept (cut harvest) | Phase 4 |
| H | dedup on resolved defaults suppresses relax | High | Accept (moot — harvest cut) | — |
| Q | default deep/proactive trips GATE | High | Accept (→ standard + init-ask) | Phase 1/2 |
| R | reminder free-text = prompt-injection | High | Accept (drop key) | — (cut) |
| E | design §7 false memory_gap dedup claim | High | Accept (corrected) | design |
| D | `dismissed_reminders` phantom consumer | Medium | Accept (moot — key dropped) | — |
| I | critique provenance reuses stale report on knob change | Medium | Accept (moot — critique deferred) | Phase 3 (cut) |
| J | `--set` list-key foot-gun | Medium | Accept (moot — no list key) | — |
| K | Phase-2 wrong section ref | Medium | Accept | Phase 2 |
| L | 3rd end-of-session nudge stacking | Medium | Accept | Phase 4 |
| M | YAML bool coercion mangles list items | Medium | Accept (moot — no list key) | — |
| N | Phase-4 multi-write loss (transitive on A) | Medium | Accept (subsumed by A) | Phase 1 |
| S | Phase-3 ships unresolved Q3 (proactive vs report-only) | Medium | Accept (moot — critique deferred) | Phase 3 (cut) |

**Corrections (R3-verified):** claude-pack does NOT ship `preferences.yaml` (`selection.py:30-36`); `save()` IS
path-fenced (`preferences.py:210`). Both noted in design §13 to prevent over-correction.

## Validation Log

### Session 1 — 2026-06-04
Verification pass SKIPPED per Step-2.5 Guard (a `## Red Team Review` with `file:line` evidence already exists; no
`[UNVERIFIED]` tags). 3 critical-decision questions asked.

| Topic | Decision | Propagated to |
|-------|----------|---------------|
| Critique wiring worth it? | **Drop from v1** — post-cuts critique gains only one clamped knob whose `standard` = status quo; the only new value (`minimal`) does not justify the `critique_bundle.py` edit + provenance-hash rebust (global one-time re-judge). Re-add later is cheap. | Phase 3 → Deferred; Phase 5 (drop critique SKILL.md); Red Team C/I/S → moot |
| Init-Flow ask UX | **Combine** the strict-first question into the existing `detail_level` Init-Flow `AskUserQuestion` batch when total ≤4 (max 1 batch = 4 questions); else separate batch. | Phase 2 |
| `interview_rigor` scope | **All interview levels** (vision/BRD/PRD/epic/story), not just story/epic. | Phase 2 |

### Whole-Plan Consistency Sweep
Re-read `plan.md` + all phase files after propagation. Decision deltas applied: critique cut (Phase 3 deferred, Phase
5 critique edits removed, Red Team C/I/S marked moot, Phase 5 dep `[1,2,3,4]→[1,2,4]`), init-batch-combine + rigor-all-
levels added to Phase 2. No remaining contradiction: no phase still treats critique as in-scope; no orphan reference to
`standing_reminders`/`--reflect` as active work; defaults consistently `standard`; count guard consistently 15.
**Result: 0 unresolved contradictions.** Plan eligible for implementation.
