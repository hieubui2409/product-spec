---
phase: 5
title: "E4 stakeholder brief (via --summary --audience)"
status: pending
priority: P3
effort: "0.5d"
dependencies: []
---

# Phase 5: E4 — stakeholder brief via `--summary --audience exec|release-notes`

> **Rerouted after red-team (2026-06-03).** No new `--brief` flag — the exec one-pager IS today's
> `--summary`. Extend `--summary` with an `--audience` modifier instead (surface budget H8; DRY M1).

## Overview
A thin audience-facing brief generated FROM the spec, reusing `--summary`. `exec` flavor = the existing
exec one-pager; `release-notes` flavor = "what changed since last approved" pulling from the C9 audit
trail. Different audience, same source-of-truth. No new top-level flag.

## Requirements
- Functional: `--summary --audience exec|release-notes`; `exec` default (= current `--summary` behavior); bilingual via session `lang`.
- Non-functional: DRY — reuse `--summary`'s value-assembly path; no network.

## Key facts (from research + red-team)
- `--summary` → `docs/product/exec-summary.md`; the exec template's token VALUES (name+core-value, BRD goals, PRDs, roadmap, personas, top-3 risks) are assembled by the **`--summary` workflow**, NOT by `generate_templates.py`.
- **M1 correction:** `generate_templates.render()` is pure `{{token}}` substitution with a hard error on any unresolved token (`generate_templates.py:86,135`). It is NOT an assembler. So "reuse exec_summary" means reuse the **`--summary` value-assembly path** (where the token VALUES are built), then render — do NOT expect `--type exec_summary` to hand back populated content.
- No dedicated release-notes mode exists. The C9 trail (Phase 4) is the since-last-approved source.

## Architecture
- Add an `--audience` modifier to `--summary` (default `exec`). `exec` = current behavior unchanged.
- `release-notes` = consume the Phase-4 `assemble_audit_trail.py` since-last-approved-snapshot delta into a release-notes template; render via the same value-assembly→template path as exec.
- **Dependency split (per red-team F8):** `exec` is independent (ships without Phase 4); `release-notes` depends on Phase 4. Reflected in the frontmatter as a soft note, not a hard block, because exec carries the phase.

## Related Code Files
- Modify: `.claude/skills/product-spec/SKILL.md` (add `--audience` to `--summary`, not a new flag) + menu text + CLAUDE.md pointer
- Modify: the `--summary` value-assembly path (identify in `workflow-validate.md` `--summary` section) to branch on audience
- Create: a `release_notes` template (mirror the exec-summary template file)
- Reuse: Phase 4 `assemble_audit_trail.py` (release-notes delta)

## Implementation Steps
> **TDD:** write step 4 tests FIRST, confirm fail, implement to green, re-run full suite.
1. Locate the `--summary` value-assembly path (the code/workflow that builds the exec token VALUES); add an `--audience` branch.
2. `exec` flavor → unchanged output (regression-guard the existing exec-summary).
3. `release-notes` flavor → assemble since-last-approved delta from `assemble_audit_trail.py`, fill a release-notes template (bilingual).
4. Tests: `--audience exec` reproduces current exec-summary byte-for-byte (regression); `--audience release-notes` renders from a spec with a prior approved snapshot (EN/VI); unresolved-token guard does not fire (all values supplied).

## Success Criteria
- [ ] `--summary --audience exec` = current exec one-pager (no new flag, regression-clean).
- [ ] `--summary --audience release-notes` emits a since-last-approved doc using the C9 trail.
- [ ] Reuses `--summary`'s value-assembly path (no token-sub misuse, no new assembler).
- [ ] exec ships without Phase 4; release-notes gated on Phase 4. Tests pass; full suite green.

## Risk Assessment
- Lowest-risk phase. Pitfall: treating `generate_templates.render()` as an assembler → addressed by M1 (reuse the value path).
- If Phase 4 slips, ship `--audience exec` alone; gate release-notes behind Phase 4.
