"""lens_product_memory.py — health of the PRODUCT-SPEC memory store at
`docs/product/.memory/` (the PO's spec-state layer), as distinct from the
`memory` lens which validates the assistant's own kebab-md memory dir.

Narrates what a PO cares about: is the store present, how stale is the last
validation baseline, how big is the critique-lens cache, and which expected
state files are missing. READ-ONLY (usage-&-health boundary): NO disk writes.
stdlib-only; ships in the release bundle.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import telemetry_paths

# Expected top-level state files the product-spec memory flow maintains. A
# missing one is surfaced (not fatal): a fresh spec simply has not produced it.
EXPECTED_FILES = (
    "last_validated.json",
    "preferences.yaml",
    "critique-state.json",
    "critique-findings-index.json",
)
STALE_DAYS = 30  # last-validated baseline older than this → a YELLOW/RED signal


def _product_memory_dir(root: str | None) -> Path:
    base = Path(root) if root else Path(telemetry_paths.project_dir())
    return base / "docs" / "product" / ".memory"


def _age_days(p: Path) -> int | None:
    try:
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - mtime).days
    except OSError:
        return None


def _findings_count(p: Path) -> int:
    """Number of indexed critique findings. The live index is
    `{"entries": {<id>: {...}}, "version": ...}`; an older shape used a top-level
    `findings` list/dict. Count the recognized container; fail-soft → 0 on any
    parse issue or unknown shape (never the misleading top-level-key count)."""
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("entries", "findings"):
            container = data.get(key)
            if isinstance(container, (list, dict)):
                return len(container)
    return 0


def gather(root: str | None = None) -> dict:
    base = _product_memory_dir(root)
    present = base.is_dir()

    missing = sorted(n for n in EXPECTED_FILES if not (base / n).is_file()) if present else list(EXPECTED_FILES)

    lv = base / "last_validated.json"
    last_validated_age_days = _age_days(lv) if lv.is_file() else None
    stale = last_validated_age_days is not None and last_validated_age_days > STALE_DAYS

    cache_dir = base / "critique-lens-cache"
    cache_files = sorted(cache_dir.glob("*.json")) if cache_dir.is_dir() else []
    cache_bytes = 0
    for f in cache_files:
        try:
            cache_bytes += f.stat().st_size
        except OSError:
            pass

    findings_count = _findings_count(base / "critique-findings-index.json")

    # Issue tally (hard counts only): absent store, each missing file, stale baseline.
    issues = (0 if present else 1) + len(missing) + (1 if stale else 0)
    status = "GREEN" if issues == 0 else ("YELLOW" if issues <= 2 else "RED")

    return {
        "lens": "product_memory",
        "memory_dir": str(base),
        "read_only": True,
        "present": present,
        "missing_files": missing,
        "last_validated_age_days": last_validated_age_days,  # None = never validated
        "stale_baseline": stale,
        "cache_count": len(cache_files),
        "cache_bytes": cache_bytes,
        "findings_count": findings_count,
        "issue_count": issues,
        "status": status,
    }
