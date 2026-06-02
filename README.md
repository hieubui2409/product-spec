# cleanmatic skills

A small collection of **Claude Code skills** by cleanmatic. Three skills ship here, each self-contained under
`.claude/skills/`:

| Skill | For whom | What it does |
|---|---|---|
| **[`product-spec`](.claude/skills/product-spec/)** | Non-technical **Product Owners** | Interview-driven product spec hierarchy (**Vision → 1 BRD → many PRDs → Epics → Stories with AC**) with strict traceability, validation, and visualization — in plain language, no code required. Bilingual EN/VI. |
| **[`spec-critique`](.claude/skills/spec-critique/)** | **Product Owners** | An opinionated, brutal-but-grounded tear-down of a `product-spec` spec across four lenses (product/tech/market/craft). Says what `--validate` cannot: why it would die, where it sits in the market, whether the writing holds up. Nine voice levels, never edits the spec, never gates CI. Bilingual EN/VI. |
| **[`claude-pack`](.claude/skills/claude-pack/)** | **Developers** | Package a curated subset of the `.claude/` tree (skills, agents, hooks, rules) into a versioned, **deterministic** `tar.gz` for sharing or installing on another machine. Manifest-first; multiplatform recipient installer. |

> 📘 **Usage guides (every use case as a sample conversation):**
> - product-spec — [`GUIDE-VI.md`](.claude/skills/product-spec/GUIDE-VI.md) (Tiếng Việt) · [`GUIDE-EN.md`](.claude/skills/product-spec/GUIDE-EN.md) (English)
> - spec-critique — [`GUIDE-VI.md`](.claude/skills/spec-critique/GUIDE-VI.md) (Tiếng Việt) · [`GUIDE-EN.md`](.claude/skills/spec-critique/GUIDE-EN.md) (English)
> - claude-pack — [`GUIDE-VI.md`](.claude/skills/claude-pack/GUIDE-VI.md) (Tiếng Việt) · [`GUIDE-EN.md`](.claude/skills/claude-pack/GUIDE-EN.md) (English)

The three skills share **one Python virtual environment** at `.claude/skills/.venv/` (created by any installer).

---

## `product-spec` — for Product Owners

Runs an interview, captures your product spec as a strictly-traceable hierarchy, validates it, and visualizes it — all
in plain language, no code required from you. Bilingual: English and Vietnamese.

### What it does for you

| You want to… | Run |
|---|---|
| Start a new product spec from scratch | `/cleanmatic:product-spec` (no flag → menu) |
| Add a new feature area | `/cleanmatic:product-spec --prd <feature>` |
| Decompose a long brain-dump into a clean spec | `/cleanmatic:product-spec --auto` |
| Check the spec for orphans, missing AC, drift | `/cleanmatic:product-spec --validate` |
| Sign off a BRD/PRD/Epic/Story | `/cleanmatic:product-spec --approve` |
| Get a 1-page exec summary | `/cleanmatic:product-spec --summary` |
| Draw the spec tree / roadmap / coverage map | `/cleanmatic:product-spec --viz <view>` |
| Apply a change without losing prior decisions | `/cleanmatic:product-spec --update` |

Output lives in `docs/product/` inside your project — markdown files with rich YAML metadata. The skill never writes
outside `docs/product/`.

### Install

```bash
# POSIX (macOS / Linux / WSL)
bash .claude/skills/product-spec/install.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File .\.claude\skills\product-spec\install.ps1
```

Requires **Python 3.11+** and (on first run only, if the vendored JS is absent) `curl`/`wget`. The installer creates the
shared venv, installs `pyyaml`, and vendors the Mermaid + marked + DOMPurify runtimes for offline HTML. Idempotent —
re-running is safe.

Then invoke from Claude Code:

```
/cleanmatic:product-spec
```

### Deep links

- **Usage guide:** [`GUIDE-VI.md`](.claude/skills/product-spec/GUIDE-VI.md) / [`GUIDE-EN.md`](.claude/skills/product-spec/GUIDE-EN.md)
- **README:** [`.claude/skills/product-spec/README.md`](.claude/skills/product-spec/README.md)
- **Operating contract:** [`.claude/skills/product-spec/SKILL.md`](.claude/skills/product-spec/SKILL.md)
- **Worked sample:** [`examples/acme-shop`](.claude/skills/product-spec/examples/acme-shop)

### What it does NOT do

