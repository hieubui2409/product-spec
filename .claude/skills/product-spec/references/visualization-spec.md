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
| `risk` | `--viz risk` | risk matrix: impact (rows) × likelihood (cols) from `risks` frontmatter on epics/PRDs. HTML-native default. |
| `competition` | `--viz competition` | competitive parity matrix (competitor × PRD) + threat heatmap. HTML-native default. |
| `time` | `--viz time [--filter-wont]` | TIME dimension: PRD/Epic by horizon with `target_date` + `depends_on`. ASCII text + Mermaid gantt. |
| `dashboard` | `--viz dashboard` | **HTML-only** multi-dim page: roadmap/deadlines + risk grid + competition, stacked on one page. No ASCII/Mermaid form. |
| `delta` | `--viz delta [--snapshot <name>]` | diff between two graph snapshots from `docs/product/visuals/.snapshots/`. |
| `board` | `--viz board [--group-by status\|horizon\|moscow] [--layers …]` | kanban: columns = the group field, cards = goal/PRD/epic/story; client-side search + facet filters (status/moscow/horizon/persona/layer); click a card → its sanitized body. Default `--format html`. |
| `explorer` | `--viz explorer [--layers …]` | one page, in-page toggle across **Tree** (collapsible nav) / **Flat-tabs** (per layer) / **Table-tree** (treegrid w/ metadata columns); shared search + facets; last mode persisted to `localStorage`. Default `--format html`. |

## View × Format Matrix

Most graph views support all 3 formats. **Default format is per-view** (PO decision §0.2): the rich matrix/multi-dim views — `risk`, `competition`, and the HTML-only `dashboard` — default to **HTML-native**; the 2 body views (`board`/`explorer`) default to HTML; everything else (`tree`, `heatmap`, `scope`, `roadmap`, `persona`, `gap`, `moscow`, `time`, `delta`) defaults to **ASCII**, preserving the zero-dep terminal/CI path.

| View | ASCII | Mermaid | HTML |
|------|-------|---------|------|
| `tree` | **text-summary** (one line/node `[type:id] title · status`, 2-space indent, counts footer; NO box-drawing art) | `flowchart BT` | Mermaid + collapse/zoom JS |
| `heatmap` | ASCII table | `quadrantChart` or text fallback | Mermaid embed |
| `scope` | 2D ASCII grid | `quadrantChart` | Mermaid embed |
| `roadmap` | grouped lists (now/next/later) | `timeline` | Mermaid embed |
| `persona` | ASCII table (persona × feature) | text fallback (`pre`) | Mermaid embed |
| `gap` | ASCII bullet list of unaddressed nodes | `flowchart LR` with gap nodes highlighted | Mermaid embed |
| `moscow` | 2×2 ASCII grid | `quadrantChart` (must/should × could/wont) | Mermaid embed |
| `risk` | 3×3 ASCII grid (terminal fallback) | text fallback (`pre`) | **default** — HTML-native `<table>` (impact × likelihood; cells drill down to description + mitigation + status). Not Mermaid — Q44. |
| `competition` | parity matrix + threat list (terminal fallback) | text fallback (`pre`) | **default** — HTML-native parity matrix + threat heatmap. Not Mermaid — Q30/Q44. |
| `time` | grouped-by-horizon text (target_date + depends_on) | `gantt` (cycle-safe; dep annotations) | Mermaid gantt embed |
| `dashboard` | — (HTML-only) | — (HTML-only; `--format mermaid\|ascii` → HTML + stderr note) | **default + only** — roadmap + risk grid + competition stacked on one page |
| `delta` | unified-diff-style text | `flowchart TB` with +/− tags | Mermaid embed |
| `board` | grouped lists per `--group-by` | → ASCII board (note on stderr) | **default** — kanban + search/facets + click→sanitized body |
| `explorer` | = `tree`; with `--layers` an orphan-rooted forest (surviving nodes whose parent was filtered out become roots, like the HTML explorer) | → ASCII tree (note on stderr) | **default** — Tree/Flat-tabs/Table-tree + search/facets |

