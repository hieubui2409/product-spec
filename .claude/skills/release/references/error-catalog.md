# error-catalog

Every error code, message template, and remediation surfaced by `cleanmatic:release`. Stable codes (`MANIFEST_E###`) cross-reference between source, tests, and PO-facing diagnostics.

## Manifest Errors (`scripts/manifest_loader.py`)

| Code | Message template | Raised by | Remediation |
|------|------------------|-----------|-------------|
| `MANIFEST_E001` | `version must match SemVer 2.0.0 or be '0.0.0-dev'; got <value>` | `validate` | Set `version: "X.Y.Z"` in manifest, or pass `--version X.Y.Z`. |
| `MANIFEST_E002` | `refuse to build with placeholder version '0.0.0-dev'; pass --allow-dev-version` | `validate` | Either set a real version or pass `--allow-dev-version` for dev/CI builds. |
| `MANIFEST_E003` | `bundle_name has invalid characters` | `validate` | Use `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`. No `/`, no `..`, no spaces. |
| `MANIFEST_E010` | `<category> must be a list, got <type>` | `validate` | Rewrite as YAML list. |
| `MANIFEST_E011` | `<category> entry must be non-empty string` | `validate` | Remove blank/None entries. |
| `MANIFEST_E012` | `duplicate entries in <category>` | `validate` | Dedupe the list. |
| `MANIFEST_E020` | `absolute paths not allowed in <category>: <path>` | `validate` | Use repo-relative paths; absolute paths are rejected in every path-bearing category (skills, agents, rules, hooks, extra, _include_shared) for tar-slip containment. |
| `MANIFEST_E021` | `path traversal not allowed in <category>: <path>` | `validate` | Remove `..` segments. Applies to all path-bearing categories (skills, agents, rules, hooks, extra, _include_shared); also covers symlink-based escapes (real-path containment check on skills). |
| `MANIFEST_E030` | `top_level must be a mapping` | `validate` | Use a YAML mapping under `top_level:`. |
| `MANIFEST_E031` | `unknown top_level key: <key>` | `validate` | Use only `include_readme`, `include_claudemd`, `include_settings`, `include_ck_config`. |
| `MANIFEST_E032` | `top_level.<key> must be bool` | `validate` | Use `true` or `false`. |
| `MANIFEST_E040` | `defaults must be a mapping` | `validate` | Use a YAML mapping under `defaults:`. |
| `MANIFEST_E041` | `unknown defaults key: <key>` | `validate` | Use only `include_scripts`, `include_schemas`, `max_size_bytes`. |
| `MANIFEST_E042` | `defaults.max_size_bytes must be int>=0; got <value>` | `validate` | Use a non-negative integer (bytes). Rejects bool/string/negative — e.g. `false` would silently become 0 and reject every bundle. |
| `MANIFEST_E043` | `defaults.<key> must be bool; got <value>` | `validate` | `include_scripts`/`include_schemas` take `true`/`false` only. |
| `MANIFEST_E050` | `follow_shared must be bool` | `validate` | Use `true` or `false`. |
| `MANIFEST_E060` | `unknown top-level key: <key>` | `validate` | Remove or check spelling against schema. |
| `MANIFEST_E070` | `missing skill: <slug>` | `validate` | Verify the skill dir exists under `.claude/skills/`. Case sensitivity follows the host filesystem (case-sensitive on Linux ext4; case-insensitive on macOS APFS/HFS+ and Windows NTFS, where a wrong-case slug may silently resolve). |
| `MANIFEST_E071` | `missing agents: <slug>` / `missing agents: <slug> (search root absent)` / `ambiguous agents: <slug> matches [<path>, ...]` | `validate` | Missing: verify the agent file exists under `.claude/agents/` (the `(search root absent)` variant means the `.claude/agents/` dir itself is missing). Ambiguous: two+ files share the basename; rename one or pin a unique path. |
| `MANIFEST_E072` | `missing rules: <slug>` / `missing rules: <slug> (search root absent)` / `ambiguous rules: <slug> matches [<path>, ...]` | `validate` | Same as above (applies to `.claude/rules/`). |
| `MANIFEST_E073` | `missing hook: <name>` | `validate` | Provide full filename including extension. |
| `MANIFEST_E074` | `ambiguous hook: <name> matches <N> files; use a unique name or path` | `validate` | Two+ hook files share the basename; rename one or pin a unique path. Guards against a non-deterministic `rglob` pick. |
| `MANIFEST_E101` | `unsupported schema_version: <value>; this builder supports [<versions>]` | `validate` | Update release or migrate the manifest. |
| `MANIFEST_E102` | `schema_version must be a string; got <type>` | `validate` | Quote the value: `schema_version: "1.0"` (unquoted `1.0` parses as a float). |
| (raw parse) | `<path>:<line>:<col>: <yaml-problem>` | `load` | Fix YAML syntax at the indicated position. |

## Safety Errors (`scripts/safety_check.py`)

No hard errors raised at scan time. All "drops" are emitted as warn-level findings. The `--strict` flag is plumbed but currently has no qualifying conditions (reserved for future).

## Template Errors (`scripts/pack/templates.py`)

| Code | Message | Raised by | Remediation |
|------|---------|-----------|-------------|
| (no code) | `unknown template token(s): {{NAME}},...` | `render` | Add the missing token(s) to the dict passed to `render_template`, or remove the `{{NAME}}` from the template. |

## Collision Error (`scripts/pack/manifest_io.py`)

| Code | Message | Raised by | Remediation |
|------|---------|-----------|-------------|
| (no code) | `output exists: <path> (use --force to overwrite)` | `atomic_replace` | Either pass `--force` (backup made as `.bak.{epoch}`) or move the existing file aside. |

## `build_manifest.py` Exit Codes (`scripts/build_manifest.py --write`)

These codes apply ONLY to the `build_manifest.py` entry point and differ from `pack/cli.py`:

| Code | Condition |
|------|-----------|
| 0 | Success (manifest written). |
| 1 | Validation error — includes `manifest_loader.validate` failures and the stderr message `refuse to write outside repo root: <path>` (path would escape the repo root). |
| 2 | Collision — manifest file already exists; stderr: `manifest exists: <path> (use --force to overwrite)`. |

Note: `build_manifest.py`'s exit code 2 means collision; in `pack/cli.py` exit code 2 means strict-gate — the namespaces are distinct.

## Exit Codes (`scripts/pack/cli.py`)

| Code | Condition |
|------|-----------|
| 0 | Success. |
| 1 | Manifest load/validate error (any `MANIFEST_E###` above); also returned for `--all` (unimplemented in v0.1) and `TemplateError` (unknown `{{TOKEN}}` in an installer template). |
| 2 | `--strict` gate hit a `severity=error` finding. |
| 3 | Output exists, no `--force`. |
| 4 | Write error (disk full, permission denied, cross-fs replace failure). |
| 5 | Empty selection OR over-max-size. |
| 130 | SIGINT (Ctrl+C). |

## Quick-Reference Lookups

- "absolute paths not allowed" → `MANIFEST_E020` → remove leading `/` or drive letter.
- "missing skill" → `MANIFEST_E070` → check spelling and case.
- "nothing to pack" → exit 5 → manifest produced empty selection; check `skills`/`agents`/`rules`/`extra`.
- "unsupported schema_version" → `MANIFEST_E101` → update release.
