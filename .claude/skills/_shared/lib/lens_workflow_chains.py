"""lens_workflow_chains.py — actual per-session skill chains (from invocations.jsonl)
vs the chains DECLARED in the routing docs; ranks common chains + flags deviations.
Ported from human-analyzer's analyze-workflow-chains.py; framework-prefix logic
stripped — both sides normalize to flat dir slugs via catalog.py (D1).

Pure gather → render-agnostic dict. READ-ONLY, fail-soft. Ships in the release bundle.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import telemetry_paths
from catalog import load_catalog, to_dir_id

# A declared chain in the routing docs: "/ck:plan → /ck:cook → /ck:test".
CHAIN_RE = re.compile(r"(/?[a-z]+:[a-z-]+(?:\s*→\s*/?[a-z]+:[a-z-]+)+)")


def _routing_docs() -> list[Path]:
    root = Path(telemetry_paths.project_dir()) / ".claude" / "rules"
    return [root / "skill-workflow-routing.md", root / "skill-domain-routing.md"]


def _invocations_path():
    return telemetry_paths.TELEMETRY / "invocations.jsonl"


def _parse_ts(raw: str):
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def actual_chains(days: int, catalog: dict) -> list[list[str]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    by_session: dict[str, list[tuple]] = defaultdict(list)
    p = _invocations_path()
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            skill = to_dir_id(rec.get("skill", ""), catalog)
            sess = rec.get("session", "")
            ts = _parse_ts(rec.get("ts", ""))
            if not skill or not sess or (ts and ts < cutoff):
                continue
            by_session[sess].append((ts or datetime.min.replace(tzinfo=timezone.utc), skill))
    chains = []
    for items in by_session.values():
        items.sort(key=lambda x: x[0])
        chains.append([s for _, s in items])
    return chains


def declared_chains(catalog: dict) -> list[list[str]]:
    out = []
    for doc in _routing_docs():
        if not doc.exists():
            continue
        for m in CHAIN_RE.findall(doc.read_text(encoding="utf-8")):
            steps = [to_dir_id(s.strip().lstrip("/"), catalog) for s in m.split("→")]
            steps = [s for s in steps if s]
            if len(steps) >= 2:
                out.append(steps)
    return out


def _norm(chain: list[str]) -> str:
    return " → ".join(chain)


def gather(days: int = 30, top: int = 10, min_sessions: int = 5, skills_dir=None) -> dict:
    catalog = load_catalog(skills_dir)
    actual = actual_chains(days, catalog)
    declared = declared_chains(catalog)
    declared_set = {_norm(c) for c in declared}
    chain_freq = Counter(_norm(c) for c in actual if c)
    common = chain_freq.most_common(top)
    deviations = sorted(
        ((c, n) for c, n in chain_freq.items() if " → " in c and c not in declared_set),
        key=lambda x: -x[1],
    )
    return {
        "lens": "workflow_chains",
        "days": days,
        "sessions_analyzed": len(actual),
        "sufficient": len(actual) >= min_sessions,
        "min_sessions": min_sessions,
        "common_chains": [{"chain": c, "count": n} for c, n in common],
        "declared_chains": [_norm(c) for c in declared],
        "deviations": [{"chain": c, "count": n} for c, n in deviations[:top]],
        "gated": telemetry_paths.low_volume_gate(len(actual), min_sessions),
    }
