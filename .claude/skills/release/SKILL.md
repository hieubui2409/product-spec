---
name: cleanmatic:release
description: "Cut a versioned release of the product-spec bundle: pack opt-in .claude/ artifacts into a deterministic tar.gz AND manage the root CHANGELOG.md release lifecycle (lock [Unreleased] → [X.Y.Z], bump manifest, hand the owner the tag push that fires release CI). Manifest-first selection; multiplatform recipient installer."
user-invocable: true
when_to_use: "When you need to bundle a curated subset of this repo's .claude/ tree for sharing/installing, OR cut a versioned release (lock the changelog, bump the version, print the owner-owned tag-push command)."
category: release
keywords: [release, packaging, distribution, tarball, manifest, changelog, versioning, claude, skill-distribution]
argument-hint: "[--manifest <path>] [--version <semver>] [--skills <list>] [--dry-run] | release.py [--release X.Y.Z | --bump major|minor|patch] [--apply] [--push]"
metadata:
  author: cleanmatic
  version: "1.1.1"
---

# cleanmatic:release

Developer-facing skill with two halves of one job — **cutting a release** of the `product-spec` bundle:

1. **Pack** — bundle a curated subset of this repo's `.claude/` tree (skills, agents, hooks, rules, scripts, schemas) + optional top-level files (`README.md`, `CLAUDE.md`) into a **versioned, deterministic** `tar.gz`. Each bundle ships a `MANIFEST.json` (per-file SHA256), an `INSTALL.md`, and bundled multiplatform installers (`install.sh` POSIX + `install.ps1` Windows) so the recipient extracts once and runs.
2. **Release lifecycle** (`scripts/release.py`) — manage the root `CHANGELOG.md` Keep-a-Changelog flow: lock `## [Unreleased]` → `## [X.Y.Z] — <date>`, bump `pack.manifest.yaml`, and hand the owner the exact `git tag product-spec-vX.Y.Z && git push` that fires the release CI. The GitHub Release body is the just-locked CHANGELOG section (`release.py --extract`). Dry-run by default; the tag push is **owner-owned**.

> **Renamed from `cleanmatic:claude-pack` (≤ 0.3.0).** The bundle artifact is now `product-spec-{version}.tar.gz` and the release tag is `product-spec-v*`.

> 📘 **Developer usage guide:** [`GUIDE-VI.md`](./GUIDE-VI.md) (Tiếng Việt) / [`GUIDE-EN.md`](./GUIDE-EN.md) (English) —
> every use case as a sample conversation, covering both the natural-language way (preferred) and the CLI-equivalent
> (`python -m pack`). Read this for a task-oriented walkthrough; this `SKILL.md` is the operating contract.

## When to Use

- A developer wants to share a curated set of skills/agents/rules with a teammate.
- You need to seed a new repo's `.claude/` from an existing repo's working setup.
- You want a reproducible, content-hashed snapshot of `.claude/` for CI artifacts.
- You want to **cut a release**: lock the changelog, bump the version, and publish a versioned `product-spec-{version}.tar.gz` to GitHub Releases.

## Flags

| Flag | Purpose |
|------|---------|
| (no flag) | Interactive menu → build manifest → preview → confirm → pack. |
| `--manifest <path>` | Manifest file (default `.claude/pack.manifest.yaml`). |
| `--skills <list>` | Comma-separated skill slugs (override manifest). |
| `--agents <list>` | Comma-separated agent slugs (override manifest). |
| `--hooks <list>` | Comma-separated hook filenames (override manifest). |
| `--rules <list>` | Comma-separated rule filenames (override manifest). |
| `--extra <paths>` | Extra repo-relative paths (no `..`, no absolute). |
| `--version <semver>` | Override `manifest.version` for ad-hoc builds. |
| `--bundle-name <name>` | Override output filename stem. |
| `--out <dir>` | Output dir (default `dist/`). |
| `--dry-run` | Print would-be file list + total size; no tarball. |
| `--dry-run --compute-sha` | Add would-be SHA256 (opt-in; avoids double-pass). |
| `--include-settings` | Include `.claude/settings.json` (opt-in). |
| `--include-ck-config` | Include `.claude/.ck.json` (opt-in). |
| `--include-scripts` / `--include-schemas` | Include `.claude/scripts/` or `schemas/` (CK-framework internals; opt-in, off by default). |
| `--include-shared <list>` | Opt-in `skills/_shared/<name>` (warn-only otherwise). |
| `--max-size <bytes>` | Reject if compressed tar.gz > limit (default 100MB). |
| `--source-date-epoch <int\|env>` | Override mtime root (default 0 = fully deterministic). |
| `--strict` | Treat un-included `_shared/` references as errors (exit 2). |
| `--json` | Emit JSON status to stdout (machine-parseable). |

