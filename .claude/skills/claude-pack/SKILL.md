---
name: cleanmatic:claude-pack
description: "Package opt-in .claude/ artifacts (skills, agents, hooks, rules) into a versioned deterministic tar.gz for distribution. Manifest-first selection; multiplatform recipient installer."
user-invocable: true
when_to_use: "When you need to bundle a curated subset of this repo's .claude/ tree for sharing with another developer or installing on another machine."
category: packaging
keywords: [packaging, distribution, tarball, manifest, claude, skill-distribution]
argument-hint: "[--manifest <path>] [--version <semver>] [--all|--skills <list>] [--dry-run]"
metadata:
  author: cleanmatic
  version: "0.1.0"
---

# cleanmatic:claude-pack

Developer-facing skill that bundles a curated subset of this repo's `.claude/` tree (skills, agents, hooks, rules, scripts, schemas) + optional top-level files (`README.md`, `CLAUDE.md`) into a **versioned, deterministic** `tar.gz`. Each bundle ships a `MANIFEST.json` (per-file SHA256), an `INSTALL.md`, and bundled multiplatform installers (`install.sh` POSIX + `install.ps1` Windows) so the recipient extracts once and runs.

## When to Use

- A developer wants to share a curated set of skills/agents/rules with a teammate.
- You need to seed a new repo's `.claude/` from an existing repo's working setup.
- You want a reproducible, content-hashed snapshot of `.claude/` for CI artifacts.
- You want to publish a versioned `claude-pack-{version}.tar.gz` to GitHub Releases.

## Flags

| Flag | Purpose |
|------|---------|
| (no flag) | Interactive menu → build manifest → preview → confirm → pack. |
| `--manifest <path>` | Manifest file (default `.claude/pack.manifest.yaml`). |
| `--all` | (v0.5+) Pack everything under `.claude/` not on the always-drop list. Not implemented in v0.1 — errors. |
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
├── claude-pack-{version}.tar.gz          # the bundle
└── claude-pack-{version}.tar.gz.sha256   # coreutils-format sidecar
```

Tarball internal layout:

```
claude-pack-{version}/
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
    B --> O[claude-pack-{v}.tar.gz]
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

All scripts emit JSON on `--json`. Analytical scripts exit 0; the `--strict` gate is the LLM's job. Determinism is the script's job: byte-identical tar.gz for the same input + `SOURCE_DATE_EPOCH`.

## What This Skill Does NOT Do

- **No remote upload.** Use `gh release upload` manually.
- **No GPG signing v1.** SHA256 sidecar only.
- **No recipient `claude-unpack` companion.** `tar -xzf` + bundled installer is the contract.
- **No merge-resolver.** Recipient `install.sh` skips existing skills by default; `FORCE_OVERWRITE=1` opt-in.
- **No multi-project packing.** One `.claude/` root per bundle.
- **No zip / tar.zst.** Tar.gz only in v1.
