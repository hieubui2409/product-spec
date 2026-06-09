#!/usr/bin/env python3
"""
record_outcome — the Outcome Register: the append-only home for measured outcomes
(`OUT-<n>`), the quantitative half of the `--learn` loop.

On every `--learn` measurement the PO declares target+actual for a BRD goal metric;
this script computes a deterministic 3-tier verdict (hit|partial|miss) and appends
one record block to `docs/product/outcomes.md`. The register NEVER touches the BRD
goal schema — an outcome is a measurement-in-time, the goal is the definition; they
stay decoupled (DRY).

SCRIPT-vs-LLM split (CLAUDE.md): this script owns the deterministic structural work —
compute the numeric verdict (direction-aware ratio vs configurable floors), allocate
the next monotonic id, validate the goal/metric refs, append WITHOUT overwriting prior
records. The LLM/PO owns the free-text `note` and — for a non-numeric metric — the
asserted `--verdict` (the Hybrid B3 path, deliberately outside the deterministic gate).

Storage mirrors the Decision Register: each outcome is one `---`-fenced YAML block
(id/goal/metric/target/actual/unit/direction/measured_on/source/verdict) + a
`## OUT-<n>` heading + the note. Append is text-concat (prior records byte-unchanged),
written through the shared soft fence (`fs_guard`) so it can never escape docs/product/.

Verdict math (3-tier, matches the brainstorm OQ#3 / red-team #2):
  higher-is-better → ratio = actual / target
  lower-is-better  → ratio = target / actual   (actual=0 → best → hit)
  ratio ≥ hit_floor → hit · partial_floor ≤ ratio < hit_floor → partial · else miss
Floors default 0.9 / 0.5, overridable via preferences.py
(`outcome_hit_floor` / `outcome_partial_floor`). A bad floor pair (partial ≥ hit, or
outside [0,1]) is rejected with a non-zero exit — never a silent wrong verdict.

CLI:
    record_outcome.py --root <dir> --alloc-id
    record_outcome.py --root <dir> --append-alloc --goal BRD-G1 --metric gmv-year1 \\
        --target 2000000 --actual 1450000 [--unit USD] [--direction higher] \\
        [--measured-on 2026-05-31] [--source "..."] [--verdict miss] [--note "..."] [--force]
    record_outcome.py --root <dir> --list
"""

import argparse
import contextlib
import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from encoding_utils import configure_utf8_console
from fs_guard import assert_under_docs_product
# Shared append-only fenced-record machinery (also used by decision_register): the
# block-splitter regex, injection escape, file lock, and raw id scan live in ONE home.
from register_store import RECORD_RE as _RECORD_RE, escape_injection, register_lock, scan_record_ids
# The deterministic verdict CORE lives in outcome_verdict (pure, no I/O); re-export
# the names here so callers/tests importing them from record_outcome keep working.
from outcome_verdict import (  # noqa: F401  (re-export)
    OutcomeError, VERDICTS, DIRECTIONS, _num, compute_verdict, load_floors, load_goals,
)

configure_utf8_console()

OUTCOME_ID_RE = re.compile(r"^OUT-\d+$")
# The register's own heading anchor (a note line `## OUT-<n>` would smuggle a phantom
# heading); passed to the shared escape_injection on write.
_INJ_HEADING_RE = re.compile(r"(?m)^(##\s+OUT-)")

TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "templates" / "outcomes.md"
)


def _outcomes_path(root) -> Path:
    return Path(root) / "docs" / "product" / "outcomes.md"


def _lock_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".outcome_register.lock"


def parse_outcomes(root) -> List[Dict[str, Any]]:
    """Every outcome record in file order. A corrupt/malformed block is skipped
    (fail-soft), mirroring parse_decisions. `note` = the block body, trimmed."""
    try:
        text = _outcomes_path(root).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return []
    records: List[Dict[str, Any]] = []
    for m in _RECORD_RE.finditer(text):
        try:
            fm = yaml.safe_load(m.group("fm")) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict):
            continue
        out_id = str(fm.get("id", "")).strip()
        if not OUTCOME_ID_RE.match(out_id):
            continue
        rec = {k: fm.get(k) for k in (
            "goal", "metric", "target", "actual", "unit", "direction",
            "measured_on", "source", "verdict")}
        rec["id"] = out_id
        body = re.sub(rf"^##\s+{re.escape(out_id)}\b.*?$", "", m.group("body"),
                      count=1, flags=re.MULTILINE).strip()
        rec["note"] = body
        records.append(rec)
    return records


def alloc_id(root) -> str:
    """Next free OUT-<n> = max-existing + 1 (monotonic, never reused). Scans the raw
    `id:` lines of every block (shared scan_record_ids) so a corrupt-but-id-bearing
    block still reserves its number."""
    try:
        text = _outcomes_path(root).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        text = ""
    used = [int(m.group(1)) for rid in scan_record_ids(text)
            if (m := re.match(r"^OUT-(\d+)$", rid))]
    return f"OUT-{(max(used) + 1) if used else 1}"


def _yaml_scalar(value) -> str:
    """Render a frontmatter scalar: bare for numbers, double-quoted+escaped for text."""
    if _num(value) is not None and str(value).strip() != "":
        return str(value).strip()
    s = "" if value is None else str(value)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def _sanitize_note(note: str) -> str:
    """Break record-fence / OUT-heading injection in the PO note, preserving text
    (shared escape_injection, with this register's OUT-heading anchor)."""
    return escape_injection(note, _INJ_HEADING_RE)


