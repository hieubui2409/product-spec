#!/usr/bin/env python3
"""
outcome_verdict — the deterministic verdict CORE of the `--learn` outcome loop.

Pure computation + the BRD-goal facts the verdict needs — NO register I/O. Split out
of `record_outcome.py` (which owns the OUT-<n> block storage + CLI) so the math is
independently testable and reusable by `load_outcomes` (gap calc) WITHOUT importing
the writer. `record_outcome` re-exports these names, so callers/tests importing them
from `record_outcome` keep working.

Verdict math (3-tier, direction-aware):
  higher-is-better → ratio = actual / target
  lower-is-better  → ratio = target / actual   (actual=0 → best → hit)
  ratio ≥ hit_floor → hit · partial_floor ≤ ratio < hit_floor → partial · else miss
Floors default 0.9 / 0.5, overridable via preferences.py; a bad pair (partial ≥ hit,
outside [0,1]) is a hard OutcomeError.
"""

import math
from pathlib import Path
from typing import Any, Dict, Optional

import preferences
from frontmatter_parser import parse_file

VERDICTS = ("hit", "partial", "miss")
DIRECTIONS = ("higher", "lower")


class OutcomeError(ValueError):
    """Raised on a grammar/ref/shape/threshold violation (CLI → non-zero exit)."""


def _num(value) -> Optional[float]:
    """float(value) if it parses as a FINITE number, else None (empty/None → None).

    Non-finite tokens (`inf`, `-inf`, `nan`) are rejected → None, so they route to the
    Hybrid path (PO-asserted verdict) instead of silently producing an inf/nan ratio."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    try:
        n = float(s)
    except ValueError:
        return None
    return n if math.isfinite(n) else None


def compute_verdict(direction: str, target: float, actual: float,
                    hit_floor: float, partial_floor: float) -> str:
    """Deterministic 3-tier verdict. Caller guarantees target != 0 and both numeric;
    `lower` with actual=0 is the best possible (no div-by-zero) → hit."""
    if direction == "lower":
        ratio = float("inf") if actual == 0 else target / actual
    else:
        ratio = actual / target
    if ratio >= hit_floor:
        return "hit"
    if ratio >= partial_floor:
        return "partial"
    return "miss"


def load_floors(root) -> tuple:
    """Resolve verdict floors from preferences (defaults 0.9/0.5). A non-numeric or
    out-of-order pair (partial ≥ hit, or outside [0,1]) is a hard error."""
    prefs = preferences.load(root)
    try:
        hit = float(prefs.get("outcome_hit_floor", 0.9))
        partial = float(prefs.get("outcome_partial_floor", 0.5))
    except (TypeError, ValueError):
        raise OutcomeError("outcome verdict floors in preferences are not numbers")
    if not (0 <= partial < hit <= 1):
        raise OutcomeError(
            f"invalid verdict floors: need 0 ≤ partial_floor ({partial}) "
            f"< hit_floor ({hit}) ≤ 1"
        )
    return hit, partial


def load_goals(root) -> Dict[str, Dict[str, Any]]:
    """Map BRD goal id → goal dict (id/metrics/...) from brd.md frontmatter."""
    parsed = parse_file(Path(root) / "docs" / "product" / "brd.md")
    if not parsed.get("ok"):
        raise OutcomeError(f"cannot read brd.md goals: {parsed.get('error')}")
    goals = (parsed["frontmatter"] or {}).get("goals") or []
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(goals, list):
        for g in goals:
            if isinstance(g, dict) and g.get("id"):
                out[str(g["id"]).strip()] = g
    return out
