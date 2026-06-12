#!/usr/bin/env python3
"""
render_html — thin orchestrator for self-contained HTML visualization pages.

Reads:
  - assets/templates/visual-html-shell.html (the page skeleton)
  - assets/vendor/mermaid.min.js (vendored Mermaid; pin via install.sh)

If the vendored mermaid.min.js is missing, the renderer falls back to a
CDN-hosted script tag and prints a visible warning banner in the output.

Output is one self-contained file at:
  docs/product/visuals/<view>-<timestamp>.html

CLI usage is via visualize.py.

Structure:
  render_html_risk_grid.py    — HTML-native risk grid (3×3 impact × likelihood table)
  render_html_assets.py       — vendor/asset loaders + body-render helpers
  render_html_count_grid.py   — HTML-native count grids (status heatmap, persona coverage)
  render_html_competition.py  — HTML-native competition view (parity matrix + threat heatmap)
  render_html_tooltip.py      — hover-tooltip island + client scanner
  render_html_governance.py   — HTML-native audit trail + multi-dim dashboard
  render_html.py              — this orchestrator: escaping, view-body dispatch, page assembly
"""

import datetime as dt
import re
from pathlib import Path
from typing import Any, Dict

from spec_graph import _now
from i18n_labels import label
from fs_guard import assert_under_docs_product

# ── Sub-module imports (public re-exports preserved for callers) ──────────────
from render_html_risk_grid import (          # noqa: F401 — re-exported
    risk,
    _RISK_GRID_CSS,
    _risk_heat_class,
    _risk_cell_detail,
)
from render_html_escape import _escape       # noqa: F401 — re-exported
from render_html_assets import (             # noqa: F401 — re-exported
    _load_vendored_mermaid_js,
    _cdn_fallback_snippet,
    _load_mermaid_js,
    _load_vendored_markdown_libs,
    viewer_head,
    embed_spec_data,
    markdown_libs_banner,
    body_render_values,
    _BODY_RENDER_JS,
    VENDOR_MERMAID,
    CDN_FALLBACK,
)
from render_html_count_grid import (         # noqa: F401 — re-exported
    heatmap,
    persona,
    _COUNT_GRID_CSS,
    _is_deferred_node,
)
from render_html_competition import (        # noqa: F401 — re-exported
    competition,
    _COMPETITION_CSS,
    _PARITY_CELL_CLASS,
    _THREAT_CELL_CLASS,
)
from render_html_tooltip import (            # noqa: F401 — re-exported
    tooltip_index,
    tooltip_island,
    _TOOLTIP_JS,
    _tip_scalar,
)
from render_html_governance import (         # noqa: F401 — re-exported
    audit,
    dashboard,
    _AUDIT_CSS,
    _DASHBOARD_CSS,
)

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"
SHELL_PATH = TEMPLATES / "visual-html-shell.html"
VIEWER_HEAD_PARTIAL = TEMPLATES / "_viewer-head.html"


def _render_view_body(view_format: str, view_text: str) -> str:
    """Wrap the per-view body so the page renders Mermaid OR pre text.

    view_format == "mermaid"   -> extract inner Mermaid DSL from fenced block,
                                  wrap in <div class="mermaid">.
    view_format == "html"/"risk-grid" -> view_text is an ALREADY-SAFE HTML
                                  fragment (e.g. the risk() grid, whose spec
                                  text was escaped at build time). Inject as-is
                                  — do NOT re-escape (that would render the
                                  <table> markup as literal text).
    view_format == "pre" / *   -> escape view_text and wrap in <pre> so the
                                  browser renders raw ASCII (used for the
                                  heatmap / persona views where Mermaid has no
                                  clean expression).
    """
    if view_format in ("html", "risk-grid"):
        # Pre-rendered HTML-native fragment. The ONLY safe-HTML view_format:
        # the producer (render_html.risk) is responsible for escaping every
        # spec-derived value through _escape() before assembling the fragment.
        return view_text
    if view_format == "mermaid":
        m = re.search(r"```mermaid\n(.*?)\n```", view_text, re.DOTALL)
        body = m.group(1) if m else view_text
        # Escape only `<` and `>` in the Mermaid DSL body — NOT `&`.
        #
        # Defense-in-depth layer: the HTML parser runs before Mermaid's
        # auto-renderer, so raw `<script>` or `<img onerror=…>` in the DSL
        # body would execute during parsing before securityLevel:strict can
        # intercept.  Escaping `<`/`>` neutralises that class of injection
        # while keeping `-->` as a safe textContent round-trip (`--&gt;` in
        # source decodes back to `-->` when Mermaid reads .textContent).
        #
        # `&` is intentionally NOT escaped here. `_safe_label` (in
        # render_mermaid) already encodes `&` → `&amp;` at the label
        # chokepoint.  Escaping `&` again here would double-encode to
        # `&amp;amp;`, so a node titled "R&D" would render as literal
        # "R&amp;D" in the browser instead of "R&D".
        body_escaped = body.replace("<", "&lt;").replace(">", "&gt;")
        return f'<div class="mermaid">\n{body_escaped}\n</div>'
    return f"<pre>{_escape(view_text)}</pre>"


