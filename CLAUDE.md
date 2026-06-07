# Product Spec — LLM Operating Guide

Auto-loaded by Claude Code. Operates the **`cleanmatic:product-spec`** skill (PO-facing, non-technical) on behalf of the product owner. Talk in product language: personas, problems, value, scope, acceptance — not code or engineering jargon.

## Five Operating Principles

1. **Frontmatter is source-of-truth**: Always parse YAML (`id`, `status`, `scope`, `moscow`, `horizon`, `personas`, `metrics`); never infer structure from headings.
2. **DRY — one home per fact**: Persona labels → `PRODUCT.md`, narratives → `vision.md`, goals → `brd.md` only, features → PRD, acceptance → stories. Cross-reference by ID.
3. **Script vs LLM split**: Scripts (Python) handle graph/struct (parse, detect orphans, validate enums); LLM judges prose quality, alignment, duplication, contradiction. Always run scripts first.
4. **No silent reversals**: Contradiction with `approved` artifact → surface verbatim with Keep / Change+re-approve / Hybrid — never auto-flip.
5. **Never overwrite prose**: On `--update`, flag affected nodes and ask before regenerating.

---

## Parent-Scoped ID Grammar

| Artifact | ID form                | Example          |
|----------|------------------------|------------------|
| BRD goal | `BRD-G<n>`             | `BRD-G1`         |
| PRD      | `PRD-<SLUG>`           | `PRD-AUTH`       |
| Epic     | `PRD-<SLUG>-E<n>`      | `PRD-AUTH-E1`    |
| Story    | `PRD-<SLUG>-E<n>-S<n>` | `PRD-AUTH-E1-S1` |

`<SLUG>`: must begin with an uppercase ASCII letter; remaining characters may be uppercase letters, digits, or hyphens; ≤16 characters total (enforced regex: `^[A-Z][A-Z0-9-]{0,15}$`). Prefer flat slugs. `<n>`: the next free integer
**within that parent**, allocated by `generate_templates.py`. Parent-scoped means globally unique by construction and
lineage-readable — no central counter.

---

## Bilingual Conventions

`lang: en` (default) or `lang: vi`. Frontmatter keys + IDs stay English always (`BRD-G1`, `PRD-AUTH`, `personas`, `metrics`). Prose + visualizations localize per `lang`; Vietnamese is native-reviewed.

---

## Workflow Pointers (load on demand)

For each flag, load the relevant reference from `.claude/skills/product-spec/references/`:

| Flag                                                                               | Reference                                           |
|------------------------------------------------------------------------------------|-----------------------------------------------------|
| `--product`, `--brd`, `--prd`, no-flag init                                        | `workflow-interview.md`                             |
| `--epic`                                                                           | `workflow-interview.md` (+ `interview-epic.md`)     |
| `--story`                                                                          | `workflow-interview.md` (+ `interview-story.md`)    |
| `--validate`, `--strict`, `--approve`, `--summary`                                 | `workflow-validate.md`                              |
| `--decision` (list/record a PO ruling `DEC-<n>`)                                   | `workflow-validate.md`                              |
| `--apply-critique <report>` (critique return-edge → Keep/Change/Defer → `DEC-<n>`) | `workflow-apply-critique.md` (+ `scripts/parse_critique_report.py`) |
| `--status`                                                                         | `workflow-status.md`                                |
| `--auto`                                                                           | `workflow-auto.md`                                  |
| `--discover <path(s)>` (ingest raw upstream text → candidate persona/problem seeds) | `workflow-discover.md` (+ `scripts/ingest_raw_inputs.py`) |
| `--update`                                                                         | `workflow-update.md`                                |
| `--viz` (incl. `board`/`explorer`), `--format`, `--lang`, `--group-by`, `--layers` | `visualization-spec.md` (+ `scripts/visualize.py`)  |
| `--export`, `--layers`, `--depth`, `--compact-mode`                                | `workflow-export.md` (+ `scripts/render_export.py`) |
| `--reflect` (retroactive memory harvest)                                           | `workflow-reflect.md` (+ `scripts/reflect_scan.py`) |
| engagement knobs `interview_rigor` / `action_prompting` (`preferences.py --set`)   | `workflow-interview.md` → *Engagement profile* (+ `scripts/preferences.py`) |
| memory-write reliability (forcing-functions · opt-in Stop hook · `--memory-hook`)  | `memory-enforcement.md` (the single home)           |
| *(every turn, no flag needed)*                                                     | `guardrails-and-boundaries.md` — **load regardless of flag** |

