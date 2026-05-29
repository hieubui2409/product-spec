# Skill-Creator Conventions & Product-Spec Extension Points

**Date:** 2026-05-29 | **For:** F1 Export + F2 Viewer features  
**Status:** Extension-point mapping complete; ready for implementation  

---

## PART A — Skill-Creator Conventions Checklist

**Source:** `.claude/skills/skill-creator/SKILL.md` (lines 1–155)

The cleanmatic:product-spec skill must satisfy these conventions when extended:

### SKILL.md Structure (lines 14–133)

- [ ] Frontmatter: name, description (≤1024 chars, "pushy"), user-invocable=true, when_to_use (triggers), category, metadata (version bump on change)
- [ ] Keep SKILL.md <300 lines; defer prose to `references/`
- [ ] Flag table: new `--export`, `--layers`, `--group-by` added to table; all flags documented
- [ ] Output contract updated: new `exports/` dir documented
- [ ] "Loads on demand" section: references relevant to new flags listed
- [ ] New views documented as part of the `--viz` flag description

### Load-On-Demand References (lines 102–113)

- [ ] **For F1 Export:** create `references/workflow-export.md` (~300 lines); describe export-selection model, depth/layer filtering, assemble_digest contract
- [ ] **For F2 Viewer:** extend `references/visualization-spec.md` (add board/explorer to the 9×3 matrix)
- [ ] Link each new reference from SKILL.md's "Loads on demand" section
- [ ] Avoid duplication: frontmatter spec, ID grammar, hierarchy already in existing references

### Script vs LLM Split (operating principle, CLAUDE.md)

- [ ] **Scripts** own: graph querying (`ancestors()`), digest assembly (deterministic full/struct), HTML shell rendering, snapshot I/O
- [ ] **LLM** owns: `--compact-mode llm` summarization (post-script, workflow step), interactive prompt flows in board/explorer
- [ ] Assemble determinism: test via snapshot comparison (same input → same digest JSON)

### Assets & Vendor Pattern (lines 26–46 skill-anatomy, install.sh lines 78–84)

- [ ] **Vendoring**: New `install-vendor-markdown.sh` (mirrors `install-vendor-mermaid.sh` exactly):
  - Pinned URL + SHA256 for marked.min.js + purify.min.js
  - Idempotent check: skip if present and sha256 matches
  - Fallback: None (marked+purify non-negotiable per D8 in brainstorm)
  - Called from `install.sh` as new step before Mermaid vendor step
- [ ] **Templates**: New `assets/templates/board-shell.html`, `explorer-shell.html`, `export-shell.html`
  - Token shape: `{{lang}}`, `{{title}}`, `{{generated_at}}`, `{{product_name}}`, `{{view_body}}`, `{{search_js}}`, `{{filter_js}}`, `{{print_css}}`, etc.
  - Inline marked+DOMPurify only on body-render paths (skip on Mermaid views)
  - Print-CSS embedded via `@media print { … }`

### Eval & Testing Conventions (lines 64–77 skill-creator/SKILL.md)

- [ ] Create `scripts/tests/test_assemble_digest.py`: determinism on (select, depth, layers, lang)
- [ ] Create `scripts/tests/test_render_export.py`: md/html assembly, XSS payloads neutralized
- [ ] Create `scripts/tests/test_render_viewer.py`: board/explorer HTML shell assembly, search/filter JS slots
- [ ] Extend `scripts/tests/test_visualize.py`: +board, +explorer ASCII/HTML tests
- [ ] Test fixtures: reuse `scripts/tests/fixtures/valid-spec/`; create synthetic multi-layer specs for board/explorer testing
- [ ] Determinism assertion: same graph + same args → identical text output (HTML timestamps are OK, sanitized body must be stable)

### Versioning & CHANGELOG (convention implicit in skill-creator)

- [ ] Update SKILL.md frontmatter `version: "1.1.0"` (feature addition)
- [ ] If `CHANGELOG.md` exists in skill root, append new features + version bump
- [ ] Git commit message: `feat(product-spec): add export and viewer features (F1, F2)`

### Security Invariants (for HTML/Viewer)

- [ ] XSS chokepoint: All artifact bodies pass `DOMPurify.sanitize()` before DOM injection
- [ ] Comment invariant in code: "INVARIANT: footer values are passed through _escape() before injection"
- [ ] Test: inject `<script>alert('xss')</script>` and `onerror` payloads; assert neutralized
- [ ] Offline: zero CDN fallback; marked+purify vendored; print-CSS no external fonts

