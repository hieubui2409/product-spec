#!/usr/bin/env python3
"""
frontmatter_parser — read a markdown artifact and return its YAML frontmatter,
body, and section map.

Tolerant: on parse failure returns a structured parse_error indicator instead
of raising, so the caller can emit a finding rather than crash.

CLI:
    frontmatter_parser.py <file>            # prints JSON to stdout
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from encoding_utils import configure_utf8_console, read_text_utf8

configure_utf8_console()


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
SECTION_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def parse_file(path: Path) -> Dict[str, Any]:
    """Parse a markdown artifact file.

    Returns a dict:
        {
          "ok": bool,
          "file": "<path>",
          "frontmatter": {...} | None,
          "body": "<markdown body>",
          "sections": {<heading>: <section text>, ...},
          "error": "<message>" | None
        }
    """
    p = Path(path)
    result: Dict[str, Any] = {
        "ok": False,
        "file": str(p),
        "frontmatter": None,
        "body": "",
        "sections": {},
        "error": None,
    }
    try:
        text = read_text_utf8(p)
    except FileNotFoundError:
        result["error"] = f"file not found: {p}"
        return result
    except OSError as exc:
        result["error"] = f"read error: {exc}"
        return result

    return parse_text(text, file_label=str(p))


def parse_text(text: str, file_label: str = "<text>") -> Dict[str, Any]:
    """Parse raw markdown content (frontmatter + body)."""
    result: Dict[str, Any] = {
        "ok": False,
        "file": file_label,
        "frontmatter": None,
        "body": "",
        "sections": {},
        "error": None,
    }

    # Strip a leading UTF-8 BOM if present. Windows text editors (Notepad,
    # older VS Code presets) often save files with U+FEFF prefix, which
    # otherwise prevents the `---` frontmatter sentinel from matching at
    # column 0 and raises a misleading "no YAML frontmatter" error.
    if text.startswith("﻿"):
        text = text.lstrip("﻿")

    if not text.lstrip().startswith("---"):
        result["error"] = "no YAML frontmatter (file does not start with '---')"
        return result

    m = FRONTMATTER_RE.match(text.lstrip())
    if not m:
        result["error"] = "malformed YAML frontmatter (missing closing '---')"
        return result

    raw_fm, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(raw_fm) or {}
        if not isinstance(fm, dict):
            result["error"] = "frontmatter is not a YAML mapping"
            return result
    except yaml.YAMLError as exc:
        result["error"] = f"YAML parse error: {exc}"
        return result

    result["frontmatter"] = fm
    result["body"] = body
    result["sections"] = extract_sections(body)
    result["ok"] = True
    return result


def extract_sections(body: str) -> Dict[str, str]:
    """Map heading-text -> section content (until the next heading of any level)."""
    sections: Dict[str, str] = {}
    matches = list(SECTION_RE.finditer(body))
    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[heading] = body[start:end].strip()
    return sections


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: frontmatter_parser.py <file>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    result = parse_file(target)
    # YAML parses ISO date strings into datetime.date objects; default=str
    # serializes them as ISO 8601 strings so the JSON dump round-trips cleanly.
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
