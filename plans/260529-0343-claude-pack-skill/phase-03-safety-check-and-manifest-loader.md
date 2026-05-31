---
phase: 3
title: "Safety Check and Manifest Loader"
status: pending
priority: P1
effort: "5h"
dependencies: [1]
---

# Phase 3: Safety Check and Manifest Loader

## Overview

Implement two supporting modules + create the error catalog. **Critical phase**: contains all 3 CRITICAL findings fixes from red-team review (expanded secrets list, absolute-path rejection, `.git/` always-drop) plus 14 HIGH-severity validate/red-team items.

- **`safety_check.py`** — encapsulates the EXPANDED always-drop list (hard safety, non-negotiable), the opt-in-only list (settings.json, .ck.json), and the `_shared/` dependency grep (warn-only per R2.Q3; NOT auto-resolve). Emits JSON findings to stdout when CLI; importable for in-process use by `pack/`.
- **`manifest_loader.py`** — parses `pack.manifest.yaml`, merges CLI overrides per locked precedence (`BooleanOptionalAction(default=None)` from Phase 2), validates against the hardened schema, resolves defaults, returns normalized manifest dict.
- **`references/error-catalog.md`** — NEW: machine-readable + human-readable catalog of every error code/message/remediation in claude-pack (validate F6.2 HIGH).

These modules are **structural** layer (script-vs-LLM split). They never call AskUserQuestion; that's Phase 4 LLM layer.

## Context Links

- Plan `## API Contracts` — locked signatures (`is_dropped`, `is_optional`, `find_shared_refs`, `load`, `merge_cli`, `validate`, `apply_defaults`, `ManifestError`)
- Plan `## Schema Migration Policy` — schema_version semantics
- Red-team report — `F2.1`, `F2.2`, `F4.5`, `F14.2` (CRITICAL); `F2.3`, `F4.1`, `F4.2`, `F5.1`, `F17.1`, `F-X1` (HIGH)
- Validate report — `F2.2` (API contracts), `F6.2` (error catalog), `F9.1` (schema migration)
- Convention precedent: `.claude/skills/product-spec/scripts/check_consistency.py` (findings JSON shape), `frontmatter_parser.py` (yaml.safe_load pattern)

## Requirements

### safety_check.py

**Always-drop list (EXPANDED per red-team F2.1 + F14.2 CRITICAL):**

```python
ALWAYS_DROP_EXACT = frozenset({
    # Secrets / credentials
    ".env", ".envrc",
    "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
    ".netrc", ".pgpass",
    # Runtime / cache
    "metadata.json",
    ".DS_Store", "Thumbs.db", "desktop.ini",
})

ALWAYS_DROP_DIRS = frozenset({
    # VCS — critical to drop (F14.2)
    ".git", ".gitlab", ".hg", ".svn", ".bzr",
    # Runtime caches
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    # Virtualenvs / vendoring
    ".venv", "venv", "node_modules", ".npm", ".yarn",
    # Claude Code runtime state
    ".logs", "session-state", "agent-memory",
    # Build artifacts
    "dist", "build", "target", ".next", ".turbo",
})

ALWAYS_DROP_PATTERNS = (
    # Secrets variants
    "**/.env.*", "**/.env-*", "**/.env_*",
    "**/secrets.*", "**/credentials.*",
    "**/*.pem", "**/*.key", "**/*.p12", "**/*.pfx", "**/*.jks",
    "**/id_rsa*", "**/id_ed25519*", "**/id_ecdsa*", "**/id_dsa*",
    "**/*.kdbx",           # KeePass DB
    "**/*token*.json", "**/*secret*.json",
    # Python compiled
    "**/*.pyc", "**/*.pyo",
)

OPT_IN_PATHS = {
    ".claude/settings.json": "settings",
    ".claude/.ck.json": "ck-config",
}

SHARED_REF_RE = re.compile(r"_shared/([a-z0-9_-]+)")  # lowercase enforced
```

