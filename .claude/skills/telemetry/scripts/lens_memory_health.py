"""lens_memory_health.py — validates THIS repo's persistent memory dir
(memory_dir() → ~/.claude/projects/<root>/memory/): per-file frontmatter,
MEMORY.md index sync (orphan files / dead index entries), [[name]] cross-link
resolution, type validity, and staleness. Ported from human-analyzer's
check-memory-system-health.py.

READ-ONLY by skill boundary (D / Phase-4): NO --apply, NO disk writes — memory
writes belong to the product-spec memory flow, not this usage-&-health lens. A
dry-run `fix_preview` lists the dead index lines a repair WOULD drop, nothing
more. stdlib-only frontmatter parser (no pyyaml dependency). Ships in the release bundle.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import telemetry_paths

REQUIRED_FIELDS = ("name", "description")
VALID_TYPES = {"user", "feedback", "project", "reference"}
STALE_DAYS = 30
PROJECT_STALE_DAYS = 14
LINK_RE = re.compile(r"\[\[([a-z0-9][a-z0-9-]*)\]\]")
INDEX_LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")


def _memory_dir() -> Path:
    return telemetry_paths.memory_dir()


def _extract_frontmatter(path: Path) -> dict:
    """Minimal `---` frontmatter parser for the memory shape: top-level
    key: value plus a one-level `metadata:` block. Fail-soft → {} on any issue."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    fm: dict = {}
    parent = None
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        key, val = k.strip(), v.strip()
        if indent == 0:
            if val == "":
                fm[key] = {}
                parent = key
            else:
                fm[key] = val
                parent = None
        elif parent and isinstance(fm.get(parent), dict):
            fm[parent][key] = val
    return fm


def _age_days(p: Path) -> int:
    try:
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - mtime).days
    except OSError:
        return 0


def scan_memories(mem_dir: Path) -> list[dict]:
    out: list[dict] = []
    if not mem_dir.exists():
        return out
    for f in sorted(mem_dir.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        fm = _extract_frontmatter(f)
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            text = ""
        missing = [k for k in REQUIRED_FIELDS if not fm.get(k)]
        meta = fm.get("metadata") or {}
        mtype = fm.get("type") or (meta.get("type") if isinstance(meta, dict) else None) or ""
        out.append({
            "file": f.name,
            "name": fm.get("name", ""),
            "type": mtype,
            "missing_fields": missing,
            "invalid_type": bool(mtype) and mtype not in VALID_TYPES,
            "age_days": _age_days(f),
            "links": sorted(set(LINK_RE.findall(text))),
        })
    return out


def parse_index(mem_dir: Path) -> list[str]:
    idx = mem_dir / "MEMORY.md"
    if not idx.exists():
        return []
    try:
        return INDEX_LINK_RE.findall(idx.read_text(encoding="utf-8"))
    except OSError:
        return []


def gather() -> dict:
    mem_dir = _memory_dir()
    mems = scan_memories(mem_dir)
    files = {m["file"] for m in mems}
    names = {m["name"] for m in mems if m["name"]}
    name_to_files: dict[str, list[str]] = {}
    for m in mems:
        if m["name"]:
            name_to_files.setdefault(m["name"], []).append(m["file"])

    indexed = parse_index(mem_dir)
    indexed_set = set(indexed)
    orphans = sorted(files - indexed_set)
    dead = [f for f in indexed if f not in files]
    duplicates = {n: fs for n, fs in name_to_files.items() if len(fs) > 1}

    broken_links = [{"from": m["file"], "to": link}
                    for m in mems for link in m["links"] if link not in names]

    stale = []
    for m in mems:
        limit = PROJECT_STALE_DAYS if m["type"] == "project" else STALE_DAYS
        if m["age_days"] > limit:
            stale.append({"file": m["file"], "type": m["type"], "age_days": m["age_days"]})

    type_dist: dict[str, int] = {}
    for m in mems:
        key = m["type"] or "(none)"
        type_dist[key] = type_dist.get(key, 0) + 1

    invalid_fm = [m for m in mems if m["missing_fields"] or m["invalid_type"]]
    issues = len(orphans) + len(dead) + len(broken_links) + len(duplicates) + len(invalid_fm)
    return {
        "lens": "memory_health",
        "memory_dir": str(mem_dir),
        "read_only": True,
        "count": len(mems),
        "orphans": orphans,
        "dead_entries": dead,
        "fix_preview": dead,  # dry-run only: lines a repair WOULD drop; never written
        "broken_links": broken_links,
        "duplicates": duplicates,
        "stale": stale,
        "invalid_frontmatter": [
            {"file": m["file"], "missing": m["missing_fields"], "invalid_type": m["invalid_type"]}
            for m in invalid_fm],
        "type_distribution": dict(sorted(type_dist.items())),
        "issue_count": issues,
        "status": "GREEN" if issues == 0 else ("YELLOW" if issues <= 3 else "RED"),
    }
