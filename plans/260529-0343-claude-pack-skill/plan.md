---
title: 'cleanmatic:claude-pack skill'
description: >-
  Python skill that bundles opt-in .claude/ artifacts (skills, agents, hooks,
  rules, scripts, schemas) into a versioned, deterministic tar.gz with
  MANIFEST.json + SHA256 sidecar + bundled multiplatform installer.
status: completed
priority: P2
branch: master
tags:
  - skill
  - packaging
  - distribution
  - cleanmatic
blockedBy: []
blocks: []
created: '2026-05-29T03:43:00.000Z'
createdBy: 'ck:plan'
source: skill
---

# cleanmatic:claude-pack skill

## Overview

Build `cleanmatic:claude-pack` — a developer-facing skill that packages a curated subset of the repo's `.claude/` tree (skills, agents, hooks, rules, scripts, schemas) + optional top-level files (`README.md`, `CLAUDE.md`) into a **versioned, deterministic** `tar.gz` bundle. The bundle includes a manifest (per-file SHA256), an `INSTALL.md`, and a multiplatform bundled installer (`install.sh` POSIX + `install.ps1` Windows) so recipients can extract once and run.

**Selection model:** Manifest-first (`.claude/pack.manifest.yaml`) is source-of-truth; CLI flags override per-build; interactive `AskUserQuestion` mode regenerates the manifest. Strict safety filter is non-negotiable: secrets, runtime caches, and session state are **always** dropped.

**Authoritative inputs (sticky decisions):**
- PO interview rounds 1-3 (12 design decisions locked)
- Researcher A — Python tarball best practices: `plans/reports/from-researcher-to-planner-260529-0343-claude-pack-python-tarball-best-practices-report.md`
- Researcher B — skill convention audit: `plans/reports/researcher-260529-0343-claude-pack-skill-convention-audit-report.md`
- Red-team review: `plans/reports/from-code-reviewer-to-planner-260529-0354-claude-pack-red-team-review-report.md` (3 CRITICAL + 14 HIGH applied)
- Validate review: `plans/reports/from-planner-to-pm-260529-0405-claude-pack-validation-critical-questions-report.md` (3 BLOCKING + 22 HIGH applied)
- Existing skill anatomy in `.claude/skills/product-spec/` (convention precedent)

**Build target:** `.claude/skills/claude-pack/`. Python via shared `.claude/skills/.venv` (pyyaml only at runtime; pytest dev-only). Tarball output: `dist/claude-pack-{bundle-version}.tar.gz` + `.sha256` sidecar.

## Locked Decisions (PO interview rounds 1-3, 12 decisions)

