#!/usr/bin/env python3
"""check_report_language.py — ADVISORY language-purity scan for critique reports.

A critique report declares its language in frontmatter (`lang: vi` | `lang: en`). The
consolidator must render the WHOLE report in that language — every heading, every
why/fix label, every register word. A regression in the consolidate contract once let
Vietnamese structural labels ("Toang ở đâu", "## Theo lăng kính") and Vietnamese
register tokens ("đm", "mày/tao") leak into `lang: en` reports. This script catches
that class of leak early.

It is **ADVISORY ONLY** — it prints findings and ALWAYS exits 0. spec-critique never
gates CI (opinion + web + voice = non-deterministic); this is a reviewer aid, not a
gate. It scans the BODY only (frontmatter `body_hash` hex is skipped) and reports the
line number + the offending Vietnamese-bearing tokens so a human can judge.

Known false-positive: an `en` critique may legitimately QUOTE a Vietnamese phrase from
a bilingual source spec (e.g. citing a Vietnamese AC verbatim). The script flags it; a
human confirms whether it is a quote (fine) or a render leak (fix the consolidator).

Usage:
  check_report_language.py --file <report.md>
  check_report_language.py --dir  <critique-dir>   # scans *.md
Only `lang: en` reports are scanned (a `vi` report is expected to be Vietnamese).
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

# Structural Vietnamese tokens that must NEVER appear in an en report (the leak
# signature we actually hit). Diacritic detection below is the general net; this is
# the high-signal denylist for the specific heading/label/register leaks.
_VI_STRUCTURAL = (
    "Theo lăng kính", "sửa ngay", "Toang ở đâu", "Banh xác", "Banh nóc", "Nát bét",
    "Gõ lại", "Lặp lại từ", "Đáng ghi thành", "Kế thừa từ cha", "Rủi ro bàn giao",
    "đm", "vãi", "mày", "tao", "ông/tôi", "không có",
)


def _frontmatter_lang(text: str) -> Optional[str]:
    """The `lang:` value from a leading YAML frontmatter block, or None."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    for ln in lines[1:end]:
        m = re.match(r"\s*lang:\s*(\S+)\s*$", ln)
        if m:
            return m.group(1)
    return None


def _body(text: str) -> str:
    """The report body with a leading frontmatter block stripped (so the body_hash
    hex map never feeds the scanner)."""
    if not text.startswith("---"):
        return text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    return "\n".join(lines[end + 1:]) if end is not None else text


def _has_vietnamese_char(token: str) -> bool:
    """True iff the token carries a Vietnamese-specific letter: `đ`/`Đ`, or a Latin
    base + a combining tone/diacritic mark (English text carries neither)."""
    for ch in token:
        if ch in "đĐ":
            return True
        decomp = unicodedata.normalize("NFD", ch)
        if len(decomp) > 1 and decomp[0].isascii() and decomp[0].isalpha():
            if any("̀" <= c <= "ͯ" for c in decomp[1:]):
                return True
    return False


def _strip_quotes(tok: str) -> str:
    return tok.strip('"“”\'.,;:()')


def scan_text(text: str) -> List[Dict[str, Any]]:
    """Return per-line findings for an en report body. Each finding separates:

      * `structural_hits` — denylist heading/label/register tokens (a real leak), and
      * `unquoted_vi` — Vietnamese-diacritic tokens OUTSIDE any `"…"` span (a likely
        leak: prose/labels/register the consolidator failed to render in English), from
      * `quoted_vi` — Vietnamese tokens INSIDE a quoted span (a likely-legitimate quote
        of a Vietnamese SOURCE spec, e.g. `"Độ trễ thấp" (low delay)` — review, not leak).

    A line is a STRUCTURAL LEAK iff it has `structural_hits` or `unquoted_vi`; a line
    with only `quoted_vi` is informational (review)."""
    body = _body(text)
    findings: List[Dict[str, Any]] = []
    for i, line in enumerate(body.splitlines(), 1):
        spans = re.findall(r'"[^"]*"', line)
        quoted, unquoted = [], []
        for w in re.findall(r"\S+", line):
            if not _has_vietnamese_char(w):
                continue
            bare = _strip_quotes(w)
            in_quote = any(bare and bare in s for s in spans)
            (quoted if in_quote else unquoted).append(w)
        struct = [s for s in _VI_STRUCTURAL if s in line]
        if struct or quoted or unquoted:
            findings.append({
                "line": i,
                "structural_hits": struct,
                "unquoted_vi": sorted(set(unquoted)),
                "quoted_vi": sorted(set(quoted)),
                # Only a denylist heading/label/register token is a DEFINITE leak. When
                # the SOURCE spec is Vietnamese an en critique legitimately carries vi
                # proper nouns ("Ghép Đôi"), parenthetical glosses ("(mượt mà)") and
                # quoted source terms — so `unquoted_vi`/`quoted_vi` are review signals,
                # not leaks, and a human judges them.
                "is_leak": bool(struct),
                "needs_review": bool(unquoted or quoted),
                "text": line.strip()[:120],
            })
    return findings


def scan_file(path: Path) -> Dict[str, Any]:
    """Scan one report; only `lang: en` reports are checked. Returns a result dict."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {"file": str(path), "error": str(exc), "findings": []}
    lang = _frontmatter_lang(text)
    if lang != "en":
        return {"file": str(path), "lang": lang, "skipped": True, "findings": []}
    return {"file": str(path), "lang": "en", "findings": scan_text(text)}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Advisory language-purity scan for en critique reports")
    ap.add_argument("--file", help="a single report .md")
    ap.add_argument("--dir", help="a directory of report .md files")
    args = ap.parse_args(argv)

    targets: List[Path] = []
    if args.file:
        targets.append(Path(args.file))
    if args.dir:
        targets.extend(sorted(Path(args.dir).glob("*.md")))
    if not targets:
        print(json.dumps({"error": "pass --file or --dir", "results": []}))
        return 0  # advisory: never non-zero

    results = [scan_file(p) for p in targets]
    def _has_leak(r):
        return any(f.get("is_leak") for f in r.get("findings", []))
    def _needs_review(r):
        return any(f.get("needs_review") and not f.get("is_leak") for f in r.get("findings", []))
    structural = [r["file"] for r in results if _has_leak(r)]
    review = [r["file"] for r in results if _needs_review(r) and not _has_leak(r)]
    print(json.dumps({
        "scanned": len(results),
        # The real signal: en reports with a Vietnamese heading/label/register leak.
        "en_reports_with_structural_leak": len(structural),
        "structural_leak_files": [Path(f).name for f in structural],
        # Informational: en reports carrying vi glosses/proper-nouns/quoted source (review).
        "en_reports_needing_review": len(review),
        "review_files": [Path(f).name for f in review],
        "results": results,
    }, indent=2, ensure_ascii=False))
    return 0  # ADVISORY — always 0, never gates


if __name__ == "__main__":
    sys.exit(main())
