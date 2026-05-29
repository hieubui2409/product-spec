"""safety_check — non-negotiable filter for cleanmatic:claude-pack.

Three layers of "always-drop" rules + an opt-in catalog + a warn-only
detector for cross-skill `_shared/` references. These rules are HARD:
no CLI flag, no manifest field, no override disables them.

Imported by pack.cli; standalone CLI emits JSON findings.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

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

OPT_IN_PATHS: dict[str, str] = {
    ".claude/settings.json": "settings",
    ".claude/.ck.json": "ck-config",
}

# Lowercase enforced; uppercase _shared/Foo silently skipped (documented).
# Captures the first path segment after _shared/, so inclusion is dir-granular:
# a reference to _shared/references/x.md pulls the whole _shared/references/ dir.
SHARED_REF_RE = re.compile(r"_shared/([a-z0-9_-]+)")

_FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)


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
    """
    p = PurePosixPath(path)
    basename = p.name
    basename_lower = basename.lower()

    if basename_lower in ALWAYS_DROP_EXACT:
        return True, f"always-drop:exact:{basename_lower}"

    for part in p.parts:
        if part.lower() in ALWAYS_DROP_DIRS:
            return True, f"always-drop:dir:{part.lower()}"

    path_lower = path.lower()
    for glob in ALWAYS_DROP_PATTERNS:
        # Match the full arcname AND the basename. fnmatch treats the leading
        # ``**/`` literally (it needs a real ``/``), so a top-level file with no
        # slash in its arcname (e.g. ``deploy.pem`` added via ``extra``) would
        # otherwise slip past every ``**/``-prefixed secret pattern. Stripping
        # the ``**/`` and matching the basename closes that hole.
        # Both operands are pre-lowered so matching is case-insensitive.
        glob_lower = glob.lower()
        bare_lower = glob_lower[3:] if glob_lower.startswith("**/") else glob_lower
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


# ---------------------------------------------------------------------------
# Cross-skill _shared/ reference detection (warn-only)
# ---------------------------------------------------------------------------

def _strip_fenced_blocks(text: str) -> str:
    """Remove ```...``` fenced code blocks before regex match."""
    return _FENCED_BLOCK_RE.sub("", text)


def find_shared_refs(skill_dirs: list[Path]) -> list[tuple[str, str]]:
    """Grep SKILL.md (with fenced code stripped) for ``_shared/<name>``.

    Returns sorted, deduped ``[(shared-name, referring-skill-id), ...]``.
    Does NOT auto-resolve; caller (pack.cli) decides via --include-shared.
    """
    refs: set[tuple[str, str]] = set()
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        stripped = _strip_fenced_blocks(text)
        skill_id = skill_dir.name
        for match in SHARED_REF_RE.findall(stripped):
            refs.add((match, skill_id))
    return sorted(refs)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _walk_findings(root: Path, scan_subdir: str) -> list[dict]:
    findings: list[dict] = []
    scan_root = root / scan_subdir
    if not scan_root.exists():
        return findings

    for entry in scan_root.rglob("*"):
        if not entry.is_file():
            continue
        rel = entry.relative_to(root).as_posix()
        dropped, rule = is_dropped(rel)
        if dropped:
            findings.append({
                "check": "always_drop",
                "severity": "warn",
                "path": rel,
                "rule": rule,
            })
            continue
        opt, label = is_optional(rel)
        if opt:
            findings.append({
                "check": "optional",
                "severity": "info",
                "path": rel,
                "rule": label,
            })

    # Cross-skill _shared/ refs (warn-only).
    skills_dir = root / ".claude" / "skills"
    if skills_dir.is_dir():
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and d.name != "_shared"]
        shared_root = skills_dir / "_shared"
        for shared_name, skill_id in find_shared_refs(skill_dirs):
            shared_path = shared_root / shared_name
            if shared_path.exists():
                findings.append({
                    "check": "shared_dep",
                    "severity": "info",
                    "path": shared_path.relative_to(root).as_posix(),
                    "referring_skill": skill_id,
                })
            else:
                findings.append({
                    "check": "shared_dep_missing",
                    "severity": "warn",
                    "missing": shared_name,
                    "referring_skill": skill_id,
                })

    findings.sort(key=lambda f: (f["check"], f.get("path", f.get("missing", ""))))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="claude-pack safety scanner")
    parser.add_argument("--root", default=".", help="repo root (default: cwd)")
    parser.add_argument("--scan", default=".claude", help="subdir to walk (default: .claude)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 if any severity=error finding (currently none qualify)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    findings = _walk_findings(root, args.scan)
    output = {
        "schema_version": "1.0",
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root),
        "findings": findings,
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")

    if args.strict and any(f["severity"] == "error" for f in findings):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
