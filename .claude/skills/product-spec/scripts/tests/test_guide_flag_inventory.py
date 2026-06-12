"""Flag-inventory contract: every flag in product-spec SKILL.md must be documented in GUIDE-EN.md.

The invariant: a PO guide that omits flags documented in SKILL.md silently hides
capabilities.  This test parses the flag table from SKILL.md, parses the flag
mentions from the GUIDE, and asserts no gap exists.

Allowlist: flags that are intentionally GUIDE-omitted because they are operator /
script-level concerns, not PO-facing (each entry requires a documented reason).
"""
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL_DIR / "SKILL.md"
GUIDE_EN = SKILL_DIR / "GUIDE-EN.md"
GUIDE_VI = SKILL_DIR / "GUIDE-VI.md"

# Flags intentionally omitted from the GUIDEs:
# preferences.py --set: script-level CLI, not an in-skill flag — shown in SKILL.md
# as a quasi-flag for completeness but the guide covers it via D2 prose.
GUIDE_OMIT_ALLOWLIST = {
    "preferences.py",  # operator CLI, not an in-skill --flag
}


def _parse_skill_flags(text: str) -> list[str]:
    """Extract flag tokens (e.g. '--voice', '--compact-mode') from the SKILL.md flag table.

    Looks at lines beginning with `| `` inside the ## Flags table block.
    Returns the leading --flag token from each row (strips sub-flags and modifiers).
    """
    flags: list[str] = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("## Flags"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break  # end of flag table section
        if not in_table:
            continue
        if not line.startswith("|"):
            continue
        if set(line.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")) == set():
            continue  # separator row
        # Extract the first cell
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        cell = cells[0]
        # Skip header row and (no flag) row
        if cell.lower().startswith("flag") or cell == "(no flag)":
            continue
        # Extract the bare --flag or preferences.py token
        # Handle backtick-wrapped tokens like `--voice` or `preferences.py --set KEY=VALUE`
        m = re.search(r"`(--[\w-]+|preferences\.py)", cell)
        if m:
            flags.append(m.group(1))
    return flags


def _guide_mentions_flag(guide_text: str, flag: str) -> bool:
    """Return True if the flag appears anywhere in the guide (in a code block or inline)."""
    return flag in guide_text


def test_guide_en_covers_all_skill_flags():
    """GUIDE-EN.md mentions every flag from the SKILL.md flag table."""
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    guide_text = GUIDE_EN.read_text(encoding="utf-8")
    flags = _parse_skill_flags(skill_text)
    assert flags, "No flags parsed from SKILL.md — check the parser"
    missing = [
        f for f in flags
        if f not in GUIDE_OMIT_ALLOWLIST and not _guide_mentions_flag(guide_text, f)
    ]
    assert not missing, (
        f"GUIDE-EN.md is missing documentation for these SKILL.md flags: {missing}"
    )


def test_guide_vi_covers_all_skill_flags():
    """GUIDE-VI.md mentions every flag from the SKILL.md flag table."""
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    guide_text = GUIDE_VI.read_text(encoding="utf-8")
    flags = _parse_skill_flags(skill_text)
    assert flags, "No flags parsed from SKILL.md — check the parser"
    missing = [
        f for f in flags
        if f not in GUIDE_OMIT_ALLOWLIST and not _guide_mentions_flag(guide_text, f)
    ]
    assert not missing, (
        f"GUIDE-VI.md is missing documentation for these SKILL.md flags: {missing}"
    )
