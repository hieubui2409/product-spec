"""lens_usage_tokens.py — skill invocation counts + per-skill token attribution
+ never-used catalog. Ported from human-analyzer's scan-skill-usage-and-tokens.py
and adapted to cleanmatic's FLAT-slug identity (framework_of / to_dir_id dropped;
slug↔dir resolved via catalog.py — D1/D2).

Token attribution model (verbatim from the source, directional NOT billing-exact):
walk a session transcript chronologically; a Skill tool_use opens a span credited
to that skill; sum assistant `message.usage` (input+output) of that and following
assistant turns until the next Skill tool_use opens a new span.

Pure gather → returns a render-agnostic dict. READ-ONLY, fail-soft. Ships in the
release bundle.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import telemetry_paths
from catalog import load_catalog, to_dir_id


def _invocations_path():
    return telemetry_paths.TELEMETRY / "invocations.jsonl"


def gather_invocations(days: int, catalog: dict, now: datetime | None = None) -> dict:
    counts: dict[str, int] = defaultdict(int)
    by_day: dict[str, int] = defaultdict(int)
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    p = _invocations_path()
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            skill = to_dir_id(rec.get("skill", ""), catalog)
            if not skill:
                continue
            ts = telemetry_paths.parse_ts(rec.get("ts", ""))
            if ts and ts < cutoff:
                continue
            counts[skill] += 1
            if ts:
                by_day[ts.date().isoformat()] += 1
    return {"counts": dict(counts), "by_day": dict(sorted(by_day.items()))}


def gather_tokens(days: int, catalog: dict, now: datetime | None = None) -> dict[str, int]:
    """Per-skill token attribution across session transcripts within the window.
    Directional, not billing-exact (spans include inter-skill reasoning)."""
    sdir = telemetry_paths.sessions_dir()
    tokens: dict[str, int] = defaultdict(int)
    if not sdir.exists():
        return {}
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    for sf in sorted(sdir.glob("*.jsonl")):
        current: str | None = None
        try:
            fh = sf.open(encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = telemetry_paths.parse_ts(rec.get("timestamp", ""))
                if ts and ts < cutoff:
                    # Pre-window records are skipped wholesale, so a Skill span opened
                    # just before the cutoff under-attributes its in-window tail. Token
                    # weight is a directional metric and records are chronological →
                    # accepted as a small boundary effect, not corrected.
                    continue
                msg = rec.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill":
                            sk = (b.get("input") or {}).get("skill", "")
                            if sk:
                                current = to_dir_id(sk, catalog)
                usage = msg.get("usage")
                if current and isinstance(usage, dict):
                    tokens[current] += int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
    return dict(tokens)


def gather(days: int = 30, with_tokens: bool = True, skills_dir=None, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    catalog = load_catalog(skills_dir)
    inv = gather_invocations(days, catalog, now)
    counts = inv["counts"]
    cat_dirs = catalog["dirs"]
    owned = catalog.get("owned") or set()
    tokens = gather_tokens(days, catalog, now) if with_tokens else {}
    # never_used = OWNED skills not invoked (the actionable list). Unused vendored
    # external skills are expected, not prune candidates → counted separately, not
    # listed (M1: avoids an "85 chưa dùng" headline dominated by ck:* tools).
    never_used = sorted(s for s in owned if s not in counts)
    never_used_external_count = len([s for s in cat_dirs if s not in owned and s not in counts])
    rows = []
    for skill in cat_dirs | set(counts):
        rows.append({
            "skill": skill,
            "count": counts.get(skill, 0),
            "tokens": tokens.get(skill, 0),
            "owned": skill in owned,
        })
    rows.sort(key=lambda r: (-r["count"], -r["tokens"], r["skill"]))
    total = sum(counts.values())
    return {
        "lens": "usage_tokens",
        "days": days,
        "total_invocations": total,
        "skills_used": len([c for c in counts.values() if c]),
        "catalog_size": len(cat_dirs),
        "owned_size": len(owned),
        "never_used": never_used,                       # owned, actionable
        "never_used_external_count": never_used_external_count,  # informational
        "by_day": inv["by_day"],
        "with_tokens": with_tokens,
        "rows": rows,
        "gated": telemetry_paths.low_volume_gate(total),
    }
