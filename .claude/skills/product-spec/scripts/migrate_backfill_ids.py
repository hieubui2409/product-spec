#!/usr/bin/env python3
"""
migrate_backfill_ids — backfill a missing `id:` field into spec artifact frontmatter.

GATE contract (mirrors migrate_metric_to_metrics.py exactly):
  - dry-run (DEFAULT, no --apply): report artifacts missing `id:`; write ZERO bytes,
    create NO `.bak`. The LLM drives the per-artifact AskUserQuestion off this report.
  - --apply: writes ONLY when BOTH --confirmed-by AND --date are supplied — the explicit
    PO re-approval that authorises editing an artifact. Missing either → refused, non-zero
    exit, no write.
  - Per-artifact scoped; idempotent — if `id:` is already present the artifact is skipped
    and a re-run is a no-op.
  - `.bak` created once (`name + ".bak"`, never overwrite existing .bak).
  - Approved artifact (`status: approved`) → added to `confirm_required`; never
    silently rewritten by a blanket `--apply`. Only written when its id/path appears
    in the `--confirm-approved` allowlist AND both --confirmed-by and --date are given.
  - This migrator inserts ONE thing: the missing `id:`. It does NOT write or modify
    `schema_version` — that is orthogonal to id-backfill.

ID derivation (matches spec_graph.py ID_PATTERN_BY_TYPE):
  - PRODUCT.md        → id: PRODUCT
  - vision.md         → id: VISION
  - brd.md            → id: BRD
  - prds/<slug>.md    → id: PRD-<SLUG-UPPER>
  - epics/<stem>.md   → id: <stem-upper> (e.g. PRD-AUTH-E1)
  - stories/<stem>.md → id: <stem-upper> (e.g. PRD-AUTH-E1-S1)
  - unrecognised path → skipped (fail-soft, reported in `skipped`)

CLI:
    migrate_backfill_ids.py --root <project-dir>
        [--apply --confirmed-by <PO> --date <YYYY-MM-DD>
         [--confirm-approved <ID-or-path>] ...]
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from encoding_utils import configure_utf8_console
from frontmatter_parser import parse_file

configure_utf8_console()

# ---------------------------------------------------------------------------
# ID derivation
# ---------------------------------------------------------------------------

# Artifacts under docs/product/ that carry a fixed canonical id.
_SINGLETON_IDS: Dict[str, str] = {
    "PRODUCT.md": "PRODUCT",
    "vision.md": "VISION",
    "brd.md": "BRD",
}


def _derive_id(path: Path, product_dir: Path) -> Optional[str]:
    """Return the canonical id for an artifact at `path`, or None if undeducible.

    Mirrors the ID conventions in spec_graph.ID_PATTERN_BY_TYPE so the migrator
    inserts exactly the value the graph will later validate.
    """
    try:
        rel = path.relative_to(product_dir)
    except ValueError:
        return None

    parts = rel.parts  # e.g. ("PRODUCT.md",) or ("prds", "auth.md")

    # Singletons at docs/product/ top level
    if len(parts) == 1:
        return _SINGLETON_IDS.get(parts[0])

    # Sub-directory artifacts
    if len(parts) == 2:
        subdir, filename = parts
        stem = Path(filename).stem  # drop .md
        if subdir == "prds":
            return f"PRD-{stem.upper()}"
        if subdir == "epics":
            return stem.upper()
        if subdir == "stories":
            return stem.upper()

    # Deeper nesting or unrecognised path → underivable
    return None


# ---------------------------------------------------------------------------
# Text transformation
# ---------------------------------------------------------------------------

def _transform(text: str, artifact_id: str) -> Tuple[Optional[str], bool]:
    """Insert `id: <artifact_id>` as the first key inside the frontmatter fence.

    Returns (new_text, changed).
    - new_text is None when no parseable frontmatter fence is found.
    - changed is True only when the file was actually modified.

    BOM and inline comments are preserved — the insertion operates at the line level,
    not via YAML round-trip, so all existing content is carried verbatim.

    This migrator changes exactly ONE thing: inserting the missing `id:`.  It does NOT
    touch `schema_version` — stamping or removing schema_version is orthogonal to id
    backfill and must not downgrade era-2 files.
    """
    had_bom = text.startswith("﻿")
    src = text[1:] if had_bom else text
    lines = src.splitlines(keepends=True)

    # Locate frontmatter fence
    open_idx = next((i for i, ln in enumerate(lines) if ln.strip() == "---"), None)
    if open_idx is None:
        return None, False
    close_idx = next(
        (i for i in range(open_idx + 1, len(lines)) if lines[i].strip() == "---"),
        None,
    )
    if close_idx is None:
        return None, False

    newline = "\r\n" if lines[close_idx].endswith("\r\n") else "\n"

    # Check for existing `id:` key (idempotency guard)
    for i in range(open_idx + 1, close_idx):
        stripped = lines[i].lstrip()
        if stripped.startswith("id:") and not lines[i][0:1].isspace():
            # top-level `id:` key already present — nothing to do
            return text, False

    # Insert `id:` as the first key after the opening fence
    insert_pos = open_idx + 1
    lines.insert(insert_pos, f"id: {artifact_id}{newline}")

    result = "".join(lines)
    return ("﻿" + result) if had_bom else result, True


# ---------------------------------------------------------------------------
# Scan + plan
# ---------------------------------------------------------------------------

def _scan_artifacts(product_dir: Path) -> List[Dict[str, Any]]:
    """Walk docs/product/ and return per-artifact plans for files missing `id:`."""
    from spec_graph import ARTIFACT_GLOBS  # local import to avoid circular dep

    items: List[Dict[str, Any]] = []
    for _art_type, globs in ARTIFACT_GLOBS.items():
        for pattern in globs:
            for path in sorted(product_dir.glob(pattern)):
                parsed = parse_file(path)
                if not parsed["ok"]:
                    continue
                fm = parsed["frontmatter"] or {}
                if fm.get("id"):
                    # Already has an id — idempotency: skip entirely
                    continue
                derived = _derive_id(path, product_dir)
                item: Dict[str, Any] = {
                    "file": str(path.relative_to(product_dir.parent.parent)),
                    "path": str(path),
                    "derived_id": derived,
                    "status": fm.get("status"),
                    "approved": fm.get("status") == "approved",
                }
                items.append(item)
    return items


def _scan_unrecognised(product_dir: Path, known_paths: set, repo_root: Path) -> List[str]:
    """Return repo-relative paths of md files in docs/product/ that are outside ARTIFACT_GLOBS
    and thus cannot have an id derived. Fail-soft reporting only.

    All returned paths are relative to `repo_root` so the skipped list is uniform (no mixing
    of absolute and relative strings).
    """
    unrecognised = []
    for path in sorted(product_dir.rglob("*.md")):
        if str(path) in known_paths:
            continue
        # Check if we could derive an id — if not, report as unrecognised
        derived = _derive_id(path, product_dir)
        if derived is None:
            try:
                rel = str(path.relative_to(repo_root))
            except ValueError:
                rel = str(path)
            unrecognised.append(rel)
    return unrecognised


# ---------------------------------------------------------------------------
# Main migrate function
# ---------------------------------------------------------------------------

def migrate(
    root: Path,
    apply: bool,
    confirmed_by: Optional[str],
    date: Optional[str],
    confirm_approved: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], int]:
    """Run the migration. Returns (report_dict, exit_code).

    exit_code is non-zero only when --apply is refused (missing confirmation flags).

    `confirm_approved` is an explicit per-artifact allowlist (ids or repo-relative paths)
    that permits rewriting an approved artifact.  Without an entry in this list an approved
    artifact is always placed in `confirm_required` and skipped from writes — even when
    --apply is given.  This enforces GATE-NO-SILENT-REVERSAL.
    """
    if confirm_approved is None:
        confirm_approved = []
    # Normalise allowlist entries to lower-case strings for case-insensitive matching.
    approved_allowset: set = {str(a).lower() for a in confirm_approved}

    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "root": str(root),
        "applied": False,
        "would_insert": [],
        "confirm_required": [],
        "migrated": [],
        "skipped": [],
        "error": None,
    }

    product_dir = root / "docs" / "product"
    if not product_dir.exists():
        return report, 0

    items = _scan_artifacts(product_dir)

    # Collect unrecognised (underivable) paths — all repo-relative for uniformity (FIX 3).
    known_paths = {item["path"] for item in items}
    unrecognised = _scan_unrecognised(product_dir, known_paths, root)
    report["skipped"] = unrecognised

    # Separate underivable items from the actionable set
    underivable = [it for it in items if it["derived_id"] is None]
    actionable = [it for it in items if it["derived_id"] is not None]

    # Add underivable to skipped as well (already repo-relative from _scan_artifacts)
    report["skipped"].extend(it["file"] for it in underivable)

    report["would_insert"] = [
        {"file": it["file"], "id": it["derived_id"], "approved": it["approved"]}
        for it in actionable
    ]
    report["confirm_required"] = [
        {"file": it["file"], "id": it["derived_id"]}
        for it in actionable if it["approved"]
    ]

    if not apply:
        return report, 0

    # --apply demands explicit PO re-approval (both flags). Hard gate: missing either → refuse.
    if not confirmed_by or not date:
        report["error"] = (
            "confirmation_required: --apply must be accompanied by BOTH --confirmed-by "
            "<PO> AND --date <YYYY-MM-DD> (the explicit re-approval authorising the edit)."
        )
        return report, 1

    migrated = []
    for item in actionable:
        # GATE-NO-SILENT-REVERSAL: approved artifacts require explicit per-artifact
        # opt-in via --confirm-approved <ID-or-path>.  Without it, skip and leave file
        # byte-identical — they are already in confirm_required for the LLM to surface.
        if item["approved"]:
            artifact_id_lower = (item["derived_id"] or "").lower()
            file_lower = item["file"].lower()
            if artifact_id_lower not in approved_allowset and file_lower not in approved_allowset:
                # Not in allowlist → skip write; already reported in confirm_required.
                continue

        path = Path(item["path"])
        artifact_id = item["derived_id"]

        with open(path, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()

        new_text, changed = _transform(text, artifact_id)
        if new_text is None or not changed:
            # Unparseable fence or already has id — no write
            continue

        bak = path.with_name(path.name + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)

        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)

        migrated.append(item["file"])

    report["applied"] = bool(migrated)
    report["migrated"] = migrated
    report["confirmed_by"] = confirmed_by
    report["date"] = date
    return report, 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Backfill missing id: fields into spec artifact frontmatter."
    )
    ap.add_argument("--root", default=".", help="project root directory")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="write changes (requires --confirmed-by AND --date). Default is dry-run.",
    )
    ap.add_argument(
        "--confirmed-by",
        default=None,
        help="the PO who authorises the edit.",
    )
    ap.add_argument(
        "--date",
        default=None,
        help="ISO date of the authorisation (YYYY-MM-DD).",
    )
    ap.add_argument(
        "--confirm-approved",
        dest="confirm_approved",
        action="append",
        default=[],
        metavar="ID_OR_PATH",
        help=(
            "Explicitly allow an approved artifact to be rewritten.  Repeatable.  "
            "The value is matched against the artifact's derived ID (e.g. BRD) or its "
            "repo-relative path (case-insensitive).  Without this flag, approved artifacts "
            "are listed in confirm_required and skipped from writes."
        ),
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    report, exit_code = migrate(
        root,
        apply=args.apply,
        confirmed_by=args.confirmed_by,
        date=args.date,
        confirm_approved=args.confirm_approved,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
