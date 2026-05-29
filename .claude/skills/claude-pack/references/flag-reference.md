# flag-reference

The full CLI reference for `python -m pack`. Each flag's behavior, type, default, and precedence vs the manifest is locked here.

## Boolean Flag Convention

All boolean flags use `argparse.BooleanOptionalAction` (default `None`). `None` = "no CLI override" → manifest value wins. Explicit `--flag` or `--no-flag` overrides manifest. This protects against silent CLI defaults overwriting deliberate manifest choices.

## Flag Table

| Flag | Type | Default | Manifest equivalent | Description |
|------|------|---------|---------------------|-------------|
| `--root <dir>` | path | `cwd` | (none) | Repo root for selection + on-disk checks. |
| `--manifest <path>` | path | `.claude/pack.manifest.yaml` | (none) | Manifest YAML to load. |
| `--version <semver>` | string | (manifest) | `version` | Override bundle version. SemVer 2.0.0; `0.0.0-dev` requires `--allow-dev-version`. |
| `--bundle-name <name>` | string | `claude-pack` | `bundle_name` | Output filename stem. Must match `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`. |
| `--out <dir>` | path | `dist/` | (none, CLI-only) | Output directory. Auto-created. |
| `--all` | flag | off | (none) | Pack everything under `.claude/` minus always-drop list. **Not implemented in v0.1** — errors (exit 1); list skills/agents/rules explicitly. Planned for v0.5. |
| `--skills <list>` | csv | (manifest) | `skills` | Comma-separated skill slugs. Deduped. |
| `--agents <list>` | csv | (manifest) | `agents` | Comma-separated agent basenames. `.md` auto-appended if extension absent. |
| `--hooks <list>` | csv | (manifest) | `hooks` | Comma-separated hook filenames. Extension required. |
| `--rules <list>` | csv | (manifest) | `rules` | Comma-separated rule filenames. `.md` auto-appended if absent. |
| `--extra <paths>` | csv | (manifest) | `extra` | Comma-separated repo-relative paths. NO absolute, NO `..`. |
| `--include-shared <list>` | csv | (manifest) | (additive) | Opt-in `_shared/<name>` subtrees. Without this, refs are warn-only. |
| `--include-readme` / `--no-include-readme` | bool | (manifest) | `top_level.include_readme` | Include repo-root `README.md`. |
| `--include-claudemd` / `--no-include-claudemd` | bool | (manifest) | `top_level.include_claudemd` | Include repo-root `CLAUDE.md`. |
| `--include-settings` / `--no-include-settings` | bool | (manifest) | `top_level.include_settings` | Include `.claude/settings.json` (opt-in only). |
| `--include-ck-config` / `--no-include-ck-config` | bool | (manifest) | `top_level.include_ck_config` | Include `.claude/.ck.json` (opt-in only). |
| `--follow-shared` / `--no-follow-shared` | bool | (manifest) | `follow_shared` | If true, auto-include all `_shared/` refs. Default false = warn-only. |
| `--force` / `--no-force` | bool | off | (none) | Overwrite existing tarball. Backs up as `.bak.{epoch}`. |
| `--dry-run` / `--no-dry-run` | bool | off | (none) | List files + total size; no tarball. |
| `--compute-sha` / `--no-compute-sha` | bool | off | (none) | With `--dry-run`: include would-be tarball SHA256 (uses BytesIO). |
| `--json` / `--no-json` | bool | off | (none) | Emit JSON status to stdout (machine-parseable). |
| `--source-date-epoch <val>` | int\|`env` | (none) → 0 | `defaults.source_date_epoch` | Mtime root. `env` honors `SOURCE_DATE_EPOCH` env var. |
| `--max-size <bytes>` | int | 100MB | `defaults.max_size_bytes` | Reject if compressed bigger than this. |
| `--strict` | flag | off | (none) | Treat un-included `_shared/` references as errors (exit 2) instead of warnings. |
| `--allow-dev-version` | flag | off | (none) | Allow `version: "0.0.0-dev"` placeholder. |

## Exit Codes (LOCKED)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation / manifest error |
| 2 | Strict-gate finding (`--strict`) |
| 3 | Output collision (no `--force`) |
| 4 | Write error (disk full, permission, cross-fs replace) |
| 5 | Empty selection / over-max-size |
| 130 | Interrupted (SIGINT) |

## Examples

```bash
# Build from manifest, deterministic
python -m pack --manifest.claude/pack.manifest.yaml

# Override version for ad-hoc build
python -m pack --manifest.claude/pack.manifest.yaml --version 0.2.0-rc1

# Dry-run + would-be SHA (no double-pass cost)
python -m pack --manifest.claude/pack.manifest.yaml --dry-run --compute-sha

# JSON output (CI-friendly)
python -m pack --manifest.claude/pack.manifest.yaml --json

# Honor SOURCE_DATE_EPOCH from CI
SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct) python -m pack \
 --manifest.claude/pack.manifest.yaml --source-date-epoch env

# Opt-in _shared/ subtrees
python -m pack --manifest.claude/pack.manifest.yaml --include-shared lib,utils
```
