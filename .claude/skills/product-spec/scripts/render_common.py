#!/usr/bin/env python3
"""render_common — tiny shared helpers for the product-spec ASCII renderers.

product-spec-internal (inside the bundled skill tree — no manifest/packaging surface).
Home for `_hashable`, which was byte-identically duplicated in `render_ascii` and
`render_ascii_board`. A neutral third module avoids the existing render_ascii ↔
render_ascii_board circular-import (render_ascii imports the board module at top level,
the board module imports render_ascii lazily).
"""

from __future__ import annotations

from typing import Any


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