**Functional:**
- `is_dropped(path: str) -> tuple[bool, str | None]` — return `(True, "always-drop:<rule-id>")` or `(False, None)`.
  - Normalize path with `PurePosixPath`
  - Check basename in `ALWAYS_DROP_EXACT`
  - Check **any path component** in `ALWAYS_DROP_DIRS` (red-team F2.2: use `if c in DROPS for c in p.parts`, NOT substring `in`)
  - Check `fnmatch.fnmatchcase(path, pattern)` for each glob in `ALWAYS_DROP_PATTERNS`
  - Return `(True, f"always-drop:{rule-id}")` where rule-id = `exact:<name>` / `dir:<name>` / `pattern:<glob>`
- `is_optional(path: str) -> tuple[bool, str | None]` — return `(True, label)` for opt-in paths; `(False, None)` otherwise.
  - Match `OPT_IN_PATHS` keys with **arcname-suffix anchor** (red-team F2.3): `path == key or path.endswith("/" + key)`.
- `find_shared_refs(skill_dirs: list[Path]) -> list[tuple[str, str]]` — for each skill dir, read SKILL.md, **strip fenced markdown code blocks** (` ``` ... ``` `) before regex (red-team F5.1), find `_shared/<name>` matches. Return `[(shared-name, referring-skill-id), ...]`. **Does NOT auto-resolve** (warn-only per R2.Q3). Caller (pack/cli) decides include/skip via `--include-shared` flag.
- **Missing-ref warn**: also emit a `shared_dep_missing` finding when SKILL.md references `_shared/foo` but `.claude/skills/_shared/foo` doesn't exist on disk (red-team F5.3).
- CLI: `safety_check.py --root <project> [--scan <subdir>] [--strict]` — emit JSON findings; exit 2 only if `--strict` AND any `severity: error` finding (currently none qualify; reserved for future).

**JSON output shape** (versioned for future evolution):
```json
{
  "schema_version": "1.0",
  "scanned_at": "2026-05-29T03:43:00Z",
  "root": "/abs/path",
  "findings": [
    {"check": "always_drop", "severity": "warn", "path": ".claude/.env", "rule": "exact:.env"},
    {"check": "always_drop", "severity": "warn", "path": ".git/objects/pack", "rule": "dir:.git"},
    {"check": "optional", "severity": "info", "path": ".claude/settings.json", "rule": "settings"},
    {"check": "shared_dep", "severity": "info", "path": ".claude/skills/_shared/lib", "referring_skill": "ck-plan"},
    {"check": "shared_dep_missing", "severity": "warn", "missing": "legacy_thing", "referring_skill": "old-skill"}
  ]
}
```

**Non-functional:**
- Pure stdlib (no pyyaml dep here — paths + regex + fnmatch only).
- Deterministic ordering: findings sorted by `(check, path)`.
- Importable: `from safety_check import is_dropped, is_optional, find_shared_refs, SafetyError`.

### manifest_loader.py

**Functional:**

- `load(path: Path) -> dict` — `yaml.safe_load`; wrap `yaml.YAMLError → ManifestError` carrying `file:line:col`. Returns `{}` for empty file.
- `merge_cli(manifest: dict, cli: argparse.Namespace) -> dict` — precedence:
  - For each CLI key: if `getattr(cli, key, None) is None` → keep manifest value
  - Else: CLI value replaces manifest value
  - Lists from CLI (`--skills foo,bar`) are split on `,` and **dedupe** (red-team F4.3): replace manifest list with `list(dict.fromkeys(parts))`
  - Booleans use `BooleanOptionalAction(default=None)` (red-team F17.2) — `None` keeps manifest; `True`/`False` overrides.
