"""catalog.py — the skill catalog loader + slug↔dir normalization shared by the
usage and workflow lenses.

cleanmatic records skill invocations under heterogeneous identities:
  - `cleanmatic:product-spec`  (Skill tool, owned skill — dir DROPS the prefix → `product-spec`)
  - `product-spec`             (UserPromptExpansion / dir form)
  - `ck:plan`                  (external skill — dir KEEPS a hyphenated prefix → `ck-plan`)
  - `cook`                     (bare command → dir `cook`)

Because the prefix→dir rule is NOT uniform, we resolve to the canonical dir slug
by reading each `.claude/skills/*/SKILL.md` `name:` field and building a
slug→dir map, then falling back to structural guesses. Flat dir slug is the
identity (HA's framework_of / to_dir_id are intentionally dropped — D1).

Ships in the release bundle. stdlib only.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import telemetry_paths

_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
# Lib/support dirs under .claude/skills that are not invocable skills.
_NON_SKILL_DIRS = {"_shared", "common", "document-skills"}


def skills_dir() -> Path:
    """The repo's skill catalog dir. CK_SKILLS_DIR overrides it (tests)."""
    env = os.environ.get("CK_SKILLS_DIR")
    if env:
        return Path(env)
    return Path(telemetry_paths.project_dir()) / ".claude" / "skills"


def _read_name(skill_md: Path) -> str | None:
    try:
        head = skill_md.read_text(encoding="utf-8")[:2000]
    except OSError:
        return None
    m = _NAME_RE.search(head)
    return m.group(1).strip() if m else None


# Skills authored in THIS repo carry this name prefix; everything else under
# .claude/skills/ is a vendored external tool the PO installed but does not own.
# "never used" is only actionable for owned skills (M1) — an unused vendored
# `ck:*` tool is expected, not a prune candidate.
_OWNED_NAME_PREFIX = "cleanmatic:"


def load_catalog(sdir: Path | None = None) -> dict:
    """Return {'dirs': set[str], 'slug_to_dir': dict[str, str], 'owned': set[str]}.

    dirs   = catalog identity (dir name of every dir holding a SKILL.md).
    slug_to_dir = each SKILL.md `name:` slug → its dir (so recorded invocation
                  identities resolve to the canonical dir).
    owned  = dirs whose SKILL.md `name:` is `cleanmatic:*` (PO-authored). Used to
             scope the actionable never-used list away from ~80 vendored tools.
    Fail-soft: a missing / unreadable skills dir yields empty structures."""
    sdir = sdir or skills_dir()
    dirs: set[str] = set()
    slug_to_dir: dict[str, str] = {}
    owned: set[str] = set()
    try:
        entries = sorted(p for p in sdir.iterdir() if p.is_dir())
    except OSError:
        return {"dirs": dirs, "slug_to_dir": slug_to_dir, "owned": owned}
    for d in entries:
        if d.name in _NON_SKILL_DIRS:
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        dirs.add(d.name)
        name = _read_name(skill_md)
        if name:
            slug_to_dir[name] = d.name
            slug_to_dir.setdefault(name.replace(":", "-"), d.name)
            if name.startswith(_OWNED_NAME_PREFIX):
                owned.add(d.name)
        slug_to_dir.setdefault(d.name, d.name)
    return {"dirs": dirs, "slug_to_dir": slug_to_dir, "owned": owned}


def to_dir_id(skill: str, catalog: dict) -> str:
    """Normalize a recorded invocation identity to its canonical dir slug.

    Resolution: exact slug→dir map → known dir → ':'-stripped variants → flat
    fallback (':' → '-'). An unknown skill is still returned (counted), never
    dropped — surfaced honestly under its flat slug."""
    if not skill:
        return ""
    s2d = catalog.get("slug_to_dir", {})
    dirs = catalog.get("dirs", set())
    if skill in s2d:
        return s2d[skill]
    if skill in dirs:
        return skill
    hyphen = skill.replace(":", "-")
    if hyphen in dirs:
        return hyphen
    tail = skill.split(":")[-1]
    if tail in dirs:
        return tail
    return hyphen
