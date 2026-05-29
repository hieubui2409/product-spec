"""pipeline — build-stage helpers for pack.cli.

Pulled out of ``cli.py`` to keep it under the 200-LOC budget. These functions
are pure orchestration over tarball/manifest_io/selection; they return data
(and exit-code + payload tuples), leaving all stdout/stderr emission to cli.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
from pathlib import Path

from .manifest_io import (
    CollisionError,
    atomic_replace,
    build_manifest_json,
    filter_findings,
    write_sha256_sidecar,
)
from .selection import render_embedded
from .tarball import build_tarball, verify_gzip_mtime_zero

EXIT_OK = 0
EXIT_COLLISION = 3
EXIT_WRITE = 4
EXIT_EMPTY_OR_OVER_SIZE = 5


def prepare_build(manifest: dict, root: Path, epoch: int, bundle_root: str,
                  selection: list[tuple[Path, str]]
                  ) -> tuple[bytes, list[tuple[str, bytes]], list[tuple[Path, str]]]:
    """Compute MANIFEST.json, render embedded files, and version-prefix the selection."""
    file_count, total_bytes = filter_findings(selection)
    manifest_json = build_manifest_json(
        selection, manifest, source_date_epoch=epoch, repo_root=root,
    )
    parsed = json.loads(manifest_json)
    tokens = {
        "BUNDLE_NAME": manifest["bundle_name"],
        "VERSION": manifest["version"],
        "BUILT_AT": parsed.get("built_at", ""),
        "SOURCE_COMMIT": parsed.get("source_commit", "unknown"),
        "FILE_COUNT": str(file_count),
        "TOTAL_SIZE": f"{total_bytes} bytes",
    }
    versioned = [(src, f"{bundle_root}/{arc}") for src, arc in selection]
    versioned.sort(key=lambda x: x[1].encode("utf-8"))
    skill_root = Path(__file__).resolve().parent.parent.parent
    embedded = render_embedded(
        skill_root, bundle_root_dir=bundle_root,
        manifest_json=manifest_json, tokens=tokens,
    )
    return manifest_json, embedded, versioned


def write_tarball(args: argparse.Namespace, manifest: dict, out_dir: Path,
                  bundle_root: str, versioned: list[tuple[Path, str]],
                  embedded: list[tuple[str, bytes]], epoch: int
                  ) -> tuple[int, dict]:
    """Atomic deterministic write + sidecar. Returns (exit_code, payload)."""
    final_path = out_dir / f"{bundle_root}.tar.gz"
    out_dir.mkdir(parents=True, exist_ok=True)
    # PID + random hex suffix prevents concurrent same-bundle builds from
    # clobbering each other's in-progress tmp files.
    tmp_path = out_dir / f".{bundle_root}.{os.getpid()}.{secrets.token_hex(4)}.tar.gz.tmp"
    try:
        with tmp_path.open("wb") as f:
            tar_sha = build_tarball(versioned, embedded, f, source_date_epoch=epoch)
        # Use explicit None checks so that 0 (reject-all) is honored for both
        # the CLI flag and the manifest field. A falsy `or` chain would silently
        # skip 0 and fall through to the default, which is incorrect.
        cli_max = getattr(args, "max_size", None)
        manifest_max = (manifest.get("defaults") or {}).get("max_size_bytes", None)
        if cli_max is not None:
            max_size = cli_max
        elif manifest_max is not None:
            max_size = manifest_max
        else:
            max_size = 100 * 1024 * 1024
        actual_size = tmp_path.stat().st_size
        if actual_size > max_size:
            tmp_path.unlink(missing_ok=True)
            return EXIT_EMPTY_OR_OVER_SIZE, {
                "error": f"over max size: {actual_size} > {max_size}"
            }
        atomic_replace(tmp_path, final_path, force=bool(args.force))
    except CollisionError as e:
        tmp_path.unlink(missing_ok=True)
        return EXIT_COLLISION, {"error": str(e)}
    except OSError as e:
        tmp_path.unlink(missing_ok=True)
        return EXIT_WRITE, {"error": f"write error: {e}"}

    sidecar = write_sha256_sidecar(final_path)
    file_count, total_bytes = filter_findings(versioned)
    return EXIT_OK, {
        "bundle_root": bundle_root,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "output_path": str(final_path),
        "sha256": tar_sha,
        "sidecar": str(sidecar),
        "gzip_mtime_zero": verify_gzip_mtime_zero(final_path),
    }