| Decision | Value | Source |
|----------|-------|--------|
| Skill name | `cleanmatic:claude-pack` | R1.Q2 |
| Approach | Full Python skill (modularized `pack/` subpackage) | R1.Q1 + R3.Q4 |
| Selection | Manifest-first + CLI override + interactive fallback | R1.Q3 |
| Default ship | `.claude/scripts/`, `.claude/schemas/` | R1.Q4 |
| Opt-in (flagged) | `.claude/settings.json`, `.claude/.ck.json` | R1.Q4 |
| Tar layout | Versioned root dir `claude-pack-{version}/` + MANIFEST.json + INSTALL.md + bundled installers + `.claude/` subtree | R2.Q1 |
| Tar filename | `claude-pack-{version}.tar.gz` | R2.Q1 |
| Deps (`_shared/`) | **Warn-only**, opt-in via `--include-shared <list>` (NOT auto-include) | R2.Q3 (overrides earlier draft) |
| Installer | Bundled `install.sh` (POSIX) + `install.ps1` (Windows), version-aware (detects stale/newer/same on recipient side) | R2.Q3 + R3.Q9 |
| Version source | `pack.manifest.yaml:version` (CLI `--version` overrides) | R2.Q4 |
| Format v1 | `tar.gz` only | R1.Q5 |
| Output dir | `dist/` at repo root (gitignored) | R1.Q5 |
| Eval target | Synthetic fixture (unit) + live `cleanmatic:product-spec` (integration, `-m integration`, non-blocking CI) | R3.Q3 |
| Determinism | PAX format + sorted walk (file-granular) + mtime=0 default + uid/gid=0 + gzip mtime=0; opt-in `--source-date-epoch` for env-honor | R3.Q1 |
| Platforms | **Cross-platform** (POSIX + Windows) using `os.replace`; CI matrix includes Windows runner | R3.Q2 |
| Phase 4 (interactive) | Kept in v1 (~4h cost accepted) | R1.Q1 + R3.Q1 |
| Phase 7 (CI) | Added: GitHub Actions matrix + release pipeline | R3.Q2 |
| pack.py structure | Modularized `pack/` subpackage (cli, tarball, manifest_io, templates) — honors 200-line rule | R3.Q4 |
| Pytest install | Dev-only via `--dev` flag (recipients don't get pytest); same pattern back-propagated to product-spec install.sh | R3.Q10 |
| Documentation deliverables | `references/maintainers-guide.md`, `references/error-catalog.md`, `references/troubleshooting.md`, FAQ section in `README.md`, `CHANGELOG.md` | R3.Q11 |
| Edge cases (all enabled) | Empty selection → exit 1; `--max-size` flag (default 100MB); reject symlinks with WARN; tmp cleanup on startup | R3.Q12 |
| Release ladder | `0.1.0` (dogfood) → `0.5.0` (beta, multi-OS) → `1.0.0` (GA) | R3.Q4 |
| SKILL.md `metadata.version` | Starts at `0.1.0` (NOT 1.0.0) — aligns with release ladder | Validate F11.2 |

## Open Questions Resolved Pre-Plan

- **Q1: Does product-spec reference `_shared/`?** → No (verified via grep excluding vendored mermaid.min.js). With warn-only `_shared/` policy (R2.Q3), v1 eval ships without auto-resolver.
- **Q2: Where does `pack.manifest.yaml` live?** → `.claude/pack.manifest.yaml` (scope to `.claude/` subtree).
- **Q3: MANIFEST.json schema_version?** → `"1.0"` (forward-compat). Migration policy: see `## Schema Migration Policy` below.
- **Q4: `--dry-run` output?** → Fast path: file list + total size. `--dry-run --compute-sha` opt-in for would-be SHA256 (avoids double-pass cost — red-team F16.1).
- **Q5: Golden test strategy?** → Synthetic minimal fixture for blocking determinism unit test; live product-spec as integration test marker, non-blocking.

## API Contracts (LOCKED — plan-amend required for change)

This section is the cross-phase coordination point per validate F2.2. Phases 2, 3, 4 implement these signatures verbatim. Any change requires a plan amendment commit before either side can ship.

```python
# safety_check.py (Phase 3)
ALWAYS_DROP_EXACT: frozenset[str]      # see safety-rules.md for full list
ALWAYS_DROP_DIRS: frozenset[str]
ALWAYS_DROP_PATTERNS: tuple[str, ...]  # fnmatch glob patterns
OPT_IN_PATHS: dict[str, str]           # path → label

class SafetyError(Exception): ...

def is_dropped(path: str) -> tuple[bool, str | None]:
    """Return (drop?, rule-id) for a candidate arcname."""

def is_optional(path: str) -> tuple[bool, str | None]:
    """Return (opt-in?, label) for paths that need CLI flags to include."""

def find_shared_refs(skill_dirs: list[Path]) -> list[tuple[str, str]]:
    """Grep SKILL.md (with fenced-code stripped) for _shared/<name>.
    Returns [(shared-name, referring-skill-id), ...]. Does NOT auto-resolve."""


# manifest_loader.py (Phase 3)
class ManifestError(Exception):
    """Raised on parse failure or validation error. Carries file:line if available."""

def load(path: Path) -> dict: ...
def merge_cli(manifest: dict, cli: argparse.Namespace) -> dict: ...
def validate(manifest: dict, root: Path) -> list[str]: ...
def apply_defaults(manifest: dict, root: Path) -> dict: ...


# pack/ subpackage (Phase 2, modularized)
# pack/cli.py
def main(argv: list[str] | None = None) -> int: ...
# pack/tarball.py
def build_tarball(selection: list[tuple[Path, str]], manifest: dict,
                  out_path: Path, *, source_date_epoch: int = 0) -> str:
    """Returns SHA256 hexdigest of the produced tarball."""
def normalize_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None: ...
# pack/manifest_io.py
def build_manifest_json(files: list[FileEntry], bundle: dict, source_commit: str) -> bytes: ...
def write_sha256_sidecar(tarball_path: Path) -> Path: ...
# pack/templates.py
def render_template(template_path: Path, tokens: dict[str, str]) -> bytes:
    """Substitute {{TOKEN}}; unknown token raises TemplateError (NOT silent)."""


# build_manifest.py (Phase 4)
def discover(root: Path) -> dict: ...
def list_questions(discovery: dict, lang: str = "en") -> dict: ...
def write_manifest(answers: dict, out_path: Path, force: bool = False) -> int: ...
```

**Boolean CLI precedence (red-team F17.2):** all boolean flags use `argparse.BooleanOptionalAction(default=None)`. `merge_cli` treats `None` as "no override" — manifest value wins. Only explicit `--flag` or `--no-flag` from CLI overrides.

## Cross-Phase Artifact Mutations

| Artifact | Phase 1 declares | Mutated by | Final form |
|----------|------------------|------------|------------|
| `scripts/requirements.txt` | created with `pyyaml>=6.0,<7` | (no further changes) | `pyyaml>=6.0,<7` |
| `scripts/requirements-dev.txt` | NOT created in Phase 1 | Phase 5 creates | `pytest>=7,<9\npytest-cov` |
| `references/manifest-spec.md` | stub | Phase 3 fills | full schema reference |
| `references/flag-reference.md` | stub | Phase 2 fills | full 18-flag table |
| `references/safety-rules.md` | stub | Phase 3 fills | full always-drop catalog |
| `references/workflow-pack.md` | stub | Phase 4 fills | interactive flow + question bank |
| `references/error-catalog.md` | NOT created | Phase 3 creates | error code table |
| `references/troubleshooting.md` | NOT created | Phase 6 creates | top 5 failures + fixes |
| `references/maintainers-guide.md` | NOT created | Phase 6 creates | architecture + extension recipes |
| `CHANGELOG.md` (skill root) | NOT created | Phase 6 creates | seeded with v0.1.0 entry |
| `README.md` (skill root) | created basic | Phase 6 adds FAQ section | install + quickstart + FAQ |
| `SKILL.md` flags table | Phase 1 lists names | Phase 2 fills descriptions | full descriptions |
| `install.sh` (skill) | venv + pyyaml only | Phase 5 adds `--dev` flag | venv + pyyaml; `--dev` opt-in installs pytest |
| `.claude/skills/product-spec/install.sh` | NOT in scope | **Phase 6 modifies** to mirror `--dev` pattern (back-port per R3.Q10) | dev-only pytest |

## Release Gates (validate F5.1 BLOCKING resolved)

| Version | Gate criteria |
|---------|---------------|
| **0.1.0** (dogfood) | All 7 phases complete · pytest green (Ubuntu + macOS) · smoke test 7 green · used internally to pack product-spec |
| **0.5.0** (beta) | External recipient successfully extracts + runs installer on macOS + Linux + Windows · install.sh + install.ps1 covered · `references/troubleshooting.md` validated against real recipient issues |
| **1.0.0** (GA) | 5+ external bundles shipped without bug reports · maintainer's guide ratified · all PO-judgment decisions documented in change log |

Skill SKILL.md `metadata.version` follows this ladder (start `0.1.0`, never `1.0.0` until GA gate).

## Schema Migration Policy (validate F9.1 HIGH resolved)

`pack.manifest.yaml` schema follows semver:

- **Patch (1.0 → 1.1):** additive only (new optional fields with defaults). Old manifests still parse. No migration needed.
- **Minor (1.0 → 1.5):** additive + optional rename of fields with backward-compat alias. Migration helper documented in CHANGELOG.
- **Major (1.0 → 2.0):** breaking. `pack.py` refuses with: `"manifest schema v1.0 not supported in this version of claude-pack; run pack.py --migrate-manifest <input>"`. The `--migrate-manifest` subcommand is YAGNI for now; documented as the contract.

Tarball `MANIFEST.json` schema follows same versioning rules. Recipient `install.sh` reads `schema_version` first and bails gracefully on unsupported.

## Sunset Considerations (validate F14.1)

If Anthropic ships an official skill registry/marketplace later, claude-pack tarball format remains useful as a transport. Migration path: tighten MANIFEST.json schema toward registry-compatible format; recipient docs cross-reference official tooling. Low-effort foresight; not a deliverable.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Scaffold and Templates](./phase-01-scaffold-and-templates.md) | Completed |
| 2 | [Pack Builder Core](./phase-02-pack-builder-core.md) | Completed |
| 3 | [Safety Check and Manifest Loader](./phase-03-safety-check-and-manifest-loader.md) | Completed |
| 4 | [Interactive Manifest Builder](./phase-04-interactive-manifest-builder.md) | Completed |
| 5 | [Eval and Pytest Tests](./phase-05-eval-and-pytest-tests.md) | Completed |
| 6 | [Root CLAUDE.md Integration and Smoke Test](./phase-06-root-claude-md-integration-and-smoke-test.md) | Completed |
| 7 | [CI Integration and Release Pipeline](./phase-07-ci-integration-and-release-pipeline.md) | Completed |