- `validate(manifest: dict, root: Path) -> list[str]` — HARDENED checks:
  - `schema_version` in `{"1.0"}` (else error: "unsupported schema version; this builder supports 1.0")
  - `version` matches SemVer 2.0.0 (red-team F4.2): `^(?:\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?|0\.0\.0-dev)$`
  - **Refuse `0.0.0-dev`** unless explicit CLI `--allow-dev-version` (red-team F4.1) — return error: "refuse to build with placeholder version; pass --allow-dev-version to override or set version in manifest"
  - `bundle_name` matches `^[a-zA-Z0-9][a-zA-Z0-9._-]*$` (red-team F4.7) — no path traversal in output filename
  - Each of `skills`, `agents`, `hooks`, `rules`, `extra` is a list of non-empty strings
  - **No duplicates** in any category list (red-team F4.3): `if len(set(L)) != len(L): error`
  - For each `extra` path: **reject absolute** (red-team F4.5 CRITICAL): `if Path(p).is_absolute() or (":" in p[:3] for Windows drive letters): error`; **reject traversal**: `if ".." in PurePosixPath(p).parts: error`
  - `top_level` is a dict; **strict known-keys check** (red-team F4.6): allowed = `{include_readme, include_claudemd, include_settings, include_ck_config}`; unknown → warn-level error message
  - Top-level unknown keys → warn-level error
  - `follow_shared` is a bool (default `false`; warn-only opt-in per R2.Q3)
  - **For each skill/agent/hook/rule slug: verify on-disk existence** with **case-sensitive** check (red-team F4.4): `(root / ".claude/skills" / slug).is_dir()` — error "missing skill: {slug}" if not found
- `apply_defaults(manifest: dict, root: Path) -> dict` — fill missing top-level keys with defaults; auto-add `.claude/scripts/` and `.claude/schemas/` to `extra` if they exist on disk AND not already present AND `defaults.include_scripts != false` (red-team F13.1: opt-out exists).
- CLI: `manifest_loader.py --manifest <path> [--root <project>] [--resolve]` — emit JSON `{ok, manifest, errors}`; exit 0.

**Manifest schema v1.0 (LOCKED end of this phase per validate F5.3):**
```yaml
schema_version: "1.0"            # optional; default "1.0"
version: "1.0.0"                 # required SemVer 2.0.0; "0.0.0-dev" requires --allow-dev-version
bundle_name: "claude-pack"       # default; matches ^[a-zA-Z0-9][a-zA-Z0-9._-]*$
skills: []                       # skill slug names (no path prefix); deduped
agents: []                       # agent file basenames (auto-append .md if no extension)
hooks: []                        # hook file basenames (extension required)
rules: []                        # rule file basenames (auto-append .md if no extension)
extra: []                        # paths relative to repo root; NO absolute, NO ..
top_level:
  include_readme: false
  include_claudemd: false
  include_settings: false
  include_ck_config: false
defaults:
  include_scripts: true          # default-ship .claude/scripts/
  include_schemas: true          # default-ship .claude/schemas/
follow_shared: false             # warn-only; opt-in via --include-shared CLI
```

**Extension auto-append edge cases (red-team F17.5):** if basename has no extension, append `.md`. If basename has any extension, use as-is. Multiple disk matches for same basename → error. Pin in manifest-spec.md.

### references/error-catalog.md (NEW per validate F6.2)

Table with columns: code, message template, raised-by, PO-facing remediation. Cover every `ManifestError`, `SafetyError`, `TemplateError`, `CollisionError`, exit codes 1-5. ≤150 lines.

## Architecture

```
safety_check.py
├── ALWAYS_DROP_EXACT / DIRS / PATTERNS constants
├── OPT_IN_PATHS dict
├── SHARED_REF_RE regex
├── SafetyError(Exception)
├── is_dropped(path) → tuple[bool, str | None]
├── is_optional(path) → tuple[bool, str | None]
├── find_shared_refs(skill_dirs) → list[tuple[str, str]]
├── _strip_fenced_blocks(text: str) → str   # helper: remove ```...```
└── main() — CLI: --root --scan --strict

manifest_loader.py
├── ManifestError(Exception)
├── DEFAULT_SCHEMA_VERSION = "1.0"
├── SEMVER_RE = re.compile(r"^(?:\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?|0\.0\.0-dev)$")
├── BUNDLE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
├── ALLOWED_TOP_LEVEL_KEYS = frozenset({...})
├── ALLOWED_NESTED_TOP_LEVEL_KEYS = frozenset({"include_readme", ...})
├── load(path) → dict
├── merge_cli(manifest, cli) → dict
├── validate(manifest, root) → list[str]
├── apply_defaults(manifest, root) → dict
├── _resolve_extension(slug: str, root: Path, category: str) → Path  # auto-append .md
└── main() — CLI: --manifest --root --resolve
```

