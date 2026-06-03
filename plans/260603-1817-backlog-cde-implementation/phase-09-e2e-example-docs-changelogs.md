---
phase: 9
title: "Capstone — real E2E + full example + docs sweep + changelogs"
status: pending
priority: P1
effort: "2d"
dependencies: [1, 2, 3, 4, 5, 6, 7, 8]
---

# Phase 9: Capstone — real E2E, full example, docs sweep, changelogs

> Final release-readiness phase. Runs AFTER all features land (depends on Phases 1–8). Proves the whole
> `product-spec` → `product-spec-critique` pipeline works end-to-end on real data, refreshes the canonical
> example, sweeps every doc surface, and backfills/updates all changelogs.

## Overview
Three deliverables: (1) a **real, full E2E run** of both product-spec* skills in an external folder
(scripts + LLM, real data), captured as (2) the **refreshed canonical example**, then (3) a **docs sweep**
(root + skill docs) and **changelog backfill** for all three skills.

## Requirements
- Functional: a real E2E exercising the full flow; refreshed examples carrying real frontmatter; every doc surface updated for the new flags/views; changelogs backfilled.
- Non-functional: product-spec half stays **no-network**; the LLM half is a **human-observed dogfood checklist, NOT an automated CI gate** (non-deterministic — same reason critique stays out of CI). Only the script half is reproducibly assertable.

## Key facts (scouted)
- Both skills have `examples/`. The critique examples are hand-authored with **no frontmatter** (red-team H2) — a real run fixes this.
- Skill docs = `SKILL.md` + `GUIDE-EN.md` + `GUIDE-VI.md` + `README.md` per skill. **No skill-level CLAUDE.md** — the LLM operating guides live in **root `CLAUDE.md`**. Root also has `README.md`.
- Only `claude-pack/CHANGELOG.md` exists today; Phase 1 (E5) scaffolds the other two. Git history: product-spec 22 commits (backfillable), critique 1, claude-pack 10.

## Architecture / approach
### A. Real E2E in an external folder (real data, script + LLM)
- **Drive it THROUGH THE WORKFLOW, not by hand (PO 2026-06-03).** The run MUST follow the skills' actual workflow references end-to-end — `workflow-interview.md` (+ `interview-vision/brd/prd/epic/story`), `workflow-validate.md`, `workflow-critique.md`, `workflow-apply-critique.md`, `workflow-discover.md`, the viz/summary flows — invoking the real flags/menus exactly as a PO would. No hand-authoring artifacts, no shortcutting steps. This dogfoods the workflow docs themselves: if a workflow reference is wrong/stale, the run breaks and that IS a finding to fix.
- In a temp dir OUTSIDE the repo, drive the full flow on a real product idea:
  `--product`/init → BRD → PRD → epic → story → `--validate`/`--strict` → critique (real lenses, LLM, may use web for market lens) → **E1 `--apply-critique`** → **C9 `--viz audit`** → **E4 `--summary --audience`** → **E2 `--discover`** seed → exercise **`goal_without_metric`** + strengthened lenses (Phase 8).
- Capture: the deterministic script outputs (assertable) + a human-observed checklist of the LLM steps (interview/critique/apply-critique quality). The script half can become a repeatable E2E smoke script; the LLM half is a release checklist.

### B. Refresh the canonical example (synergy with red-team H2)
- Use the E2E run's REAL artifacts (with real frontmatter + `body_hash`) to refresh `product-spec/examples/` and `product-spec-critique/examples/`. **The example is whatever the workflow actually produced** — not a hand-polished mock — so it stays faithful to real tool output. The refreshed critique example now carries frontmatter → becomes the **E1 freshness test fixture** Phase 3 needs (closes H2). Keep a hand-authored note only where illustration is clearer.

### C. Docs sweep (root + skill)
- **Root `CLAUDE.md`**: update the product-spec + critique operating guides for every new surface — `--apply-critique`, `--viz audit`, `--summary --audience`, `--discover`, `goal_without_metric`, strengthened lens prompts, E5 versioning + verifier. Update the workflow-pointers tables.
- **Root `README.md`**: top-level feature list / flow.
- **Per skill** (`product-spec`, `product-spec-critique`): `SKILL.md` (flag/view registry + menu), `GUIDE-EN.md` + `GUIDE-VI.md` (PO-facing walkthrough, bilingual), `README.md`. Reflect the refreshed example + new flows.

