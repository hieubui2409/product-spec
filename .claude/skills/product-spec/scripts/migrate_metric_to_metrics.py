#!/usr/bin/env python3
"""
migrate_metric_to_metrics — rename a BRD goal's legacy singular `metric:` key to the
spec's plural `metrics:` (a list), preserving the value, and stamp `schema_version: 2`.

This is the GATE-safe companion to migrate_multidim_fields.py. It is a SEPARATE script on
purpose: migrate_multidim_fields only ever inserts EMPTY placeholders and NEVER writes an
`approved` file. The `metric:`→`metrics:` rename, by contrast, moves a real VALUE and must
run precisely on the `approved` legacy BRD that the bug afflicts — so it cannot live inside
that placeholder-only migrator without breaking its locked invariants.

Two-step, no-silent-reversal:
  - dry-run (DEFAULT, no --apply): report which goals carry `metric:`; write ZERO bytes and
    create NO `.bak`. The LLM drives the per-goal AskUserQuestion (Keep / Change / Hybrid)
    off this report.
  - --apply: writes ONLY when BOTH --confirmed-by AND --date are supplied — the explicit PO
    re-approval that authorizes editing an approved artifact. Missing either → refused, no
    write. On apply: rename the key (wrapping a bare scalar into a 1-item list), insert
    `schema_version: 2` if absent, and back the original up to `<file>.bak` first.

Scope: the BRD singleton (`docs/product/brd.md`) and its `goals:` block ONLY — a `metric:`
elsewhere (e.g. an outcomes record) is never touched. Analytical script: ALWAYS exits 0.

CLI:
    migrate_metric_to_metrics.py --root <project-dir>
        [--apply --confirmed-by <PO> --date <ISO>]
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from encoding_utils import configure_utf8_console
from frontmatter_parser import parse_file

configure_utf8_console()

# A `metric:` key line inside the goals block: leading indent, the key, then the rest.
_METRIC_LINE_RE = re.compile(r"^(?P<indent>\s+)metric:(?P<rest>.*)$")
# A `metrics:` (already-plural) key line — marks a goal entry that must NOT be renamed
# (touching its `metric:` too would emit a second `metrics:` key, i.e. invalid YAML).
_METRICS_PLURAL_RE = re.compile(r"^\s+metrics:")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _split_inline_comment(rest: str) -> Tuple[str, str]:
    """Split the text after `metric:` into (value, comment). A ` #` outside any quoted span
    starts a trailing comment; the returned comment keeps the whitespace that preceded it so
    value+comment rejoin losslessly. No comment → (rest, "")."""
    in_single = in_double = False
    for i, ch in enumerate(rest):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double and i > 0 and rest[i - 1] in " \t":
            j = i
            while j > 0 and rest[j - 1] in " \t":
                j -= 1
            return rest[:j], rest[j:]
    return rest, ""


def _rename_metric_value(rest: str) -> str:
    """Build the `metrics:` value text from the old `metric:` line's `rest` (everything
    after the colon). A flow list `[a, b]` and an empty value (block list follows) are kept
    as-is; a bare scalar is wrapped into a 1-item flow list. A trailing inline comment is
    carried verbatim AFTER the wrapped value so the rewritten line stays valid YAML."""
    value, comment = _split_inline_comment(rest)
    stripped = value.strip()
    if not stripped:
        # `metric:` with a block list on the following lines — rename the key only.
        return rest
    if stripped.startswith("["):
        # Already a flow list — preserve verbatim (including any trailing comment).
        return rest
    # A bare scalar value → wrap into a 1-item list, preserving leading space + comment.
    lead = value[: len(value) - len(value.lstrip(" "))] or " "
    return f"{lead}[{stripped}]{comment}"


def _goal_entry_ranges(lines, lo: int, hi: int):
    """Segment the goals child-region `[lo, hi)` into per-goal-entry `[start, end)` ranges,
    keyed off the indent of the first list item (`- `). A goal's nested block (e.g. a
    `metric:` block list, indented deeper than the item dash) stays inside its entry, so a
    goal's `metric:`/`metrics:` lines are never split across entries."""
    item_indent = None
    for i in range(lo, hi):
        s = lines[i].rstrip("\r\n").lstrip()
        if s.startswith("- ") or s == "-":
            item_indent = _indent(lines[i].rstrip("\r\n"))
            break
    if item_indent is None:
        return []
    entries = []
    cur = None
    for i in range(lo, hi):
        body = lines[i].rstrip("\r\n")
        if not body.strip():
            continue
        s = body.lstrip()
        if _indent(body) == item_indent and (s.startswith("- ") or s == "-"):
            cur = [i, i + 1]
            entries.append(cur)
        elif cur is not None:
            cur[1] = i + 1
    return [(a, b) for a, b in entries]


