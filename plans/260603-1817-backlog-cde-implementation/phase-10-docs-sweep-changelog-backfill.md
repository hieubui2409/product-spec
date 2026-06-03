---
phase: 10
title: "9b — docs sweep + changelog backfill"
status: partial
priority: P1
effort: "2d"
dependencies: [9]
---

# Phase 10 (9b): docs sweep + changelog backfill

> Split from Phase 9 after red-team (docs ≈ 2,400 lines across 10 files; different skill profile from the E2E
> run; docs can only finalize once the real example exists). Depends on Phase 9 (9a) — docs reference the
> real example.

## Overview
Sweep every doc surface (root + per-skill) to reflect the new flags/views/checks + strengthened lenses, then
backfill the three changelogs correctly (subject-scoped, rename-following).

## Requirements
- Functional: every doc surface updated for `--apply-critique`, `--viz audit`, `--summary --audience`, `--discover`, `goal_without_metric`, strengthened lens prompts, E5 versioning; 3 changelogs backfilled.
- Non-functional: bilingual GUIDE-VI native-reviewed (per CLAUDE.md bilingual rule); no network.

## Key facts (scouted)
- Doc surfaces (~2,400 lines): `product-spec/GUIDE-EN.md` 743, `GUIDE-VI.md` 736, `product-spec-critique/GUIDE-EN.md` 201, `GUIDE-VI.md` 232, two `SKILL.md` (189+182), two `README.md`, root `CLAUDE.md` 145, root `README.md` 231. **No skill-level CLAUDE.md** — operating guides live in root `CLAUDE.md` (mixes all 3 skills → edit the right section only).
- Changelogs: Phase 1 (E5) scaffolds product-spec + critique CHANGELOGs (structure + current version); only claude-pack has one today.
- **Git history is contaminated (red-team H5):** `git log -- .claude/skills/product-spec/` = 22 commits but includes `feat(spec-critique)` work (the critique skill was renamed through that subtree, e.g. `1798229 refactor: rename spec-critique → product-spec-critique`); the critique path itself = 1 commit.

## Architecture / approach
### A. Docs sweep
- **Root `CLAUDE.md`**: update the product-spec + critique operating-guide sections for every new surface + the workflow-pointer tables — touch only the relevant skill's section.
- **Root `README.md`**: top-level feature/flow list.
- **Per skill** (`product-spec`, `product-spec-critique`): `SKILL.md` (flag/view registry + menu + `argument-hint`), `GUIDE-EN.md` + `GUIDE-VI.md` (PO walkthrough, bilingual, VI native-reviewed), `README.md`. Reflect the real Phase-9 example.

### B. Changelog backfill (correct attribution — red-team H5)
- **DRY with Phase 1:** Phase 1 scaffolds the files; this phase POPULATES them.
- **Do NOT drive off raw `git log -- <path>`.** Attribute by **commit subject scope**: `feat(product-spec)`/`fix(product-spec)` → product-spec CHANGELOG; `feat(spec-critique)`/`feat(...critique)` → critique CHANGELOG. Use `git log --follow` for the critique skill to trace through the rename.
- `product-spec/CHANGELOG.md`: themed keepachangelog from the subject-scoped product-spec commits + this plan's features (E5/D11/E1/C9/E4/E2/goal_without_metric).
- `product-spec-critique/CHANGELOG.md`: reconstruct from subject-scoped critique commits across the OLD path (`--follow`) + this plan's features (strengthened lenses).
- `claude-pack/CHANGELOG.md`: bundle update noting the new product-spec*/validate/critique capabilities shipping.

## Related Code Files
- Modify: root `CLAUDE.md`, root `README.md`
- Modify: `product-spec/{SKILL.md,GUIDE-EN.md,GUIDE-VI.md,README.md}`, `product-spec-critique/{SKILL.md,GUIDE-EN.md,GUIDE-VI.md,README.md}`
- Modify: `product-spec/CHANGELOG.md`, `product-spec-critique/CHANGELOG.md` (backfill), `claude-pack/CHANGELOG.md` (bundle)

## Implementation Steps
1. Sweep docs: root `CLAUDE.md` (per-skill sections) + `README.md`; each skill's `SKILL.md`/`GUIDE-EN`/`GUIDE-VI`/`README`. Reflect every new flag/view/check + strengthened lens + the real example.
2. Backfill changelogs by subject-scope + `--follow` (NOT raw path log); update claude-pack bundle changelog.
3. VI native-review pass on both GUIDE-VI.

## Success Criteria
- [ ] Root `CLAUDE.md` (correct per-skill section only) + `README.md` and all per-skill `SKILL.md`/`GUIDE-EN`/`GUIDE-VI`/`README` updated for every new surface; reference the real Phase-9 example.
- [ ] `product-spec` + `product-spec-critique` CHANGELOGs backfilled by **subject scope + `--follow`** (no critique features mis-attributed to product-spec); `claude-pack` CHANGELOG updated.
- [ ] GUIDE-VI native-reviewed. Full suite still green (docs-only changes).

## Risk Assessment
- Risk: editing the wrong section of the shared root `CLAUDE.md` → scope each edit to the relevant skill's section.
- Risk: changelog mis-attribution (H5) → subject-scope + `--follow`, never raw path log.
- Risk: GUIDE-VI shallow pass under time pressure → this is why 9b is split out with its own budget + native-review step.
