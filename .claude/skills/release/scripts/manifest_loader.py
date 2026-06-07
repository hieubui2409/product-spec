"""manifest_loader — parse, merge, validate, and resolve defaults for
``.claude/pack.manifest.yaml``.

Public API (all symbols resolve here for callers, tests, monkeypatch targets):
``load`` · ``merge_cli`` · ``validate`` · ``apply_defaults`` · ``match_hooks``
· ``ManifestError`` · ``SEMVER_RE`` · ``BUNDLE_NAME_RE`` · ``LIST_CATEGORIES``

Pure stdlib + pyyaml. Does NOT call AskUserQuestion (that is the LLM layer).
Leaf modules: manifest_constants · manifest_path_guards · manifest_validator
· manifest_on_disk_checks. This file owns load(), merge_cli(), apply_defaults(),
and the CLI entry point.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from manifest_constants import (  # type: ignore[import-not-found]
    ALLOWED_DEFAULTS_KEYS,
    ALLOWED_NESTED_TOP_LEVEL_KEYS,
    ALLOWED_TOP_LEVEL_KEYS,
    BUNDLE_NAME_RE,
    DEFAULT_SCHEMA_VERSION,
    LIST_CATEGORIES,
    OPT_IN_DEFAULTS_FLAGS,
    SEMVER_RE,
    SUPPORTED_SCHEMA_VERSIONS,
    ManifestError,
)
from manifest_path_guards import match_hooks, resolve_extension as _resolve_extension  # type: ignore[import-not-found]
from manifest_validator import validate  # type: ignore[import-not-found]

# -- load --------------------------------------------------------------------

def load(path: Path) -> dict:
    """Load manifest YAML. Returns ``{}`` for empty file.

    Wraps ``yaml.YAMLError`` -> ``ManifestError`` with file:line:col context.

    **Duplicate top-level keys**: ``yaml.safe_load`` follows YAML 1.1 behaviour
    where a duplicate key silently last-wins (the later value overwrites the
    earlier one).  This is a YAML spec grey-area; the behaviour is documented
    here rather than patched (adding a custom loader for a LOW-risk edge case
    would be non-trivial and break other things).  If you see unexpected values,
    check the manifest for duplicate keys.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ManifestError(f"manifest not found: {path}") from e
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        if mark is not None:
            loc = f"{path}:{mark.line + 1}:{mark.column + 1}"
        else:
            loc = str(path)
        raise ManifestError(f"{loc}: {getattr(e, 'problem', str(e))}") from e
    if doc is None:
        return {}
    if not isinstance(doc, dict):
        raise ManifestError(f"{path}: top-level must be a mapping, got {type(doc).__name__}")
    return doc


# -- merge_cli ---------------------------------------------------------------

def _split_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items = [str(x) for x in value]
    else:
        items = [s.strip() for s in str(value).split(",") if s.strip()]
    return list(dict.fromkeys(items))


def merge_cli(manifest: dict, cli: argparse.Namespace) -> dict:
    """Merge CLI overrides into manifest. ``None`` = no override (manifest wins).

    Lists from CLI are split on ``,`` and deduped. Booleans use
    ``BooleanOptionalAction(default=None)`` from pack/args.py.
    """
    merged = dict(manifest)

    for category in LIST_CATEGORIES:
        cli_val = getattr(cli, category, None)
        if cli_val is not None:
            merged[category] = _split_list(cli_val)

    for scalar in ("version", "bundle_name"):
        cli_val = getattr(cli, scalar, None)
        if cli_val is not None:
            merged[scalar] = cli_val

    # top_level booleans
    top = dict(merged.get("top_level") or {})
    for flag in ALLOWED_NESTED_TOP_LEVEL_KEYS:
        cli_val = getattr(cli, flag, None)
        if cli_val is not None:
            top[flag] = bool(cli_val)
    if top:
        merged["top_level"] = top

    follow = getattr(cli, "follow_shared", None)
    if follow is not None:
        merged["follow_shared"] = bool(follow)

    # opt-in shared list (additive — not a manifest field per se)
    include_shared = getattr(cli, "include_shared", None)
    if include_shared:
        merged["_include_shared"] = _split_list(include_shared)

    # --include-scripts / --include-schemas: opt-in flags for CK-framework internals.
    # When passed, set defaults.include_scripts/include_schemas = True.
    # The manifest field still wins if already set; CLI flags only promote to True.
    for opt_flag in OPT_IN_DEFAULTS_FLAGS:
        cli_val = getattr(cli, opt_flag, None)
        if cli_val is not None:  # --include-scripts True / --no-include-scripts False
            defaults = dict(merged.get("defaults") or {})
            defaults[opt_flag] = bool(cli_val)
            merged["defaults"] = defaults

    return merged


# -- apply_defaults ----------------------------------------------------------

def apply_defaults(manifest: dict, root: Path) -> dict:
    """Fill missing top-level keys + auto-add default-ship subtrees to ``extra``."""
    out = dict(manifest)
    out.setdefault("schema_version", DEFAULT_SCHEMA_VERSION)
    out.setdefault("bundle_name", "product-spec")
    for category in LIST_CATEGORIES:
        out.setdefault(category, [])
    out.setdefault("top_level", {})
    out.setdefault("defaults", {})
    out.setdefault("follow_shared", False)

    defaults = out["defaults"] or {}
    extra = list(out.get("extra") or [])

    # Opt-in only: top-level .claude/scripts + .claude/schemas are CK-framework
    # internals (a skill's own scripts live under skills/<slug>/scripts/), so
    # they are NOT auto-shipped. Enable via defaults.include_scripts/_schemas
    # or the --include-scripts/--include-schemas flags.
    if defaults.get("include_scripts", False):
        scripts_rel = ".claude/scripts"
        if (root / scripts_rel).is_dir() and scripts_rel not in extra:
            extra.insert(0, scripts_rel)

    if defaults.get("include_schemas", False):
        schemas_rel = ".claude/schemas"
        if (root / schemas_rel).is_dir() and schemas_rel not in extra:
            extra.insert(0, schemas_rel)

    out["extra"] = extra
    return out


# -- CLI ---------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="release manifest loader/validator")
    parser.add_argument("--manifest", required=True, type=Path,
                        help="path to pack.manifest.yaml")
    parser.add_argument("--root", default=".", type=Path,
                        help="repo root for on-disk checks (default: cwd)")
    parser.add_argument("--resolve", action="store_true",
                        help="apply_defaults after validate")
    parser.add_argument("--allow-dev-version", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = load(args.manifest)
    except ManifestError as e:
        json.dump({"ok": False, "errors": [str(e)]}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0  # analytical scripts always exit 0

    errors = validate(manifest, args.root.resolve(), allow_dev_version=args.allow_dev_version)
    if args.resolve and not errors:
        manifest = apply_defaults(manifest, args.root.resolve())

    json.dump({"ok": not errors, "manifest": manifest, "errors": errors},
              sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