### D. Changelogs
- **Backfill** `product-spec/CHANGELOG.md` (22 commits → keepachangelog history grouped by theme) and `product-spec-critique/CHANGELOG.md` (thin — 1 commit + this plan's features). **DRY with Phase 1:** Phase 1 scaffolds the files (structure + `[Unreleased]` + current version); Phase 9 POPULATES them from git log + adds the C/D/E feature entries under the right versions.
- **Update** `claude-pack/CHANGELOG.md` for the bundle (the "changelog for all"): note the new product-spec*/validate/critique capabilities shipping in the bundle.

## Related Code Files
- Create: an external-folder E2E smoke script (script-half, repeatable) + a release-checklist doc for the LLM half (under `product-spec/` or the plan reports)
- Modify: `product-spec/examples/*`, `product-spec-critique/examples/*` (refresh from real run)
- Modify: root `CLAUDE.md`, root `README.md`
- Modify: `product-spec/{SKILL.md,GUIDE-EN.md,GUIDE-VI.md,README.md}`, `product-spec-critique/{SKILL.md,GUIDE-EN.md,GUIDE-VI.md,README.md}`
- Modify: `product-spec/CHANGELOG.md`, `product-spec-critique/CHANGELOG.md` (backfill), `claude-pack/CHANGELOG.md` (bundle update)

## Implementation Steps
1. Run the full E2E in an external temp folder on real data **by following the workflow references step-by-step** (interview→validate→critique→apply-critique→discover→viz→summary), invoking real flags/menus; scripts via venv python + LLM steps. Record script outputs + LLM-step observations + **any workflow-doc defect the run exposes** (fix those docs as part of step 3).
2. Refresh both `examples/` from the real workflow-produced artifacts (real frontmatter/body_hash); wire the critique example as E1's freshness fixture (closes H2).
3. Sweep docs: root `CLAUDE.md` + `README.md`; each skill's `SKILL.md`/`GUIDE-EN`/`GUIDE-VI`/`README`. Every new flag/view/check + strengthened lens reflected.
4. Backfill `product-spec` + `product-spec-critique` CHANGELOGs from git log (keepachangelog, themed); update `claude-pack` CHANGELOG for the bundle.
5. Capture the E2E as: a repeatable script-half smoke + a human release checklist (state plainly the LLM half is not a CI gate).

## Success Criteria
- [ ] A real E2E run completed in an external folder **by following the workflow references** (not hand-built), exercising EVERY new surface (E1/C9/E4/E2/goal_without_metric/strengthened lenses) — script + LLM — with outputs + any workflow-doc defects recorded and fixed.
- [ ] Both `examples/` refreshed from real artifacts; critique example carries frontmatter and serves as E1's freshness fixture (H2 closed).
- [ ] Root `CLAUDE.md` + `README.md` and all per-skill `SKILL.md`/`GUIDE-EN`/`GUIDE-VI`/`README` updated for the new surfaces.
- [ ] `product-spec` + `product-spec-critique` CHANGELOGs backfilled from git log; `claude-pack` CHANGELOG updated for the bundle.
- [ ] Script-half E2E is repeatable; LLM-half is a documented checklist (explicitly not a CI gate). Full existing suite still green.

## Risk Assessment
- Risk: treating the LLM E2E as a deterministic gate → it is NOT; document it as dogfood/checklist (the script half is the only repeatable assertion).
- Risk: changelog double-work vs Phase 1 → Phase 1 scaffolds, Phase 9 backfills; do not recreate the files.
- Risk: real run hits product-spec's no-network rule → product-spec stays offline; only the critique market lens may use web (its existing behavior).
- Risk: external-folder run leaks into the repo → run in a temp dir; commit only the curated refreshed examples, not the scratch run.

## Open question
- Numbering: added as **Phase 9** (next contiguous). PO referred to it as "phase 10" — confirm whether a separate Phase 9 (e.g. a cook/test gate) should be inserted and this renumbered to 10.