**ASCII downgraded, NOT removed (PO decision §0.2).** HTML-native is the new default for the rich views, but the ASCII path stays alive: the `tree` view renders a minimal, deterministic **text-summary** (compact structure + node/finding counts) instead of the old heavy box-drawing graph-art, and `board`/`explorer` keep their text-summary fallback on `--format mermaid`. The zero-dependency terminal/CI path loses nothing.

If a Mermaid view type can't cleanly express a view (e.g., `heatmap`-as-quadrant is awkward), the Mermaid output falls back to a text fallback inside a `pre` block. Document the fallback in the renderer's comment. The `risk` and `competition` views go the other way: Mermaid still falls back to text, but their **HTML** form is HTML-native (`render_html.risk()` / `render_html.competition()`), not a `<pre>` — matrix/heatmap/risk-grid render HTML-native per Q44. The `dashboard` is HTML-only — a `--format mermaid|ascii` request renders HTML anyway with a one-line note on stderr. Body views (`board`/`explorer`) have no Mermaid form at all — `--format mermaid` falls back to their ASCII renderer with a one-line note on stderr.

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
    {"node": "PRD-AUTH-E1", "description": "OAuth dependency", "impact": "high", "likelihood": "med", "mitigation": "Fallback provider on standby", "status": "open"}
  ],
  "competitors": [
    {"id": "COMP-ACME", "name": "Acme Commerce", "url": "https://acme.example", "threat": "high"}
  ],
  "parse_errors": [],
  "root_path": "/absolute/path/to/project"
}
```

`edges[].kind` records the field name used in the child's frontmatter (`epic`, `prd`, `brd_goal`) — keeps the graph self-describing.

When the `docs/product/` directory is absent, `spec_graph.py` emits a minimal stub graph that additionally carries `"missing_product_dir": true` (and has empty `nodes`/`edges`/`risks`/`competitors`).

## Renderer Inputs / Outputs

- **Input:** built from `--root <dir>` (triggers `spec_graph.py` internally); the delta view also reads a baseline via `--snapshot`. No stdin path.
- **Output:**
  - ASCII → stdout (terminal-safe; always uncolored — no ANSI).
  - Mermaid → stdout (a fenced ```mermaid block ready to paste into docs).
  - HTML → file in `docs/product/visuals/<view>-<timestamp>.html`.

## Flag → View / Format Mapping

```
--viz <view>            # default --format is per-view: html for risk/competition/dashboard
                        #   + board/explorer; ascii for everything else
--viz <view> --format mermaid
--viz <view> --format html
--viz dashboard         # HTML-only multi-dim page (no ascii/mermaid form)

--viz delta             # uses two most-recent snapshots
--viz delta --snapshot <name>     # explicit baseline

--viz <view> --filter-wont        # hide deferred (moscow=wont / scope=out) items
--viz board --group-by status|horizon|moscow
--viz board|explorer --layers goal,prd,epic,story   # filter cards by artifact type
```

`--lang en|vi` localizes labels in the rendered output (e.g., "now/next/later" → "hiện tại/tiếp theo/sau này"). IDs, edges, and frontmatter values stay English.

`--filter-wont` hides deferred items (frontmatter `moscow: wont` or `scope: out`) from `tree`/`roadmap`/`time`/`persona`/`board`/`explorer` (ascii, mermaid, and html alike). **Default keeps them visible** — a trailing `*` marker on the graph views, a card on board/explorer — so nothing is silently dropped; `--filter-wont` is the opt-in to declutter.

## HTML Self-Containment