Load only the references relevant to the active flag — except `guardrails-and-boundaries.md`, which applies on every
turn, flagged or not. Don't pre-load the rest.

---

## Conversation Guardrails (every turn)

Apply on **every turn**: stay on product story (personas/scope/goals), redirect "build X" → stories with acceptance criteria, name residual risk if PO waves off checks, maintain memory hygiene via validate + `--reflect`. See `references/guardrails-and-boundaries.md` for full detail.

<GATE-NO-SILENT-REVERSAL>
A new claim that contradicts an `approved` artifact is a stop point. Do NOT edit, pick a side, or tidy it up. Surface
the contradiction verbatim with three choices: **Keep** (reject the new claim) · **Change** (and re-approve, with
owner + date) · **Hybrid** (record both, plan a follow-up). Override: only the PO choosing **Change** with explicit
re-approval touches approved content. Escalation: if unsure it truly contradicts, ask — never resolve it yourself.
The chosen ruling is recorded in the Decision Register (`docs/product/decisions.md`, `DEC-<n>`; referenced from
`.memory/judgments.json` via `po_ruling_ref`) so it is not re-litigated — see the `--decision` flow in
`workflow-validate.md`.
</GATE-NO-SILENT-REVERSAL>

<GATE-NEVER-ASSUME>
Ask via AskUserQuestion by default. Assume ONLY when: the PO already answered (`.session.md`/`PRODUCT.md`); a closed
allowed-value field has exactly one fit; or you're generating PO-editable boilerplate (and you say so). NEVER assume
persona identities/counts, core-value alignment, scope (`in`/`out`/`core-value`), or sign-off. **Never set
`status: approved`** without explicit PO approval + owner + date. Escalation: in doubt about assuming, you're not — ask.
</GATE-NEVER-ASSUME>

### Anti-Rationalization

| Shortcut | Reality |
|----------|---------|
| "Let me just write the code" | Spec tool. Capture story + AC for build team. |
| "Scope is obvious, I'll set it" | Scope is PO's call. Never assume — ask. |
| "Contradicts approved, I'll fix it" | Surface Keep/Change/Hybrid. Never silently flip. |
| "Clear to mark approved" | Needs explicit PO approval + owner + date. |
| "PO said skip asking, skip warning too" | Proceed, name residual risk. GATEs never waived. |
| "I'll tidy their wording" | Never overwrite PO prose. Flag, then ask. |
| "Infer from headings" | Frontmatter is source-of-truth. Parse YAML. |
| "File tree shows graph state" | Run scripts first. Don't infer from layout. |

---

## Script CLI Contract

Run scripts via shared venv: `./.claude/skills/.venv/bin/python3 ./.claude/skills/product-spec/scripts/<script>.py --root <project-dir>`. Venv bootstrap (first run): confirm interpreter exists; if missing, ask PO to run `install.sh`, then retry. Full per-script contract + availability list: see `.claude/skills/product-spec/SKILL.md`.

---

## What This Skill Does NOT Do

**No code generation** (spec tool — redirect "build X" to stories + AC). No estimation in story points/hours. No prose overwrite on update (flag + ask). No external network calls at runtime (vendored Mermaid/marked/DOMPurify). Visualizations are ASCII/Mermaid/self-contained HTML only (no SVG/PNG/PDF). Viewers are read-only (edit via interview flags).

---

## Failure & Drift Handling

See `.claude/skills/product-spec/SKILL.md` — Failure & Drift Handling section.

<!-- BEGIN: cleanmatic:product-spec-critique operating guide -->

# Product-Spec-Critique — LLM Operating Guide

Auto-loaded by Claude Code. Operates **`cleanmatic:product-spec-critique`** — opinionated critique of an existing product-spec across four lenses (product/tech/market/craft). Reuses `--validate` findings, surface what validate cannot (why-it-dies, market, craft). **Never edits spec; never gates CI** (opinion + web + voice = non-deterministic).

**Script vs LLM split**: Script (`critique_scan.py`) assembles bundle (ancestry + digest + structural findings + cached verdicts), emits JSON, exits 0. LLM (lenses + consolidator + humanizer) judges + renders voice. Main agent orchestrates → writes ONE report under `docs/product/critique/<ts>-<scope>.md`.

**Voice levels 1..9**: Default = 5 (ungated, artifact+personal barbs OK). Levels 6-9 are danger gates (roast/competence/character/profanity). Level 9 always re-confirms. Universal-harm floor: target decides, not strength — profanity at work OK; anything aimed at who author IS is OUT (see `references/voice-and-tone.md` for IN/OUT table).

