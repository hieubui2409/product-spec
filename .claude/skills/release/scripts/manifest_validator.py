"""manifest_validator — structural validation of a parsed manifest dict.

The single public entry point is ``validate(manifest, root)``, which runs every
hardened schema check and returns a list of error strings, each with a stable
``[MANIFEST_Exxx]`` code.  Analytical contract: always returns a list (never
raises); exits 0 is the caller's responsibility.

Depends on:
- manifest_constants      — schema enums + ManifestError
- manifest_path_guards    — syntactic path-safety predicates
- manifest_on_disk_checks — filesystem existence + containment checks
"""

from __future__ import annotations

from pathlib import Path

from manifest_constants import (  # type: ignore[import-not-found]
    ALLOWED_DEFAULTS_KEYS,
    ALLOWED_NESTED_TOP_LEVEL_KEYS,
    ALLOWED_TOP_LEVEL_KEYS,
    BUNDLE_NAME_RE,
    DEFAULT_SCHEMA_VERSION,
    LIST_CATEGORIES,
    SEMVER_RE,
    SUPPORTED_SCHEMA_VERSIONS,
)
from manifest_on_disk_checks import validate_on_disk  # type: ignore[import-not-found]
from manifest_path_guards import check_path_safety  # type: ignore[import-not-found]


def _as_list(value: object) -> list:
    """A list as-is, anything else as []. A malformed scalar category (already
    flagged E010) must never be iterated — that would TypeError on an int or
    char-split a bare string into phantom single-char slugs."""
    return value if isinstance(value, list) else []


