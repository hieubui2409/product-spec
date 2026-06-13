"""lens_artifact_heat.py — artifact-edit frequency lens.

Reads artifact-events.jsonl (written by track_artifact_edits.py) and tallies
edits per artifact_path, returning a heat ranking (most-edited first).

Pure gather → render-agnostic dict. READ-ONLY, fail-soft. Ships in the release bundle.

Output shape:
  {
    "lens": "artifact_heat",
    "days": <int>,
    "total_edits": <int>,
    "rows": [
        {"artifact": <str>, "edits": <int>, "last_edit": <str ISO ts>},
        ...
    ]  # ordered by edits descending
  }
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import telemetry_paths

_SINK_NAME = "artifact-events.jsonl"


def _sink_path():
    return telemetry_paths.TELEMETRY / _SINK_NAME


def gather(days: int = 30, *, now: datetime | None = None) -> dict:
    """Tally artifact edits within the last ``days`` days.

    Returns a dict with lens="artifact_heat", total_edits, and rows sorted
    by edits descending. Skips malformed lines silently (fail-soft).

    ``now`` injects the reference clock (default: real UTC now) so the days
    window is deterministic and testable."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    counts: dict[str, int] = defaultdict(int)
    last_edit: dict[str, str] = {}

    p = _sink_path()
    total = 0
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = telemetry_paths.parse_ts(rec.get("ts", ""))
            if ts and ts < cutoff:
                continue
            artifact = rec.get("artifact_path") or ""
            if not artifact:
                continue
            counts[artifact] += 1
            total += 1
            # Track latest timestamp per artifact
            ts_str = rec.get("ts", "")
            if artifact not in last_edit or ts_str > last_edit[artifact]:
                last_edit[artifact] = ts_str

    rows = [
        {"artifact": art, "edits": cnt, "last_edit": last_edit.get(art, "")}
        for art, cnt in counts.items()
    ]
    rows.sort(key=lambda r: -r["edits"])

    return {
        "lens": "artifact_heat",
        "days": days,
        "total_edits": total,
        "rows": rows,
    }
