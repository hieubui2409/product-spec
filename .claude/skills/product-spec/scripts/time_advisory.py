#!/usr/bin/env python3
"""
time_advisory — wall-clock TIME advisory, deliberately OUTSIDE the --validate gate.

`overdue` (target_date < today) consumes the wall clock, so it is NON-deterministic
by nature. Putting it inside the structural --validate gate would make that gate
non-reproducible (it would flip green→red just by the date changing). Instead it
ships as this standalone advisory: it takes a pinnable `--today <ISO>` (default =
real today) and emits an advisory JSON. It is NOT a gate — it ALWAYS exits 0, even
when items are overdue, so a CI pipeline never blocks on the calendar.

Pure date comparison — no LLM, no judgment (Script-vs-LLM split).

CLI:
    time_advisory.py --root <project-dir> [--today YYYY-MM-DD]
        Prints {schema_version, root, today, checked_at, findings:[overdue...]}
        to stdout. Always exits 0. (`checked_at` is wall-clock provenance, same
        envelope as the validate findings schema; reproducibility is over the
        pinned `--today`, which determines the `findings` payload.)
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, _now
from check_consistency import _parse_iso_date

configure_utf8_console()


def check_overdue(graph: Dict[str, Any], today: dt.date) -> List[Dict[str, Any]]:
    """Return one `overdue` advisory per artifact whose target_date is strictly
    before `today`. A node with no (or malformed) target_date is silently skipped
    — the field is optional and shape errors are the validate gate's job."""
    findings: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        td = _parse_iso_date(n.get("target_date"))
        if td is None:
            continue
        if td < today:
            findings.append({
                "check": "overdue",
                "severity": "advisory",
                "artifact_id": n.get("id"),
                "file": n.get("file"),
                "detail": (
                    f"{n.get('id')} target_date {td} is before today {today} "
                    f"(overdue by {(today - td).days} days)."
                ),
                "context": {
                    "target_date": str(td),
                    "today": str(today),
                    "days_overdue": (today - td).days,
                },
            })
    # Deterministic order for a given --today (stable across runs).
    findings.sort(key=lambda f: str(f.get("artifact_id")))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument(
        "--today", default=None,
        help="ISO date (YYYY-MM-DD) to evaluate against; default = real today. "
             "Tests/evals PIN this so the advisory is reproducible.",
    )
    args = ap.parse_args()

    today = _parse_iso_date(args.today) if args.today else dt.date.today()
    if today is None:
        # A malformed --today is the only user error worth a non-zero exit; the
        # advisory itself never blocks (overdue items still exit 0).
        print(f"--today must be an ISO date (YYYY-MM-DD); got {args.today!r}.",
              file=sys.stderr)
        return 1

    root = Path(args.root).resolve()
    graph = build_graph(root)
    findings = check_overdue(graph, today)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "today": str(today),
        "checked_at": _now(),
        "findings": findings,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
