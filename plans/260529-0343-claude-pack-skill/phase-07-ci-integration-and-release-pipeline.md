---
phase: 7
title: "CI Integration and Release Pipeline"
status: pending
priority: P1
effort: "3h"
dependencies: [2, 3, 4, 5, 6]
---

# Phase 7: CI Integration and Release Pipeline

## Overview

Add GitHub Actions CI workflow + release pipeline. Validates the determinism contract (T-D1, T-G1a) on a matrix of Ubuntu + macOS + Windows × Python 3.11/3.12/3.13. Pre-merge gate: `pytest -m "not integration"` must pass on every PR. Release pipeline: on tag `claude-pack-v*`, runs deterministic build + uploads `.tar.gz` + `.sha256` sidecar to GitHub Releases.

**Critical:** without CI matrix, the byte-identical determinism guarantee is local-only (validate F8.1 BLOCKING). Cross-platform support (R3.Q2) requires Windows runner to verify `os.replace` + PowerShell installer.

## Context Links

- Plan `## Locked Decisions` row "Platforms: Cross-platform" (R3.Q2)
- Plan `## Release Gates` ladder (0.1.0 → 0.5.0 → 1.0.0)
- Validate report F8.1 (BLOCKING), F8.2 (fail-fast), F8.3 (release pipeline)
- Red-team F1.5 (Python version determinism), F3.1 (Windows pack.py)
- Phase 5 (`pyproject.toml` markers, `requirements-dev.txt`)
- Phase 6 (`pack.manifest.yaml` seed, `dist/` gitignored)
- Convention precedent: any existing `.github/workflows/*.yml` in this repo (check before writing)

## Requirements

**Functional:**
- `.github/workflows/claude-pack-ci.yml` — pre-merge gate:
  - Matrix: `{os: [ubuntu-latest, macos-latest, windows-latest]} × {python: ['3.11', '3.12', '3.13']}` = 9 jobs
  - Steps: checkout · setup-python · run installer (`install.sh --dev` on POSIX, `install.ps1 -Dev` on Windows) · `pytest -m "not integration"` from skill root · `python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0 --dry-run` smoke
  - Triggers: `pull_request` (paths: `.claude/skills/claude-pack/**` + `.claude/pack.manifest.yaml` + workflow file itself)
  - Fail-fast: false (collect all matrix failures)
- `.github/workflows/claude-pack-release.yml` — release pipeline:
  - Trigger: `push` of tag matching `claude-pack-v*.*.*`
  - Ubuntu runner only (determinism guarantees same output across OSes; Ubuntu is canonical)
  - Steps: checkout · install · build with `SOURCE_DATE_EPOCH` from tag commit time · upload `dist/claude-pack-X.Y.Z.tar.gz` + `.sha256` to GitHub Release
  - Uses `gh release create` or `softprops/action-gh-release@v2`
- `.github/workflows/claude-pack-integration.yml` (optional, weekly cron):
  - Trigger: `schedule: cron '0 0 * * 0'` (Sunday 00:00 UTC)
  - Ubuntu only, Python 3.12
  - Runs `pytest -m integration` (live product-spec dogfood)
  - Non-blocking; reports as workflow status only

**Non-functional:**
- Pre-merge workflow runtime <5 min total (matrix runs in parallel; each job <2 min)
- Release workflow runtime <3 min
- Workflows use `actions/checkout@v4`, `actions/setup-python@v5` (latest stable as of 2026)
- All workflows have `permissions:` block: `contents: read` for CI, `contents: write` for release
- Workflows store no secrets in env; release uses `GITHUB_TOKEN` only
- **SOURCE_DATE_EPOCH normalization** (red-team F1.5, validate F8.2): Every CI job runs with `SOURCE_DATE_EPOCH` UNSET. The release pipeline explicitly sets `SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct ${{ github.sha }})` for reproducible-from-tag builds.

## Architecture

```
.github/workflows/
├── claude-pack-ci.yml             — pre-merge matrix, 9 jobs
├── claude-pack-release.yml        — tag → build → release
└── claude-pack-integration.yml    — weekly live-dogfood (optional)
```

**Workflow inter-dependency:**
- CI runs on every PR; merge requires green
- Release runs only on tag; assumes CI was green on the commit being tagged (manual responsibility for v0.1.0; can be enforced via "required status checks" GH setting later)
- Integration is informational; failure does not block merge or release

## Related Code Files

**Create:**
- `/home/hieubt/Documents/cleanmatic-skills/.github/workflows/claude-pack-ci.yml`
- `/home/hieubt/Documents/cleanmatic-skills/.github/workflows/claude-pack-release.yml`
- `/home/hieubt/Documents/cleanmatic-skills/.github/workflows/claude-pack-integration.yml`

