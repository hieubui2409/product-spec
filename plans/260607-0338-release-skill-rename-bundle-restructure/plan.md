# Release-skill rename + bundle restructure (BREAKING)

**Created:** 2026-06-07 · **Branch:** master · **Mode:** breaking change (PO-authorized) · **Risk:** HIGH (touches production release pipeline)

## Re-learn delta (HA model re-scanned 2026-06-07 — supersedes earlier path refs)

The human-analyzer release tooling **moved + modularized** since this plan was first drafted. Authoritative current state:
- **Engine relocated:** `tools/release/release_changelog.py` → **`.claude/skills/_framework-shared/scripts/release.py`** (`REPO=parents[4]`). Same function set: `extract_section`, `_section_exists`, `lock_unreleased`, `bump_version`, `manifest_version`, `set_manifest_version`, `_git`, `_do_extract`, `_do_release`. Flags: `--extract / --release / --bump {major,minor,patch} / --pre-release LABEL / --date / --apply / --push` (`--push` requires `--apply`; default dry-run prints git cmds). Tag `frameworks-v<ver>`.
- **HA now splits into 5 scripts:** `release.py` (changelog lifecycle) · `release_notes.py` (deterministic catalog `docs/RELEASE-NOTES-v<ver>.md` + `_assert_pii_clean`) · `build_pack.py` (reproducible tarball, `--verify` build-twice) · `scan_pack_pii.py` (fail-closed real-name/secret gate) · `safety_filter.py` (non-removable drop rules).
- **CI body flow:** `release.py --extract <ver> > dist/RELEASE-BODY.md` → uploaded via `body_path:` (replaces `generate_release_notes: true`). Plus a `--verify` determinism gate + `scan_pack_pii.py` gate + `dist/SHA256SUMS`.
- **Old `generate_changelog.py` (auto-embedded git log) was REMOVED** — it leaked bare display names (PIIR-S4). Lesson already baked into our deterministic `[Unreleased]`-lock decision.

**What this changes for cleanmatic (3-skill repo):**
1. **Only need to ADD `release.py`** (the changelog-lifecycle engine) — cleanmatic ALREADY has the rest as `pack/` modules (`build_pack.py`≈`python -m pack`, `safety_filter.py`≈`safety_check.py`, per-file catalog ≈ embedded `MANIFEST.json`). DRY: reuse `pack/`, don't port HA's build scripts.
2. **DROP decisions REAFFIRMED:** no `release_notes.py` RELEASE-NOTES catalog (cleanmatic embeds `MANIFEST.json` per-file catalog in the tarball already); no `scan_pack_pii.py` real-name gate (cleanmatic has NO character corpus → HA's `pii_tokens` loaders no-op anyway; cleanmatic's `safety_check.py` already scrubs secrets). The GitHub body = locked CHANGELOG section via `--extract`.
3. **Engine home:** `.claude/skills/release/scripts/release.py` (cleanmatic has no `_framework-shared`; the `release` skill owns packaging). Path math: `REPO = parents[?]` — VERIFY depth from `.claude/skills/release/scripts/` (= `parents[3]`) at implement time.
4. **ADD `--pre-release` + `--date` flags** for parity (earlier draft omitted them).
5. **CI:** adopt `--extract → dist/RELEASE-BODY.md → body_path` precisely; keep cleanmatic's existing SHA256 sidecar + determinism eval (`sha256_stable`/`gzip_mtime_zero`); optionally add a `python -m pack` build-twice verify.

---

## Intent (PO directive)
- Rename skill **`claude-pack` → `release`** (invoke `cleanmatic:release`). Rationale: "release" is the umbrella; *building a tarball* and *pushing a tag* are both instances of release.
- Rename bundle artifact **`claude-pack-{v}.tar.gz` → `product-spec-{v}.tar.gz`** (`bundle_name: product-spec`).
- Adopt HA's release-changelog model: root `/CHANGELOG.md` `[Unreleased]` flow + `release_changelog.py` helper + GitHub Release body = the just-locked changelog section.
- Breaking changes allowed. Tag-push / release cut stays **owner-owned** (helper prints the command, never pushes).

