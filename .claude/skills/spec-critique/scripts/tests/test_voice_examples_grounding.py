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


def _body_after_frontmatter(text: str) -> str:
    """Return the report body with a leading YAML frontmatter block removed.

    Once regenerated, the committed reports carry a `---`…`---` frontmatter; the grounding
    scan must run on the BODY only — the frontmatter `body_hash` map (`ID: 8hex`) would
    otherwise feed the citation regex a false `ID:<all-digit-hash>` match. A report with
    no frontmatter (the current examples) is returned unchanged."""
    if not text.startswith("---"):
        return text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    return "\n".join(lines[end + 1:]) if end is not None else text


def _read_body(path: Path) -> str:
    return _body_after_frontmatter(path.read_text(encoding="utf-8"))


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
    text = _read_body(EXAMPLES / fname)
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
    text = _read_body(EXAMPLES / fname)
    key = fname.replace("critique-acme-shop-mobile-", "").replace(".md", "")
    assert FIX_LABEL[key] in text, f"{fname}: missing the level fix-label {FIX_LABEL[key]!r}"


@pytest.mark.parametrize("fname", EXAMPLE_FILES)
def test_every_finding_line_is_grounded(fname):
    """Ratio rule: no finding line stands without a citation (scorn never floats free)."""
    text = _read_body(EXAMPLES / fname)
    findings = _finding_lines(text)
    assert findings, f"{fname}: no finding lines parsed"
    for f in findings:
        assert CITATION.search(f), f"{fname}: ungrounded finding line (no ID:line): {f[:80]}"


def test_resolver_indexed_the_mobile_artifacts():
    # Sanity: the resolver actually found the artifacts the examples cite.
    assert "PRD-MOBILE" in ID_LINES
    assert "PRD-MOBILE-E1-S1" in ID_LINES


# ---------------------------------------------------------------------------
# The 18 dating-app voice-ladder fixtures (vi + en, levels 1..9).
#
# Auto-generated by the genuine consolidate→humanize agents, so the strict
# per-citation-resolves rule used on the curated acme examples is too tight here:
# the harsh-level voice legitimately uses shorthand (`S4:18`, `AC:18`) ALONGSIDE a
# full citation on the same finding line. The HARD contract that still holds — and
# the one worth guarding — is the ratio rule: every finding line carries at least one
# RESOLVABLE full `<ID>:<line>` (no scorn line floats free). Resolution is graph-aware
# (a goal id like `BRD-G2` lives inside `brd.md`, so its line count comes from the
# node→file map, not a per-file `id:` scan).
# ---------------------------------------------------------------------------

import sys  # noqa: E402

_PSP_SCRIPTS = SKILL_DIR.parent / "product-spec" / "scripts"
if str(_PSP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_PSP_SCRIPTS))
import spec_graph  # noqa: E402

DATING_ROOT = SKILL_DIR.parents[2] / "e2e" / "dating-app"
DATING_PROD = DATING_ROOT / "docs" / "product"
VOICE_LADDER_DIR = DATING_PROD / "critique"
VOICE_LADDER_FILES = [
    f"voice-ladder9-{lang}-lvl{n}.md" for lang in ("vi", "en") for n in range(1, 10)
]
# The lens-findings-cache key each lang's reports carry (the consolidate_only store key).
LENS_FINDINGS_HASH = {"vi": "196b1f155bf4b30f", "en": "22e9b7fd857a9d8e"}


def _dating_resolver() -> dict:
    """Map every dating-app node id (incl. goals) to its file's line count, plus the
    file-level pseudo-ids (`BRD`/`VISION`/`PRODUCT`) the source-file map exposes."""
    graph = spec_graph.build_graph(DATING_ROOT)
    res = {}
    for node in graph.get("nodes", []):
        rel = node.get("file")
        if not rel:
            continue
        p = DATING_PROD / rel
        if p.exists():
            res[node["id"]] = len(p.read_text(encoding="utf-8").splitlines())
    for pid, fname in {"BRD": "brd.md", "VISION": "vision.md",
                       "PRODUCT": "PRODUCT.md", "PRODUCT.md": "PRODUCT.md"}.items():
        p = DATING_PROD / fname
        if p.exists():
            res.setdefault(pid, len(p.read_text(encoding="utf-8").splitlines()))
    return res


DATING_RESOLVER = _dating_resolver()


@pytest.mark.parametrize("fname", VOICE_LADDER_FILES)
def test_voice_ladder_findings_grounded(fname):
    """Ratio contract: every finding line carries >=1 resolvable, in-range citation."""
    text = _read_body(VOICE_LADDER_DIR / fname)
    findings = _finding_lines(text)
    assert findings, f"{fname}: no finding lines parsed"
    for f in findings:
        resolvable = [
            art for art, line_s in CITATION.findall(f)
            if art in DATING_RESOLVER and 1 <= int(line_s) <= DATING_RESOLVER[art]
        ]
        assert resolvable, f"{fname}: finding line without a resolvable citation: {f[:80]}"


@pytest.mark.parametrize("fname", VOICE_LADDER_FILES)
def test_voice_ladder_frontmatter(fname):
    """Frontmatter carries scope/level/lang + the lang's lens_findings_hash; the
    register block is present IFF level >= 7 (the register threshold)."""
    text = (VOICE_LADDER_DIR / fname).read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{fname}: missing frontmatter"
    fm = text.split("---\n", 2)[1]
    m = re.match(r"voice-ladder9-(vi|en)-lvl(\d)\.md", fname)
    lang, level = m.group(1), int(m.group(2))
    assert f"lang: {lang}" in fm, f"{fname}: lang mismatch"
    assert f"level: {level}" in fm, f"{fname}: level mismatch"
    assert f"lens_findings_hash: {LENS_FINDINGS_HASH[lang]}" in fm, f"{fname}: hash mismatch"
    assert ("register:" in fm) == (level >= 7), \
        f"{fname}: register block must appear iff level>=7"


def test_voice_ladder_set_is_complete():
    # All 18 fixtures exist on disk.
    missing = [f for f in VOICE_LADDER_FILES if not (VOICE_LADDER_DIR / f).exists()]
    assert not missing, f"missing voice-ladder fixtures: {missing}"
