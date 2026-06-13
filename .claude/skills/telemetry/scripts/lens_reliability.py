"""lens_reliability.py — subagent reliability from the Phase-2 SubagentStop sink
(subagent-outcomes.jsonl): per agent-type counts of success / api_error /
timeout / blocked / unknown, a success rate, and the top failure modes. Gated on
volume — thin data shows raw counts, no verdicts.

Pure gather → render-agnostic dict. READ-ONLY, fail-soft. Ships in the release bundle.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import telemetry_paths

_OUTCOMES = ("success", "api_error", "timeout", "blocked", "unknown")


def _path():
    return telemetry_paths.TELEMETRY / "subagent-outcomes.jsonl"


def gather(days: int = 30, *, now: datetime | None = None) -> dict:
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    by_type: dict[str, dict] = defaultdict(lambda: {k: 0 for k in _OUTCOMES} | {"total": 0})
    failure_modes: Counter = Counter()
    p = _path()
    total = 0
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = telemetry_paths.parse_ts(rec.get("ts", ""))
            if ts and ts < cutoff:
                continue
            atype = rec.get("agent_type") or "unknown"
            outcome = rec.get("outcome") or "unknown"
            if outcome not in _OUTCOMES:
                outcome = "unknown"
            agg = by_type[atype]
            agg["total"] += 1
            agg[outcome] += 1
            total += 1
            if outcome != "success":
                failure_modes[outcome] += 1
    rows = []
    for atype, a in sorted(by_type.items(), key=lambda kv: -kv[1]["total"]):
        rows.append({
            "agent_type": atype,
            **{k: a[k] for k in _OUTCOMES},
            "total": a["total"],
            "success_rate": round(100 * a["success"] / a["total"]) if a["total"] else 0,
        })
    return {
        "lens": "reliability",
        "days": days,
        "total": total,
        "rows": rows,
        "top_failure_modes": failure_modes.most_common(8),
        "gated": telemetry_paths.low_volume_gate(total),
    }
