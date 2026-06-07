"""lens_session_shape.py — coarse shape of recorded sessions from sessions.jsonl:
count, avg/median duration, total files modified, total subagents, and skill
co-occurrence (which skills tend to run together in one session).

Pure gather → render-agnostic dict. READ-ONLY, fail-soft. CM-local (NOT shipped).
"""
from __future__ import annotations

import json
from collections import defaultdict
from itertools import combinations

import telemetry_paths
from catalog import load_catalog, to_dir_id


def _sessions_path():
    return telemetry_paths.TELEMETRY / "sessions.jsonl"


def _median(xs: list[int]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return float(s[mid]) if n % 2 else (s[mid - 1] + s[mid]) / 2


def gather(skills_dir=None) -> dict:
    catalog = load_catalog(skills_dir)
    p = _sessions_path()
    durations: list[int] = []
    files_total = 0
    subagents_total = 0
    cooccur: dict[str, int] = defaultdict(int)
    count = 0
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            count += 1
            durations.append(int(rec.get("duration_s", 0) or 0))
            files_total += int(rec.get("files_modified", 0) or 0)
            subagents_total += int(rec.get("subagents", 0) or 0)
            skills = sorted({to_dir_id(s, catalog) for s in (rec.get("skills") or []) if s})
            for a, b in combinations(skills, 2):
                cooccur[f"{a} + {b}"] += 1
    avg = round(sum(durations) / count) if count else 0
    top_cooccur = sorted(cooccur.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    return {
        "lens": "session_shape",
        "sessions": count,
        "avg_duration_s": avg,
        "median_duration_s": _median(durations),
        "files_modified_total": files_total,
        "subagents_total": subagents_total,
        "top_cooccurrence": top_cooccur,
        "gated": telemetry_paths.low_volume_gate(count),
    }
