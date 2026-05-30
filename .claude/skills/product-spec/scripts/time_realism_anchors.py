#!/usr/bin/env python3
"""
time_realism_anchors — SCRIPT half of the `time_realism` LLM check (TIME dimension).

`time_realism` is an LLM-judgment warn (Script-vs-LLM split: G-B2) — "this deadline
is unrealistic for this scope" is a sensory call no regex can make. But to stop the
LLM hallucinating ("phi thực tế" is the classic over-flag), the design (R2) pins the
LLM to STRUCTURED, SCRIPT-precomputed anchors and forbids it from doing any date math:

    {artifact_id, type, size, horizon, target_date, today_date,
     days_remaining, child_story_count, incomplete}

`days_remaining = (target_date - today).days` is computed HERE, not by the LLM. The
LLM only applies the fixed AND-rule against these numbers (see the scaffold in
references/validation-rules-spec.md → "time_realism LLM scaffold").

`today_date` comes from a pinnable `--today <ISO>` (default = real today). Evals/tests
PIN it so the anchor — and therefore the gate's reproducibility — is deterministic
(design F3 / goal G-D6). This is the SAME pinning contract as time_advisory.py.

This script emits ONLY anchors — it never decides flag/no-flag (that is the LLM's
judgment). An epic missing any anchor needed by the rule (no `target_date`, or no
`size`) is emitted with that field null and `eligible: false` so the LLM returns
`{finding: null, reason: "missing_anchor"}` without inventing data.

Scope: epics (the size+story-count unit the rule is defined on, design R2). A PRD has
no `size` and is not the realism unit, so it is skipped.

Pure data assembly — no LLM, no judgment, no wall-clock side effects beyond the
pinnable today. Always exits 0 (an advisory feeder, never a gate); a malformed
--today is the one user error worth a non-zero exit.

CLI:
    time_realism_anchors.py --root <project-dir> [--today YYYY-MM-DD]
        Prints {schema_version, root, today, checked_at, anchors:[...]} to stdout.
        Exits 0. (`checked_at` is wall-clock provenance, same envelope as the
        validate findings schema; the deterministic payload is `anchors`.)
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, matching_child_counts, _now
from check_consistency import _parse_iso_date

configure_utf8_console()


def build_anchors(graph: Dict[str, Any], today: dt.date) -> List[Dict[str, Any]]:
    """Assemble one anchor record per EPIC for the LLM `time_realism` check.

    `days_remaining` is computed here (target_date − today). When `target_date` or
    `size` is absent the anchor is still emitted (with that field null) but marked
    `eligible: false`, so the LLM returns `missing_anchor` instead of fabricating a
    date. Sorted by artifact_id → deterministic order for a pinned --today (G-A4)."""
    child_counts = matching_child_counts(graph)
    anchors: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        if n.get("type") != "epic":
            continue
        td = _parse_iso_date(n.get("target_date"))
        size = n.get("size")
        story_count = child_counts.get(n["id"], 0)
        days_remaining: Optional[int] = (td - today).days if td is not None else None
        # An epic is "incomplete" unless it is fully approved; informational context
        # for the LLM (an already-approved epic is unlikely to need a realism nudge).
        incomplete = n.get("status") != "approved"
        # The LLM rule needs BOTH a parseable target_date and a size; absent either,
        # it must return missing_anchor (never guess). child_story_count is always
        # known (a graph count), so it is not part of the eligibility gate.
        eligible = td is not None and size is not None
        anchors.append({
            "artifact_id": n.get("id"),
            "file": n.get("file"),
            "type": "epic",
            "size": size,
            "horizon": n.get("horizon"),
            "target_date": str(td) if td is not None else None,
            "today_date": str(today),
            "days_remaining": days_remaining,
            "child_story_count": story_count,
            "incomplete": incomplete,
            "eligible": eligible,
        })
    anchors.sort(key=lambda a: str(a.get("artifact_id")))
    return anchors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument(
        "--today", default=None,
        help="ISO date (YYYY-MM-DD) to compute days_remaining against; default = "
             "real today. Tests/evals PIN this so the anchor is reproducible.",
    )
    args = ap.parse_args()

    today = _parse_iso_date(args.today) if args.today else dt.date.today()
    if today is None:
        print(f"--today must be an ISO date (YYYY-MM-DD); got {args.today!r}.",
              file=sys.stderr)
        return 1

    root = Path(args.root).resolve()
    graph = build_graph(root)
    anchors = build_anchors(graph, today)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "today": str(today),
        "checked_at": _now(),
        "anchors": anchors,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