def validate(manifest: dict, root: Path, allow_dev_version: bool = False) -> list[str]:
    """Run all hardened checks. Returns list of error strings (each with stable code)."""
    errors: list[str] = []

    schema_version = manifest.get("schema_version", DEFAULT_SCHEMA_VERSION)
    if not isinstance(schema_version, str):
        errors.append(
            f"[MANIFEST_E102] schema_version must be a string; got {type(schema_version).__name__}"
        )
    elif schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"[MANIFEST_E101] unsupported schema_version: {schema_version!r}; "
            f"this builder supports {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )

    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(
            f"[MANIFEST_E001] version must match SemVer 2.0.0 or be '0.0.0-dev'; got {version!r}"
        )
    elif version == "0.0.0-dev" and not allow_dev_version:
        errors.append(
            "[MANIFEST_E002] refuse to build with placeholder version '0.0.0-dev'; "
            "pass --allow-dev-version or set a real version"
        )

    bundle_name = manifest.get("bundle_name", "product-spec")
    if not isinstance(bundle_name, str) or not BUNDLE_NAME_RE.match(bundle_name):
        errors.append(
            f"[MANIFEST_E003] bundle_name has invalid characters (must match "
            f"[a-zA-Z0-9][a-zA-Z0-9._-]*); got {bundle_name!r}"
        )

    for category in LIST_CATEGORIES:
        value = manifest.get(category, [])
        if not isinstance(value, list):
            errors.append(f"[MANIFEST_E010] {category} must be a list, got {type(value).__name__}")
            continue
        for item in value:
            if not isinstance(item, str) or not item.strip():
                errors.append(f"[MANIFEST_E011] {category} entry must be non-empty string; got {item!r}")
        # Duplicate detection: compare only string entries to avoid TypeError on
        # unhashable elements (lists/dicts); non-strings are already caught by E011.
        strs = [i for i in value if isinstance(i, str)]
        if len(set(strs)) != len(strs):
            errors.append(f"[MANIFEST_E012] duplicate entries in {category}")

    # Traversal/absolute checks for ALL path-bearing categories (not just extra).
    # skills/agents/rules/hooks use slug resolution but a traversal slug like
    # '../../x' would produce an arcname outside the extraction dir (tar-slip).
    for category in ("skills", "agents", "rules", "hooks"):
        check_path_safety(manifest.get(category, []) or [], category, errors)

    check_path_safety(manifest.get("extra", []) or [], "extra", errors)

    # _include_shared is a `_`-prefixed key exempt from the unknown-key check, but
    # traversal in shared slugs would produce arcnames outside the extraction dir.
    # A non-list value (hand-edited scalar) would char-split downstream — flag it
    # E010 like the public list categories and treat as [] for the rest of this
    # pass so neither path-safety here nor the _shared resolution below char-splits.
    shared_val = manifest.get("_include_shared", []) or []
    if not isinstance(shared_val, list):
        errors.append(f"[MANIFEST_E010] _include_shared must be a list, got {type(shared_val).__name__}")
        shared_val = []
    check_path_safety(shared_val, "_include_shared", errors)

    top_level = manifest.get("top_level", {}) or {}
    if not isinstance(top_level, dict):
        errors.append(f"[MANIFEST_E030] top_level must be a mapping, got {type(top_level).__name__}")
    else:
        for key in top_level:
            if key not in ALLOWED_NESTED_TOP_LEVEL_KEYS:
                errors.append(f"[MANIFEST_E031] unknown top_level key: {key!r}")
        # Bool flags — all keys except `source` must be bool.
        bool_keys = ALLOWED_NESTED_TOP_LEVEL_KEYS - {"source"}
        for key in bool_keys:
            if key in top_level and not isinstance(top_level[key], bool):
                errors.append(
                    f"[MANIFEST_E032] top_level.{key} must be bool; got {top_level[key]!r}"
                )
        # `source` must be a non-empty string when present, AND a repo-relative
        # path. selection.py resolves it as `root / source` and ships files from
        # there; an absolute path or `..` traversal would let the bundle pull docs
        # from outside the repo. Reject those at validate-time (E020/E021) rather
        # than relying on selection.py's downstream WARN-and-skip mitigation.
        if "source" in top_level:
            src_val = top_level["source"]
            if not isinstance(src_val, str) or not src_val.strip():
                errors.append(
                    f"[MANIFEST_E033] top_level.source must be a non-empty string; got {src_val!r}"
                )
            else:
                check_path_safety([src_val], "top_level.source", errors)

    defaults = manifest.get("defaults", {}) or {}
    if defaults and not isinstance(defaults, dict):
        errors.append("[MANIFEST_E040] defaults must be a mapping")
    elif isinstance(defaults, dict):
        for key in defaults:
            if key not in ALLOWED_DEFAULTS_KEYS:
                errors.append(f"[MANIFEST_E041] unknown defaults key: {key!r}")
        # Type-check values so a string like "100MB" fails early rather than
        # crashing at runtime with a TypeError during size comparison. bool is
        # a subclass of int, so reject it explicitly: max_size_bytes: false
        # would otherwise pass and then reject every non-empty bundle (> 0).
        if "max_size_bytes" in defaults:
            msb = defaults["max_size_bytes"]
            if isinstance(msb, bool) or not isinstance(msb, int) or msb < 0:
                errors.append(
                    f"[MANIFEST_E042] defaults.max_size_bytes must be int>=0; got {msb!r}"
                )
        for bool_key in ("include_scripts", "include_schemas"):
            if bool_key in defaults and not isinstance(defaults[bool_key], bool):
                errors.append(
                    f"[MANIFEST_E043] defaults.{bool_key} must be bool; "
                    f"got {defaults[bool_key]!r}"
                )

    follow_shared = manifest.get("follow_shared", False)
    if not isinstance(follow_shared, bool):
        errors.append(f"[MANIFEST_E050] follow_shared must be bool; got {type(follow_shared).__name__}")

    for key in manifest:
        if key not in ALLOWED_TOP_LEVEL_KEYS and not key.startswith("_"):
            errors.append(f"[MANIFEST_E060] unknown top-level key: {key!r}")

    validate_on_disk(manifest, root, shared_val, errors)
    return errors
