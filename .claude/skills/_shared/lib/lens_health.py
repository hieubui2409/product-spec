"""lens_health.py — coarse script health from hook-telemetry.jsonl: per-script
run count, error count + rate (the COARSELY-inferred `exit`), and average
duration `ms` where the Pre/Post:Bash pairing recorded it.

Labelled "approx": `exit` is inferred (no reliable numeric code in the payload)
and `ms` is present only when both Bash hooks fired. Pure gather → dict.
READ-ONLY, fail-soft. Ships in the release bundle.
"""
from __future__ import annotations

import json
from collections import defaultdict

import telemetry_paths


def _health_path():
    return telemetry_paths.TELEMETRY / "hook-telemetry.jsonl"


def gather() -> dict:
    p = _health_path()
    runs: dict[str, int] = defaultdict(int)
    errors: dict[str, int] = defaultdict(int)
    ms_sum: dict[str, int] = defaultdict(int)
    ms_n: dict[str, int] = defaultdict(int)
    total = 0
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            script = rec.get("script")
            if not script:
                continue
            total += 1
            runs[script] += 1
            if int(rec.get("exit", 0) or 0) != 0:
                errors[script] += 1
            if "ms" in rec and isinstance(rec.get("ms"), (int, float)):
                ms_sum[script] += int(rec["ms"])
                ms_n[script] += 1
    rows = []
    for script in sorted(runs, key=lambda s: (-runs[s], s)):
        n = runs[script]
        err = errors.get(script, 0)
        avg_ms = round(ms_sum[script] / ms_n[script]) if ms_n.get(script) else None
        rows.append({
            "script": script,
            "runs": n,
            "errors": err,
            "error_rate": round(100 * err / n) if n else 0,
            "avg_ms": avg_ms,  # None when no Pre/Post pair recorded a duration
        })
    return {
        "lens": "health",
        "approx": True,
        "total_runs": total,
        "scripts": len(runs),
        "total_errors": sum(errors.values()),
        "rows": rows,
        "gated": telemetry_paths.low_volume_gate(total),
    }
