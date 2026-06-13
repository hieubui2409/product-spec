"""Single home for HTML escaping shared by the render_html_* module family.

This is a leaf module — it imports nothing from the render_html family — so the
orchestrator and every view module can import one escaper instead of each
carrying a self-contained copy. The escaper is the XSS chokepoint, so a second,
slightly-different copy is a security-consistency hazard, not merely duplication.
"""

from __future__ import annotations

from typing import Any


def _escape(s: str) -> str:
    # & must be replaced first so subsequent escaped sequences don't get double-encoded.
    # Quotes are escaped to make the function safe for attribute context as well as body
    # context, even though current call sites only feed body text. str() guards non-str input.
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _tip_scalar(v: Any) -> str:
    """Coerce a node field that may arrive as a 1-element list (a hand-edited
    `status: [draft]`) to a plain string for HTML meta lines / count-grid keys.
    One home for the count-grid and tooltip renderers (was duplicated in both)."""
    if isinstance(v, list):
        v = v[0] if v else ""
    return str(v) if v not in (None, "") else ""
