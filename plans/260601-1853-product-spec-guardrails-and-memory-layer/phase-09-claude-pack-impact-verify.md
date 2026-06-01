---
phase: 9
title: "claude-pack-impact-verify"
status: done
priority: P2
effort: "2h"
dependencies: [1, 2, 3, 4, 5, 6, 7, 8]
---

# Phase 9: claude-pack-impact-verify

## Overview
Verification-only closeout: prove the new product-spec files auto-ship via claude-pack with **zero** manifest/safety changes, run the whole-plan consistency gate equivalent (full test suite + structural checks), and confirm no out-of-scope writes. No new feature code.

## Requirements
- Functional: a `claude-pack` dry-run build includes the new references (`guardrails-and-boundaries.md`, split files, `workflow-status.md`, `behavioral-memory.md`) + new scripts (`decision_register.py`, `judgment_cache.py`, `check_fence.py`, `behavioral_memory.py`, `fs_guard.py`) WITHOUT editing `pack.manifest.yaml` or `safety_check.py`.
- Non-functional: confirm runtime `.memory/` files are out of packer scope (packer walks `.claude/` only); confirm `.claude/rules/*` untouched.

## Architecture
- `claude-pack` lists skills by slug + rglob's the whole skill dir (`selection.py:35`) → new files under `.claude/skills/product-spec/` ship automatically. This phase just PROVES it.
- `docs/product/.memory/` lives in a PO project, never in the bundle (`--scan .claude` default).

## Related Code Files
- Read/verify only: `.claude/pack.manifest.yaml`, `.claude/skills/claude-pack/scripts/pack/selection.py`, `.claude/skills/claude-pack/scripts/safety_check.py`
- Run: `claude-pack` dry-run (`python -m pack --dry-run` or equivalent), full `product-spec/scripts/tests/` suite, P2/P3/P4 structural checks

## Verification
1. **(red-team RT-P9 — dry-run emits only a COUNT, not a list)** Do NOT rely on `--dry-run` JSON for a per-file diff. Instead either (a) run a REAL build and extract `MANIFEST.json` (it lists files) and diff its file list vs a pre-plan baseline, or (b) run `safety_check.py`'s subtree walk over `.claude/skills/product-spec/`. Assert every new reference + script is present; additions = only the intended set.
2. `pack.manifest.yaml` + `safety_check.py` byte-unchanged (git diff empty for those).
3. Full `scripts/tests/` suite green (P1/P5/P6/P7/P8 tests).
4. Structural checks from P2/P3/P4 re-run clean (no broken cross-ref, DRY-dup single-home via content-signature, CLAUDE.md marker block byte-unchanged via marker-text awk).
5. **SKILL.md flag-row accuracy (red-team RT-12)**: re-read the P2-authored `--decision`/`--status` rows; confirm each matches the shipped flag surface (P5 `--decision` logic, P8b `--status` output). Flag drift if any.
6. `git status` shows no writes outside `.claude/skills/product-spec/`, repo-root `CLAUDE.md`, and the plan dir.
7. **Whole-plan consistency sweep**: re-read plan.md + all phase files; zero unresolved contradictions / stale refs.

## Implementation Steps
1. Run full test suite + P2/P3/P4 structural checks.
2. Run `claude-pack` dry-run; diff file list.
3. Confirm `pack.manifest.yaml`/`safety_check.py` unchanged (git diff).
4. Confirm no out-of-scope writes (git status).
5. Whole-plan consistency sweep; report.

## Success Criteria
- [ ] New references + scripts present in claude-pack dry-run output; 0 manifest/safety edits.
- [ ] Full test suite green; all structural checks clean.
- [ ] No writes outside the allowed surfaces; `.claude/rules/*` untouched.
- [ ] Consistency sweep: zero unresolved contradictions.

## Risk Assessment
- A new runtime-state dir accidentally added UNDER the skill → would auto-ship; this phase's dry-run diff catches it (then name it a drop-dir or add to ALWAYS_DROP_DIRS — only if it happens).
- Verification-only → lowest risk; gate before declaring the plan done.
