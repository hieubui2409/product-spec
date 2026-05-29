"""manifest_io — MANIFEST.json, SHA256 sidecar, atomic IO for pack."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

MANIFEST_SCHEMA_VERSION = "1.0"


class CollisionError(Exception):
    """Raised when output path exists and ``--force`` not set."""


def _sha256_file(path: Path, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def _git_command(args: list[str], cwd: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", *args], cwd=str(cwd), stderr=subprocess.DEVNULL, timeout=5,
        )
        return out.decode("utf-8").strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""


def build_manifest_json(
    selection: list[tuple[Path, str]],
    bundle: dict,
    *,
    source_date_epoch: int,
    repo_root: Path,
) -> bytes:
    """Build the embedded ``MANIFEST.json`` payload (sorted by arcname)."""
    files = []
    total_bytes = 0
    for src, arcname in selection:
        # Skip symlinks and non-regular files so MANIFEST.json file list and
        # counts match the tarball, which already drops symlinks in tarball.py.
        if src.is_symlink() or not src.is_file():
            continue
        size = src.stat().st_size
        total_bytes += size
        files.append({
            "path": arcname,
            "size": size,
            "sha256": _sha256_file(src),
        })

    # built_at follows source_date_epoch so the bundle is byte-identical by
    # default. Unset (<=0) pins it to the epoch (1970-01-01T00:00:00+00:00);
    # callers wanting a real provenance date pass --source-date-epoch env with
    # SOURCE_DATE_EPOCH set to e.g. the git commit time (the release pipeline does).
    epoch = source_date_epoch if source_date_epoch and source_date_epoch > 0 else 0
    built_at = datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="seconds")

    source_commit = _git_command(["rev-parse", "HEAD"], repo_root) or "unknown"
    source_repo = _git_command(["remote", "get-url", "origin"], repo_root)

    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "bundle_name": bundle.get("bundle_name", "claude-pack"),
        "bundle_version": bundle.get("version", "0.0.0-dev"),
        "built_at": built_at,
        "source_repo": source_repo,
        "source_commit": source_commit,
        "total_bytes": total_bytes,
        "files": files,
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_sha256_sidecar(tar_path: Path) -> Path:
    """Write coreutils-format ``<hex>  <basename>\\n`` sidecar next to ``tar_path``."""
    sidecar = tar_path.with_suffix(tar_path.suffix + ".sha256")
    digest = _sha256_file(tar_path)
    sidecar.write_text(f"{digest}  {tar_path.name}\n", encoding="utf-8")
    return sidecar


def atomic_replace(tmp: Path, final: Path, *, force: bool) -> None:
    """POSIX + Windows atomic move (``os.replace``). Cross-fs fallback to ``shutil.move``.

    Behavior:
    - ``final`` exists, ``force=False`` -> ``CollisionError`` (caller maps to exit 3).
    - ``final`` exists, ``force=True`` -> rename existing to ``{final}.bak.{epoch}`` first.
    """
    if final.is_symlink() or final.exists():
        if not force:
            raise CollisionError(f"output exists: {final} (use --force to overwrite)")
        backup = final.with_suffix(final.suffix + f".bak.{int(time.time())}")
        final.rename(backup)
    else:
        backup = None
    try:
        os.replace(str(tmp), str(final))
    except OSError as e:
        if "cross-device" in str(e).lower() or "EXDEV" in str(e):
            shutil.move(str(tmp), str(final))
        else:
            # Restore backup before re-raising so the user's existing output
            # is not left only as a .bak.{epoch} file with the final path absent.
            tmp.unlink(missing_ok=True)
            if backup is not None and backup.exists():
                try:
                    backup.rename(final)
                except OSError as restore_err:
                    # Both the replace and the restore failed: tell the user
                    # where their previous output survives so it is recoverable.
                    raise OSError(
                        f"{e}; restore failed ({restore_err}); "
                        f"previous output preserved at {backup}"
                    ) from e
            raise


def cleanup_stale_tmp(out_dir: Path, max_age: float = 3600.0) -> int:
    """Remove ``out_dir/.*.tmp`` files older than ``max_age`` seconds."""
    if not out_dir.is_dir():
        return 0
    now = time.time()
    removed = 0
    for entry in out_dir.glob(".*.tmp"):
        try:
            if now - entry.stat().st_mtime > max_age:
                entry.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def filter_findings(selection: Iterable[tuple[Path, str]]) -> tuple[int, int]:
    """Return (file_count, total_bytes) for a selection (regular files only).

    Symlinks are excluded so counts match the tarball (tarball.py skips them).
    """
    count = 0
    total = 0
    for src, _ in selection:
        if src.is_symlink() or not src.is_file():
            continue
        count += 1
        total += src.stat().st_size
    return count, total
