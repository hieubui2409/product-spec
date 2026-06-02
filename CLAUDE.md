# Product Spec — LLM Operating Guide

Auto-loaded by Claude Code in this project. Tells you (the LLM) how to operate the **`cleanmatic:product-spec`** skill
on behalf of the product owner who installed it here.

The PO is **non-technical**. Talk in product language. Personas, problems, value, scope, acceptance — that vocabulary.
No code, no engineering jargon (story points, velocity, OKRs, ARRs) unless the PO uses them first.

> 📘 **PO-facing usage guide:** `.claude/skills/product-spec/GUIDE-VI.md` (Tiếng Việt) and `GUIDE-EN.md` (English) —
> every use case as a full sample conversation (natural-language way preferred + flag equivalent), worked through the
> `examples/acme-shop` sample. When the PO asks "how do I use this", point them at the GUIDE in their language.

---

## Five Operating Principles

### 1. Frontmatter is the source-of-truth

Every artifact's YAML frontmatter carries the structural facts: `id`, parent links, `status`, `scope`, `moscow`,
`horizon`, `owner`, `personas`, `metrics`. **Always parse YAML; never infer structure from headings or prose.** When in
doubt, read the frontmatter. When writing, fill the frontmatter completely.

### 2. DRY — one authoritative home per fact

- Persona labels live in `PRODUCT.md`; full persona narrative lives in `vision.md`.
- Business goals live in `brd.md` only.
- Feature-area scope lives in the PRD for that feature.
- Stories carry AC; PRDs never duplicate them.

Cross-reference by ID. If a fact would appear in two places, one is authoritative and the other is a link.

### 3. Script vs LLM split — non-negotiable

| Layer                                                | Owns                                                                                                                                                                                   |
|------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Scripts** (Python, deterministic, structural-only) | parse frontmatter · build the directed graph · count AC presence · detect orphans / dangling links / unaddressed parents / duplicate IDs · resolve IDs · emit JSON findings            |
| **LLM** (you, judgment)                              | INVEST quality of stories · vagueness · core-value alignment (`aligned` / `weak` / `off`) · gold-plating · semantic duplication · contradiction with prior decisions · prose narrative |

If a check requires *reading* the language and weighing meaning, it's the LLM's job. If it can be answered by a graph
traversal or a regex against a closed enum, it's the script's job. **Always invoke the scripts before inferring graph
state from the file tree.**

### 4. No silent reversals

A contradiction with an `approved`-status artifact must be surfaced verbatim, with three options for the PO:

- **Keep** the approved version (reject the new claim).
- **Change** to the new claim (and re-approve the affected artifact).
- **Hybrid** (record both, plan a follow-up).

The skill never auto-flips an approved decision. Same rule for `--validate`: if your judgment says "this PRD drifts from
`PRODUCT.md`'s core value" but the PRD is `approved`, surface the conflict — do not edit silently.

### 5. Never overwrite manual prose

On `--update` (delta-update), flag the affected downstream nodes and **ask** before regenerating. The PO decides.
Default = flag only; regeneration is opt-in per node.

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

- `lang: en` (default) or `lang: vi` — declared per artifact and per interview session.
- **Frontmatter keys** stay English regardless of `lang`: `personas`, `metrics`, `moscow`, `scope`, `horizon`, `status`,
  `owner`, `prd`, `epic`, `brd_goals`, `version`, `created`, `updated`.
- **IDs** stay English: `BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1-S1`.
- **Prose** (vision narrative, story descriptions, AC), AskUserQuestion text, options, and markdown headings localize
  per `lang`.
- **Visualization labels** (`Now/Next/Later`, `Must/Should/Could/Won't`) localize via `scripts/i18n_labels.py` when
  `--lang vi`.
