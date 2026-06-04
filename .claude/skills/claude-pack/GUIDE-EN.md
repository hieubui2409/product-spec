# `claude-pack` Guide for Developers

> This guide is for **developers** who want to bundle a curated subset of the `.claude/` tree (skills,
> agents, hooks, rules…) into a **versioned, deterministic** `tar.gz` for sharing or installing on another
> machine. The language here is technical.
>
> Vietnamese version: [`GUIDE-VI.md`](./GUIDE-VI.md).

---

## 1. What does this skill do?

`claude-pack` gathers a **curated subset** of `.claude/` (plus a few optional top-level files like
`README.md`, `CLAUDE.md`) into a version-stamped `tar.gz`. Each bundle ships:

- `MANIFEST.json` — per-file SHA256 listing.
- `INSTALL.md` — install instructions for the recipient.
- `install.sh` (POSIX) + `install.ps1` (Windows) — multiplatform, version-aware installers.

Two core guarantees:

1. **Manifest is the source-of-truth.** `.claude/pack.manifest.yaml` declares build inputs. CLI flags
   override per-build; interactive mode regenerates the manifest.
2. **Determinism is a contract.** Same source + manifest → **byte-identical** `tar.gz`. Achieved via PAX
   format, sorted walk (file-granular), `mtime=0`, `uid=gid=0`, gzip header `mtime=0`.

The safety filter is **non-removable**: `.env`/secrets/keys, `.git/`, runtime caches, session state are
always dropped. `settings.json` and `.ck.json` enter the bundle only when explicitly opted in.

---

## 2. Two ways to give instructions — and which to prefer

### Way 1 (preferred): Describe your intent in words

Tell the skill what you want to bundle; it runs `build_manifest` in discover mode, walks you through manifest
authoring, previews, then packs:

> *"Pack the product-spec skill with the planner and researcher agents to send to a teammate."*
>
> *"Build a bundle from the existing manifest, version 0.2.0."*
>
> *"Preview the file list that would go into the bundle — don't create a tarball yet."*

This is the recommended path because the LLM owns the UI layer (AskUserQuestion) while the script owns the
structural layer — consistent with the Script-vs-LLM split.

### Way 2 (equivalent): Invoke the skill with flags

