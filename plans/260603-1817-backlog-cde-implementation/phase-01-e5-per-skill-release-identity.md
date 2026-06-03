---
phase: 1
title: "E5 per-skill release identity"
status: done
priority: P2
effort: "0.5d"
dependencies: []
---

# Phase 1: E5 per-skill release identity

## Overview
Standardize the loose hybrid versioning: give product-spec + product-spec-critique their own
CHANGELOG, keep `version:` in each SKILL.md as truth-of-record, and make the release CI **verify**
SKILL.md versions match the shipped bundle (fail on drift). Single bundle tag stays the release unit.

## Requirements
- Functional: each of the 3 skills has a `CHANGELOG.md` (keepachangelog format); release workflow fails if any SKILL.md `version` is missing/malformed or unaccounted for in the bundle.
- Non-functional: NO new tooling (no Changesets/Lerna — Python+md repo). No CI release split. KISS.

## Key facts (from research)
- `claude-pack-release.yml:27` derives version from **tag** (`claude-pack-v*`), never reads SKILL.md.
- Only `claude-pack/CHANGELOG.md` exists (keepachangelog, theme-grouped). product-spec & critique have none.
- SKILL.md versions today: product-spec `2.0.0`, critique `1.0.0`, claude-pack `0.1.0`; bundle ships `1.1.0` (decorative/divergent).

## Architecture (corrected per red-team)
- CHANGELOG per skill = human changelog (keepachangelog). Bundle GitHub Release notes stay auto-generated from commits (unchanged) — CHANGELOGs are NOT the release-notes source (matches claude-pack's existing split). **PO decision: keep both new CHANGELOGs** (E5 = standardize-hybrid, locked) despite internal-only distribution.
- **`version` is nested `metadata.version`, NOT top-level** (verified: `product-spec/SKILL.md:11`, critique `:11`, claude-pack `:11`). The verifier reads `metadata.version`.
- **Verifier scope = semver shape + presence ONLY** (no cross-version "consistency"): the 3 skill versions (2.0.0/1.0.0/0.1.0) are independent of and divergent from the bundle tag (1.1.0) **by design** — there is no consistency relation to assert. Verifier: each `metadata.version` exists + matches `^\d+\.\d+\.\d+$`; exit 1 on any missing/malformed. Do NOT assert equality with the bundle version.

## Related Code Files
- Create: `.claude/skills/product-spec/CHANGELOG.md`
- Create: `.claude/skills/product-spec-critique/CHANGELOG.md`
- Create: `.claude/skills/claude-pack/scripts/pack/` helper OR `.github/workflows/` inline step — a `verify_skill_versions` check (prefer a small script `.claude/skills/<?>/scripts/verify_skill_versions.py` runnable in CI + locally)
- Modify: `.github/workflows/claude-pack-release.yml` (add verify step before build)
- Reference: `.claude/skills/claude-pack/CHANGELOG.md` (format to mirror)

## Implementation Steps
> **TDD:** write step 5's verifier tests FIRST (valid set passes, missing/garbled version fails), confirm they fail, then implement steps 1–4 to green; re-run full suite.
1. Decide the verifier's home (claude-pack scripts is natural since it owns release). Write `verify_skill_versions.py`: read each SKILL.md frontmatter **`metadata.version`** (nested), validate `^\d+\.\d+\.\d+$`, print a table, exit 1 on any invalid/missing. **No bundle-equality check.** Keep <60 LOC.
2. Seed `CHANGELOG.md` for product-spec (start at its current `2.0.0`) and critique (`1.0.0`), keepachangelog headers + an `## [Unreleased]` section. Backfill is optional — seed with current version only (YAGNI).
3. Add a CI step in `claude-pack-release.yml` calling the verifier before the build job. Fail the release on drift.
4. Document the release discipline (update 3 CHANGELOGs per release) in claude-pack SKILL.md/CHANGELOG release-process note.
5. Add a pytest for the verifier: valid set passes; a missing `metadata:` block fails; a top-level-only `version` (no `metadata.version`) fails; a garbled version fails.

## Success Criteria
- [ ] product-spec + critique each have a keepachangelog `CHANGELOG.md` with `[Unreleased]` + current version.
- [ ] `verify_skill_versions.py` reads nested `metadata.version`, exits 0 on current repo, exits 1 when a version is removed/garbled/non-nested (tested); does NOT assert bundle-equality.
- [ ] `claude-pack-release.yml` runs the verifier before build; drift fails CI.
- [ ] No CI release split introduced (bundle tag remains the single release unit).
- [ ] New pytest passes; existing 50 tests untouched.

## Risk Assessment
- Low risk; additive. Main pitfall: over-engineering into full Changesets — explicitly out of scope.
- Don't make CHANGELOGs the GitHub-release-notes source (would diverge from claude-pack's existing auto-gen). They are human changelogs only.