- No production code — output is product specs; your engineering team writes the code.
- No story-point / hour estimation — stories carry only `size: S | M | L`.
- No overwriting your manual edits — on `--update` it flags affected items and asks first.
- No auto-flipping an `approved` decision — contradictions are surfaced for you to resolve (Keep / Change / Hybrid).
- No internet at runtime — after install, everything runs on your machine (one caveat: if Mermaid failed to vendor at install time, Mermaid **graph** views fall back to a CDN script at browser-render; re-run the installer to vendor it — ASCII and body views never reach a CDN).

> 💬 **Want an opinion, not just a pass/fail?** [`spec-critique`](.claude/skills/spec-critique/) (below) tears the same
> spec apart and tells you whether it is worth building. Optional: install its post-validate drift nudge with
> `spec-critique/install.sh --critique-hook` to be reminded (once per session) when the spec has changed enough to be
> worth re-critiquing.

---

## `spec-critique` — for Product Owners

`--validate` tells you the spec is structurally sound. `spec-critique` tells you whether it is any **good** — an
honest, sarcastic, brutal-but-grounded tear-down across four lenses (product / tech / market / craft). It reuses the
validate findings as ammo, then says what validate cannot: why this would die in the market, whether it is a me-too,
whether the writing actually holds up. It **never edits your spec** and is **never** in a CI gate (it is opinion + web
research + voice, non-deterministic by design).

### What it does for you

| You want to… | Run |
|---|---|
| An honest read on the whole spec | `/cleanmatic:spec-critique` (or `all`) |
| Tear apart one feature (PRD / epic / story) | `/cleanmatic:spec-critique PRD-CHECKOUT` |
| Only the market angle (or product / tech / craft) | `/cleanmatic:spec-critique --market` |
| Pick scope + lenses + intensity interactively | `/cleanmatic:spec-critique --interactive` |
| Dial the voice from gentle to brutal | `/cleanmatic:spec-critique --level 1..9` |
| Make it harsher without re-analysing | bump `--level` on an unchanged spec — only the voice re-renders, the analysis is reused |
| Re-judge from scratch after a fix | `/cleanmatic:spec-critique PRD-CHECKOUT --fresh` |
| Refresh competitor research | `/cleanmatic:spec-critique --refresh-web` |
| Ignore the parent's prior findings | `/cleanmatic:spec-critique PRD-CHECKOUT-E1-S1 --no-inherit` |

Every finding cites a real `ID:line`, says why it dies, and ends with a concrete fix — no free-floating insults.

**Re-runs are cheap.** Critique the same scope twice and it reuses prior work (no spec change → nothing re-analysed;
just a level bump → only the voice re-renders). Critique a child after its parent and the child inherits the parent's
unresolved blockers as risk; critique a parent after its children and it rolls up "N of M children carry blockers".
All token-saving only — `--fresh` forces a full rebuild.

### Voice levels (1 to 9) and the safety floor

Nine intensity levels. **Default is 5** (no-mercy: brutal, may jab you, but still all about the work). Levels 1 to 4
never attack you, only the artifact. Levels **6 to 9 are dangerous and opt-in** — 6 roasts you as the author, 7 to 9
escalate through a harsher Vietnamese register (`ông/tôi` → `mày/tao`) and, at 9, work-aimed profanity; 6 to 8 ask you
to confirm, and **9 re-confirms on every run**. There is one line the tool never crosses, at **any** level, even 9,
even with your consent: it attacks the **work**, never **you** — no threats, no slurs on who you are, nothing about
your family, no self-harm or sexual content. The rule is the target of the line, not how harsh it is.

### Deep links

- **Usage guide:** [`GUIDE-VI.md`](.claude/skills/spec-critique/GUIDE-VI.md) / [`GUIDE-EN.md`](.claude/skills/spec-critique/GUIDE-EN.md)
- **README:** [`.claude/skills/spec-critique/README.md`](.claude/skills/spec-critique/README.md)
- **Operating contract:** [`.claude/skills/spec-critique/SKILL.md`](.claude/skills/spec-critique/SKILL.md)
- **The voice (all 9 levels + the floor):** [`references/voice-and-tone.md`](.claude/skills/spec-critique/references/voice-and-tone.md)

### What it does NOT do

- No code generation, and no spec editing — it writes one critique report, never touches your spec artifacts.
- No CI gate — it is opinionated and non-deterministic by design; `--validate` stays the reproducible gate.
- No auto-memory — a big finding only becomes a recorded decision (`DEC-<n>`) if you confirm it.
- It does not run `--validate` for you — that stays reproducible and PO-facing; critique only reads its results.

---

## `claude-pack` — for Developers

