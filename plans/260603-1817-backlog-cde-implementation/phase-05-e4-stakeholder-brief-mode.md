---
phase: 5
title: "E4 stakeholder brief mode"
status: pending
priority: P3
effort: "0.5d"
dependencies: [4]
---

# Phase 5: E4 stakeholder brief mode (`--brief`)

## Overview
A thin audience-facing brief generated FROM the spec — exec one-pager / release-notes — reusing the
existing `--summary` and `--export` assemblers. Different audience, same source-of-truth. Cheapest feature.

## Requirements
- Functional: `--brief <exec|release-notes>` (or `--brief --audience …`) produces a one-page artifact; bilingual via session `lang`.
- Non-functional: DRY — reuse existing assemblers, no new generator; no network.

## Key facts (from research)
- `--summary` → `docs/product/exec-summary.md` via `generate_templates.py --type exec_summary` (fixed inputs: name+core-value, BRD goals, PRDs, roadmap, personas, top-3 risks).
- `--export` → flexible tree-slice via `assemble_digest.py` (md/html, `--depth`, `--compact-mode`).
- Both inherit session `lang`; no per-flag lang override today.
- No dedicated release-notes mode exists.

## Architecture
- `--brief exec` = exec one-pager: reuse the exec_summary template path; can ship WITHOUT Phase 4.
- `--brief release-notes` = "what changed since last approved snapshot": pulls from the C9 audit trail (Phase 4) + change-log; **depends on Phase 4** for this flavor only.
- Add a release-notes template variant to `generate_templates.py`; no new assembler.

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/generate_templates.py` (add `brief`/`release_notes` template type)
- Reuse: `assemble_digest.py`, exec_summary path, Phase 4 `assemble_audit_trail.py` (release-notes flavor)
- Modify: SKILL.md (flag + menu), CLAUDE.md pointer, references/workflow-validate.md (`--summary` section neighbor) or a short workflow note

## Implementation Steps
> **TDD:** write step 4's tests FIRST (exec brief renders EN/VI from a fixture; release-notes brief from a spec w/ a prior approved snapshot), confirm they fail, then implement the template variants to green; re-run full suite.
1. Add `--brief` flag with audience preset; default `exec`.
2. exec flavor → render exec one-pager from existing exec_summary inputs (bilingual).
3. release-notes flavor → consume C9 trail (since-last-approved delta) into a release-notes template.
4. Tests: exec brief renders from a fixture spec (EN/VI); release-notes brief renders from a spec with a prior approved snapshot.

## Success Criteria
- [ ] `--brief exec` emits a one-page exec brief (bilingual) reusing exec_summary; works without Phase 4.
- [ ] `--brief release-notes` emits a since-last-approved release-notes doc using the C9 trail.
- [ ] No new assembler created (DRY); no network.
- [ ] Tests pass; 50 existing untouched.

## Risk Assessment
- Lowest-risk phase. Pitfall: duplicating assembler logic — forbidden, reuse only.
- If Phase 4 slips, ship `--brief exec` alone; gate release-notes flavor behind Phase 4.
