# safety-rules

The non-negotiable filter applied to every candidate path. **HARD**: no CLI flag, no manifest field, no override disables these rules. Implementation: `scripts/safety_check.py`.

Three layers + opt-in catalog + a warn-only `_shared/` policy.

## Layer 1 — `ALWAYS_DROP_EXACT` (basename match)

| Pattern | Why |
|---------|-----|
| `.env` | Environment vars; almost always secret. |
| `.envrc` | direnv config; may contain secrets. |
| `id_rsa`, `id_ed25519`, `id_ecdsa`, `id_dsa` | SSH private keys. |
| `.netrc` | curl/wget machine credentials. |
| `.pgpass` | PostgreSQL password file. |
| `metadata.json` | Anthropic skill runtime state (per-skill ephemeral). |
| `.DS_Store` | macOS Finder metadata. |
| `Thumbs.db` | Windows Explorer thumbnails. |
| `desktop.ini` | Windows folder customization. |

## Layer 2 — `ALWAYS_DROP_DIRS` (any path component match)

| Pattern | Why |
|---------|-----|
| `.git`, `.gitlab`, `.hg`, `.svn`, `.bzr` | VCS metadata — leak history + secrets. **CRITICAL**. |
| `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox` | Python build/lint caches. |
| `.venv`, `venv`, `node_modules`, `.npm`, `.yarn` | Vendored deps — huge + reproducible. |
| `.logs`, `session-state`, `agent-memory` | Claude Code runtime state — leaks transcripts. |
| `dist`, `build`, `target`, `.next`, `.turbo` | Build artifacts. |

Match rule: each component of the candidate path is checked against `ALWAYS_DROP_DIRS`. Substring matching is NOT used — `foo/legitimate-dir/bar` does not trigger `dir:dir`.

## Layer 3 — `ALWAYS_DROP_PATTERNS` (fnmatch glob)

| Pattern | Why |
|---------|-----|
| `**/.env.*`, `**/.env-*`, `**/.env_*` | `.env.local`, `.env-staging`, etc. |
| `**/secrets.*`, `**/credentials.*` | Credential files of any extension. |
| `**/*.pem`, `**/*.key`, `**/*.p12`, `**/*.pfx`, `**/*.jks` | TLS/Java keystores. |
| `**/id_rsa*`, `**/id_ed25519*`, `**/id_ecdsa*`, `**/id_dsa*` | SSH key variants (`id_rsa.pub`, `id_rsa.bak`). |
| `**/*.kdbx` | KeePass database. |
| `**/*token*.json`, `**/*secret*.json` | API tokens, generic secrets. |
| `**/*.pyc`, `**/*.pyo` | Python compiled bytecode. |

Patterns are matched against both the full arcname and the **basename**, so a top-level file (e.g. `deploy.pem` added via `extra`) is dropped just like a nested one. The patterns are intentionally broad and fail-safe: `secrets.*` / `credentials.*` match **any** extension (`.json`, `.yaml`, `.ini`, `.txt`, …). A consequence is that a documentation file literally named `secrets.md` or `credentials.md` will also be dropped — name such docs differently (e.g. `secret-handling.md`). Narrowing the patterns to an extension allowlist is deliberately avoided: it would let unanticipated secret formats (`secrets.ini`, `secrets.properties`) leak.

## Opt-In Catalog (`OPT_IN_PATHS`)

These paths only ship when the user explicitly passes a CLI flag.

| Path | Flag | Manifest equivalent |
|------|------|---------------------|
| `.claude/settings.json` | `--include-settings` | `top_level.include_settings: true` |
| `.claude/.ck.json` | `--include-ck-config` | `top_level.include_ck_config: true` |

Match anchored: `path == key` OR `path.endswith("/" + key)`. No substring matching.

## `_shared/` Policy (warn-only)

When a packed skill's `SKILL.md` references `_shared/<name>`, pack emits:

```
WARN: skill <skill-id> references _shared/<name> — use --include-shared <name> to include
```

**Default behavior:** the `_shared/<name>` subtree is NOT included. Recipient may extract the bundle and manually add the dependency, or the publisher passes `--include-shared <name>` to bundle it.

Fenced markdown code blocks (` ``` `... ` ``` `) are stripped before regex match — references inside fenced examples don't trigger warnings.

Lowercase enforced (`_shared/<name>` regex `[a-z0-9_-]+`). Uppercase `_shared/Foo` silently skipped — document the lowercase convention in your repo.

## Adding a New Rule

1. Decide which layer fits (exact basename, any-dir, fnmatch glob).
2. Add to the corresponding `frozenset` / `tuple` in `safety_check.py`.
3. Add a row to this document with a rationale (don't expand the catalog silently).
4. Add a pytest case under `scripts/tests/test_safety_check.py`.
5. Bump CHANGELOG with the new rule under `### Added`.

## What Safety Does NOT Block

- Public configs (`.gitignore`, `.editorconfig`) — these are deliberately shipped.
- General markdown (`*.md`) — even if it accidentally contains a token, that's the user's authoring problem; not detectable by filename.
- Binary files — no content scanning. Use a separate secret scanner before publishing if needed.
