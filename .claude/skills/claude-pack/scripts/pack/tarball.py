"""tarball — deterministic tar.gz writer for cleanmatic:claude-pack.

Determinism knobs:
- PAX format
- File-granular sorted walk (NOT ``tar.add(directory)``)
- ``mtime=0`` (or ``SOURCE_DATE_EPOCH``)
- ``uid=gid=0``, ``uname=gname=""``
- Gzip header ``mtime=0`` (verified at byte 4-7 by the test suite)
"""

from __future__ import annotations

import gzip
import hashlib
import io
import sys
import tarfile
from pathlib import Path

import safety_check  # type: ignore[import-not-found]


_LOG_STREAM = sys.stderr


def _log_warn(msg: str) -> None:
    _LOG_STREAM.write(f"WARN: {msg}\n")


def make_normalize_filter(source_date_epoch: int):
    """Return a tarfile filter that:

    1. Rejects symlinks/hardlinks unconditionally.
    2. Drops any path that ``safety_check.is_dropped`` flags.
    3. Normalizes metadata for byte-identical reproducibility.
    """

    def _filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if tarinfo.issym() or tarinfo.islnk():
            _log_warn(f"dropped symlink {tarinfo.name} -> {tarinfo.linkname}")
            return None

        # Defense-in-depth: safety_check.is_dropped now catches traversal/absolute
        # as its first rule, but be explicit here so the filter is self-sufficient.
        dropped, rule = safety_check.is_dropped(tarinfo.name)
        if dropped:
            _log_warn(f"dropped {tarinfo.name} (rule: {rule})")
            return None

        tarinfo.mtime = source_date_epoch
        tarinfo.uid = 0
        tarinfo.gid = 0
        tarinfo.uname = ""
        tarinfo.gname = ""
        if tarinfo.isdir():
            tarinfo.mode = 0o755
        elif tarinfo.isfile():
            tarinfo.mode = 0o644
        return tarinfo

    return _filter


def _add_bytes(tar: tarfile.TarFile, arcname: str, payload: bytes,
               filter_fn) -> None:
    info = tarfile.TarInfo(name=arcname)
    info.size = len(payload)
    info.mtime = 0
    info.mode = 0o644
    info.type = tarfile.REGTYPE
    info = filter_fn(info)
    if info is None:
        return
    tar.addfile(info, io.BytesIO(payload))


def _add_file(tar: tarfile.TarFile, src: Path, arcname: str, filter_fn) -> None:
    info = tar.gettarinfo(str(src), arcname=arcname)
    info = filter_fn(info)
    if info is None:
        return
    if info.isfile():
        with src.open("rb") as f:
            tar.addfile(info, f)
    else:
        tar.addfile(info)


def build_tarball(
    selection: list[tuple[Path, str]],
    embedded_files: list[tuple[str, bytes]],
    out_stream,
    *,
    source_date_epoch: int = 0,
) -> str:
    """Write a deterministic tar.gz to ``out_stream`` (a binary file-like).

    Args:
        selection: ``[(src_path, arcname), ...]`` sorted by ``arcname.encode("utf-8")``.
        embedded_files: ``[(arcname, payload_bytes), ...]`` written first
            (MANIFEST.json, INSTALL.md, install.sh, install.ps1). Sorted by caller.
        out_stream: open binary file-like (file or ``BytesIO``).
        source_date_epoch: mtime value for every entry (default 0).

    Returns:
        SHA256 hex digest of the produced tar.gz bytes.
    """
    filter_fn = make_normalize_filter(source_date_epoch)

    sha = hashlib.sha256()

    class _ShaSink:
        def __init__(self, sink):
            self._sink = sink

        def write(self, data: bytes) -> int:
            sha.update(data)
            return self._sink.write(data)

        def flush(self) -> None:
            self._sink.flush()

    sha_wrapper = _ShaSink(out_stream)
    gz = gzip.GzipFile(fileobj=sha_wrapper, mode="wb", mtime=0, compresslevel=9)
    try:
        tar = tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT)
        try:
            for arcname, payload in embedded_files:
                _add_bytes(tar, arcname, payload, filter_fn)
            for src, arcname in selection:
                if not src.exists():
                    _log_warn(f"selection source missing: {src}")
                    continue
                _add_file(tar, src, arcname, filter_fn)
        finally:
            tar.close()
    finally:
        gz.close()

    return sha.hexdigest()


def verify_gzip_mtime_zero(tar_path: Path) -> bool:
    """Return ``True`` iff bytes [4:8] of ``tar_path`` are zero (gzip mtime=0)."""
    with tar_path.open("rb") as f:
        head = f.read(8)
    return len(head) >= 8 and head[4:8] == b"\x00\x00\x00\x00"