Full descriptions: `references/flag-reference.md`.

## No-Flag Menu

When invoked without a flag, the skill runs `python -m build_manifest --discover`, presents an AskUserQuestion-driven walk through skills/agents/rules/extra/top_level/follow_shared, then writes `.claude/pack.manifest.yaml` and previews the build. Full interactive flow + question bank: `references/workflow-pack.md`.

## Output Contract

```
dist/
├── product-spec-{version}.tar.gz          # the bundle
└── product-spec-{version}.tar.gz.sha256   # coreutils-format sidecar
```

Tarball internal layout:

```
product-spec-{version}/
├── MANIFEST.json     # schema_version "1.0", per-file SHA256
├── INSTALL.md        # rendered from INSTALL.md.template
├── install.sh        # POSIX recipient installer
├── install.ps1       # Windows recipient installer
└── .claude/          # selected subtree
```

Determinism: PAX format, sorted walk (file-granular), `mtime=0`, `uid=gid=0`, gzip header `mtime=0`. Same inputs → byte-identical tar.gz.

## Workflow Map

```mermaid
flowchart LR
    M[pack.manifest.yaml] --> L[manifest_loader]
    CLI[CLI flags] --> L
    L --> S[safety_check]
    S --> W[sorted walker]
    W --> B[tarball builder]
    T[templates] --> B
    B --> O[product-spec-{v}.tar.gz]
    B --> H[.sha256 sidecar]
```

ASCII fallback:

```
manifest + CLI --> loader --> safety_check --> walker --> builder --> tar.gz + .sha256
                                  ^                          ^
                                  |                          |
                               always-drop                templates
```

## Load-on-Demand References

| When | Reference |
|------|-----------|
| `--manifest`, manifest authoring | `references/manifest-spec.md` |
| Any CLI flag | `references/flag-reference.md` |
| Safety filter, always-drop list | `references/safety-rules.md` |
| No-flag / interactive flow | `references/workflow-pack.md` |
| Error message lookup | `references/error-catalog.md` |
| Recipient install failures | `references/troubleshooting.md` |
| Skill internals, extension recipes | `references/maintainers-guide.md` |

Load only the reference relevant to the active flag. Don't pre-load.

## Resources

```
scripts/
├── pack/                  # modularized pack builder (cli, tarball, manifest_io, templates)
├── release.py             # root-CHANGELOG release lifecycle (extract/release/bump/apply/push)
├── safety_check.py        # always-drop + opt-in catalog + shared-ref detection
├── manifest_loader.py     # YAML load · CLI merge · validate · apply defaults
└── build_manifest.py      # discover · list-questions · write manifest

assets/templates/
├── manifest.example.yaml  # copyable manifest seed (annotated)
├── INSTALL.md.template    # recipient docs skeleton (token-driven)
├── install.sh.template    # POSIX recipient installer (version-aware)
└── install.ps1.template   # Windows recipient installer (version-aware)
```

## Operating Principles

Single source-of-truth = root `CLAUDE.md` "Claude Pack — LLM Operating Guide" section. The five principles (Manifest is truth · DRY · Script vs LLM split · Never silent reverse · Never overwrite recipient state) are documented there. Cross-reference, do not duplicate.

## Script CLI Contract

