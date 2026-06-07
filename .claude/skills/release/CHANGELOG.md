# Changelog — release (the release skill)

Changes to the **`cleanmatic:release` skill itself** (deterministic-tarball bundler + root-CHANGELOG release
lifecycle). Pinned to this skill's `SKILL.md` `metadata.version`; the A4 PR-gate asserts the top `## [X.Y.Z]` here
equals that version.

> **Scope:** this is the *skill* changelog. The bundle/release history (what each tagged `product-spec-v*` GitHub
> Release shipped — formerly `claude-pack-v*`) lives in the repo-root [`/CHANGELOG.md`](../../../CHANGELOG.md).
> Versions before `0.3.0` were reconstructed from git history when the two logs were separated.

Format: [keepachangelog.com](https://keepachangelog.com/en/1.1.0/). Versioning: [semver](https://semver.org/).

## [Unreleased]

## [1.1.1] — 2026-06-08

### Changed
- **Installer registrar path follows the self-contained telemetry skill.** `install.sh` / `install.ps1`
  now invoke `.claude/skills/telemetry/scripts/register_telemetry_hooks.py` (was `_shared/scripts/…`) after
  the telemetry code moved into its own skill folder. The opt-out command in the notice updated to match.
- **`pack.manifest.yaml` `_include_shared` reduced to `[lib]`.** `_shared/scripts` no longer exists; only the
  cross-skill eval-gate (`run_evals`, `llm_eval`) still rides `_include_shared`. The telemetry surface ships
  via the `skills:` walk now that it is self-contained. Manifest comment updated.

## [1.1.0] — 2026-06-08

### Added
- **Installer auto-registers telemetry hooks.** The generated `install.sh` / `install.ps1` now run
  `register_telemetry_hooks.py` against the recipient root after install, so the shipped `cleanmatic:telemetry`
  lenses have data out of the box. Idempotent + upgrade-safe (never double-registers); non-fatal; opt out with
  `register_telemetry_hooks.py --remove`.

### Changed
- **`safety_catalog` drops `__tests__/` and `tests/`** from every bundle — test suites + fixtures are dev
  artifacts and never ship to recipients (joins `plans/`, caches, VCS in `ALWAYS_DROP_DIRS`).
- **Bundle telemetry guard inverted** (`tests/test_bundle_excludes_telemetry.py` →
  `test_bundle_includes_telemetry.py`): the suite now asserts the telemetry skill + 5 hooks + shared lens/eval
  code ARE present, while runtime sinks (`.claude/telemetry/`) and test dirs stay OUT. `telemetry` added to
  `test_version_sync.VERSION_SYNCED_SKILLS` (it ships → changelog-pinned).

## [1.0.0] — 2026-06-07

**BREAKING — renamed from `cleanmatic:claude-pack`.** The skill is now `cleanmatic:release`; the bundle artifact is
`product-spec-{version}.tar.gz` (was `claude-pack-{version}.tar.gz`); the release tag is `product-spec-v*` (was
`claude-pack-v*`); `bundle_name` defaults to `product-spec`. The `python -m pack` builder and its determinism
contract are unchanged — only the names and the surrounding release lifecycle changed.

### Added
- **Release-lifecycle engine** (`scripts/release.py`, modelled on human-analyzer's `_framework-shared/release.py`):
  manage the root `CHANGELOG.md` Keep-a-Changelog flow — `--extract X.Y.Z` (print a section body; the GitHub Release
  body), `--release X.Y.Z` / `--bump major|minor|patch` (lock `[Unreleased]` → `[X.Y.Z] — <date>` + bump
  `pack.manifest.yaml`), `--pre-release LABEL`, `--date`, `--apply` (write; default dry-run), `--push` (owner opt-in,
  requires `--apply`). Refuses an empty `[Unreleased]` or an already-locked version. The `git tag product-spec-vX.Y.Z
  && git push` that fires release CI is **owner-owned** (printed, not run, unless `--push`).
- **CI release body from the locked changelog** — the release workflow now publishes `release.py --extract <ver>` as
  the GitHub Release body (replacing `generate_release_notes`).

### Changed
- **Renamed** the skill dir `.claude/skills/claude-pack/` → `.claude/skills/release/` (git history preserved); the
  3 CI workflows `claude-pack-*.yml` → `release-*.yml`; the venv `.pth` `claude-pack.pth` → `release.pth`.

## [0.3.0] — 2026-06-07

Consolidates the skill's evolution since the `0.2.x` onboarding line. The bundler core's determinism contract is
unchanged; this groups the structural, safety, and release-tooling work that landed on the skill.

### Added
- **Release-identity tooling** — `verify_skill_versions.py` (asserts each skill's `metadata.version` is present +
  semver; the release gate) plus `changelog_top_version()` (first released `## [X.Y.Z]`, skipping `[Unreleased]`
  and pre-release/build-metadata headings).
- **A4 version-sync PR-gate** (`tests/test_version_sync.py`, `bug_class`): each skill's `SKILL.md` version must
  equal its own CHANGELOG top; a bundle-identity check ties root `/CHANGELOG.md` top to `pack.manifest.yaml`.
- **Telemetry tarball-exclusion sentinel** (`tests/test_bundle_excludes_telemetry.py`, `bug_class`): selection +
  a real `python -m pack` build prove `.claude/telemetry/` and the CM-local telemetry hooks never reach a bundle.
- **Recipient-installer tests** — a SemVer precedence matrix (`test_installer_semver.py`, incl. PowerShell on the
  Windows leg) + an install e2e (`test_installer_e2e.py`: build → extract → run `install.sh` into a throwaway
  tree → assert clean + idempotent).
- **Eval `_gating` reshape** — claude-pack's `eval/evals.json` moved from bare strings to `_gating:
  structural|llm_advisory` + machine-runnable `check`/`exec`, wired into the shared `run_evals.py` harness.

### Changed
- **Modularized `pack/`** into focused sub-modules (`args`, `cli`, `selection`, `tarball`, `manifest_io`,
  `templates`; `manifest_loader` + `build_manifest` + `safety_check` split out) — each under 200 LOC.
- **Bundles the full pair** — added `cleanmatic:product-spec-critique` (skill + 6 lens/consolidator agents + Stop
  hook) and the `memory-harvester` agent + `memory_gap_hook.py` handler to the manifest.
- **Removed the non-functional `--all` flag** (it errored and ran against the curated-distribution design; use the
  manifest or `--skills <list>`).

## [0.2.1] — 2026-05-31

### Changed
- Usage guides (`GUIDE-VI.md` + `GUIDE-EN.md`) present the **skill-flag form** (`/cleanmatic:claude-pack --flag`)
  as the second way to run each use case, keeping the underlying `python -m pack` invocation as a dev-facing note.

## [0.2.0] — 2026-05-31

Documentation + onboarding release. No change to the pack-builder core or the determinism contract.

### Added
- Per-skill **usage guides** (`GUIDE-VI.md` + `GUIDE-EN.md`) — every use case as a full sample conversation
  (natural-language form preferred, flag/CLI equivalent shown).
- `install.ps1` Windows-native installer parity (shared venv + dependency vendoring with sha256 verification).
- **Venv-bootstrap operating instruction** — when the shared venv is missing, the skill asks (AskUserQuestion) to
  run the installer rather than silently failing or falling back to system Python.

## [0.1.0] — 2026-05-31

First tagged bundler. The deterministic-tarball core.

### Added
- **Manifest-first selection** (`.claude/pack.manifest.yaml`) with CLI flag override + interactive fallback.
- **Byte-deterministic `tar.gz`** — PAX, file-granular sorted walk, `mtime=0`, `uid=gid=0`, gzip header
  `mtime=0`; same source → byte-identical output. Opt-in `--source-date-epoch` for real provenance time.
- **Always-drop safety filter** (HARD, non-negotiable): `.env`/`.envrc`, SSH keys, `.netrc`/`.pgpass`, `.git/` +
  VCS dirs, runtime caches, session state, build artifacts, `*.pem`/`*.key`/keystores, `*token*.json` /
  `*secret*.json`. `settings.json` + `.ck.json` opt-in only.
- **Hardened manifest validation** — SemVer 2.0.0, absolute-path + `..`-traversal rejection, duplicate detection,
  strict known-keys, on-disk existence checks; stable `MANIFEST_E###` error codes.
- **SHA256 sidecar** (coreutils format) + embedded `MANIFEST.json` (schema 1.0, per-file SHA256).
- **Multiplatform recipient installer** (`install.sh` POSIX + `install.ps1` Windows), version-aware
  (STALE / NEWER / OK SAME).
- 25 CLI flags including `--dry-run`, `--compute-sha`, `--max-size`, `--source-date-epoch`, `--include-shared`,
  `--json`; matrix CI (Ubuntu + macOS + Windows × Python 3.11/3.12/3.13).

### Hardening (initial review cycles)
- Tarball path-traversal close, remote-URL/userinfo scrub, semver tightening, Windows-safe path containment,
  `EXDEV` move-failure backup restore, crash-safety against malformed manifests, unified hook matcher across
  validate + selection.
