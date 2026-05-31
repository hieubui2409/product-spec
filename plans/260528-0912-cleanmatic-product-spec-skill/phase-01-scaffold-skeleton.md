---
phase: 1
title: "Scaffold & Skeleton"
status: completed
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Scaffold & Skeleton

## Overview
Bootstrap the skill folder, write the lean SKILL.md frontmatter + skeleton body (flag routing + no-flag menu + workflow map), and the packaging docs (README, in-skill CLAUDE.md). Establishes the namespace, folder name, and the doc-output contract everything else fills in.

## Requirements
- Functional: skill discoverable + invocable as `/cleanmatic:product-spec`; SKILL.md declares all flags via `argument-hint`; no-flag invocation routes to a detect-state menu (described, not yet implemented).
- Non-functional: SKILL.md < 300 lines (progressive disclosure — detail lives in `references/`); no external API keys; cross-platform Python only.

## Architecture
- **Namespace/folder:** name `cleanmatic:product-spec`. Run `init_skill.py` and confirm the folder it emits (skill-id segment → `product-spec`). If init rejects the `cleanmatic:` namespace, scaffold manually mirroring `skill-creator` layout. Folder = `.claude/skills/product-spec/`.
- **SKILL.md sections (skeleton only; prose filled in Phase 7):** Overview · When to Use · Flags table · No-flag menu · Workflow map (Mermaid) · "Loads references/* on demand" · Resources. Reference loading pointers to Phase 2 spec files.
- **Output contract (documented here, consumed everywhere):** all PO artifacts live under `docs/product/` in the *user's* project (not the skill dir): `PRODUCT.md`, `vision.md`, `brd.md`, `prds/<feature>.md`, `epics/<epic>.md`, `stories/<story>.md`, `.session.md`, `exec-summary.md`, `visuals/`.
- **In-skill CLAUDE.md:** detailed LLM operating guide/context for running the skill (novel for this repo — user-requested; harmless additive file).

## Related Code Files
- Create: `.claude/skills/product-spec/SKILL.md` (frontmatter + skeleton)
- Create: `.claude/skills/product-spec/README.md` (quickstart + flag reference — finalized Phase 8)
- Create: repo-root `CLAUDE.md` (LLM operating guide). **Decision §18 amendment (2026-05-28):** the in-skill CLAUDE.md was consolidated into the repo-root CLAUDE.md + `references/*` because SKILL.md + the on-demand references already absorb the operating-guide content; root placement matches Claude Code's auto-load convention. Skill ZIP ships SKILL.md + references/ only; the dev repo carries the root CLAUDE.md as a dev-side guide.
- Create: dirs `references/ scripts/ assets/templates/ agents/ eval/ examples/`
- Read for pattern: `.claude/skills/skill-creator/SKILL.md`, `.claude/skills/scout/SKILL.md`, `.claude/skills/skill-creator/references/yaml-frontmatter-reference.md`

## Red-Team Corrections
- **Namespace discoverability spike (M1) — GATE:** verified `init_skill.py` accepts `cleanmatic:` (folder = slug `product-spec`, `name: cleanmatic:product-spec`); repo already has `ckm:design` + bare `excalidraw` so multi-prefix coexists. STILL smoke-test before building 8 phases: scaffold a stub SKILL.md, reload, confirm `/cleanmatic:product-spec` actually surfaces/invokes. Gate the rest of the plan on this.
- **SKILL.md line budget (M2):** allocate up front — frontmatter ~15, flags table ~40, no-flag menu ~20, workflow map ~30, reference pointers ~30 → ~135 lines, slack to 300. If routing won't fit, signal to collapse flag surface (don't silently bust the limit).
- **VENV (C1):** use repo venv `./.claude/skills/.venv/bin/python3` for all commands in this repo.

## Implementation Steps
1. **Spike first:** scaffold stub, reload Claude Code, confirm `/cleanmatic:product-spec` invocable. If not, resolve discovery before proceeding. Then run: `./.claude/skills/.venv/bin/python3 ~/.claude/skills/skill-creator/scripts/init_skill.py cleanmatic:product-spec --path ./.claude/skills`. Inspect folder name (expect `product-spec`) + delete example placeholders.
2. Write SKILL.md frontmatter: `name: cleanmatic:product-spec`, `description` (<200 chars, PO-focused triggers), `user-invocable: true`, `when_to_use`, `category: product`, `keywords: [prd, brd, epic, story, product-owner, requirements, traceability]`, `argument-hint: "[--flag] [target]"`, `metadata.version: 1.0.0`.
3. Write SKILL.md skeleton body: flags table, no-flag detect-state menu description, Mermaid workflow map, reference-loading pointers (stubs for Phase 2 files), Resources section.
4. Create empty dir structure + `.gitkeep` where needed.
5. Draft README skeleton + in-skill CLAUDE.md (operating principles: PO audience, no code, DRY, frontmatter=source-of-truth, script-vs-LLM split summary).
6. Validate frontmatter: `~/.claude/skills/.venv/bin/python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py .claude/skills/product-spec/SKILL.md`.

## Success Criteria
- [ ] `quick_validate.py` passes on SKILL.md (frontmatter valid, <300 lines).
- [ ] Folder structure created; example placeholders removed.
- [ ] SKILL.md lists every flag and documents the no-flag menu + output paths under `docs/product/`.
- [ ] README + CLAUDE.md skeletons present.
- [ ] Namespace/folder decision recorded (init output vs manual) in README.

## Risk Assessment
- **init_skill.py rejects `cleanmatic:` namespace** (validator may only allow known prefixes) → mitigate: manual scaffold copying skill-creator structure; keep `name: cleanmatic:product-spec` in frontmatter regardless of folder name.
- **Folder-name mismatch** with invocation expectations → mitigate: verify discovery by checking how an existing bare-folder skill (e.g. `scout` → `ck:scout`) maps folder→name before finalizing.