Each HTML output is a single file with:
- The shared design-system head (inline `<style>` + theme + helper JS; no external fonts).
- Graph views: inline Mermaid JS (vendored at `assets/vendor/mermaid.min.js`) + one `<div class="mermaid">…</div>` + zoom JS.
- Body views (`board`/`explorer`/`export`): inline marked + DOMPurify (`assets/vendor/marked.min.js`, `purify.min.js`) + an inert JSON data island; the client builds metadata via safe DOM APIs and bodies via the chokepoint `DOMPurify.sanitize(marked.parse(md))`.

The HTML opens with no server and no network. Vendored libs are pinned + SHA-verified + committed. **Symmetric payload gating:** graph views inline no marked/DOMPurify; body views inline no Mermaid. If the markdown libs are missing, body views **fail closed** to escaped text + a visible banner — never a CDN sanitizer.

## HTML Design System (one source for every view)

All HTML outputs — every `--viz` graph view (including the HTML-native `risk`/`competition`/`dashboard`) + `board` + `explorer` + `--export --format html` — share **one** head partial (`assets/templates/_viewer-head.html`), included by every shell via the `{{viewer_head}}` token (single-pass substituted in `render_html`):

- **Theme toggle** (sun/moon) persisted to `localStorage`; semantic + status palette (`--green/red/amber/sage/teal/plum` + `-dim`) with a light/dark `[data-theme]` switch.
- **Typography scale** + `.ve-card` depth tiers (`--elevated/--recessed/--hero`) + stagger fade-in + `min-width:0` overflow guard.
- **Print-CSS** (`@media print`) hides chrome (toggle/search/facets) for clean Save-as-PDF.
- Mermaid views add theme-var overrides so diagram text follows light/dark.

Change the look in one place → every output updates (DRY). The `explorer` UI is the reference the legacy shell was brought up to.

**Search + facet filters** (`board`/`explorer`): client-side, instant; facets over status/moscow/horizon/persona/layer; `board` also groups columns by `--group-by`. "PDF" = browser Save-as-PDF over the print-CSS.

## Snapshot & Delta

`spec_graph.py` writes a snapshot JSON to `docs/product/visuals/.snapshots/<ISO-second>-<content-hash8>.json` (separators stripped; hash = first 8 hex digits of SHA-256 of the body) on every `--validate` run. The `delta` view compares two snapshots:

- **Default**: compare the two most-recent snapshots.
- **Explicit baseline**: `--snapshot <name>` picks a specific older snapshot.
- **No baseline available**: render a "no baseline yet — run --validate to create one" message; do not crash.

Delta detection is purely on the graph JSON (no `git show` archaeology):
- Added nodes / removed nodes (by ID).
- Changed status, scope, moscow, horizon, size.

## Determinism

ASCII and Mermaid outputs are **deterministic** (same input → same output). This is testable: `pytest scripts/tests/test_visualize.py` asserts exact text — including the `tree` text-summary (sorted by ID at each depth → byte-identical run-to-run) and its counts footer. HTML may carry a generation timestamp (best-effort to localize), but the embedded fragment / Mermaid graph itself is deterministic.

## Renderer Limits (advisory)

- The ASCII `tree` is now a compact text-summary (structure + counts), so even large specs stay readable in a terminal; for the rich hierarchical layout use the HTML or Mermaid form.
- Mermaid `quadrantChart` doesn't render some labels well — if labels overlap, fall back to a 2D ASCII grid embedded in a `pre` block.
- `timeline` Mermaid view requires the v11 timeline syntax; ensure it stays valid.

## What This Spec Does NOT Define

- ASCII color: ASCII output is always uncolored (no ANSI; no `--color` flag). The shared design system DOES define the HTML palette (light/dark).
- SVG/PNG output (intentionally dropped per validate gate).
- Live updating / live-reload / server (visualizations are one-shot, self-contained renders).
- Edit-from-viewer (`board`/`explorer`/`export` are read surfaces; edits go through the interview flags).
- A real PDF binary ("PDF" = the browser's Save-as-PDF over `@media print`).
