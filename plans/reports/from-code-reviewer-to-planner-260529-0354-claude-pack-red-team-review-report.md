---
title: "claude-pack red-team review"
from: code-reviewer
to: planner
plan: plans/260529-0343-claude-pack-skill/
date: 2026-05-29
severity_legend: "CRITICAL (block ship) · HIGH (fix before /ck:cook) · MEDIUM (fix in v1) · LOW (defer/accept) · OBSERVE (note for future)"
---

# Red-Team Review — `cleanmatic:claude-pack`

Stress-tested plan.md + phase-01..06.md against 17 attack surfaces. Findings grouped by attack surface (Q-numbers map to user's prompt). Citations use `phase-NN:line` or `plan.md:line`.

Bottom line: **plan is solid in shape, leaky in determinism + safety + manifest schema**. ~8 findings are HIGH-or-above and must be resolved before `/ck:cook`. The dominant risk class is **silent data exposure via underspecified matchers** (Q2) and **non-byte-identical builds** (Q1, Q7) — both directly violate the plan's marquee guarantees.

---

## Q1 — Determinism guarantee

### F1.1 — HIGH — `os.walk` ordering not normalized; phase-02 sort happens too late

phase-02:104 says "Sort — `sorted(selection, key=lambda t: t[1])` (sort by arcname)". But the *selection list* is built in step 3 from manifest-category mappings (selecting whole skill dirs). The actual per-file walk inside each selected dir is *not specified* — `tar.add(skill_dir, ...)` with no recursive filter+sort defers to tarfile's internal walk, which **prior to Python 3.7 was unsorted**, and since 3.7 sorts by *bytes of basename within each directory*, not full path globally. Researcher A's skeleton (`os.walk` lines 76-83) wraps both `dirnames.sort()` and `sorted(filenames)`, but phase-02 inherits only the outer arcname sort.

What could fail: Two boxes with different `os.walk` order (rare on modern Linux, observed on some NFS mounts + macOS APFS) produce different intra-skill ordering → different SHA256 → T-D1 fails.

Fix: phase-02 step 3 must produce a **flat (src, arcname) list at file granularity**, sorted globally by arcname-bytes. Then use `tar.addfile()` per entry, not `tar.add(dir, ...)`. Document explicitly: "no `tar.add(directory)` calls; always per-file addfile with explicit TarInfo." Update phase-02:R2 mitigation to apply to all entries, not just non-ASCII.

### F1.2 — HIGH — locale-dependent sort risk

phase-02:R2 says `key=lambda t: t[1].encode("utf-8")` for non-ASCII. Good — but the rest of phase-02 step 6 just says `sorted(selection, key=lambda t: t[1])` (string sort). On systems with `LC_COLLATE=C.UTF-8` vs `LC_COLLATE=en_US.UTF-8`, Python's `sorted()` of strings does **not** consult locale (Python 3 sorts by codepoint), so this is actually safe — but the plan's mitigation reads as if it isn't. Spec ambiguity will cause the implementer to over-engineer.

Fix: phase-02 step 6 — replace with `sorted(selection, key=lambda t: t[1].encode("utf-8"))` everywhere; delete R2 mitigation as redundant.

### F1.3 — MEDIUM — symlink behavior contradicts phase-02:R6 statement

phase-02:R6 says "tarfile.add() default follows them — explicitly use `dereference=False`". **Wrong.** `tarfile.add(name, ...)` does NOT follow symlinks by default; the symlink is added as a symlink member. The actual switch is the TarFile constructor's `dereference=False` (default). Researcher A's filter never sets this.

What could fail: A symlink in a packed skill (e.g., `.claude/skills/foo/data → /etc/passwd`) gets recorded as a symlink member. When recipient extracts with default `data` filter (Python 3.12+), `data_filter` blocks absolute symlink targets → OK. But on Python 3.11 or with `fully_trusted` filter, recipient creates symlink pointing to `/etc/passwd` on their machine — attack vector.

Fix: phase-02 normalize_filter explicitly: `if tarinfo.issym() or tarinfo.islnk(): return None` and emit `WARN: dropped symlink {name} → {target}`. Update phase-02:R6 wording: "tarfile records symlinks as symlinks by default; we reject them entirely." This is also a Q2 safety boundary item.

### F1.4 — MEDIUM — gzip mtime verification command is wrong

phase-02:11 says verify via `od -An -tu1 -N10 tarball.tar.gz | awk '{print $5,$6,$7,$8}'`. Bytes 5-8 of gzip header are mtime (correct), but `-N10` reads 10 bytes and `$5..$8` skips magic + cm + flg. T-D4 (phase-05:161) says "bytes 4-8 of gzip header, assert `b"\x00\x00\x00\x00"`". Off-by-one: gzip mtime is bytes **4-7 (0-indexed)** = bytes **5-8 (1-indexed)**. Plan mixes both; tests will be flaky depending on implementer's interpretation.

Fix: phase-05 T-D4 — write byte-precise: `data[4:8] == b"\x00\x00\x00\x00"` (0-indexed slice, 4 bytes). phase-02:11 — align verification command. Add to test docstring.

### F1.5 — LOW — Python 3.11 vs 3.12 vs 3.13 gzip output differences

CPython 3.14+ defaults `gzip.GzipFile` to `mtime=0` in some contexts. Earlier versions emit current time unless explicit. Plan correctly wraps with explicit `gzip.GzipFile(mtime=0)`, but doesn't pin Python version. T-D1 on a CI matrix with 3.11 + 3.12 + 3.13 may produce different SHA256 across versions due to gzip implementation drift (header field defaults differ; flag byte semantics differ).

Fix: phase-05 T-D1 — restrict determinism gate to *same Python version*; add Python version to MANIFEST.json or pin minimum in `requirements.txt` (`python_requires=">=3.11"`). Document in `references/manifest-spec.md` that byte-identical guarantee is intra-version only.

### F1.6 — OBSERVE — case-sensitivity (HFS+ vs ext4)

If a maintainer develops on macOS HFS+ (case-insensitive) and a contributor on ext4 (case-sensitive), `sorted()` order is identical (Python codepoint), so byte-identity holds. But a filesystem that **silently normalizes** Unicode (HFS+ NFD vs ext4 NFC) will produce different arcnames → different SHA256. Plan does not mention this.

Fix: phase-02 add note: "filenames containing non-ASCII characters may produce different SHA256 across NFC/NFD filesystems; recommend ASCII-only filenames in `.claude/`."

---

## Q2 — Safety filter robustness

### F2.1 — CRITICAL — `is_dropped` matching logic is underspecified; path traversal bypass possible

phase-03:33 says `is_dropped` checks "exact basenames (`.env`, `metadata.json`), directory names (`__pycache__`)". phase-03 step 2 says "normalize with `pathlib.PurePosixPath`; check basename in exact set; check any path component in dir set". **Two gaps:**

1. **No path normalization before component check.** `extra: ["./.claude/skills/foo/../.env"]` → `PurePosixPath` does NOT collapse `..` (that's `os.path.normpath` or `resolve()`). The path components are `[".claude", "skills", "foo", "..", ".env"]`; basename is `.env` — ✅ this case is caught by exact basename. But `extra: ["legit/.envconfig"]` → basename `.envconfig`, NOT in `{".env"}` set → ✅ passes (correctly, since `.envconfig` is not necessarily a secret). HOWEVER:

2. **Glob `**/.env.*` only matches files like `.env.local`, NOT `.envrc`, NOT `.env_prod`, NOT `.env-staging`.** The always-drop list in plan.md:40 includes `.env` (exact); researcher A's draft (skeleton lines 521-527) used `{'.env'}` only. Real-world secrets files include `.envrc` (direnv), `.env.production`, `.env.local`, `dotenv`, `env.sh`, `secrets.json`, `credentials.json`, `*.pem`, `*.key`, `id_rsa`, `*.p12`. None except `.env` are in the spec.

What could fail: Developer's `.claude/scripts/load-env.sh` references `.env.production` in repo root; manifest `extra: [".env.production"]` (mistakenly). Filter does NOT drop. Tarball ships secrets.

Fix: Expand `ALWAYS_DROP_EXACT` and `ALWAYS_DROP_PATTERNS` to industry-standard secret patterns:
```
ALWAYS_DROP_EXACT = {".env", ".envrc", "metadata.json", ".DS_Store",
                     "id_rsa", "id_ed25519", "id_ecdsa", ".netrc", ".pgpass"}
ALWAYS_DROP_PATTERNS = ["**/.env.*", "**/.env-*", "**/.env_*", "**/secrets.*",
                        "**/credentials.*", "**/*.pem", "**/*.key", "**/*.p12",
                        "**/*.pfx", "**/*.jks", "**/id_rsa*", "**/id_ed25519*"]
```
phase-02 security section claims "Filter callback drops `.env`, `secrets.*`, `credentials.*` even if user explicitly lists them" — but `secrets.*` and `credentials.*` are NOT in phase-03's constant list. **Direct spec contradiction between phase-02 and phase-03**. Reconcile.

### F2.2 — CRITICAL — substring-match risk on directory check

phase-03 step 2: "check any path component in dir set". If implemented naively as `if "__pycache__" in path.parts`, that's correct. If implemented as `if "__pycache__" in path` (string), then `path = "myskill/not__pycache__test/foo.py"` → match → false positive drop. Conversely if implemented as `if path.endswith("__pycache__")`, then `__pycache__/x.pyc` doesn't end with `__pycache__` → false negative.

phase-05 T-S2 only tests `__pycache__/x.pyc` — does not cover deep nesting (e.g., `.claude/skills/foo/scripts/__pycache__/bar.pyc`). T-S3 only tests `docs/dev.md` — does not cover near-miss strings.

Fix: Spec phase-03 step 2 exactly: `if any(p in ALWAYS_DROP_DIRS for p in PurePosixPath(path).parts): return (True, f"always-drop:dir:{p}")`. Add T-S6, T-S7: deep-nested `__pycache__`, near-miss string `not__pycache__test`, mixed-case `__Pycache__` (case-insensitive fs).

### F2.3 — HIGH — opt-in matcher is path-prefix-anchored to `.claude/` only

phase-03 `OPT_IN_PATHS = {".claude/settings.json": "settings", ".claude/.ck.json": "ck-config"}`. If user runs `pack.py` from a subdirectory or with `--root /other/path`, arcname may not start with `.claude/`. Or if multiple settings.json files exist in different `.claude/` subtrees (none documented, but possible in nested projects).

Plan doesn't specify whether `is_optional` matches by exact arcname, suffix, or basename. T-S* tests don't cover this.

Fix: phase-03 — spec exact match semantics: `OPT_IN_PATHS` is a dict of arcname-suffix matches (`path.endswith(key) and len(path) == len(key) or path[len(path)-len(key)-1] == "/"`). Add test.

### F2.4 — HIGH — UTF-8 normalization bypass

`is_dropped(".env")` does basename match against literal `.env`. But on filesystems with NFD normalization, a file named `.énv` (NFD) ≠ `.env`. Less interesting attack vector here (developer doesn't accidentally create `.énv`), but the documented protection should clarify it doesn't cover non-ASCII variants of secret filenames.

Fix: phase-03 reference doc — explicit note: "matching is exact-byte; Unicode-confusable filenames are not detected. Use canonical ASCII basenames."

### F2.5 — MEDIUM — symlink to `.env` outside the tree

User manifests `extra: ["docs/config.env"]` which is a symlink to `../.env`. If `tarfile.add(follow_symlinks=True)` (default for `add`, NOT for filter callback — verify), the symlink is dereferenced and `.env` contents are packed under the arcname `docs/config.env`. The `is_dropped("docs/config.env")` check sees `docs/config.env` — not in ALWAYS_DROP. Tarball ships secrets.

Per F1.3, plan must reject symlinks entirely. Make this explicit: even if filter passes by arcname, the resolved-content must be checked. Simpler: refuse to dereference any symlink and skip with WARN.

Fix: Combined with F1.3 — drop all symlinks early in normalize_filter, before name match.

### F2.6 — LOW — case `.envfoo` (substring concern from prompt)

Not a real risk if matchers are strictly basename-exact and component-exact (as F2.2 spec'd). But the plan's wording is ambiguous enough that a careless implementer might use `.startswith(".env")` and accidentally drop legitimate files (`.env-example`, `.envrc.sample`) — false positives that hurt UX without security benefit.

Fix: Test cases in phase-05 must include both:
- `.envfoo` → NOT dropped (legitimate file, no match)
- `.env-example` → may be dropped or not (PO decision; recommend NOT, since it's a template)

---

## Q3 — Atomic write claim (Windows)

### F3.1 — HIGH — `pack.py` Windows support is undefined

phase-01 says install.sh + install.ps1 for *recipient*. But does `pack.py` itself run on Windows? Plan never says. phase-02:R3 uses `os.rename` which **fails on Windows if target exists**. phase-02 step 10 says "build tarball into `tmp`; `tmp.write_bytes(...)` + `os.fsync`; `os.rename(tmp, final)`" — `os.fsync` requires fd, not path; `tmp.write_bytes()` is `pathlib.Path` syntax, not the `tar.open()` flow.

phase-02 step 13 says "with `--force`: rename existing to `{name}.bak.{epoch}` before write" — partial mitigation, but the rename of `tmp → final` still fails on Windows even after backup, because Windows `os.rename` errors if target exists *and* the operation isn't `os.replace`.

What could fail: Windows developer runs `pack.py` → tarball builds into `.tmp`, rename fails with `FileExistsError`, no tarball produced. With `--force`, backup succeeds but rename still fails (race on `--force --no-overwrite-after`).

Fix:
1. phase-02 — replace `os.rename` with `os.replace` (atomic on POSIX *and* Windows, overwrites silently).
2. Plan clarify: "pack.py supports POSIX + Windows. Tested only on POSIX in CI; Windows is best-effort." OR explicitly: "pack.py is POSIX-only; Windows recipients install via PowerShell installer but cannot build packs."
3. phase-02 step 10 — clean code path: `with open(tmp_path, "wb") as f: ...; f.flush(); os.fsync(f.fileno()); f.close(); os.replace(tmp_path, final_path)`.

### F3.2 — MEDIUM — `.tmp` file leaked on exception

phase-02 step 10 atomic-rename narrative doesn't include `try/finally`. If `tarfile.open()` raises mid-write, `tmp` file stays around forever. Phase-05 T-D7 ("SIGTERM") only verifies `not final.exists()`, not `.tmp` cleanup.

Fix: phase-02 — wrap in `try: build → fsync → replace except: os.unlink(tmp) if exists; raise`. Update T-D7 to also assert `.tmp` is cleaned (or document that `.tmp` is left for debugging and `--force` cleans it on next run).

### F3.3 — LOW — atomic across filesystems

phase-02:R3 acknowledges `--out` to a different filesystem breaks atomicity. Acceptable. But the failure mode (cross-fs `os.replace` raises `OSError`) should be detected and either fall back to copy+remove or error out clearly.

Fix: phase-02 — catch `OSError` on replace; if errno indicates cross-fs, use `shutil.move` and warn "atomic guarantee disabled".

---

## Q4 — Manifest schema completeness

### F4.1 — HIGH — Empty manifest defaults to dangerous `0.0.0-dev`

phase-03 `apply_defaults`: missing version → `"0.0.0-dev"`. phase-06 step 5 hardcodes seed manifest with `"0.1.0"` (good). But if a user runs `pack.py --manifest empty.yaml` (manifest exists but version omitted), they get `claude-pack-0.0.0-dev.tar.gz`. Released bundles with `0.0.0-dev` in filename are confusing and may be silently uploaded to GitHub Releases.

Plan principle phase-02:R5 says "pack.py never *reads* SOURCE_DATE_EPOCH" — but the version field has no such safeguard.

Fix: phase-03 `validate` — if `version == "0.0.0-dev"` AND no `--version` CLI override provided AND not `--allow-dev-version`, return validation error "refuse to build with placeholder version". phase-06's "When to Ask vs Assume" already says "Never assume: bundle version (refuse to use `0.0.0-dev` for tagged releases)" — but never propagated to actual validation logic.

### F4.2 — HIGH — semver regex too narrow, breaks SemVer 2.0.0 build metadata

phase-03 step 3: `r"^(?:\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?|0\.0\.0-dev)$"`. SemVer 2.0.0 allows `+build.1` build-metadata suffix (`1.0.0-beta+exp.sha.5114f85`). Regex rejects it. Also rejects upper-case in prerelease (e.g., `1.0.0-RC.1`).

What could fail: User edits manifest to `version: "1.0.0+build.42"`, runs pack → validate error → confusing message.

Fix: phase-03 — adopt full SemVer 2.0.0 regex (or document subset explicitly). Recommended: `r"^(?:\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?|0\.0\.0-dev)$"`.

### F4.3 — MEDIUM — duplicate skills in list

`skills: ["product-spec", "product-spec"]` — plan doesn't say dedupe or error. Selection step 3 maps each to same dir; pack would attempt to `addfile` the same arcname twice → tarfile may raise or silently include twice → byte-identity broken.

Fix: phase-03 `validate` — `if len(set(L)) != len(L): return [f"duplicate entries in {field}: {dupes}"]`. OR `apply_defaults` silently dedupes; pick one and spec.

### F4.4 — MEDIUM — case-sensitivity on filesystem

`skills: ["Product-Spec"]` on case-sensitive fs (Linux) → `.claude/skills/Product-Spec` does not exist → silent skip (depends on phase-02 step 3 behavior — undefined). On case-insensitive fs (macOS HFS+, Windows NTFS), maps to `.claude/skills/product-spec` silently.

Fix: phase-02 step 3 — fail-fast: if `(repo_root / ".claude/skills" / slug).is_dir()` is False, exit 1 with "missing skill: {slug}". This catches both case mismatches and typos.

### F4.5 — CRITICAL — absolute paths in `extra` not rejected

`extra: ["/etc/passwd"]`. Plan says "list of paths relative to repo root" but no enforcement. phase-03 `validate` only checks "list of non-empty strings". phase-02 step 3 says `extra: [docs/dev.md] → preserve relative path` — no rejection of absolute.

What could fail: Manifest authored with absolute path → pack reads `/etc/passwd` (if readable) → ships in tarball. Trust-boundary violation.

Fix: phase-03 `validate` — `if path.startswith("/") or ":" in path[:3]: error("absolute paths not allowed")`. Also reject `..` traversal: `if ".." in PurePosixPath(p).parts: error("path traversal not allowed")`. Add tests.

### F4.6 — MEDIUM — `top_level` unknown keys silently ignored

phase-03:R3 says "allow extra keys with `warn`-level finding". But schema says `top_level` is a dict with bool fields. If user types `top_lvl: {include_readme: true}` (typo), validator might not flag — silent regression (README not included).

Fix: phase-03 `validate` — strict check on top-level keys: known set = `{schema_version, version, bundle_name, skills, agents, hooks, rules, extra, top_level, follow_shared}`; unknown emit `warn`. For nested `top_level`, known set = `{include_readme, include_claudemd, include_settings, include_ck_config}`; unknown emit `warn`. Test phase-05 T-M2 covers "unknown top-level keys" but not nested.

### F4.7 — LOW — `bundle_name` validation missing

Manifest can set `bundle_name: "../etc/passwd"` → output filename `dist/../etc/passwd-1.0.0.tar.gz` → writes outside `dist/`. Or `bundle_name: " "` (whitespace).

Fix: phase-03 `validate` — `bundle_name` must match `r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$"`. Same for the `{stem}` in CLI override.

---

## Q5 — Dep grep (`_shared/`)

### F5.1 — HIGH — false positive in code blocks / docs / vendored content

phase-03:R2 says "vendored mermaid.min.js produces false positive; restrict grep to SKILL.md only". But SKILL.md *also* has code blocks. Example: a SKILL.md that documents "if a skill references `_shared/foo` it must include the dep" — the doc itself triggers the grep, auto-including `_shared/foo` even though that skill doesn't use it.

Researcher B's audit (not read in detail but cited) likely flagged this. Current spec defers.

Fix: phase-03 step 4 — strip fenced code blocks before regex; OR restrict regex to only match `_shared/` references *outside* fenced markdown blocks; OR (simpler) make `follow_shared` produce a `warn` finding, not auto-inclusion; PO can opt-in via CLI `--include-shared <list>`. **This contradicts plan.md:42** ("Auto-include + warn") but is safer.

### F5.2 — MEDIUM — transitive `_shared/` not resolved

If `_shared/foo/SKILL.md` references `_shared/bar`, phase-03 follow_shared returns only `foo`. `bar` is silently missing.

Fix: phase-03 step 4 — iterate `follow_shared` until fixed point (`while new_set: scan new dirs for more refs`). Bound depth to 10 to prevent cycles. Add T-S5b for transitive case.

### F5.3 — MEDIUM — referenced `_shared/x` doesn't exist on disk

Skill SKILL.md mentions `_shared/legacy_thing` (stale reference). phase-03 step 4 says "check `shared_root / name` exists; if yes, append". If no, currently silent skip. Better: emit `warn` finding so PO knows the SKILL.md has stale refs.

Fix: phase-03 step 4 — if `not (shared_root / name).is_dir()`: emit `{"check": "shared_dep_missing", "severity": "warn", "referring_skill": ..., "missing": name}`.

### F5.4 — LOW — regex character class too narrow

`r"_shared/([a-z0-9_-]+)"` rejects uppercase dirs (`_shared/Foo`). If convention allows uppercase, this silently misses. If convention forbids, fine.

Fix: phase-03 — add note that `_shared/<NAME>` must be lowercase-kebab. Reject uppercase in `validate` or add `[A-Z]` to regex.

---

## Q6 — Versioned root dir + recipient install

### F6.1 — HIGH — installer skip-existing leaves stale version, no detection

Researcher A's install.sh (line 333-344) does `[SKIP] $dst (exists)`. phase-06 step 9 sandbox installs to `/tmp/cp-recipient` — clean dir, no clash. But real recipients with prior install have `.claude/skills/product-spec/` from v0.9 → installer of v1.0 reports `[SKIP]`, recipient runs old code, thinks they upgraded.

Fix: install.sh.template (Phase 1) — before each `[SKIP]`, read existing `MANIFEST.json` (or per-skill `SKILL.md` version frontmatter) and compare. If newer-in-tarball: emit `[STALE] existing v0.9 < bundled v1.0; use FORCE_OVERWRITE=1 to upgrade`. If same: `[OK SAME] v1.0 already installed`. If recipient installed newer: `[NEWER] recipient v1.1 > bundled v1.0; refusing to downgrade`.

This requires installer to know how to read versions. Alternative simpler fix: installer prints a warning summary at end listing all SKIPs and recommends `FORCE_OVERWRITE=1` for upgrades.

### F6.2 — MEDIUM — no version-clash detection at MANIFEST level

phase-06:R4 acknowledges chicken-and-egg but only for the build side. Recipient side: if v0.1 of claude-pack is already installed and recipient extracts v0.2 tarball, no detection happens.

Fix: install.sh — read recipient's `.claude/skills/claude-pack/SKILL.md` frontmatter `metadata.version`; compare to `MANIFEST.json:bundle_version`; emit ASCII banner with comparison.

---

## Q7 — SOURCE_DATE_EPOCH leak (spec drift)

### F7.1 — HIGH — direct contradiction: phase-02:R5 vs researcher A skeleton

phase-02:R5 says "pack.py never *reads* SOURCE_DATE_EPOCH from environment unless user passes `--reproducible`". But researcher A's skeleton (line 56, 526, 571) reads `int(os.environ.get('SOURCE_DATE_EPOCH', '0'))` directly.

Two implementers will read these and write different code:
- Implementer A (reads phase-02:R5): hardcodes `mtime = 0` unless `--reproducible` flag set.
- Implementer B (reads researcher A): always uses env var if present.

If `--reproducible` flag is supposed to *opt in* to env-var consumption (which is the inverse of what's stated — `--reproducible` should *force* env var, or default value), the semantics are muddled.

Fix: Plan must lock the semantics explicitly. Recommendation:
- **Default behavior:** `pack.py` always uses `mtime=0` (most-deterministic, ignores environment).
- **`--reproducible-from-env` flag:** opts into `SOURCE_DATE_EPOCH` if set; falls back to 0 if not. (Better name: `--source-date-epoch <int>` or `--source-date-epoch env` to be explicit.)
- Delete the contradictory phase-02:R5 language; write phase-02 step 11 to spec explicit env-var handling.

Currently this is the **biggest spec-drift item**. Cook agent will choose wrong.

---

## Q8 — Interactive flow gaps

### F8.1 — MEDIUM — no session state for interactive resume

product-spec saves `.session.md` for resume. claude-pack plan-04 step 5 says explicitly "no partial file written" if PO aborts. But PO has already answered 3 of 4 batches — answers are lost. PO has to start over.

For a 4-batch interview, this is annoying but tolerable. For an LLM-driven flow with `AskUserQuestion`, the LLM context already holds the answers, so resume = "I have your answers from batches 1-3, ready for batch 4?" — no file needed.

Fix (option A — defer): document in workflow-pack.md: "if you abort mid-interview, all answers are lost. Run again from scratch." Acceptable for v1 given small batch count.

Fix (option B — implement): build_manifest.py adds `--save-partial /tmp/cp-session.json` flag; on `--write`, accept stdin or `--from-partial` flag. Defer to v1.1.

phase-04 R3 mentions overwrite-prompt at start of interactive run. Adequate for v1.

### F8.2 — LOW — JSON-over-stdin contract not idempotent if LLM retries

`build_manifest.py --write` reads stdin → parses → writes. If LLM's first attempt errors (validation fails), LLM may re-invoke with corrected JSON. If `--force` not set and previous attempt wrote (it shouldn't, validation precedes write per phase-04 step 3) — wait, validate-before-write is correct. OK.

Fix: phase-04 step 3 — add explicit note: "validation precedes write; failed validation leaves no file written; re-run with corrected JSON is safe."

---

## Q9 — Test flakiness

### F9.1 — HIGH — T-D7 mock vs SIGTERM mismatch

phase-05:R2 says "instead of timing-based test, mock `tarfile.open` to raise after first addfile; assert atomic rename did not happen". But the failure mode this is supposed to detect is **process killed mid-write** — that's the OS, not Python code raising.

Mocking `tarfile.open` to raise after first addfile tests:
- The exception path in pack.py code.
- Whether cleanup runs.

It does NOT test:
- Whether `os.fsync` was actually called before the rename.
- Whether crash *between* tarball-close and rename leaves a `.tmp.tar.gz` that looks complete but isn't atomic.

The real test for SIGTERM-style atomicity requires either:
- Subprocess + signal (the original phase-05:T-D7 wording — flaky but correct).
- Filesystem trace (e.g., `strace` for syscall order) — overkill.

Fix: phase-05 T-D7 — keep subprocess approach but with deterministic trigger:
- Set `pack.py` to honor `PACK_KILL_AFTER_N_FILES=3` env var (debug-only); when set, raise `SystemExit(137)` after Nth `addfile`.
- Test invokes subprocess with env var; asserts `.tmp` may exist, `final` does NOT.
- Document this as a debug-only env var; never document for users.

Plus: keep the mock test (T-D7b) for exception-path validation, separately labeled.

### F9.2 — MEDIUM — T-S4 (hard safety) has no negative-path test

T-S4 tests: `.env` in `extra` is dropped. Doesn't test: `.env` in `skills/foo/.env` (transitively included via skill selection). Doesn't test: `.env` inside a `_shared/` dep that was auto-added. Doesn't test: `.env` in a path with mixed-case (`.ENV`).

Fix: phase-05 — add T-S4b (transitive via skill), T-S4c (transitive via `_shared/`), T-S4d (case-insensitive: `.ENV`, document expected behavior).

### F9.3 — LOW — test runtime budget too tight

phase-05:R1/non-functional says "Tests run in <5s total". 17 tests including a golden-extract test reading 42-file tarball is likely <2s on dev machines, but CI runners with cold cache or slow IO may breach 5s. Recommend 15s budget.

Fix: phase-05 — relax to `<15s` for full suite, `<10s` excluding golden, `<5s` for hot path (test_safety_check + test_manifest_loader). Update phase-05:NF and Success Criteria.

---

## Q10 — Golden test stability

### F10.1 — HIGH — golden = `cleanmatic:product-spec` source → product-spec edits break claude-pack CI

phase-05:T-G1 packs product-spec; CI fails on file-tree drift. Typo fix in `product-spec/SKILL.md` → golden mismatch → claude-pack CI red → cross-skill coupling.

Fix options:
- **A (best):** Golden = synthetic minimal fixture in `scripts/tests/fixtures/sample-skill/` — claude-pack owns it, no cross-skill churn. Use product-spec as the *integration* test (separate marker, `pytest -m integration`, not blocking).
- **B:** Update process: `UPDATE_GOLDEN=1 pytest` automated in PR-bot for product-spec changes. High maintenance.
- **C:** Compare file tree (paths-only) not file contents. Survives prose edits but catches file-add/remove. Compromise.

Recommend A. Update phase-05:T-G1 spec accordingly.

### F10.2 — MEDIUM — golden test asserts exact match, not subset

prompt Q10 asks "exact match or subset?". Plan says "extracted tarball file tree matches golden". Ambiguous: exact = all files match; subset = all golden files present (allow new files). For determinism, exact is needed (new file = drift = SHA mismatch). For maintenance, subset is forgiving.

Fix: phase-05 — spec exact match (`set(extracted) == set(golden)`), document trade-off.

---

## Q11 — CLAUDE.md append integrity

### F11.1 — MEDIUM — no structural marker; future inserts break "append after Product Spec"

phase-06 step 1: "find end of Product Spec section". If a future plan appends `# Some Other Section` between Product Spec and the planned append point, the algorithm is undefined: does cook-agent append after Product Spec (now misordered) or at end (now correct)?

Fix: phase-06 — introduce HTML-comment markers around inserted section:
```
<!-- BEGIN: cleanmatic:claude-pack operating guide -->
# Claude Pack — LLM Operating Guide
...
<!-- END: cleanmatic:claude-pack operating guide -->
```
Idempotent: future updates detect markers, replace in-place. Documented in phase-06 implementation steps.

Plus: add a similar `<!-- BEGIN: cleanmatic:product-spec operating guide -->` retroactively to product-spec section? Out of scope for this plan, but recommend.

### F11.2 — LOW — `# Claude Pack` collides with `cleanmatic:claude-pack` ambiguity

Two skills share `cleanmatic:` namespace; section headings should match the slug. Currently "Claude Pack" (display) vs `cleanmatic:claude-pack` (slug). Acceptable; just be consistent.

Fix: phase-06 — heading is `# cleanmatic:claude-pack — LLM Operating Guide` to match product-spec convention (`# Product Spec — LLM Operating Guide` — wait, product-spec doesn't use the namespaced slug either). OK as written.

---

## Q12 — Self-referencing manifest

### F12.1 — MEDIUM — bootstrap problem documented but not solved

phase-06:R4 acknowledges. Self-referencing manifest works **after** v0.1.0 ships, because manifest_loader exists. But the **first build** must run from source tree — pack.py is executed via `./.claude/skills/.venv/bin/python3 .claude/skills/claude-pack/scripts/pack.py`. The script imports `manifest_loader` from same dir — works without "installation". OK, no bootstrap problem in practice.

However, validation of the seed manifest happens via `manifest_loader.validate` which is *part of the thing being packed*. If validator has a bug, you can't validate your way out. Acceptable for v1; flag for awareness.

Fix: phase-06 — add note: "pack.py validates manifest using bundled validator; validator bugs are caught by Phase 5 tests, not the seed validation." No code change.

---

## Q13 — Missing edge case: empty selection

### F13.1 — MEDIUM — empty manifest behavior undefined

Manifest with `skills: [], agents: [], hooks: [], rules: [], extra: []` and all `top_level: false`. Default-ship adds `.claude/scripts/`, `.claude/schemas/` (phase-02 step 4). So tarball isn't truly empty. But if user explicitly excludes those? plan doesn't have an `exclude_default_ship` flag.

What could fail: User wants minimal pack with only MANIFEST + INSTALL — no way to express. Or user wants only `extra` paths — default-ship adds scripts/ they don't want.

Fix: phase-03 — add manifest field `defaults: {include_scripts: true, include_schemas: true}` (default true). Or CLI flag `--no-default-ship`. Document.

Plus: phase-02 — if final selection is empty AND no MANIFEST/INSTALL added → exit 1 with "empty selection; nothing to pack". Currently undefined.

---

## Q14 — Missing edge case: very large pack

### F14.1 — MEDIUM — no size cap; accidental `.git/` inclusion blows up

User manifest `extra: [".git/"]` → pack.py walks multi-GB tree, hashes everything, then builds 2GB tarball. No warning, no cap.

Fix: phase-02 — add `--max-size <bytes>` flag (default 100MB). On exceed during walk, abort with warn. Also: `apply_defaults` could pre-warn if any `extra` path is `.git/` (specific drop pattern). Add `.git/` to `ALWAYS_DROP_DIRS` (currently missing — researcher A's skeleton drop_patterns includes `.git` (line 521), plan.md:40 lists `node_modules` but NOT `.git`).

phase-03 `ALWAYS_DROP_DIRS` (line 105-106): `{"__pycache__", ".venv", "node_modules", ".logs", "session-state", "agent-memory", ".pytest_cache"}` — **`.git` is missing**. CRITICAL omission.

Fix: phase-03 — add `.git` to `ALWAYS_DROP_DIRS`. Reflect in plan.md:40.

### F14.2 — UPGRADE TO CRITICAL — `.git/` not in always-drop list

Per F14.1 finding, plan.md:40 + phase-03:105 omit `.git`. If user does `extra: ["."]` (whole repo) for testing → pack ships entire git history including credentials in commit messages, removed `.env` files in history, etc.

Severity: CRITICAL — secret exposure via git history.

Fix: Add `.git` (and `.gitlab`, `.hg`, `.svn`) to `ALWAYS_DROP_DIRS`. Update T-S list to test.

---

## Q15 — Missing: pack.py error recovery

### F15.1 — HIGH — `.tmp` leak on rename-fail

Covered in F3.2. Reiterate: `try/finally` cleanup is missing from phase-02 step 10. CRITICAL for CI re-runs (next `pack.py --force` doesn't know to clean `.tmp` from previous failure).

Fix: explicit `try/finally` in phase-02 step 10 pseudocode.

### F15.2 — MEDIUM — partial fsync failure (disk full)

If `os.fsync` raises `OSError(ENOSPC)`, `.tmp` has partial data, rename does NOT run (good), but cleanup hits same disk-full and may fail. Exit code is 1 (generic error) — recipient can't distinguish from manifest error.

Fix: phase-02 — exit code 4 = "disk full" or "write error"; preserve `.tmp` for postmortem; emit clear error message.

---

## Q16 — YAGNI violations

### F16.1 — MEDIUM — `--dry-run` double-pass is expensive

phase-02 step 9: dry-run computes "would-be SHA256" by running full build into `BytesIO`. For a 100MB tree, this is ~10s and uses 100MB RAM. The PO use case for dry-run is "preview what'll ship" — file list + total bytes is enough. SHA256 is a nice-to-have that doubles execution.

Recommend: split into `--dry-run` (file list + bytes, fast) and `--dry-run-sha` (full hash, slow). Default `--dry-run` is fast.

Fix: phase-02 — `--dry-run` prints file list + total bytes + path. `--dry-run --compute-sha` adds would-be SHA256 (opt-in).

### F16.2 — LOW — `--no-follow-shared` flag use case unclear

CLI flag exists, manifest field exists. When does user invoke `--no-follow-shared`? If `_shared/` deps are auto-included with warn, opting out means accepting broken skills. The use case is "user knows recipient already has `_shared/` installed". Edge case.

Recommend: keep flag; document use case in references/flag-reference.md. Not a YAGNI violation if documented.

### F16.3 — LOW — 17 CLI flags is a lot

Plan says "17-flag CLI". For manifest-first design, half are overrides. Consolidation possible:
- `--include-readme / --include-claudemd / --include-settings / --include-ck-config` (4) → `--top-level readme,claudemd,settings` (1 with comma list).
- `--all / --skills / --agents / --hooks / --rules` (5) → `--all` (sugar for "all four"); rest per-category.

Trade-off: discoverability via `--help` vs concise syntax.

Recommend: keep 17 for v1 (discoverable, less surprise); revisit in v1.1 if users complain.

### F16.4 — LOW — SHA256 sidecar + embedded checksums (overkill?)

Sidecar = recipient verifies before extract. MANIFEST inner-checksums = audit trail after extract. Both serve different purposes. Not overkill; keep.

### F16.5 — MEDIUM — interactive mode in v1

Researcher B noted defer-to-v1.1. Plan keeps in v1 (phase-04). build_manifest.py is ~250 lines (substantial). For dogfood-only v1, the seed manifest in phase-06 step 5 covers the actual repo; PO never needs interactive mode.

Recommend (PO call): defer build_manifest.py to v1.1; v1 ships manifest.example.yaml + docs only; PO copies+edits by hand. Saves ~4h effort.

If kept in v1: ensure phase-04 tests run; budget tight at 24h total effort.

### F16.6 — MEDIUM — pytest in install.sh by default

phase-05 modifies install.sh to optionally run smoke pytest after install. Researcher B's audit (phase-05:R4) notes default-on. For recipients (not maintainers), pytest is dead weight — bloats install with `pytest>=7,<9` + transitive deps.

Recommend: phase-05 — pytest is dev-only; `requirements-dev.txt` (separate file); install.sh does NOT install pytest by default. `install.sh --dev` opts in. Mirror product-spec only if product-spec actually does this (verify).

---

## Q17 — Specification ambiguity / under-specification

### F17.1 — HIGH — Phase 2 step 3: agents subdir structure undefined

Plan says `agents: [bar]` → `.claude/agents/bar.md`. But what if agents nested? `.claude/agents/sub-team/planner.md`? Plan doesn't say. T-B1 may pass if all agents at top level (current state) but fails when nested.

Fix: phase-02 step 3 — spec exactly: "agents: [name] → search `.claude/agents/**/*.md` for first match; error if multiple matches with same basename." OR: "agents must be top-level only; nested agents not supported in v1."

Same ambiguity for `rules` (does `.claude/rules/` allow subdirs?).

### F17.2 — HIGH — merge_cli precedence for booleans

phase-03 step 4: "for each CLI override (e.g., `cli.skills`, `cli.agents`), if non-None: replace manifest field". For booleans (e.g., `--include-readme`):
- Default `argparse` boolean = `False` (not None).
- If user doesn't pass `--include-readme`, `cli.include_readme = False`.
- merge logic checks `is not None` → False is not None → overrides manifest `True` to `False`. **Wrong.**

Fix: phase-03 step 4 — use `argparse.BooleanOptionalAction` with `default=None` for booleans; OR explicit per-field handling: "if CLI bool is None: keep manifest; if True: set; if False: unset". phase-02 step 1 mentions `BooleanOptionalAction` for `--follow-shared` but not the `--include-*` flags. Spec all of them.

### F17.3 — HIGH — INSTALL.md token substitution semantics

phase-02 step 8: "substitute `{{VERSION}}`, `{{BUILT_AT}}`, `{{SOURCE_COMMIT}}`". What if template has `{{UNKNOWN_TOKEN}}`? Two valid implementations:
- A: Leave literal `{{UNKNOWN_TOKEN}}` in output (recipient sees confusing string).
- B: Error at build time ("unknown token").
- C: Replace with empty string (silent drop).

Fix: phase-02 — spec exactly: "unknown `{{...}}` tokens are errors at build time" (option B). Add T-T1: template with unknown token → pack.py exits 1.

### F17.4 — MEDIUM — pyyaml version pinning

phase-04:R5 says "pin `pyyaml>=6.0,<7`". phase-01 requirements.txt just says "pyyaml". Conflict between phase-01 and phase-04. Pick.

Fix: phase-01 step 5 — requirements.txt: `pyyaml>=6.0,<7`. Consistent with phase-04.

### F17.5 — MEDIUM — extension-auto-append edge cases

phase-03 manifest schema: "agents — list of agent file basenames (auto-append .md if missing)". What if user writes `agents: ["planner.md.bak"]`? Auto-append → `planner.md.bak.md`? Or `agents: ["planner.txt"]`? Auto-append? Or `agents: ["planner"]` and there's both `.md` and `.markdown` versions?

Fix: phase-03 — spec: "if basename has no extension, append `.md`. If basename has any extension, use as-is. Multiple matches with same basename: error."

### F17.6 — LOW — exit code 2 vs 3 inconsistency

phase-02 NF "exit codes":
- 0 = success
- 1 = manifest error or selection-resolution error
- 2 = safety violation in dry-run
- 3 = output collision

phase-06 CLAUDE.md section says:
- 0 = success
- 1 = validation error
- 2 = strict-gate or collision
- 3 = output collision

Two different mappings for exit code 2 (safety violation vs strict-gate vs collision). Three different mappings for code 3 (output collision in both, but phase-06 lists collision twice for 2 and 3).

Fix: phase-02 NF and phase-06 CLAUDE.md section — reconcile to single table. Recommend:
- 0 = success
- 1 = validation/manifest error
- 2 = strict-gate finding (`--strict`)
- 3 = output collision (no `--force`)
- 4 = write error (disk full, permission)

Document in references/flag-reference.md.

---

## Cross-cutting findings

### F-X1 — HIGH — plan.md:40 always-drop list disagrees with phase-03:104-107

| Item | plan.md:40 | phase-03 |
|------|------------|----------|
| `.env` | exact | exact ✓ |
| `metadata.json` | exact | exact ✓ |
| `.logs/` | dir | dir ✓ |
| `session-state/` | dir | dir ✓ |
| `agent-memory/` | dir | dir ✓ |
| `__pycache__/` | dir | dir ✓ |
| `.venv/` | dir | dir ✓ |
| `node_modules/` | dir | dir ✓ |
| `.DS_Store` | — | exact ✓ added |
| `.pytest_cache` | — | dir ✓ added |
| `.git/` | — | — ❌ missing both |
| `**/.env.*` glob | — | pattern ✓ added |

phase-03 added items not in plan.md (DS_Store, pytest_cache) and a glob pattern. Plan.md must be updated to be source-of-truth — otherwise PO reading plan.md gets incomplete picture.

Fix: Reconcile plan.md:40 with phase-03 constants; add `.git`/`.gitlab`/etc per F14.2.

### F-X2 — MEDIUM — phase efforts may underrun for hardened spec

Sum of phase efforts: 3+5+4+4+5+2 = 23 hours. Adding fixes:
- F1.1 (file-granular sort): +1h.
- F2.* (safety hardening + tests): +2h.
- F3.1 (Windows + os.replace): +0.5h.
- F4.1-4.7 (validate strengthening): +1.5h.
- F5.* (transitive deps + missing-ref findings): +1h.
- F6.1 (version-aware installer): +1h.
- F10.1 (golden refactor to synthetic): +1h.
- F11.1 (CLAUDE.md markers): +0.5h.

Adjusted total: ~31h. Plan's "no risk to ship" reading needs updated estimates.

Fix: Adjust phase efforts post-fix; phase-02 + phase-03 each grow by ~2h.

---

## Severity Roll-up

| Severity | Count | Items |
|----------|-------|-------|
| CRITICAL | 3 | F2.1, F2.2, F4.5, F14.2 |
| HIGH | 14 | F1.1, F1.2, F2.3, F2.4, F3.1, F4.1, F4.2, F5.1, F6.1, F7.1, F9.1, F10.1, F15.1, F17.1, F17.2, F17.3 |
| MEDIUM | 16 | F1.3, F1.4, F2.5, F3.2, F4.3, F4.4, F4.6, F5.2, F5.3, F8.1, F9.2, F10.2, F11.1, F13.1, F14.1, F15.2, F16.1, F16.5, F16.6, F17.4, F17.5, F-X1, F-X2 |
| LOW | 12 | F1.5, F1.6, F2.6, F3.3, F4.7, F5.4, F6.2, F8.2, F9.3, F11.2, F12.1, F16.2, F16.3, F16.4, F17.6 |
| OBSERVE | 1 | F1.6 |

(Counts approximate; some findings span severities.)

---

## Open Questions for PO

Decide before `/ck:cook`:

1. **F2.1 secrets list** — expand always-drop to industry-standard (id_rsa, *.pem, *.key, etc.)? Or strict "`.env` only" and trust manifest authors?
2. **F4.5 absolute paths in `extra`** — reject entirely or normalize to repo-relative with warning?
3. **F5.1 follow_shared semantics** — auto-include (plan.md:42) vs warn-only (recommended)? Auto-include risks false-positive inclusion from doc strings.
4. **F6.1 installer version awareness** — implement now or defer to v1.1?
5. **F7.1 SOURCE_DATE_EPOCH** — default to `mtime=0` always, or honor env var?
6. **F10.1 golden source** — use product-spec (current plan, brittle) or synthetic fixture (recommended)?
7. **F13.1 empty pack** — add `--no-default-ship` flag, or refuse empty selection?
8. **F14.2 `.git/` always-drop** — confirm add to always-drop list. (Recommend yes.)
9. **F16.5 interactive mode** — keep in v1 (cost ~4h) or defer to v1.1?
10. **F16.6 pytest in install.sh** — dev-only via `--dev` flag, or include by default for "small skill, ~10MB"?
11. **F17.1 nested agents/rules** — support `.claude/agents/sub/foo.md` in v1, or top-level only?

---

## Unresolved

- **Windows `pack.py` support scope:** No evidence in plan that anyone has tested or even attempted Windows pack-builds. Plan should explicitly state POSIX-only or commit to Windows CI. F3.1 partial answer.
- **CI matrix:** Plan doesn't mention CI configuration. T-D1 determinism is a Python-version-sensitive test; without a CI matrix, byte-identity guarantee is local-only. Out-of-scope for this plan but should be a follow-up.
- **Recipient extract filter version:** Python 3.12+ adds `filter='data'` default; pre-3.12 extract is silently less safe. Recipient INSTALL.md must spec minimum Python or use `bash tar` (which has its own filter caveats). Not addressed.
- **`.gitignore` ambiguity** in phase-06:R3 (`dist/` vs `/dist/`): documented but no test verifies the right form is used.
- **Researcher B report not directly cited in this review** — read inline references only; if Researcher B identified additional risks not in this review, they should be cross-checked separately.