Once you're comfortable, invoke the skill with "flags" — the same way you call any other user-invocable skill:

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --dry-run
```

Both ways yield the same result. Flags are just a shortcut for people who already know the ropes.

> 🔧 **Because this is a developer skill — note the command that actually runs.** Each skill flag maps 1-to-1
> to a `python -m pack` invocation that the LLM runs under the hood. In every scenario below, alongside the
> skill flag, this guide also lists the **underlying command** — use it directly when automating in CI or
> calling without the LLM:
> ```bash
> .claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run
> ```

> ⚠️ **Boundary note:** Python scripts **never** call `AskUserQuestion`. The LLM is the UI layer, the script
> is the structural layer. The LLM **never** edits the tarball directly.

> 💡 Not sure what to do? Just type `/cleanmatic:claude-pack` (no flag): if no manifest exists, the skill runs
> the interactive interview; if one exists, it asks reuse / overwrite / cancel.

---

## 3. Core concepts — the contract (read this once)

Six guarantees govern every build:

1. **Manifest is source-of-truth.** `.claude/pack.manifest.yaml` declares the inputs; CLI flags override
   per-build, interactive mode regenerates it.
2. **Determinism is a contract.** Same source + manifest → **byte-identical** `tar.gz` (PAX, sorted walk,
   `mtime=0`, `uid=gid=0`, gzip `mtime=0`). Never hand-edit a tarball — it breaks the contract.
3. **The safety filter is non-removable.** `.env`/secrets/keys, `.git/`, caches, session state are **always
   dropped**; `settings.json`/`.ck.json`/top-level `README`/`CLAUDE.md`/internals are **opt-in only**.
4. **Script-vs-LLM split.** Scripts do the structural work (parse, safety, tarball); the LLM owns the UI
   (`AskUserQuestion`) and **never edits the tarball**. Scripts never call `AskUserQuestion`.
5. **No auto-install.** The recipient runs the installer **by hand** — skip-existing by default,
   `FORCE_OVERWRITE=1` to opt in (backs up first).
6. **Release is tag-triggered CI only.** Bump `version` + the CHANGELOG, push an annotated tag; **never
   hand-build + `gh release create`** — a manual build's SHA won't match CI's reproducible build, breaking
   the published checksum.

## 4. Learning path

- **Build basics:** interactive build (Tier A1) → preview with `--dry-run` (A3) → build from an existing
  manifest (A2).
- **Shape the bundle:** override version/name (B1), content flags (B2), opt-in sensitive files (B3),
  `_shared/` handling (B4).
- **Automate in CI:** reproducible build with `SOURCE_DATE_EPOCH` (C1), JSON output (C2), the exit-code table.
- **Ship & receive:** recipient install POSIX/Windows (D1); for an *official* release, drive the
  tag-triggered pipeline (concept §3.6), never a hand build.

## 5. Important caveats & gotchas

- **Official releases are tag-triggered only** — never `gh release create` by hand; a manual build's bytes
  differ from CI's reproducible build and break SHA256 verification. (§3.6)
- **Bundle version ≠ skill version** — it labels the *distribution*. `0.0.0-dev` is refused for real builds
  (use `--allow-dev-version` for throwaways).
- **The safety filter can't be turned off** — secrets/`.env`/keys are always dropped; no flag pulls them back.
- **`_shared/` is warn-only by default** — refs inside code fences are stripped first, so real deps need
  `--include-shared <name>` explicitly (`--strict` turns un-included refs into a blocking error).
- **`dist/` is gitignored** — tarballs are reproducible artifacts, not source; commit them only on a tagged release.
- **v1 boundaries:** no remote upload, no GPG signing, no `claude-unpack`, no multi-project packing, tar.gz only.

## 6. Every use case — grouped by what you reach for

Grouped into four tiers: **A. Build basics** (1–3), **B. Shape the bundle** (4–7), **C. CI & automation**
(8–9), **D. Recipient & release** (10). Each scenario includes: when to use it, a **sample conversation**,
the **equivalent skill flag**, and the **underlying command** that runs under the hood.

---

## Tier A — Build basics

### Priority 1 — Interactive build from scratch (no manifest yet)

**When to use:** No `.claude/pack.manifest.yaml` exists, or you want to author a new one via interview.

The skill runs `build_manifest --discover` to list available skills/agents/hooks/rules, then walks you
through **4 question batches**: (1) version + bundle name, (2) select skills/agents/hooks/rules, (3)
top-level files, (4) extras + `_shared/` handling. Finally it previews and **confirms via a hard-locked
prompt** before writing the manifest.

#### Conversation

> **You:** Create a bundle with the product-spec skill, the planner and researcher agents, and the two rules
> primary-workflow and development-rules.
>
> **Skill:** I've discovered the repo. Let's walk the batches.
> - *Bundle version* (SemVer)? Default `0.1.0`. *Bundle name*? Default `claude-pack`.
> - **Available skills:** product-spec, claude-pack. You pick `product-spec`.
> - **Agents:** planner, researcher, … → you pick `planner`, `researcher`.
> - **Rules:** you pick `primary-workflow.md`, `development-rules.md`.
> - Top-level: include `README.md` / `CLAUDE.md`? (default no)
> - `_shared/`: auto-include refs? (default false = warn-only)
>
> **You:** Version 1.0.0, no top-level, keep `_shared` warn-only.
>
> **Skill:** Summary: `version=1.0.0, skills=1, agents=2, rules=2`.
> > **Ready to write .claude/pack.manifest.yaml with 1 skills, 2 agents, 2 rules? [y/N]**
>
> **You:** y
>
> **Skill:** Manifest written. Build preview: N files, total size X. Want me to pack it now?

#### Equivalent skill flag

```
/cleanmatic:claude-pack            # no flag → interactive interview flow
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m build_manifest --discover --root .
.claude/skills/.venv/bin/python3 -m build_manifest --list-questions --root .
# (after collecting answers + confirmation)
echo "$answers_json" | .claude/skills/.venv/bin/python3 -m build_manifest --write --root .
```

> If a manifest already exists, `--write` exits 2 (collision) unless `--force`. The skill must surface the
> collision and re-prompt.

---

### Priority 2 — Build from an existing manifest

**When to use:** `.claude/pack.manifest.yaml` already exists; you just want to produce the tarball.

#### Conversation

> **You:** Build the bundle from the current manifest.
>
> **Skill:** I load `.claude/pack.manifest.yaml`, run safety_check (drops always-drop entries), walk sorted,
> then write `dist/claude-pack-1.0.0.tar.gz` plus the `.sha256` sidecar. The build is deterministic — the
> same input produces byte-identical output.

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml
```

