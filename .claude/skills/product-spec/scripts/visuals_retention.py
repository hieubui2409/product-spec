#!/usr/bin/env python3
"""
visuals_retention — stable latest-alias, staleness banner, content-hash reuse,
and clean-old-renders for the product-spec visualization pipeline.

Public API (called by visualize.py dispatch / render_html.write wiring):
  latest_alias(out_path)                      -> Path  (write/refresh <view>-latest.html)
  staleness_banner(root, view, graph)         -> str   (empty when 0 drift)
  save_render_signature(root, view, out_path, graph)   (persist baseline node-id set)
  content_hash(html)                          -> str   (sha256 hex of UTF-8 encoded HTML)
  record_content_hash(root, view, out_path, html)      (store hash sidecar)
  reuse_if_unchanged(root, view, html)        -> Optional[Path]
  clean_old_renders(root, view, keep=5)       -> List[Path]  (returns deleted paths)

Design decisions:
  - Alias is a copy (not a symlink) — symlinks are unsupported on some filesystems.
  - Hash sidecar: .hashes/<view>.json alongside docs/product/visuals/
  - Node signature sidecar: .signatures/<view>.json (sorted list of node ids)
  - Missing sidecar → treat as changed (safe: will re-render).
  - keep default = 5 (chosen in phase-04 — hard integer, DRY: one place).
  - Retention never deletes a file whose name ends with "-latest.html".
"""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Constants ─────────────────────────────────────────────────────────────────

# Hard retention count: keep this many most-recent timestamped renders per view.
# Stated here as the single authoritative source; phase-04 implementation report
# records this choice (DRY — never embed the literal 5 elsewhere in this module).
RETENTION_KEEP = 5

_HASHES_DIR = ".hashes"
_SIGS_DIR = ".signatures"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _visuals_dir(root: Path) -> Path:
    """Canonical output directory; created on demand."""
    d = root / "docs" / "product" / "visuals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _hashes_dir(root: Path) -> Path:
    d = _visuals_dir(root) / _HASHES_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sigs_dir(root: Path) -> Path:
    d = _visuals_dir(root) / _SIGS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _hash_file(root: Path, view: str) -> Path:
    return _hashes_dir(root) / f"{view}.json"


def _sig_file(root: Path, view: str) -> Path:
    return _sigs_dir(root) / f"{view}.json"


def _node_ids(graph: Dict[str, Any]) -> List[str]:
    """Sorted list of node ids from a graph dict — deterministic for hashing."""
    nodes = graph.get("nodes") or []
    return sorted(str(n.get("id", "")) for n in nodes if n)


# ── Public API ────────────────────────────────────────────────────────────────

def content_hash(html: str) -> str:
    """SHA-256 of the UTF-8 encoded HTML string.

    Stable for identical content regardless of platform (same bytes → same hash).
    """
    return hashlib.sha256(html.encode("utf-8")).hexdigest()


def record_content_hash(root: Path, view: str, out_path: Path, html: str) -> None:
    """Persist the content hash + file path for the most recent render of `view`."""
    hf = _hash_file(root, view)
    data = {
        "hash": content_hash(html),
        "path": str(out_path),
    }
    hf.write_text(json.dumps(data, indent=2), encoding="utf-8")


def reuse_if_unchanged(root: Path, view: str, html: str) -> Optional[Path]:
    """Return the existing render path if `html` matches the last recorded hash.

    Returns None when content differs (caller should write a new file).
    Missing sidecar is treated as "changed" (safe: forces a fresh render).
    """
    hf = _hash_file(root, view)
    if not hf.exists():
        return None
    try:
        data = json.loads(hf.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("hash") != content_hash(html):
        return None
    p = Path(data.get("path", ""))
    if p.exists():
        return p
    return None


def save_render_signature(root: Path, view: str, out_path: Path,
                          graph: Dict[str, Any]) -> None:
    """Persist the sorted node-id list from `graph` as the render-time baseline."""
    sf = _sig_file(root, view)
    data = {
        "node_ids": _node_ids(graph),
        "path": str(out_path),
    }
    sf.write_text(json.dumps(data, indent=2), encoding="utf-8")


def staleness_banner(root: Path, view: str, graph: Dict[str, Any]) -> str:
    """Return a stale-banner string when the current graph differs from baseline.

    The drift count is len(symmetric difference between baseline and current node ids).
    Returns "" when drift == 0 or no baseline signature exists (treat as fresh).
    """
    sf = _sig_file(root, view)
    if not sf.exists():
        return ""
    try:
        data = json.loads(sf.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    baseline_ids = set(data.get("node_ids") or [])
    current_ids = set(_node_ids(graph))
    added = current_ids - baseline_ids
    removed = baseline_ids - current_ids
    drift = len(added) + len(removed)
    if drift == 0:
        return ""
    return f"stale — {drift} nodes drifted since render"


def latest_alias(out_path: Path) -> Path:
    """Write/refresh the <view>-latest.html file as a copy of `out_path`.

    The alias name is derived by stripping the timestamp suffix from the filename:
      <view>-<ts>.html  →  <view>-latest.html

    Falls back to a copy rather than a symlink for filesystem portability.
    Returns the alias Path.
    """
    stem = out_path.stem  # e.g. "tree-20260101T000000Z"
    # Strip the last hyphen-separated segment (the timestamp or any suffix)
    parts = stem.rsplit("-", 1)
    # Handle the case where the stem has no hyphen (safety fallback)
    view = parts[0] if len(parts) > 1 else stem
    alias = out_path.parent / f"{view}-latest.html"
    shutil.copy2(str(out_path), str(alias))
    return alias


def clean_old_renders(root: Path, view: str, keep: int = RETENTION_KEEP) -> List[Path]:
    """Delete old timestamped renders for `view`, keeping the `keep` most recent.

    Rules:
      - Never deletes a file whose name ends with "-latest.html".
      - Sorts candidates by filename (timestamp prefix → lexicographic == chronological
        for the compact UTC stamp format %Y%m%dT%H%M%SZ).
      - Returns the list of deleted Paths.
      - No-op (returns []) when zero or ≤keep renders exist.
    """
    vdir = _visuals_dir(root)
    # Gather only timestamped renders (not -latest aliases, not sidecar dirs)
    candidates = sorted(
        p for p in vdir.glob(f"{view}-*.html")
        if not p.name.endswith("-latest.html")
    )
    to_delete = candidates[:-keep] if len(candidates) > keep else []
    deleted: List[Path] = []
    for p in to_delete:
        p.unlink(missing_ok=True)
        deleted.append(p)
    return deleted