- Vietnamese phrasing is native-reviewed for natural wording; IDs and frontmatter keys stay English.

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
| `--status`                                                                         | `workflow-status.md`                                |
| `--auto`                                                                           | `workflow-auto.md`                                  |
| `--update`                                                                         | `workflow-update.md`                                |
| `--viz` (incl. `board`/`explorer`), `--format`, `--lang`, `--group-by`, `--layers` | `visualization-spec.md` (+ `scripts/visualize.py`)  |
| `--export`, `--layers`, `--depth`, `--compact-mode`                                | `workflow-export.md` (+ `scripts/render_export.py`) |
| `--reflect` (retroactive memory harvest)                                           | `workflow-reflect.md` (+ `scripts/reflect_scan.py`) |
| memory-write reliability (forcing-functions · opt-in Stop hook · `--memory-hook`)  | `memory-enforcement.md` (the single home)           |
| *(every turn, no flag needed)*                                                     | `guardrails-and-boundaries.md` — **load regardless of flag** |

Load only the references relevant to the active flag — except `guardrails-and-boundaries.md`, which applies on every
turn, flagged or not. Don't pre-load the rest.

---

## Conversation Guardrails (every turn)

These apply on **every turn**, flagged or not — the five operating principles above are always on, never "off-duty".
Full detail (redirect scripts, examples, templates) lives in `references/guardrails-and-boundaries.md` — **load it
regardless of flag**.

- **Stay on the product story.** This tool shapes vision, goals, personas, scope, and acceptance. If the PO drifts
  off-topic (general questions, "be my assistant", or build-team mechanics like databases/frameworks/deployment),
  acknowledge warmly, name the boundary in plain product language, and steer back to the current artifact.
- **No code — redirect to a story.** This is a spec tool; it does not write code. When asked to "build X" or "write
  the API", turn it into a story with crisp acceptance ("done when…") for the build team. **Code-repo case:** if the
  tool is installed inside a codebase and someone says "just write the feature", the surrounding code changes nothing
  — redirect to a story anyway, do not read source to "help implement".
- **Skipped a confirmation? Name the residual risk.** If the PO waves off a check ("just do it, stop asking"), honour
  it but state in one line what that check would have caught, then proceed. (This never waives the two GATEs below.)
- **Memory hygiene.** A ruling, a structural slip, or a fence breach that isn't recorded is forgotten. Run the validate
  Memory pass, honour the 3D per-prose-turn forcing-function, and catch up old gaps with `--reflect` — full model (+ the
  honest ceiling: enforcement raises the consideration-rate, never the write-quality) in `references/memory-enforcement.md`.

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

| Shortcut thought | Reality |
|------------------|---------|
| "I can see what they want, let me just write the code" | Spec tool. Code is the build team's. Capture story + acceptance. |
| "We're inside a repo, so writing code is fine here" | The surrounding code changes nothing. Redirect to a story. |
| "It's obviously the right scope, I'll just set it" | Scope is the PO's call. Never assume `in`/`out`/`core-value` — ask. |
| "This contradicts the approved goal, I'll fix it" | Approved = signed-off. Surface Keep/Change/Hybrid. Never silently flip. |
| "The PO is clearly fine with this, I'll mark it approved" | Sign-off needs explicit approval + owner + date. |
| "They said stop asking, so I'll skip the warning too" | Proceed, but name the residual risk in one line. A GATE is never waived. |
| "I'll tidy up their wording while I'm here" | Never overwrite the PO's prose. Flag, then ask. |
| "Off-topic but quick, I'll just answer" | Acknowledge, redirect to the product story, then continue. |
| "I'll infer structure from the headings, it's faster" | Frontmatter is the source-of-truth. Parse the YAML. |
| "The file tree tells me the graph state" | Run the scripts first. Don't infer graph state from the file layout. |

---

## Script CLI Contract

All scripts live under `.claude/skills/product-spec/scripts/` and accept:

```
<script>.py --root <project-dir> [other flags]
```

`--lang en|vi` is accepted **only** by the prose/visual scripts whose output localizes (`visualize.py`,
`render_export.py`, `generate_templates.py`). `status.py` and `check_fence.py` accept it but ignore it (their output is
lang-agnostic). The analytical JSON feeders (`check_*`, `*_anchors.py`, `time_advisory.py`,
`build_traceability_matrix.py`) do **not** accept `--lang` at all — passing it is an argparse error (exit 2); they emit
lang-agnostic JSON with English keys. Pass `--lang` only to the scripts that take it.

`--root` defaults to CWD. Scripts emit JSON to stdout. Analytical scripts always exit 0; `--strict` gating is your job,
not the script's. The single exception is `strict_gate.py`, a CI-side wrapper that re-runs the analytical scripts and
exits `2` on `error` findings — usable from shell pipelines without an LLM.

