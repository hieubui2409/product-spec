---
phase: 1
title: "Scaffold and Templates"
status: pending
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Scaffold and Templates

## Overview

Create the skill directory structure, write `SKILL.md` (operating contract), `install.sh` + `install.ps1` (venv setup, multiplatform), `README.md` (quickstart + FAQ placeholder), seeded `CHANGELOG.md`, all reference stubs, and all asset templates with locked skeletons. No executable logic yet — this is the documentation + scaffolding layer subsequent phases reference.

## Context Links

- Plan overview: `./plan.md` — read first for locked decisions + API contracts + Cross-Phase Mutations table
- Convention precedent: `.claude/skills/product-spec/SKILL.md`, `.claude/skills/product-spec/install.sh:1-92`
- Researcher B report (frontmatter shape, install.sh pattern): `plans/reports/researcher-260529-0343-claude-pack-skill-convention-audit-report.md` Q1-Q3, Q8

## Requirements

**Functional:**
- Skill discoverable via `/cleanmatic:claude-pack` (frontmatter `user-invocable: true`)
- `install.sh` creates shared venv `.claude/skills/.venv` and installs `pyyaml>=6.0,<7` from `scripts/requirements.txt` (mirror product-spec)
- `install.sh --dev` opt-in installs `pytest>=7,<9 + pytest-cov` from `scripts/requirements-dev.txt`
- `install.ps1` provides equivalent Windows behavior
- `SKILL.md` documents: 18-flag CLI, no-flag interactive menu, output contract, workflow map, load-on-demand references
- 7 reference files (4 stubs + 3 new docs) referenced from SKILL.md
- All asset templates valid (YAML, markdown, sh + ps1 syntax-valid)
- `CHANGELOG.md` seeded with v0.1.0 unreleased entry
- `README.md` has install + quickstart + FAQ section header (FAQ filled Phase 6)
- `metadata.version: "0.1.0"` (NOT 1.0.0; aligns with Release Gates ladder)

**Non-functional:**
- `SKILL.md` 220-line ceiling (enforced); compile check via `head -c $((220*80)) SKILL.md` byte budget
- All reference stubs ≥10 lines (purpose paragraph + section headings)
- Templates use `{{TOKEN}}` for substitution; unknown tokens raise `TemplateError` at build (Phase 2 enforces)
- POSIX shell `install.sh` works on macOS + Linux; no bash-isms beyond `set -euo pipefail`
- `install.ps1` uses `-ExecutionPolicy Bypass` scoped to script run only; no global ExecutionPolicy mutation

## Architecture

```
.claude/skills/claude-pack/
├── SKILL.md                  ← operating contract
├── README.md                 ← quickstart + FAQ section
├── CHANGELOG.md              ← keepachangelog seed
├── install.sh                ← venv + pyyaml; --dev opt-in
├── install.ps1               ← Windows equivalent
├── scripts/
│   ├── requirements.txt          ← pyyaml>=6.0,<7
│   └── requirements-dev.txt      ← pytest>=7,<9 + pytest-cov (Phase 5 creates)
├── references/                   ← 4 stubs + 3 new (this phase creates stubs only)
│   ├── manifest-spec.md          ← stub (Phase 3 fills)
│   ├── flag-reference.md         ← stub (Phase 2 fills)
│   ├── safety-rules.md           ← stub (Phase 3 fills)
│   └── workflow-pack.md          ← stub (Phase 4 fills)
└── assets/
    └── templates/
        ├── manifest.example.yaml      ← full annotated example
        ├── INSTALL.md.template        ← skeleton LOCKED (see Step 9)
        ├── install.sh.template        ← POSIX recipient installer
        └── install.ps1.template       ← Windows recipient installer
```

`requirements-dev.txt`, `references/error-catalog.md`, `references/troubleshooting.md`, `references/maintainers-guide.md` are created in later phases (per Cross-Phase Mutations table).

## Related Code Files

