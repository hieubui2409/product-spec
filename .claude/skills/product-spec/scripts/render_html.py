#!/usr/bin/env python3
"""
render_html — assemble a self-contained HTML visualization page.

Reads:
  - assets/templates/visual-html-shell.html (the page skeleton)
  - assets/vendor/mermaid.min.js (vendored Mermaid; pin via install.sh)

If the vendored mermaid.min.js is missing, the renderer falls back to a
CDN-hosted script tag and prints a visible warning banner in the output.

Output is one self-contained file at:
  docs/product/visuals/<view>-<timestamp>.html

CLI usage is via visualize.py.
"""

import datetime as dt
import re
from pathlib import Path
from typing import Any, Dict, Optional


SKILL_ROOT = Path(__file__).resolve().parent.parent
SHELL_PATH = SKILL_ROOT / "assets" / "templates" / "visual-html-shell.html"
VENDOR_MERMAID = SKILL_ROOT / "assets" / "vendor" / "mermaid.min.js"
CDN_FALLBACK = (
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"
)


def _load_vendored_mermaid_js() -> Optional[str]:
    """Return the inline Mermaid JS payload if vendored; else None.

    Split out from the CDN-fallback path so each path has a single
    responsibility: this one only reads the local file, returns None on
    miss. The caller decides whether to fall back.
    """
    if VENDOR_MERMAID.exists():
        return VENDOR_MERMAID.read_text(encoding="utf-8")
    return None


def _cdn_fallback_snippet() -> str:
    """Return a <script>-close + CDN-load + <script>-reopen snippet.

    The shell template embeds the returned string inside a `<script>` tag.
    To inject an external `<script src=...>`, this snippet closes the
    surrounding tag, emits the CDN tag, then reopens an empty `<script>`
    so the rest of the shell stays syntactically valid.
    """
    warning = (
        "console.warn('product-spec: vendored mermaid.min.js is missing; "
        "falling back to CDN. Run install.sh to vendor the file for "
        "offline self-containment.');"
    )
    return (
        "/* vendored Mermaid not found — falling back to CDN. */\n"
        + warning
        + "\n</script>\n"
        + f'<script src="{CDN_FALLBACK}"></script>\n'
        + "<script>"
    )


def _load_mermaid_js() -> str:
    """Return either the vendored JS payload or the CDN-fallback snippet.

    Thin compatibility wrapper kept so callers (and tests) that don't care
    about the source can stay one-line. New code should prefer the two
    explicit helpers above to make the source path obvious at the call site.
    """
    vendored = _load_vendored_mermaid_js()
    return vendored if vendored is not None else _cdn_fallback_snippet()


def _render_view_body(view_format: str, view_text: str) -> str:
    """Wrap the per-view body so the page renders Mermaid OR pre text.

    view_format == "mermaid"  -> extract inner Mermaid DSL from fenced block,
                                 wrap in <div class="mermaid">.
    view_format == "pre" / *  -> escape view_text and wrap in <pre> so the
                                 browser renders raw ASCII (used for the
                                 heatmap / persona / risk views where Mermaid
                                 has no clean expression).
    """
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


def _escape(s: str) -> str:
    # & must be replaced first so subsequent escaped sequences don't get double-escaped.
    # Quotes are escaped to make the function safe for attribute context as well as body
    # context, even though current call sites only feed body text.
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )


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
    product_name = (graph.get("product") or {}).get("name") or "(unnamed)"
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"
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
        "product_name": _escape(product_name),
        "view": view,
        "view_body": _render_view_body(view_format, view_text),
        "mermaid_js": mermaid_js_payload,
        "footer_note": footer,
    }
    for k, v in values.items():
        shell = shell.replace("{{" + k + "}}", v)
    return shell


def write(
    root: Path,
    view: str,
    view_format: str,
    view_text: str,
    graph: Dict[str, Any],
    lang: str = "en",
) -> Path:
    """Write the assembled HTML to docs/product/visuals/<view>-<ts>.html."""
    out_dir = root / "docs" / "product" / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = out_dir / f"{view}-{ts}.html"
    target.write_text(assemble(view, view_format, view_text, graph, lang), encoding="utf-8")
    return target