## Decisions (RESOLVED by PO)
1. **Tag prefix** `claude-pack-v*` → **`product-spec-v*`** ✓ (repo renamed to `product-spec`; artifact `product-spec-{v}.tar.gz`).
2. **bundle_name** → **`product-spec`** ✓ (PO renamed the GitHub repo to `product-spec`; it is the ecosystem baseline — no skill-name-clash concern, product-spec IS the product).
3. **Python package** `scripts/pack/` (`python -m pack`) → **keep `pack`** ✓ (internal packing engine; the *skill* is `release`).
4. **CI workflow files** `claude-pack-*.yml` → **`release-*.yml`** (3 files); update path filters + names.
5. **Skill dir** `.claude/skills/claude-pack/` → **`.claude/skills/release/`** ✓ (git mv, preserve history).
6. **Model fidelity** — full lifecycle of HA `com:release` / **`_framework-shared/scripts/release.py`** (re-scanned 2026-06-07; `--extract/--release/--bump/--pre-release/--date/--apply/--push`, `--push` requires `--apply`, owner-stops-before-push, GitHub body = locked CHANGELOG section via `--extract`). **Adaptation (reaffirmed against new HA structure):** DROP HA's `release_notes.py` RELEASE-NOTES catalog + `scan_pack_pii.py` real-name gate — cleanmatic already embeds `MANIFEST.json` per-file catalog in the tarball, has `safety_check.py` secret scrub, and has NO character corpus (HA's PII loaders would no-op). Reuse cleanmatic's existing `pack/` for the build (≈ HA `build_pack.py`); only ADD the changelog-lifecycle engine. Helper lives at **`.claude/skills/release/scripts/release.py`** (renamed from earlier `release_changelog.py` to match HA; verify `REPO=parents[3]` depth at implement).

## Touchpoint inventory (from scout — must all migrate, or release breaks)
- **Skill dir + identity:** dir rename; `SKILL.md` `name: cleanmatic:release`; `cleanmatic:claude-pack` invocation refs.
- **Manifest:** `pack.manifest.yaml` skills-list entry `claude-pack`→`release`; `bundle_name`→`product-spec`. Defaults `"claude-pack"` in `manifest_loader.py:138`, `manifest_io.py:90`, `build_manifest_writer.py:59`, `manifest_validator.py:65` → `product-spec`.
- **Tarball name:** `pack/cli.py:111` + `pack/pipeline.py:85,89` build `{bundle_name}-{version}.tar.gz` — driven by bundle_name, so manifest change suffices; verify.
- **Release CI** (`claude-pack-release.yml`): tag trigger `claude-pack-v*` (l.6), version derive strip (l.29), `sha256sum -c claude-pack-*` (l.49), `files: dist/claude-pack-*` (l.55-56) → `product-spec-*` + tag `product-spec-v*`. Replace `generate_release_notes: true` with `release.py --extract <ver> > dist/RELEASE-BODY.md` + `body_path: dist/RELEASE-BODY.md`. Optional: build-twice determinism verify (cleanmatic already has SHA sidecar + `sha256_stable` eval).
- **Other CI:** `claude-pack-ci.yml`, `claude-pack-integration.yml`, `cross-skill-bug-class.yml` — path filters `.claude/skills/claude-pack/**` → `.claude/skills/release/**`; rename files.
- **Test path math:** `test_version_sync.py`/`test_verify_skill_versions.py`/`test_bundle_excludes_telemetry.py` `parents[5]`; `verify_skill_versions.py parents[4]`; telemetry `register_telemetry_hooks` REPO_ROOT — re-verify after dir move (depth unchanged, but re-run).
- **Telemetry exclusion test:** `TELEMETRY_HOOK_BASENAMES` unaffected; member-name asserts unaffected; re-run real build.
- **Installers:** `install.sh`/`install.ps1` (skill dir refs), recipient version-aware naming.
- **Docs:** `GUIDE-EN/VI.md`, `README.md`, `references/*.md`, `CLAUDE.md` (claude-pack operating-guide section + release process), `BACKLOG.md`, `STANDARDIZE.md`, `docs/audit-trail/*`.
- **Version model:** root `/CHANGELOG.md` top == manifest version == tag `product-spec-vX.Y.Z` == GitHub body; per-skill `changelog top == SKILL.md` (incl. renamed `release` skill).
- **Out of migration (history, do NOT touch):** `plans/**` prior reports.