---

## PART B — Extension Points (File:Line)

### 1. `scripts/spec_graph.py` — Graph Construction & Queries

#### Output Shape: `build_graph()` returns (line 138–165)
```json
{
  "version": "1.0",
  "generated_at": "<ISO>",
  "product": {...},
  "nodes": [...],
  "edges": [...],
  "risks": [...],
  "parse_errors": [...],
  "root_path": "<str>"
}
```

#### Signature: `downstream(graph, node_id)` (line 192–205)
- Input: graph dict + node ID string
- Output: set of descendant node IDs (children, grandchildren, …)
- **Usage:** F1 Export uses to assemble descendants of a selected node

#### Insert Here: `ancestors(graph, node_id)` — NEW HELPER
- **File:line:** After `downstream()`, before `write_snapshot()` (insert after line 205)
- **Signature:** `def ancestors(graph: Dict[str, Any], node_id: str) -> List[str]:` (ordered from root to parent)
- **Impl logic:** Walk edges backward (from child to parent) via `edge["to"] == node_id`, collect `edge["from"]`, recurse. Return list ordered ancestor→…→immediate-parent.
- **Usage:** F1 Export `--depth context` walks ancestors (compacted) + target (full) + descendants (full)
- **DRY note:** Mirrors `downstream()` signature/contract; part of graph query API

#### Edge Encoding (line 119–135: `build_edges()`)
- Edges: `{"from": child_id, "to": parent_id, "kind": "epic|prd|brd_goal"}`
- Special: BRD goals have NO outbound edge (no synthetic "goal→BRD" node; goals are direct children of PRODUCT)
- **Usage:** ancestors/descendants walk these edges; `kind` field distinguishes parent type (unused for F1/F2, kept for extensibility)

#### Bodies Loading (line 52–61: `load_artifacts()`)
- Walks `docs/product/` by ARTIFACT_GLOBS (product, vision, brd, prd, epic, story)
- Parses frontmatter via `frontmatter_parser.parse_file()`
- Returns full artifact dicts (frontmatter + body text + file path)
- **Usage:** F1 Export calls load_artifacts() separately to get body text for each node in the digest

#### No Changes Needed to build_graph() or load_artifacts()
- Both are consumed as-is by F1/F2; no modifications required

---

### 2. `scripts/visualize.py` — View Dispatcher

#### Current VIEWS Tuple (line 32)
```python
VIEWS = ("tree", "heatmap", "scope", "roadmap", "persona", "gap", "moscow", "risk", "delta")
```

#### Insert Here: Add board + explorer
- **File:line:** Line 32, replace tuple
- **New tuple:** `VIEWS = ("tree", "heatmap", "scope", "roadmap", "persona", "gap", "moscow", "risk", "delta", "board", "explorer")`

#### Argparse Args (line 111–128)
- **Insert after `--filter-wont` (line 125):**
  ```python
  ap.add_argument(
      "--layers", default=None,
      help="filter by artifact types: comma-separated vision,brd,prd,epic,story,goal (default all)."
  )
  ap.add_argument(
      "--group-by", default="status", choices=["status", "horizon", "moscow"],
      help="board view only: group cards by this field (default status)."
  )
  ```

#### Dispatch Logic (line 135–161)
- **ASCII path (line 135–138):** Add board/explorer cases
  ```python
  if args.view == "board":
      body = render_ascii.board(graph, lang=args.lang, group_by=args.group_by, layers=args.layers, filter_wont=args.filter_wont)
      print(body)
      return 0
  if args.view == "explorer":
      body = render_ascii.explorer(graph, lang=args.lang, layers=args.layers, filter_wont=args.filter_wont)
      print(body)
      return 0
  ```
- **Mermaid path (line 140–143):** Add board/explorer cases (both fallback to ASCII `<pre>`)
  ```python
  if args.view in ("board", "explorer"):
      # No clean Mermaid for board/explorer; use ASCII fallback
      body_text = render_ascii.board(...) if args.view == "board" else render_ascii.explorer(...)
      view_format = "pre"
  ```
- **HTML path (line 145–159):** Route board/explorer to render_html with view_format="pre" (not mermaid)
  - board/explorer do NOT use `_render_mermaid()`; they use `render_ascii.*` and set `view_format = "pre"`
  - This ensures Mermaid JS is NOT loaded for these views (smaller files)

