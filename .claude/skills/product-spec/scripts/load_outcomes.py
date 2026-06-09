#!/usr/bin/env python3
"""
load_outcomes — join the Outcome Register (`outcomes.md`) with the BRD goals into
the shape the outcome viz views (scorecard / insight-gap / outcome-trend /
learning-map) consume. Pure read-only assembly — no I/O beyond reading the two
registers, no rendering. Shared by Phase-4 viz and Phase-5 learning-map (DRY).

Card model (one per measured goal+metric pair, plus one blind-spot card per goal
with NO outcomes):
  goal_id, metric, title, status   — goal identity (title/status from brd.md)
  latest, prev, history            — outcomes for this pair, oldest→newest;
                                     `latest` = newest measured_on, max OUT id on a
                                     tie (red-team #5); `prev` = the one before it
  blind_spot                       — goal has no outcome at all (grey "unmeasured")
  orphan                           — outcome points at a goal no longer in brd.md
                                     (red-team #5b: render "goal removed", never crash)
  gap                              — normalized shortfall of `latest` (≥0; None if
                                     non-numeric/blind-spot), for insight-gap ordering
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from record_outcome import parse_outcomes
from outcome_verdict import OutcomeError, load_goals, _num

# hit is "better" than partial is "better" than miss — used for trend direction.
VERDICT_RANK = {"miss": 0, "partial": 1, "hit": 2}


def _out_num(out_id: str) -> int:
    """Integer suffix of an OUT-<n> id (for the same-date tiebreak)."""
    try:
        return int(str(out_id).split("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def compute_gap(outcome: Optional[Dict[str, Any]]) -> Optional[float]:
    """Normalized shortfall of one outcome, clamped ≥0 (red-team #6b):
      higher-is-better → max(0, (target-actual)/target)
      lower-is-better  → max(0, (actual-target)/target)
    A goal that EXCEEDS target → gap 0 (never negative, never tops the list).
    None when target/actual is non-numeric or target=0 (no deterministic gap)."""
    if not outcome:
        return None
    t, a = _num(outcome.get("target")), _num(outcome.get("actual"))
    if t is None or a is None or t == 0:
        return None
    direction = str(outcome.get("direction") or "higher")
    raw = (a - t) / t if direction == "lower" else (t - a) / t
    return max(0.0, raw)


def load_outcomes(root) -> Dict[str, Any]:
    """Return {"cards": [...], "periods": [sorted measured_on]} — see module docstring."""
    outcomes = parse_outcomes(root)
    try:
        goals = load_goals(root)
    except OutcomeError:
        # A missing/broken brd.md → no goal metadata; still render outcomes (orphan
        # cards). Narrowed to OutcomeError (the only thing load_goals raises) so a
        # genuine programming error surfaces instead of being swallowed.
        goals = {}

    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for o in outcomes:
        groups[(str(o.get("goal")), str(o.get("metric")))].append(o)
    for key in groups:
        # oldest → newest; same measured_on → larger OUT id wins the "latest" slot.
        groups[key].sort(key=lambda o: (str(o.get("measured_on") or ""), _out_num(o["id"])))

    cards: List[Dict[str, Any]] = []
    measured_goals = set()
    for (gid, metric), hist in groups.items():
        latest = hist[-1]
        goal = goals.get(gid)
        measured_goals.add(gid)
        cards.append({
            "goal_id": gid, "metric": metric,
            "title": goal.get("title") if goal else None,
            "status": goal.get("status") if goal else None,
            "latest": latest, "prev": hist[-2] if len(hist) >= 2 else None,
            "history": hist, "blind_spot": False, "orphan": goal is None,
            "gap": compute_gap(latest),
        })
    # Blind-spot card per goal with no measurement at all.
    for gid, goal in goals.items():
        if gid not in measured_goals:
            cards.append({
                "goal_id": gid, "metric": None, "title": goal.get("title"),
                "status": goal.get("status"), "latest": None, "prev": None,
                "history": [], "blind_spot": True, "orphan": False, "gap": None,
            })

    cards.sort(key=lambda c: (c["goal_id"], c["metric"] or ""))
    periods = sorted({str(o.get("measured_on") or "") for o in outcomes if o.get("measured_on")})
    return {"cards": cards, "periods": periods}
