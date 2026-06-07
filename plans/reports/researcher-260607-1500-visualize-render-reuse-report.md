# Render Function Inventory & Reuse Path for analyze_telemetry.py

## Executive Summary

`visualize.py` renders three formats (ASCII, Mermaid, self-contained HTML) through a modular pipeline. The HTML path inlines vendored JS assets (2.6 MB total) from `assets/vendor/`, applies `{{token}}` substitution templates, and enforces server-side escaping. For `analyze_telemetry.py` to render charts with minimal duplication, the **recommended path is Option B**: reuse the same vendored asset paths and the `substitute()` / `_escape()` helpers, extracting an HTML template builder into `_shared/lib/` if multiple scripts need it. No full refactor needed—three helper functions suffice.

---

## Part 1: Render Function Inventory

### ASCII Rendering (Module: `render_ascii.py`)
No shared extracted module; each view function (tree, heatmap, persona, roadmap, gap, moscow, time, delta) is self-contained. Patterns reusable in analyze_telemetry.py if ASCII charts are needed:
- Manual string concatenation with `\n` joins
- No helper library exported; would require inline implementation

### Mermaid Rendering (Module: `render_mermaid.py`)
Functions emit fenced Mermaid blocks (`\`\`\`mermaid ... \`\`\``) for all graph views. Two defense-in-depth strategies visible:
- `_safe_label(s)` (line ~25–42): Escapes `<`, `>`, `&`, `"`, `'`, newlines, brackets for safe label embedding
- `_safe_label_lines(*parts)`: Multi-part safe label builder
- Entry points: `tree()`, `heatmap()`, `persona()`, `roadmap()`, `gap()`, `moscow()`, `risk()`, `competition()`, `time()`, `delta()`
- All return fenced blocks; consumed by `visualize.py` → `_render_view_body(view_format="mermaid", …)` → wrapped in `<div class="mermaid">`

**Reusability:** `_safe_label()` is generic and could be imported; rest are view-specific DSL builders.

### HTML Rendering (Module: `render_html.py`)
Core helpers extracted and reusable:

| Function | Purpose | Lines | Signature | Reusable? |
|----------|---------|-------|-----------|-----------|
| `_escape(s)` | HTML-safe encode: `&` → `&amp;`, `<` → `&lt;`, etc. | 129–139 | `(s: str) -> str` | ✅ Yes—used across all HTML paths |
| `_render_view_body(view_format, view_text)` | Wraps ASCII/Mermaid/HTML fragments per format type | 87–126 | `(str, str) -> str` | ✅ Partially—format dispatch logic applicable |
| `_load_mermaid_js()` | Reads vendored mermaid.min.js or returns CDN fallback | 76–84 | `() -> str` | ✅ Yes—reusable for any Mermaid page |
| `_load_vendored_markdown_libs()` | Reads marked.min.js + purify.min.js, concatenates, escapes `</script` | 740–752 | `() -> Optional[str]` | ✅ Yes—reusable for body-bearing views |
| `_load_vendored_mermaid_js()` | Low-level file read; returns None on miss | 42–51 | `() -> Optional[str]` | ✅ Yes—dependency of `_load_mermaid_js()` |
| `_cdn_fallback_snippet()` | Generates fallback JS tag when vendored file absent | 54–73 | `() -> str` | ✅ Yes—generic fallback logic |
| `viewer_head()` | Reads shared design-system CSS + helper JS from `_viewer-head.html` | 755–757 | `() -> str` | ✅ Yes—one source for all HTML |
| `embed_spec_data(payload)` | JSON-serializes + `<`-escapes for inert data island | 760–773 | `(Any) -> str` | ✅ Yes—safe JSON embedding pattern |
| `substitute(shell, values)` | Single-pass `{{token}}` template substitution (no re-scan) | 1060–1071 | `(str, Dict[str, str]) -> str` | ✅ Yes—generic safe substitution |
| `assemble(view, view_format, view_text, graph, lang)` | Full page assembly: shell + view body + tokens | 989–1057 | Core HTML builder | ✅ Partially—depends on specific view types |
| `write(root, view, view_format, view_text, graph, lang)` | Write assembled HTML to `docs/product/visuals/<view>-<ts>.html` | 1088–1098 | Entry point for graph views | ✅ Partially—path/gating logic is product-spec-specific |

**Entry Point Hierarchy:**
```
visualize.py::_dispatch()
├─ Graph views (tree/roadmap/risk/etc.) → render_html.assemble() → render_html.write()
│  └─ Template: visual-html-shell.html, tokens: {view_body, mermaid_js, title, …}
├─ Body views (board/explorer) → render_board.write() / render_explorer.write()
│  └─ Template: board-shell.html / explorer-shell.html, tokens: {spec_data, markdown_libs, …}
└─ Audit view → render_html.audit() → render_html.write()
   └─ Template: visual-html-shell.html, tokens: {view_body (table fragment)}
```

