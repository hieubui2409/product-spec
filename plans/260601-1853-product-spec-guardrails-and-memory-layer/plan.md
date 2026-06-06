---
title: "product-spec: guardrails + memory layer (combined)"
description: "Guardrails (off-topic/no-code/anti-rationalization) + references restructure (split+DRY) + memory 3-store + behavioral 3D/3E + --status. Mode: --hard --tdd, workflow-orchestratable."
status: completed
priority: P1
branch: "feat/product-spec-guardrails-and-memory-layer"
tags: [product-spec, memory, guardrails, references, tdd]
blockedBy: []
blocks: []
created: "2026-06-01T11:57:56.779Z"
createdBy: "ck:plan"
source: skill
---

# product-spec: guardrails + memory layer (combined)

## Overview

Combined plan from a 4-report brainstorm series. Adds to the **product-spec** skill: (1) **guardrails** (off-topic
redirect, no-code redirect, anti-rationalization, named gates, consistency-sweep, scope-challenge), (2) **references
restructure** (split 2 bundled files + fix 3 DRY-dups), (3) **memory layer** (decisions / preferences / judgment-cache),
(4) **behavioral memory** (PO-style + LLM-self-correction), (5) **soft fence** + **`--status`** nudge.

Source-of-truth input (decisions LOCKED): `plans/reports/from-brainstorm-to-plan-260601-1833-product-spec-guardrails-memory-combined-scope-report.md` (consolidates `…-1754-…memory-layer-application` + `…-1819-…guardrails-and-behavioral-memory`).

**Mode:** `--hard --tdd`. Script phases (P1/P5/P6/P7/P8) are tests-first; prose phases (P2/P3/P4) verify via structural checks (pointer-table integrity, DRY-dup removed, no broken cross-refs), not pytest.

**Impact boundary:** all changes inside `product-spec` skill + repo-root `CLAUDE.md`. **claude-pack = 0 changes** (new references auto-ship via slug rglob). `.claude/rules/*` is ck-managed → **NEVER edit**.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [body-hash-foundation](./phase-01-body-hash-foundation.md) | Done |
| 2 | [references-restructure](./phase-02-references-restructure.md) | Done |
| 3 | [guardrails-claude-md-and-boundaries](./phase-03-guardrails-claude-md-and-boundaries.md) | Done |
| 4 | [workflow-guardrails](./phase-04-workflow-guardrails.md) | Done |
| 5 | [memory-core-decisions-prefs](./phase-05-memory-core-decisions-prefs.md) | Done |
| 6 | [judgment-cache-incremental-validate](./phase-06-judgment-cache-incremental-validate.md) | Done |
| 7 | [behavioral-memory-style-self-correction](./phase-07-behavioral-memory-style-self-correction.md) | Done |
| 8 | [soft-fence-and-status-nudge](./phase-08-soft-fence-and-status-nudge.md) | Done |
| 9 | [claude-pack-impact-verify](./phase-09-claude-pack-impact-verify.md) | Done |

## Workflow-Orchestration Spec (ultracode-runnable)

### File-ownership matrix (each file = exactly ONE owning phase → no parallel write conflict)

