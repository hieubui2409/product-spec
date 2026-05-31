# Changelog

All notable changes to `cleanmatic:claude-pack` are documented here.
Format: [keepachangelog.com](https://keepachangelog.com/en/1.1.0/). Versioning: [semver](https://semver.org/).

## [Unreleased]

## [0.2.2] — 2026-05-31

### Fixed
- `product-spec` graph-view HTML: **Zoom +/− and Reset now work.** The zoom transform was applied to `#diagram`,
  which carries the shared `.ve-card` entrance animation (`ps-fade`, `animation-fill-mode: both`) — and an animated
  property's computed value wins over inline style, so the scale was silently clobbered. The transform now targets a
  non-animated inner `#diagram-scale` wrapper; `#diagram` keeps `overflow: auto` so a zoomed diagram scrolls instead of
  clipping. Verified live in headless Chrome (3× zoom → `matrix(1.3,…)`, reset → `matrix(1,…)`).

### Changed
- `product-spec` worked example (`examples/acme-shop`): enriched from a thin fixture into a **mature ~2-year product
  spec** — 44 nodes (1 PRODUCT, 1 Vision, 6 BRD goals, 7 PRDs, 11 epics, 18 stories), 5 personas, 4 competitors, risk
  registers, target dates (incl. shipped/past), `depends_on` chains, and full MoSCoW (Must/Should/Could/Won't) +
  Now/Next/Later coverage. Generated via the skill's own `generate_templates.py` (no hand-authoring). Validates clean:
  0 errors on `check_consistency` / `check_traceability`. Gives the board/explorer/risk/competition/MoSCoW views real
  data to render.

## [0.2.1] — 2026-05-31

### Changed
- `claude-pack` usage guides (`GUIDE-VI.md` + `GUIDE-EN.md`): present the **skill flag** form
  (`/cleanmatic:claude-pack --flag`) as the second way to run each use case — matching the product-spec guide
  pattern — and keep the underlying `python -m pack` invocation as a dev-facing "runs under the hood" note.

## [0.2.0] — 2026-05-31

Documentation + onboarding release. No change to the pack builder core or the determinism contract.

### Added
- Per-skill **usage guides** (`GUIDE-VI.md` + `GUIDE-EN.md`) for both bundled skills: every use case as a full sample conversation, covering the natural-language way (preferred) and the flag/CLI equivalent. product-spec guides use the `examples/acme-shop` worked sample.
- `cleanmatic:product-spec/install.ps1` — Windows-native installer (parity with `claude-pack`): creates the shared venv, installs `pyyaml`, and vendors Mermaid + marked + DOMPurify with sha256 verification.
- **Venv-bootstrap operating instruction** in both `SKILL.md` files + repo-root `CLAUDE.md`: when the shared venv is missing, the LLM asks (AskUserQuestion) to run the installer instead of silently failing or falling back to system Python.

### Changed
- Repo-root `README.md` now covers **both** skills (product-spec + claude-pack) as an umbrella, with per-skill install (POSIX + Windows) and deep links.
- Cross-references to the new guides added to both `SKILL.md` + `README.md` files and the two `CLAUDE.md` operating-guide sections.

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
