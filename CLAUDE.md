# Product Spec — LLM Operating Guide

Auto-loaded by Claude Code in this project. Tells you (the LLM) how to operate the **`cleanmatic:product-spec`** skill on behalf of the product owner who installed it here.

The PO is **non-technical**. Talk in product language. Personas, problems, value, scope, acceptance — that vocabulary. No code, no engineering jargon (story points, velocity, OKRs, ARRs) unless the PO uses them first.

---

## Five Operating Principles

### 1. Frontmatter is the source-of-truth

Every artifact's YAML frontmatter carries the structural facts: `id`, parent links, `status`, `scope`, `moscow`, `horizon`, `owner`, `personas`, `metrics`. **Always parse YAML; never infer structure from headings or prose.** When in doubt, read the frontmatter. When writing, fill the frontmatter completely.

### 2. DRY — one authoritative home per fact

- Persona labels live in `PRODUCT.md`; full persona narrative lives in `vision.md`.
- Business goals live in `brd.md` only.
- Feature-area scope lives in the PRD for that feature.
- Stories carry AC; PRDs never duplicate them.

Cross-reference by ID. If a fact would appear in two places, one is authoritative and the other is a link.

### 3. Script vs LLM split — non-negotiable

| Layer | Owns |
|-------|------|
| **Scripts** (Python, deterministic, structural-only) | parse frontmatter · build the directed graph · count AC presence · detect orphans / dangling links / unaddressed parents / duplicate IDs · resolve IDs · emit JSON findings |
| **LLM** (you, judgment) | INVEST quality of stories · vagueness · core-value alignment (`aligned` / `weak` / `off`) · gold-plating · semantic duplication · contradiction with prior decisions · prose narrative |

If a check requires *reading* the language and weighing meaning, it's the LLM's job. If it can be answered by a graph traversal or a regex against a closed enum, it's the script's job. **Always invoke the scripts before inferring graph state from the file tree.**

### 4. No silent reversals

A contradiction with an `approved`-status artifact must be surfaced verbatim, with three options for the PO:

- **Keep** the approved version (reject the new claim).
- **Change** to the new claim (and re-approve the affected artifact).
- **Hybrid** (record both, plan a follow-up).

The skill never auto-flips an approved decision. Same rule for `--validate`: if your judgment says "this PRD drifts from `PRODUCT.md`'s core value" but the PRD is `approved`, surface the conflict — do not edit silently.

### 5. Never overwrite manual prose

On `--update` (delta-update), flag the affected downstream nodes and **ask** before regenerating. The PO decides. Default = flag only; regeneration is opt-in per node.

---

## Parent-Scoped ID Grammar

| Artifact | ID form | Example |
|----------|---------|---------|
| BRD goal | `BRD-G<n>` | `BRD-G1` |
| PRD | `PRD-<SLUG>` | `PRD-AUTH` |
| Epic | `PRD-<SLUG>-E<n>` | `PRD-AUTH-E1` |
| Story | `PRD-<SLUG>-E<n>-S<n>` | `PRD-AUTH-E1-S1` |

`<SLUG>`: uppercase ASCII letters/digits, hyphen permitted but prefer flat, ≤16 chars. `<n>`: the next free integer **within that parent**, allocated by `generate_templates.py`. Parent-scoped means globally unique by construction and lineage-readable — no central counter.

---

## Bilingual Conventions

- `lang: en` (default) or `lang: vi` — declared per artifact and per interview session.
- **Frontmatter keys** stay English regardless of `lang`: `personas`, `metrics`, `moscow`, `scope`, `horizon`, `status`, `owner`, `prd`, `epic`, `brd_goals`, `version`, `created`, `updated`.
- **IDs** stay English: `BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1-S1`.
- **Prose** (vision narrative, story descriptions, AC), AskUserQuestion text, options, and markdown headings localize per `lang`.
- **Visualization labels** (`Now/Next/Later`, `Must/Should/Could/Won't`) localize via `scripts/i18n_labels.py` when `--lang vi`.
- Vietnamese ships best-effort. On the first VI session, note that native-speaker review of phrasing is pending.

---

## Workflow Pointers (load on demand)

For each flag, load the relevant reference from `.claude/skills/product-spec/references/`:

| Flag | Reference |
|------|-----------|
| `--product`, `--brd`, `--prd`, `--epic`, `--story`, no-flag init | `workflow-interview.md` |
| `--validate`, `--strict`, `--approve`, `--summary` | `workflow-validate.md` |
| `--auto`, `--update` | `workflow-auto-and-update.md` |
| `--viz`, `--format`, `--lang` | `visualization-spec.md` (+ `scripts/visualize.py`) |

Load only the references relevant to the active flag. Don't pre-load everything.

---

## Script CLI Contract

All scripts live under `.claude/skills/product-spec/scripts/` and accept:

```
<script>.py --root <project-dir> [--lang en|vi] [other flags]
```

`--root` defaults to CWD. Scripts emit JSON to stdout. Analytical scripts always exit 0; `--strict` gating is your job, not the script's. The single exception is `strict_gate.py`, a CI-side wrapper that re-runs the analytical scripts and exits `2` on `error` findings — usable from shell pipelines without an LLM.

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
- `generate_templates.py` — instantiate an artifact from `assets/templates/` with `{{token}}` substitution; allocates the next parent-scoped ID.
- `visualize.py` — 9 views × 3 formats (ASCII, Mermaid, self-contained HTML).
- `install-vendor-mermaid.sh` — one-time vendor of the Mermaid runtime (called from `install.sh`).

---

## What This Skill Does NOT Do

- **No code generation.** This is a spec skill. If the PO asks "write the API", redirect: stories + AC, the engineering team writes code.
- **No engineering-unit estimation.** Stories carry `size: S | M | L` — never story points, never hours.
- **No prose overwrite on update.** Flag, don't rewrite.
- **No runtime external network calls.** Everything runs from the local install (vendored Mermaid, stdlib + pyyaml). The one-time installer is the only network step.
- **No SVG/PNG output.** Visualizations are ASCII, Mermaid (markdown-fenced), or self-contained HTML.

---

## Failure & Drift Handling

- **Frontmatter parse error** → script emits a `parse_error` finding; do not crash, surface to the PO.
- **Missing parent (dangling link)** → script flags `dangling_link`; do not invent the parent.
- **Conflicting status** (e.g., story `approved` under epic `draft`) → flag `status_inconsistency`; surface to PO.
- **Stale `.session.md`** (answers reference IDs no longer in the spec) → on resume, ask "**Resume from saved state** / **Discard and restart**".
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

- **ASCII** → plain text on stdout. Default; zero deps.
- **Mermaid** → a fenced markdown block. For views Mermaid can't express cleanly (`heatmap`, `persona`, `risk`, no-baseline `delta`), the renderer emits a plain ` ``` ` fence with the ASCII fallback inside (the dispatcher routes the HTML path accordingly).
- **HTML** → a self-contained file under `docs/product/visuals/<view>-<timestamp>.html`. Mermaid runtime embedded inline for views that need it; omitted for ASCII-fallback views to keep file size small.

All renders are deterministic: same input → same output. The graph JSON is the single source of truth (`scripts/spec_graph.py`).

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
└── visuals/              (rendered visualizations)
    └── .snapshots/       (graph-snapshot JSONs for delta/diff)
```

The skill never writes outside `docs/product/`.
