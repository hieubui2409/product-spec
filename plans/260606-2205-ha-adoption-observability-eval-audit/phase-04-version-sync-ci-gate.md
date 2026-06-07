# Phase 04 — Version-sync CI gate (A4)

**Item:** A4 · **Prio:** P1 · **Effort:** S · **Status:** pending · **Depends:** none

## Context links
- Blueprint Lens D: `…ha-implementation-blueprint…` (§LENS D, version-sync gate — "CM can beat HA here")
- Existing (E5): `.claude/skills/claude-pack/scripts/verify_skill_versions.py` (shape+presence only, release-time only)
- CI to extend: `.github/workflows/cross-skill-bug-class.yml`

## Overview
Today `verify_skill_versions.py` only checks each SKILL.md `metadata.version` is *present + semver*, and only at **release** time. Gap: a PR can bump SKILL.md but forget CHANGELOG (or vice-versa) and nothing catches it. Add a PR-time gate that each skill's SKILL.md version **matches its own CHANGELOG.md top entry**.

## ⛔ GATE H1 — claude-pack BREAKS the equality on a clean repo (verified)
- product-spec: CHANGELOG `2.2.0` == SKILL.md `2.2.0` ✅ · critique: `1.2.0` == `1.2.0` ✅
- **claude-pack: CHANGELOG `1.4.0` ≠ SKILL.md `0.2.0`** ❌ — its CHANGELOG tracks the **bundle** version (E5 decoupling), not the skill version.
→ A naive `SKILL.md == CHANGELOG top` check is **RED on a correct tree**. **A4 checks product-spec + critique ONLY; EXCLUDE claude-pack.** PO confirm the claude-pack CHANGELOG is intentionally bundle-versioned (plan.md Q2) before coding.

## Key insights
- A4 check = **SKILL.md version == CHANGELOG.md first semver `## [X.Y.Z]`**, **for product-spec + critique only** (claude-pack excluded per gate H1).
- `## [Unreleased]` is the **NORMAL top heading of all 3 changelogs** (verified) — NOT an edge. Helper takes the **first semver heading, skipping `[Unreleased]`**. This is the PRIMARY spec.
- Do **NOT** add a `manifest.version == CHANGELOG` equality — contradicts E5 (leave manifest↔tag in release.yml).
- Ride the `bug_class` marker channel (existing `cross-skill-bug-class.yml`, path-filtered).

## Requirements
**Functional**
- For **product-spec + critique** (NOT claude-pack): parse SKILL.md `metadata.version` + first semver `## [X.Y.Z]` (skip `[Unreleased]`) from CHANGELOG.md → assert equal.
- Fail (exit 1 / pytest fail) on drift, naming the skill + both values.
- Runnable locally + CI.

**Non-functional**
- Reuse `verify_skill_versions.py`'s frontmatter parse (DRY) — extend it, don't fork.
- Deterministic, no network.

## Architecture
Two clean options (pick in step 1):
- **(a) Extend `verify_skill_versions.py`** with a `--check-changelog` mode that also reads CHANGELOG top + compares. Wire as a CI step.
- **(b) New `test_version_sync.py` (`@pytest.mark.bug_class`)** per skill, reusing the parser. Rides existing `cross-skill-bug-class.yml` automatically.

**Recommended: (b)** — `bug_class` channel already runs per-skill on PR; least new CI plumbing.

## Related code files
**Create**
- `.claude/skills/claude-pack/scripts/tests/test_version_sync.py` (or per-skill) — `@pytest.mark.bug_class`; reuses `_frontmatter` + a small `changelog_top_version()` helper.
- (if helper shared) extend `verify_skill_versions.py` with `changelog_top_version(path)`.

**Modify**
- None to CI if (b) — `cross-skill-bug-class.yml` already runs `pytest -m bug_class` per skill. (If the test lives in claude-pack/scripts/tests it runs in the claude-pack leg; ensure it checks all 3 skills' files via repo-root paths.)
- Single test checking both skills lives at `claude-pack/scripts/tests/test_version_sync.py` (runs in the claude-pack `bug_class` leg). Repo-root = `Path(__file__).resolve().parents[5]` (one level deeper than `verify_skill_versions.py` which uses `parents[4]` from `scripts/`). **Pin + test in CI working-dir, not just local CWD.**

## Implementation steps
1. Decide (a) vs (b) → default (b).
2. Write `changelog_top_version(changelog_path)`: regex first `^## \[(\d+\.\d+\.\d+)\]` (keepachangelog).
3. Test: for each skill, `metadata.version == changelog_top_version` → assert, clear failure message.
4. Confirm it runs under an existing `bug_class` CI leg (no new workflow needed). If unavoidable, add a minimal step.
5. Deliberately drift one version locally → confirm RED → revert → GREEN.

## Todo
- [ ] approach decided (b default)
- [ ] `changelog_top_version()` helper
- [ ] `test_version_sync.py` (`bug_class`) covering 3 skills
- [ ] confirmed running in existing CI leg
- [ ] RED/GREEN drift check
- [ ] pytest green

## TDD discipline (red → green → refactor)
- **RED first:** write `test_version_sync.py` against **fixtures** (a temp skill dir with a deliberately drifted SKILL.md vs CHANGELOG) → assert it FAILS with a clear message; aligned fixture → passes. Also test `changelog_top_version()` on edge inputs (see below) BEFORE wiring real skills.
- **GREEN:** implement `changelog_top_version()` + comparison. **REFACTOR:** share the frontmatter parser with `verify_skill_versions.py` (no fork).
- Then point at the 3 real skills; expect green (they are currently aligned — confirm).

## Red-team angles (tests MUST cover)
- **`## [Unreleased]` at top** → helper must skip it, take first real semver heading (else false drift).
- **No CHANGELOG / empty / no semver heading** → explicit FAIL, not a crash or false-pass.
- **Pre-release / build-metadata** (`1.2.0-rc.1`, `1.2.0+build`) in heading vs plain `1.2.0` in SKILL.md → decide exact-match policy; test it.
- **Path resolution** when one test reaches all 3 skills from the claude-pack CI leg → repo-root anchor; test must run in CI not just local CWD.
- **Bypass:** ensure the gate actually runs on a PR that touches only SKILL.md (path filter covers it).

## Success criteria
- Bump a SKILL.md version without CHANGELOG → CI red, message names skill + mismatch.
- Aligned repo → green.
- No new standalone workflow (rides `bug_class`).

## Risk
- **Keepachangelog format variance** (`## [Unreleased]` at top) → helper must skip `Unreleased`, take first semver heading.
- **Path resolution** in a single-leg test reaching all 3 skills → use repo-root anchor, test on CI not just local.

## Security
- None (reads version strings only).

## Next steps
- This is where CM exceeds HA (HA has no version-sync gate). Note in STANDARDIZE.md (Phase 6) as a CM-original, not an HA adoption.
