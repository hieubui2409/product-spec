"""manifest_loader — parse, merge, validate, and resolve defaults for
``.claude/pack.manifest.yaml``.

API surface:
- ``load(path) -> dict``
- ``merge_cli(manifest, cli) -> dict``
- ``validate(manifest, root) -> list[str]``
- ``apply_defaults(manifest, root) -> dict``
- ``ManifestError`` exception

Pure stdlib + pyyaml. Does NOT call AskUserQuestion (that is the LLM layer).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

DEFAULT_SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

SEMVER_RE = re.compile(
    r"^(?:(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?|0\.0\.0-dev)$"
)
BUNDLE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")

ALLOWED_TOP_LEVEL_KEYS = frozenset({
    "schema_version", "version", "bundle_name",
    "skills", "agents", "hooks", "rules", "extra",
    "top_level", "defaults", "follow_shared",
})

ALLOWED_NESTED_TOP_LEVEL_KEYS = frozenset({
    "include_readme", "include_claudemd",
    "include_settings", "include_ck_config",
})

# Opt-in flags that set defaults.include_scripts / defaults.include_schemas to True
# when passed on the CLI. Absent from manifest ⇒ False (top-level .claude/scripts and
# .claude/schemas are CK-framework internals, not skill content; skill scripts live
# under skills/<x>/scripts/).
OPT_IN_DEFAULTS_FLAGS = frozenset({"include_scripts", "include_schemas"})

ALLOWED_DEFAULTS_KEYS = frozenset({
    "include_scripts", "include_schemas", "max_size_bytes",
})

LIST_CATEGORIES = ("skills", "agents", "hooks", "rules", "extra")


class ManifestError(Exception):
    """Raised on parse failure or validation error.

    Carries ``file:line:col`` when available (yaml parse errors).
    """


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# merge_cli
# ---------------------------------------------------------------------------

def _split_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items = [str(x) for x in value]
    else:
        items = [s.strip() for s in str(value).split(",") if s.strip()]
    return list(dict.fromkeys(items))


def _as_list(value: Any) -> list:
    """A list as-is, anything else as []. A malformed scalar category (already
    flagged E010) must never be iterated — that would TypeError on an int or
    char-split a bare string into phantom single-char slugs."""
    return value if isinstance(value, list) else []


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


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def _is_absolute_or_drive(p: str) -> bool:
    if not p:
        return False
    # POSIX absolute, or Windows UNC / backslash-rooted path.
    if p.startswith("/") or p.startswith("\\"):
        return True
    # Windows drive letter: ``C:\foo``, ``C:/foo``, or bare ``C:``
    # Require: letter at index 0, colon at index 1, then either end-of-string
    # or a slash/backslash separator. This excludes POSIX paths like ``a:b``
    # (colon at index 1 but followed by a non-separator character).
    if len(p) >= 2 and p[0].isalpha() and p[1] == ":" and (len(p) == 2 or p[2] in "/\\"):
        return True
    return False


def _has_traversal(p: str) -> bool:
    return ".." in PurePosixPath(p.replace("\\", "/")).parts


def _check_path_safety(entries: list, label: str, errors: list[str]) -> None:
    """Validate each path entry in ``entries`` for absolute / traversal patterns.

    Emits ``MANIFEST_E020`` (absolute) or ``MANIFEST_E021`` (traversal) into
    ``errors``.  Non-string entries are skipped (caught upstream by E011).
    Called for each path-bearing category so the check is defined once.

    A non-list ``entries`` (a malformed scalar category — already flagged E010)
    is a no-op: never iterate an int (TypeError) or char-split a bare string.
    """
    if not isinstance(entries, list):
        return
    for path_entry in entries:
        if not isinstance(path_entry, str):
            continue
        if _is_absolute_or_drive(path_entry):
            errors.append(
                f"[MANIFEST_E020] absolute paths not allowed in {label}: {path_entry!r}"
            )
        if _has_traversal(path_entry):
            errors.append(
                f"[MANIFEST_E021] path traversal not allowed in {label}: {path_entry!r}"
            )


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

    bundle_name = manifest.get("bundle_name", "claude-pack")
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
        _check_path_safety(manifest.get(category, []) or [], category, errors)

    _check_path_safety(manifest.get("extra", []) or [], "extra", errors)

    # _include_shared is a `_`-prefixed key exempt from the unknown-key check, but
    # traversal in shared slugs would produce arcnames outside the extraction dir.
    # A non-list value (hand-edited scalar) would char-split downstream — flag it
    # E010 like the public list categories and treat as [] for the rest of this
    # pass so neither path-safety here nor the _shared resolution below char-splits.
    shared_val = manifest.get("_include_shared", []) or []
    if not isinstance(shared_val, list):
        errors.append(f"[MANIFEST_E010] _include_shared must be a list, got {type(shared_val).__name__}")
        shared_val = []
    _check_path_safety(shared_val, "_include_shared", errors)

    top_level = manifest.get("top_level", {}) or {}
    if not isinstance(top_level, dict):
        errors.append(f"[MANIFEST_E030] top_level must be a mapping, got {type(top_level).__name__}")
    else:
        for key in top_level:
            if key not in ALLOWED_NESTED_TOP_LEVEL_KEYS:
                errors.append(f"[MANIFEST_E031] unknown top_level key: {key!r}")
        for key in ALLOWED_NESTED_TOP_LEVEL_KEYS:
            if key in top_level and not isinstance(top_level[key], bool):
                errors.append(
                    f"[MANIFEST_E032] top_level.{key} must be bool; got {top_level[key]!r}"
                )

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

    # On-disk existence (case-sensitive) + resolve-within-base containment.
    # The traversal check above catches '../../x' syntactically; here we also
    # resolve symlinks and verify the real path stays within the category base,
    # catching symlink-based escapes.  We use pathlib's relative_to() instead of
    # a string-prefix test so the check is separator-agnostic (avoids false E021
    # on Windows builders where Path.__str__ uses '\\').
    claude_dir = root / ".claude"
    skills_base = (claude_dir / "skills").resolve()
    for slug in _as_list(manifest.get("skills")):
        if not isinstance(slug, str):
            continue
        skill_dir = claude_dir / "skills" / slug
        if not skill_dir.is_dir():
            errors.append(f"[MANIFEST_E070] missing skill: {slug}")
        else:
            try:
                resolved_skill = skill_dir.resolve()
                resolved_skill.relative_to(skills_base)
            except ValueError:
                errors.append(
                    f"[MANIFEST_E021] skill path escapes skills base: {slug!r}"
                )
            except OSError:
                pass  # broken symlink; E070 will catch missing dir

    for slug in _as_list(manifest.get("agents")):
        if isinstance(slug, str):
            try:
                resolved_agent = _resolve_extension(slug, claude_dir / "agents", "agents")
                try:
                    agents_base = (claude_dir / "agents").resolve()
                    resolved_agent.resolve().relative_to(agents_base)
                except ValueError:
                    errors.append(f"[MANIFEST_E021] agent path escapes agents base: {slug!r}")
                except OSError:
                    pass
            except ManifestError as e:
                errors.append(f"[MANIFEST_E071] {e}")

    for slug in _as_list(manifest.get("rules")):
        if isinstance(slug, str):
            try:
                resolved_rule = _resolve_extension(slug, claude_dir / "rules", "rules")
                try:
                    rules_base = (claude_dir / "rules").resolve()
                    resolved_rule.resolve().relative_to(rules_base)
                except ValueError:
                    errors.append(f"[MANIFEST_E021] rule path escapes rules base: {slug!r}")
                except OSError:
                    pass
            except ManifestError as e:
                errors.append(f"[MANIFEST_E072] {e}")

    for slug in _as_list(manifest.get("hooks")):
        if isinstance(slug, str):
            # Must match a FILE (a slug naming a directory would pass a bare
            # rglob existence test yet bundle nothing). >1 match is ambiguous:
            # rglob order is filesystem-dependent, so picking one silently would
            # make the tarball non-deterministic across machines. Use the SHARED
            # matcher so this gate and selection.resolve_selection agree on which
            # file(s) a name resolves to (a name that validates here is the same
            # set that gets bundled).
            hook_matches = match_hooks(claude_dir, slug)
            if not hook_matches:
                errors.append(f"[MANIFEST_E073] missing hook: {slug}")
            elif len(hook_matches) > 1:
                errors.append(
                    f"[MANIFEST_E074] ambiguous hook: {slug} matches "
                    f"{len(hook_matches)} files; use a unique name or path"
                )
            else:
                # Containment check for hooks as well.
                try:
                    hooks_base = (claude_dir / "hooks").resolve()
                    hook_matches[0].resolve().relative_to(hooks_base)
                except ValueError:
                    errors.append(
                        f"[MANIFEST_E021] hook path escapes hooks base: {slug!r}"
                    )
                except OSError:
                    pass

    # _include_shared: verify each slug stays within .claude/skills/_shared/.
    # `shared_val` was already type-checked (E010) + coerced to a list above, so a
    # hand-edited scalar can't char-split here.
    shared_base = (claude_dir / "skills" / "_shared").resolve()
    for slug in shared_val:
        if not isinstance(slug, str):
            continue
        shared_dir = claude_dir / "skills" / "_shared" / slug
        if shared_dir.exists():
            try:
                shared_dir.resolve().relative_to(shared_base)
            except ValueError:
                errors.append(
                    f"[MANIFEST_E021] _include_shared path escapes shared base: {slug!r}"
                )
            except OSError:
                pass

    return errors


def match_hooks(claude_dir: Path, name: str) -> list[Path]:
    """Resolve a manifest hook NAME to matching files — the ONE matcher shared by
    validate() (the missing/ambiguous gate) and selection.resolve_selection (the
    bundling step), so a name that passes validation bundles exactly the same
    file(s). `rglob(name)` matches a bare basename, a path-relative fragment
    (`a/foo.cjs`), or a glob (`*.sh`) identically on both call sites; the result is
    sorted for a deterministic pick. (Replaces C5's basename-only index in
    selection, which diverged from this rglob gate and silently dropped a
    path-qualified/glob hook that had passed validation.)"""
    hooks_dir = claude_dir / "hooks"
    if not hooks_dir.is_dir():
        return []
    return sorted((p for p in hooks_dir.rglob(name) if p.is_file()), key=lambda p: p.as_posix())


def _resolve_extension(slug: str, search_root: Path, category: str) -> Path:
    """Resolve a basename -> real Path under ``search_root``.

    If ``slug`` has no extension, append ``.md``. Multiple matches -> ``ManifestError``.
    """
    if not search_root.is_dir():
        raise ManifestError(f"missing {category}: {slug} (search root absent)")
    candidate = slug if "." in PurePosixPath(slug).name else f"{slug}.md"
    matches = [p for p in search_root.rglob(candidate) if p.is_file()]
    if len(matches) == 0:
        raise ManifestError(f"missing {category}: {slug}")
    if len(matches) > 1:
        rels = sorted(str(p.relative_to(search_root)) for p in matches)
        raise ManifestError(f"ambiguous {category}: {slug} matches {rels}")
    return matches[0]


# ---------------------------------------------------------------------------
# apply_defaults
# ---------------------------------------------------------------------------

def apply_defaults(manifest: dict, root: Path) -> dict:
    """Fill missing top-level keys + auto-add default-ship subtrees to ``extra``."""
    out = dict(manifest)
    out.setdefault("schema_version", DEFAULT_SCHEMA_VERSION)
    out.setdefault("bundle_name", "claude-pack")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="claude-pack manifest loader/validator")
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
