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


def _load_mermaid_js() -> str:
    """Return the inline Mermaid JS payload or a CDN-fallback <script> tag."""
    if VENDOR_MERMAID.exists():
        return VENDOR_MERMAID.read_text(encoding="utf-8")
    # Fallback: load Mermaid from CDN with a visible warning. The shell
    # template embeds this whole string inside a <script> tag, so output
    # a `</script>` to close it, an external <script>, and reopen a
    # placeholder script so the surrounding template stays valid.
    warning = (
        "console.warn('product-spec: vendored mermaid.min.js is missing; "
        "falling back to CDN. Run install.sh to vendor the file for "
        "offline self-containment.');"
    )
    cdn = (
        "/* vendored Mermaid not found — falling back to CDN. */\n"
        + warning
        + "\n</script>\n"
        + f'<script src="{CDN_FALLBACK}"></script>\n'
        + "<script>"
    )
    return cdn


def _render_view_body(view_format: str, view_text: str) -> str:
    """Wrap the per-view body so the page renders Mermaid OR pre text."""
    if view_format == "mermaid":
        # The view emits a fenced ```mermaid block; extract inner graph code.
        m = re.search(r"```mermaid\n(.*?)\n```", view_text, re.DOTALL)
        body = m.group(1) if m else view_text
        return f'<div class="mermaid">\n{body}\n</div>'
    return f"<pre>{_escape(view_text)}</pre>"


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
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

    values = {
        "lang": lang,
        "title": title,
        "generated_at": generated_at,
        "product_name": _escape(product_name),
        "view": view,
        "view_body": _render_view_body(view_format, view_text),
        "mermaid_js": _load_mermaid_js(),
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
