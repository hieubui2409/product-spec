"""manifest_io — MANIFEST.json, SHA256 sidecar, atomic IO for pack."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

MANIFEST_SCHEMA_VERSION = "1.0"


class CollisionError(Exception):
    """Raised when output path exists and ``--force`` not set."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def _collect_file_entries(
    selection: list[tuple[Path, str]],
    extra_embedded: list[tuple[str, bytes]] | None,
) -> tuple[list[dict], int]:
    """Build sorted files[] entries + total_bytes from selection + extra_embedded."""
    files: list[dict] = []
    total = 0
    for src, arc in selection:
        if src.is_symlink() or not src.is_file():
            continue
        size = src.stat().st_size
        total += size
        files.append({"path": arc, "size": size, "sha256": _sha256_file(src)})
    # Rendered/generated embedded files (upgrade.sh, _upgrade/*.py …).
    # MANIFEST.json itself is excluded (self-referential; hash unknowable at build time).
    for arc, content in (extra_embedded or []):
        if arc.endswith("/MANIFEST.json"):
            continue
        size = len(content)
        total += size
        files.append({"path": arc, "size": size, "sha256": _sha256_bytes(content)})
    files.sort(key=lambda f: f["path"])
    return files, total


def build_manifest_json(
    selection: list[tuple[Path, str]],
    bundle: dict,
    *,
    source_date_epoch: int,
    repo_root: Path,
    extra_embedded: list[tuple[str, bytes]] | None = None,
) -> bytes:
    """Build the embedded ``MANIFEST.json`` payload (sorted by arcname).

    ``extra_embedded``: optional (arcname, bytes) pairs for files rendered at
    build time (install.sh, upgrade.sh, _upgrade/*.py). Included in files[]
    for integrity. MANIFEST.json itself is excluded (self-referential).
    """
    files, total_bytes = _collect_file_entries(selection, extra_embedded)
    # source_date_epoch <=0 → epoch (1970-01-01T00:00:00+00:00) for reproducibility.
    epoch = source_date_epoch if source_date_epoch and source_date_epoch > 0 else 0
    built_at = datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="seconds")
    source_commit = _git_command(["rev-parse", "HEAD"], repo_root) or "unknown"
    _raw_repo = _git_command(["remote", "get-url", "origin"], repo_root)
    # Strip user:token@ from HTTPS origins before embedding — never leak credentials.
    # scp-style git@host:org/repo is NOT stripped (the username is the SSH alias,
    # not a secret; stripping makes source_repo unresolvable).
    source_repo = re.sub(r"(://)[^/]*@", r"\1", _raw_repo)
    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "bundle_name": bundle.get("bundle_name", "product-spec"),
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
        if e.errno == errno.EXDEV:
            # Cross-fs fallback. If the move ALSO fails, restore the backup and
            # drop the tmp before re-raising — mirror the non-EXDEV path so the
            # user's output is never left only as a .bak.{epoch} with final absent.
            try:
                shutil.move(str(tmp), str(final))
            except OSError as move_err:
                tmp.unlink(missing_ok=True)
                if backup is not None and backup.exists():
                    try:
                        backup.rename(final)
                    except OSError as restore_err:
                        raise OSError(
                            f"{move_err}; restore failed ({restore_err}); "
                            f"previous output preserved at {backup}"
                        ) from move_err
                raise
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
