"""Changelog size claims must reproduce from two named git tags via context_footprint.

The invariant: any "before → after (−X%)" claim in a CHANGELOG.md must be
computable from git-tagged snapshots using the repo's own token proxy
(ceil(chars/4)).  This test pins the SKILL.md values so a future edit to
either changelog that introduces a new non-reproducible number will fail here
before shipping.
"""
import math
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]  # .../product-spec
TAG_BEFORE = "product-spec-v2.2.2"
TAG_AFTER = "product-spec-v2.3.0"
SKILL_PATH = ".claude/skills/product-spec/SKILL.md"
SKILL_CHANGELOG = REPO_ROOT / ".claude/skills/product-spec/CHANGELOG.md"
ROOT_CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# These are the stored expected values — computed once from the two tags and
# committed here.  A discrepancy between these constants and the tag content
# would itself be caught by test_tag_values_match_expected below.
EXPECTED_BEFORE = 5758
EXPECTED_AFTER = 5371


def _token_proxy(text: str) -> int:
    return math.ceil(len(text) / 4)


def _git_show(tag: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{tag}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git show {tag}:{path} failed: {result.stderr.strip()}"
        )
    return result.stdout


def test_tag_values_match_expected():
    """Verify the stored EXPECTED_* constants reproduce from the two tags."""
    before_text = _git_show(TAG_BEFORE, SKILL_PATH)
    after_text = _git_show(TAG_AFTER, SKILL_PATH)
    assert _token_proxy(before_text) == EXPECTED_BEFORE, (
        f"Token proxy at {TAG_BEFORE} is {_token_proxy(before_text)}, "
        f"expected {EXPECTED_BEFORE}"
    )
    assert _token_proxy(after_text) == EXPECTED_AFTER, (
        f"Token proxy at {TAG_AFTER} is {_token_proxy(after_text)}, "
        f"expected {EXPECTED_AFTER}"
    )


def _extract_skill_proxy_claim(changelog_text: str):
    """Extract (before, after, pct_str) from a 'N → N (−X%)' claim."""
    m = re.search(
        r"\*\*(\d+)\s*→\s*(\d+)\s*\((−[\d.]+%)\)\*\*",
        changelog_text,
    )
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), m.group(3)


def test_skill_changelog_numbers_match_tags():
    """The skill CHANGELOG.md 'before → after' claim matches the tag-measured values."""
    text = SKILL_CHANGELOG.read_text(encoding="utf-8")
    claim = _extract_skill_proxy_claim(text)
    assert claim is not None, (
        "Could not find a 'before → after (−X%)' claim in "
        f"{SKILL_CHANGELOG.relative_to(REPO_ROOT)}"
    )
    before_claimed, after_claimed, _ = claim
    assert before_claimed == EXPECTED_BEFORE, (
        f"Skill CHANGELOG 'before' value {before_claimed} "
        f"does not match tag-measured {EXPECTED_BEFORE}"
    )
    assert after_claimed == EXPECTED_AFTER, (
        f"Skill CHANGELOG 'after' value {after_claimed} "
        f"does not match tag-measured {EXPECTED_AFTER}"
    )


def test_root_changelog_product_spec_pct_is_consistent():
    """Root CHANGELOG.md product-spec percentage is consistent with the tag-measured values."""
    text = ROOT_CHANGELOG.read_text(encoding="utf-8")
    # Root changelog uses a plain percentage claim (no before/after numbers)
    m = re.search(r"product-spec SKILL\.md\s+(−[\d.]+%)", text)
    assert m is not None, (
        "Could not find 'product-spec SKILL.md −X%' claim in root CHANGELOG.md"
    )
    pct_str = m.group(1)
    actual_pct = (EXPECTED_AFTER - EXPECTED_BEFORE) / EXPECTED_BEFORE * 100
    # Strip the unicode minus sign (U+2212) and the percent sign, then parse
    stated = float(pct_str.replace("−", "").replace("%", ""))
    # The stated value must be within 0.2 percentage points of actual
    assert abs(stated - abs(actual_pct)) <= 0.2, (
        f"Root CHANGELOG.md states {pct_str} but measured value is "
        f"{actual_pct:.1f}%"
    )
