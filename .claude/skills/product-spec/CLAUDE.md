# LLM Operating Guide — `cleanmatic:product-spec`

This file is the **LLM-facing** operating guide for running the skill. Read it before driving the interview, generating artifacts, validating, decomposing brain-dumps, or rendering visualizations. SKILL.md is the entry surface; this file carries the principles.

## Audience

The user invoking this skill is a **non-technical product owner**. Talk in product language. No code in conversational responses. No engineering jargon (story points, ARRs, velocity, OKRs unless the PO uses them). Personas, problems, value, scope, success — that vocabulary.

## Five Operating Principles

### 1. Frontmatter is the source-of-truth

Every artifact's YAML frontmatter carries the structural facts: ID, parent links, status, scope, MoSCoW, horizon, owner, personas, metrics. **Scripts parse YAML; the LLM never infers structure from headings or prose.** When in doubt about structure, read the frontmatter. When writing, fill the frontmatter completely.

### 2. DRY — one authoritative home per fact

- Persona definitions live in `PRODUCT.md` (labels) and `vision.md` (narrative).
- Business goals live in `brd.md` only.
- Feature-area scope lives in the PRD for that feature.
- Stories carry AC; PRDs do not duplicate them.

Cross-reference by ID. Never duplicate prose; if a fact would appear in two places, one is authoritative and the other is a link.

### 3. Script vs LLM split — non-negotiable

| Layer | Owns |
|-------|------|
| **Scripts** (deterministic, Python, structural-only) | parse frontmatter · build the directed graph · count AC presence · detect orphans / dangling links / unaddressed parents / dup IDs · resolve IDs · emit JSON findings |
| **LLM** (judgment) | INVEST quality of stories · vagueness · core-value alignment (aligned / weak / off) · gold-plating · semantic duplication · contradiction with prior decisions · prose narrative |

If a check requires *reading* the language and weighing meaning, it belongs to the LLM. If it can be answered by a graph traversal or a regex against a closed enum, it belongs to a script. **Do not** infer the graph by reading files — always invoke the scripts first.

### 4. No silent reversals

A contradiction with an approved decision (in an `approved`-status artifact) must be surfaced verbatim with three options for the PO:
- **Keep** the approved version (reject the new claim).
- **Change** to the new claim (and re-approve).
- **Hybrid** (record both, ask follow-up).

The skill never auto-flips an approved decision based on a new answer. Same rule for `--validate`: if the LLM's judgment says "this PRD drifts from PRODUCT.md's core-value" but the PRD is `approved`, surface the conflict — do not edit silently.

### 5. Never overwrite manual prose

When delta-update flags an affected downstream node, present the change and ask **whether** to regenerate. The PO decides. Default = flag only; regeneration is opt-in.

## Bilingual Conventions

- `lang: en` (default) or `lang: vi` — frontmatter field per artifact and session.
- All **frontmatter keys** stay English: `personas`, `metrics`, `moscow`, `scope`, `horizon`, `status`, `owner`, `parent`, `prd`, `epic`, `brd_goal`, `version`, `created`, `updated`.
- All **IDs** stay English: `BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1-S1`.
- Prose, AskUserQuestion text, options, and headings localize per `lang`.
- VI ships best-effort; on first VI run, note that native-speaker review is pending.

## Parent-Scoped ID Grammar

| Artifact | ID form | Example |
|----------|---------|---------|
| BRD goal | `BRD-G<n>` | `BRD-G1` |
| PRD | `PRD-<SLUG>` | `PRD-AUTH` |
| Epic | `PRD-<SLUG>-E<n>` | `PRD-AUTH-E1` |
| Story | `PRD-<SLUG>-E<n>-S<n>` | `PRD-AUTH-E1-S1` |

`<SLUG>` is uppercase, kebab-allowed-but-prefer-flat-uppercase, ≤16 chars, derived from the PRD feature-area name. `<n>` is the next free integer **within that parent**, allocated by `generate_templates.py`. Parent-scoped means: globally unique by construction, lineage readable, no global counter needed.

## Workflow Pointers

For each flag, load the relevant reference:

- `--product`, `--brd`, `--prd`, `--epic`, `--story`, no-flag init → `references/workflow-interview.md`
- `--validate`, `--strict`, `--approve`, `--summary` → `references/workflow-validate.md`
- `--auto`, `--update` → `references/workflow-auto-and-update.md`
- `--viz`, `--format` → `references/visualization-spec.md` (+ `scripts/visualize.py`)

These workflow references are filled out in Phase 7. The skeleton files exist in Phase 1; do not refer to them until they carry content.

## Script CLI Contract

All scripts live under `scripts/` and accept:

```
<script>.py --root <project-dir> [--lang en|vi] [other flags]
```

`--root` defaults to CWD. Scripts emit JSON to stdout (`{"findings": [...], "graph": {...}}` or view-specific JSON). Scripts always exit 0; `--strict` gating is the LLM's job, not the script's.

Run scripts via the repo venv:

```bash
./.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/<script>.py --root <project-dir>
```

## What This Skill Does NOT Do

- **No code generation** — this is a spec skill. If the PO asks "write the API," redirect: stories and AC, the engineering team writes code.
- **No estimation in engineering units** — stories carry `size: S|M|L`, not story points.
- **No prose overwrite on update** — flag, don't rewrite.
- **No external network calls** — everything runs from the repo (vendored Mermaid, stdlib + pyyaml).
- **No SVG/PNG output** — visualizations are ASCII, Mermaid, or self-contained HTML.

## Failure & Drift Handling

- Frontmatter parse error → emit a `parse_error` finding, do not crash. Report drift; let the PO fix.
- Missing parent (dangling link) → script flags as `dangling_link` finding; LLM does not invent the parent.
- Conflicting status (e.g., story `approved` under epic `draft`) → flag as `status_inconsistency`; surface to PO.
- Stale `.session.md` (answers don't match current PRODUCT.md) → on resume, offer **resume from saved state** or **discard and restart**.

## When to Ask Versus Assume

Default: ask via AskUserQuestion. Acceptable to assume only when:
- The PO has answered the question already (in `.session.md` or PRODUCT.md).
- A frontmatter field has a closed enum and only one value is consistent with prior answers.
- Generating boilerplate that the PO can edit in the next round (always say so).

Never assume:
- Persona identities or counts.
- Core-value alignment for a new artifact.
- Scope boundaries (in / out / core-value).
- Sign-off / approval — never set `status: approved` without `--approve` and explicit owner+date.
