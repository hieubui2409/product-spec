# claude-pack — Production-Readiness Review

Reviewer: code-reviewer · Date: 2026-05-29 · Scope: `.claude/skills/claude-pack/` (untracked working tree)
Verdict: **FIX-FIRST** (1 CRITICAL secret-leak + 2 IMPORTANT contract violations before ship)

Test baseline: `pytest -m "not integration"` → 57 passed. Determinism verified byte-identical via real CLI subprocess across runs. All 19 `.py` compile clean; restoration left no dropped-`()` / collapsed-double-space damage. SHA256 sidecar is correct two-space coreutils format (verified with `sha256sum -c`).

---

## CRITICAL

### C1. Safety filter misses ALL top-level secrets — `*.pem`/`*token*.json`/`.env.*` at repo root LEAK
`scripts/safety_check.py:47-57` (`ALWAYS_DROP_PATTERNS`) + `is_dropped` at `:94-96`.

**Problem.** Every glob is `**/`-prefixed (`**/*.pem`, `**/*.key`, `**/*token*.json`, `**/*secret*.json`, `**/.env.*`, `**/id_rsa*`, `**/*.p12` …) and matched with `fnmatch.fnmatchcase(path, glob)` against the **full arcname**. In `fnmatch`, `**/` requires a literal `/` in the path, so a top-level file with no slash never matches.

Verified end-to-end through `resolve_selection` with `extra: ["deploy.pem","prod-token.json",".env.production","certs"]`:
```
SECRETS LEAKED INTO BUNDLE: ['.env.production', 'deploy.pem', 'prod-token.json']
```
(`certs/server.key` was correctly dropped — it has a slash.) `id_rsa.bak`, `my.p12`, `client-secret.json`, `server.key` at repo root all leak the same way. `.env.production` leaks because basename `.env.production` is not in `ALWAYS_DROP_EXACT` (only `.env` is) and the `**/.env.*` pattern needs a slash.

**Why it matters.** Directly violates the stated HARD invariant ("must drop `*.pem`/`*.key`/keystores, `*token*.json`/`*secret*.json`" and "a path placed in `extra` STILL gets dropped if it matches"). The whole point of the filter is that no manifest/flag can leak secrets; the realistic vector (`extra:` pointing at a repo-root key/token, or a stray `.env.production`/`deploy.pem` in the repo) bypasses it silently. Both defense layers (`selection.py:80-83` and `tarball.make_normalize_filter`) call the same `is_dropped`, so both miss it.

**Why tests didn't catch it.** `test_safety_check.py:32-46` only feeds patterns with a directory prefix (`foo/secrets.json`, `baz/cert.pem`, …). Golden tests assert "no `.env` leaked" but never plant a top-level `.pem`/`token.json` to exercise the net. False green.

**Fix.** Match the **basename** against bare patterns, not the full path against `**/`-globs. Verified this catches top-level + nested and avoids false positives (`.envfoo`, `notes.pem.txt` stay):
```python
basename = p.name
BASENAME_GLOBS = ("*.pem","*.key","*.p12","*.pfx","*.jks","*.kdbx",
                  ".env.*",".env-*",".env_*","secrets.*","credentials.*",
                  "*token*.json","*secret*.json","*.pyc","*.pyo",
                  "id_rsa*","id_ed25519*","id_ecdsa*","id_dsa*")
for glob in BASENAME_GLOBS:
    if fnmatch.fnmatchcase(basename, glob):
        return True, f"always-drop:pattern:{glob}"
```
Keep `ALWAYS_DROP_EXACT` and `ALWAYS_DROP_DIRS` as-is (component match already correct). Add regression tests for bare top-level inputs: `is_dropped("deploy.pem")`, `is_dropped("prod-token.json")`, `is_dropped(".env.production")` must all drop; `is_dropped(".envfoo")`, `is_dropped("notes.pem.txt")` must not.

---

