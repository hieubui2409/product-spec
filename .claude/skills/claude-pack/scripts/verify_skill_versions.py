#!/usr/bin/env python3
"""verify_skill_versions — E5 release-identity gate.

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
DEFAULT_SKILLS = ("product-spec", "product-spec-critique", "claude-pack")


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

    if args.skill:
        skill_dirs = list(args.skill)
    else:
        # script lives at <root>/.claude/skills/claude-pack/scripts/ → parents[4] == <root>
        root = args.root or Path(__file__).resolve().parents[4]
        skill_dirs = [root / ".claude" / "skills" / s for s in DEFAULT_SKILLS]

    results, ok = verify(skill_dirs)
    width = max((len(r.name) for r in results), default=4)
    for r in results:
        mark = "OK " if r.ok else "FAIL"
        print(f"[{mark}] {r.name:<{width}}  {r.version or '-':<8}  {r.reason}")
    if not ok:
        print("\nVersion verification FAILED — fix the above before releasing.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