**Create (this phase):**
- `.claude/skills/claude-pack/SKILL.md`
- `.claude/skills/claude-pack/README.md`
- `.claude/skills/claude-pack/CHANGELOG.md`
- `.claude/skills/claude-pack/install.sh`
- `.claude/skills/claude-pack/install.ps1`
- `.claude/skills/claude-pack/scripts/requirements.txt`
- `.claude/skills/claude-pack/references/manifest-spec.md` (skeleton)
- `.claude/skills/claude-pack/references/flag-reference.md` (skeleton)
- `.claude/skills/claude-pack/references/safety-rules.md` (skeleton)
- `.claude/skills/claude-pack/references/workflow-pack.md` (skeleton)
- `.claude/skills/claude-pack/assets/templates/manifest.example.yaml`
- `.claude/skills/claude-pack/assets/templates/INSTALL.md.template`
- `.claude/skills/claude-pack/assets/templates/install.sh.template`
- `.claude/skills/claude-pack/assets/templates/install.ps1.template`

## Implementation Steps

1. **Create directory tree** — `mkdir -p .claude/skills/claude-pack/{scripts,references,assets/templates}` (no `eval/` yet — Phase 5).

2. **Write `SKILL.md` frontmatter** — exact copy of product-spec shape (`.claude/skills/product-spec/SKILL.md:1-12`) with claude-pack-specific values:
   ```yaml
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
     version: "0.1.0"   # ← starts at 0.1.0 per Release Gates ladder
   ---
   ```

3. **Write `SKILL.md` body sections** (5 Operating Principles MUST match root CLAUDE.md exactly — see Phase 6):
   - Title + 1-line summary
   - When to Use (3-5 bullets)
   - Flags (table with all 18 flag NAMES; full descriptions filled by Phase 2)
   - No-Flag Menu (LLM walks AskUserQuestion via Phase 4 question bank)
   - Output Contract (versioned tar dir + dist/)
   - Workflow Map (Mermaid data-flow diagram: manifest → loader → safety → walker → builder → sidecar + ASCII fallback)
   - Load-on-Demand References (table mapping flag groups to 7 reference files)
   - Resources (scripts/, assets/, eval/)
   - **Operating Principles (5):** identical wording to root CLAUDE.md "Claude Pack — LLM Operating Guide" section. See Phase 6 for exact text. Single source-of-truth = root CLAUDE.md; this is a cross-reference.

4. **Write `install.sh`** (~50 lines):
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   # Detect --dev flag (opt-in pytest install)
   DEV=0
   for arg in "$@"; do [[ "$arg" == "--dev" ]] && DEV=1; done
   # venv setup, pip install pyyaml (always), pytest (if --dev)
   ```
   Multi-step: detect Python 3.11+, create venv at `.claude/skills/.venv` if absent, upgrade pip, install requirements.txt, conditionally install requirements-dev.txt. No vendor shim. No pytest smoke test (Phase 5 adds optional).

5. **Write `install.ps1`** — PowerShell equivalent. Param: `[switch]$Dev`. Same flow. Use `python3 -m venv` (or `py -3.11 -m venv` if `py` launcher present). No global `ExecutionPolicy` mutation.

6. **Write `scripts/requirements.txt`** — exactly:
   ```
   pyyaml>=6.0,<7
   ```
   Single line. No comments. (Phase 5 creates separate `requirements-dev.txt`.)

7. **Write `README.md`** (~80 lines): 5 sections
   - Title + 1-line purpose
   - Install: `./install.sh` (or `./install.sh --dev` for dev)
   - Quickstart: `/cleanmatic:claude-pack` (LLM-driven) or `python -m pack --manifest .claude/pack.manifest.yaml`
   - Layout summary (link to SKILL.md for detail)
   - FAQ (Phase 6 fills; for now: section header + `<!-- Phase 6 fills -->`)

8. **Write `CHANGELOG.md`** — keepachangelog format, seeded:
   ```markdown
   # Changelog

   All notable changes to `cleanmatic:claude-pack` are documented here.
   Format: keepachangelog.com. Versioning: semver.

   ## [Unreleased]

   ### Added
   - Initial scaffold (Phase 1).

   ## [0.1.0] — TBD (dogfood release)
   ```

9. **Write 4 reference stubs** — each ≥10 lines: frontmatter (`# {Title}`), 2-sentence purpose paragraph, section headings later phase will fill, explicit `<!-- STUB: filled in Phase N -->` comment.

