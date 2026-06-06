---
phase: 4
title: "Skill & references"
status: completed
priority: P1
effort: "1d"
dependencies: [1, 2]
---

# Phase 4: Skill & references

## Overview

The skill package: `SKILL.md` (lean skeleton, flags, workflow map) + three references (`workflow-critique.md`, `voice-and-tone.md`, `lens-frameworks.md`). This is where the **orchestration** is specified — how the main agent runs `critique_scan.py` (structural fresh + cached verdicts, no forced validate) → fans out the 4 lens agents → spawns the consolidator → writes `docs/product/critique/<ts>-<scope>.md` → updates `last_critique.json` → optional DEC bridge.

## Requirements

- **Functional:** `SKILL.md` declares the skill (frontmatter: name `cleanmatic:spec-critique`, user-invocable, when_to_use, category `product`, keywords, argument-hint), the flag table, the workflow map, the output contract, and loads references on demand. `workflow-critique.md` is the executable orchestration (the 6-step flow). `voice-and-tone.md` owns the 5-level voice (vi+en) + the 5 grounding principles. `lens-frameworks.md` owns the per-lens framework→question→signature tables (single home; agents reference it).
- **Non-functional:** PO-facing in user-visible prose; lean skeleton (~250–300 lines) with references loaded by need; uses shared venv. Mirrors product-spec's SKILL.md conventions.

## Architecture

- **`SKILL.md`** (template = `product-spec/SKILL.md`):
  - Frontmatter + "When to Use" + **Flags table**: `[scope]` · `--product/--tech/--market/--craft` · `--interactive` · `--lang vi|en` (default vi) · `--no-web` · `--level 1..5` (default 3) · alias `--warm/--gentle/--blunt/--savage/--no-mercy`.
  - **Output contract:** `docs/product/critique/<ts>-<scope>.md`; marker `.memory/last_critique.json`; never edits artifacts; never gates CI.
  - **Workflow map** (mermaid) + "Loads references/* on demand".
  - **Anti-overlap-with-validate** note (the §4 table) so the LLM never critiques a validate label verbatim.
  - **Venv bootstrap** note (reuse `.claude/skills/.venv`; if missing, AskUserQuestion → run product-spec or spec-critique installer).
- **`references/workflow-critique.md`** — the orchestration the main agent executes:
  0. **early-exit guards:** no `docs/product/` or empty graph → friendly "chưa có spec để chửi" message, spawn NO agents. `--validate` itself errors → surface the validate error, do not critique on broken structure.
  1. parse flags; if `--interactive`, AskUserQuestion to pick lenses+scope+level.
  2. **verdict ammo (refined D8 — no forced validate):** critique_scan runs structural checks fresh + reads cached `judgments.json` (may be empty). The skill does NOT auto-run `--validate`. If the cache is empty/stale, surface a one-line suggestion "chạy `--validate` trước để critique sắc hơn" and proceed anyway (lens agents judge independently).
  3. `critique_scan.py --root --scope --lang` → bundle JSON written to a `$TMPDIR`/`plans/`-side temp path (outside the fence — it is scratch, not a spec artifact); pass the path to each agent.
  4. **fan-out** the selected lens agents in parallel via `Task(spec-critique-<lens>)`, each given the bundle path + `--level`/`--lang`. Scope-aware: at story scope, market thinned/skipped (consolidator warns). Market with no BRD `competitors:` AND `--no-web` → market flags "thiếu căn cứ cạnh tranh", never fabricates.
  5. `Task(spec-critique-consolidate)` with the available lens reports (**N≤4, tolerate missing**) + `prior_reports` → final markdown; header names any lens that did not complete.
  6. main agent WRITES `docs/product/critique/<ts>-<scope>.md` (through `fs_guard`), then `critique_scan.py --snapshot` to refresh `last_critique.json`.
  7. **DEC bridge:** if consolidator flagged DEC-worthy items, AskUserQuestion per item → on PO confirm, `decision_register.py --alloc-id` + `--append` with a `source: critique` tag on the ruling (provenance: born from a non-deterministic critique, distinguishable from a validate-contradiction DEC) (GATE-NEVER-ASSUME; GATE-NO-SILENT-REVERSAL if it touches an approved artifact).
  - Two GATEs restated; read-only-with-spec restated; scope-aware lens applicability table; `--scope all` carries a "this is expensive" note.
- **`references/voice-and-tone.md`** — the 5-level table (vi+en sample lines per level), the personal-attack redline (levels 1–4 forbid; only level 5 lifts, with a warning), the 5 grounding principles (evidence ID+line · failure-mode-not-person · observation-vs-opinion · pre-mortem · always-a-fix). Per-finding template: `evidence → mỉa → why-it-dies → fix`.
- **`references/lens-frameworks.md`** — the 4 framework banks (from the value-lenses research): diagnostic questions + failure signatures per framework. Single home so agents stay DRY.

## Related Code Files

- Create: `.claude/skills/spec-critique/SKILL.md`
- Create: `.claude/skills/spec-critique/references/workflow-critique.md`
- Create: `.claude/skills/spec-critique/references/voice-and-tone.md`
- Create: `.claude/skills/spec-critique/references/lens-frameworks.md`

## Implementation Steps

1. Read `product-spec/SKILL.md` for the skeleton conventions (frontmatter keys, flag-table style, references-on-demand, venv-bootstrap note).
2. Write `SKILL.md` skeleton with flags + output contract + workflow map + anti-overlap note + venv note.
3. Write `workflow-critique.md` (the 6-step orchestration + GATEs + scope-aware table + DEC bridge).
4. Write `voice-and-tone.md` (5 levels vi+en + redline + 5 principles + per-finding template).
5. Write `lens-frameworks.md` (4 framework banks).
6. Sanity: the bundle schema referenced here matches Phase 1; the agent names match Phase 2; the DEC/validate/preferences scripts referenced exist in product-spec.

## Success Criteria

- [ ] `SKILL.md` valid frontmatter, lists all flags incl. `--level 1..5` default 3, output contract correct, loads references on demand, ~≤300 lines.
- [ ] `workflow-critique.md` fully specifies validate→scan→fan-out→consolidate→write→DEC-bridge with both GATEs.
- [ ] `voice-and-tone.md` encodes 5 levels (vi+en), redline, 5 grounding principles, per-finding template.
- [ ] `lens-frameworks.md` holds all 4 banks; agents reference it (no duplication).
- [ ] Cross-refs consistent with Phase 1 bundle + Phase 2 agent names.

## Risk Assessment

- **Skeleton bloat:** keep prose in references; SKILL.md stays lean. Mirror product-spec.
- **Orchestration mismatch with agent expectations:** Phase 4 is the contract author; verify agent input/output schemas (Phase 2) line up before marking done.
- **Double LLM cost (validate + critique):** acknowledged + documented (PO chose full-validate ammo). `--no-web` + scope control mitigate.