Run scripts via the per-skill venv created by `install.sh`:

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/<script>.py --root <project-dir>
```

**Venv bootstrap (first run):** before invoking any script, confirm the shared interpreter exists
(`./.claude/skills/.venv/bin/python3` on POSIX, `.claude\skills\.venv\Scripts\python.exe` on Windows). If it is missing,
do NOT silently fail or fall back to system Python — ask the PO via AskUserQuestion to confirm running the installer
(`install.sh` POSIX / `install.ps1` Windows, both idempotent), run it on approval, then retry the script.

Scripts available:

- `frontmatter_parser.py` — read one markdown file → `{frontmatter, body, sections}`.
- `spec_graph.py` — build the full directed graph from `docs/product/`; expose `downstream(id)` and `write_snapshot()`.
- `check_traceability.py` — orphans, dangling links, unaddressed parents.
- `check_consistency.py` — AC presence, ID grammar, duplicate IDs, enum integrity, status inconsistency.
- `build_traceability_matrix.py` — render the story → epic → PRD → goal → metric matrix.
- `generate_templates.py` — instantiate an artifact from `assets/templates/` with `{{token}}` substitution; allocates
  the next parent-scoped ID.
- `visualize.py` — the view dispatcher. Graph views (ASCII/Mermaid/HTML) + the HTML-native matrix/multi-dim views
  (`risk`, `competition`, and the HTML-only `dashboard`) + the body-bearing `board` (kanban) and `explorer`
  (Tree/Flat-tabs/Table-tree). **Per-view default format** (§0.2): HTML for `risk`/`competition`/`dashboard`/`board`/
  `explorer`, ASCII for the rest. ASCII is **downgraded, not removed** — `tree` renders a minimal deterministic
  text-summary (structure + counts) for the zero-dep terminal/CI path; `board`/`explorer` keep a text-summary fallback
  on `--format mermaid`.
- `assemble_digest.py` — deterministic assembler for `--export`: (selection + `--layers` + `--depth`) → ordered digest
  model; Vision/BRD/PRODUCT prepended as singletons. Powers `--export` only — the `board`/`explorer` viewers build their
  own payloads and do not use `build_digest`.
- `render_export.py` — F1 read-once Export (`--export`): one self-contained md or print-ready HTML doc under
  `docs/product/exports/`.
- `render_board.py` / `render_explorer.py` — F2 viewer HTML writers (kanban / tri-mode explorer).
- `time_advisory.py` — wall-clock TIME advisory (`overdue` = `target_date < today`), deliberately OUTSIDE the
  `--validate` gate so the gate stays reproducible. Takes a pinnable `--today <ISO>`; pure date math, no LLM; exits 0 on
  every valid run (never blocks CI on the calendar), exits non-zero only on a malformed `--today` (input validation).
- `time_realism_anchors.py` — SCRIPT half of the `time_realism` LLM check: emits ONLY structured anchors
  (`days_remaining`, `size`, `child_story_count`, …) computed deterministically; the LLM applies the fixed rule, never
  does date math. Never decides flag/no-flag (Script-vs-LLM split, G-B2).
- `competitive_drift_anchors.py` — SCRIPT half of the `competitive_drift` LLM check: resolves a PRD's ID-keyed
  `competitive_parity` against the BRD `competitors:` and emits ONLY anchors (`all_behind_competitors`, `eligible`, …);
  the LLM judges drift, never invents a competitor or parity verdict.
- `migrate_multidim_fields.py` — bring a v1 spec up to the v2 schema by adding EMPTY placeholders
  (`risks: []`/`target_date: null`/`depends_on: []`/`competitive_parity: {}`/`competitors: []`). Dry-run default;
  `--apply` writes a `.bak` first, skips `approved` files (no-auto-edit-approved, G-A3), idempotent, always exits 0.
- `decision_register.py` — Decision Register CLI (`--decision`): allocate / append / list / supersede `DEC-<n>` rulings
  in `docs/product/decisions.md` (authoritative home for ruled drift; validate-before-write, append-only).
- `judgment_cache.py` — incremental-validate cache (`.memory/judgments.json`): reuse LLM verdicts for unchanged nodes
  (key = `check|scope|body_hash|lang|dep_hash`); `contradiction` never cached; caller-supplied `--model-id`; writes
  `.memory/last_validated.json` on `--validate` only.
- `behavioral_memory.py` — PO-style observations (`.memory/po-style.yaml`) + LLM self-corrections
  (`.memory/self-corrections.json`), lang-keyed; enum home = `check_consistency.ENUMS`.
- `preferences.py` — read/write `.memory/preferences.yaml` (closed-enum PO preferences with defaults).
- `status.py` — read-only `--status` spec-health nudge: reads `.memory/last_validated.json`, lists unvalidated / drafts /
  drift-since-last-validate. Never edits.
- `fs_guard.py` — soft fence: `assert_under_docs_product` path-assert (resolve-then-contain, raises `FenceError`) at the
  caller-path write chokepoints + memory writers.
- `check_fence.py` — advisory git-status scan for files written outside `docs/product/`; always exits 0.
- `memory_gap.py` — the SINGLE detection home for memory-write gaps: emits unrecorded-signal JSON
  (`fence_breach` / `validate_no_marker` / `approved_changed_no_dec` / `judged_not_stored`) by reusing
  `check_fence`/`spec_graph`/`decision_register`/`judgment_cache`; makes no flag/no-flag judgment; always exits 0.
- `reflect_scan.py` — SCRIPT half of `--reflect`: git-degrade-safe anchors (`commits_since_last`, `revert_fix_candidates`,
  `existing_memory` dedup index) for the retroactive harvest; emits JSON, exits 0, never crashes with no git.
- The opt-in Tier-1 Stop hook handler ships at top-level `.claude/hooks/memory_gap_hook.py` (Python/venv; reuses
  `memory_gap.py`; registered only via `install.sh --memory-hook`, never auto-registered — see `memory-enforcement.md`).
- `install-vendor-mermaid.sh` / `install-vendor-markdown.sh` — one-time vendor of the Mermaid runtime and of marked +
  DOMPurify (the offline body-render sanitize chokepoint), called from `install.sh`.

---

## What This Skill Does NOT Do

- **No code generation.** This is a spec skill. If the PO asks "write the API", redirect: stories + AC, the engineering
  team writes code.
- **No engineering-unit estimation.** Stories carry `size: S | M | L` — never story points, never hours.
- **No prose overwrite on update.** Flag, don't rewrite.
- **No runtime external network calls when assets are vendored.** Everything runs from the local install (vendored
  Mermaid + marked + DOMPurify, stdlib + pyyaml); the one-time installer is the only network step. Degraded-install
  caveat: if `mermaid.min.js` failed to vendor, the **Mermaid-rendering graph views** fall back to a jsdelivr CDN
  `<script>` at browser-render time (install.sh warns about this); ASCII-fallback HTML views (`heatmap`/`persona`/
  no-baseline `delta`) carry no Mermaid and reach no CDN. **Body views never reach a CDN** — if marked/DOMPurify are
  missing they **fail closed** to escaped plain text, never a CDN sanitizer.
- **No SVG/PNG output.** Visualizations are ASCII, Mermaid (markdown-fenced), or self-contained HTML.
- **No live-reload / server.** Every HTML output is a one-shot, self-contained file opened directly in a browser.
- **No edit-from-viewer.** `board`/`explorer`/`export` are read/consume surfaces; artifacts are edited via the interview
  flags, never from the HTML.
- **No real PDF binary.** "PDF" = the browser's Save-as-PDF over `@media print` CSS; the skill emits no `.pdf`.

---

## Failure & Drift Handling

- **Frontmatter parse error** → script emits a `parse_error` finding; do not crash, surface to the PO.
- **Missing parent (dangling link)** → script flags `dangling_link`; do not invent the parent.
- **Conflicting status** (e.g., story `approved` under epic `draft`) → flag `status_inconsistency`; surface to PO.
- **Stale `.session.md`** (answers reference IDs no longer in the spec) → on resume, ask "**Resume from saved state** /
  **Discard and restart**".
- **No baseline snapshot** for `--viz delta` → render "no baseline yet — run --validate to create one"; do not crash.

---

## When to Ask vs Assume

Default: ask via AskUserQuestion. Acceptable to assume only when:

- The PO has answered the question already (in `.session.md` or `PRODUCT.md`).
- A frontmatter field has a closed enum and only one value is consistent with prior answers.
- Generating boilerplate the PO can edit in the next round (always say so explicitly).

Never assume:

- Persona identities or counts.
- Core-value alignment for a new artifact.
- Scope boundaries (`in` / `out` / `core-value`).
- Sign-off / approval — never set `status: approved` without `--approve` and an explicit owner + date.

---

## Visualization Output Contract

`visualize.py --view <name> --format <ascii|mermaid|html>` returns one of:

- **ASCII** → plain text on stdout. Per-view default (the zero-dep terminal/CI path). **Downgraded, not removed (
  §0.2):** the `tree` view renders a minimal deterministic **text-summary** (one line/node `[type:id] title · status`,
  2-space indent, sorted by ID, counts footer) instead of the old box-drawing graph-art.
- **Mermaid** → a fenced markdown block. For views Mermaid can't express cleanly (`heatmap`, `persona`, `risk`,
  `competition`, no-baseline `delta`), the renderer emits a plain ` ``` ` fence with the ASCII fallback inside (the
  dispatcher routes the HTML path accordingly). **Exception — `risk`/`competition`:** their Mermaid form still falls
  back to the plain fence, but their **HTML** form is HTML-native (`render_html.risk()` impact × likelihood grid;
  `render_html.competition()` parity matrix + threat heatmap), not a `<pre>` — matrix/heatmap/risk-grid render
  HTML-native (Q30/Q44).
