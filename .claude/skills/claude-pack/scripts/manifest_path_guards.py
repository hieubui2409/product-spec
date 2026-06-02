"""manifest_path_guards — path-safety predicates and slug resolvers for manifest validation.

Provides the low-level checks that manifest_validator.validate() calls for each
path-bearing category (skills, agents, hooks, rules, extra, _include_shared):

- Absolute-path and Windows drive-letter detection.
- Path-traversal detection (``..`` components).
- Per-category entry scanning that emits MANIFEST_E020 / MANIFEST_E021 errors.
- Hook name-to-file resolution shared by validate() and selection.resolve_selection()
  so that a name that passes the gate bundles the same file(s).
- Extension-aware slug resolver for agents/rules (basename → real Path).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from manifest_constants import ManifestError  # type: ignore[import-not-found]


# ---------------------------------------------------------------------------
# Absolute / traversal predicates
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


def check_path_safety(entries: list, label: str, errors: list[str]) -> None:
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


# ---------------------------------------------------------------------------
# Hook resolver — shared by validate() and selection.resolve_selection()
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Extension-aware slug resolver for agents / rules
# ---------------------------------------------------------------------------

def resolve_extension(slug: str, search_root: Path, category: str) -> Path:
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