**Implementation note (2026-05-29):** All 7 phases implemented + verified. Final state: `pack/` subpackage modularized into 7 files (args, cli, pipeline, selection, tarball, manifest_io, templates — each <200 LOC, `pipeline.py` added during code-review to keep `cli.py` under budget). 60 unit tests + 1 integration test green; 17/17 smoke checks green; tarball byte-identical determinism verified. Code-review pass fixed one CRITICAL (top-level secret leak in `safety_check.is_dropped` — patterns were `**/`-anchored and missed bare arcnames; now basename-matched) + IMPORTANT (`BUNDLE_NAME` token in INSTALL.md, `--strict`/`--all` made functional/honest). `built_at` made deterministic-by-default (epoch 0) to honor the byte-identity contract.

**Total effort (post-fix):** Phase 1 (3h) + Phase 2 (7h) + Phase 3 (5h) + Phase 4 (4h) + Phase 5 (8h) + Phase 6 (4h) + Phase 7 (3h) = **34h** (was 23h pre-review).

## Target Directory Structure

```
.claude/skills/claude-pack/
├── SKILL.md                          # ~220 lines, operating contract
├── README.md                         # ~80 lines, install + quickstart + FAQ
├── CHANGELOG.md                      # ~40 lines, keepachangelog format
├── install.sh                        # ~50 lines, venv + pyyaml; --dev opt-in
├── install.ps1                       # ~50 lines, Windows equivalent (NEW)
├── scripts/
│   ├── requirements.txt              # pyyaml>=6.0,<7
│   ├── requirements-dev.txt          # pytest>=7,<9 + pytest-cov
│   ├── pack/                         # MODULARIZED (200-line rule)
│   │   ├── __init__.py               # exports main entry
│   │   ├── __main__.py               # python -m pack
│   │   ├── cli.py                    # ~120 lines, argparse
│   │   ├── tarball.py                # ~150 lines, deterministic build
│   │   ├── manifest_io.py            # ~80 lines, MANIFEST.json + sidecar
│   │   └── templates.py              # ~50 lines, token substitution
│   ├── safety_check.py               # ~200 lines (expanded secrets list)
│   ├── manifest_loader.py            # ~220 lines (validate strengthening)
│   ├── build_manifest.py             # ~250 lines, discover + write
│   └── tests/
│       ├── conftest.py
│       ├── test_pack_determinism.py
│       ├── test_safety_check.py
│       ├── test_manifest_loader.py
│       ├── test_build_manifest.py
│       ├── test_golden_synthetic.py     # blocking unit (synthetic fixture)
│       ├── test_golden_product_spec.py  # marker: pytest -m integration, non-blocking
│       └── fixtures/
│           ├── sample-skill/             # synthetic fixture for golden unit
│           ├── dirty-claude/             # contains .env, .git, __pycache__
│           ├── minimal-claude/
│           ├── sample.manifest.yaml
│           └── interactive-answers.json
├── references/
│   ├── manifest-spec.md              # pack.manifest.yaml schema + examples
│   ├── flag-reference.md             # full 18-flag table
│   ├── safety-rules.md               # expanded always-drop catalog (~150 lines)
│   ├── workflow-pack.md              # interactive + CLI + manifest flow
│   ├── error-catalog.md              # NEW: all errors + messages + remediations
│   ├── troubleshooting.md            # NEW: top 5 recipient failures
│   └── maintainers-guide.md          # NEW: architecture + extension recipes
├── assets/
│   └── templates/
│       ├── manifest.example.yaml     # copyable manifest seed
│       ├── INSTALL.md.template       # ships in tar root, skeleton locked
│       ├── install.sh.template       # POSIX recipient installer (version-aware)
│       └── install.ps1.template      # Windows recipient installer (version-aware)
└── eval/
    ├── evals.json                    # 3 scenarios
    └── fixtures/
        ├── minimal.manifest.yaml
        ├── interactive-answers.json
        └── dirty-claude/.env
```