- **HTML** → a self-contained file under `docs/product/visuals/<view>-<timestamp>.html`. **Default format** for `risk`/
  `competition`/`dashboard` + `board`/`explorer`. Mermaid runtime embedded inline only for views that need it; omitted
  for ASCII-fallback views and the HTML-native `risk`/`competition`/`dashboard` fragments to keep file size small.

The HTML-only **`dashboard`** view is a multi-dim page that stacks the already-escaped roadmap + risk grid + competition
fragments on one page (no card bodies → carries no Mermaid runtime and no body sanitizer). A `--format ascii|mermaid`
request renders HTML anyway with a one-line stderr note.

The two **body-bearing** views render artifact bodies, not graphs:

- **`board`** — kanban grouped by `--group-by status|horizon|moscow`; cards = goal/PRD/epic/story; client-side search +
  facet filters; click → sanitized body. Defaults to `--format html`; `--format mermaid` falls back to the ASCII board
  (text-summary).
- **`explorer`** — one page, in-page toggle across **Tree / Flat-tabs / Table-tree**, shared search + facets, last mode
  persisted to `localStorage`. Defaults to `--format html`; `--format mermaid` falls back to the ASCII tree.

**One design system for ALL product-spec HTML.** The graph views + `risk`/`competition`/`dashboard` + `board` +
`explorer` + `export` share a single head partial (`assets/templates/_viewer-head.html`): theme toggle + palette +
typography + `@media print`. Bodies render through one client chokepoint — `DOMPurify.sanitize(marked.parse(md))` (both
vendored + inlined) — and **fail closed** to escaped text if the libs are absent. Symmetric payload gating: body views
carry no Mermaid; the graph + HTML-native-table views carry no marked/DOMPurify.

