"""pack — deterministic tarball builder for cleanmatic:claude-pack.

Modularized into ``cli``, ``tarball``, ``manifest_io``, ``templates``
(each <200 LOC). See ``../../SKILL.md`` for the operating contract and
``plan.md`` for locked signatures.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from .cli import main  # noqa: E402

__version__ = "0.1.0"
__all__ = ["main", "__version__"]
