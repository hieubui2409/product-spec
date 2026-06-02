#!/usr/bin/env python3
"""critique_common.py — shared low-level primitives for the spec-critique scripts.

The single home for the cross-dir product-spec import, the UTC stamp, and the graph
helpers (target resolution + body_hash maps + provenance fingerprint) that
critique_scan / critique_bundle / critique_provenance / critique_drift all reuse.
Kept dependency-free of the other critique_* modules so it sits at the bottom of the
import DAG (no cycles)."""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BUNDLE_VERSION = 2  # v2 adds source_files (line-numbered) + per-entry source_file
DEFAULT_THRESHOLD = 3

# Body-hash sentinels the cache key uses for an absent/bodyless node. They are not
# real content fingerprints, so drift must never count them as a change.
_HASH_SENTINELS = frozenset({"none", "missing"})


def _psp_dir() -> Path:
    """The product-spec `scripts/` dir, resolved relative to this file.

    Layout: `.claude/skills/spec-critique/scripts/critique_common.py`
         -> `.claude/skills/product-spec/scripts/`. parents[2] is `.claude/skills/`."""
    return Path(__file__).resolve().parents[2] / "product-spec" / "scripts"


def _import_psp():
    """Import the pure product-spec helpers (spec_graph, assemble_digest,
    judgment_cache, preferences, fs_guard). Loud error if the product-spec scripts
    dir is absent — the skill cannot run without it."""
    psp = _psp_dir()
    if not psp.is_dir():
        raise ModuleNotFoundError(
            f"product-spec scripts dir not found at {psp}. spec-critique reuses "
            "product-spec's scripts; install product-spec first."
        )
    sd = str(psp)
    if sd not in sys.path:
        sys.path.insert(0, sd)
    import spec_graph
    import assemble_digest
    import judgment_cache
    import preferences
    import fs_guard
    return spec_graph, assemble_digest, judgment_cache, preferences, fs_guard


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _node_index(graph: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {n["id"]: n for n in graph.get("nodes", [])}


def _resolve_targets(spec_graph, graph: Dict[str, Any], scope: str) -> Tuple[List[str], Optional[str]]:
    """Resolve the critique target id-set: scope node + its descendants.

    Returns (target_ids, error). scope == 'all' -> every node. An unknown scope
    yields ([], error) so the caller records a parse_error and emits an empty
    bundle rather than crashing."""
    ids = [n["id"] for n in graph.get("nodes", [])]
    if scope == "all":
        return sorted(ids), None
    if scope not in set(ids):
        return [], f"unknown scope {scope!r}: not an artifact id in the spec"
    targets = {scope} | spec_graph.downstream(graph, scope)
    return sorted(targets), None


def _live_body_hashes(spec_graph, root: Path) -> Dict[str, str]:
    """Per-node body_hash from a fresh build_graph. Skips nodes whose body_hash is
    None (goals — no standalone body to fingerprint)."""
    graph = spec_graph.build_graph(root)
    out: Dict[str, str] = {}
    for n in graph.get("nodes", []):
        bh = n.get("body_hash")
        if isinstance(bh, str) and bh not in _HASH_SENTINELS:
            out[n["id"]] = bh
    return out


def _scoped_body_hashes(spec_graph, root: Path, scope: str) -> Dict[str, str]:
    """Per-node body_hash for the in-scope nodes (scope node + descendants). For
    scope=='all' this is every bodied node. Reuses build_graph; skips sentinel/None
    hashes (goals)."""
    graph = spec_graph.build_graph(root)
    out: Dict[str, str] = {}
    for n in graph.get("nodes", []):
        bh = n.get("body_hash")
        if isinstance(bh, str) and bh not in _HASH_SENTINELS:
            out[n["id"]] = bh
    if scope == "all":
        return out
    target_ids, _err = _resolve_targets(spec_graph, graph, scope)
    tset = set(target_ids)
    return {i: h for i, h in out.items() if i in tset}


def _provenance_hash(body_hash_map: Dict[str, str]) -> str:
    """A stable 16-hex fingerprint of the scoped body_hash map (sorted, no
    whitespace) — the critique-state fast-path key for 'spec unchanged since last
    critique'."""
    canon = json.dumps(body_hash_map, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]