# ── Shared body-render substrate (export / board / explorer) ────────────────
#
# Body-bearing HTML outputs render artifact markdown bodies CLIENT-SIDE through
# the chokepoint  DOMPurify.sanitize(marked.parse(md))  (defined in
# _viewer-head.html as psRenderMarkdown). The server NEVER injects body HTML; it
# ships bodies as an inert JSON data island. Two enumerated sinks:
#   1. the embedded-JSON body channel  → escaped via embed_spec_data()
#   2. attribute-context values (data-*, aria-label, id) → built client-side via
#      safe DOM APIs (textContent / dataset) and/or _escape() for server tokens.
#      There is no href channel: bodies are sanitized by DOMPurify, metadata is
#      set via textContent/dataset — no renderer ever emits a spec-derived href.


def file_timestamp() -> str:
    """Compact UTC stamp (`%Y%m%dT%H%M%SZ`, no colons) for output filenames — one
    source for every writer (export / board / explorer / the 12 graph views). The
    colon-bearing ISO body stamp is `spec_graph._now`; this is its filename twin."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def product_name(graph: Dict[str, Any]) -> str:
    """The product display name, or `(unnamed)` — one source for every renderer.
    Coerces a non-str name (and a non-dict product block from a poisoned graph
    JSON) to str so chrome/heading callers never crash in _escape / .replace."""
    product = graph.get("product")
    name = product.get("name") if isinstance(product, dict) else None
    return str(name) if name else "(unnamed)"


def goal_detail_md(node: Dict[str, Any], lang: str = "en") -> str:
    """Synthesize a markdown detail body for a BRD goal card.

    Goals are expanded from `brd.md.goals` and carry no narrative body of their own
    (spec_graph.index_artifacts deliberately does not key them — the BRD prose is the
    container's, not any one goal's). The board/explorer detail panel renders a
    per-card markdown body, so a goal card would otherwise open empty while a PRD/
    epic/story shows its file body. Surface the goal's metrics — the one field no
    card badge or table column in either viewer already shows (status/owner/etc. are
    columns) — as markdown that flows through the same client sanitize chokepoint as
    every body. Returns "" for any non-goal node so callers fall back to the artifact
    body, and "" for a goal with no metrics (nothing additive to synthesize)."""
    if node.get("type") != "goal":
        return ""
    raw = node.get("metrics")
    if not isinstance(raw, list):
        # A bare-scalar `metrics:` would char-split into phantom items; the
        # risk/competition renderers in this file apply the same isinstance gate.
        raw = [raw] if raw else []
    metrics = [str(m) for m in raw if m]
    if not metrics:
        return ""
    return f"**{label('metrics', lang)}:** " + ", ".join(metrics)


def chrome_values(graph: Dict[str, Any], lang: str, title: str) -> Dict[str, str]:
    """The body-shell token preamble shared by export / board / explorer:
    `lang_attr`, escaped `title`, escaped `product_name`, `generated_at`. Pairs
    with body_render_values() (which supplies viewer_head/markdown_libs/spec_data)."""
    return {
        "lang_attr": lang,
        "title": _escape(title),
        "product_name": _escape(product_name(graph)),
        "generated_at": _now(),
    }


def assemble_body_shell(shell: str, payload: Any, graph: Dict[str, Any],
                        lang: str, title: str) -> str:
    """Assemble one body-bearing shell: body-render substrate + chrome preamble →
    single-pass substitute. Collapses the `read → values → update → substitute`
    plumbing that board/explorer (and export) otherwise copy-paste verbatim."""
    values = body_render_values(payload)
    values.update(chrome_values(graph, lang, title))
    return substitute(shell, values)


def assemble(
    view: str,
    view_format: str,
    view_text: str,
    graph: Dict[str, Any],
    lang: str = "en",
) -> str:
    """Build the full HTML page string."""
    shell = SHELL_PATH.read_text(encoding="utf-8")
    title = f"{view.title()} View"

    # The `time` view (TIME dimension) builds its own body from the graph when no
    # body text is supplied: a CYCLE-SAFE Mermaid gantt + depends_on annotations
    # (render_mermaid.time uses a visited-set walk, so a circular depends_on chain
    # terminates instead of hanging this renderer). Imported
    # lazily: render_mermaid imports render_ascii, neither imports render_html, so
    # there is no import cycle, but the lazy import keeps module-load order simple.
    if view == "time" and not view_text:
        import render_mermaid
        view_text = render_mermaid.time(graph, lang=lang)
        view_format = "mermaid"
    generated_at = _now()
    footer = (
        "Self-contained HTML. To re-render: "
        "python3 visualize.py --view "
        f"{view} --format html --root &lt;dir&gt;"
    )
    if not VENDOR_MERMAID.exists():
        footer = (
            '<strong style="color:#c33">Note:</strong> vendored mermaid.min.js '
            "missing; CDN fallback in use. Run install.sh to vendor it.<br>"
            + footer
        )
    # INVARIANT: footer_note is injected into the HTML template WITHOUT further
    # escaping (it may contain renderer-literal markup such as <strong>).
    # Any spec-derived value added to footer_note in the future MUST be passed
    # through _escape() before interpolation — never interpolated raw.

    # ASCII-fallback views (view_format != "mermaid") render as plain <pre>;
    # the Mermaid runtime is never used, so skipping it saves ~2.5 MB and the
    # cost of an unnecessary `mermaid.initialize()` scan on every page load.
    mermaid_js_payload = _load_mermaid_js() if view_format == "mermaid" else ""

    values = {
        "lang": lang,
        "title": title,
        "generated_at": generated_at,
        "product_name": _escape(product_name(graph)),
        "view": view,
        "view_body": _render_view_body(view_format, view_text),
        "mermaid_js": mermaid_js_payload,
        "footer_note": footer,
        # The graph + HTML-native views adopt the shared design-system head too, so
        # ALL product-spec HTML (graph/native + board/explorer/export) looks identical.
        # EXTEND-only: every prior token + the RAW-footer_note invariant are
        # preserved; legacy views still inline NO SKILL sanitizer — no bodies, so
        # no {{markdown_libs}} block and no psRenderMarkdown chokepoint. NB the
        # mermaid-format payload bundles Mermaid's OWN internal DOMPurify for SVG
        # sanitization; that third-party copy is not a body-render sink and is
        # exempt from the symmetric-gating rule — the contract is "no skill body-sanitizer", not "no
        # vendor lib named DOMPurify".
        "viewer_head": viewer_head(),
        # Hover-on-ID: an inert id→{title,meta} island + the client scanner that
        # tags Mermaid SVG labels / wraps bare IDs in text so every artifact ID in
        # any graph or HTML-native view surfaces its title + metadata on hover.
        "tooltip_data": tooltip_island(graph),
        "tooltip_js": _TOOLTIP_JS,
    }
    return substitute(shell, values)


def substitute(shell: str, values: Dict[str, str]) -> str:
    """Single-pass `{{token}}` substitution.

    A multi-pass `for k,v: shell.replace(...)` re-scans already-inserted content
    on every later key, so a spec-derived value of `"{{mermaid_js}}"` would
    inject the whole Mermaid payload, and a body containing `{{footer_note}}`
    would bleed the footer. A single `re.sub` pass expands each `{{token}}`
    exactly once and never re-scans the inserted value, closing that injection /
    bleed sink (shared by the 9 legacy views and every body-bearing shell).
    Unknown tokens are left verbatim so partial shells fail loudly, not silently.
    """
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), shell)


def _write_visual(root: Path, filename: str, html: str) -> Path:
    """Write a self-contained visual to docs/product/visuals/<filename>. One home for
    the out_dir + mkdir + write_text + return that the 12 graph views and the board /
    explorer writers otherwise copy verbatim."""
    out_dir = root / "docs" / "product" / "visuals"
    target = out_dir / filename
    # Soft-fence: resolve + contain BEFORE mkdir/write so a filename carrying
    # traversal cannot escape docs/product/ (and never creates stray dirs).
    assert_under_docs_product(target, root)
    out_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return target


def write(
    root: Path,
    view: str,
    view_format: str,
    view_text: str,
    graph: Dict[str, Any],
    lang: str = "en",
) -> Path:
    """Write the assembled HTML to docs/product/visuals/<view>-<ts>.html."""
    return _write_visual(root, f"{view}-{file_timestamp()}.html",
                         assemble(view, view_format, view_text, graph, lang))