## Phases (proposed)
1. **Rename engine** — `git mv` skill dir; update `pack.manifest.yaml` (skill entry + bundle_name); update the 4 default-string sites; update SKILL.md name + invocation. Run pack build → assert `product-spec-{v}.tar.gz`.
2. **CI rewire** — rename 3 workflow files; update path filters + tag trigger `product-spec-v*` + version derive + sha/files globs. (No tag pushed — owner-owned.)
3. **Test + path re-verify** — fix any `parents[]`/REPO_ROOT refs; run all suites (claude→release skill, product-spec, critique, _shared, node).
4. **Release-changelog tooling** — `release.py` in `release/scripts/` mirroring HA's function set (`extract_section`, `_section_exists`, `lock_unreleased`, `bump_version`, `manifest_version`, `set_manifest_version`, `_git`, `_do_extract`, `_do_release`); flags `--extract/--release/--bump/--pre-release/--date/--apply/--push` (`--push` requires `--apply`, default dry-run prints `git tag product-spec-vX.Y.Z && git push`); interview-on-release; root `/CHANGELOG.md` `[Unreleased]`→`[X.Y.Z]—date` deterministic text-lock (refuse empty/existing); CI rewires `generate_release_notes: true` → `release.py --extract <ver> > dist/RELEASE-BODY.md` + `body_path:`. Reuse `pack/` for the actual tarball build. TDD synthetic-first (the lock/bump/extract logic is pure-text → unit-testable without git).
5. **Docs sweep** — guides/README/references/CLAUDE.md/STANDARDIZE/BACKLOG; record EVIDENCE/REVIEW entries; update `docs/audit-trail`.

## Owner-owned boundary
I will NOT: push any tag, cut a release, merge, or rebuild dist for upload. The helper stops before push and prints the exact `git tag … && git push …` for the owner. The actual first release under the new naming is the owner's cut.

## Quality gates (PO-directed order: TDD → red-team → validate → PO confirm)

Each implementation phase passes through this gate chain before the next; the whole restructure passes it again as a suite before release:

1. **TDD (per phase, tests-first):** write/extend tests for the new behavior BEFORE the change, watch them go RED, implement, watch GREEN. New units: `release.py` lifecycle (`lock_unreleased` refuse-empty/refuse-existing, `bump_version` major/minor/patch, `extract_section` exact body, `--push` requires `--apply`) — all pure-text/argparse → unit-testable with no git, no network. Rename touchpoints: a "no dangling `claude-pack`" grep-test + a real `python -m pack` build asserting `product-spec-2.0.0.tar.gz`.
2. **Red-team (task 12):** adversarial pass on the new release pipeline — try to make it cut a wrong/empty release, push without `--apply`, drift the two version axes, leak telemetry into the tarball, or break determinism. Every invariant attacked with a reproducible command+state; findings → `docs/audit-trail/REVIEW.md`.
3. **Validate (full sweep):** all suites green across the renamed `release` skill + product-spec + critique + `_shared` + node; `run_evals.py` structural gate per skill; `test_version_sync.py` both axes (per-skill changelog==frontmatter; bundle root `/CHANGELOG.md`==manifest==`2.0.0`); a real reproducible `python -m pack` build (artifact name + telemetry-exclusion + byte-determinism). No green skip, no faked pass.
4. **PO confirm:** STOP. Present the green suite + red-team verdict + the exact `git tag product-spec-v2.0.0 && git push` command. Owner does the actual tag push that fires release CI (task 14). I never push.

## Test strategy
TDD per phase (gate 1 above); after each phase, run the full multi-skill sweep + a real `python -m pack` build asserting the new artifact name + telemetry-exclusion + determinism. No green skip.

## Open questions (resolve at approval)
1. ~~Tag prefix~~ → **RESOLVED** `product-spec-v*` (Decision 1).
2. ~~bundle_name~~ → **RESOLVED** `product-spec` (Decision 2).
3. ~~Python package~~ → **RESOLVED** keep `pack` (Decision 3).
4. ~~This session vs fresh~~ → **RESOLVED** proceeding (PO added to todo 2026-06-07).
5. ~~MAJOR version~~ → **RESOLVED `2.0.0`** (PO 2026-06-07). Bundle `1.4.0` → `2.0.0`. Tag `product-spec-v2.0.0`; root `/CHANGELOG.md` `[Unreleased]`→`[2.0.0]`; manifest `version: 2.0.0`; per-skill versions bump independently (the renamed `release` skill gets its own major if its contract breaks — decide per-skill at implement).
6. **[resolve at implement, not PO]** `release.py` `REPO=parents[N]` depth from `.claude/skills/release/scripts/` (expected `parents[3]`) — verify empirically, don't assume.