#### Snapshot Baseline (line 66–108)
- No change; `--snapshot` applies only to `--view delta`

---

### 3. `scripts/render_html.py` — HTML Assembly

#### Current Token Slots in `assemble()` (line 122–167)
- Existing: `{{lang}}`, `{{title}}`, `{{generated_at}}`, `{{product_name}}`, `{{view}}`, `{{view_body}}`, `{{mermaid_js}}`, `{{footer_note}}`

#### Insert Here: New Token Handling (before line 155)
- **For board/explorer bodies:** Load marked.min.js + purify.min.js (new helpers below)
- **Insert new helper functions before `assemble()` (line 122):**

```python
def _load_vendored_markdown_libs() -> Optional[Tuple[str, str]]:
    """Return (marked.min.js, purify.min.js) tuple if vendored; else None."""
    marked = SKILL_ROOT / "assets" / "vendor" / "marked.min.js"
    purify = SKILL_ROOT / "assets" / "vendor" / "purify.min.js"
    if marked.exists() and purify.exists():
        return (marked.read_text(encoding="utf-8"), purify.read_text(encoding="utf-8"))
    return None

def _render_markdown_body(markdown_text: str, marked_js: str, purify_js: str) -> str:
    """Return JS-executable snippet that renders markdown → sanitized HTML."""
    # Escape markdown for safe embedding in JS string; JS runs marked() + DOMPurify.sanitize()
    escaped_md = markdown_text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return f"""
    <div id="md-body"></div>
    <script>
    {marked_js}
    {purify_js}
    (function() {{
        const md = '{escaped_md}';
        const html = marked.parse(md);
        const sanitized = DOMPurify.sanitize(html);
        document.getElementById('md-body').innerHTML = sanitized;
    }})();
    </script>
    """
```

#### Token Expansion (line 155–166)
- **Insert after existing values dict, before loop:**
  ```python
  # For board/explorer HTML: include search/filter JS + print-CSS
  if view_format == "pre":  # board/explorer (ASCII fallback in <pre>)
      values["search_js"] = _inject_search_filter_js()
      values["print_css"] = _inject_print_css()
      values["markdown_libs_js"] = ""  # not needed for ASCII fallback
  else:  # Mermaid views (tree, heatmap, etc.)
      values["search_js"] = ""
      values["print_css"] = ""
      values["markdown_libs_js"] = ""
  ```

#### New Helper: `_inject_search_filter_js()` (insert before `assemble()`)
- Returns inline JS snippet for client-side text search + facet filters
- Operates on embedded JSON dataset (nodes + edges)
- Filters visible nodes based on search terms + selected facets (status, moscow, persona, layer)
- Updates DOM to show/hide nodes in real-time

#### New Helper: `_inject_print_css()` (insert before `assemble()`)
- Returns `<style>@media print { … }</style>` block
- Hides interactive controls (search, filters, toggles)
- Adjusts fonts/margins for PDF export
- Ensures tree/table structure remains readable in print

#### Escaping Invariant (line 109–119)
- Existing `_escape()` remains unchanged
- **Add comment above escaping in new helpers:** "INVARIANT: all artifact bodies from DOMPurify pass through _escape() if injected into HTML attributes"

#### Conditional Mermaid Loading (line 153–158)
- **Current:** Loads mermaid JS only for Mermaid views
- **No change needed:** board/explorer set view_format="pre", so mermaid_js stays empty

---

### 4. `scripts/render_ascii.py` — ASCII Views

#### Existing Per-View Functions (line 30–127)
- `tree()`, `heatmap()`, `scope()`, `roadmap()`, `persona()`, `gap()`, `moscow()`, `risk()`
- Shared: `_hashable()`, `_mark()`, `_is_deferred()`, `_grid()`

#### Insert Here: `board(graph, lang, group_by, layers, filter_wont)` — NEW
- **File:line:** After `risk()`, before `delta()` (after line ~280)
- **Return type:** str (ASCII)
- **Logic:** 
  - Parse `layers` CSV (default all types)
  - Group nodes by `group_by` field (status/horizon/moscow)
  - Within each group, list artifacts (ID + title + key fields)
  - Format: "## Status: <value>" header, then bullet list of cards
  - Apply `filter_wont` to hide deferred items
