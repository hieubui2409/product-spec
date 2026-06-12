#!/usr/bin/env python3
"""
status_vcs — VCS-state checks surfaced through --status.

A focused sibling of status.py that keeps the main module near its LOC budget
by owning all VCS-state detection logic. status.py imports and calls
vcs_warnings() in both its return branches.

Checks emitted (type field):
  "spec_tree_untracked"
      The spec artifact tree is outside a git work tree — no version control.
      Triggers when `git rev-parse --is-inside-work-tree` fails for the
      spec_root directory.

  "large_uncommitted_diff"
      The spec tree has ≥ LARGE_DIFF_FILE_COUNT uncommitted files (untracked
      + modified + staged but not yet committed). Hard threshold: 5 files.
      Detected via `git status --porcelain -- <spec_root>` line count.

Hard thresholds (concrete integers, not prose):
  LARGE_DIFF_FILE_COUNT = 5   (number of changed files; ≥ this → warn)

Each warning dict carries:
  {
    "type":     str,          # one of the type strings above
    "severity": "warn",       # all VCS warnings are non-blocking
    "subject":  str,          # human-readable subject
    "detail":   str,          # additional context (file counts, paths)
  }

Fail-soft contract: no git binary, not a repo, any subprocess error → the
relevant check degrades to an empty list, never crashes. The caller (status.py)
always gets a List[Dict], never an exception from this module.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

# Hard threshold: number of uncommitted files (new + modified + staged) in the
# spec tree that constitutes a "large" diff worth warning about.
LARGE_DIFF_FILE_COUNT: int = 5


def _is_git_work_tree(root: Path) -> bool:
    """True when root is inside a git work tree.

    Mirrors the reflect_scan._is_git_work_tree pattern: any failure degrades
    to False, never raises."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(root), capture_output=True, text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _uncommitted_file_count(spec_root: Path) -> int:
    """Count uncommitted files (new + modified + staged) under spec_root.

    Uses `git status --porcelain -- <path>`. Each output line is one file.
    Returns 0 on any subprocess error (fail-soft).
    """
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", str(spec_root)],
            cwd=str(spec_root), capture_output=True, text=True,
        )
    except (OSError, FileNotFoundError):
        return 0
    if proc.returncode != 0:
        return 0
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return len(lines)


def _warn(warning_type: str, subject: str, detail: str) -> Dict[str, Any]:
    return {
        "type": warning_type,
        "severity": "warn",
        "subject": subject,
        "detail": detail,
    }


def vcs_warnings(spec_root: Path) -> List[Dict[str, Any]]:
    """Return VCS-state warnings for the spec artifact tree at spec_root.

    Always returns a List[Dict]; never raises. Empty list means clean VCS state.

    Checks (in order):
    1. Is spec_root inside a git work tree? If not → spec_tree_untracked.
       Short-circuits: no point counting a diff if there is no git repo.
    2. How many files in the spec tree are uncommitted?
       If ≥ LARGE_DIFF_FILE_COUNT → large_uncommitted_diff.
    """
    spec_root = Path(spec_root)
    warnings: List[Dict[str, Any]] = []

    if not spec_root.is_dir():
        # Spec root does not exist — not a git issue, not our warning to raise
        return warnings

    if not _is_git_work_tree(spec_root):
        warnings.append(_warn(
            "spec_tree_untracked",
            "Spec artifact tree is outside git version control",
            f"The directory {spec_root} is not inside a git work tree. "
            "Changes to spec artifacts are not tracked and cannot be recovered "
            "from git history. Consider initialising a git repo or running "
            "`--snapshot` to capture a manual backup.",
        ))
        # No point checking diff count without a git repo
        return warnings

    count = _uncommitted_file_count(spec_root)
    if count >= LARGE_DIFF_FILE_COUNT:
        warnings.append(_warn(
            "large_uncommitted_diff",
            f"Large uncommitted diff in spec tree ({count} files)",
            f"{count} file(s) in {spec_root} are modified or untracked but not "
            f"committed (threshold: {LARGE_DIFF_FILE_COUNT}). Consider committing "
            "your work or running `--snapshot` to capture a point-in-time backup "
            "before continuing.",
        ))

    return warnings
