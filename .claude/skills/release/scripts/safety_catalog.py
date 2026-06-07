"""safety_catalog — always-drop catalog and path-classification predicates for release.

Defines every hard-coded drop rule and exposes ``is_dropped`` / ``is_optional``
so that safety_check, pack.selection, and pack.tarball can all import from one
authoritative source.  The rules are non-negotiable: no CLI flag, no manifest
field, no caller override can disable them.

``is_dropped`` is called per entry across three walk loops inside the tarball
pipeline, so the pattern twins (_PATTERNS_LOWER) are pre-computed once at import
rather than re-lowered on every call.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import PurePosixPath

# ---------------------------------------------------------------------------
# Catalog (non-negotiable; secrets + VCS + caches + session state)
# ---------------------------------------------------------------------------

ALWAYS_DROP_EXACT: frozenset[str] = frozenset({
    # Secrets / credentials
    ".env", ".envrc",
    "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
    ".netrc", ".pgpass",
    # Runtime / cache
    "metadata.json",
    ".DS_Store", "Thumbs.db", "desktop.ini",
})

ALWAYS_DROP_DIRS: frozenset[str] = frozenset({
    # VCS
    ".git", ".gitlab", ".hg", ".svn", ".bzr",
    # Runtime caches
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    # Virtualenvs / vendoring
    ".venv", "venv", "node_modules", ".npm", ".yarn",
    # Claude Code runtime state
    ".logs", "session-state", "agent-memory",
    # Internal planning / review reports — never ship to recipients
    "plans",
    # Test suites + their fixtures — dev artifacts, never ship to recipients
    # (matches any path component, so `__tests__/fixtures/` is dropped wholesale).
    "__tests__", "tests",
    # Build artifacts
    "dist", "build", "target", ".next", ".turbo",
})

ALWAYS_DROP_PATTERNS: tuple[str, ...] = (
    # Secrets variants
    "**/.env.*", "**/.env-*", "**/.env_*",
    "**/secrets.*", "**/credentials.*",
    "**/*.pem", "**/*.key", "**/*.p12", "**/*.pfx", "**/*.jks",
    "**/id_rsa*", "**/id_ed25519*", "**/id_ecdsa*", "**/id_dsa*",
    "**/*.kdbx",
    "**/*token*.json", "**/*secret*.json",
    # Python compiled
    "**/*.pyc", "**/*.pyo",
)

# Pre-lowered (full-glob, bare-glob) twins, computed ONCE at import. is_dropped is
# called per entry/file across three walk loops, so the patterns are invariant —
# re-lowering + re-slicing them on every call was redundant. The `bare` form drops
# the leading "**/" so a top-level basename (no slash) still matches.
_PATTERNS_LOWER: tuple[tuple[str, str], ...] = tuple(
    (g.lower(), g.lower()[3:] if g.lower().startswith("**/") else g.lower())
    for g in ALWAYS_DROP_PATTERNS
)

OPT_IN_PATHS: dict[str, str] = {
    ".claude/settings.json": "settings",
    ".claude/.ck.json": "ck-config",
}


class SafetyError(Exception):
    """Raised for unrecoverable safety-rule violations."""


# ---------------------------------------------------------------------------
# Path classification
# ---------------------------------------------------------------------------

def is_dropped(path: str) -> tuple[bool, str | None]:
    """Return (drop?, rule-id) for a candidate arcname.

    All three match layers are case-insensitive so that ``deploy.PEM``,
    ``.ENV``, ``ID_RSA``, and ``.GIT/config`` are caught on case-insensitive
    and case-preserving filesystems alike.

    rule-id format: ``always-drop:exact:<name>`` | ``always-drop:dir:<name>``
    | ``always-drop:pattern:<glob>`` (canonical lowercase rule label).

    Self-sufficient backstop: this function is the LAST line of defense even if
    a new input category bypasses manifest_loader.validate() and
    selection.resolve_selection().  It intentionally duplicates those checks so
    that safety holds under any future refactoring that adds a new input path.
    """
    # Normalize backslashes to forward slashes BEFORE PurePosixPath so that a
    # backslash-encoded traversal like "foo\\..\\bar" is caught by the ".." parts
    # check (PurePosixPath would otherwise treat the whole string as one component).
    normalized = path.replace("\\", "/")
    pp = PurePosixPath(normalized)
    # Defense-in-depth: drop any path that contains a traversal component or is
    # absolute.  The drive-letter check mirrors manifest_loader._is_absolute_or_drive:
    # require letter at index 0, ':' at index 1, then end-of-string or a separator.
    # This avoids over-dropping POSIX arcnames whose 2nd char happens to be ':'.
    is_drive = (
        len(path) >= 2
        and path[0].isalpha()
        and path[1] == ":"
        and (len(path) == 2 or path[2] in "/\\")
    )
    if ".." in pp.parts or normalized.startswith("/") or path.startswith("\\") or is_drive:
        return True, "always-drop:traversal"

    p = pp
    basename = p.name
    basename_lower = basename.lower()

    if basename_lower in ALWAYS_DROP_EXACT:
        return True, f"always-drop:exact:{basename_lower}"

    for part in p.parts:
        if part.lower() in ALWAYS_DROP_DIRS:
            return True, f"always-drop:dir:{part.lower()}"

    path_lower = path.lower()
    # Match the full arcname AND the basename. fnmatch treats the leading ``**/``
    # literally (it needs a real ``/``), so a top-level file with no slash in its
    # arcname (e.g. ``deploy.pem`` added via ``extra``) would otherwise slip past
    # every ``**/``-prefixed secret pattern; matching the bare basename closes
    # that hole. Both operands are pre-lowered (case-insensitive); the pattern
    # twins are precomputed at import (see _PATTERNS_LOWER).
    for glob_lower, bare_lower in _PATTERNS_LOWER:
        if fnmatch.fnmatchcase(path_lower, glob_lower) or fnmatch.fnmatchcase(basename_lower, bare_lower):
            return True, f"always-drop:pattern:{glob_lower}"

    return False, None


def is_optional(path: str) -> tuple[bool, str | None]:
    """Return (opt-in?, label) for paths that need CLI flags to include.

    Match against ``OPT_IN_PATHS`` keys with arcname-suffix anchor: ``path == key``
    or ``path.endswith("/" + key)``.
    """
    for key, label in OPT_IN_PATHS.items():
        if path == key or path.endswith("/" + key):
            return True, label
    return False, None