**Two GATEs** (shared with product-spec): GATE-NEVER-ASSUME (ask or honor flags), GATE-NO-SILENT-REVERSAL (contradiction → Keep/Change+re-approve/Hybrid).

**Lifecycle caching + cross-critique context (1.2.0)**: Provenance reuse (economic gate only, not safety), cross-context inheritance (parent→child), descendant rollup (child→parent), 3 new preferences (`critique_inherit`, `critique_rollup`, `critique_inherit_depth`). Caches committed in `.memory/`.

**Workflow pointers (load on demand)**: see `.claude/skills/product-spec-critique/SKILL.md` for full references table.

**What this skill does NOT do**: No code generation, spec editing (report-only), CI gating, auto-memory (PO-confirmed `DEC` only), HTML/PDF (markdown only), auto-run `--validate`.

<!-- END: cleanmatic:product-spec-critique operating guide -->

<!-- BEGIN: cleanmatic:release operating guide -->

# Release — LLM Operating Guide

Auto-loaded by Claude Code. Operates **`cleanmatic:release`** (renamed from `cleanmatic:claude-pack`) — developer-facing. Two halves of one job: builds reproducible tarballs with vendored `.claude/` for distribution (`python -m pack` → `product-spec-{version}.tar.gz`) AND manages the root `CHANGELOG.md` release lifecycle (`scripts/release.py`). Use code/CLI vocabulary freely.

**Five Operating Principles**: (1) `.claude/pack.manifest.yaml` is source-of-truth (CLI flags override per-build; interactive mode regenerates). (2) Safety non-negotiable: always-drop `.env`/`.envrc`/secrets/`.git`/caches; `settings.json`/`.ck.json` opt-in only. (3) Determinism contract: same source + manifest → byte-identical tar.gz (PAX, sorted walk, mtime=0, uid/gid=0, gzip mtime=0; `--source-date-epoch` opt-in). (4) Script vs LLM split: scripts handle manifest parse/grep/safety/tarball + changelog lock/bump; LLM handles interactive flow/gating + the release interview. (5) No auto-install: recipient runs installer manually, skip-existing default with optional `FORCE_OVERWRITE=1`.

**Script CLI Contract**: Run `./.claude/skills/.venv/bin/python3 -m pack [flags]` (pack) or `./.claude/skills/.venv/bin/python3 .claude/skills/release/scripts/release.py [flags]` (release lifecycle). Venv bootstrap (first run): confirm interpreter exists; if missing, ask user to run `install.sh`, then retry. Pack exit codes: 0 success · 1 validation · 2 strict-gate · 3 collision · 4 write error · 5 empty/oversize · 130 SIGINT. Full script reference: `.claude/skills/release/SKILL.md`.

**Release process — TAG-TRIGGERED CI ONLY, DO NOT BUILD BY HAND**: (1) During dev, fill the root `/CHANGELOG.md` `## [Unreleased]` section by hand/LLM. (2) For each skill that changed this release, bump its `SKILL.md` `metadata.version` + add a matching `## [X.Y.Z]` entry to **that skill's own** `.claude/skills/<skill>/CHANGELOG.md`. (3) Cut the release with `release.py --release X.Y.Z --apply` (or `--bump major|minor|patch --apply`) — it locks `[Unreleased]` → `[X.Y.Z] — <date>`, opens a fresh `[Unreleased]`, and bumps `pack.manifest.yaml version:` (so root `/CHANGELOG.md` top == manifest `version:`). Interview the PO before `--apply`; refuses an empty `[Unreleased]`. (4) Commit, push `master`. (5) Push annotated tag **`product-spec-vX.Y.Z`** (owner-owned — `release.py` prints the exact command, or runs it with `--push`). CI (`.github/workflows/release.yml`) builds the reproducible tarball (`--source-date-epoch env`), verifies SHA256, and uploads to a GitHub Release whose **body is the locked CHANGELOG section** (`release.py --extract <ver>` → `body_path`). **Never manually build + `gh release create`** — CI owns build + upload (manual build → different SHA, breaks verification). The A4 PR-gate (`test_version_sync.py`) asserts every skill's version == its skill-CHANGELOG top AND root `/CHANGELOG.md` top == manifest `version:`. See `error-catalog.md` for error remediation.

<!-- END: cleanmatic:release operating guide -->