- **Example output:**
  ```
  ## Status: draft
  - PRD-AUTH (Vision: secure sign-in)
  - PRD-AUTH-E1-S2 (Story: add 2FA)
  
  ## Status: approved
  - PRD-AUTH-E1-S1 (Story: email + password)
  ```

#### Insert Here: `explorer(graph, lang, layers, filter_wont)` — NEW
- **File:line:** After `board()`
- **Return type:** str (ASCII)
- **Logic:** 
  - Parse `layers` CSV (default all types)
  - Render a tree (like existing `tree()`) but with metadata columns appended
  - Format: "ID | Title | Status | Moscow | Owner" as ASCII table with tree indentation
  - Apply `filter_wont` to hide deferred items
  - Note: 3-mode toggle (tree/flat-tabs/table) is JS-only (HTML); ASCII fallback = tree

#### Layer Filtering Helper (insert before `board()`)
- **Function:** `_filter_by_layers(graph, layers_csv) -> Dict[str, Any]`
- **Logic:** Parse layers CSV, filter nodes by type, rebuild edges for filtered graph
- **Usage:** Both board() and explorer() call this to select artifact types

---

### 5. `scripts/render_html.py` — Shared Body Render Helper

#### Insert Before `assemble()` (line 122)

New helper: `_render_markdown_body_html(body_text: str, marked_js: str, purify_js: str) -> str`
- Takes markdown body from an artifact
- Returns HTML with marked → DOMPurify pipeline embedded
- Used by board/explorer card bodies (on click) to render artifact content

New helper: `_render_search_filter_html(graph: Dict[str, Any]) -> str`
- Takes graph (nodes + edges)
- Returns JS-executable code that:
  - Embeds nodes as JSON in a `<script id="nodes-data">` block
  - Implements search box filtering (text match on title + body)
  - Implements facet filters (status, moscow, persona, layer)
  - Updates DOM visibility on filter change
- Called by board-shell.html and explorer-shell.html templates

---

### 6. `assets/templates/visual-html-shell.html` — Existing Shell

#### Current Tokens (line ~20–40)
- `{{lang}}`, `{{title}}`, `{{generated_at}}`, `{{product_name}}`, `{{view}}`, `{{view_body}}`, `{{mermaid_js}}`, `{{footer_note}}`

#### No Changes to Existing Shell
- Existing Mermaid views (tree, heatmap, etc.) use existing shell as-is

---

### 7. `assets/templates/board-shell.html` — NEW

- **File:line:** Create new (mirrors visual-html-shell.html structure)
- **Token slots:** `{{lang}}`, `{{title}}`, `{{generated_at}}`, `{{product_name}}`, `{{view_body}}`, `{{search_js}}`, `{{filter_js}}`, `{{print_css}}`, `{{board_stylesheet}}`
- **Structure:**
  - Header: search box + filter dropdowns (status/moscow/persona/layer)
  - Body: `<div class="board">` with `<div class="board-column">` per group value
    - Each column contains cards (artifact blocks)
    - Card on-click expands to show full body (rendered via marked+DOMPurify)
  - Footer: "Self-contained HTML. To re-render: python3 visualize.py --view board …"
  - Stylesheet: Kanban layout (flexbox columns), card styling, print-CSS

---

### 8. `assets/templates/explorer-shell.html` — NEW

- **File:line:** Create new (mirrors visual-html-shell.html structure)
- **Token slots:** Similar to board-shell + mode-toggle JS
- **Structure:**
  - Header: Mode toggle buttons (Tree / Flat-tabs / Table-tree)
  - Navigation pane: Tree view (collapse/expand)
  - Content pane: Selected node body + metadata
  - Footer: Same footer note as board
  - JS: In-page mode switching (hide/show nav + content layouts)

---

### 9. `assets/templates/export-shell.html` — NEW

- **File:line:** Create new (for F1 `--export --format html`)
- **Token slots:** `{{lang}}`, `{{title}}`, `{{generated_at}}`, `{{toc}}`, `{{content}}`, `{{print_css}}`
- **Structure:**
  - Header: Document title + metadata (product name, export date, selection)
  - TOC: Auto-generated from headings (Vision → BRD → PRD → Epic → Story hierarchy)
  - Content: Artifact bodies (Vision→BRD(struct)→PRDs(full)→Epics(full)→Stories(full,with AC))
  - Footer: "Exported from product-spec on <date>. To export again: python3 render_export.py …"
  - Print-CSS: Optimized for Save-as-PDF (page breaks between major sections)

