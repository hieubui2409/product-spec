#!/usr/bin/env python3
"""
migrate_multidim_fields — bring an existing v1 spec up to the v2 multidim schema
by adding the new dimension fields as EMPTY placeholders.

Per-type placeholder set (the only fields this migration touches):
    PRD  → risks: [], target_date: null, depends_on: [], competitive_parity: {}
    Epic → risks: [], target_date: null, depends_on: []
    BRD  → competitors: []

Why placeholders (not values): the empty shapes parse cleanly (`[]`/`{}`/`null`),
keep every renderer branch-free, and silence the PRD/Epic "warn-if-missing" noise
without inventing data the PO never entered. The PO fills real values later via the
interview flags.

Contract (Script-vs-LLM split / G-B1 — structural only, no judgment):
  - Dry-run is the DEFAULT (no --apply): report which files lack which v2 fields;
    write NOTHING; create NO `.bak`.
  - --apply: insert the missing placeholder lines into the existing frontmatter
    block (a minimal text edit — the rest of the file is preserved byte-for-byte),
    after copying the original to `<file>.bak` first.
  - status: approved files are NEVER written — they are deferred to a
    `confirm_required` list (the LLM drives the per-item AskUserQuestion). This is
    the no-auto-edit-approved guarantee (G-A3 / G-F3).
  - Idempotent + deterministic: a field already present is never re-added, so a
    second --apply run is a no-op and does NOT clobber the first run's `.bak`.
  - Analytical script: ALWAYS exits 0 (the CLI contract); --apply is the only
    mutating flag.

CLI:
    migrate_multidim_fields.py --root <project-dir> [--apply]
        Prints a JSON report to stdout. Always exits 0.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from encoding_utils import configure_utf8_console
from frontmatter_parser import parse_file

configure_utf8_console()


# The v2 placeholder lines per artifact type, in deterministic insertion order.
# Each entry is (field-name, frontmatter-line). The line is the EXACT YAML text
# inserted before the closing `---` when the field is absent. Empty shapes only:
# `[]` / `{}` / `null` — never a value (Script-vs-LLM split; the PO fills real
# data later via the interview flags).
PLACEHOLDER_LINES_FOR_TYPE: Dict[str, List[Tuple[str, str]]] = {
    "prd": [
        ("risks", "risks: []"),
        ("target_date", "target_date: null"),
        ("depends_on", "depends_on: []"),
        ("competitive_parity", "competitive_parity: {}"),
    ],
    "epic": [
        ("risks", "risks: []"),
        ("target_date", "target_date: null"),
        ("depends_on", "depends_on: []"),
    ],
    "brd": [
        ("competitors", "competitors: []"),
    ],
}

# Where each migratable type lives under docs/product/. Mirrors
# spec_graph.ARTIFACT_GLOBS for the subset this migration touches (PRODUCT/vision
# carry no v2 dimension fields, so they are intentionally absent).
MIGRATABLE_GLOBS: Dict[str, List[str]] = {
    "brd": ["brd.md"],
    "prd": ["prds/*.md"],
    "epic": ["epics/*.md"],
}


def _iter_migratable_files(product_dir: Path) -> List[Tuple[str, Path]]:
    """Yield (type, path) for every migratable artifact, in a deterministic order
    (type order is fixed; paths sorted within each glob)."""
    out: List[Tuple[str, Path]] = []
    for art_type, globs in MIGRATABLE_GLOBS.items():
        for pattern in globs:
            for path in sorted(product_dir.glob(pattern)):
                out.append((art_type, path))
    return out


def _missing_fields(frontmatter: Dict[str, Any], art_type: str) -> List[Tuple[str, str]]:
    """Return the placeholder (field, line) tuples whose field is ABSENT from the
    frontmatter mapping. A field already present (even if empty/None) is left
    untouched — that is what makes a re-run idempotent."""
    fm = frontmatter or {}
    return [(name, line) for (name, line) in PLACEHOLDER_LINES_FOR_TYPE.get(art_type, [])
            if name not in fm]


def _insert_before_closing_fence(text: str, lines: List[str]) -> Optional[str]:
    """Insert `lines` immediately before the closing `---` of the frontmatter
    block. Returns the new text, or None if the file has no parseable closing
    fence (caller skips it rather than corrupting it).

    A minimal text edit on purpose: the body and the existing frontmatter lines
    are preserved verbatim, so the `.bak`/idempotency invariants hold and a
    YAML round-trip never reflows the PO's hand-authored frontmatter."""
    # Capture and preserve a leading UTF-8 BOM so --apply is byte-for-byte
    # on BOM-authored files (stripping only for fence-scanning, not for output).
    had_bom = text.startswith("﻿")
    src = text[1:] if had_bom else text

    src_lines = src.splitlines(keepends=True)
    # Find the opening fence (first line that is exactly `---`) and the matching
    # closing fence (the next `---`). Mirrors frontmatter_parser's FRONTMATTER_RE
    # contract: the file must start with `---`.
    open_idx = None
    for i, ln in enumerate(src_lines):
        if ln.strip() == "---":
            open_idx = i
            break
    if open_idx is None:
        return None
    close_idx = None
    for i in range(open_idx + 1, len(src_lines)):
        if src_lines[i].strip() == "---":
            close_idx = i
            break
    if close_idx is None:
        return None

    # Re-validate the candidate frontmatter slice: a block-scalar value may contain
    # an indented line that strips to '---', making the scanner stop early and yield
    # a partial YAML slice. If the slice between open_idx and close_idx does not
    # parse as a YAML mapping, the close_idx is wrong — do not insert (return None
    # so the caller skips this file rather than corrupting it).
    candidate_fm = "".join(src_lines[open_idx + 1:close_idx])
    try:
        parsed_candidate = yaml.safe_load(candidate_fm)
    except yaml.YAMLError:
        return None
    if not isinstance(parsed_candidate, dict):
        return None

    # Detect the line-ending style from the CLOSING fence of the frontmatter block
    # (not from the whole file). A body section may use CRLF for e.g. a code sample
    # while the frontmatter was authored with LF, or vice versa — using the closing
    # fence line's own terminator keeps the inserted placeholder lines consistent
    # with the frontmatter style without being influenced by body newlines.
    newline = "\r\n" if src_lines[close_idx].endswith("\r\n") else "\n"

    insert_block = "".join(ln.rstrip("\r\n") + newline for ln in lines)
    new_lines = src_lines[:close_idx] + [insert_block] + src_lines[close_idx:]
    result = "".join(new_lines)
    return ("﻿" + result) if had_bom else result


