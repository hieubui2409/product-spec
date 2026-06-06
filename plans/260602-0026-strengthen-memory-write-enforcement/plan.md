---
title: "product-spec: strengthen memory-write reliability (forcing-functions + opt-in hook + --reflect)"
description: "Make memory writes (decision / 3D po-style / 3E self-corrections / judgment-cache) reliable via deterministic triggers without false hard-guarantees. Tier-0 forcing-functions + Tier-1 opt-in Stop hook + Tier-2 --reflect harvester. Mode: --hard --tdd, ultracode-orchestratable."
status: completed
priority: P1
branch: "feat/product-spec-guardrails-and-memory-layer"
tags: [product-spec, memory, hook, agents, reflect, claude-pack, tdd]
blockedBy: []
blocks: []
created: "2026-06-01T17:34:29.049Z"
createdBy: "ck:plan"
source: skill
---

# product-spec: strengthen memory-write reliability (forcing-functions + opt-in hook + --reflect)

## Overview

The product-spec memory layer (decision register, judgment cache, 3D PO-style, 3E self-corrections) is entirely
**LLM-discretionary** — writes only happen if the LLM remembers to run a writer at a workflow hook point. This plan
makes the *trigger* deterministic without a false hard-guarantee, in three tiers:

- **Tier-0 (portable, no hook):** a single deterministic detector (`memory_gap.py`), a required "Memory pass"
  forcing-function in `--validate`, a per-prose-turn 3D forcing-function in interview, `judgment_cache` batch-write
  (collapse N→1), a `--voice` flag, and `--status unrecorded_signals`.
- **Tier-1 (opt-in Stop hook):** `memory_gap_hook.py` (Python/venv) with a per-signal persistence policy
  (fence=persist, others=nudge-once via `stop_hook_active`), a `PostToolUse` no-op guard, and an `install --memory-hook`
  idempotent `settings.local.json` merge with a ≤1/day recommend-nudge. **Reverses the locked "no hook" decision —
  opt-in only, never auto-registered.**
- **Tier-2 (`--reflect`):** a retroactive harvest — `reflect_scan.py` (git-degrade-safe) + a read-only opus harvester
  agent at top-level `.claude/agents/memory-harvester.md` → candidate report → PO interview → persist-after-confirm.

Source of truth (decisions LOCKED): `plans/reports/from-brainstorm-to-plan-260602-0005-strengthen-memory-write-enforcement-report.md` (§8 resolved decisions, §9 packaging).

**Mode:** `--hard --tdd`. Script phases (2,3,4,5,7,9) are tests-first (pytest). Prose/reference phases (6,10) verify via
structural checks (pointer-table integrity, cross-ref resolves, DRY single-home). Phase 1 is a verification spike. Phase
11 is packaging. Phase 12 is integration verify.

**Honest ceiling (documented, do NOT over-claim):** decision + 3E + fence get materially stronger; 3D stays nudge-only
(conversational, no structural signal) + retroactive via `--reflect`; cache via batch-write. **Enforcement raises the
consideration-rate, never the write-quality** — the LLM can still rubber-stamp "none". No way around the judgment limit.

