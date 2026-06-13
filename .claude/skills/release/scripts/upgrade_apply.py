"""upgrade_apply — mutator for the 1.x -> 2.x legacy sweep.

The ONLY module that touches the filesystem during an upgrade.
All planning lives in upgrade_planner.py.

Public surface:
    apply(plan_items, target_root, backup_root, *, now_ts) -> dict
    rollback(backup_dir) -> dict

Atomicity guarantee: if ANY removal step raises, every item already removed
is restored from the backup dir and the exception is re-raised. Net: all or
nothing — the target tree is either fully swept or left as before.

Symlink safety: before any delete, is_symlink() is checked. Symlink-typed
entries use os.unlink() only — never shutil.rmtree through a link.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from upgrade_planner import NOOP, PROMPT, REMOVE, UNLINK_ONLY, PlanItem  # type: ignore[import-not-found]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _backup_path(backup_dir: Path, target_root: Path, live: Path) -> Path:
    """Destination inside backup_dir that mirrors live's repo-relative path."""
    try:
        rel = live.relative_to(target_root)
    except ValueError:
        rel = Path(live.name)
    dst = backup_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    return dst


def _copy_to_backup(
    live: Path, target_root: Path, backup_dir: Path
) -> tuple:
    """Copy file or directory tree to backup.

    Returns (backup_path_str, symlink_target_or_None).
    For symlinks the backup_path_str points to the .symlink_target sidecar file;
    symlink_target_or_None holds the readlink value so rollback can recreate the link.
    For regular files/dirs symlink_target_or_None is None.
    """
    dst = _backup_path(backup_dir, target_root, live)
    if live.is_symlink():
        # Record the link target in a sidecar file (for forensics + restore).
        link_target = os.readlink(str(live))
        sidecar = dst.with_name(dst.name + ".symlink_target")
        sidecar.write_text(link_target, encoding="utf-8")
        return (str(sidecar), link_target)
    if live.is_dir():
        shutil.copytree(str(live), str(dst), symlinks=True)
    else:
        shutil.copy2(str(live), str(dst))
    return (str(dst), None)


def _delete_live(live: Path, is_symlink: bool) -> None:
    """Delete live path. Symlinks: os.unlink only. Dirs: rmtree (no follow)."""
    if is_symlink or live.is_symlink():
        # Never rmtree through a symlink
        live.unlink()
    elif live.is_dir():
        shutil.rmtree(str(live))
    else:
        live.unlink()


