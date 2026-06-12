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
  - `unrecorded_signals` — the `memory_gap.collect` signals (what looks like it
                     should have been written to the memory layer but the persisted
                     markers say it wasn't). `memory_gap` is the SINGLE detection
                     home (Script-vs-LLM split); status only IMPORTS and reports it —
                     no second detector lives here. Degrades to `[]` when there is
                     nothing to flag (incl. an absent `.memory/`).
  - `open_questions` — PO-facing markers ("cần PO xác định"/"TBD"/"Vẫn còn mở")
                     riding inside artifacts that look done, via the single
                     `open_questions.scan` home. The `--approve` flow consults the same
                     detector per-file before sealing. `[]` when none.
  - `reflect_suggestion` — a soft, one-line advisory string pointing at `--reflect`,
                     present ONLY when drift-since-last-validate is high (the
                     existing `unvalidated` metric crosses `HIGH_DRIFT_THRESHOLD`);
                     `None` otherwise. Derived advisory text, never a gate.
  - `bundle_age`   — build-age facts read from the installed bundle MANIFEST
                     (`<root>/.claude/MANIFEST.json`): `{bundle_version, built_at,
                     age_days}`, or `None` when the MANIFEST is absent/unreadable.
                     `age_days` = days since the running copy was PACKED (not since
                     install) — the honest "is my copy stale?" signal, since a
                     freshly-installed but already-old release still reads as old.
                     The LLM turns this into an "ask the publisher for a newer
                     release" nudge. Fail-silent + no network: it is a soft hint.

The snapshot delta degrades safely: a missing/corrupt marker, or a referenced
snapshot file that no longer exists, yields `baseline: false` with empty deltas —
never a crash, never an over-report. `memory_gap.collect` is likewise advisory and
degrades on an absent `.memory/`, so wiring it in keeps `--status` read-only and
crash-free.

CLI:
    status.py --root <project-dir> [--today YYYY-MM-DD]
        Prints {schema_version, root, baseline, checked_at, today, unvalidated,
        added, removed, drafts, stale_approvals, overdue, unrecorded_signals,
        open_questions, reflect_suggestion, bundle_age} to stdout. Exits 0, EXCEPT
        on a malformed --today (the
        one input error, mirroring time_advisory) → exit 1. The nudge itself never
        gates.
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

# How many unvalidated (drifted-since-last-validate) nodes count as "high drift" —
# the point past which a retroactive `--reflect` harvest is worth suggesting. A soft
# line: below it the per-node `unvalidated` list already tells the story; at/above it
# the volume of un-harvested change is the signal. Advisory only, never a gate.
HIGH_DRIFT_THRESHOLD = 5


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


def _unrecorded_signals(root: Path) -> List[Dict[str, Any]]:
    """The memory-gap signals for `root`, via the single detection home.

    DRY: `memory_gap.collect` owns ALL "this looks unrecorded" detection (fence
    breach, no validate marker, approved-changed-no-DEC, judged-not-stored). Status
    only imports and surfaces it — it adds NO detection logic of its own. The import
    is function-local on purpose: `memory_gap` imports this module's marker/snapshot
    readers, so a module-level import here would be a cycle. Lazy import keeps both
    modules importable in any order and the read-only contract intact (`collect` is
    advisory and never writes)."""
    import memory_gap  # local: breaks the status<->memory_gap import cycle
    return memory_gap.collect(root)


def _open_questions(root: Path) -> List[Dict[str, Any]]:
    """Open-question markers across the spec, via the single detection home.

    DRY: `open_questions.scan` owns ALL "cần PO xác định"/"TBD"/"Vẫn còn mở" marker
    detection; status only surfaces it (the `--approve` flow consults the same module
    per-file). Local import keeps status cheap to import and adds no scan logic here."""
    import open_questions  # local: keep status import-light
    return open_questions.scan(root)


def _bundle_age(root: Path, eval_today: dt.date) -> Optional[Dict[str, Any]]:
    """Build-age beacon facts from the installed bundle MANIFEST, or None.

    The installer drops `<root>/.claude/MANIFEST.json` (bundle_version + built_at)
    into the PO's tree. Here we surface the *build age* — days since the running copy
    was packed — so the LLM can nudge "ask the publisher for a newer release" per
    `references/workflow-status.md`. Build-age (not install-age) is the honest
    staleness signal: it catches a freshly-installed but already-old release.

    Fail-silent by design: a missing MANIFEST (the dev tree, or a hand-copied spec),
    malformed JSON, a missing/non-string `built_at`, or an unparseable `built_at` all
    yield None — the beacon is a soft hint and must NEVER gate, raise, or touch the
    network. A `built_at` after `eval_today` (clock skew) clamps to 0 rather than
    reporting a negative age."""
    path = root / ".claude" / "MANIFEST.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    version = data.get("bundle_version")
    built_at = data.get("built_at")
    # Empty strings count as absent: a corrupt MANIFEST that carried a blank
    # version would otherwise render a half-formed "version  " nudge — the
    # fail-silent contract says degrade to None instead.
    if not isinstance(version, str) or not version:
        return None
    if not isinstance(built_at, str) or not built_at:
        return None
    try:
        built_date = dt.datetime.fromisoformat(built_at).date()
    except (ValueError, TypeError):
        return None
    age_days = max(0, (eval_today - built_date).days)
    return {"bundle_version": version, "built_at": built_at, "age_days": age_days}


def _reflect_suggestion(unvalidated: List[str]) -> Optional[str]:
    """A soft one-line `--reflect` hint when drift-since-last-validate is high.

    Keyed off the EXISTING `unvalidated` drift metric (no new measure) — at/above
    `HIGH_DRIFT_THRESHOLD` un-harvested nodes a retroactive harvest is worth a
    nudge. Returns None below the line. Advisory text only; the LLM may localize it
    per `references/workflow-status.md`."""
    if len(unvalidated) < HIGH_DRIFT_THRESHOLD:
        return None
    return (
        f"{len(unvalidated)} nodes have drifted since the last validate — consider "
        "--reflect to retroactively harvest any rulings/observations that were never "
        "recorded."
    )


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
        # memory_gap still has something to say here (a `validate_no_marker` gap),
        # and `unvalidated == []` means no high-drift reflect hint.
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
            "unrecorded_signals": _unrecorded_signals(root),
            "open_questions": _open_questions(root),
            "reflect_suggestion": _reflect_suggestion([]),
            "bundle_age": _bundle_age(root, eval_today),
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
        "unrecorded_signals": _unrecorded_signals(root),
        "open_questions": _open_questions(root),
        "reflect_suggestion": _reflect_suggestion(unvalidated),
        "bundle_age": _bundle_age(root, eval_today),
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
