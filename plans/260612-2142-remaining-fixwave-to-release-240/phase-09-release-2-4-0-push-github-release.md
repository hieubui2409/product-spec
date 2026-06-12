---
phase: 9
title: "Release 2.4.0 push + github release"
status: pending
priority: P1
effort: "0.5d"
dependencies: [1, 2, 3, 4, 5, 6, 7, 8]
---

# Phase 9: Release 2.4.0 + push + GitHub release (Gate C)

## Overview
Cut bundle release 2.4.0: bump the 4 skills (version + per-skill CHANGELOG), fill root `[Unreleased]`, lock it
via `release.py --apply`, commit, push tag → CI builds tarball + creates GitHub release. **Runs only after the
controller's Stage-4 code-review + Stage-5 interview + release-notes sign-off (Gate C).** Owner authorized Claude
to push tag + release directly.

## Requirements
- Functional: 4 skills' `SKILL.md metadata.version` + per-skill `CHANGELOG.md` top bumped together (A4 gate);
  this round's entries added to each skill CHANGELOG + root `[Unreleased]`; `release.py --release 2.4.0 --apply`
  locks root `[Unreleased]`→`[2.4.0]` + bumps `pack.manifest.yaml`; commit; push tag `product-spec-v2.4.0`;
  verify GitHub release (CI) or fallback manual `gh release create`.
- Non-functional: `verify_skill_versions.py` green BEFORE `release.py --apply`. Verify git remote before push.

## Version deltas (scout-confirmed current → target)
| Skill | SKILL.md | per-skill CHANGELOG top | → target (minor) |
|---|---|---|---|
| product-spec | 2.3.1 | [Unreleased] | **2.4.0** |
| product-spec-critique | 1.2.1 | [Unreleased] | **1.3.0** |
| release | 1.1.1 | [Unreleased] | **1.2.0** |
| telemetry | 1.0.1 | [Unreleased] | **1.1.0** |
| bundle manifest | 2.3.0 | root [Unreleased] | **2.4.0** |

(Each skill changed across the field-audit waves; product-spec + telemetry changed most this round. All bump minor.)

## Architecture / runbook (scout-verified)
1. Add this round's entries (P10b/P11/#9) to each affected per-skill CHANGELOG `[Unreleased]` + root `[Unreleased]`.
2. Bump each skill SKILL.md `metadata.version` + lock its CHANGELOG `[Unreleased]`→`[X.Y.Z] — <date>`.
3. `verify_skill_versions.py` → must be green.
4. `release.py --release 2.4.0` (dry-run) → review; then `--apply` (locks root CHANGELOG + bumps manifest atomically).
5. `git add` changed files; commit `release: product-spec v2.4.0`; `git tag product-spec-v2.4.0`; verify remote;
   `git push origin HEAD` + `git push origin product-spec-v2.4.0`.
6. Tag push fires `.github/workflows/release.yml` → builds deterministic tarball + sha256, extracts `[2.4.0]` body,
   creates GitHub Release with both assets. Verify release page; fallback manual `gh release create` if CI absent/fails.

## Related Code Files
- Modify: 4× `SKILL.md` (metadata.version), 4× per-skill `CHANGELOG.md`, root `CHANGELOG.md`, `.claude/pack.manifest.yaml`
- Run: `verify_skill_versions.py`, `release.py`, pack build (CI), git tag/push, `gh release` (CI or fallback)
- Modify: BACKLOG.md (mark waves shipped), REVIEW.md (close ticked rows / note Cycle 3 remaining = LIB-9 only)

## TDD — gate, not new code
Documentation/release phase. Gates instead of RED→GREEN:
1. `verify_skill_versions.py` green (4 skills version==changelog-top).
2. `release.py --release 2.4.0` dry-run output reviewed (correct lock + manifest bump).
3. `test_version_sync.py` (`bundle_changelog_top==manifest_version`) green after apply.
4. Full suite + `CONTRIBUTING.md:69` green on the release commit.

## Pre-push gate checklist (red-team C3/H4/M1 — ALL must pass before any push)
- [ ] `git status --porcelain` empty (clean tree).
- [ ] current branch == `master` (not detached/stray): `git rev-parse --abbrev-ref HEAD`.
- [ ] all P1-P8 work committed (no staged/unstaged residue from the cook run).
- [ ] `git remote -v` → origin is the intended repo.
- [ ] `release.py --extract 2.4.0` prints a NON-EMPTY body (guards the CI release-notes regex).
- [ ] `verify_skill_versions.py` green AND `test_version_sync.py` green (bundle root==manifest — NOT covered by verify_skill_versions).
- [ ] full suite + `CONTRIBUTING.md:69` green **on the exact release commit**.
- [ ] run CI's exact verify command locally (fresh-venv `verify_skill_versions.py` + `--extract`) to avoid post-push CI abort.

## Implementation Steps
1. Compose per-skill + root CHANGELOG entries for P10b/P11/#9.
2. Bump 4 SKILL.md versions + lock 4 per-skill CHANGELOGs.
3. `verify_skill_versions.py`.
4. `release.py --release 2.4.0 --apply`; commit `release: product-spec v2.4.0`.
5. **Gate C**: present 2.4.0 release notes (the locked `[2.4.0]` body) to owner for sign-off (controller Stage-5).
6. **Run the pre-push gate checklist above** — every box ticked.
7. `git tag product-spec-v2.4.0`; push HEAD + tag.
8. Watch `release.yml`; verify GitHub release (tarball+sha256); fallback `gh release create` if CI absent/fails.

## Success Criteria
- [ ] `verify_skill_versions.py` green; 4 skills version==changelog-top.
- [ ] root `[2.4.0]` == `pack.manifest.yaml` version (`test_version_sync` green).
- [ ] full suite + CONTRIBUTING:69 green on release commit.
- [ ] **Pre-push gate checklist fully ticked** (clean tree · master · committed · `--extract` non-empty · CI verify local).
- [ ] **Gate C sign-off received** from owner on the 2.4.0 release notes before push.
- [ ] tag `product-spec-v2.4.0` pushed; GitHub release live with tarball + sha256.
- [ ] BACKLOG/REVIEW updated (Cycle 3 remaining = LIB-9 only).

## Risk Assessment
- A4 gate fail (forgot a bump) → run `verify_skill_versions.py` before apply; bump SKILL.md + CHANGELOG together.
- Push to wrong/absent remote → `git remote -v` verify before push.
- CI release.yml absent/fails → fallback manual pack build + `gh release create` with tarball+sha256.
- Premature release (review/interview not done) → phase blockedBy 1-8 + Gate C sign-off required.