## IMPORTANT

### I1. INSTALL.md hardcodes `claude-pack-{VERSION}` — wrong filename for any custom `bundle_name`
`assets/templates/INSTALL.md.template:9,15,21,27` + `scripts/pack/cli.py:83-89` (token dict has no `BUNDLE_NAME`).

**Problem.** The verify/extract/cd commands are literally `claude-pack-{{VERSION}}.tar.gz`. But the actual artifact is `{bundle_name}-{version}.tar.gz` (`cli.py:104`, `bundle_root = f"{bundle_name}-{version}"`). `bundle_name` is a first-class, validated, `--bundle-name`-overridable field. If a recipient sets `bundle_name: my-pack`, the bundle is `my-pack-1.0.0.tar.gz` yet INSTALL.md tells them to run `sha256sum -c claude-pack-1.0.0.tar.gz.sha256` and `tar -xzf claude-pack-1.0.0.tar.gz` — both fail.

**Why it matters.** Recipient-facing install docs are wrong for any non-default bundle name; the verify-then-extract flow the skill advertises breaks. No `TemplateError` fires because the template never references a missing token — it's just hardcoded prose.

**Fix.** Add `"BUNDLE_NAME": manifest["bundle_name"]` to the tokens dict in `cli.py:_prepare_build`, and replace the four hardcoded `claude-pack-{{VERSION}}` occurrences in `INSTALL.md.template` with `{{BUNDLE_NAME}}-{{VERSION}}`. (The two installer templates only use `{{VERSION}}` in comments and are fine.)

### I2. `--strict` and `--all` are dead flags — advertised behavior never happens
`scripts/pack/args.py:35-36` (`--all`), `:60-61` (`--strict`); never read in `cli.py` / `selection.py` / `manifest_loader.merge_cli`. `EXIT_STRICT = 2` (`cli.py:30`) is defined but never returned.

**Problem.**
- `--all` help: "pack everything under .claude/ minus always-drop list." `merge_cli` doesn't read `args.all`; `resolve_selection` has no all-mode branch. Passing `--all` silently packs nothing extra (whatever the manifest already said).
- `--strict` help: "treat warnings as errors." `cli.py` never reads `args.strict`; the `_warn_shared_refs` warnings (`:46-55`) and per-file drop WARNs go to stderr and are always non-fatal. Exit code 2 is unreachable from the CLI.

**Why it matters.** Contract lists exit 2 = strict as a guaranteed exit code, and CI/release pipelines may rely on `--strict` to fail a build on unresolved `_shared/` refs. Both are false promises. `--all` is the more dangerous of the two because a user could believe `--all` is including their whole `.claude/` (and the safety net) when it includes nothing beyond the manifest.

**Fix (pick per intent).** Either implement them or remove them. Minimum: wire `--strict` so any emitted WARN (shared-ref or dropped-symlink/secret) returns `EXIT_STRICT`; implement `--all` in `resolve_selection` (walk `.claude/` minus always-drop) or delete the arg. Do not ship defined-but-ignored flags. NOTE: `strict_gate.py` is referenced in the project CLAUDE.md as the CI strict wrapper but does not exist under `scripts/` — confirm whether strict gating was descoped.

---

## MINOR

### M1. Recipient `install.sh` summary counters always print 0 (subshell pitfall)
`assets/templates/install.sh.template:69-114`.

`find … | sort | while … done` runs the loop body in a subshell, so `ADDED/SKIPPED/OVERWROTE/STALE/NEWER` increments are lost; the Summary always reports zeros. Verified live: file copied (`[+] .claude/skills/demo/SKILL.md`) but `Added: 0`. **Files still install correctly** — only the summary is wrong (cosmetic). The PowerShell version uses `ForEach-Object` in caller scope, so it is unaffected.
Fix: feed the loop via process substitution to keep it in the parent shell — `while IFS= read -r REL; do … done < <(find .claude -type f | sort)`.

