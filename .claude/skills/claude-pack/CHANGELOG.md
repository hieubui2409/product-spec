# Changelog

All notable changes to `cleanmatic:claude-pack` are documented here.
Format: [keepachangelog.com](https://keepachangelog.com/en/1.1.0/). Versioning: [semver](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-05-29 (dogfood release)

First internal release. Used to pack `cleanmatic:product-spec` + `cleanmatic:claude-pack` from this repo.

### Added
- Manifest-first selection (`.claude/pack.manifest.yaml`) with CLI flag override and interactive fallback.
- Deterministic tar.gz builder: PAX format, file-granular sorted walk, `mtime=0`, `uid=gid=0`, gzip header `mtime=0`. Same source → byte-identical bytes.
- Always-drop safety filter (HARD, non-negotiable): `.env`/`.envrc`, SSH keys, `.netrc`/`.pgpass`, `.git/` + VCS dirs, runtime caches, session state, build artifacts, `*.pem`/`*.key`/keystores, `*token*.json`/`*secret*.json`. `settings.json` + `.ck.json` opt-in only.
- `_shared/` dependency detection: warn-only (fenced code blocks stripped first); opt-in via `--include-shared`.
- Hardened manifest validation: SemVer 2.0.0 (build metadata), absolute-path + `..`-traversal rejection, duplicate detection, strict known-keys, on-disk existence checks. Stable error codes (`MANIFEST_E###`).
- Bundled multiplatform recipient installer (`install.sh` POSIX + `install.ps1` Windows), version-aware (STALE / NEWER / OK SAME).
- SHA256 sidecar (coreutils format) + embedded `MANIFEST.json` (schema 1.0, per-file SHA256).
- 25 CLI flags including `--dry-run`, `--compute-sha`, `--max-size`, `--source-date-epoch`, `--include-shared`, `--json`.
- Modularized `pack/` subpackage (args, cli, selection, tarball, manifest_io, templates) — each < 200 LOC.
- 57 pytest tests (synthetic golden blocking + live product-spec integration marker) + 3-scenario eval.
- Documentation: SKILL.md, README + FAQ, manifest-spec, flag-reference, safety-rules, workflow-pack, error-catalog, troubleshooting, maintainers-guide.

### CI
- GitHub Actions matrix CI: Ubuntu + macOS + Windows × Python 3.11 / 3.12 / 3.13 (9 jobs, `fail-fast: false`); pre-merge gate runs `pytest -m "not integration"` + a dry-run pack smoke.
- Release pipeline: tag `claude-pack-v*.*.*` → reproducible build (`SOURCE_DATE_EPOCH` from commit time) → SHA256 verify → upload tarball + sidecar to GitHub Releases.
- Weekly integration check (`cron 0 0 * * 0`, `workflow_dispatch`): live product-spec dogfood, non-blocking (`continue-on-error`).

### Notes
- `_shared/` policy is warn-only (not auto-include) to avoid false positives from doc code blocks.
- `pack.py` is cross-platform (POSIX + Windows) via `os.replace`.
- `built_at` is deterministic by default (epoch 0); pass `--source-date-epoch env` for a real provenance date — the release pipeline does this from the git commit time.
- v0.1.0 guarantees **same-OS** byte-identity; cross-OS byte-identity is gated on the 0.5.0 release.
- Side-effect: back-ported the `--dev` flag pattern to `cleanmatic:product-spec/install.sh` (pytest is now dev-only there too).
