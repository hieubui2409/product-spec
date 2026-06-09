---
phase: 5
title: "Installer + docs + release cut"
status: completed
priority: P2
effort: "2-3h"
dependencies: [4]
---

# Phase 5: Installer + docs + release cut

## Overview

Three parts: **(1)** update the installer so `--memory-hook`/`--critique-hook` flip the config flag (now that the bundle wires the enforcement hooks permanently — validate D3); **(2)** docs for the toggle + crash log; **(3)** CUT a release version (validate D4 — not just stage). Git-tracking + `.gitignore` fixes already landed in Phase 2/3; this phase confirms they pack.

## Requirements

- Functional: installer (`install.sh` / install logic) — `--memory-hook`/`--critique-hook` now FLIP the `product-spec-hooks.json` enforcement flag to `true` instead of adding settings.json wiring (wiring is now permanent in the shipped `settings.json`). Without the flag, the keys stay false ⇒ hooks no-op. Document the new meaning. Verify a fresh install leaves enforcement OFF by default.
- Functional: telemetry `SKILL.md` "Hook config & crash log" section: disable a hook via `product-spec-hooks.json`, the telemetry-vs-enforcement default asymmetry, `CK_TELEMETRY_DISABLED`, crash-log location + `CK_HOOK_AUDIT_DISABLED`, `mark_bash_start` ⇒ `ms`.
- Functional: dry-run pack CONFIRMS `hook_runtime.py`, `product-spec-hooks.json`, and the wired `settings.json` are present; `hook_io.py` is GONE (consolidated into `hook_runtime.py`); `.logs/` + `__tests__` excluded.
- Functional: **cut a release version** (validate D4) — bump telemetry `SKILL.md metadata.version` + its `CHANGELOG.md`, fill root `/CHANGELOG.md [Unreleased]`, then run the release flow (`release.py --release X.Y.Z --apply`, or `--bump`). The owner pushes the tag (release skill prints it). Confirm A4 version-sync gate would pass.
- Non-functional: respect `docs/` update policy — document user-visible behavior; the enforcement-wiring change IS user-visible (install semantics) → must be documented + changelogged.

## Architecture

- `product-spec-hooks.json` committed (Phase 3 added the `!` rule) → confirm it's in the packed bundle.
- Crash log runtime/ignored → excluded from pack; `.gitignore:121` fix (Phase 2) makes `.claude/hooks/.logs/` explicitly ignored; confirm `hook-crashes.log*` not packed.
- Release cut (validate D4): bump telemetry `SKILL.md metadata.version` + skill `CHANGELOG.md`, fill root `[Unreleased]`, run `release.py --release X.Y.Z --apply` (or `--bump`). CI builds the deterministic tarball on the owner's tag push — do NOT hand-build. Interview the owner on the version number before `--apply`.
- Installer: locate the install script's hook-wiring logic; the enforcement hooks are now ALWAYS in the shipped `settings.json`, so the flags' job changes from "wire" to "set `product-spec-hooks.json` enforcement key true". A fresh install must leave them false.

## Related Code Files

- Modify: `.claude/skills/telemetry/SKILL.md` (config + crash-log section; version bump if releasing)
- Modify: `.claude/pack.manifest.yaml` (include new files if not auto-covered)
- Modify: `.gitignore` (ignore `.logs/hook-crashes.log*` if not already)
- Modify (if releasing): `.claude/skills/telemetry/CHANGELOG.md`, root `/CHANGELOG.md`
- Read for context: `.claude/skills/release/SKILL.md`, current `pack.manifest.yaml`

## Implementation Steps

1. Update installer hook-wiring logic: `--memory-hook`/`--critique-hook` flip the config flag, not settings.json wiring. Verify fresh install ⇒ enforcement OFF.
2. Write the SKILL.md "Hook config & crash log" section (table: 7 stems → default → how to disable; asymmetry note; `mark_bash_start`⇒`ms`; `track_skill_invocation` one-key-two-events; both env switches).
3. Confirm `pack.manifest.yaml` selects `hook_runtime.py` + `product-spec-hooks.json` (entries added Phase 2/3); confirm wired `settings.json` packs.
4. Dry-run pack (`python -m pack`): new files present, no `hook_io.py`, crash log + `__tests__` excluded.
5. `git ls-files` assertion: `hook_runtime.py` + `product-spec-hooks.json` tracked.
6. Fill root `/CHANGELOG.md [Unreleased]` + telemetry skill changelog/version; cut via `release.py --release X.Y.Z --apply` after owner confirms the version; owner pushes the tag.

## Success Criteria

- [ ] Installer `--memory-hook`/`--critique-hook` flip the config flag; fresh install leaves enforcement OFF.
- [ ] SKILL.md documents 7-hook toggle (with asymmetry) + crash log + both env switches + `ms`/`mark_bash_start`.
- [ ] Dry-run pack includes `hook_runtime.py`, `product-spec-hooks.json`, wired `settings.json`; NO `hook_io.py`; excludes crash log + `__tests__`.
- [ ] `.gitignore` covers the crash log (`:121` fixed in Phase 2).
- [ ] Version cut: telemetry SKILL.md version == its CHANGELOG top == root `/CHANGELOG.md` top == manifest `version:` (A4 gate green); owner handed the tag-push command.

## Risk Assessment

- Risk: own-config silently NOT shipped → recipients can't toggle. Mitigation: dry-run pack assertion (step 4) is a hard gate.
- Risk: crash log accidentally committed (PII/noise). Mitigation: `.gitignore` rule + manifest exclusion both verified.
- Risk: over-documenting internal refactor. Mitigation: keep it to the user-facing toggle + log location; skip the DRY/refactor narrative in user docs.