**Impact boundary:** product-spec skill + repo-root `CLAUDE.md` + top-level `.claude/agents/memory-harvester.md` +
top-level `.claude/hooks/memory_gap_hook.py` + claude-pack `pack.manifest.yaml` + `INSTALL.md.template`. **`.claude/rules/*`
is ck-managed → NEVER edit.** The existing ck-managed `.claude/hooks/*.cjs` files are NEVER edited — only the new
skill-owned `memory_gap_hook.py` is added alongside them. The `cleanmatic:claude-pack` BEGIN/END marker block in
`CLAUDE.md` stays **byte-unchanged**.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [hook-mechanics-spike](./phase-01-hook-mechanics-spike.md) | Done |
| 2 | [memory-gap-detector](./phase-02-memory-gap-detector.md) | Done |
| 3 | [judgment-cache-batch-write](./phase-03-judgment-cache-batch-write.md) | Done |
| 4 | [behavioral-memory-voice-flag](./phase-04-behavioral-memory-voice-flag.md) | Done |
| 5 | [status-unrecorded-signals](./phase-05-status-unrecorded-signals.md) | Done |
| 6 | [tier0-forcing-functions-refs](./phase-06-tier0-forcing-functions-refs.md) | Done |
| 7 | [stop-hook-and-noop-guard](./phase-07-stop-hook-and-noop-guard.md) | Done |
| 8 | [install-memory-hook-and-nudge](./phase-08-install-memory-hook-and-nudge.md) | Done |
| 9 | [reflect-harvest-and-agent](./phase-09-reflect-harvest-and-agent.md) | Done |
| 10 | [docs-skill-claude-guide-readme](./phase-10-docs-skill-claude-guide-readme.md) | Done |
| 11 | [claude-pack-packaging](./phase-11-claude-pack-packaging.md) | Done |
| 12 | [integration-verify](./phase-12-integration-verify.md) | Done |

## Workflow-Orchestration Spec (ultracode-runnable)

### File-ownership matrix (each file = exactly ONE owning phase → no parallel write conflict)

| File / path | Owner | Action |
|-------------|-------|--------|
| (verification only — no shipped code; findings note in plan dir) | **P1** | spike |
| `scripts/memory_gap.py`, `scripts/tests/test_memory_gap.py` | **P2** | create + test |
| `scripts/judgment_cache.py` (batch-write path), `scripts/tests/test_judgment_cache.py` (batch tests) | **P3** | modify + test |
| `scripts/behavioral_memory.py` (`--voice` CLI write), `scripts/tests/test_behavioral_memory.py` (voice test) | **P4** | modify + test |
| `scripts/status.py` (`unrecorded_signals` + reflect suggestion), `scripts/tests/test_status.py` (additions) | **P5** | modify + test |
| `references/memory-enforcement.md` (NEW DRY home), `references/workflow-validate.md` (Memory-pass + batch-store wiring), `references/workflow-interview.md` (3D forcing-fn + validate nudge), `references/workflow-status.md` (unrecorded_signals), `references/behavioral-memory.md` (3D/3E trigger update) | **P6** | reference prose |
| `.claude/hooks/memory_gap_hook.py` (top-level, skill-owned), `scripts/tests/test_memory_gap_hook.py` | **P7** | create + test |
| `install.sh`, `install.ps1` (product-spec — `--memory-hook` merge + recommend-nudge) | **P8** | modify |
| `scripts/reflect_scan.py`, `scripts/tests/test_reflect_scan.py`, `.claude/agents/memory-harvester.md` (top-level), `references/workflow-reflect.md` | **P9** | create + test |
| repo-root `CLAUDE.md` (hygiene line + pointers + scripts list), `SKILL.md` (flag rows + install note), `GUIDE-EN.md`, `GUIDE-VI.md`, `README.md` (product-spec) | **P10** | docs |
| `.claude/pack.manifest.yaml` (`agents:` += memory-harvester, `hooks:` += memory_gap_hook.py), `.claude/skills/claude-pack/assets/templates/INSTALL.md.template` (+1 line) | **P11** | packaging |
| (verification only — full suite + byte-invariant + pack dry-run) | **P12** | verify |

### Dependency DAG

```
P1 (spike) ─────────────────────────────┐ (gates P7)
P2 (memory_gap) ──┬── P5 ──┐             │
                  │        ├── P6 ───────┼── P9 ──┬── P11
                  ├────────┘             │        │
P3 (batch-write) ─┘ (P6 needs 2,3,4,5)   P7 ── P8 │
P4 (--voice) ─────────────────────────────────────┤
                                          P10 (needs all feature phases) ┘
P12 = LAST (needs all)
```