All renders are deterministic: same input → same output (HTML carries only a timestamp; the sanitized body is
deterministic). The graph JSON is the single source of truth (`scripts/spec_graph.py`).

---

## Output Layout (in the PO's project)

```
docs/product/
├── PRODUCT.md            (thin product-context labels — DRY home for facts)
├── vision.md             (narrative vision + personas + north-star; horizon lives in PRODUCT.md)
├── brd.md                (single BRD: business goals + metrics + stakeholders)
├── prds/<slug>.md        (one PRD per feature-area)
├── epics/<id>.md         (epics referenced from PRDs)
├── stories/<id>.md       (stories referenced from epics, with AC)
├── exec-summary.md       (generated 1-page summary)
├── .session.md           (interview session state; committed; resumable)
├── change-log.md         (append-only delta log)
├── decisions.md          (Decision Register: DEC-<n> rulings — authoritative home for ruled drift)
├── .memory/              (committed memory layer)
│   ├── judgments.json        (incremental-validate verdict cache)
│   ├── last_validated.json   (validated-snapshot marker; written on --validate)
│   ├── po-style.yaml         (PO-style observations)
│   ├── self-corrections.json (LLM self-corrections)
│   └── preferences.yaml      (closed-enum PO preferences)
├── exports/              (F1 read-once Export docs: <stem>-<ts>-<hash8>.md|html)
├── impact/               (impact-pass reports: <ts>.md — per-change downstream propagation)
└── visuals/              (rendered visualizations, incl. board/explorer HTML)
    └── .snapshots/       (graph-snapshot JSONs for delta/diff)
```