def _transform(text: str) -> Tuple[Optional[str], bool, bool]:
    """Rewrite `metric:`→`metrics:` inside the frontmatter goals block and ensure a
    `schema_version: 2` top-level marker. Returns (new_text, renamed_any, had_marker).
    new_text is None when the file has no parseable frontmatter fence (caller skips it).

    Rename is scoped per goal entry: an entry already carrying a plural `metrics:` key is
    left untouched, so a half-migrated goal can never gain a duplicate `metrics:` key."""
    had_bom = text.startswith("﻿")
    src = text[1:] if had_bom else text
    lines = src.splitlines(keepends=True)

    open_idx = next((i for i, ln in enumerate(lines) if ln.strip() == "---"), None)
    if open_idx is None:
        return None, False, False
    close_idx = next((i for i in range(open_idx + 1, len(lines))
                      if lines[i].strip() == "---"), None)
    if close_idx is None:
        return None, False, False

    newline = "\r\n" if lines[close_idx].endswith("\r\n") else "\n"

    # Pass 1 — locate the goals child-region and detect an existing schema_version marker.
    had_marker = False
    g_start = g_end = None
    in_goals = False
    for i in range(open_idx + 1, close_idx):
        body = lines[i].rstrip("\r\n")
        if not body.strip():
            continue
        top_level = not body[:1].isspace() and not body.lstrip().startswith("#")
        if not top_level:
            continue
        key = body.split(":", 1)[0].strip()
        if in_goals:                 # a new top-level key closes the goals block
            g_end = i
            in_goals = False
        if key == "schema_version":
            had_marker = True
        if key == "goals":
            in_goals = True
            g_start = i + 1
    if in_goals and g_end is None:   # goals ran to the closing fence
        g_end = close_idx

    # Pass 2 — rename `metric:`→`metrics:` per entry, skipping any entry already on plural.
    renamed_any = False
    if g_start is not None:
        for lo, hi in _goal_entry_ranges(lines, g_start, g_end):
            if any(_METRICS_PLURAL_RE.match(lines[j].rstrip("\r\n")) for j in range(lo, hi)):
                continue
            for j in range(lo, hi):
                m = _METRIC_LINE_RE.match(lines[j].rstrip("\r\n"))
                if m:
                    new_value = _rename_metric_value(m.group("rest"))
                    lines[j] = f"{m.group('indent')}metrics:{new_value}{newline}"
                    renamed_any = True

    if not renamed_any:
        # Nothing to migrate → return the ORIGINAL untouched (BOM intact), no marker write.
        return text, False, had_marker

    if not had_marker:
        lines.insert(close_idx, f"schema_version: 2{newline}")

    result = "".join(lines)
    return ("﻿" + result) if had_bom else result, True, had_marker


def plan_brd(root: Path) -> Optional[Dict[str, Any]]:
    """Inspect docs/product/brd.md for goals carrying the legacy `metric:` key. Returns a
    plan dict, or None when there is nothing to migrate (no BRD, unparseable, or already
    on the plural schema)."""
    brd = root / "docs" / "product" / "brd.md"
    if not brd.exists():
        return None
    parsed = parse_file(brd)
    if not parsed["ok"]:
        return None
    fm = parsed["frontmatter"] or {}
    goals = fm.get("goals")
    if not isinstance(goals, list):
        return None
    legacy_goal_ids = [
        g.get("id") for g in goals
        if isinstance(g, dict) and "metric" in g and "metrics" not in g
    ]
    if not legacy_goal_ids:
        return None
    return {
        "file": "brd.md",
        "id": fm.get("id"),
        "status": fm.get("status"),
        "goal_ids": legacy_goal_ids,
        "approved": fm.get("status") == "approved",
    }


def migrate(root: Path, apply: bool, confirmed_by: Optional[str],
            date: Optional[str]) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "root": str(root),
        "applied": False,
        "would_rename": [],
        "confirm_required": [],
        "migrated": [],
    }
    plan = plan_brd(root)
    if plan is None:
        return report

    report["would_rename"] = [plan]
    if plan["approved"]:
        report["confirm_required"] = [plan]

    if not apply:
        return report

    # --apply demands the explicit PO re-approval (both flags). This is the only path that
    # may write an approved artifact, so the gate is hard: missing either flag → refuse.
    if not confirmed_by or not date:
        report["error"] = (
            "confirmation_required: --apply must be accompanied by BOTH --confirmed-by "
            "<PO> AND --date <ISO> (the explicit re-approval of an approved artifact)."
        )
        return report

    brd = root / "docs" / "product" / "brd.md"
    with open(brd, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    new_text, renamed, _had_marker = _transform(text)
    if new_text is None or not renamed or new_text == text:
        # Nothing actually changed (no parseable fence / already migrated) — no write.
        return report

    bak = brd.with_name(brd.name + ".bak")
    if not bak.exists():
        shutil.copy2(brd, bak)
    with open(brd, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)

    report["applied"] = True
    report["migrated"] = [plan["file"]]
    report["confirmed_by"] = confirmed_by
    report["date"] = date
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true",
                    help="rename metric->metrics (requires --confirmed-by AND --date). "
                         "Default is a dry-run that writes nothing.")
    ap.add_argument("--confirmed-by", default=None,
                    help="the PO who re-approves the edit to the approved artifact.")
    ap.add_argument("--date", default=None, help="ISO date of the re-approval.")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    report = migrate(root, apply=args.apply, confirmed_by=args.confirmed_by, date=args.date)
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
