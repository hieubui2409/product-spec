"""cli — dispatch for ``python -m pack``. Argparse lives in ``args.py``."""

from __future__ import annotations

import argparse
import io
import json
import signal
import sys
from pathlib import Path

import manifest_loader  # type: ignore[import-not-found]
import safety_check  # type: ignore[import-not-found]

from .args import build_parser, resolve_epoch
from .manifest_io import cleanup_stale_tmp, filter_findings
from .pipeline import prepare_build, write_tarball
from .selection import resolve_selection
from .tarball import build_tarball
from .templates import TemplateError

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_STRICT = 2
EXIT_EMPTY_OR_OVER_SIZE = 5
EXIT_INTERRUPTED = 130


def _emit(args: argparse.Namespace, payload: dict, *, fp=sys.stdout) -> None:
    if args.json:
        json.dump(payload, fp, indent=2, default=str)
        fp.write("\n")
    else:
        for k, v in payload.items():
            fp.write(f"{k}: {v}\n")


def _warn_shared_refs(manifest: dict, root: Path) -> int:
    """Emit a WARN per un-included _shared/ reference. Returns the count."""
    skill_dirs = [root / ".claude/skills" / s for s in manifest.get("skills", [])
                  if (root / ".claude/skills" / s).is_dir()]
    include_shared = set(manifest.get("_include_shared") or [])
    count = 0
    for ref, skill_id in safety_check.find_shared_refs(skill_dirs):
        if ref not in include_shared:
            count += 1
            sys.stderr.write(
                f"WARN: skill {skill_id} references _shared/{ref} — "
                f"use --include-shared {ref} to include\n"
            )
    return count


def _load_and_validate(args: argparse.Namespace, root: Path) -> tuple[dict, int]:
    manifest_path = args.manifest or root / ".claude" / "pack.manifest.yaml"
    try:
        manifest = manifest_loader.load(manifest_path)
    except manifest_loader.ManifestError as e:
        _emit(args, {"error": str(e)}, fp=sys.stderr)
        return {}, EXIT_VALIDATION
    manifest = manifest_loader.merge_cli(manifest, args)
    errors = manifest_loader.validate(manifest, root,
                                      allow_dev_version=args.allow_dev_version)
    if errors:
        _emit(args, {"errors": errors}, fp=sys.stderr)
        return {}, EXIT_VALIDATION
    manifest = manifest_loader.apply_defaults(manifest, root)
    return manifest, EXIT_OK


def main(argv: list[str] | None = None) -> int:
    signal.signal(signal.SIGINT, lambda *_: sys.exit(EXIT_INTERRUPTED))
    args = build_parser().parse_args(argv)
    root = args.root.resolve()

    if args.all:
        _emit(args, {"error": "--all is not implemented in v0.1; list skills/agents/"
                              "rules explicitly in the manifest or via flags"},
              fp=sys.stderr)
        return EXIT_VALIDATION

    manifest, rc = _load_and_validate(args, root)
    if rc != EXIT_OK:
        return rc

    selection = resolve_selection(manifest, root)
    if not selection:
        _emit(args, {"error": "nothing to pack (empty selection)"}, fp=sys.stderr)
        return EXIT_EMPTY_OR_OVER_SIZE

    shared_warn_count = _warn_shared_refs(manifest, root)
    if args.strict and shared_warn_count:
        _emit(args, {"error": f"--strict: {shared_warn_count} un-included _shared/ "
                              f"reference(s); pass --include-shared or drop --strict"},
              fp=sys.stderr)
        return EXIT_STRICT

    bundle_name = manifest["bundle_name"]
    version = manifest["version"]
    bundle_root = f"{bundle_name}-{version}"
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cleanup_stale_tmp(out_dir)
    epoch = resolve_epoch(args)

    try:
        _, embedded, versioned = prepare_build(
            manifest, root, epoch, bundle_root, selection,
        )
    except TemplateError as e:
        _emit(args, {"error": str(e)}, fp=sys.stderr)
        return EXIT_VALIDATION

    if args.dry_run:
        file_count, total_bytes = filter_findings(selection)
        payload: dict = {
            "bundle_root": bundle_root,
            "file_count": file_count,
            "total_bytes": total_bytes,
            "output_path": str(out_dir / f"{bundle_root}.tar.gz"),
        }
        if args.compute_sha:
            payload["would_be_sha256"] = build_tarball(
                versioned, embedded, io.BytesIO(), source_date_epoch=epoch,
            )
        _emit(args, payload)
        return EXIT_OK

    rc, payload = write_tarball(args, manifest, out_dir, bundle_root,
                                versioned, embedded, epoch)
    fp = sys.stdout if rc == EXIT_OK else sys.stderr
    _emit(args, payload, fp=fp)
    return rc


if __name__ == "__main__":
    sys.exit(main())
