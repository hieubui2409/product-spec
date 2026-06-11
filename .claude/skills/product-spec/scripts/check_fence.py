#!/usr/bin/env python3
"""
check_fence — advisory soft-fence SCAN. Reports working-tree changes that land
OUTSIDE `docs/product/`. ADVISORY ONLY: it never blocks, always exits 0, and is
not a write guard.

This is the pull-side companion to `fs_guard` (the script-path write guard).
Where `fs_guard` refuses an out-of-tree SCRIPT write, this scan surfaces — after
the fact — any file the session touched outside the spec boundary (including raw
LLM `Write`s and LLM-composed bodies that the guard cannot intercept). It feeds
the behavioral pass as a soft nudge, not a gate.

Mechanism: `git status --porcelain` over the project root, listing every changed
path; any path not under `docs/product/` is one `fence_breach` finding (severity
`warn`). No LLM, deterministic. If `root` is not inside a git work tree, the scan
degrades to empty findings (it cannot read change state, and advisory is not an
error).

CLI:
    check_fence.py --root <project-dir>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from encoding_utils import configure_utf8_console
from spec_graph import _now

configure_utf8_console()

# The spec boundary, as a POSIX path prefix relative to the project root.
FENCE_PREFIX = "docs/product/"

# Kit infrastructure: the skill installs its own tree under `.claude/`. Those files
# are NOT PO-authored spec content, so a change there is not a spec-boundary breach —
# and a fresh install dirties thousands of them, which would flood this advisory into
# a useless over-report. Excluded from the scan (only `.claude/`; every other path
# outside FENCE_PREFIX is still surfaced).
KIT_PREFIX = ".claude/"


def _porcelain_paths(root: Path) -> List[str]:
    """Return repo-relative POSIX paths of every changed file per
    `git status --porcelain -z`. NUL-delimited so paths with spaces/newlines are
    parsed unambiguously; rename entries (`R`) carry `dest\\x00orig` — both halves
    are real touches. Returns [] (degrades, never raises) if root is not a git
    work tree."""
    try:
        # -uall: list individual untracked FILES, not collapsed parent dirs — a
        # brand-new `docs/product/` tree would otherwise report as the bare
        # `docs/` dir and be misread as an outside touch.
        proc = subprocess.run(
            ["git", "status", "--porcelain", "-z", "-uall"],
            cwd=str(root), capture_output=True, text=True,
        )
    except (OSError, FileNotFoundError):
        return []
    if proc.returncode != 0:
        # Not a git repo, or git unavailable → advisory degrades to empty.
        return []

    paths: List[str] = []
    # `-z` format: each record is `XY <path>` (and for renames an extra NUL-
    # separated `<orig>` follows). Split on NUL; a record begins with the 2-char
    # status + a space, the remainder is the path.
    fields = proc.stdout.split("\x00")
    i = 0
    while i < len(fields):
        rec = fields[i]
        if not rec:
            i += 1
            continue
        status = rec[:2]
        path = rec[3:]
        paths.append(path)
        # A rename/copy record is followed by its original path in the next field.
        if status and status[0] in ("R", "C"):
            i += 1
            if i < len(fields) and fields[i]:
                paths.append(fields[i])
        i += 1
    return paths


def scan(root: Path) -> List[Dict[str, Any]]:
    """One `fence_breach` finding (severity `warn`) per changed path outside
    `docs/product/`. Advisory — callers must not gate on this."""
    findings: List[Dict[str, Any]] = []
    for rel in _porcelain_paths(Path(root)):
        # Normalize to POSIX separators so the prefix test is OS-agnostic.
        posix = rel.replace("\\", "/")
        if posix == "docs/product" or posix.startswith(FENCE_PREFIX):
            continue
        # Kit's own installed tree — not a spec breach (see KIT_PREFIX).
        if posix == ".claude" or posix.startswith(KIT_PREFIX):
            continue
        findings.append({
            "check": "fence_breach",
            "severity": "warn",
            "artifact_id": None,
            "file": posix,
            "detail": (
                f"{posix} was touched outside the spec boundary "
                f"(docs/product/). Advisory only — the skill writes specs under "
                f"docs/product/; confirm this change belongs here."
            ),
            "context": None,
        })
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    # --lang accepted for CLI-contract uniformity; this is a lang-agnostic JSON
    # feeder (English keys), so it is ignored.
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    args = ap.parse_args()

    root = Path(args.root).resolve()
    findings = scan(root)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "checked_at": _now(),
        "findings": findings,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    # Advisory: always exit 0, even on breaches. It never gates.
    return 0


if __name__ == "__main__":
    sys.exit(main())