## Related Code Files

**Create:**
- `.claude/skills/claude-pack/scripts/safety_check.py` (~200 LOC; expanded from earlier ~180)
- `.claude/skills/claude-pack/scripts/manifest_loader.py` (~220 LOC; hardened from earlier ~200)
- `.claude/skills/claude-pack/references/error-catalog.md` (NEW, ≤150 LOC)

**Modify:**
- `.claude/skills/claude-pack/references/safety-rules.md` — fill from Phase 1 stub with EXPANDED catalog: every entry in `ALWAYS_DROP_EXACT/DIRS/PATTERNS` documented with rationale, plus `OPT_IN_PATHS` table, plus `_shared/` warn-only policy explanation
- `.claude/skills/claude-pack/references/manifest-spec.md` — fill from Phase 1 stub: full schema reference with every field type + required + default + example; include "Migration from v0 to v1" placeholder per validate F9.1

## Implementation Steps

### safety_check.py

1. **Constants** — per Requirements block above. Sorted for review.

2. **`_strip_fenced_blocks(text)`** — regex `r"```.*?```"` (DOTALL flag) → replace with empty string. Used by `find_shared_refs` before regex (red-team F5.1).

3. **`is_dropped(path)`** — 4-step check:
   - Normalize via `PurePosixPath(path)`
   - basename in `ALWAYS_DROP_EXACT` → `(True, f"always-drop:exact:{basename}")`
   - any part in `ALWAYS_DROP_DIRS` → `(True, f"always-drop:dir:{matching_part}")`
   - `fnmatch.fnmatchcase(path, pattern)` for each glob → `(True, f"always-drop:pattern:{glob}")`
   - else `(False, None)`

4. **`is_optional(path)`** — exact-or-suffix match against `OPT_IN_PATHS` keys. Return `(True, label)` or `(False, None)`.

5. **`find_shared_refs(skill_dirs)`** — for each skill dir, read SKILL.md (skip silently if missing), strip fenced blocks, regex-find `_shared/<name>` (must be lowercase per regex), dedupe matches per skill, return `[(name, skill-id), ...]` sorted. NO transitive resolution (defer to v0.5; document).

6. **CLI `main()`** — argparse `--root` (default CWD), `--scan` (default `.claude`), `--strict`. Walk subdir; for each entry: `is_dropped`, `is_optional`. Separately: enumerate skills in `.claude/skills/`, call `find_shared_refs`; for refs without on-disk presence, emit `shared_dep_missing`. Build findings list, sort, print JSON, exit 0 (or 2 in `--strict` if errors).

### manifest_loader.py

7. **Exceptions + constants** — `ManifestError(Exception)`, `SEMVER_RE`, `BUNDLE_NAME_RE`, allowed-key sets.

8. **`load(path)`** — `yaml.safe_load`; catch `YAMLError` → raise `ManifestError(f"{path}:{e.problem_mark.line}:{e.problem_mark.column}: {e.problem}")`. Return `{}` for empty.