**Outputs (recipient-facing):**
```
dist/
├── claude-pack-0.1.0.tar.gz
└── claude-pack-0.1.0.tar.gz.sha256
```

**Tarball internal layout (versioned root dir):**
```
claude-pack-0.1.0/
├── MANIFEST.json
├── INSTALL.md
├── install.sh
├── install.ps1
└── .claude/
    ├── skills/
    │   └── product-spec/...
    ├── agents/...
    ├── rules/...
    └── scripts/, schemas/, ...
```

## Cross-Plan Dependencies

- **Reads from (completed plan):** `plans/260528-0912-cleanmatic-product-spec-skill/` — convention precedent for SKILL.md frontmatter, install.sh, eval/evals.json shape, venv pattern. No active dependency (that plan is `status: completed`).
- **Modifies (out-of-plan side effect, Phase 6):** `.claude/skills/product-spec/install.sh` + its `requirements.txt` — back-ports the `--dev` flag pattern per PO directive R3.Q10. Documented as a deliberate scope expansion.
- **Blocks:** none.
- **Blocked by:** none.

## Boundary / Scope (KISS)

**In scope (v1):**
- Pack `.claude/` subtree per manifest selection
- Modularized `pack/` subpackage (5 files, each <200 LOC)
- Multiplatform bundled installer (sh + ps1) with version-awareness
- SHA256 sidecar
- Deterministic tarball (PAX + sorted + mtime=0)
- Cross-platform pack.py (POSIX + Windows)
- 3-scenario eval + 17-test pytest suite
- CI matrix (Ubuntu + macOS + Windows × Python 3.11/3.12/3.13)
- Release pipeline (tag → build → gh release upload)
- Documentation suite: troubleshooting, error catalog, maintainer's guide, FAQ, CHANGELOG
- Edge cases: empty pack rejection, `--max-size`, symlink rejection, tmp cleanup
- `_shared/` deps: warn-only, opt-in `--include-shared`
- Side effect: product-spec install.sh `--dev` retrofit

**Out of scope (defer to v0.5 or later):**
- `zip` / `tar.zst` formats
- GPG signing
- Recipient-side `cleanmatic:claude-unpack` companion skill
- Intelligent merge-resolver into recipient's `.claude/`
- Multi-project manifest (packing >1 `.claude/` root)
- Diff between two packs (`claude-pack diff a.tar.gz b.tar.gz`)
- Auto-publish to S3 (recipient uses `gh release upload` manually)
- Bilingual EN+VI prose (developer-facing, English-only)
- Manifest schema migration tool (`--migrate-manifest` documented, not built)
- Transitive `_shared/` resolution (single-level grep only)
- Incremental/delta packs