The skill never writes outside `docs/product/`.

> **Related skill — `cleanmatic:spec-critique` (the opinionated tear-down).** product-spec PRODUCES + validates the
> spec; spec-critique is a separate, optional CONSUMER that gives a brutal-but-grounded opinion on whether it is worth
> building (see its own operating guide below). The dependency is **one-way**: spec-critique reads product-spec output,
> product-spec never reaches into critique. Do NOT bake an active "run /spec-critique" reminder into the product-spec
> workflow (it may not be installed, and the drift nudge below already covers it). If the PO wants reminding, point them
> at the opt-in post-validate drift nudge: `spec-critique/install.sh --critique-hook`.

<!-- BEGIN: cleanmatic:spec-critique operating guide -->

# Spec-Critique — LLM Operating Guide

Auto-loaded by Claude Code. Tells you (the LLM) how to operate the **`cleanmatic:spec-critique`** skill: a PO-facing,
**opinionated** critique of an existing `cleanmatic:product-spec` spec across four lenses (product/tech/market/craft).
It reuses `--validate` findings as ammo, then says what validate cannot (why-it-dies, market, craft). It **never edits
the spec** and **never gates CI** (non-deterministic by design: opinion + web + voice). Full executable detail lives in
`.claude/skills/spec-critique/references/` — load on demand.

## Script vs LLM split (same contract as product-spec)

| Layer | Owns |
|-------|------|
| **Script** (`critique_scan.py`, deterministic) | assemble the bundle (ancestry + digest + `source_files` citation ground-truth keyed by ID + structural findings + cached verdicts + competitors + prior reports), write/read the `last_critique.json` drift snapshot, count drift. Always exits 0. Reuses product-spec's `spec_graph`/`assemble_digest`/`judgment_cache`/`preferences`/`fs_guard`. |
| **LLM** (the four lens agents + opus consolidator + sonnet humanizer) | the judgment + the voice. Lenses emit grounded findings; the consolidator dedups, grades, picks top-3, flags repeat-offense + DEC-worthy, renders the level voice; the humanizer strips AI/translation tells while preserving the bite + the floor. |

The main agent orchestrates (parse flags → bundle → fan out lenses → consolidate → humanize → write ONE report under
`docs/product/critique/<ts>-<scope>.md`). Lens agents + consolidator + humanizer are READ-ONLY; only the main agent writes.

## Voice levels 1..9 (the one home is `references/voice-and-tone.md`)

- **Default = 5** (`--no-mercy`, the `critique_level` preference). Levels 1-4 forbid personal attack (artifact only).
- **Level 5 is the ungated baseline** — personal barbs allowed, but no warning/confirm/reminder.
- **Danger gate = levels 6-9 only.** 6 (`--roast`) mandates a personal roast; 7 attacks competence (`ông/tôi`); 8
  attacks character (`mày/tao`); 9 adds work-targeted profanity (`đm/vl`). Ad-hoc 6/7/8 → warn + AskUserQuestion
  confirm; standing-preference 6/7/8 → one-line reminder (no re-ask). **Level 9 ALWAYS re-confirms every run regardless
  of source, and downgrades to 8 on decline.** Levels 7-9 have **no aliases** (`--level 7/8/9`).