10. **Write `manifest.example.yaml`** — full annotated example covering all categories. YAML inline comments document each field. Example:
    ```yaml
    # cleanmatic:claude-pack manifest — source-of-truth for what gets packed.
    # See references/manifest-spec.md for full schema.
    schema_version: "1.0"
    version: "0.1.0"             # bundle version (semver); CLI --version overrides
    bundle_name: "claude-pack"   # output filename stem
    skills:
      - product-spec             # skill slug under .claude/skills/
    agents:
      - planner                  # auto-appends .md if missing
    hooks: []
    rules:
      - primary-workflow.md
    extra: []                    # extra paths (repo-relative; NO absolute, NO ..)
    top_level:
      include_readme: false
      include_claudemd: false
      include_settings: false    # opt-in via --include-settings
      include_ck_config: false   # opt-in via --include-ck-config
    follow_shared: false         # warn-only; opt-in via --include-shared
    ```

11. **Write `INSTALL.md.template`** — SKELETON LOCKED (validate F6.4):
    ```markdown
    # Claude Pack v{{VERSION}}

    Built: {{BUILT_AT}}
    Source commit: {{SOURCE_COMMIT}}

    ## Verify
    sha256sum -c claude-pack-{{VERSION}}.tar.gz.sha256

    ## Extract
    tar -xzf claude-pack-{{VERSION}}.tar.gz

    ## Install (macOS/Linux)
    cd claude-pack-{{VERSION}}/ && bash install.sh

    ## Install (Windows)
    cd claude-pack-{{VERSION}}\ ; .\install.ps1

    ## What gets installed
    {{FILE_COUNT}} files, {{TOTAL_SIZE}} into your repo's `.claude/` directory.
    See `MANIFEST.json` for the full list.

    ## Troubleshooting
    See `.claude/skills/claude-pack/references/troubleshooting.md` after installation.

    ## Uninstall
    rm -rf .claude/skills/<installed-skill>/ (or restore from your backup)
    ```
    Each section ≥1 line. Token list: `{{VERSION}}`, `{{BUILT_AT}}`, `{{SOURCE_COMMIT}}`, `{{FILE_COUNT}}`, `{{TOTAL_SIZE}}`. Unknown tokens → Phase 2 raises `TemplateError`.

12. **Write `install.sh.template`** — POSIX recipient installer with version-awareness (R3.Q9). ~80 lines:
    - Read `MANIFEST.json` for bundle version
    - For each existing `.claude/skills/<slug>/SKILL.md`, parse `metadata.version` frontmatter
    - Compare: `[STALE]` (existing < bundled) → suggest `FORCE_OVERWRITE=1`; `[OK SAME]` → skip; `[NEWER]` (existing > bundled) → refuse downgrade
    - Skip-existing default; `FORCE_OVERWRITE=1` env var triggers timestamped backup + overwrite
    - Run per-skill `install.sh` hooks after extract (if exists)
    - Final summary: counts of `[+]`, `[SKIP]`, `[OVERWRITE]`, `[STALE]`, `[NEWER]`

13. **Write `install.ps1.template`** — PowerShell equivalent. Same version detection logic. `-ForceOverwrite` switch. `-NoExecute` switch to skip per-skill install hooks.

## Success Criteria

