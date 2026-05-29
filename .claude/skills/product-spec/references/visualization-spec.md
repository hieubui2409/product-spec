# Visualization Spec

The views × formats matrix, the graph-JSON shape consumed by every renderer, and the flag → view mapping. **SVG/PNG dropped** (validate gate decision) — no external Mermaid-CLI binary; HTML uses **Mermaid JS vendored inline** for offline self-containment. Two body-bearing views — `board` and `explorer` — render artifact **bodies** (not graphs) and additionally vendor **marked + DOMPurify** inline for an offline sanitize chokepoint.

## Formats

| Format | When | Notes |
|--------|------|-------|
| `ascii` | terminal / log review | default. zero deps. always available. |
| `mermaid` | embed in markdown docs | emits a fenced ```mermaid block. Valid v11 syntax. |
| `html` | share / browse interactively | self-contained file. Mermaid JS vendored inline. opens with no server, no network. |

## Views

| View | Flag | What it shows |
|------|------|---------------|
| `tree` | `--viz tree` | full traceability tree: Vision → PRODUCT → BRD → goals → PRDs → epics → stories. |
| `heatmap` | `--viz heatmap` | status grid: rows = artifact type, cols = status (draft/review/approved); cells = count. |
| `scope` | `--viz scope` | scope/value map: in / out / core-value × MoSCoW grid. |
| `roadmap` | `--viz roadmap` | timeline: now / next / later. groups artifacts by `horizon`. |
| `persona` | `--viz persona` | persona × feature coverage: rows = persona, cols = PRD/epic, cells = story count. |
| `gap` | `--viz gap` | gap-analysis: BRD goals with no PRDs; PRDs with no epics; epics with no stories. Structural-only — sufficiency judgment is separate. |
| `moscow` | `--viz moscow` | MoSCoW quadrant: must/should/could/wont distribution across stories. |
| `risk` | `--viz risk` | risk matrix: impact (rows) × likelihood (cols) from `risks` frontmatter on epics/PRDs. |
| `delta` | `--viz delta [--snapshot <name>]` | diff between two graph snapshots from `docs/product/visuals/.snapshots/`. |
| `board` | `--viz board [--group-by status\|horizon\|moscow] [--layers …]` | kanban: columns = the group field, cards = goal/PRD/epic/story; client-side search + facet filters (status/moscow/persona/layer); click a card → its sanitized body. Default `--format html`. |
| `explorer` | `--viz explorer [--layers …]` | one page, in-page toggle across **Tree** (collapsible nav) / **Flat-tabs** (per layer) / **Table-tree** (treegrid w/ metadata columns); shared search + facets; last mode persisted to `localStorage`. Default `--format html`. |

## View × Format Matrix

The 9 graph views support all 3 formats. The 2 body views default to HTML and fall back to their ASCII renderer on `--format mermaid` (they carry no Mermaid by design).

| View | ASCII | Mermaid | HTML |
|------|-------|---------|------|
| `tree` | tree characters (├ │ └) | `flowchart BT` | Mermaid + collapse/zoom JS |
| `heatmap` | ASCII table | `quadrantChart` or text fallback | Mermaid embed |
| `scope` | 2D ASCII grid | `quadrantChart` | Mermaid embed |
| `roadmap` | grouped lists (now/next/later) | `timeline` | Mermaid embed |
| `persona` | ASCII table (persona × feature) | text fallback (`pre`) | Mermaid embed |
| `gap` | ASCII bullet list of unaddressed nodes | `flowchart LR` with gap nodes highlighted | Mermaid embed |
| `moscow` | 2×2 ASCII grid | `quadrantChart` (must/should × could/wont) | Mermaid embed |
| `risk` | 3×3 ASCII grid | text fallback (`pre`) | Mermaid embed |
| `delta` | unified-diff-style text | `flowchart TB` with +/− tags | Mermaid embed |
| `board` | grouped lists per `--group-by` | → ASCII board (note on stderr) | **default** — kanban + search/facets + click→sanitized body |
| `explorer` | = `tree`; with `--layers` an orphan-rooted forest (surviving nodes whose parent was filtered out become roots, like the HTML explorer) | → ASCII tree (note on stderr) | **default** — Tree/Flat-tabs/Table-tree + search/facets |

If a Mermaid view type can't cleanly express a view (e.g., `heatmap`-as-quadrant is awkward), the Mermaid output falls back to a text fallback inside a `pre` block. Document the fallback in the renderer's comment. Body views (`board`/`explorer`) have no Mermaid form at all — `--format mermaid` falls back to their ASCII renderer with a one-line note on stderr.

## Graph JSON Shape (single source of truth)

Every renderer consumes this shape (produced by `spec_graph.py` and persisted in snapshots).

```json
{
  "version": "1.0",
  "generated_at": "<ISO 8601>",
  "product": {
    "name": "<from PRODUCT.md>",
    "core_value": "<from PRODUCT.md>",
    "personas": ["shopper", "store-admin"]
  },
  "nodes": [
    {
      "id": "BRD-G1",
      "type": "goal",
      "title": "<title or first-line summary>",
      "status": "approved",
      "scope": "in",
      "moscow": "must",
      "horizon": "now",
      "size": null,
      "personas": [],
      "metrics": ["conversion-rate"],
      "owner": "Jane Doe",
      "version": "1.0.0",
      "file": "brd.md"
    }
  ],
  "edges": [
    {"from": "PRD-AUTH", "to": "BRD-G1", "kind": "brd_goal"},
    {"from": "PRD-AUTH-E1", "to": "PRD-AUTH", "kind": "prd"},
    {"from": "PRD-AUTH-E1-S1", "to": "PRD-AUTH-E1", "kind": "epic"}
  ],
  "risks": [
    {"node": "PRD-AUTH-E1", "description": "OAuth dependency", "impact": "high", "likelihood": "med"}
  ]
}
```

`edges[].kind` records the field name used in the child's frontmatter (`epic`, `prd`, `brd_goal`) — keeps the graph self-describing.

## Renderer Inputs / Outputs

- **Input:** graph JSON (from stdin OR via `--root <dir>` triggering `spec_graph.py` internally).
- **Output:**
  - ASCII → stdout (terminal-safe; no ANSI colors by default; `--color` flag opt-in).
  - Mermaid → stdout (a fenced ```mermaid block ready to paste into docs).
  - HTML → file in `docs/product/visuals/<view>-<timestamp>.html`.

