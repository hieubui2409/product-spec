# manifest-spec

The schema reference for `.claude/pack.manifest.yaml`. Implementation: `scripts/manifest_loader.py`.

## Top-Level Fields

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `schema_version` | string | no | `"1.0"` | Schema version. Builder refuses unsupported major versions. |
| `version` | string | **yes** | — | Bundle version. SemVer 2.0.0. `0.0.0-dev` requires `--allow-dev-version`. |
| `bundle_name` | string | no | `"claude-pack"` | Output filename stem. Regex `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`. |
| `skills` | list[string] | no | `[]` | Skill slugs under `.claude/skills/`. Case-sensitive. Deduped. |
| `agents` | list[string] | no | `[]` | Agent file basenames under `.claude/agents/` (`.md` auto-appended). |
| `hooks` | list[string] | no | `[]` | Hook filenames under `.claude/hooks/` (extension required). |
| `rules` | list[string] | no | `[]` | Rule filenames under `.claude/rules/` (`.md` auto-appended). |
| `extra` | list[string] | no | `[]` | Repo-relative paths. NO absolute. NO `..`. |
| `top_level` | mapping | no | `{}` | Top-level repo flags. See below. |
| `defaults` | mapping | no | `{}` | Opt-in subtree + size behavior. See below. |
| `follow_shared` | bool | no | `false` | If true, auto-include `_shared/` refs. Default warn-only. |

Unknown top-level keys emit a `MANIFEST_E060` error.

## `top_level` Sub-Schema

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `include_readme` | bool | `false` | Ship repo-root `README.md` at tar root. |
| `include_claudemd` | bool | `false` | Ship repo-root `CLAUDE.md` at tar root. |
| `include_settings` | bool | `false` | Ship `.claude/settings.json` (opt-in). |
| `include_ck_config` | bool | `false` | Ship `.claude/.ck.json` (opt-in). |

Strict known-keys check. Unknown keys → `MANIFEST_E031`. Non-bool values → `MANIFEST_E032`.

## `defaults` Sub-Schema

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `include_scripts` | bool | `false` | **Opt-in.** Auto-prepend `.claude/scripts/` to `extra`. CK-framework internals — NOT shipped by default. Enable with `--include-scripts`. |
| `include_schemas` | bool | `false` | **Opt-in.** Auto-prepend `.claude/schemas/` to `extra`. CK-framework internals — NOT shipped by default. Enable with `--include-schemas`. |
| `max_size_bytes` | int | 100MB | Reject if compressed tarball exceeds. CLI `--max-size` overrides. |

## CLI Merge Precedence

1. `manifest_loader.load(path)` loads YAML.
2. `manifest_loader.merge_cli(manifest, args)` applies CLI overrides:
 - For list keys: CLI value (csv-split, deduped) replaces manifest if not `None`.
 - For boolean flags using `BooleanOptionalAction(default=None)`: `None` = no override, `True`/`False` overrides.
3. `manifest_loader.validate(manifest, root)` returns list of error strings (each prefixed with stable code).
4. `manifest_loader.apply_defaults(manifest, root)` fills missing keys + prepends the `scripts`/`schemas` subtrees **only when their `defaults` flag is true** (both default false → opt-in).

## Validation Rules

- `version` must match SemVer 2.0.0 regex (allows pre-release and build metadata).
- `bundle_name` regex enforces filesystem-safe stem.
- Each list category: non-empty strings; no duplicates.
- All path-bearing categories (`skills`, `agents`, `rules`, `hooks`, `extra`, CLI-injected `_include_shared`): no absolute paths (`/etc/foo` or `C:\bar`); no `..` traversal. Enforced in every category for tar-slip containment — not just `extra`. Skills additionally have a symlink real-path containment check (resolves to within `.claude/skills/`).
- On-disk existence is checked using `is_dir()`/`rglob` with no case normalization — case sensitivity follows the host filesystem (case-sensitive on Linux ext4; case-insensitive on macOS APFS/HFS+ and Windows NTFS, where a wrong-case slug may resolve without error).
- Ambiguous basename match (multiple files under search root) → `MANIFEST_E071` (agents), `E072` (rules), `E074` (hooks). Rename or pin a unique path; this guards against a non-deterministic `rglob` pick.

## Extension Auto-Append

- If the basename has no extension (`primary-workflow` instead of `primary-workflow.md`), `.md` is appended.
- If any extension is present, use as-is. `foo.md.bak` is treated literally (no double-append).
- Multiple disk matches for the same basename → error. Disambiguate by pinning a path-qualified slug **within the same category** (e.g. `agents: [<subdir>/<name>]`), matching the `rglob`-on-relative-path resolution; reserve `extra` for non-agent/rule files.

## Schema Migration (semver)

- **Patch (1.0 → 1.1):** additive optional fields with defaults. Old manifests still parse.
- **Minor (1.0 → 1.5):** additive + backward-compat alias for renamed fields.
- **Major (1.0 → 2.0):** breaking. Builder refuses with `MANIFEST_E101`. `--migrate-manifest` is a documented future tool; YAGNI for v1.

## Example

See `assets/templates/manifest.example.yaml` for an annotated copyable example.

## Errors

See `references/error-catalog.md` for the full error code → message → remediation table.