- [ ] `ls .claude/skills/claude-pack/` shows all 5 subdirs (`scripts`, `references`, `assets`) + 5 root files (SKILL.md, README.md, CHANGELOG.md, install.sh, install.ps1)
- [ ] `wc -l .claude/skills/claude-pack/SKILL.md` ≤ 220
- [ ] `./.claude/skills/claude-pack/install.sh` exits 0 on a clean repo, creates `.claude/skills/.venv/bin/python3`, installs `pyyaml`; `.venv/bin/python -c "import yaml"` succeeds
- [ ] `./.claude/skills/claude-pack/install.sh --dev` additionally installs pytest (verified via `.venv/bin/python -c "import pytest"`)
- [ ] `pwsh -NoProfile -File .claude/skills/claude-pack/install.ps1 -WhatIf` syntax-checks (skip on non-Windows: `command -v pwsh && pwsh -Command "Get-Content install.ps1 | Out-String | Invoke-Expression -ErrorAction Stop"` or visual review against template)
- [ ] `SKILL.md` frontmatter passes `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" SKILL.md` (round-trip)
- [ ] `SKILL.md` body has all 9 sections (verify by grep `^## ` count == 9)
- [ ] `SKILL.md` `metadata.version` == `"0.1.0"` (NOT 1.0.0)
- [ ] `manifest.example.yaml` parses with `yaml.safe_load`
- [ ] `install.sh.template` syntax-checks with `bash -n`
- [ ] `install.ps1.template` does not contain bash-isms (grep `set -euo` returns nothing; grep `\$(.*)` returns nothing)
- [ ] 4 reference stubs each ≥10 lines (`wc -l references/*.md | tail -1` ≥ 40)
- [ ] All 4 reference stubs marked `STUB: filled in Phase N` (grep `STUB:` returns 4 lines)
- [ ] `INSTALL.md.template` has all 7 sections from Step 11 skeleton (grep `^## ` returns 7)
- [ ] `CHANGELOG.md` parses (markdown) and has `[Unreleased]` + `[0.1.0]` sections
- [ ] `python -m py_compile` not applicable (no .py files this phase); skip

## Risk Assessment

- **R1: Frontmatter drift from product-spec convention** → Mitigation: pinned exact frontmatter at `.claude/skills/product-spec/SKILL.md:1-12` verified at plan-time.
- **R2: install.sh failure on macOS (default sh != bash)** → Mitigation: shebang `#!/usr/bin/env bash`; CI matrix in Phase 7 tests macOS.
- **R3: PowerShell template invalid syntax** → Mitigation: lint with `pwsh -Command` if available; Phase 7 CI runs on Windows runner.
- **R4: SKILL.md operating principles drift from CLAUDE.md** → Mitigation: Phase 6 is single source-of-truth; SKILL.md cross-references it. No duplication.
- **R5: install.ps1 version-detection regex fragile** → Mitigation: parse YAML frontmatter via PowerShell `ConvertFrom-Yaml` (PowerShell-Yaml module) OR fallback to `Get-Content | Select-String` for `metadata: version:` line. Test in Phase 7.

## Security Considerations

- `install.sh.template` + `install.ps1.template` (recipient-facing): pure local file copy. No `curl | bash`. No remote code fetch.
- `install.ps1.template` uses `-ExecutionPolicy Bypass` scoped to script process only (`powershell.exe -ExecutionPolicy Bypass -File install.ps1`). Never `Set-ExecutionPolicy` globally.
- No secrets in templates or example manifest. `manifest.example.yaml` uses placeholder values only.
- `CHANGELOG.md` `[0.1.0]` entry will list actual changes when Phase 6 ships; for now, marker only.

## Next Steps

Phase 2 (Pack Builder Core) consumes:
- `assets/templates/manifest.example.yaml` (schema reference)
- `assets/templates/INSTALL.md.template`, `install.sh.template`, `install.ps1.template` (embedded in tar root by `pack.py` via Phase 2 template renderer)
- `references/safety-rules.md` (Phase 3 fills; Phase 2 imports `safety_check.is_dropped` per API Contracts)
- `references/flag-reference.md` stub (Phase 2 fills full table)
