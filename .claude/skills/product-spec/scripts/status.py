#!/usr/bin/env python3
"""
status — the deterministic SCRIPT feeder for the read-only `--status` health nudge.

`--status` answers "where does my spec stand against the last time I validated it?"
without touching a single artifact. It is a PULL flow: the PO asks, the skill
reports. This module owns the structural facts; the LLM composes the human-facing
nudge from this JSON per `references/workflow-status.md`.

READ-ONLY — and specifically read-only over the memory layer. It READS the
`docs/product/.memory/last_validated.json` marker that the VALIDATE hub writes
(`judgment_cache.write_last_validated`); it never creates, mutates, or deletes it.
The `--validate`/`--status` timelines stay owned by their own flows.

What it reports (all deterministic — Script-vs-LLM split):
  - `baseline`     — was there a last-validated marker at all? With NO baseline the
                     feeder reports `baseline: false` ("no validation baseline yet")
                     and an EMPTY unvalidated set. A never-validated spec has no
                     comparison point — flagging every node would be a false alarm.
  - `unvalidated`  — node ids that changed since the baseline snapshot: per-field /
                     body changes (`spec_graph.changed_nodes`) UNION added/removed
                     ids (`spec_graph.diff_graphs`). This is the work the last
                     validate never saw.
  - `added`/`removed` — the set-diff halves, surfaced separately for the nudge.
  - `drafts`       — node ids whose `status` is `draft` (still in progress).
  - `stale_approvals` — APPROVED node ids that ALSO changed since the baseline:
                     they carry an approval the new wording was never validated
                     under (no-silent-reversal — surface, never re-flip).
  - `overdue`      — reuses `time_advisory.check_overdue` (shared date math, pinnable
                     `--today`); the calendar half of the nudge.

The snapshot delta degrades safely: a missing/corrupt marker, or a referenced
snapshot file that no longer exists, yields `baseline: false` with empty deltas —
never a crash, never an over-report.

CLI:
    status.py --root <project-dir> [--today YYYY-MM-DD]
        Prints {schema_version, root, baseline, checked_at, today, unvalidated,
        added, removed, drafts, stale_approvals, overdue} to stdout. Exits 0,
        EXCEPT on a malformed --today (the one input error, mirroring
        time_advisory) → exit 1. The nudge itself never gates.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, changed_nodes, diff_graphs, _now
from check_consistency import _parse_iso_date
from time_advisory import check_overdue
from judgment_cache import _last_validated_path

configure_utf8_console()


def _snapshots_dir(root: Path) -> Path:
    return root / "docs" / "product" / "visuals" / ".snapshots"


def _load_last_validated(root: Path) -> Optional[Dict[str, Any]]:
    """Return the parsed `last_validated.json` payload, or None when absent/corrupt.

    Read-only: this opens the marker the validate hub wrote and never touches it.
    A parse failure degrades to None (no baseline) — the same safe direction the
    judgment cache uses, since a never-validated spec and a corrupt marker both
    mean "no trustworthy comparison point"."""
    path = _last_validated_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("snapshot"), str):
        return None
    return data


def _load_baseline_snapshot(root: Path, marker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load the snapshot graph the marker points at, or None when that file is
    gone / unreadable. The marker records a filename under `.snapshots/`; we read
    it back to diff the CURRENT graph against the validated one."""
    name = marker.get("snapshot")
    if not isinstance(name, str) or not name:
        return None
    snap_path = _snapshots_dir(root) / name
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return snap if isinstance(snap, dict) else None


def _drafts(graph: Dict[str, Any]) -> List[str]:
    """Node ids still in `status: draft` — work not yet carried to approval."""
    return sorted(n["id"] for n in graph.get("nodes", []) if n.get("status") == "draft")


def _approved_ids(graph: Dict[str, Any]) -> set:
    return {n["id"] for n in graph.get("nodes", []) if n.get("status") == "approved"}


def build_status(root, today: Optional[str] = None) -> Dict[str, Any]:
    """Compose the deterministic status facts for `root`.

    `today` (ISO) pins the overdue date math for reproducibility; default = real
    today. Raises ValueError on a malformed `today` so the CLI can surface the one
    input error as a non-zero exit (the nudge itself never gates)."""
    root = Path(root).resolve()

    if today is not None:
        eval_today = _parse_iso_date(today)
        if eval_today is None:
            raise ValueError(f"--today must be an ISO date (YYYY-MM-DD); got {today!r}.")
    else:
        eval_today = dt.date.today()

    graph = build_graph(root)

    drafts = _drafts(graph)
    overdue = check_overdue(graph, eval_today)

    marker = _load_last_validated(root)
    baseline_snapshot = _load_baseline_snapshot(root, marker) if marker else None

    if baseline_snapshot is None:
        # No trustworthy baseline → degrade. We do NOT mark every node unvalidated;
        # a never-validated (or marker-lost) spec has nothing to compare against.
        return {
            "schema_version": "1.0",
            "root": str(root),
            "baseline": False,
            "checked_at": _now(),
            "today": str(eval_today),
            "unvalidated": [],
            "added": [],
            "removed": [],
            "drafts": drafts,
            "stale_approvals": [],
            "overdue": overdue,
        }

    diff = diff_graphs(graph, baseline_snapshot)
    added = diff["added"]
    removed = diff["removed"]
    # Unvalidated = field/body changes on surviving nodes UNION added/removed ids.
    # `changed_nodes` only looks at ids present in BOTH snapshots, so the set-diff
    # halves (added/removed) must be folded in to catch new and deleted work.
    field_changed = changed_nodes(graph, baseline_snapshot)
    unvalidated = sorted(set(field_changed) | set(added) | set(removed))

    # A stale approval is an approved artifact that changed since the baseline:
    # the approval predates the new wording. Surface it (the PO decides) — never
    # silently re-flip an approved decision.
    approved = _approved_ids(graph)
    stale_approvals = sorted(approved & set(unvalidated))

    return {
        "schema_version": "1.0",
        "root": str(root),
        "baseline": True,
        "checked_at": _now(),
        "today": str(eval_today),
        "unvalidated": unvalidated,
        "added": added,
        "removed": removed,
        "drafts": drafts,
        "stale_approvals": stale_approvals,
        "overdue": overdue,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument(
        "--today", default=None,
        help="ISO date (YYYY-MM-DD) for the overdue date math; default = real "
             "today. Tests/evals PIN this so the report is reproducible.",
    )
    # --lang accepted for CLI-contract uniformity; this is a lang-agnostic JSON
    # feeder (English keys), so it is ignored (the LLM localizes the nudge prose).
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    args = ap.parse_args()

    try:
        report = build_status(args.root, today=args.today)
    except ValueError as exc:
        # A malformed --today is the only user error worth a non-zero exit (mirrors
        # time_advisory); the nudge itself never blocks.
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