| File / path | Owner | Action |
|-------------|-------|--------|
| `scripts/spec_graph.py` (+`CHANGED_FIELDS`/`changed_nodes` DRY home), `scripts/render_ascii.py` (delta field tuple), `scripts/tests/test_spec_graph*.py` | **P1** | modify + test |
| `references/workflow-validate.md` | **P1** | modify (Step 2.5 body-detect) — **P2/P5/P6/P7 edits to it serialize behind P1** (see deps + line 74) |
| split: `interview-epic-story.md`→`interview-epic.md`+`interview-story.md`; `workflow-auto-and-update.md`→`workflow-auto.md`+`workflow-update.md`; DRY homes `validation-rules-spec.md`, `frontmatter-and-id-spec.md`; **`SKILL.md` (references list + ALL flag rows incl. `--decision`/`--status`)** | **P2** | split/DRY/pointer/flags |
| repo-root `CLAUDE.md` (guardrail anchors + pointer-table + **F1 fence prose anchor**); `references/guardrails-and-boundaries.md` (new, incl. F1 detail) | **P3** | guardrails |
| `references/workflow-update.md`, `workflow-auto.md`, `workflow-interview.md`, `interview-frameworks.md` | **P4** | workflow guardrails |
| `docs/product/decisions.md`†, `scripts/decision_register.py` (new), `assets/templates/decision-record.md` (new), `.memory/preferences.yaml`†, `references/workflow-validate.md` (Contradiction wiring) | **P5** | memory core (validate edit serializes behind P2) |
| `scripts/judgment_cache.py` (new), `.memory/judgments.json`†, `references/workflow-validate.md` (Step 2 orchestration) | **P6** | cache (validate edit last, behind P5) |
| `.memory/po-style.yaml`†, `.memory/self-corrections.json`†, `scripts/behavioral_memory.py` (new), `references/behavioral-memory.md` (new); final-writer hook-lines in `workflow-interview.md` (after P4) + `workflow-validate.md` (after P6) | **P7** | behavioral |
| **P8a:** `scripts/fs_guard.py` (new, imported by P5/P6/P7), `scripts/check_fence.py` (new), path-assert at `render_html._write_visual`+`render_export.py:262`+`generate_templates.py:463`. **P8b:** `references/workflow-status.md` (new), `--status` (reads P6's `last_validated.json`). No SKILL/CLAUDE edits | **P8** | fence + status |
| (verification only — reads `pack.manifest.yaml`, `safety_check.py`) | **P9** | verify |

† runtime files created in a PO project, not in the skill repo — referenced by scripts/tests, scaffolded via templates.

### Dependency DAG

```
P1 ──> P2 ──> P5 ──> P6 ──> P7
       │       (P6 needs P1+P5)   ▲▲
       ├──> P3                    ││
       └──> P4 ───────────────────┘│  (P7 deps [4,5,6,8]: after P4's interview.md + P6's validate.md + P8's check_fence)
P8 ────────────────────────────────┘
P8.scripts ∥ P1  (distinct files; P8 also feeds P5/P6/P7 via shared fs_guard → P5/P6 dep [8])
P9 = LAST (needs all)
```

**Serialization driver:** `workflow-validate.md` is a hub edited by P1→P2→P5→P6→P7 (sequential on that file; P7 adds the final 3E hook-line). `SKILL.md` is owned solely by **P2** (it adds the `--decision`/`--status` flag rows itself — P5/P8 only implement the logic). `CLAUDE.md` is owned solely by **P3** (incl. the F1 fence prose). `workflow-interview.md` is edited by P4 then P7 (3D hook-line, final writer).

### Execution waves (for a Workflow script)

| Wave | Phases (parallel within wave) | Gate |
|------|------------------------------|------|
| W1 | **P1** ∥ **P8a** (fs_guard.py + check_fence.py + path-assert) | distinct files; fs_guard ready for later phases |
| W2 | **P2** | shares validate hub w/ P1 |
| W3 | **P3** ∥ **P4** | distinct files (CLAUDE.md+newref vs split workflow refs) |
| W4 | **P5** (imports fs_guard) | validate hub + decisions |
| W5 | **P6** (imports fs_guard; writes last_validated.json) | validate hub + cache |
| W6 | **P7** ∥ **P8b** (`--status`, reads last_validated) | P7 needs P4+P5+P6+P8a; P8b needs P6 |
| W7 | **P9** verify | needs all |

> A Workflow runs waves sequentially; phases inside a wave fan out (`parallel()` / per-phase `agent()` with `isolation:'worktree'` if mutating shared tree). `--tdd`: each script phase's tests are authored + run before its implementation step within the same agent.

## Locked decisions (do NOT re-litigate — see report 1833 §0)

folder Split (decisions.md visible + `.memory/` hidden, **all committed**) · soft fence F1+F3+F2 (no hook) · Decision Register auto-on-contradiction + `--decision` · contradiction **no-cache** · ruled-drift = `po_ruling_ref: DEC-n` field in `judgments.json` → `decisions.md` authoritative (RT-3 refined: surface DEC on body change, never silent re-flag) · **Scope Challenge always-on per PRD** · guardrail home = anchor in CLAUDE.md + detail in `references/guardrails-and-boundaries.md` · CLAUDE.md project-owned + shipped + **NOT ck-overwritten** (edit product-spec section ABOVE the `cleanmatic:claude-pack` BEGIN marker; verify block byte-unchanged via marker-text awk, not line numbers) · `.claude/rules/*` ck-managed → never edit.

## Dependencies

- **Cross-plan:** `260530-0503-product-spec-multidim-impact-v2` is `status: pending` (6/38 tracked) but its v2.0.0 features already exist in code (risks/competitive_parity/anchors scripts present; git `bump to 2.0.0`). Classified **stale-pending, no blocking relationship** — this plan builds on the current post-multidim codebase. If that plan is resumed, re-check `spec_graph.py` + `workflow-validate.md` overlap.
- **Script-vs-LLM split** (CLAUDE.md): scripts own deterministic work (hash, key, staleness, ID alloc, path-assert, fence scan); LLM owns judgment (verdict, rationale, voice observation).
- **Venv:** all scripts run via `./.claude/skills/.venv/bin/python3`.
