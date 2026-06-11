"""lens_workflow_chains.py — actual per-session skill chains (from invocations.jsonl)
vs the chains DECLARED in data/skill-chains.yaml; ranks common chains + flags deviations.
Ported from human-analyzer's analyze-workflow-chains.py; framework-prefix logic
stripped — both sides normalize to flat dir slugs via catalog.py (D1).

The declared side reads an on-demand data file owned by this skill (not always-on
routing docs); it fails loud when that file is missing rather than silently reporting
zero declared chains.

Pure gather → render-agnostic dict. READ-ONLY. The actual-chains side is fail-soft on
telemetry invocation data; the declared side fails LOUD if its data file is missing or
malformed (a packaging/authoring bug, never silently zero chains). Ships in the bundle.
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

import telemetry_paths
from catalog import load_catalog, to_dir_id


def _declared_chains_path() -> Path:
    """On-demand source of declared skill→skill chains, owned by this skill
    (data/skill-chains.yaml) — never always-on context. Overridable via the
    CK_SKILL_CHAINS env var so tests can point at a fixture."""
    override = os.environ.get("CK_SKILL_CHAINS")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "data" / "skill-chains.yaml"


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
    path = _declared_chains_path()
    if not path.exists():
        raise FileNotFoundError(
            f"declared skill-chains data file missing: {path} — the workflow-chains lens "
            "needs it; restore .claude/skills/telemetry/data/skill-chains.yaml (it ships "
            "with the skill). A missing file here is a packaging bug, not zero chains."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("chains")
    if raw is None:  # `chains:` absent or explicitly null → deliberately no declared chains.
        return []
    if not isinstance(raw, list):
        raise ValueError(f"{path}: 'chains' must be a list, got {type(raw).__name__}")
    out = []
    for chain in raw:
        # Fail loud on a malformed entry rather than silently char-splitting a bare string
        # or coercing a null into a "None" skill — silent corruption is the LIB-5 class of bug.
        if not isinstance(chain, list):
            raise ValueError(f"{path}: each chain must be a list of skill ids, got {chain!r}")
        steps = []
        for s in chain:
            if not isinstance(s, str) or not s.strip():
                raise ValueError(f"{path}: chain step must be a non-empty string, got {s!r} in {chain!r}")
            steps.append(to_dir_id(s.strip().lstrip("/"), catalog))
        steps = [s for s in steps if s]  # drop ids not in the catalog (coverage, not corruption)
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