---

### Priority 3 — Preview before packing (Dry-run)

**When to use:** You want to see the **file list + total size** without producing a tarball. Optionally with
the would-be SHA256.

#### Conversation

> **You:** Preview what would go into the bundle — don't create the real file.
>
> **Skill:** Dry-run done: 47 files, 312 KB compressed total. No always-drop file slipped through. Want me to
> also compute the would-be tarball SHA256? (single pass, no double cost)
>
> **You:** Yes.

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --dry-run
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --dry-run --compute-sha
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run --compute-sha
```

---

## Tier B — Shape the bundle

### Priority 4 — Override version / bundle name for ad-hoc builds

**When to use:** Test builds with a different version without editing the manifest.

> ⚠️ The skill refuses the `0.0.0-dev` placeholder for real builds (needs `--allow-dev-version`). The version
> labels the *distribution*, decoupled from the skill's own version.

#### Conversation

> **You:** Build an rc, version 0.2.0-rc1.
>
> **Skill:** Override `version=0.2.0-rc1` for this build; the manifest is untouched. Output:
> `dist/claude-pack-0.2.0-rc1.tar.gz`.

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --version 0.2.0-rc1
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --bundle-name my-pack
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --version 0.2.0-rc1
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --bundle-name my-pack
```

---

### Priority 5 — Override content via flags (without editing the manifest)

**When to use:** Add/remove skills, agents, hooks, rules, or extra paths for one build.

> Flag overrides **win** over the manifest value for that category. `--extra` forbids absolute paths and `..`.

#### Conversation

> **You:** Build like the manifest but take only the product-spec skill and add docs/onboarding.md.
>
> **Skill:** Override `--skills product-spec --extra docs/onboarding.md`. Other categories follow the manifest.

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --skills product-spec --extra docs/onboarding.md
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --agents planner,researcher --rules primary-workflow.md,development-rules.md
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --skills product-spec --extra docs/onboarding.md
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --agents planner,researcher --rules primary-workflow.md,development-rules.md
```

---

### Priority 6 — Opt-in sensitive / internal files

**When to use:** You need to include `settings.json`, `.ck.json`, top-level README/CLAUDE.md, or the
`scripts/`/`schemas/` internals. All are **off by default** and must be enabled explicitly.

> `settings.json` and `.ck.json` belong to the safety filter's opt-in catalog — they enter the bundle only
> via the matching flag. Secrets/keys/`.env` are **always dropped**; no flag can pull them back.

#### Conversation

> **You:** Also include the top-level README and CLAUDE.md, plus settings.json.
>
> **Skill:** Enabling `--include-readme --include-claudemd --include-settings`. Note `settings.json` is a
> sensitive opt-in — added per your explicit request. `.env`/secrets stay dropped regardless.

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --include-readme --include-claudemd --include-settings
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --include-scripts --include-schemas
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --include-readme --include-claudemd --include-settings
# CK-framework internals (off by default):
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --include-scripts --include-schemas
```

---

### Priority 7 — Handle `_shared/` dependencies

**When to use:** A packed skill references `skills/_shared/<name>`. Default is **warn-only** (many refs live
inside example code fences, not real dependencies — the skill strips fenced blocks, then warns).

#### Conversation

> **You:** My skill uses _shared/lib and _shared/utils, pull them in too.
>
> **Skill:** Opt-in `--include-shared lib,utils`. If you want un-included `_shared/` refs to be treated as
> **errors** (blocking the build), add `--strict` (exit 2).

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --include-shared lib,utils
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --follow-shared
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --strict
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --include-shared lib,utils
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --follow-shared
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --strict
```

---

## Tier C — CI & automation

### Priority 8 — Reproducible build for CI (`SOURCE_DATE_EPOCH`)

**When to use:** You want a reproducible build pinned to the commit date in CI.

> Default `mtime=0` (fully deterministic). `--source-date-epoch env` honors the `SOURCE_DATE_EPOCH` variable;
> if the var is empty/non-numeric it falls back silently to 0.

#### Conversation

> **You:** In CI, pin mtime to the last commit.
>
> **Skill:** Set `SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)` then pass `--source-date-epoch env`. The
> tarball stays deterministic on the same commit.

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --source-date-epoch env
```

#### Underlying command (runs under the hood)

```bash
SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct) \
  .claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --source-date-epoch env
```

