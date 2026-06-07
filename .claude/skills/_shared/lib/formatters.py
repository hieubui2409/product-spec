"""Output formatting: markdown tables, JSON, summary blocks, severity badges.

Ported verbatim (framework-agnostic) from human-analyzer's
platform_lib/formatters.py for the telemetry usage-&-health lenses. No skill_ids
dependency, stdlib only. Handles Vietnamese display-width (NFC + East-Asian
width) so VI narration tables align in a terminal.

CM-local dev tooling, NOT shipped in the pack bundle.
"""
import json
import sys
import unicodedata
from typing import Optional

_MIN_SEP = 3  # GFM needs at least 3 dashes per column separator cell


def _disp_width(s: str) -> int:
    """Terminal display width of a string. NFC-normalizes first so Vietnamese
    diacritics (often authored as NFD base+combining) count as one cell, and
    treats East-Asian wide/fullwidth glyphs as two cells, combining marks as zero."""
    s = unicodedata.normalize("NFC", str(s))
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def _pad(s: str, width: int) -> str:
    """Left-justify by DISPLAY width (str.ljust pads by code points → misaligns)."""
    s = str(s)
    return s + " " * max(0, width - _disp_width(s))


def markdown_table(headers: list[str], rows: list[list[str]], align: Optional[list[str]] = None) -> str:
    """Generate a markdown table. align: list of 'l', 'r', 'c' per column."""
    if not rows:
        return f"| {' | '.join(headers)} |\n| {' | '.join(['---'] * len(headers))} |\n| _(empty)_ |"
    widths = [max(_disp_width(h), max((_disp_width(r[i]) for r in rows), default=0))
              for i, h in enumerate(headers)]
    sep = []
    for i, w in enumerate(widths):
        a = (align[i] if align and i < len(align) else "l")
        if a == "r":
            sep.append("-" * max(_MIN_SEP - 1, w - 1) + ":")
        elif a == "c":
            sep.append(":" + "-" * max(_MIN_SEP - 2, w - 2) + ":")
        else:
            sep.append("-" * max(_MIN_SEP, w))
    lines = [
        "| " + " | ".join(_pad(h, widths[i]) for i, h in enumerate(headers)) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_pad(row[i], widths[i]) for i in range(len(headers))) + " |")
    return "\n".join(lines)


def json_output(data, pretty: bool = True) -> str:
    """Format data as JSON string."""
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, default=str)


def summary_block(title: str, items: dict[str, str]) -> str:
    """Format a key-value summary block."""
    lines = [f"## {title}", ""]
    for k, v in items.items():
        lines.append(f"- **{k}**: {v}")
    return "\n".join(lines)


def severity_badge(severity: str) -> str:
    """Return severity indicator."""
    badges = {"HIGH": "[!!!]", "MEDIUM": "[!!]", "LOW": "[!]", "INFO": "[i]", "CRITICAL": "[XXX]"}
    return badges.get(severity.upper(), f"[{severity}]")


def print_table(headers: list[str], rows: list[list[str]], align: Optional[list[str]] = None):
    """Print markdown table to stdout."""
    print(markdown_table(headers, rows, align))


def print_json(data, pretty: bool = True):
    """Print JSON to stdout."""
    print(json_output(data, pretty))


def eprint(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)