---

### 10. `scripts/install-vendor-markdown.sh` — NEW

- **File:line:** Create (mirrors install-vendor-mermaid.sh exactly, lines 1–69)
- **Pinned URLs:**
  - marked.min.js: `https://cdn.jsdelivr.net/npm/marked@<version>/marked.min.js`
  - purify.min.js: `https://cdn.jsdelivr.net/npm/dompurify@<version>/dist/purify.min.js`
- **SHA256:** Pinned per CDN fetch date (e.g., 2026-05-28)
- **Output:** Both libs to `assets/vendor/marked.min.js` + `assets/vendor/purify.min.js`
- **Idempotency:** Skip if both present and SHA256 matches
- **Fallback:** None (no CDN fallback; marked+purify non-negotiable)

---

### 11. `install.sh` — Updated

#### Insert New Step (after line 84: Mermaid vendor step, before line 86)
```bash
# --- Step 4b: Markdown libs vendor ---
step "Vendoring markdown libraries for export/viewer"
if [ -x "$SCRIPT_DIR/scripts/install-vendor-markdown.sh" ]; then
    bash "$SCRIPT_DIR/scripts/install-vendor-markdown.sh"
else
    fail "vendor shim missing for markdown libs"
fi
```

#### Update venv smoke-test (line 88)
- No change; markdown libs are vendored, not pip-installed

---

### 12. `scripts/tests/test_assemble_digest.py` — NEW

- **File:line:** Create
- **Fixtures:** Reuse `scripts/tests/fixtures/valid-spec/`
- **Test cases:**
  - `test_assemble_digest_all_layers_full()`: `--export all --depth full`
  - `test_assemble_digest_prd_only_struct()`: `--export PRD-AUTH --depth brief`
  - `test_assemble_digest_layers_filter()`: `--export all --layers epic,story` (skip vision/brd/prd)
  - `test_assemble_digest_deterministic()`: same input → same JSON body (except generated_at timestamp)
  - `test_assemble_digest_depth_context_compacts_ancestors()`: ancestors struct + target full + descendants full
- **Assertion:** Output is valid JSON; digest shape matches schema (defined in workflow-export.md)

---

### 13. `scripts/tests/test_render_export.py` — NEW

- **File:line:** Create
- **Test cases:**
  - `test_export_md_contains_toc()`: MD export has `## Table of Contents` section
  - `test_export_html_is_self_contained()`: HTML export has no external script/link tags
  - `test_export_xss_payload_neutralized()`: Inject `<script>alert('xss')</script>` in artifact body; assert escaped in output
  - `test_export_md_deterministic()`: Same digest → same MD (no timestamps in body)
  - `test_export_html_has_print_css()`: `@media print { … }` present in HTML

---

### 14. `scripts/tests/test_render_viewer.py` — NEW

- **File:line:** Create
- **Test cases:**
  - `test_board_ascii_groups_by_status()`: ASCII board groups artifacts by status column
  - `test_board_html_has_search_js()`: HTML board contains search-filter JS
  - `test_explorer_ascii_is_tree()`: ASCII explorer falls back to tree format
  - `test_explorer_html_has_mode_toggle()`: HTML explorer has tree/flat-tabs/table-tree JS toggle
  - `test_explorer_html_xss_neutralized()`: Body content passes DOMPurify; payloads escap

ed
  - `test_board_explorer_layers_filter()`: `--layers epic,story` filters display

---

### 15. `scripts/tests/test_visualize.py` — Extended

#### Insert New Tests (after line ~120, in Mermaid section)

- `test_board_ascii_output_has_status_header()`: "## Status: draft" present
- `test_explorer_ascii_output_is_tree_format()`: Contains tree characters (├ │ └)
- `test_board_html_output_file_created()`: HTML file written to `docs/product/visuals/`
- `test_explorer_html_output_file_created()`: HTML file written

#### Insert After HTML section (line ~160)

- `test_board_html_skips_mermaid_js()`: No `<div class="mermaid">` in board HTML (uses `<pre>` fallback)
- `test_explorer_html_skips_mermaid_js()`: Same as board
- `test_layers_arg_filters_nodes()`: `--layers epic,story` reduces node count in output

---

### 16. `references/workflow-export.md` — NEW

