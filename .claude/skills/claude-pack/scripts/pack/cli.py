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
from .pipeline import prepare_build, resolve_max_size, write_tarball
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


def _packed_skill_dirs(manifest: dict, root: Path) -> list[Path]:
    """Return existing skill directories referenced by manifest."""
    return [
        root / ".claude/skills" / s
        for s in manifest.get("skills", [])
        if (root / ".claude/skills" / s).is_dir()
    ]


def _warn_shared_refs(manifest: dict, root: Path) -> int:
    """Emit a WARN per un-included _shared/ reference. Returns the count."""
    skill_dirs = _packed_skill_dirs(manifest, root)
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

    # When follow_shared is set, discover _shared/ refs from packed skill dirs
    # and union them into _include_shared so resolve_selection bundles them and
    # _warn_shared_refs treats them as covered (no --strict failure).
    if manifest.get("follow_shared"):
        skill_dirs = _packed_skill_dirs(manifest, root)
        found_refs = {ref for ref, _ in safety_check.find_shared_refs(skill_dirs)}
        existing = set(manifest.get("_include_shared") or [])
        manifest["_include_shared"] = sorted(existing | found_refs)

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
    epoch = resolve_epoch(args)

    # FS side-effects (mkdir + stale-tmp cleanup) are skipped under --dry-run:
    # they mutate the filesystem and are not needed for a read-only size/count check.
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        cleanup_stale_tmp(out_dir)

    try:
        _, embedded, versioned = prepare_build(
            manifest, root, epoch, bundle_root, selection,
        )
    except TemplateError as e:
        _emit(args, {"error": str(e)}, fp=sys.stderr)
        return EXIT_VALIDATION

    if args.dry_run:
        file_count, total_bytes = filter_findings(selection)
        # Resolve max_size the same way write_tarball does so --dry-run never
        # reports success for a payload the real run would reject (EXIT 5).
        max_size = resolve_max_size(args, manifest)
        payload: dict = {
            "bundle_root": bundle_root,
            "file_count": file_count,
            "total_bytes": total_bytes,
            "output_path": str(out_dir / f"{bundle_root}.tar.gz"),
            "max_size": max_size,
        }
        if args.compute_sha:
            buf = io.BytesIO()
            payload["would_be_sha256"] = build_tarball(
                versioned, embedded, buf, source_date_epoch=epoch,
            )
            compressed_size = buf.tell()
            payload["over_max_size"] = compressed_size > max_size
        else:
            # over_max_size is null (not False) when --compute-sha is absent:
            # we didn't compress, so we cannot know if the output would exceed
            # max_size.  Callers must not interpret null as a passing verdict.
            payload["over_max_size"] = None
        _emit(args, payload)
        return EXIT_OK

    rc, payload = write_tarball(args, manifest, out_dir, bundle_root,
                                versioned, embedded, epoch)
    fp = sys.stdout if rc == EXIT_OK else sys.stderr
    _emit(args, payload, fp=fp)
    return rc


if __name__ == "__main__":
    sys.exit(main())
