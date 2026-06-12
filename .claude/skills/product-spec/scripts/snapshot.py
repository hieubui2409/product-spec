#!/usr/bin/env python3
"""
snapshot — opt-in spec-artifact snapshot/restore engine.

Captures the current spec artifact tree (docs/product/** or any resolved spec
root) into a timestamped snapshot dir under a configurable snapshots home, and
restores a named snapshot back over the spec tree.

CRITICAL DESIGN: snapshot is OPT-IN ONLY.
  - Invoked explicitly via --snapshot / --restore flags in the CLI.
  - No automatic snapshot call is wired into any migrator, approve, or update
    path. That convenience hook is deferred; the sibling migrator files are
    never touched by this module.

Public API:
  make_snapshot(spec_root, snapshots_home, ts) -> Path
      Copy spec_root/** into <snapshots_home>/<ts>/ + write README.
      Timestamps are injected so tests are deterministic; CLI path uses real time.

  restore_snapshot(spec_root, snapshots_home, ts, *, confirm=False) -> None
      Restore <snapshots_home>/<ts>/ back over spec_root.
      Refuses (raises RestoreDirtyError) when spec_root is inside a git work
      tree AND has uncommitted changes AND confirm=False.
      Uses a staging dir + atomic rename so partial copies never leave the
      live tree in an inconsistent state.

  list_snapshots(snapshots_home) -> List[str]
      Return sorted timestamp strings of available snapshots.
      Returns [] when snapshots_home is absent or empty — never raises.

Thresholds (hard integers, no prose):
  None in this module — safety threshold for "dirty" is the presence of ANY
  uncommitted change returned by `git status --porcelain docs/product/`.

CLI (wired from status.py argparse wiring):
  snapshot.py --root <project-dir> --snapshot [--label <label>]
  snapshot.py --root <project-dir> --restore <ts> [--confirm]
  snapshot.py --root <project-dir> --list
"""

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class RestoreDirtyError(Exception):
    """Raised when restore would clobber uncommitted changes without confirmation."""


class SnapshotNotFoundError(Exception):
    """Raised when the requested snapshot timestamp does not exist."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_README_TEMPLATE = """\
# Product-Spec Snapshot

Captured: {ts}
Source:   {spec_root}

This directory is an opt-in point-in-time copy of the spec artifact tree.
It was created by `snapshot.py --snapshot` and is excluded from git tracking
via the project's .gitignore.

## Restore

To restore this snapshot over the live spec tree:

    python3 snapshot.py --root <project-root> --restore {ts} --confirm

The `--confirm` flag is required when the live tree has uncommitted changes
(to prevent silent data loss). Without it the restore is refused.

## Contents