- **File:line:** Create (~300 lines; mirrors workflow-interview.md structure)
- **Sections:**
  - Selection model: `--export <select>` grammar (all | ID | comma-list)
  - Layers: `--layers` type filtering (vision, brd, prd, epic, story, goal)
  - Depth: `--depth context|full|brief` and ancestor/descendant role assignment
  - Compaction: `--compact-mode struct|llm` (struct = script, llm = LLM workflow)
  - Output: `docs/product/exports/<select>-<ts>.md|html` + TOC + provenance
  - Workflow: F1 (export) first; assembler is deterministic; compaction-llm is a separate LLM step
  - Examples: `--export PRD-AUTH --format md`, `--export all --depth full --compact-mode struct`

---

### 17. `references/visualization-spec.md` — Extended

#### Add to Views Matrix (line 13–25, after delta row)

```
| board    | `--viz board`    | kanban: columns by `--group-by` (status/horizon/moscow), cards = artifacts. client-side search/filter. |
| explorer | `--viz explorer` | tree/flat-tabs/table-tree toggle; collapsible nav + content pane; search/filter. |
```

#### Add to View × Format Matrix (line 31–41, after delta row)

```
| board    | grouped ASCII lists (per group value) | N/A | Kanban layout + search/filter JS |
| explorer | ASCII tree (with metadata columns)   | N/A | Tree/flat-tabs/table-tree + search/filter JS |
```

#### Add New Section: "New Viewer Flags"

```
| Flag | Purpose |
|------|---------|
| `--layers <types>` | Filter displayed artifacts: comma-separated vision,brd,prd,epic,story,goal (default all). Applied to all views. |
| `--group-by <field>` | Board view only: group cards by status\|horizon\|moscow (default status). |
```

#### Add New Section: "Layers and Depth"

- Layers = artifact type filtering (applied before rendering)
- Depth = ancestor/descendant inclusion rules (for export only; viewers show all selected layers)
- Interaction: `--export <ID> --layers epic,story` = select PRD subtree, then filter to epics + stories only

---

### 18. `SKILL.md` — Updated

#### Update Flags Table (line 26–44)

```
| `--export <select>` | Export a spec slice to one md/html doc (F1). Select by ID or "all"; see references/workflow-export.md. |
| `--layers <types>` | Filter by artifact type (vision,brd,prd,epic,story,goal). Used by export + viewer. |
| `--group-by <field>` | Board view only (--viz board). Group cards by status/horizon/moscow. |
| `--depth context\|full\|brief` | Export depth (default context): context=ancestors compacted+target full+descendants full. |
| `--compact-mode struct\|llm` | Export compaction (default struct): struct=deterministic skeleton, llm=LLM-post-processed summary. |
```

#### Update `--viz` Flag Description (line 42)

From:
```
Views: tree, heatmap, scope, roadmap, persona, gap, moscow, risk, delta.
```

To:
```
Views: tree, heatmap, scope, roadmap, persona, gap, moscow, risk, delta, board, explorer.
Board/explorer both support --layers and --group-by (board only); see visualization-spec.md.
```

#### Update Output Contract (line 61–77)

```
├── exports/              # F1 exported docs (new)
│   ├── <select>-<ts>.md  # markdown export
│   ├── <select>-<ts>.html # html export
│   └── ...
└── visuals/              # rendered visualizations (extended)
    ├── board-<ts>.html   # F2 board viewer
    ├── explorer-<ts>.html # F2 explorer viewer
    └── ...
```

#### Update "Loads on demand" (line 102–112)

Add:
```
- `references/workflow-export.md` — F1 export workflow, selection + depth + compaction.
- Updated `references/visualization-spec.md` — board/explorer views added to matrix; new `--layers` / `--group-by` flags.
```

---

### 19. `CLAUDE.md` (repo-root product-spec guide) — Minor Update

#### Update Visualization section (line already reference visualization-spec.md)

Add note to visualization section:
```
F1 Export: `--export <ID> [--layers <types>] [--depth context|full|brief] [--format md|html]`
F2 Viewer: `--viz board [--group-by status|horizon|moscow]` or `--viz explorer [--layers <types>]`
See references/workflow-export.md for export workflow. See references/visualization-spec.md for viewer matrix.
```

---

## Extension Seams Summary

