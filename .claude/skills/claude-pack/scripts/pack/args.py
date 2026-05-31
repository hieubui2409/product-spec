"""args — argparse setup for ``python -m pack``.

Pulled out of ``cli.py`` to keep cli.py under the 200-LOC budget.
``BooleanOptionalAction(default=None)`` is non-negotiable for the
manifest-vs-CLI precedence rule.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def _add_bool(parser: argparse.ArgumentParser, name: str, help_text: str) -> None:
    parser.add_argument(f"--{name.replace('_', '-')}", dest=name,
                        action=argparse.BooleanOptionalAction,
                        default=None, help=help_text)


def _nonneg_int(s: str) -> int:
    v = int(s)
    if v < 0:
        raise argparse.ArgumentTypeError("--max-size must be >= 0")
    return v


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pack",
        description="Build a deterministic claude-pack tarball.",
    )
    p.add_argument("--root", type=Path, default=Path.cwd(),
                   help="repo root (default: cwd)")
    p.add_argument("--manifest", type=Path, default=None,
                   help="manifest YAML (default: .claude/pack.manifest.yaml)")
    p.add_argument("--version", default=None, help="override manifest.version")
    p.add_argument("--bundle-name", dest="bundle_name", default=None,
                   help="override manifest.bundle_name")
    p.add_argument("--out", type=Path, default=Path("dist"),
                   help="output directory (default: dist/)")
    p.add_argument("--all", action="store_true",
                   help="pack everything under .claude/ minus always-drop list")
    p.add_argument("--skills", default=None, help="comma-separated skill slugs")
    p.add_argument("--agents", default=None, help="comma-separated agent basenames")
    p.add_argument("--hooks", default=None, help="comma-separated hook filenames")
    p.add_argument("--rules", default=None, help="comma-separated rule filenames")
    p.add_argument("--extra", default=None,
                   help="comma-separated repo-relative paths (no abs, no ..)")
    p.add_argument("--include-shared", dest="include_shared", default=None,
                   help="comma-separated _shared/<name> to include (opt-in)")
    _add_bool(p, "include_readme", "include repo-root README.md")
    _add_bool(p, "include_claudemd", "include repo-root CLAUDE.md")
    _add_bool(p, "include_settings", "include .claude/settings.json")
    _add_bool(p, "include_ck_config", "include .claude/.ck.json")
    _add_bool(p, "include_scripts", "include .claude/scripts (CK-framework; opt-in)")
    _add_bool(p, "include_schemas", "include .claude/schemas (CK-framework; opt-in)")
    _add_bool(p, "follow_shared",
              "warn-only _shared/ refs (false = warn, true = include)")
    _add_bool(p, "force", "overwrite existing output (backup as .bak.{epoch})")
    _add_bool(p, "dry_run", "list files + size; no tarball write")
    _add_bool(p, "compute_sha", "with --dry-run: include would-be SHA256")
    _add_bool(p, "json", "emit JSON status to stdout (machine-parseable)")
    p.add_argument("--source-date-epoch", dest="source_date_epoch", default=None,
                   help="mtime root: integer epoch, 'env' to honor "
                        "SOURCE_DATE_EPOCH, default 0 (deterministic)")
    p.add_argument("--max-size", dest="max_size", type=_nonneg_int, default=None,
                   help="reject if compressed > bytes (default 100MB)")
    p.add_argument("--strict", action="store_true",
                   help="treat warnings as errors")
    p.add_argument("--allow-dev-version", action="store_true",
                   help="allow 0.0.0-dev placeholder version")
    return p


# 9999-12-31T23:59:59Z — the ceiling datetime.fromtimestamp(.., utc) accepts.
# A larger epoch raises OverflowError/OSError deep in manifest_io; bound it here.
_MAX_EPOCH = 253402300799


def resolve_epoch(args: argparse.Namespace) -> int:
    val = args.source_date_epoch
    if val is None:
        return 0
    if val == "env":
        env = os.environ.get("SOURCE_DATE_EPOCH")
        # Guard against unicode-digit strings: str.isdigit() returns True for
        # chars like '²' but int() raises ValueError on them.  Require ASCII.
        # An out-of-range value falls back to 0 (env is ambient provenance).
        if env and env.isascii() and env.isdigit():
            n = int(env)
            return n if 0 <= n <= _MAX_EPOCH else 0
        return 0
    try:
        n = int(val)
    except ValueError:
        raise SystemExit(f"--source-date-epoch must be int or 'env'; got {val!r}")
    if n < 0:
        raise SystemExit("--source-date-epoch must be >= 0")
    if n > _MAX_EPOCH:
        raise SystemExit(f"--source-date-epoch must be <= {_MAX_EPOCH} (year 9999); got {n}")
    return n
