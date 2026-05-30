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
from typing import Any, Dict

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
    except UnicodeDecodeError as exc:
        # A non-UTF-8 file raises UnicodeDecodeError (a ValueError subclass, NOT an
        # OSError); surface it as a parse_error so the graph build stays fail-soft
        # instead of crashing on the first byte that is not valid UTF-8.
        result["error"] = f"encoding error (not valid UTF-8): {exc}"
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
        # An empty block (`---\n---`) HAS a closing fence but no inner content, so
        # the content-requiring regex misses it — report that accurately instead
        # of the misleading "missing closing '---'".
        if re.match(r"^---\s*\n---\s*\n?", text.lstrip()):
            result["error"] = "frontmatter block is empty"
        else:
            result["error"] = "malformed YAML frontmatter (missing closing '---')"
        return result

    raw_fm, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(raw_fm) or {}
        if not isinstance(fm, dict):
            result["error"] = "frontmatter is not a YAML mapping"
            return result
    except (yaml.YAMLError, ValueError) as exc:
        # PyYAML's timestamp/int constructors raise a bare ValueError (NOT a
        # yaml.YAMLError) for an out-of-range value like an unquoted
        # `target_date: 2026-13-99`. Catch it here so the gate emits a
        # parse_error finding (and strict_gate exits 2) instead of crashing.
        result["error"] = f"YAML parse error: {exc}"
        return result

    result["frontmatter"] = fm
    result["body"] = body
    result["sections"] = extract_sections(body)
    result["ok"] = True
    return result


def extract_sections(body: str) -> Dict[str, str]:
    """Map heading-text -> section content (until the next heading of any level).

    Consumed by the CLI (`main()` dumps the full result); the library callers
    (spec_graph etc.) read only frontmatter/body. Duplicate heading texts are
    disambiguated with a numeric suffix so a repeated heading does not silently
    overwrite an earlier section (the map was last-wins / lossy before)."""
    sections: Dict[str, str] = {}
    matches = list(SECTION_RE.finditer(body))
    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        key = heading
        if key in sections:
            n = 2
            while f"{heading} ({n})" in sections:
                n += 1
            key = f"{heading} ({n})"
        sections[key] = content
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