def _restore_from_backup(manifest_entries: list[dict], backup_dir: Path) -> None:
    """Restore each entry from backup_dir to original_path."""
    for entry in manifest_entries:
        original = Path(entry["original_path"])
        original.parent.mkdir(parents=True, exist_ok=True)

        # Symlink entries: recreate the symlink from the stored target string.
        if entry.get("is_symlink"):
            target = entry.get("symlink_target")
            if original.is_symlink() or original.exists():
                if original.is_dir() and not original.is_symlink():
                    shutil.rmtree(str(original))
                else:
                    original.unlink()
            if target is not None:
                os.symlink(target, str(original))
            continue

        backup = Path(entry["backup_path"])
        if not backup.exists() and not backup.is_symlink():
            continue
        if backup.is_dir():
            if original.exists() or original.is_symlink():
                if original.is_symlink():
                    original.unlink()
                else:
                    shutil.rmtree(str(original))
            shutil.copytree(str(backup), str(original), symlinks=True)
        else:
            shutil.copy2(str(backup), str(original))


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------
def apply(
    plan_items: list[PlanItem],
    target_root: Path,
    backup_root: Path,
    *,
    now_ts: str,
) -> dict:
    """Execute the upgrade plan.

    Args:
        plan_items:  Output of upgrade_planner.plan().
        target_root: Absolute path to the recipient repo root.
        backup_root: Directory under which the timestamped backup dir is created.
        now_ts:      Injected timestamp string (e.g. "20260612T101500Z").
                     NEVER call datetime.now() here — caller injects for determinism.

    Returns a summary dict with keys: removed, kept_prompts, unlinked, noop, backup_dir.

    Atomicity: on any exception mid-loop, restores all previously removed items
    from backup and re-raises the original exception.
    """
    backup_dir = backup_root / f"upgrade-backup-{now_ts}"
    backup_created = False

    def _ensure_backup_dir() -> None:
        nonlocal backup_created
        if not backup_created:
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_created = True

    rollback_manifest: list[dict] = []
    removed: list[str] = []
    kept_prompts: list[str] = []
    unlinked: list[str] = []
    noop: list[str] = []

    for item in plan_items:
        live = target_root / item.path

        if item.action == NOOP:
            noop.append(item.path)
            continue

        if item.action == PROMPT:
            kept_prompts.append(item.path)
            continue

        if item.action in (REMOVE, UNLINK_ONLY):
            # Safety check: re-verify symlink status at apply time
            is_sym = live.is_symlink()

            if not live.exists() and not is_sym:
                # Already absent — idempotent, record as noop
                noop.append(item.path)
                continue

            # Backup first, record in manifest
            _ensure_backup_dir()
            try:
                backup_path_str, symlink_target = _copy_to_backup(
                    live, target_root, backup_dir
                )
            except OSError as e:
                _restore_from_backup(rollback_manifest, backup_dir)
                raise RuntimeError(
                    f"Backup failed for {item.path}: {e} — aborting upgrade, tree restored"
                ) from e

            manifest_entry = {
                "original_path": str(live),
                "backup_path": backup_path_str,
                "action": item.action,
                "kind": item.kind,
                "is_symlink": is_sym,
                "symlink_target": symlink_target,
            }
            rollback_manifest.append(manifest_entry)

            # Write rollback manifest before mutating (so rollback is always possible)
            _write_rollback_manifest(backup_dir, rollback_manifest)

            # Now delete
            try:
                _delete_live(live, is_sym)
            except OSError as e:
                _restore_from_backup(rollback_manifest, backup_dir)
                raise RuntimeError(
                    f"Delete failed for {item.path}: {e} — aborting upgrade, tree restored"
                ) from e

            if item.action == UNLINK_ONLY:
                unlinked.append(item.path)
            else:
                removed.append(item.path)

    # Final manifest write (covers all items; only if the backup dir was created)
    if backup_created:
        _write_rollback_manifest(backup_dir, rollback_manifest)

    return {
        "removed": removed,
        "kept_prompts": kept_prompts,
        "unlinked": unlinked,
        "noop": noop,
        "backup_dir": str(backup_dir),
    }


def _write_rollback_manifest(backup_dir: Path, entries: list[dict]) -> None:
    manifest_path = backup_dir / "rollback-manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": entries}, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------
def rollback(backup_dir: Path) -> dict:
    """Restore all items from a backup dir using its rollback-manifest.json.

    Idempotent-ish: re-copying an already-restored file is safe (overwrites
    with same content). Returns a dict with keys: restored, backup_dir.
    """
    manifest_path = backup_dir / "rollback-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"rollback-manifest.json not found in {backup_dir}"
        )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"corrupt rollback-manifest.json in {backup_dir}: {e}") from e
    entries = data.get("entries", [])
    _restore_from_backup(entries, backup_dir)
    return {
        "restored": [e["original_path"] for e in entries],
        "backup_dir": str(backup_dir),
    }


# ---------------------------------------------------------------------------
# CLI (thin — mainly for upgrade.sh's --rollback flag)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Rollback a previous upgrade-backup dir."
    )
    parser.add_argument("--rollback", metavar="BACKUP_DIR", required=True,
                        help="Path to the upgrade-backup-* dir to restore from")
    args = parser.parse_args()

    try:
        result = rollback(Path(args.rollback))
        print(json.dumps(result, indent=2))
    except (FileNotFoundError, OSError, ValueError) as e:
        print(f"[upgrade_apply] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
