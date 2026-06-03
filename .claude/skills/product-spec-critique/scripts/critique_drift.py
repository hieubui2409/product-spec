#!/usr/bin/env python3
"""critique_drift.py — the snapshot + drift modes of product-spec-critique.

`write_snapshot` persists the per-node body_hash baseline (`last_critique.json`);
`compute_drift` counts body_hash changes vs that baseline (live build, or the
cheaper validate-time hashes recovered from judgments.json keys on the Stop-hook
path). All deterministic, all advisory — drift never blocks."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from critique_common import _HASH_SENTINELS, _import_psp, _live_body_hashes, _now


def _validated_body_hashes(judgment_cache, root: Path) -> Optional[Dict[str, str]]:
    """Validate-time per-node body_hash recovered from judgments.json keys.

    Each single-node key embeds the node's body_hash as its 3rd `|` segment
    (`check|node_id|body_hash|lang|dep_hash`). Pair-check keys (`idA+idB`) are
    skipped — their hash segment is `hashA+hashB`, not a single node's hash.

    The cache GC only evicts entries for DELETED node ids, never a superseded
    body_hash for a still-live id, so a node can carry two distinct validate-time
    hashes (old + new body, both validated). We collect ALL distinct hashes per node
    and keep one ONLY when there is exactly one; a node with conflicting hashes is
    UNCERTAIN and excluded (conservative). Returns None when the cache is
    absent/empty so the caller can fall back to a live build."""
    cache = judgment_cache.load_cache(root)
    if not cache:
        return None
    entries = cache.get("entries")
    if not isinstance(entries, dict) or not entries:
        return None
    seen: Dict[str, set] = {}
    for key in entries:
        parts = str(key).split("|")
        if len(parts) < 3:
            continue
        scope_key, body_hash = parts[1], parts[2]
        if "+" in scope_key:  # pair check — composite hash, not a single node's
            continue
        if body_hash and body_hash not in _HASH_SENTINELS:
            seen.setdefault(scope_key, set()).add(body_hash)
    out = {nid: next(iter(hashes)) for nid, hashes in seen.items() if len(hashes) == 1}
    return out or None


def _load_marker(root: Path) -> Optional[Dict[str, Any]]:
    path = root / "docs" / "product" / ".memory" / "last_critique.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _diff_hashes(current: Dict[str, str], previous: Dict[str, str],
                 threshold: int, current_covers_all: bool = True) -> Dict[str, Any]:
    """Count nodes whose body_hash differs between `current` and `previous`.

    `current_covers_all` is the universe contract:
      - True (live --drift): both sides fingerprint EVERY bodied node, so the diff
        universe is the union — an added/removed node is real drift.
      - False (--vs-validated): `current` covers only the VALIDATED subset; a node
        in `previous` but absent from `current` carries no validate-time signal, so
        it must NOT count as changed. The universe is `current` only."""
    ids = set(current) | set(previous) if current_covers_all else set(current)
    changed = sorted(i for i in ids if current.get(i) != previous.get(i))
    return {
        "changed_count": len(changed),
        "changed_ids": changed,
        "threshold": threshold,
        "over": len(changed) >= threshold,
    }


def write_snapshot(root: Path, scope: str) -> Dict[str, Any]:
    spec_graph, _ad, _jc, _pref, fs_guard = _import_psp()
    body_hash = _live_body_hashes(spec_graph, root)
    marker = {"critiqued_at": _now(), "scope": scope, "body_hash": body_hash}

    path = root / "docs" / "product" / ".memory" / "last_critique.json"
    resolved = fs_guard.assert_under_docs_product(path, root)  # raises FenceError out-of-tree
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="") as fh:
        json.dump(marker, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return {"snapshot_written": str(resolved), "node_count": len(body_hash), "scope": scope}


def compute_drift(root: Path, vs_validated: bool, threshold: int) -> Dict[str, Any]:
    spec_graph, _ad, judgment_cache, _pref, _fs = _import_psp()

    marker = _load_marker(root)
    if marker is None:
        # No baseline critique yet — never "over"; the skill suggests a first run.
        return {"changed_count": 0, "changed_ids": [], "threshold": threshold,
                "over": False, "first_run": True}
    previous = marker.get("body_hash") if isinstance(marker.get("body_hash"), dict) else {}

    current: Optional[Dict[str, str]] = None
    source = "live"
    if vs_validated:
        current = _validated_body_hashes(judgment_cache, root)
        source = "validated"
    if current is None:  # --vs-validated with no cache, or plain --drift
        current = _live_body_hashes(spec_graph, root)
        source = "live"

    result = _diff_hashes(current, previous, threshold,
                          current_covers_all=(source == "live"))
    result["source"] = source
    return result