Run via the per-skill venv created by `install.sh`:

```bash
.claude/skills/.venv/bin/python3 -m pack \
  --root <repo-root> [flags]
```

> ⚙️ **Venv bootstrap (first run):** before invoking `python -m pack` (or any script), check the shared interpreter
> exists (`.claude/skills/.venv/bin/python3` on POSIX, `.claude\skills\.venv\Scripts\python.exe` on Windows). If it is
> **missing**, do NOT silently fail or fall back to system Python — pause and ask the user via **AskUserQuestion** to
> confirm running the installer (`./install.sh` POSIX / `install.ps1` Windows, both idempotent). Run it only on approval,
> then retry.

The pack builder (`python -m pack`) emits JSON on `--json`. The other scripts (`manifest_loader.py`, `safety_check.py`, `build_manifest.py`) emit JSON to stdout unconditionally — they have no `--json` flag. Analytical scripts exit 0; the `--strict` gate is the LLM's job. Determinism is the script's job: byte-identical tar.gz for the same input + `SOURCE_DATE_EPOCH`.

## Release Lifecycle (`scripts/release.py`)

Cutting a release is two artifacts moving together: the **version** (`pack.manifest.yaml`) and the **changelog** (root `CHANGELOG.md`). `release.py` owns that transform deterministically — it never derives content from git, so the committed `CHANGELOG.md` is reproducible.

**Interview first (mandatory).** Before any `--apply`, confirm with the PO via AskUserQuestion: (1) the resulting version string (explicit `--release X.Y.Z` or computed `--bump`), (2) stable vs `--pre-release`, (3) read back the `[Unreleased]` body that will be locked (refuse if thin/empty), (4) push now or hand off — **the tag push is owner-owned**.

```bash
# Preview a cut (writes nothing):
.claude/skills/.venv/bin/python3 .claude/skills/release/scripts/release.py --bump minor

# Apply locally, then hand the printed tag command to the owner:
.claude/skills/.venv/bin/python3 .claude/skills/release/scripts/release.py --release 2.0.0 --apply

# Inspect what CI will publish as the GitHub Release body:
.claude/skills/.venv/bin/python3 .claude/skills/release/scripts/release.py --extract 2.0.0
```

| Flag | Effect |
|------|--------|
| `--extract X.Y.Z` | Print a version's CHANGELOG section body (the CI release body). Read-only. |
| `--release X.Y.Z` | Cut at an explicit version. |
| `--bump major\|minor\|patch` | Cut at the next version computed from the manifest. |
| `--pre-release LABEL` | Append a pre-release label (`rc.1` → `X.Y.Z-rc.1`). |
| `--date YYYY-MM-DD` | Override the release date (default: today). |
| `--apply` | Write changes (default: dry-run preview). |
| `--push` | Owner opt-in: also create + push the `product-spec-vX.Y.Z` tag (requires `--apply`). |

A cut locks `## [Unreleased]` → `## [X.Y.Z] — <date>`, opens a fresh empty `[Unreleased]`, bumps `pack.manifest.yaml`, and prints the exact `git tag product-spec-vX.Y.Z && git push` (or runs it with `--push`). It **refuses** an empty `[Unreleased]` or an already-locked version. Per-skill `SKILL.md` versions + their CHANGELOGs are bumped by hand during dev (the A4 gate enforces each skill version == its CHANGELOG top); `release.py` only moves the bundle version + root changelog. Pushing the tag fires `.github/workflows/release.yml` (build → SHA256 → GitHub Release whose body is the locked section via `--extract`).

## What This Skill Does NOT Do

- **No remote upload.** Use `gh release upload` manually.
- **No GPG signing v1.** SHA256 sidecar only.
- **No recipient `claude-unpack` companion.** `tar -xzf` + bundled installer is the contract.
- **No merge-resolver.** Recipient `install.sh` skips existing skills by default; `FORCE_OVERWRITE=1` opt-in.
- **No multi-project packing.** One `.claude/` root per bundle.
- **No zip / tar.zst.** Tar.gz only in v1.