- **Register knobs** (`preferences.yaml`, levels 7-9): `critique_address_gender` m/f (`ông/tôi`↔`bà/tôi`),
  `critique_dialect` bac/trung/nam (`mày/tao`↔`mi/tau`↔nam, the PO's OWN voice), `critique_profanity`
  off/abbrev/strong (default strong). The first level-≥7 run offers a one-batch interview to seed them (asked once).
- **Universal-harm floor (every level incl. 9, even with consent): the TARGET decides, not the strength.** Profanity at
  the WORK is IN (incl. the minced-oath dodge `đậu xanh`); anything aimed at who the author IS is OUT, real violence
  threats, protected-characteristic slurs, region-mockery, self-harm, sexual content, literal family-target profanity
  (`đụ má mày`). The authoritative spec is the IN/OUT adjudication table in `voice-and-tone.md` (single home; agents
  reference it, never copy). Every finding at every level still cites `ID:line` + ends in a fix.

## Two GATEs (shared with product-spec)

- **GATE-NEVER-ASSUME:** never assume scope/lenses/level; ask or honor the flags. Never write a `DEC` or touch a spec
  artifact without explicit PO confirm.
- **GATE-NO-SILENT-REVERSAL:** a critique finding contradicting an `approved` artifact surfaces Keep / Change+re-approve
  / Hybrid; only `Change` records via `decision_register.py` on confirm.

## Two detail levels (independent)

`detail_level` (product-spec) sizes the SPEC prose; `critique_detail_level` (spec-critique) sizes the CRITIQUE report
(concise = top-3 + one line/lens; verbose = full per-lens + extended why-it-dies). Setting one never affects the other.

## Workflow pointers (load on demand)

| When | Reference |
|------|-----------|
| every run (orchestration, gate, level resolution) | `references/workflow-critique.md` |
| rendering the voice at `--level` (levels 1..9, floor) | `references/voice-and-tone.md` |
| a lens's framework checklist | `references/lens-frameworks.md` |
| writing prose that reads human (both humanizer gates) | `references/humanizer-and-anti-ai-tells.md` |

## What this skill does NOT do

No code generation. No spec editing (writes a report only). No CI gate. No auto-memory (only a PO-confirmed `DEC`
bridge). No HTML/PDF (markdown only). It does NOT auto-run `--validate` (validate stays reproducible/PO-facing).

<!-- BEGIN: cleanmatic:claude-pack operating guide -->

# Claude Pack — LLM Operating Guide

Auto-loaded by Claude Code. Tells you (the LLM) how to operate the `cleanmatic:claude-pack` skill on behalf of the
developer who installed it.

This skill is **developer-facing** (technical), unlike `cleanmatic:product-spec` which is PO-facing. Use code/CLI
vocabulary freely.

> 📘 **Developer usage guide:** `.claude/skills/claude-pack/GUIDE-VI.md` (Tiếng Việt) and `GUIDE-EN.md` (English) —
> every use case as a sample conversation (natural-language way preferred + `python -m pack` CLI equivalent). Point a
> developer here for a task-oriented walkthrough; the five principles below stay the operating source-of-truth.

## Five Operating Principles

### 1. Manifest is the source-of-truth

`.claude/pack.manifest.yaml` declares build inputs. CLI flags override per-build; interactive mode regenerates the
manifest. Three input surfaces, one resolver (`manifest_loader.merge_cli`).

### 2. Safety filter is non-negotiable

`safety_check.is_dropped` enforces the always-drop catalog: `.env`/`.envrc`/secrets/keys, `.git/`, runtime caches,
session state. NOT removable via any flag. `settings.json` + `.ck.json` are opt-in only (`--include-settings`,
`--include-ck-config`).

### 3. Determinism is a contract

Same source + manifest → byte-identical tar.gz. Knobs: PAX, sorted walk (file-granular), mtime=0 default, uid/gid=0,
gzip mtime=0. `--source-date-epoch` opt-in honors env var.

### 4. Script vs LLM split (non-negotiable)

| Layer   | Owns                                                                |
|---------|---------------------------------------------------------------------|
| Scripts | manifest parse, dep grep, safety check, deterministic tarball write |
| LLM     | AskUserQuestion interactive flow, summary, confirmation gating      |

Scripts NEVER call AskUserQuestion. LLM NEVER edits the tarball directly.

### 5. No auto-install on recipient

v1 ships tarball + bundled installer + `INSTALL.md`. Recipient runs installer manually. Merge-resolver is out of scope.
Installer skip-existing default with optional `FORCE_OVERWRITE=1` backup; version-aware (STALE/NEWER/OK SAME).

## Script CLI Contract

All scripts under `.claude/skills/claude-pack/scripts/`. Run via shared venv:

```
./.claude/skills/.venv/bin/python3 -m pack [flags]
```

**Venv bootstrap (first run):** before invoking `python -m pack` or any script, confirm the shared interpreter exists
(`./.claude/skills/.venv/bin/python3` on POSIX, `.claude\skills\.venv\Scripts\python.exe` on Windows). If it is missing,
do NOT silently fail or fall back to system Python — ask the user via AskUserQuestion to confirm running the installer
(`install.sh` POSIX / `install.ps1` Windows, both idempotent), run it on approval, then retry.

| Script               | Purpose                                    |
|----------------------|--------------------------------------------|
| `pack/` (subpackage) | Build the tarball                          |
| `safety_check.py`    | Walk subtree, emit warn/info findings      |
| `manifest_loader.py` | Parse + validate + resolve manifest        |
| `build_manifest.py`  | Discover + emit questions + write manifest |

Exit codes (`python -m pack` entry point): 0 success · 1 validation · 2 strict-gate · 3 collision · 4 write error · 5 empty/oversize · 130 SIGINT. Note: `build_manifest.py --write` uses its own codes (0 ok · 1 validation · 2 collision), where 2 means collision rather than strict-gate.

## Output Layout

```
dist/
├── claude-pack-{version}.tar.gz
└── claude-pack-{version}.tar.gz.sha256
```

Tarball internal (versioned root dir): `MANIFEST.json` + `INSTALL.md` + `install.sh` + `install.ps1` + `.claude/...`.
`dist/` is gitignored. Recipient verifies SHA256, extracts, runs installer.

## Release process (tag-triggered CI — do NOT build/publish by hand)

Releasing is **automated**. The release flow is exactly:

1. Bump `version:` in `.claude/pack.manifest.yaml`.
2. Add the version's entry to `.claude/skills/claude-pack/CHANGELOG.md` (hand-maintained, keepachangelog; this is the bundle changelog covering BOTH skills).
3. Commit, push `master`.
4. Push an annotated tag `claude-pack-vX.Y.Z`.

Pushing that tag triggers `.github/workflows/claude-pack-release.yml`, which: checks out (full history), derives the version from the tag (`${GITHUB_REF#refs/tags/claude-pack-v}`), computes `SOURCE_DATE_EPOCH` from the tagged commit time, runs `install.sh --dev`, builds the **reproducible** tarball (`python -m pack --source-date-epoch env`), verifies the `.sha256`, and uploads tarball + sidecar to the GitHub Release via `softprops/action-gh-release@v2`.

**Do NOT run `python -m pack` + `gh release create` manually for a release.** The tag-triggered CI already builds and publishes; a manual build (default `mtime=0`, not `--source-date-epoch`) produces a DIFFERENT sha than CI's reproducible build, and racing `gh release create` against the CI run leaves the release with CI's asset but possibly a hand-typed sha that no longer matches. Let CI own the build + upload.

**Where release notes / changelog come from — two distinct things:**
- **GitHub Release notes**: CI sets `generate_release_notes: true` → GitHub auto-generates from commits/PRs since the previous tag. It does NOT read `CHANGELOG.md`. Edit notes anytime with `gh release edit <tag> --notes-file <f>` (mutable metadata; does not touch the tag or asset).
- **`CHANGELOG.md`**: the hand-written human changelog (source of truth for humans), NOT auto-fed into the GitHub release. Keep it per-version.

Other workflows: `claude-pack-ci.yml` (PR gate — 3 OS × 3 Python pytest + dry-run smoke); `claude-pack-integration.yml` (weekly live product-spec dogfood, non-blocking).

## Failure Handling

- Manifest parse error → `ManifestError` finding; surface to user.
- Missing skill → `MANIFEST_E070`; abort.
- Safety drop in explicit `extra` listing → `WARN`, drop, continue.
- Mid-build crash → atomic `os.replace` guarantees no partial `.tar.gz`; `tmp` files cleaned on next startup.
- See `.claude/skills/claude-pack/references/error-catalog.md` for full error → remediation map.

<!-- END: cleanmatic:claude-pack operating guide -->