All files in this snapshot directory mirror the layout of the original
spec artifact tree at the time of capture. Files are copies — the source
tree was never moved or deleted.
"""


def _is_git_work_tree(root: Path) -> bool:
    """True only when `root` is inside a git work tree.

    Mirrors the reflect_scan._is_git_work_tree pattern: any failure (no git
    binary, not a repo) degrades to False — never raises."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(root), capture_output=True, text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _has_uncommitted_changes(spec_root: Path) -> bool:
    """True when `spec_root` (or its parent git root) has uncommitted changes
    touching the spec_root subtree.

    Uses `git status --porcelain -- <path>` which lists untracked, modified,
    and staged-but-not-committed files under the given path. Any output line
    means there are uncommitted changes.

    Degrades to False on any subprocess error (fail-safe: if we cannot check,
    we do not block the user)."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", str(spec_root)],
            cwd=str(spec_root), capture_output=True, text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    if proc.returncode != 0:
        return False
    return bool(proc.stdout.strip())


def _real_ts() -> str:
    """Real-time timestamp in the canonical format used for snapshot dir names.
    Tests inject a deterministic string instead of calling this."""
    return dt.datetime.now().strftime("%Y%m%dT%H%M%S")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_snapshot(spec_root: Path, snapshots_home: Path, ts: Optional[str] = None) -> Path:
    """Copy spec_root into <snapshots_home>/<ts>/ and write a README.

    Parameters
    ----------
    spec_root:      the spec artifact tree to capture (e.g. docs/product/)
    snapshots_home: where all snapshots live (e.g. <proj>/.product-spec-snapshots/)
    ts:             timestamp string used as the snapshot dir name; default = real
                    clock time. Tests inject a deterministic value.

    Returns the Path of the newly created snapshot dir.

    Never moves or deletes source files — always copies. Never overwrites an
    existing snapshot dir (timestamps are unique enough; if the exact ts already
    exists, the copy target is the existing dir plus the new files, matching
    copytree behaviour on Python 3.8+).
    """
    spec_root = Path(spec_root)
    snapshots_home = Path(snapshots_home)
    if ts is None:
        ts = _real_ts()

    dest = snapshots_home / ts
    snapshots_home.mkdir(parents=True, exist_ok=True)

    # Copy tree — dirs_exist_ok=True so a re-run with the same ts is safe
    shutil.copytree(str(spec_root), str(dest), dirs_exist_ok=True)

    # Write README after the copy so it describes the captured state
    readme = dest / "README.md"
    readme.write_text(
        _README_TEMPLATE.format(ts=ts, spec_root=spec_root),
        encoding="utf-8",
    )

    return dest


def restore_snapshot(
    spec_root: Path,
    snapshots_home: Path,
    ts: str,
    *,
    confirm: bool = False,
) -> None:
    """Restore a snapshot back over the live spec tree.

    Safety contract (mirrors the migrator caution philosophy):
      - If spec_root is inside a git work tree AND has uncommitted changes AND
        confirm=False → raises RestoreDirtyError. No files are touched.
      - With confirm=True the restore proceeds even over dirty trees.

    Atomicity: copies into a staging dir first, then performs an atomic
    rename swap so the live tree is never left in a partially-restored state.

    Parameters
    ----------
    spec_root:      live spec tree to restore over
    snapshots_home: parent dir of all snapshots
    ts:             timestamp string identifying the snapshot to restore
    confirm:        set True to allow restore over uncommitted changes
    """
    spec_root = Path(spec_root)
    snapshots_home = Path(snapshots_home)
    snap_dir = snapshots_home / ts

    if not snap_dir.is_dir():
        raise SnapshotNotFoundError(
            f"Snapshot '{ts}' not found in {snapshots_home}. "
            f"Available: {list_snapshots(snapshots_home)}"
        )

    # Dirty-tree guard: refuse if inside git and has uncommitted changes
    if not confirm and _is_git_work_tree(spec_root) and _has_uncommitted_changes(spec_root):
        raise RestoreDirtyError(
            f"Refusing to restore snapshot '{ts}': the spec tree at {spec_root} "
            "has uncommitted changes. Pass confirm=True (--confirm on CLI) to "
            "override, or commit / stash your changes first."
        )

    # Staging dir: sibling of spec_root to stay on the same filesystem
    staging = spec_root.parent / f"_restore_staging_{ts}"
    try:
        # Copy snapshot into staging (README excluded from the live tree)
        shutil.copytree(str(snap_dir), str(staging), dirs_exist_ok=False)

        # Remove README from staging — it is snapshot metadata, not a spec artifact
        readme_in_staging = staging / "README.md"
        if readme_in_staging.is_file():
            readme_in_staging.unlink()

        # Atomic swap: rename live tree to a backup, staging to live
        backup = spec_root.parent / f"_restore_backup_{ts}"
        if backup.exists():
            shutil.rmtree(backup)
        spec_root.rename(backup)
        staging.rename(spec_root)
        # Remove the backup now that the swap succeeded
        shutil.rmtree(backup)

    finally:
        # Clean up staging if it still exists (swap did not complete)
        if staging.exists():
            shutil.rmtree(staging)


def list_snapshots(snapshots_home: Path) -> List[str]:
    """Return sorted list of snapshot timestamp strings.

    Returns [] when snapshots_home does not exist or is empty. Never raises.
    """
    snapshots_home = Path(snapshots_home)
    if not snapshots_home.is_dir():
        return []
    entries = sorted(
        d.name for d in snapshots_home.iterdir() if d.is_dir()
    )
    return entries


def latest_snapshot(snapshots_home: Path) -> Optional[str]:
    """Return the most recent snapshot timestamp string, or None if none exist."""
    entries = list_snapshots(snapshots_home)
    return entries[-1] if entries else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _default_snapshots_home(root: Path) -> Path:
    """Conventional snapshots home: <project-root>/.product-spec-snapshots/"""
    return root / ".product-spec-snapshots"


def _default_spec_root(root: Path) -> Path:
    """Conventional spec artifact root: <project-root>/docs/product/"""
    return root / "docs" / "product"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Opt-in snapshot/restore engine for the product spec artifact tree."
    )
    ap.add_argument("--root", default=".", help="Project root directory.")
    ap.add_argument(
        "--snapshot", action="store_true",
        help="Capture the current spec artifact tree into a timestamped snapshot.",
    )
    ap.add_argument(
        "--label", default=None,
        help="Optional label suffix appended to the snapshot timestamp dir name.",
    )
    ap.add_argument(
        "--restore", metavar="TS",
        help="Restore the snapshot identified by timestamp TS over the live spec tree.",
    )
    ap.add_argument(
        "--confirm", action="store_true",
        help="Allow --restore to proceed even when the live tree has uncommitted changes.",
    )
    ap.add_argument(
        "--list", action="store_true",
        help="List available snapshot timestamps.",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    spec_root = _default_spec_root(root)
    snapshots_home = _default_snapshots_home(root)

    if args.snapshot:
        ts = _real_ts()
        if args.label:
            ts = f"{ts}-{args.label}"
        dest = make_snapshot(spec_root, snapshots_home, ts=ts)
        print(f"Snapshot captured: {dest}", file=sys.stderr)
        return 0

    if args.restore:
        try:
            restore_snapshot(spec_root, snapshots_home, args.restore, confirm=args.confirm)
            print(f"Restored snapshot '{args.restore}' to {spec_root}", file=sys.stderr)
        except RestoreDirtyError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        except SnapshotNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        return 0

    if args.list:
        snaps = list_snapshots(snapshots_home)
        if snaps:
            for s in snaps:
                print(s)
        else:
            print("(no snapshots)", file=sys.stderr)
        return 0

    ap.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
