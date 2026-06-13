"""harvester.py — read-only suggestion harvester for the telemetry feedback loop.

Reads two sources:
  1. Self-corrections: docs/product/.memory/self-corrections.json (PO corrections to
     LLM assumptions — category/artifact/description).
  2. Repeat-findings: artifact-events.jsonl (P6 sink) — tallies repeated edits per
     artifact as a signal of churn/instability.

Returns a dict {"suggestions": [...]} where each suggestion has:
  - category: str  — correction category or "repeat_edits"
  - artifact: str  — path of the artifact in question
  - count: int     — number of times the issue appeared
  - why: str       — human-readable reason text

BOUNDARY A9 (non-negotiable):
  This module NEVER opens any file for writing. It is READ-ONLY by construction.
  No write to skill/template/SKILL.md. The function opens files only in read mode
  and returns a plain dict — the caller (PO-reviewed export) handles any output.

Ships in the release bundle. Zero third-party deps (stdlib only).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Default path for self-corrections — overridable by callers (tests inject tmp paths).
_DEFAULT_CORRECTIONS = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent  # up to project root
    / "docs" / "product" / ".memory" / "self-corrections.json"
)

_DEFAULT_REPEAT_THRESHOLD = 3  # artifacts edited ≥ this many times are "hot"


def _load_self_corrections(corrections_path: Path) -> list[dict]:
    """Read self-corrections JSON. Returns [] if file absent or malformed. Read-only."""
    if not corrections_path.exists():
        return []
    try:
        with open(str(corrections_path), encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _load_artifact_events(telemetry_path: Path, days: int, now: datetime | None = None) -> list[dict]:
    """Read artifact-events.jsonl within the days window. Returns []. Read-only."""
    if not telemetry_path.exists():
        return []
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    records = []
    try:
        with open(str(telemetry_path), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Filter by time window
                ts_raw = rec.get("ts", "")
                try:
                    ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    ts = None
                if ts and ts < cutoff:
                    continue
                records.append(rec)
    except OSError:
        pass
    return records


def harvest_suggestions(
    days: int = 30,
    corrections_path: Path | None = None,
    repeat_threshold: int = _DEFAULT_REPEAT_THRESHOLD,
    now: datetime | None = None,
) -> dict:
    """Gather read-only suggestions from self-corrections + repeat artifact edits.

    Parameters
    ----------
    days:
        Look-back window in days for artifact-events. Default 30.
    corrections_path:
        Path to self-corrections.json. Defaults to the in-repo standard path.
        Pass a tmp path in tests.
    repeat_threshold:
        Artifacts edited >= this many times in the window are flagged as hot.
        Default 3.

    Returns
    -------
    {"suggestions": [
        {"category": str, "artifact": str, "count": int, "why": str},
        ...
    ]}

    BOUNDARY A9: this function is READ-ONLY. It never opens any file for writing,
    never writes to any skill/template/SKILL.md. It only returns data.
    """
    suggestions: list[dict] = []

    # --- Source 1: self-corrections (assumption corrections by the PO) -------
    if corrections_path is None:
        corrections_path = _DEFAULT_CORRECTIONS

    corrections = _load_self_corrections(corrections_path)

    # Tally corrections per (category, artifact)
    correction_counts: Counter = Counter()
    for rec in corrections:
        cat = rec.get("category") or "unknown"
        artifact = rec.get("artifact") or ""
        if artifact:
            correction_counts[(cat, artifact)] += 1

    for (cat, artifact), count in correction_counts.most_common():
        suggestions.append({
            "category": cat,
            "artifact": artifact,
            "count": count,
            "why": (
                f"PO corrected an LLM assumption {count} time(s) on this artifact "
                f"(category: {cat}). Consider reviewing the spec guidance for {cat}."
            ),
        })

    # --- Source 2: repeat artifact edits (from P6 artifact-events sink) ------
    import telemetry_paths  # noqa: E402 — stdlib-only module; imported lazily to stay fail-open
    events_path = telemetry_paths.TELEMETRY / "artifact-events.jsonl"
    events = _load_artifact_events(events_path, days=days, now=now)

    # Count edits per artifact
    edit_counts: defaultdict[str, int] = defaultdict(int)
    for rec in events:
        artifact = rec.get("artifact_path") or ""
        if artifact:
            edit_counts[artifact] += 1

    for artifact, count in sorted(edit_counts.items(), key=lambda x: -x[1]):
        if count >= repeat_threshold:
            suggestions.append({
                "category": "repeat_edits",
                "artifact": artifact,
                "count": count,
                "why": (
                    f"Artifact was edited {count} time(s) in the last {days} day(s). "
                    f"High churn may indicate instability or frequent scope changes."
                ),
            })

    return {"suggestions": suggestions}
