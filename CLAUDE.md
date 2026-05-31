# Product Spec — LLM Operating Guide

Auto-loaded by Claude Code in this project. Tells you (the LLM) how to operate the **`cleanmatic:product-spec`** skill
on behalf of the product owner who installed it here.

The PO is **non-technical**. Talk in product language. Personas, problems, value, scope, acceptance — that vocabulary.
No code, no engineering jargon (story points, velocity, OKRs, ARRs) unless the PO uses them first.

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
| `--product`, `--brd`, `--prd`, `--epic`, `--story`, no-flag init                   | `workflow-interview.md`                             |
| `--validate`, `--strict`, `--approve`, `--summary`                                 | `workflow-validate.md`                              |
| `--auto`, `--update`                                                               | `workflow-auto-and-update.md`                       |
| `--viz` (incl. `board`/`explorer`), `--format`, `--lang`, `--group-by`, `--layers` | `visualization-spec.md` (+ `scripts/visualize.py`)  |
| `--export`, `--layers`, `--depth`, `--compact-mode`                                | `workflow-export.md` (+ `scripts/render_export.py`) |

Load only the references relevant to the active flag. Don't pre-load everything.

---

## Script CLI Contract

All scripts live under `.claude/skills/product-spec/scripts/` and accept:

```
<script>.py --root <project-dir> [--lang en|vi] [other flags]
```

`--lang` is accepted by the prose/visual scripts whose output localizes (`visualize.py`, `render_export.py`,
`generate_templates.py`); the analytical JSON feeders (`check_*`, `*_anchors.py`, `time_advisory.py`,
`build_traceability_matrix.py`) emit lang-agnostic JSON with English keys and ignore it.

`--root` defaults to CWD. Scripts emit JSON to stdout. Analytical scripts always exit 0; `--strict` gating is your job,
not the script's. The single exception is `strict_gate.py`, a CI-side wrapper that re-runs the analytical scripts and
exits `2` on `error` findings — usable from shell pipelines without an LLM.

Run scripts via the per-skill venv created by `install.sh`:

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/<script>.py --root <project-dir>
```

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
├── exports/              (F1 read-once Export docs: <stem>-<ts>-<hash8>.md|html)
├── impact/               (impact-pass reports: <ts>.md — per-change downstream propagation)
└── visuals/              (rendered visualizations, incl. board/explorer HTML)
    └── .snapshots/       (graph-snapshot JSONs for delta/diff)
```

The skill never writes outside `docs/product/`.

<!-- BEGIN: cleanmatic:claude-pack operating guide -->

# Claude Pack — LLM Operating Guide

Auto-loaded by Claude Code. Tells you (the LLM) how to operate the `cleanmatic:claude-pack` skill on behalf of the
developer who installed it.

This skill is **developer-facing** (technical), unlike `cleanmatic:product-spec` which is PO-facing. Use code/CLI
vocabulary freely.

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

## Failure Handling

- Manifest parse error → `ManifestError` finding; surface to user.
- Missing skill → `MANIFEST_E070`; abort.
- Safety drop in explicit `extra` listing → `WARN`, drop, continue.
- Mid-build crash → atomic `os.replace` guarantees no partial `.tar.gz`; `tmp` files cleaned on next startup.
- See `.claude/skills/claude-pack/references/error-catalog.md` for full error → remediation map.

<!-- END: cleanmatic:claude-pack operating guide -->
