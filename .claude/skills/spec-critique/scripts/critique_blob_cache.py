#!/usr/bin/env python3
"""critique_blob_cache.py — the two file-per-key spec-critique stores.

  * web-cache (web-cache/<url-hash>.json) — market-lens URL fetch cache + TTL.
  * lens-cache (critique-lens-cache/<lens_findings_hash>.json) — the FULL
    lens-findings array verbatim; the store that makes `consolidate_only` real
    (re-render voice at a new level WITHOUT re-running lenses). Distinct from the
    lossy findings-index: two caches, two keys, never conflated.

Split out of critique_cache. Shares the fenced-write / tolerant-read chokepoint via
critique_cache_io. Re-exported by critique_cache, so callers keep using
`critique_cache.get_lens_findings` etc."""

import hashlib
import json
from typing import Any, Dict, List, Optional

from critique_cache_io import _memory_dir, _now, _read_json, _write_json


# ---------------------------------------------------------------------------
# web-cache + TTL — market-lens URL fetch reuse
# ---------------------------------------------------------------------------

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _web_path(root, url: str):
    return _memory_dir(root) / "web-cache" / f"{_url_hash(url)}.json"


def get_cached(root, url: str, ttl_days: int = 14,
               now_iso: Optional[str] = None) -> Optional[str]:
    """The cached page content if present AND within `ttl_days`, else None.
    `now_iso` is injected so TTL expiry is pinnable in tests."""
    from datetime import datetime
    data = _read_json(_web_path(root, url))
    if not isinstance(data, dict):
        return None
    fetched_at = data.get("fetched_at")
    content = data.get("content")
    if not isinstance(fetched_at, str) or not isinstance(content, str):
        return None
    now = now_iso or _now()
    try:
        age = datetime.fromisoformat(now) - datetime.fromisoformat(fetched_at)
    except (TypeError, ValueError):
        return None
    if age.total_seconds() > ttl_days * 86400:
        return None
    return content


def put_cached(root, url: str, content: str, now_iso: Optional[str] = None):
    """Stamp `content` for `url` with `fetched_at = now_iso`."""
    payload = {"url": url, "content": content, "fetched_at": now_iso or _now()}
    return _write_json(root, _web_path(root, url), payload)


# ---------------------------------------------------------------------------
# lens-findings cache — FULL lens arrays; the consolidate_only store
# ---------------------------------------------------------------------------

def _lens_findings_hash(findings: List[Dict[str, Any]]) -> str:
    """sha256 of the canonical-JSON of the lens-findings array, first 16 hex. Stable
    for an identical array (sorted keys, no whitespace) so the same lens run keys to
    the same file."""
    canon = json.dumps(findings, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def _lens_path(root, lens_findings_hash: str):
    return _memory_dir(root) / "critique-lens-cache" / f"{lens_findings_hash}.json"


def get_lens_findings(root, lens_findings_hash: str) -> Optional[List[Dict[str, Any]]]:
    """The FULL lens-findings array stored under this hash, or None on
    missing/corrupt. Verbatim — no field dropped (NOT the lossy index subset)."""
    data = _read_json(_lens_path(root, lens_findings_hash))
    return data if isinstance(data, list) else None


def put_lens_findings(root, lens_findings_hash: str,
                      findings: List[Dict[str, Any]]):
    """Store the FULL lens-findings array verbatim under its hash."""
    return _write_json(root, _lens_path(root, lens_findings_hash), findings)
