#!/usr/bin/env python3
"""render_common — tiny shared helpers for the product-spec ASCII renderers.

product-spec-internal (inside the bundled skill tree — no manifest/packaging surface).
Home for the helpers that were byte-identically duplicated in `render_ascii` and
`render_ascii_board` (`_hashable`, `_is_deferred`, `_inline`, `_mark`). A neutral third
module avoids the existing render_ascii ↔ render_ascii_board circular-import (render_ascii
imports the board module at top level, the board module imports render_ascii lazily).
"""

from __future__ import annotations

from typing import Any, Dict


def _hashable(v: Any) -> str:
    """Coerce frontmatter values that should be enum scalars to a string.

    A PO who writes `status: [draft]` (list) or some other unhashable shape would
    otherwise crash dict indexing. Render the unexpected shape verbatim so the
    validator can flag `unknown_enum` separately, but never blow up the viz renderer.
    """
    if v is None:
        return "?"
    if isinstance(v, (list, dict, set)):
        return f"?{v!r}"
    return str(v)


def _is_deferred(node: Dict[str, Any]) -> bool:
    """A node is 'deferred' if either MoSCoW says won't OR scope says out."""
    return node.get("moscow") == "wont" or node.get("scope") == "out"


def _inline(s: Any) -> str:
    """Collapse any whitespace run (incl. CR/LF/tabs) to a single space and strip
    the ends. A free-text title written as a multi-line YAML scalar would otherwise
    inject extra lines into a one-line-per-node text summary or tree row, corrupting
    the deterministic grammar (and any naive line-count parser of the CI output).
    Mermaid's `_safe_label` and export's `_heading` collapse the same way."""
    return " ".join(str(s).split())


def _mark(node: Dict[str, Any], text: str) -> str:
    """Suffix the rendered text with a `*` when the node is deferred."""
    return f"{text} *" if _is_deferred(node) else text