Bundles a curated subset of `.claude/` (skills, agents, hooks, rules) plus optional top-level files into a versioned,
deterministic `tar.gz`. Each bundle ships a `MANIFEST.json` (per-file SHA256), an `INSTALL.md`, and multiplatform
installers (`install.sh` + `install.ps1`) so the recipient extracts once and runs.

### What it does for you

| You want to… | Run |
|---|---|
| Author a manifest interactively, then pack | `/cleanmatic:claude-pack` (no flag → interview) |
| Build from an existing manifest | `… -m pack --manifest .claude/pack.manifest.yaml` |
| Preview the file list + size, no tarball | `… -m pack --manifest … --dry-run` |
| Override version for an ad-hoc build | `… -m pack --manifest … --version 0.2.0-rc1` |
| Reproducible CI build pinned to commit date | `SOURCE_DATE_EPOCH=… … -m pack … --source-date-epoch env` |

Output lands in `dist/claude-pack-{version}.tar.gz` + a `.sha256` sidecar (`dist/` is gitignored — tarballs are
reproducible artifacts, not source).

### Install

```bash
# POSIX (macOS / Linux / WSL)
bash .claude/skills/claude-pack/install.sh            # add --dev for pytest

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File .\.claude\skills\claude-pack\install.ps1
```

Requires **Python 3.11+**. Then invoke from Claude Code:

```
/cleanmatic:claude-pack
```

### Deep links

- **Usage guide:** [`GUIDE-VI.md`](.claude/skills/claude-pack/GUIDE-VI.md) / [`GUIDE-EN.md`](.claude/skills/claude-pack/GUIDE-EN.md)
- **README:** [`.claude/skills/claude-pack/README.md`](.claude/skills/claude-pack/README.md)
- **Operating contract:** [`.claude/skills/claude-pack/SKILL.md`](.claude/skills/claude-pack/SKILL.md)

### What it does NOT do

- No remote upload — use `gh release upload` manually.
- No GPG signing in v1 — SHA256 sidecar only.
- No merge-resolver — the recipient installer skips existing skills; `FORCE_OVERWRITE=1` opts in.
- No multi-project packing — one `.claude/` root per bundle.
- No zip / tar.zst — tar.gz only in v1.

---

## Bilingual (product-spec)

- The interview asks questions in your chosen language (`--lang en` or `--lang vi`).
- LLM-generated prose (vision narrative, story descriptions, AC) is written in your chosen language.
- IDs (`BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1-S1`) and frontmatter keys (`personas`, `scope`, `moscow`, …) stay English so
  the structure is stable.
- Visualization labels (`Now/Next/Later`, `Must/Should/Could/Won't`) localize when you pass `--lang vi`.

Vietnamese phrasing is native-reviewed for natural wording.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python3: command not found` | Install Python 3.11+ from [python.org](https://www.python.org/downloads/). |
| `bash: install.sh: Permission denied` | `chmod +x .claude/skills/<skill>/install.sh` then re-run. |
| Windows: scripts blocked | Run installers with `powershell -ExecutionPolicy Bypass -File .\…\install.ps1`. |
| `pip install` hangs | Check your connection; install needs one-time PyPI + (product-spec) CDN access. After install, the skills run offline. |
| product-spec: HTML visualization shows a blank diagram | Re-run the product-spec installer to re-vendor the Mermaid engine. |
| Claude Code doesn't see a skill | Make sure you opened Claude Code in your project folder (the one containing `.claude/`), then restart it. |
| Running scripts from a workspace under `/tmp/...` can't see the `.venv` binary | Some sandbox harnesses block `/tmp/...` reads from outside the workspace. Run scripts from your project root, or install deps against the system `python3` and invoke that interpreter explicitly. |

---

## Privacy

Both skills make **no network calls at runtime**. product-spec's one-time installer downloads the Mermaid, marked, and
DOMPurify runtimes from the public CDN (`cdn.jsdelivr.net`); each is then stored locally as `mermaid.min.js` /
`marked.min.js` / `purify.min.js` and verified against a pinned SHA-256 hash. (Degraded-install caveat: if
`mermaid.min.js` failed to vendor, product-spec's Mermaid **graph** views fall back to a `cdn.jsdelivr.net` `<script>` at
browser-render time — re-run the installer to vendor it; ASCII and body views never reach a CDN.) claude-pack's safety
filter **always drops** `.env`/secrets/keys, `.git/`, runtime caches, and session state from any bundle — non-removable
via any flag.

---

## Need help?

Each skill can answer most "how do I…" questions — invoke it and ask. For installer issues, re-run the POSIX installer
with `bash -x .claude/skills/<skill>/install.sh` to see each step. For deeper detail, start from the skill's `GUIDE-*.md`
and `SKILL.md`.