def _render_record(rec: Dict[str, Any]) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    template = re.sub(r"\A\s*<!--.*?-->\s*\n", "", template, count=1, flags=re.DOTALL)
    values = {
        "id": rec["id"], "goal": rec["goal"], "metric": rec["metric"],
        "target": _yaml_scalar(rec["target"]), "actual": _yaml_scalar(rec["actual"]),
        "unit": _yaml_scalar(rec.get("unit", "")), "direction": rec["direction"],
        "measured_on": rec["measured_on"], "source": _yaml_scalar(rec.get("source", "")),
        "verdict": rec["verdict"], "note": _sanitize_note(rec.get("note", "")).strip(),
    }
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", str(val))
    return out.strip() + "\n"


def _atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)


def append_alloc(root, *, goal: str, metric: str, target, actual, unit: str,
                 direction: str, measured_on: str, source: str,
                 verdict: Optional[str], note: str, force: bool) -> Dict[str, Any]:
    """Validate refs, compute/honour the verdict, allocate the id, and append in ONE
    locked critical section. Returns a CLI-mirroring dict; raises OutcomeError on any
    grammar/ref/threshold/hybrid violation (nothing written)."""
    if direction not in DIRECTIONS:
        raise OutcomeError(f"--direction must be one of {DIRECTIONS}")
    # measured_on is a typed ISO 8601 date (frontmatter-and-id-spec). Enforce it here so
    # a typo can't silently sort/group wrong downstream (trend columns, latest tiebreak).
    try:
        dt.date.fromisoformat(str(measured_on))
    except (ValueError, TypeError):
        raise OutcomeError(
            f"--measured-on must be an ISO 8601 date (YYYY-MM-DD); got {measured_on!r}")

    goals = load_goals(root)
    if goal not in goals:
        raise OutcomeError(f"goal {goal!r} is not a BRD goal (have: {sorted(goals)})")
    warning = ""
    goal_metrics = [str(x) for x in (goals[goal].get("metrics") or [])]
    if metric not in goal_metrics:
        if not force:
            raise OutcomeError(
                f"metric {metric!r} is not in {goal}'s metrics {goal_metrics}; "
                f"fix the slug or pass --force to record anyway")
        warning = f"metric {metric!r} not in {goal}'s metrics {goal_metrics} (forced)"

    hit_floor, partial_floor = load_floors(root)
    t, a = _num(target), _num(actual)
    if t is None or t == 0 or a is None:  # Hybrid B3 → PO must assert the verdict
        if not verdict:
            raise OutcomeError(
                "non-numeric target/actual (or target=0): a PO-asserted --verdict "
                f"({'|'.join(VERDICTS)}) is required")
        final_verdict = verdict
    else:
        final_verdict = compute_verdict(direction, t, a, hit_floor, partial_floor)
    if final_verdict not in VERDICTS:
        raise OutcomeError(f"--verdict must be one of {VERDICTS}")

    with register_lock(_lock_path(root)):
        out_id = alloc_id(root)
        rec = {
            "id": out_id, "goal": goal, "metric": metric, "target": target,
            "actual": actual, "unit": unit, "direction": direction,
            "measured_on": measured_on, "source": source,
            "verdict": final_verdict, "note": note,
        }
        record = _render_record(rec)
        path = _outcomes_path(root)
        assert_under_docs_product(path, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            prior = path.read_text(encoding="utf-8")
            sep = "" if prior.endswith("\n\n") else ("\n" if prior.endswith("\n") else "\n\n")
            new_text = prior + sep + record
        else:
            new_text = "# Outcome Register\n\n" + record
        _atomic_write(path, new_text)

    result = {"id": out_id, "verdict": final_verdict,
              "path": str(path.relative_to(Path(root).resolve())), "written": True}
    if warning:
        result["warning"] = warning
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--alloc-id", action="store_true", help="print next free OUT-<n>")
    mode.add_argument("--append-alloc", action="store_true",
                      help="atomic: alloc id AND append one outcome record")
    mode.add_argument("--list", action="store_true", help="print outcomes as JSON")
    ap.add_argument("--goal"); ap.add_argument("--metric")
    ap.add_argument("--target"); ap.add_argument("--actual")
    ap.add_argument("--unit", default="")
    ap.add_argument("--direction", default="higher", choices=DIRECTIONS)
    ap.add_argument("--measured-on", default=dt.date.today().isoformat())
    ap.add_argument("--source", default="")
    ap.add_argument("--verdict", default=None, choices=[*VERDICTS, None])
    ap.add_argument("--note", default="")
    ap.add_argument("--force", action="store_true",
                    help="record even when --metric is not in the goal's metrics")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    try:
        if args.alloc_id:
            print(json.dumps({"id": alloc_id(root)}, ensure_ascii=False))
            return 0
        if args.list:
            print(json.dumps({"outcomes": parse_outcomes(root)}, indent=2,
                             ensure_ascii=False, default=str))
            return 0
        # --append-alloc
        for req in ("goal", "metric", "target", "actual"):
            if getattr(args, req) in (None, ""):
                raise OutcomeError(f"--{req} is required for --append-alloc")
        result = append_alloc(
            root, goal=args.goal, metric=args.metric, target=args.target,
            actual=args.actual, unit=args.unit, direction=args.direction,
            measured_on=args.measured_on, source=args.source,
            verdict=args.verdict, note=args.note, force=args.force,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except OutcomeError as exc:
        # Unlike the read-only analytical scripts (exit 0 + finding), a record-write
        # rejection exits NON-ZERO (mirrors preferences.save): a refused write must be
        # an unmistakable failure, not a quiet JSON note the caller might treat as ok.
        print(json.dumps({"error": "invalid_input", "message": str(exc),
                          "written": False}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