**Modify:**
- `.claude/skills/claude-pack/CHANGELOG.md` — add `### CI` subsection to `[0.1.0]` entry
- `.claude/skills/claude-pack/references/maintainers-guide.md` — Section "Refreshing golden test": pin instruction `gh workflow run claude-pack-integration` to verify locally before commit

## Implementation Steps

### claude-pack-ci.yml

1. **Skeleton + matrix:**
   ```yaml
   name: claude-pack CI
   on:
     pull_request:
       paths:
         - '.claude/skills/claude-pack/**'
         - '.claude/pack.manifest.yaml'
         - '.github/workflows/claude-pack-ci.yml'
   permissions:
     contents: read
   jobs:
     test:
       strategy:
         fail-fast: false
         matrix:
           os: [ubuntu-latest, macos-latest, windows-latest]
           python: ['3.11', '3.12', '3.13']
       runs-on: ${{ matrix.os }}
       env:
         SOURCE_DATE_EPOCH: ''   # explicit unset; conftest.py also delenv
   ```

2. **Steps:**
   - `actions/checkout@v4`
   - `actions/setup-python@v5` with `python-version: ${{ matrix.python }}`
   - POSIX install + tests:
     ```yaml
     - name: Install (POSIX)
       if: runner.os != 'Windows'
       run: bash .claude/skills/claude-pack/install.sh --dev
     - name: Install (Windows)
       if: runner.os == 'Windows'
       run: .claude/skills/claude-pack/install.ps1 -Dev
       shell: pwsh
     ```
   - Test invocation (cross-platform via Python module):
     ```yaml
     - name: Run pytest
       run: .claude/skills/.venv/bin/python -m pytest .claude/skills/claude-pack/scripts/tests/ -m "not integration" -v
       shell: bash
     - name: Run pytest (Windows)
       if: runner.os == 'Windows'
       run: .claude\skills\.venv\Scripts\python -m pytest .claude\skills\claude-pack\scripts\tests\ -m "not integration" -v
       shell: pwsh
     ```
   - Smoke dry-run pack to verify cross-platform pack.py:
     ```yaml
     - name: Smoke dry-run pack
       run: .claude/skills/.venv/bin/python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0 --dry-run
     ```

3. **Determinism cross-OS check** (job downstream of matrix):
   ```yaml
   determinism-cross-os:
     needs: test
     runs-on: ubuntu-latest
     steps:
       - ... checkout + install ...
       - name: Build on Ubuntu
         run: |
           .claude/skills/.venv/bin/python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0
           sha256sum dist/claude-pack-0.1.0.tar.gz > sha-ubuntu.txt
       # Compare against artifact uploaded from macos/windows job ... defer to v0.5.0
   ```
   v0.1.0: same-OS determinism only. v0.5.0: cross-OS deterministic byte-identity (recipient-facing guarantee).

### claude-pack-release.yml

4. **Trigger + permissions:**
   ```yaml
   name: claude-pack Release
   on:
     push:
       tags:
         - 'claude-pack-v*.*.*'
   permissions:
     contents: write
   jobs:
     release:
       runs-on: ubuntu-latest
   ```

5. **Build with reproducible epoch:**
   ```yaml
   - name: Compute reproducible epoch
     id: epoch
     run: echo "value=$(git log -1 --pretty=%ct ${{ github.sha }})" >> "$GITHUB_OUTPUT"
   - name: Build deterministic tarball
     env:
       SOURCE_DATE_EPOCH: ${{ steps.epoch.outputs.value }}
     run: |
       bash .claude/skills/claude-pack/install.sh --dev
       VERSION="${GITHUB_REF#refs/tags/claude-pack-v}"
       .claude/skills/.venv/bin/python -m pack \
         --manifest .claude/pack.manifest.yaml \
         --version "$VERSION" \
         --source-date-epoch env
   ```

6. **Verify SHA256 sidecar + upload:**
   ```yaml
   - name: Verify SHA256
     run: |
       cd dist
       sha256sum -c claude-pack-*.tar.gz.sha256
   - name: Upload to GitHub Release
     uses: softprops/action-gh-release@v2
     with:
       files: |
         dist/claude-pack-*.tar.gz
         dist/claude-pack-*.tar.gz.sha256
       generate_release_notes: true
   ```

### claude-pack-integration.yml

