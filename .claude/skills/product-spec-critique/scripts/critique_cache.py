#!/usr/bin/env python3
"""critique_cache.py — the product-spec-critique cache facade + the JSON-dict stores.

Five committed stores live under `docs/product/.memory/` (the `.memory/` dir IS
committed in this repo per the locked folder-split decision; these markers follow
that convention — NOT gitignored runtime data. The web-cache holding scraped
third-party page text is an accepted trade-off the PO chose for `.memory/`
consistency, commit-all).

This module owns the three plain JSON-dict stores and RE-EXPORTS the two file-per-key
stores from `critique_blob_cache` so callers keep using
`critique_cache.get_lens_findings` / `put_cached` / etc.:

  * findings-index   (critique-findings-index.json) — evidence-ID query cache, LOSSY
       (blockers + DEC-worthy only). Feeds inherit + repeat-offense (here).
  * critique-state   (critique-state.json) — per-scope freshness/provenance marker (here).
  * humanized-cache  (humanized-cache.json) — reuse humanized output when unchanged (here).
  * web-cache        (web-cache/<url-hash>.json) — market URL fetch + TTL (critique_blob_cache).
  * lens-cache       (critique-lens-cache/<hash>.json) — FULL lens arrays, (critique_blob_cache).

NOT last_critique.json: that is the per-node body_hash SNAPSHOT (a distinct home,
owned by critique_drift.write_snapshot). `critique-state.json` is a per-scope INDEX
marker, not a body_hash map.

Shared IO (fenced write + tolerant read + memory-dir) lives in `critique_cache_io`.
"""

from typing import Any, Dict, List

from critique_cache_io import (  # noqa: F401 — facade re-export of the shared IO
    _fs_guard, _memory_dir, _now, _psp_dir, _read_json, _write_json,
)
from critique_blob_cache import (  # noqa: F401 — facade re-export of the blob stores
    _lens_findings_hash, _url_hash, get_cached, get_lens_findings, put_cached,
    put_lens_findings,
)


# ---------------------------------------------------------------------------
# findings-index — evidence-ID query cache (lossy: blockers + DEC-worthy)
# ---------------------------------------------------------------------------

def _index_path(root):
    return _memory_dir(root) / "critique-findings-index.json"


# `finding_fingerprint` (N1): stable per-finding anchor for dedup, computed at
# write time by critique_inherit. May be None (unresolvable/structural cited line)
# → readers fall back to the evidence_id key. Legacy rows lack it → `.get` → None.
_INDEX_FIELDS = ("severity", "why", "fix", "dec_worthy", "finding_fingerprint")


def load_index(root) -> Dict[str, Dict[str, Any]]:
    """The entries map (`<evidence_id>@<report_ts>` -> entry), `{}` on missing/corrupt."""
    data = _read_json(_index_path(root))
    if not isinstance(data, dict):
        return {}
    entries = data.get("entries")
    return entries if isinstance(entries, dict) else {}


def upsert_findings(root, report_ts: str, scope: str,
                    findings: List[Dict[str, Any]]):
    """Upsert each finding under the composite key `<evidence_id>@<report_ts>`.

    Last-write-wins per `(evidence_id, report_ts)`; distinct `report_ts` coexist. A
    finding with no `evidence_id` is skipped (nothing to key on)."""
    entries = load_index(root)
    for f in findings:
        eid = f.get("evidence_id")
        if not eid:
            continue
        entry = {"evidence_id": eid, "report_ts": report_ts, "scope": scope}
        for k in _INDEX_FIELDS:
            entry[k] = f.get(k)
        entries[f"{eid}@{report_ts}"] = entry
    return _write_json(root, _index_path(root), {"version": 1, "entries": entries})


# ---------------------------------------------------------------------------
# critique-state — per-scope freshness marker (provenance fast-path)
# ---------------------------------------------------------------------------

def _state_path(root):
    return _memory_dir(root) / "critique-state.json"


def load_state(root) -> Dict[str, Dict[str, Any]]:
    """The per-scope state map, `{}` on missing/corrupt."""
    data = _read_json(_state_path(root))
    return data if isinstance(data, dict) else {}


def save_state(root, scope: str, **fields: Any):
    """Merge `fields` into the record for `scope` (incremental update); other scopes
    untouched. Stores per-scope `{last_ts, provenance_hash, blocker_count,
    drift_since, ...}` — whichever the caller passes."""
    state = load_state(root)
    rec = state.get(scope)
    if not isinstance(rec, dict):
        rec = {}
    rec.update(fields)
    state[scope] = rec
    return _write_json(root, _state_path(root), state)


# ---------------------------------------------------------------------------
# humanized-output cache — reuse when consolidated markdown is unchanged
# ---------------------------------------------------------------------------

def _humanized_path(root):
    return _memory_dir(root) / "humanized-cache.json"


def get_humanized(root, consolidated_hash: str):
    data = _read_json(_humanized_path(root))
    if not isinstance(data, dict):
        return None
    val = data.get(consolidated_hash)
    return val if isinstance(val, str) else None


def put_humanized(root, consolidated_hash: str, text: str):
    data = _read_json(_humanized_path(root))
    if not isinstance(data, dict):
        data = {}
    data[consolidated_hash] = text
    return _write_json(root, _humanized_path(root), data)