- **P6 deps [2,3,4,5]:** references describe the new script behaviors → must follow them.
- **P7 deps [1,2]:** hook needs verified mechanics (P1) + the detector (P2).
- **P8 deps [7]:** installer registers the hook script (P7).
- **P9 deps [2,6]:** reflect reuses `memory_gap` dedup (P2) + links the `memory-enforcement.md` DRY home (P6).
- **P10 deps [2,3,4,5,6,7,8,9]:** docs reflect final behavior of every feature; CLAUDE.md pointer targets `memory-enforcement.md` (P6).
- **P11 deps [9]:** manifest bundles the harvester agent (P9).

### Execution waves (for a Workflow script)

| Wave | Phases (parallel within wave) | Gate |
|------|------------------------------|------|
| W1 | **P1** ∥ **P2** ∥ **P3** ∥ **P4** | all distinct files; spike independent |
| W2 | **P5** | needs P2 (`memory_gap`) |
| W3 | **P6** ∥ **P7** | distinct files (refs vs hook script); P6 needs 2-5, P7 needs 1-2 |
| W4 | **P8** ∥ **P9** | P8 needs P7; P9 needs 2+6 (distinct files) |
| W5 | **P10** ∥ **P11** | P10 = docs (needs all feature); P11 = packaging (needs P9) |
| W6 | **P12** verify | needs all |

> Workflow runs waves sequentially; phases inside a wave fan out (`parallel()` / per-phase `agent()`). `--tdd`: each
> script phase authors + runs its tests before its implementation step within the same agent.

## Locked decisions (do NOT re-litigate — see report §8/§9)

- **No-hook reversal (re-ratified):** Tier-1 hook is **opt-in only**, **never auto-registered**; capability ships
  (script + agent + `--memory-hook` flag), recipient opts in. Auto-modifying a user's settings = trust violation.
- **Hook = Python via shared venv** (`memory_gap_hook.py`), reuses `memory_gap.py`.
- **Per-signal hook policy:** `fence_breach` = persist (block until fixed, 8-cap); `validate_no_marker` +
  `approved_changed_no_dec` = nudge-once (honor `stop_hook_active`). Block-once → a false positive costs one re-judgment.
- **Harvester = read-only at the tool layer** (`tools: Glob, Grep, Read, Bash`; NO Write/Edit/Task), `model: opus`,
  top-level `.claude/agents/`, bundled via manifest `agents:`.
- **Cache never authoritative:** no chat-time judgment-cache write; content change self-heals via `body_hash` key;
  PO-overrides-in-chat → Decision Register, not the cache.
- **Recommend-nudge:** passive ≤1/day + explicit "never" (markers: `hook-prompted-last` + `hook-optout`); not blocking.
- **Doc-placement (hard):** `CLAUDE.md` = ref-only 1-line pointers (token-optimized, loads per turn); `references/*` =
  operative detail; `GUIDE-EN/VI` = full use-cases; `README` = overview.
- **`--reflect` = on-demand + soft `--status` suggestion; git-degrade-safe** (no git → harvest `.memory/`/`decisions.md`
  diff state only, never crash).
- **Honest ceiling:** enforcement raises consideration-rate, not write-quality. 3D stays nudge-only.
- **`.claude/rules/*` = ck-managed → never edit.** `cleanmatic:claude-pack` marker block in `CLAUDE.md` = byte-unchanged.

## Dependencies

- **Foundation:** `260601-1853-product-spec-guardrails-and-memory-layer` (status: **done**) shipped the memory layer
  (`decision_register`, `judgment_cache`, `behavioral_memory`, `fs_guard`, `check_fence`, `status`, `spec_graph.body_hash`).
  This plan extends it; done → not a blocker. Reuse, never duplicate (`memory_gap` imports `check_fence`/`spec_graph`).
- **Stale-pending (no relation):** `260530-0503-product-spec-multidim-impact-v2` (pending; v2 features already in code).
- **Script-vs-LLM split:** scripts own deterministic detection (signals, anchors, key, path-assert); LLM owns judgment
  (verdict, candidate proposal, voice observation). Harvester sub-agent = LLM read-only; persist = main agent + scripts.
- **Venv:** all scripts run via `./.claude/skills/.venv/bin/python3`.
