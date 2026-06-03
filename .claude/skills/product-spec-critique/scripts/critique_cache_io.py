#!/usr/bin/env python3
"""critique_cache_io.py — the shared IO chokepoint for the product-spec-critique caches.

The memory dir resolver, the tolerant JSON reader, and the fenced canonical JSON
writer that both `critique_cache` (index/state/humanized) and `critique_blob_cache`
(web/lens file-per-key stores) build on. Kept as a tiny leaf module so neither cache
module imports the other (no cycle), and the fs_guard fence has ONE home.

Determinism: writes are sorted-key + trailing-newline → byte-stable. All writes
resolve through `fs_guard.assert_under_docs_product` BEFORE touching disk. Reads are
tolerant: missing/corrupt → None, never raise."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _psp_dir() -> Path:
    """The product-spec `scripts/` dir, resolved relative to this file (parents[2]
    is `.claude/skills/`)."""
    return Path(__file__).resolve().parents[2] / "product-spec" / "scripts"


def _fs_guard():
    """Import + return the product-spec fs_guard MODULE (not a bound function) so a
    test monkeypatching `fs_guard.assert_under_docs_product` takes effect at our call
    site."""
    psp = _psp_dir()
    if not psp.is_dir():
        raise ModuleNotFoundError(
            f"product-spec scripts dir not found at {psp}. product-spec-critique reuses "
            "product-spec's fs_guard; install product-spec first."
        )
    sd = str(psp)
    if sd not in sys.path:
        sys.path.insert(0, sd)
    import fs_guard
    return fs_guard


def _now() -> str:
    """Fallback UTC stamp ONLY for a caller that passes no `now_iso`. The cache logic
    never calls this implicitly — every public writer accepts `now_iso` so a test can
    pin time and assert byte-determinism."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _memory_dir(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory"


def _read_json(path: Path) -> Optional[Any]:
    """Parse a JSON file, or None on missing/corrupt — never raise."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _write_json(root, path: Path, data: Any) -> Path:
    """Write `data` as canonical JSON through the soft fence (resolve + contain
    BEFORE any mkdir/write). Sorted keys + trailing newline → byte-stable."""
    fs_guard = _fs_guard()
    resolved = fs_guard.assert_under_docs_product(path, root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return resolved