### M2. Plan-artifact reference in shipped code ("Phase 5 creates this")
`install.sh:82` and `install.ps1:83`: `fail "requirements-dev.txt missing … (Phase 5 creates this)"`.
Violates project rule "no plan-artifact refs (phase numbers) in code". `requirements-dev.txt` exists now, so the message is also stale. Reword to e.g. "requirements-dev.txt missing — reinstall the skill or create it".

### M3. `max_size` doc says "uncompressed", code measures compressed
`assets/templates/manifest.example.yaml:52` comment "100 MB (uncompressed)"; `cli.py:113` checks `tmp_path.stat().st_size` (the gzip). `args.py:58-59` help correctly says "compressed". Align the example comment to "compressed".

### M4. `extra` path validation misses Windows UNC / backslash-root
`manifest_loader._is_absolute_or_drive:142-150` returns False for `\\server\share` and `\foo`. Low real-world risk (build runs on author's POSIX host; path must exist to pack), but it's an absolute-path completeness gap. Optionally also reject leading `\`/`\\`.

### M5. Stale doc refs in example manifest
`manifest.example.yaml:29-30` references `--merge-hooks` "(not yet built)" — flag doesn't exist anywhere. Drop the speculative mention.

---

## Positive Observations

- **Determinism is genuinely solid.** PAX, file-granular sort by `arcname.encode("utf-8")`, `uid/gid=0`, `uname/gname=""`, gzip `mtime=0`, `built_at` derived from epoch (default `1970-01-01T00:00:00+00:00`). Verified embedded + real files share mtime uniformly under a non-zero epoch; two real-CLI runs are byte-identical. No `datetime.now()`/random/unordered-set leak in the build path (the only `datetime.now()` is in `safety_check.main`'s `scanned_at`, which is a standalone scanner not part of the tarball).
- **Atomic write correct**: `.tmp` → `os.replace`, EXDEV fallback, tmp unlinked on every exception branch, collision→exit 3, force backs up to `.bak.{epoch}`, stale `.*.tmp` >1h cleaned on startup. Well tested.
- **`merge_cli` is clean** — `None` = no override honored; does NOT inject `out`/`all`/`strict` or any unknown key, so the E060 unknown-key validator won't trip from CLI flags.
- **`BooleanOptionalAction(default=None)`** precedence correct and tested both directions.
- **Symlink/hardlink rejection** in the tarball filter is unconditional and tested.
- **Restoration was clean** — no syntax damage, sidecar two-space separator intact and coreutils-verified.
- Modularization budget met: every `scripts/pack/*.py` < 200 LOC (largest `cli.py` 194).
- Stable `MANIFEST_E###` codes used throughout validation (allowed).

---

## Metrics
- pack/*.py LOC: all < 200 (cli 194, tarball 145, manifest_io 141, selection 115, args 77, templates 43, __init__ 20, __main__ 11)
- Tests: 57 pass (non-integration); +1 integration (skipped unless `-m integration`)
- Compile: 19/19 `.py` OK
- Type coverage: n/a (no annotations gate configured)

---

## Unresolved Questions
1. Were `--all` and `--strict` intended for this version, or leftover scaffolding? Implement vs delete is a product call.
2. The task brief lists `.github/workflows/claude-pack-{ci,release,integration}.yml` — none exist in the tree. Descoped, or not yet committed? Determinism/strict-gate guarantees that a release pipeline would enforce are currently unverified by CI.
3. Project CLAUDE.md references `strict_gate.py` (CI wrapper, exit 2 on error findings) — not present under `scripts/`. Confirm whether strict gating moved to the (missing) workflows or was dropped; relates to I2.
4. Is `metadata.json` exact-drop intended to be unconditional? It will silently drop any skill that legitimately ships a `metadata.json` artifact. Per the catalog it's deliberate (Claude runtime state), just flagging the blast radius.
