# cleanmatic:claude-pack

Package opt-in `.claude/` artifacts (skills, agents, hooks, rules) into a versioned, deterministic `tar.gz` for distribution.

## Install

```bash
./install.sh             # runtime only (pyyaml)
./install.sh --dev       # runtime + dev (pytest + pytest-cov)
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Dev
```

Requires Python 3.11+.

## Quickstart

**LLM-driven (recommended):**

```
/cleanmatic:claude-pack
```

The skill walks you through manifest authoring (interactive) → preview → confirm → pack.

**Manual CLI:**

```bash
# Build from existing manifest
.claude/skills/.venv/bin/python3 -m pack \
  --manifest .claude/pack.manifest.yaml

# Override version for ad-hoc build
.claude/skills/.venv/bin/python3 -m pack \
  --manifest .claude/pack.manifest.yaml --version 0.2.0-rc1

# Dry-run (file list + size, no tarball)
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run

# Build with would-be SHA256
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run --compute-sha
```

Output lands in `dist/claude-pack-{version}.tar.gz` + `.sha256` sidecar.

## Layout

```
.claude/skills/claude-pack/
├── SKILL.md          # operating contract (LLM reads this)
├── scripts/          # pack/ subpackage + safety_check + manifest_loader + build_manifest
├── references/       # load-on-demand: manifest-spec, flag-reference, safety-rules, ...
└── assets/templates/ # manifest.example.yaml + INSTALL.md/install.sh/install.ps1 templates
```

Usage guide (task-oriented, all use cases as sample conversations): **[`GUIDE-VI.md`](./GUIDE-VI.md) / [`GUIDE-EN.md`](./GUIDE-EN.md)**.
Full architecture: `references/maintainers-guide.md` (added in Phase 6).
Reference index: see `SKILL.md` "Load-on-Demand References" table.

## FAQ

**Why is `dist/` gitignored?**
Tarballs are reproducible build artifacts, not source. Commit them only on a tagged release (the CI release pipeline uploads them to GitHub Releases). Same source + manifest always rebuilds the identical bytes, so there's nothing to gain from versioning them.

**Why must I pass (or set) a real `version`?**
The bundle version is decoupled from the skill's own version — it labels the *distribution*, not the code. We refuse the `0.0.0-dev` placeholder for real builds so a release never ships unversioned. Pass `--version X.Y.Z` for ad-hoc builds or `--allow-dev-version` for throwaway tests.

**Why is `_shared/` warn-only instead of auto-included?**
Skill `SKILL.md` files often mention `_shared/<name>` inside fenced code examples that aren't real dependencies. Auto-including them would bloat bundles with false positives. We strip fenced blocks, then warn — you opt in explicitly with `--include-shared <name>`.

**How do I bundle for Windows recipients?**
Every bundle ships both `install.sh` (POSIX) and `install.ps1` (Windows). The recipient runs `powershell -ExecutionPolicy Bypass -File .\install.ps1`. The installer is version-aware on both platforms (detects STALE/NEWER/OK SAME per skill).

**Is the build deterministic?**
Yes — PAX format, file-granular sorted walk, `mtime=0`, `uid/gid=0`, gzip header `mtime=0`. Two builds of the same source produce byte-identical tarballs (verified by the test suite). For source-date reproducibility in CI, pass `--source-date-epoch env` to honor `SOURCE_DATE_EPOCH`.