### Template Files (Directory: `assets/templates/`)
- `visual-html-shell.html` (108 lines): Graph view wrapper. Tokens: `{{lang}}`, `{{title}}`, `{{viewer_head}}`, `{{view_body}}`, `{{mermaid_js}}`, `{{generated_at}}`, `{{product_name}}`, `{{view}}`, `{{footer_note}}`, `{{tooltip_data}}`, `{{tooltip_js}}`.
- `_viewer-head.html` (82 lines): Shared design-system CSS + theme toggle + helper JS. Included verbatim in every HTML output.
- `board-shell.html`, `explorer-shell.html`, `export-shell.html`: Body-bearing templates with markdown-sanitize chokepoint.

---

## Part 2: Vendored Assets (Exact Paths & Sizes)

All assets vendored inside product-spec skill; **no external CDN at runtime** (CDN fallback only when local files missing).

| Asset | Path | Size | Purpose |
|-------|------|------|---------|
| `mermaid.min.js` | `.claude/skills/product-spec/assets/vendor/mermaid.min.js` | 2.57 MB | Mermaid v11 DSL→SVG renderer |
| `marked.min.js` | `.claude/skills/product-spec/assets/vendor/marked.min.js` | 42.9 KB | Markdown→HTML parser (body rendering only) |
| `purify.min.js` | `.claude/skills/product-spec/assets/vendor/purify.min.js` | 26.8 KB | HTML sanitizer (body rendering only) |
| **Total** | | **2.64 MB** | |

**Asset inlining pattern:**
1. Read file → `Path(...).read_text(encoding="utf-8")`
2. Escape `</script` substring → `re.sub(r"</(script)", r"<\\/\1", payload, flags=re.IGNORECASE)` (line 752)
3. Embed inside `<script>` tags in the HTML template
4. No CDN call at render time; offline self-contained output

**Fallback strategy:** If `mermaid.min.js` missing, `_load_mermaid_js()` returns CDN snippet (line 54–73); if marked/purify missing, `_load_vendored_markdown_libs()` returns None → `markdown_libs_banner()` warns user (line 966–972).

---

## Part 3: Shared Module Analysis (`.claude/skills/_shared/`)

Current content in `_shared/`:
- `lib/plan-table-parser.cjs` — Task/plan parsing (Node.js)
- `lib/llm_eval.py`, `lib/run_evals.py` — LLM eval infrastructure
- `lib/telemetry_paths.py` — Telemetry path discovery
- `scripts/register_telemetry_hooks.py` — Hook registration
- `references/workflow-artifacts.md` — Artifact workflow docs

**No render-related modules exist yet.** Opening for extraction is clean: `_shared/lib/html_render_helpers.py` could house:
- `escape(s)` (renamed from `_escape`)
- `load_mermaid_js(skill_root_path)` (parameterized for reuse)
- `load_vendored_markdown_libs(skill_root_path)` (parameterized)
- `substitute(shell, values)` (generic, no dependencies)

---

## Part 4: Recommended Reuse Path

### Option A: Import Helpers Directly (Direct Path)
**Feasibility:** MEDIUM—requires `render_html.py` path to be stable and public.
- Import `_escape`, `_load_mermaid_js()`, `substitute()` from `render_html`
- Risk: Names prefixed `_` indicate internal; no public API contract
- Benefit: Zero extraction effort, stays DRY immediately
- **Verdict:** Works now, but fragile if render_html refactors

### Option B: Extract Minimal Shared Module (Recommended)
**Feasibility:** HIGH—small, self-contained extraction.
- Create `.claude/skills/_shared/lib/html_render_helpers.py`:
  ```python
  # html_render_helpers.py
  from pathlib import Path
  import re
  from typing import Optional
  
  def escape(s: str) -> str:
      """HTML-safe encode."""
      return (
          str(s).replace("&", "&amp;")
          .replace("<", "&lt;")
          .replace(">", "&gt;")
          .replace('"', "&quot;")
          .replace("'", "&#39;")
      )
  
  def load_mermaid_js(vendor_dir: Path) -> str:
      """Load vendored mermaid or CDN fallback."""
      mermaid_path = vendor_dir / "mermaid.min.js"
      if mermaid_path.exists():
          return mermaid_path.read_text(encoding="utf-8")
      return (
          "/* vendored Mermaid not found — CDN fallback. */\n"
          + "</script>\n"
          + '<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js">'
          + "\n<script>"
      )
  
  def load_marked_purify(vendor_dir: Path) -> Optional[str]:
      """Load vendored marked + purify, or None."""
      marked = vendor_dir / "marked.min.js"
      purify = vendor_dir / "purify.min.js"
      if not (marked.exists() and purify.exists()):
          return None
      payload = purify.read_text(encoding="utf-8") + "\n" + marked.read_text(encoding="utf-8")
      return re.sub(r"</(script)", r"<\\/\1", payload, flags=re.IGNORECASE)
  
  def substitute(shell: str, values: dict) -> str:
      """Single-pass {{token}} substitution."""
      return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), shell)
  ```