## Flag → View / Format Mapping

```
--viz <view>            # default --format ascii
--viz <view> --format mermaid
--viz <view> --format html

--viz delta             # uses two most-recent snapshots
--viz delta --snapshot <name>     # explicit baseline
```

`--lang en|vi` localizes labels in the rendered output (e.g., "now/next/later" → "bây giờ/tiếp/sau"). IDs, edges, and frontmatter values stay English.

## HTML Self-Containment

Each HTML output is a single file with:
- The shared design-system head (inline `<style>` + theme + helper JS; no external fonts).
- Graph views: inline Mermaid JS (vendored at `assets/vendor/mermaid.min.js`) + one `<div class="mermaid">…</div>` + zoom JS.
- Body views (`board`/`explorer`/`export`): inline marked + DOMPurify (`assets/vendor/marked.min.js`, `purify.min.js`) + an inert JSON data island; the client builds metadata via safe DOM APIs and bodies via the chokepoint `DOMPurify.sanitize(marked.parse(md))`.

The HTML opens with no server and no network. Vendored libs are pinned + SHA-verified + committed. **Symmetric payload gating:** graph views inline no marked/DOMPurify; body views inline no Mermaid. If the markdown libs are missing, body views **fail closed** to escaped text + a visible banner — never a CDN sanitizer.

## HTML Design System (one source for every view)

All HTML outputs — the 9 `--viz` graph views + `board` + `explorer` + `--export --format html` — share **one** head partial (`assets/templates/_viewer-head.html`), included by every shell via the `{{viewer_head}}` token (single-pass substituted in `render_html`):

- **Theme toggle** (sun/moon) persisted to `localStorage`; semantic + status palette (`--green/red/amber/sage/teal/plum` + `-dim`) with a light/dark `[data-theme]` switch.
- **Typography scale** + `.ve-card` depth tiers (`--elevated/--recessed/--hero`) + stagger fade-in + `min-width:0` overflow guard.
- **Print-CSS** (`@media print`) hides chrome (toggle/search/facets) for clean Save-as-PDF.
- Mermaid views add theme-var overrides so diagram text follows light/dark.

Change the look in one place → every output updates (DRY). The `explorer` UI is the reference the legacy shell was brought up to.

**Search + facet filters** (`board`/`explorer`): client-side, instant; facets over status/moscow/persona/layer; `board` also groups columns by `--group-by`. "PDF" = browser Save-as-PDF over the print-CSS.

## Snapshot & Delta

`spec_graph.py` writes a snapshot JSON to `docs/product/visuals/.snapshots/<ISO>.json` on every `--validate` run. The `delta` view compares two snapshots:

- **Default**: compare the two most-recent snapshots.
- **Explicit baseline**: `--snapshot <name>` picks a specific older snapshot.
- **No baseline available**: render a "no baseline yet — run --validate to create one" message; do not crash.

Delta detection is purely on the graph JSON (no `git show` archaeology):
- Added nodes / removed nodes (by ID).
- Changed status, scope, moscow, horizon.
- Added / removed edges.

## Determinism

ASCII and Mermaid outputs are **deterministic** (same input → same output). This is testable: `pytest scripts/tests/test_visualize.py` asserts exact text. HTML may carry a generation timestamp (best-effort to localize), but the embedded Mermaid graph itself is deterministic.

## Renderer Limits (advisory)

- Tree view with >200 nodes → ASCII becomes hard to read; offer Mermaid/HTML as the preferred format.
- Mermaid `quadrantChart` doesn't render some labels well — if labels overlap, fall back to a 2D ASCII grid embedded in a `pre` block.
- `timeline` Mermaid view requires the v11 timeline syntax; ensure it stays valid.

## What This Spec Does NOT Define

- ASCII color (no color by default). The shared design system DOES define the HTML palette (light/dark).
- SVG/PNG output (intentionally dropped per validate gate).
- Live updating / live-reload / server (visualizations are one-shot, self-contained renders).
- Edit-from-viewer (`board`/`explorer`/`export` are read surfaces; edits go through the interview flags).
- A real PDF binary ("PDF" = the browser's Save-as-PDF over `@media print`).