> Note: setting the `SOURCE_DATE_EPOCH` env var is a shell operation — when automating in CI you use the
> underlying command above directly. This is exactly what the release workflow (`claude-pack-release.yml`) does.

---

### Priority 9 — JSON output for CI pipelines

**When to use:** You need machine-readable status for a pipeline to parse.

#### Conversation

> **You:** Build and return JSON for the next CI step to parse.
>
> **Skill:** Add `--json` to the pack command → JSON status on stdout. (Note: `manifest_loader.py`,
> `safety_check.py`, `build_manifest.py` always emit JSON and have no `--json` flag.)

#### Equivalent skill flag

```
/cleanmatic:claude-pack --manifest .claude/pack.manifest.yaml --json
```

#### Underlying command (runs under the hood)

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --json
```

---

## Tier D — Recipient & release

### Priority 10 — Recipient side: install the bundle (including Windows)

**When to use:** The recipient has `claude-pack-{version}.tar.gz`.

Every bundle ships **both** installers. The recipient verifies SHA256 → extracts → runs the installer. The
installer is **version-aware** (detects STALE / NEWER / OK SAME per skill) and defaults to **skip-existing**;
overwrite via `FORCE_OVERWRITE=1` (backs up first).

> ℹ️ This step is **outside** the `claude-pack` skill — it's a recipient-side operation run by hand, not via a
> skill flag. Hence this section only lists the executed commands.

#### Conversation

> **You (recipient, Windows machine):** I got the tar.gz, how do I install on Windows?
>
> **Skill:** Verify the checksum, extract, then run `install.ps1`:
> ```powershell
> # PowerShell
> (Get-FileHash claude-pack-1.0.0.tar.gz -Algorithm SHA256).Hash
> tar -xzf claude-pack-1.0.0.tar.gz
> cd claude-pack-1.0.0
> powershell -ExecutionPolicy Bypass -File .\install.ps1
> ```
> On POSIX, use the matching `install.sh`. The installer skips existing skills; to overwrite, set
> `FORCE_OVERWRITE=1`.

#### Executed commands (POSIX)

```bash
sha256sum -c claude-pack-1.0.0.tar.gz.sha256
tar -xzf claude-pack-1.0.0.tar.gz
cd claude-pack-1.0.0 && ./install.sh
FORCE_OVERWRITE=1 ./install.sh      # overwrite existing skills (backs up first)
```

---

## 7. Output Contract

```
dist/
├── claude-pack-{version}.tar.gz          # the bundle
└── claude-pack-{version}.tar.gz.sha256   # coreutils-format sidecar
```

Tarball internal layout (versioned root dir):

```
claude-pack-{version}/
├── MANIFEST.json     # schema_version "1.0", per-file SHA256
├── INSTALL.md        # rendered from INSTALL.md.template
├── install.sh        # POSIX installer
├── install.ps1       # Windows installer
└── .claude/          # the selected subtree
```

`dist/` is gitignored — tarballs are reproducible build artifacts, not source.

---

## 8. Exit Codes (for automation)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation / manifest error |
| 2 | Strict-gate finding (`--strict`) |
| 3 | Output collision (no `--force`) |
| 4 | Write error (disk full, permission, cross-fs replace) |
| 5 | Empty selection / over max-size |
| 130 | Interrupted (SIGINT) |

> `build_manifest.py --write` uses its own codes: 0 ok · 1 validation · 2 **collision** (different meaning
> from the strict-gate at the `python -m pack` entry point).

---

## 9. What this skill does NOT do

- **No remote upload.** Use `gh release upload` manually.
- **No GPG signing in v1.** SHA256 sidecar only.
- **No `claude-unpack` companion.** The contract is `tar -xzf` + the bundled installer.
- **No merge-resolver.** The recipient `install.sh` skips existing skills; `FORCE_OVERWRITE=1` opts in.
- **No multi-project packing.** One `.claude/` root per bundle.
- **No zip / tar.zst.** Tar.gz only in v1.

---

## 10. Further reading

- `SKILL.md` — the full operating contract (flag table, output contract, workflow map).
- `references/manifest-spec.md` — manifest schema.
- `references/flag-reference.md` — per-CLI-flag detail + exit codes.
- `references/safety-rules.md` — always-drop + opt-in catalog.
- `references/error-catalog.md` — `MANIFEST_E###` lookups.
- `references/troubleshooting.md` — recipient-side issues.
- Root `CLAUDE.md` → "Claude Pack — LLM Operating Guide" — the five operating principles (source-of-truth).