- Update `render_html.py` to import from `_shared`:
  ```python
  from sys import path
  path.insert(0, str(SKILL_ROOT.parent / "_shared" / "lib"))
  from html_render_helpers import escape, load_mermaid_js, substitute
  # Rename internal _escape → escape, etc.
  ```
- `analyze_telemetry.py` imports the same:
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).parent.parent / "_shared" / "lib"))
  from html_render_helpers import escape, load_mermaid_js, substitute
  ```

**Benefit:** DRY, explicit contract, scales to 3+ consumers.
**Cost:** 50 lines extraction + test coverage minimal (these are thin wrappers).

### Option C: Hybrid (Extract Only Essential Paths)
**Feasibility:** HIGH—split the load.
- Keep `substitute()` and `escape()` in `render_html.py` (small, never change).
- Extract only `load_mermaid_js()` and `load_marked_purify()` (asset loading is the consumer friction point).
- `analyze_telemetry.py` duplicates `substitute()` and `escape()` (YAGNI—if only used here, <20 lines inline).

**Verdict:** Pragmatic for telemetry-only charts; revisit if a third consumer appears.

---

## Part 5: Minimal Code Sketch — analyze_telemetry.py HTML Output

```python
#!/usr/bin/env python3
"""
analyze_telemetry.py — render telemetry charts as self-contained HTML.
Reuses vendor assets and render helpers from product-spec skill.
"""
import sys
import json
import re
from pathlib import Path
from typing import Any, Dict

# Add _shared to path for helpers
SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "_shared" / "lib"))
from html_render_helpers import escape, load_mermaid_js, substitute

VENDOR_DIR = SKILL_ROOT / "product-spec" / "assets" / "vendor"
TEMPLATE_DIR = SKILL_ROOT / "product-spec" / "assets" / "templates"
VIEWER_HEAD = TEMPLATE_DIR / "_viewer-head.html"

def load_viewer_head() -> str:
    """Shared design-system CSS + helpers."""
    return VIEWER_HEAD.read_text(encoding="utf-8")

def build_telemetry_mermaid(data: Dict[str, Any]) -> str:
    """Convert telemetry data to Mermaid pie/bar chart."""
    # Example: pie chart of command usage
    items = data.get("commands", {})
    slices = "\n    ".join(
        f'{escape(k)} : {v}' for k, v in sorted(items.items(), key=lambda x: x[1], reverse=True)
    )
    return f"""```mermaid
pie title Command Frequency (last 30 days)
    {slices}
```"""

def render_telemetry_html(data: Dict[str, Any], title: str = "Telemetry") -> str:
    """Render telemetry HTML page (reuses vendor assets + shell pattern)."""
    mermaid_text = build_telemetry_mermaid(data)
    # Extract chart from fenced block
    m = re.search(r"```mermaid\n(.*?)\n```", mermaid_text, re.DOTALL)
    chart_body = m.group(1) if m else mermaid_text
    chart_escaped = chart_body.replace("<", "&lt;").replace(">", "&gt;")
    
    values = {
        "lang": "en",
        "title": escape(title),
        "product_name": "(telemetry)",
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "view": "telemetry",
        "view_body": f'<div class="mermaid">\n{chart_escaped}\n</div>',
        "mermaid_js": load_mermaid_js(VENDOR_DIR),
        "footer_note": f"Telemetry report. Vendored assets: {VENDOR_DIR}",
        "viewer_head": load_viewer_head(),
        "tooltip_data": '<script type="application/json" id="ps-tip-data">{}</script>',
        "tooltip_js": "",  # Skip tooltip JS for telemetry (no artifact IDs)
    }
    
    # Use visual-html-shell.html template (same as graph views)
    shell = (TEMPLATE_DIR / "visual-html-shell.html").read_text(encoding="utf-8")
    return substitute(shell, values)

if __name__ == "__main__":
    # Example telemetry data
    sample = {
        "commands": {
            "git_status": 45,
            "python_run": 38,
            "bash_exec": 22,
            "file_read": 18,
        }
    }
    html = render_telemetry_html(sample, "Token Usage Telemetry")
    output = Path("/tmp/telemetry-sample.html")
    output.write_text(html, encoding="utf-8")
    print(f"Written: {output}")
