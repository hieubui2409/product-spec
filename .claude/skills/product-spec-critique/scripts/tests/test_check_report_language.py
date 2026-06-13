"""Tests for the advisory en-language-purity scan (check_report_language)."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import check_report_language as crl  # noqa: E402

EN_CLEAN = """---
lang: en
level: 9
---
# Critique: all · level 9

> Severity tally: blocker 1

## Top 3: fix now
1. **[blocker][tech] PRD-CHAT-E1-S3:18** — This AC is fucking empty. Rewrite it now.
"""

EN_LEAKY = """---
lang: en
level: 3
---
# Critique: all · level 3

## Top 3: sửa ngay
1. **[blocker][tech] PRD-CHAT-E1-S3:18** — Toang ở đâu: rỗng. Sửa: thêm ngưỡng.
"""

VI_REPORT = """---
lang: vi
level: 9
---
# Critique: all · level 9
## Top 3: sửa ngay
1. **[blocker] PRD-CHAT:15** — đm cái AC này rỗng vl. Gõ lại, đừng để tao nhắc lại.
"""

# Legitimate: an en critique quoting a Vietnamese SOURCE spec phrase, then glossing it.
EN_QUOTED_SOURCE = """---
lang: en
level: 4
---
# Critique: all · level 4
## Top 3: fix now
1. **[major] PRD-CHAT:70** — The NFR says "Độ trễ gửi tin nhắn thấp" (low message delay) with no number. Fix: add p95.
"""


def test_clean_en_report_has_no_findings():
    assert crl.scan_text(EN_CLEAN) == []


def test_leaky_en_report_is_flagged_as_structural_leak():
    findings = crl.scan_text(EN_LEAKY)
    assert findings, "expected the Vietnamese leak to be flagged"
    assert any(f["is_leak"] for f in findings), "structural leak must set is_leak"
    assert any(f["structural_hits"] for f in findings)


def test_quoted_source_is_review_not_leak():
    findings = crl.scan_text(EN_QUOTED_SOURCE)
    assert findings, "the quoted Vietnamese should still surface for review"
    assert all(not f["is_leak"] for f in findings), "a pure source-quote is NOT a leak"
    assert any(f["quoted_vi"] for f in findings)


def test_gloss_and_proper_noun_are_review_not_leak():
    # A parenthetical gloss of a source term + a Vietnamese proper noun: review, not leak.
    text = ('---\nlang: en\nlevel: 9\n---\n# Critique\n'
            '1. **[major] BRD:42** — The rival app Ghép Đôi already verifies in Việt Nam, '
            'and the AC reads "must be smooth" (mượt mà) with no number. Fix: add p95.\n')
    findings = crl.scan_text(text)
    assert findings
    assert all(not f["is_leak"] for f in findings), "glosses/proper-nouns are not leaks"
    assert any(f["needs_review"] for f in findings)


def test_unquoted_token_not_masked_by_substring_in_a_quote():
    # An unquoted Vietnamese word whose text also appears INSIDE a separate quoted
    # span on the same line must still surface as unquoted (a likely leak) — not be
    # silently reclassified as a legit source-quote by a substring match.
    text = ('---\nlang: en\nlevel: 9\n---\n# Critique\n'
            '1. The metric giải was dropped though the title says "phân giải cao".\n')
    findings = crl.scan_text(text)
    assert findings
    assert any(f["unquoted_vi"] for f in findings), \
        "an unquoted vi token must not be masked by the same text inside a quote"


def test_vi_report_is_skipped(tmp_path):
    p = tmp_path / "r-vi.md"
    p.write_text(VI_REPORT, encoding="utf-8")
    res = crl.scan_file(p)
    assert res.get("skipped") is True
    assert res["findings"] == []


def test_en_report_file_scan_flags(tmp_path):
    p = tmp_path / "r-en.md"
    p.write_text(EN_LEAKY, encoding="utf-8")
    res = crl.scan_file(p)
    assert res["lang"] == "en"
    assert res["findings"], "en file scan should surface the leak"


def test_frontmatter_lang_parse():
    assert crl._frontmatter_lang(EN_CLEAN) == "en"
    assert crl._frontmatter_lang(VI_REPORT) == "vi"
    assert crl._frontmatter_lang("no frontmatter here") is None


def test_diacritic_detector():
    assert crl._has_vietnamese_char("đm")
    assert crl._has_vietnamese_char("mượt")
    assert crl._has_vietnamese_char("Sửa")
    # plain-ASCII english (and the ascii word "Toang") carry no diacritic
    assert not crl._has_vietnamese_char("Rewrite")
    assert not crl._has_vietnamese_char("Toang")
