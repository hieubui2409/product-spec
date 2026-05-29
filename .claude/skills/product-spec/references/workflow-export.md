# Workflow — `--export` (F1 read-once Export)

Assemble a spec slice into **one self-contained doc** (markdown or print-ready HTML) for stakeholders, a single-pass read, or an LLM feed. Built on the deterministic assembler (`scripts/assemble_digest.py`, `build_digest`), which powers `--export` only. The `--viz board` / `--viz explorer` viewers build their own payloads (`render_board` / `render_explorer`) and do **not** share the digest — they filter by artifact type (`goal,prd,epic,story`), whereas `--export --layers` uses doc-layer buckets (`vision,brd,prd,epic,story`).

Run via the repo venv:

```bash
./.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/render_export.py \
  --root <project-dir> --export <all|ID|list> [flags]
```

## Selection model — `--export` + `--layers` (combined)

`--export` chooses the **subtree**; `--layers` filters which **types** appear.

| `--export` | Resolves to |
|------------|-------------|
| `all` | the whole spec: vision + BRD + every goal/PRD/epic/story |
| `<ID>` (e.g. `PRD-AUTH`) | that node + its ancestor context + its descendants |
| `<ID>,<ID>,…` | the union of each ID's slice |
| `VISION` / `BRD` / `PRODUCT` | the context singleton, emitted **once** (not edge-walked) |

`--layers` is a comma subset of `vision,brd,prd,epic,story` (default: all). Goals belong to the `brd` layer. **Vision, BRD and PRODUCT are context singletons** — the assembler loads them from their files and **prepends them once** whenever their layer is included and the selection has spec content to contextualize, or when they are explicitly selected. They are never edge-walked, so `--export VISION` cannot render vision twice.

**No silent-empty doc.** `render_export.py` exits non-zero (writing nothing) when: a selection names an ID that resolves to nothing (typo, wrong case, deleted node); a selection resolves to no artifacts at all; `--layers` names a token outside `vision,brd,prd,epic,story` (e.g. a typo, or a viewer-vocab `goal`); a non-`all` selection is filtered to empty by `--layers` (e.g. `--export VISION --layers prd`); or `--export all` whose `--layers` strips all pre-existing content (e.g. `--export all --layers story` on a spec with no stories). The stderr message names the offending value and the valid set. It never writes a frontmatter-only doc (CLAUDE.md: no silent failure). Only `--export all` on a genuinely empty/fresh spec (nothing to filter) is the one allowed-empty case.

### `--layers` precedence (owner-locked, D2) + the H5 warning

`--layers` is authoritative: an excluded type is dropped **even if it is the selected root's own type**. To avoid a silently context-less doc, the assembler emits a **provenance warning** in the doc header when this happens.

```bash
# Drops the PRD/epic/goal/vision context — keeps only the PRD's stories:
render_export.py --root . --export PRD-AUTH --layers story
```
→ header carries: `⚠ --layers ['story'] excluded the PRD layer; 1 selected prd(s) appear only via their included sub-layers (e.g. PRD-AUTH).` One warning is emitted **per excluded type** (not per node), so `--export all --layers prd` over many goals/epics/stories yields a few warnings, not one per artifact.

Precedence itself is **not** changed without owner sign-off. The warning is the mitigation.

## Depth presets — `--depth` (default `context`)

| `--depth` | Ancestors / Vision-BRD singletons | Target + descendants |
|-----------|-----------------------------------|----------------------|
| `context` (default) | struct (compacted) | full |
| `full` | full | full |
| `brief` | struct | struct |

`struct` = frontmatter + title + key fields (stories → AC count; goals → metrics; BRD → goal titles). `full` = the artifact's narrative body (+ AC items for stories).

## Compaction — `--compact-mode` (default `struct`)

| Mode | Who compacts | Output |
|------|--------------|--------|
| `struct` (default) | the **script**, deterministically | struct sections render the key-field skeleton |
| `llm` | the **LLM**, in the same skill invocation | struct sections emit the **full** body wrapped in `<!-- COMPACT:<id> --> … <!-- /COMPACT:<id> -->` markers |

**Script-vs-LLM split is non-negotiable: the script NEVER summarizes.** `--compact-mode llm` runs as **2 steps in ONE skill invocation**:

1. The skill runs `render_export.py --compact-mode llm` → a doc with full bodies + `<!-- COMPACT:<id> -->` markers around the sections to condense.
2. The LLM, in the same call, rewrites the text **between each marker pair** into a tight summary, leaving everything else byte-for-byte unchanged → one finished file.

> `--compact-mode llm` requires **`--format md`**. With `--format html` the combo is **rejected** (non-zero exit): DOMPurify strips HTML comments, so the `<!-- COMPACT -->` markers vanish from the rendered page and no `.md` is written for the step-2 rewrite. Use `md`+`llm` or `html`+`struct`.

## Format — `--format` (default `md`)

- `md`: deterministic markdown — provenance frontmatter + TOC (anchors from IDs) + sections in hierarchy order. Stories include AC.
- `html`: a **linear print-friendly** doc (TOC, no interactive nav/search — distinct from `explorer`'s chrome). The provenance frontmatter is **stripped** from the HTML body (it is a `.md`-only affordance; the page shows the same metadata in its `.ps-meta` header), then the markdown is embedded as an inert JSON island and rendered client-side through the sanitize chokepoint `DOMPurify.sanitize(marked.parse(md))`. Save-as-PDF via the browser (`@media print`). Headings localize per `--lang`.

## Output

`docs/product/exports/<stem>-<ts>-<hash8>.<md|html>`

- `<stem>` = `all` | sanitized single ID | sorted IDs joined `_` (length-capped with a hashed tail for long lists).
- `<hash8>` = 8-char SHA-256 of the **timestamp-free** body, so identical content yields a stable filename and same-second re-exports never collide.
- The skill writes **only** under `docs/product/`. `exports/` is created on demand.

## Examples

```bash
# Whole spec, one markdown doc:
render_export.py --root . --export all

# One feature for a stakeholder, full detail, as a print-ready page:
render_export.py --root . --export PRD-AUTH --depth full --format html

# Two PRDs, LLM-condensed context:
render_export.py --root . --export PRD-AUTH,PRD-CHECKOUT --compact-mode llm

# Stories only (note the header warning about dropped context):
render_export.py --root . --export PRD-AUTH --layers story
```

## v1 limits

- Relative links inside artifact bodies (`[x](./foo.md)`) render inert / as text (not resolved).
- "PDF" = browser Save-as-PDF via `@media print`; no binary PDF is produced.