```

**Key reuse points:**
1. `load_mermaid_js(VENDOR_DIR)` → same vendored asset path
2. `escape()` → safe string encoding (used in template values)
3. `substitute(shell, values)` → safe template substitution (no re-scan)
4. `load_viewer_head()` → shared design-system CSS (one look across all product-spec HTML)
5. Template: `visual-html-shell.html` (same 108-line shell, same tokens)

**Output:** Self-contained HTML, offline-ready, no runtime CDN calls (unless mermaid.min.js missing).

---

## Part 6: Extraction Checklist

If pursuing **Option B** (recommended):

- [ ] Create `.claude/skills/_shared/lib/html_render_helpers.py`
- [ ] Write tests: `.claude/skills/_shared/lib/__tests__/test_html_render_helpers.py`
- [ ] Update `render_html.py`: import from `_shared` instead of defining inline
- [ ] Verify all product-spec tests still pass (no behavioral change)
- [ ] Document in `_shared/README.md`: "Asset loading + safe substitution helpers"
- [ ] Create `analyze_telemetry.py` with import path to `_shared/lib`
- [ ] Add to `.claude/.ckignore`: no changes needed (already allows vendor/)

**Effort:** ~2 hours (extraction + tests + verification).
**Risk:** LOW (thin wrappers, no business logic).

---

## Part 7: Constraint Compliance

### No-Network Constraint
**Status:** ✅ Met
- Vendored assets inlined at render time, never fetched at runtime
- CDN fallback only when file missing (degrades gracefully, warns user)
- `analyze_telemetry.py` follows same pattern

### DRY Compliance
**Status:** ✅ Met with Option B
- Three helper functions extracted to one home
- Both `render_html.py` and `analyze_telemetry.py` import the same functions
- No duplication of asset-loading or escaping logic

### Template Reuse
**Status:** ✅ Met
- Same `visual-html-shell.html` serves graph views, audit, and telemetry
- Token set is consistent ({{lang}}, {{title}}, {{view_body}}, {{mermaid_js}}, etc.)
- Telemetry charts plug into the same template contract

---

## Unresolved Questions

1. **Should `load_mermaid_js()` behavior match across skills?** Currently, `render_html.py` distinguishes between vendored (inlined) and CDN fallback. Should `_shared` version do the same, or should each skill's caller decide fallback behavior?
   - *Recommendation:* Export both `_load_vendored_mermaid_js()` and `_cdn_fallback_snippet()` separately, let caller compose.

2. **Where should telemetry HTML output land?** If `analyze_telemetry.py` writes to `docs/product/visuals/`, it shadows product-spec charts. Should it use a different output directory, or is co-location acceptable?
   - *Recommendation:* Use `docs/telemetry/` or a configurable path, avoid collision.

3. **Does the telemetry sketch need marked/purify?** Telemetry charts are pure Mermaid (no markdown bodies), so `load_marked_purify()` is unnecessary. Should the helper be included in `_shared` anyway for future consumers?
   - *Recommendation:* Yes, include it for completeness (board/explorer will eventually call it).

4. **Test coverage for extracted helpers?** `escape()`, `substitute()` are thin but critical (XSS surface). What test vectors apply?
   - *Recommendation:* Round-trip tests (escape → embed → parse → verify), plus attack vectors (e.g., `<script>`, `${...}`, `{{...}}`).

---

## Summary Table: Option B Implementation

| Step | Owner | Effort | Risk | Blocking? |
|------|-------|--------|------|-----------|
| Extract html_render_helpers.py | You | 30 min | LOW | No |
| Write unit tests | You | 45 min | LOW | No |
| Update render_html.py imports | You | 15 min | LOW | No |
| Verify product-spec tests pass | You | 20 min | MEDIUM | **Yes** |
| Implement analyze_telemetry.py | You | 60 min | LOW | No |
| **Total** | | **2.5 h** | | |

---

## Files Referenced

- **Core:** `/home/hieubt/Documents/cleanmatic-skills/.claude/skills/product-spec/scripts/render_html.py` (1098 lines)
- **Template:** `/home/hieubt/Documents/cleanmatic-skills/.claude/skills/product-spec/assets/templates/visual-html-shell.html` (108 lines)
- **Head Partial:** `/home/hieubt/Documents/cleanmatic-skills/.claude/skills/product-spec/assets/templates/_viewer-head.html` (82 lines)
- **Vendor Dir:** `/home/hieubt/Documents/cleanmatic-skills/.claude/skills/product-spec/assets/vendor/` (3 files, 2.64 MB total)
- **Extraction Target:** `.claude/skills/_shared/lib/html_render_helpers.py` (to be created)