| File | Seam | Change Type | Notes |
|------|------|-------------|-------|
| spec_graph.py:205 | Insert `ancestors()` | Add function | DRY with downstream() |
| visualize.py:32 | VIEWS tuple | Extend | +board, +explorer |
| visualize.py:125 | argparse | Add args | --layers, --group-by |
| visualize.py:135–158 | Dispatch logic | Add branches | board/explorer ASCII/HTML routes |
| render_ascii.py:~280 | Insert `board()`, `explorer()` | Add functions | New ASCII renderers |
| render_ascii.py | Insert `_filter_by_layers()` | Add helper | Layer filtering logic |
| render_html.py:122 | Insert MD helpers | Add functions | marked+DOMPurify pipeline |
| render_html.py:155 | Token expansion | Extend dict | +search_js, +print_css |
| assets/templates/ | Create board-shell.html, explorer-shell.html, export-shell.html | Add 3 files | ~1.5 KB each; token slots |
| assets/vendor/ | Create marked.min.js, purify.min.js | Add 2 files | Vendored via install-vendor-markdown.sh |
| install-vendor-markdown.sh | New file | Create | Mirrors mermaid vendor pattern |
| install.sh:84 | New step | Insert | Call install-vendor-markdown.sh |
| scripts/tests/ | Create 3 test files, extend 1 | Add + extend | test_assemble_digest.py, test_render_export.py, test_render_viewer.py, extend test_visualize.py |
| references/workflow-export.md | New file | Create | ~300 lines; F1 workflow |
| references/visualization-spec.md | Extend views matrix + add flags section | Extend | +board/explorer rows; document --layers, --group-by |
| SKILL.md | Update flags table, output contract, loads-on-demand | Extend | 3 sections |
| CLAUDE.md | Minor note in visualization section | Extend | 1 paragraph |

---

## Unresolved Questions & Blocked Seams

### No Blocking Seams
All extension points identified as clean. No architectural mismatches.

### Minor Clarifications (Not Blocking)

1. **Layer Filtering Interaction:** Should `--layers epic,story` applied to `--export PRD-AUTH` show:
   - (A) Only epics + stories under PRD-AUTH (prune higher levels)?
   - (B) Vision/BRD(struct) + PRD-AUTH(struct) + its epics/stories(full)?
   - **Decision needed:** (B) suggested per D4 in brainstorm (ancestors compacted, target filtered, descendants full)

2. **Board Group-By Default:** If user doesn't specify `--group-by`, default to `status`. Acceptable?
   - **Assumption:** Yes (per D7 in brainstorm)

3. **Explorer Mode Toggle JS State:** Should mode toggle state persist via browser localStorage?
   - **Assumption:** No (v1 = session-only; simplifies vendor-free JS)

4. **Print-CSS Media Breakpoint:** Assume letter-size (8.5×11 in) with 1-inch margins?
   - **Assumption:** Yes (most common; users adjust in browser before print)

5. **Marked + DOMPurify Version Pins:**
   - marked: latest v11 stable (as of 2026-05-28, check jsDelivr for 11.4.1+)
   - DOMPurify: latest stable (check jsDelivr)
   - **Need:** confirm exact versions with brainstorm owner before vendoring

---

## Status

**DONE** — Extension-point mapping complete and verified against:
- Skill-creator conventions (SKILL.md, install.sh patterns)
- Product-spec architecture (spec_graph → visualize → render dispatch)
- Test conventions (fixtures, determinism, XSS payloads)
- Security invariants (XSS chokepoint, offline constraint)

**Ready for:** Implementation planning phase (Phase 1: assemble_digest.py + render_export.py, then render_board/explorer, then vendor + tests).

---

## Summary

**Part A:** Skill-creator conventions extracted as 8-part checklist (SKILL.md structure, references, script/LLM split, assets/vendor, eval, versioning, security, tests).

**Part B:** 19 extension seams mapped with exact file:line citations + insertion logic. Key seams:
- `spec_graph.py:205` — add `ancestors()` helper (mirroring `downstream()`)
- `visualize.py:32,125,135` — extend VIEWS tuple, argparse, dispatch branches
- `render_ascii.py:~280` — add `board()` + `explorer()` ASCII renderers
- `render_html.py:122,155` — add marked+DOMPurify pipeline + token expansion
- `assets/templates/` — create 3 HTML shells (board, explorer, export)
- `install-vendor-markdown.sh` — new (mirrors mermaid vendor pattern exactly)
- `references/` — new workflow-export.md; extend visualization-spec.md
- Tests: 3 new files + extend test_visualize.py

No blocking seams identified. All changes are additive or localized extending. 5 minor clarifications flagged (non-blocking; decision points for owner).