def plan_file(art_type: str, path: Path, product_dir: Path) -> Optional[Dict[str, Any]]:
    """Compute the migration plan for one file. Returns None if the file is already
    fully v2 (no missing fields) or could not be parsed for editing.

    A returned plan carries:
        {type, file, id, status, missing: [field...], approved: bool}
    """
    parsed = parse_file(path)
    if not parsed["ok"]:
        # Unparseable frontmatter is a validate-gate concern, not a migration
        # concern. Surface it as a skip so the run never crashes (G-B fail-soft).
        return {
            "type": art_type,
            "file": path.relative_to(product_dir).as_posix(),
            "id": None,
            "status": None,
            "missing": [],
            "approved": False,
            "parse_error": parsed.get("error"),
        }
    fm = parsed["frontmatter"] or {}
    missing = _missing_fields(fm, art_type)
    if not missing:
        return None
    return {
        "type": art_type,
        "file": path.relative_to(product_dir).as_posix(),
        "id": fm.get("id"),
        "status": fm.get("status"),
        "missing": [name for (name, _line) in missing],
        "_lines": [line for (_name, line) in missing],
        "approved": fm.get("status") == "approved",
    }


def apply_file(path: Path) -> bool:
    """Apply the migration to one file: back up the original to `<file>.bak`, then
    rewrite with the missing placeholder lines inserted. Returns True on success.

    Re-derives the missing set from the CURRENT on-disk content (not a stale plan)
    so the edit is idempotent even if the file changed between plan and apply.
    The `.bak` is written ONLY when there is real work to do, and never clobbered
    on a no-op re-run (the early-return below)."""
    art_type = _type_for_path(path)
    if art_type is None:
        return False
    parsed = parse_file(path)
    if not parsed["ok"]:
        return False
    # Defense-in-depth: G-A3 no-auto-edit-approved guard at the apply layer,
    # independent of migrate()'s control flow (belt-and-suspenders).
    if (parsed["frontmatter"] or {}).get("status") == "approved":
        return False
    missing = _missing_fields(parsed["frontmatter"] or {}, art_type)
    if not missing:
        # Idempotent: nothing to add → no write, no `.bak` (so a prior run's
        # original-content `.bak` is preserved).
        return False
    # Read + write with newline translation DISABLED (newline="") so the file's
    # existing CRLF/LF style survives — read_text_utf8/write_text would normalize
    # via universal-newlines + os.linesep and break the byte-for-byte contract.
    with open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    new_text = _insert_before_closing_fence(text, [line for (_n, line) in missing])
    if new_text is None or new_text == text:
        return False
    bak = path.with_name(path.name + ".bak")
    # Back up the PRE-migration original. Only write the `.bak` if it does not
    # already exist, so a second --apply (after a manual partial edit, say) can
    # never overwrite the genuine pre-migration copy with a half-migrated one.
    if not bak.exists():
        shutil.copy2(path, bak)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    return True


def _type_for_path(path: Path) -> Optional[str]:
    """Infer the migratable type from a file's location under docs/product/."""
    name = path.name
    parent = path.parent.name
    if name == "brd.md":
        return "brd"
    if parent == "prds":
        return "prd"
    if parent == "epics":
        return "epic"
    return None


def migrate(root: Path, apply: bool) -> Dict[str, Any]:
    """Build the migration report (and, with apply=True, perform the edits).

    Report shape:
        {
          schema_version, root, applied: bool,
          would_migrate: [plan...],   # non-approved files needing fields (dry-run view)
          migrated:      [file...],   # files actually written this run (apply only)
          confirm_required: [plan...],# approved files deferred to per-item PO sign-off
          skipped:       [plan...],   # parse_error files (surface, don't crash)
        }
    """
    product_dir = root / "docs" / "product"
    would_migrate: List[Dict[str, Any]] = []
    confirm_required: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    migrated: List[str] = []

    for art_type, path in _iter_migratable_files(product_dir):
        plan = plan_file(art_type, path, product_dir)
        if plan is None:
            continue
        if plan.get("parse_error"):
            skipped.append(plan)
            continue
        public_plan = {k: v for k, v in plan.items() if not k.startswith("_")}
        if plan["approved"]:
            # No-auto-edit-approved (G-A3): never written. Deferred to the PO,
            # who confirms each item; the LLM drives that AskUserQuestion.
            confirm_required.append(public_plan)
            continue
        would_migrate.append(public_plan)
        if apply:
            if apply_file(path):
                migrated.append(plan["file"])

    return {
        "schema_version": "1.0",
        "root": str(root),
        "applied": apply,
        "would_migrate": would_migrate,
        "migrated": migrated,
        "confirm_required": confirm_required,
        "skipped": skipped,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument(
        "--apply", action="store_true",
        help="write the placeholders (backing up each touched original to "
             "<file>.bak first). Default is a dry-run that writes nothing.",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    report = migrate(root, apply=args.apply)
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