7. **Weekly cron:**
   ```yaml
   name: claude-pack Integration (live product-spec)
   on:
     schedule:
       - cron: '0 0 * * 0'
     workflow_dispatch:
   permissions:
     contents: read
   jobs:
     integration:
       runs-on: ubuntu-latest
       continue-on-error: true   # non-blocking
       steps:
         - actions/checkout@v4
         - actions/setup-python@v5 with python-version: '3.12'
         - bash .claude/skills/claude-pack/install.sh --dev
         - .claude/skills/.venv/bin/python -m pytest .claude/skills/claude-pack/scripts/tests/ -m integration -v
   ```

### Documentation updates

8. **CHANGELOG.md `[0.1.0]` add `### CI`:**
   - GitHub Actions matrix CI (Ubuntu/macOS/Windows × Python 3.11/3.12/3.13)
   - Release pipeline (tag → reproducible build → upload)
   - Weekly integration check (live product-spec)

9. **maintainers-guide.md** — pin in "Refreshing golden test" section:
   ```
   # Local: pytest -m integration (refresh golden)
   # CI dispatch: gh workflow run claude-pack-integration.yml
   ```

## Success Criteria

- [ ] `.github/workflows/claude-pack-ci.yml` exists, valid YAML (`yamllint` or `python -c "import yaml; yaml.safe_load(open('...'))"`)
- [ ] CI workflow has matrix `{os: 3, python: 3} = 9 jobs`
- [ ] Workflow triggers on `pull_request` with correct path filters
- [ ] First CI run on a test PR: all 9 matrix jobs green
- [ ] `claude-pack-release.yml` exists, triggers on tag pattern `claude-pack-v*.*.*`
- [ ] Release workflow uses `GITHUB_TOKEN` only (no other secrets)
- [ ] Release run with test tag `claude-pack-v0.0.1-test`: builds reproducible tarball, uploads to GH Release
- [ ] Release tarball SHA256 matches local Smoke 5 SHA256 (cross-machine determinism verified with `SOURCE_DATE_EPOCH` set explicitly)
- [ ] `claude-pack-integration.yml` exists with weekly cron + `workflow_dispatch`
- [ ] `continue-on-error: true` confirmed in integration workflow
- [ ] Workflow permissions blocks present and minimal (`contents: read` for CI/integration; `contents: write` for release)
- [ ] CHANGELOG `[0.1.0]` mentions CI
- [ ] maintainers-guide.md "Refreshing golden test" references `gh workflow run`
- [ ] CI runs in <5 min wall clock (verify via Actions UI after first run)

## Risk Assessment

- **R1: Windows runner cannot execute `bash install.sh` directly** → Use `if: runner.os == 'Windows'` to gate POSIX vs PowerShell steps. Tested.
- **R2: `actions/setup-python@v5` 3.13 unavailable at some moment** → Pin to known-stable patch versions (`'3.11.x'`, `'3.12.x'`, `'3.13.x'`); update as upstream stabilizes.
- **R3: `sha256sum` not available on macOS/Windows runners** → Use `shasum -a 256` (macOS) or PowerShell `Get-FileHash -Algorithm SHA256` (Windows); abstract via Python helper `python -m pack.checksum verify dist/*.sha256`.
- **R4: Release workflow accidentally fires on every tag push** → Path filter restricted to `claude-pack-v*.*.*`; only this prefix triggers.
- **R5: Cross-OS byte-identity gap** → Documented in CHANGELOG: "v0.1.0 guarantees same-OS determinism only; cross-OS byte-identity gated on v0.5.0 deferred work." Phase 7 CI verifies same-OS only.
- **R6: GH token expires for forks** → Documented: external contributors must run smoke locally; PR CI uses upstream token automatically when granted.
- **R7: Integration workflow false-positive when product-spec edits** → `continue-on-error: true` + reviewer treats as informational. Maintainers-guide explains refresh procedure.
- **R8: First Windows CI run reveals platform bugs not caught locally** → Phase 7 may iterate; budget 0.5h slack for fixes (within 3h estimate).

## Security Considerations

- Workflows store NO secrets in env. `GITHUB_TOKEN` is auto-provided by GitHub Actions only.
- Release workflow has `contents: write` scope only; not `actions: write` or `id-token: write`.
- `softprops/action-gh-release@v2` is pinned by major version; consider pinning to commit SHA for supply-chain hardening in v0.5.0.
- No artifacts uploaded contain `.env`, `.git/`, secrets (verified by Phase 5 test suite in CI).

## Next Steps

- After Phase 7 green: tag `claude-pack-v0.1.0` → CI release pipeline produces first official tarball.
- After first external recipient feedback: address Phase 5 R4 (recipient install UX) + update troubleshooting.md.
- Release ladder 0.5.0 gate: enable cross-OS byte-identity verification (requires uploading artifacts between matrix jobs + comparison job).
- 1.0.0 gate: 5+ shipped without bug reports + maintainers-guide ratified by next engineer.