9. **`validate(manifest, root)`** — return list of error strings. Run ALL checks from Requirements; collect all errors (don't short-circuit). Each error string includes a stable code (`MANIFEST_E001` etc.) cross-referencing `error-catalog.md`.

10. **`merge_cli(manifest, cli)`** — iterate manifest keys + CLI-only fields (e.g., `--include-shared`). `None` from CLI keeps manifest. Lists from CLI split on `,`, deduped via `dict.fromkeys`. Booleans replace cleanly (since `None` is the "no-override" sentinel, `False` is a real override).

11. **`apply_defaults(manifest, root)`** — fill missing top-level keys; if `defaults.include_scripts is True` (or missing) AND `.claude/scripts/` exists AND not already in `extra`, prepend to `extra`. Same for `schemas/`.

12. **`_resolve_extension(slug, root, category)`** — for agents/rules: if slug has no extension, append `.md`; search recursively. Multiple matches → raise `ManifestError("ambiguous {category}: {slug} matches {paths}")`.

13. **CLI `main()`** — argparse `--manifest` + `--root` + `--resolve`. Print JSON `{ok, manifest, errors}`; exit 0.

### references fills

14. **`safety-rules.md`** — 3 tables: ALWAYS_DROP catalog (each entry: rule, severity, rationale, source), OPT_IN paths, `_shared/` policy. ≤200 lines.

15. **`manifest-spec.md`** — schema reference; every field documented; example seeds; migration policy stub.

16. **`error-catalog.md`** — error code, message template, raised-by module, PO-facing remediation. ≤150 lines.

### Compile + lint

17. **Per-phase compile** (validate F15.3): `python -m py_compile scripts/safety_check.py scripts/manifest_loader.py` exits 0.

## Success Criteria

### safety_check.py

- [ ] `safety_check.py --root . --scan .claude` emits valid JSON; sorted findings; exits 0
- [ ] `is_dropped(".claude/.env")` → `(True, "always-drop:exact:.env")`
- [ ] `is_dropped(".claude/.envrc")` → `(True, "always-drop:exact:.envrc")` (RED-TEAM F2.1 fix verified)
- [ ] `is_dropped(".claude/.env.production")` → `(True, "always-drop:pattern:**/.env.*")` (RED-TEAM F2.1 fix verified)
- [ ] `is_dropped("foo/.git/HEAD")` → `(True, "always-drop:dir:.git")` (RED-TEAM F14.2 CRITICAL fix verified)
- [ ] `is_dropped("foo/secrets.json")` → `(True, "always-drop:pattern:**/secrets.*")`
- [ ] `is_dropped("foo/id_rsa")` → `(True, "always-drop:exact:id_rsa")`
- [ ] `is_dropped(".claude/skills/foo/scripts/__pycache__/bar.pyc")` → `(True, "always-drop:dir:__pycache__")` (deep-nested)
- [ ] `is_dropped("legitimate/.envfoo")` → `(False, None)` (no false positive on substring)
- [ ] `is_dropped(".claude/skills/foo/SKILL.md")` → `(False, None)`
- [ ] `is_optional(".claude/settings.json")` → `(True, "settings")`
- [ ] `find_shared_refs([skill_dir_referencing_shared_foo])` returns `[("foo", "skill-slug")]` even when ref is inside `_shared/foo` documentation in markdown body (code block stripped)
- [ ] `find_shared_refs` on a skill whose SKILL.md references `_shared/missing` (not on disk) emits NO entry but `safety_check.py --scan` emits `shared_dep_missing` finding

### manifest_loader.py

- [ ] `manifest_loader.py --manifest assets/templates/manifest.example.yaml --resolve` emits JSON with no errors
- [ ] `validate({"version": "1.0.0"}, root)` → no errors; just defaults applied
- [ ] `validate({"version": "0.0.0-dev"}, root)` → ONE error: "refuse 0.0.0-dev without --allow-dev-version" (RED-TEAM F4.1 fix verified)
- [ ] `validate({"version": "1.0.0+build.42"}, root)` → no errors (SemVer 2.0.0 build metadata; RED-TEAM F4.2 fix verified)
- [ ] `validate({"version": "1.0.0", "extra": ["/etc/passwd"]}, root)` → error "absolute paths not allowed" (RED-TEAM F4.5 CRITICAL fix verified)
- [ ] `validate({"version": "1.0.0", "extra": ["../foo"]}, root)` → error "path traversal not allowed"
- [ ] `validate({"version": "1.0.0", "skills": ["product-spec", "product-spec"]}, root)` → error "duplicate entries in skills"
- [ ] `validate({"version": "1.0.0", "skills": ["nonexistent"]}, root)` → error "missing skill: nonexistent"
- [ ] `validate({"version": "1.0.0", "bundle_name": "../etc/foo"}, root)` → error "bundle_name has invalid characters"
- [ ] `validate({"version": "1.0.0", "top_lvl": {}}, root)` → warn-level error "unknown top-level key: top_lvl"
- [ ] `validate({"version": "1.0.0", "top_level": {"unknown_flag": true}}, root)` → warn-level error
- [ ] `merge_cli(manifest, ns(skills="foo,bar"))` replaces `manifest["skills"]` with `["foo", "bar"]` (deduped)
- [ ] `merge_cli(manifest_with_top_level_readme_true, ns(include_readme=None))` keeps manifest True (BooleanOptionalAction default None — RED-TEAM F17.2 fix verified)
- [ ] `merge_cli(manifest_with_top_level_readme_true, ns(include_readme=False))` overrides to False
- [ ] `apply_defaults({"version": "1.0.0"}, repo_root)` auto-adds `.claude/scripts/`, `.claude/schemas/` to `extra` if they exist
- [ ] `python -m py_compile scripts/safety_check.py scripts/manifest_loader.py` exits 0

### references

- [ ] `references/safety-rules.md` documents EVERY entry in ALWAYS_DROP_EXACT/DIRS/PATTERNS (`grep -c '^|' safety-rules.md` ≥ 30 rows)
- [ ] `references/manifest-spec.md` documents every schema field with type + example
- [ ] `references/error-catalog.md` has ≥10 rows (Manifest errors + Safety + Template + Collision + exit codes)

## Risk Assessment

- **R1: pyyaml `safe_load` returns `None` for empty file** → `load()` returns `{}` for `None`.
- **R2: Glob pattern `**/.env.*` over-matches** → Test with `.env.local`, `.env-staging`, `.env_prod`, AND verify it does NOT match `.envrc` (handled by exact-list) or `.envfoo` (no match, safe).
- **R3: Strict schema rejects valid YAML** → Allow `additionalProperties` for top-level keys with warn-level error (not blocking). For nested `top_level`, strict check (since the keys are bool flags — unknown = silent regression).
- **R4: case-sensitivity inconsistency macOS HFS+** → Use `PurePosixPath` always (case-sensitive). Document in safety-rules.md: recipient case-insensitive FS may collide; rare.
- **R5: `find_shared_refs` regex misses uppercase `_shared/Foo`** → Per regex `[a-z0-9_-]`, uppercase silently skipped. Add note in safety-rules.md: enforce lowercase `_shared/` convention.
- **R6: Extension auto-append breaks for `foo.md.bak`** → spec in manifest-spec.md: if basename has any extension, use as-is.
- **R7: error-catalog.md drift from actual error messages** → Phase 5 test asserts every error string includes its catalog code (`MANIFEST_E001` etc.). CI grep-check.
- **R8: schema v1.0 lock vs future v1.1 additive change** → Plan `## Schema Migration Policy` documents the rule; CHANGELOG references each schema version.

## Security Considerations

- `safety_check.is_dropped` is HARD safety. Even if user puts `.env` in `extra`, filter drops it. Phase 5 T-S4 verifies.
- `manifest_loader.load` uses `yaml.safe_load` only. CI grep `yaml.load` returns 0.
- Absolute-path + traversal rejection in `extra` prevents `/etc/passwd` exfiltration (CRITICAL F4.5).
- `.git/` always-drop prevents git-history secret leak (CRITICAL F14.2).
- `find_shared_refs` reads SKILL.md but never executes Python/scripts inside.

## Next Steps

- Phase 2 (`pack/cli.py`) is unblocked: API contracts from plan.md are locked here.
- Phase 4 (`build_manifest.py`) consumes `manifest_loader.validate` for write-time check.
- Phase 5 verifies hard safety: `.env` cannot be packed even with explicit listing; `.git/` never appears; absolute-path manifest rejected.
- Phase 6 dogfoods: seed manifest at `.claude/pack.manifest.yaml` parses + validates clean.
