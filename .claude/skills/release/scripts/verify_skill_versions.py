#!/usr/bin/env python3
"""verify_skill_versions — release-identity gate.

Reads each skill's SKILL.md frontmatter nested ``metadata.version`` and asserts it
exists and matches semver (``MAJOR.MINOR.PATCH``). Scope is shape + presence ONLY:
the 3 skill versions are independent of the bundle tag by design, so NO bundle-equality
check is performed. Exit 1 on any missing/malformed version. Runnable in CI and locally.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
# All four owned skills ship in the bundle and are semver-checked here; each is also
# changelog-pinned in test_version_sync.VERSION_SYNCED_SKILLS. The skip-missing logic
# in main() stays as a forward-compat backstop for any future CM-local (unbundled) skill.
DEFAULT_SKILLS = ("product-spec", "product-spec-critique", "release", "telemetry")

# keepachangelog: the first heading whose bracket is EXACTLY [X.Y.Z]. The closing
# `\]` is required, so `## [Unreleased]` is skipped and pre-release / build-metadata
# headings (`## [1.2.0-rc.1]`, `## [1.2.0+build]`) do NOT match — only a plain
# released semver counts as "the top version".
_CHANGELOG_VERSION = re.compile(r"^##\s+\[(\d+\.\d+\.\d+)\]")


class ChangelogError(ValueError):
    """Raised when a CHANGELOG has no parseable released-semver heading."""


def changelog_top_version(changelog_path: Path) -> str:
    """Return the first released semver under a `## [X.Y.Z]` heading (skipping
    `[Unreleased]` and pre-release headings). Raises ChangelogError on a missing
    file or a CHANGELOG with no released-semver heading — never a silent default."""
    if not changelog_path.is_file():
        raise ChangelogError(f"CHANGELOG not found: {changelog_path}")
    for line in changelog_path.read_text(encoding="utf-8").splitlines():
        m = _CHANGELOG_VERSION.match(line.strip())
        if m:
            return m.group(1)
    raise ChangelogError(f"no `## [X.Y.Z]` released heading in {changelog_path}")


@dataclass
class Result:
    name: str
    version: str | None
    ok: bool
    reason: str


def _frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    return yaml.safe_load(text[3:end]) or {}


def verify(skill_dirs: list[Path]) -> tuple[list[Result], bool]:
    results: list[Result] = []
    for d in skill_dirs:
        name = d.name
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            results.append(Result(name, None, False, "SKILL.md missing"))
            continue
        fm = _frontmatter(skill_md)
        meta = fm.get("metadata")
        if not isinstance(meta, dict) or "version" not in meta:
            results.append(Result(name, None, False, "missing metadata.version"))
            continue
        version = str(meta["version"])
        if not SEMVER.match(version):
            results.append(Result(name, version, False, f"version {version!r} not semver MAJOR.MINOR.PATCH"))
            continue
        results.append(Result(name, version, True, "ok"))
    return results, all(r.ok for r in results)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify each skill's metadata.version is present + semver.")
    ap.add_argument("--root", type=Path, help="repo root (defaults to the repo containing this script)")
    ap.add_argument("--skill", action="append", type=Path, default=[], help="explicit skill dir (repeatable)")
    args = ap.parse_args(argv)

    skipped: list[str] = []
    if args.skill:
        skill_dirs = list(args.skill)
    else:
        # script lives at <root>/.claude/skills/release/scripts/ → parents[4] == <root>
        root = args.root or Path(__file__).resolve().parents[4]
        skill_dirs = []
        for s in DEFAULT_SKILLS:
            d = root / ".claude" / "skills" / s
            if d.is_dir():
                skill_dirs.append(d)
            else:
                # CM-local skills (e.g. telemetry) are absent from a RECIPIENT bundle.
                # This checker ships in the bundle, so skip a missing DEFAULT skill dir
                # rather than fail — keeps the shipped checker bundle-portable. Locally
                # (all dirs present) every DEFAULT_SKILLS entry is still verified; a
                # present dir with a broken/absent SKILL.md still FAILS via verify().
                skipped.append(s)

    results, ok = verify(skill_dirs)
    for s in skipped:
        print(f"[skip] {s:<8}  -         not present (CM-local / not bundled)")
    width = max((len(r.name) for r in results), default=4)
    for r in results:
        mark = "OK " if r.ok else "FAIL"
        print(f"[{mark}] {r.name:<{width}}  {r.version or '-':<8}  {r.reason}")
    if not ok:
        print("\nVersion verification FAILED — fix the above before releasing.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
