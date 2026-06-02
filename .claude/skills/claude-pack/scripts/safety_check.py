"""safety_check — non-negotiable filter for cleanmatic:claude-pack.

Three layers of "always-drop" rules + an opt-in catalog + a warn-only
detector for cross-skill `_shared/` references. These rules are HARD:
no CLI flag, no manifest field, no override disables them.

Imported by pack.cli; standalone CLI emits JSON findings.

The catalog constants and path-classification predicates (is_dropped,
is_optional) live in safety_catalog so that pack.selection and pack.tarball
can import them from a leaf module without pulling in the CLI machinery.
This file re-exports those symbols and adds find_shared_refs + the CLI walker.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Re-export every public symbol callers expect on ``safety_check.*``
from safety_catalog import (  # type: ignore[import-not-found]
    ALWAYS_DROP_DIRS,
    ALWAYS_DROP_EXACT,
    ALWAYS_DROP_PATTERNS,
    OPT_IN_PATHS,
    SafetyError,
    is_dropped,
    is_optional,
)

__all__ = [
    "is_dropped", "is_optional", "find_shared_refs",
    "SafetyError",
    "ALWAYS_DROP_EXACT", "ALWAYS_DROP_DIRS", "ALWAYS_DROP_PATTERNS", "OPT_IN_PATHS",
]

# ---------------------------------------------------------------------------
# Cross-skill _shared/ reference detection (warn-only)
# ---------------------------------------------------------------------------

# Lowercase enforced; uppercase _shared/Foo silently skipped (documented).
# Captures the first path segment after _shared/, so inclusion is dir-granular:
# a reference to _shared/references/x.md pulls the whole _shared/references/ dir.
SHARED_REF_RE = re.compile(r"_shared/([a-z0-9_-]+)")

_FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)


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
        try:
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
        except (OSError, ValueError):
            # An OS error mid-walk (e.g. a broken symlink, race-deleted file) or
            # a ValueError from relative_to() must not abort the scanner — it is
            # a diagnostic tool and must always exit 0.
            continue

    # Cross-skill _shared/ refs (warn-only).
    # Derive the skills dir from the actual scan root so --scan is honored.
    # When scan_subdir ends with '.claude' the skills dir is scan_root/'skills';
    # for any other --scan value (e.g. a bare skill dir) skip the shared_dep pass.
    if scan_subdir.rstrip("/\\").endswith(".claude"):
        skills_dir = scan_root / "skills"
    else:
        skills_dir = None
    if skills_dir is not None and skills_dir.is_dir():
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
