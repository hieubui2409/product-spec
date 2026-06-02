"""Deterministic grounding/ratio guard over the committed lv7/8/9 example reports.

This is the one structural safety-adjacent test the plan keeps (there is NO floor
denylist; the harm-floor itself is judged by meaning in the LLM e2e). It proves the
HARD grounding contract on the shipped examples, the same contract every real report
must meet:

  1. every `<ID>:<line>` cited in an example resolves to a real artifact + a real line
     in the acme-shop sample spec (no fabricated citation, no past-end-of-file line),
  2. each level's fix-label is present (every finding ends in a fix), and
  3. the ratio rule: every finding line (a numbered Top-3 item or a per-lens bullet)
     carries a citation, so a level-9 "scorn line" never stands alone ungrounded
     (scorn always sits inside a grounded finding block).
"""

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2]  # .../spec-critique
EXAMPLES = SKILL_DIR / "examples"
ACME = (
    SKILL_DIR.parent
    / "product-spec"
    / "examples"
    / "acme-shop"
    / "docs"
    / "product"
)

# The six committed harsh-level example reports (vi + en).
EXAMPLE_FILES = [
    "critique-acme-shop-mobile-level7.md",
    "critique-acme-shop-mobile-level8.md",
    "critique-acme-shop-mobile-level9.md",
    "critique-acme-shop-mobile-level7-en.md",
    "critique-acme-shop-mobile-level8-en.md",
    "critique-acme-shop-mobile-level9-en.md",
]

# Per-level fix-label (the one that must appear in that level's report).
FIX_LABEL = {
    "level7": "Gõ lại cho tử tế",
    "level8": "Gõ lại ngay",
    "level9": "đừng để tao nhắc lại",
    "level7-en": "Rewrite it properly",
    "level8-en": "Rewrite it now",
    "level9-en": "make me say it twice",
}

# A citation is <ARTIFACT-ID>:<line>, e.g. PRD-MOBILE:13 or PRD-MOBILE-E1-S1:18.
CITATION = re.compile(r"\b([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*):(\d+)\b")


def _id_to_lines() -> dict:
    """Map every artifact id in the acme-shop spec to its file's line count."""
    out = {}
    for md in ACME.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        m = re.search(r"^id:\s*(\S+)\s*$", text, re.MULTILINE)
        if m:
            out[m.group(1)] = len(text.splitlines())
    return out


ID_LINES = _id_to_lines()


def _finding_lines(text: str):
    """Return the finding-bearing lines: numbered Top-3 items + per-lens bullets.

    These are the lines that MUST be grounded. Prose, headings, blockquote notes,
    and the repeat-offense / DEC sections are excluded.
    """
    lines = text.splitlines()
    findings, in_lens = [], False
    for ln in lines:
        s = ln.strip()
        if s.startswith("## "):
            # Per-lens block is "## Theo từng lăng kính" / "## By lens"; stop at the
            # repeat-offense / DEC sections that follow.
            in_lens = ("lăng kính" in s) or ("By lens" in s)
            continue
        if re.match(r"^\d+\.\s+\*\*\[", s):  # Top-3 numbered finding
            findings.append(s)
        elif in_lens and s.startswith("- **["):  # per-lens bulleted finding
            findings.append(s)
    return findings


@pytest.mark.parametrize("fname", EXAMPLE_FILES)
def test_example_citations_resolve(fname):
    text = (EXAMPLES / fname).read_text(encoding="utf-8")
    cites = CITATION.findall(text)
    assert cites, f"{fname}: no ID:line citation found"
    for art_id, line_s in cites:
        assert art_id in ID_LINES, f"{fname}: cites unknown artifact {art_id}"
        line = int(line_s)
        assert 1 <= line <= ID_LINES[art_id], (
            f"{fname}: {art_id}:{line} is out of range "
            f"(file has {ID_LINES[art_id]} lines)"
        )


@pytest.mark.parametrize("fname", EXAMPLE_FILES)
def test_example_has_fix_label(fname):
    text = (EXAMPLES / fname).read_text(encoding="utf-8")
    key = fname.replace("critique-acme-shop-mobile-", "").replace(".md", "")
    assert FIX_LABEL[key] in text, f"{fname}: missing the level fix-label {FIX_LABEL[key]!r}"


@pytest.mark.parametrize("fname", EXAMPLE_FILES)
def test_every_finding_line_is_grounded(fname):
    """Ratio rule: no finding line stands without a citation (scorn never floats free)."""
    text = (EXAMPLES / fname).read_text(encoding="utf-8")
    findings = _finding_lines(text)
    assert findings, f"{fname}: no finding lines parsed"
    for f in findings:
        assert CITATION.search(f), f"{fname}: ungrounded finding line (no ID:line): {f[:80]}"


def test_resolver_indexed_the_mobile_artifacts():
    # Sanity: the resolver actually found the artifacts the examples cite.
    assert "PRD-MOBILE" in ID_LINES
    assert "PRD-MOBILE-E1-S1" in ID_LINES
