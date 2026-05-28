#!/usr/bin/env python3
"""
Cross-platform encoding utilities for Windows compatibility.

Mirrors skill-creator's helper. Fixes UnicodeEncodeError on Windows by
reconfiguring stdout/stderr to UTF-8 and providing encoding-aware file
I/O helpers.
"""

import sys
from pathlib import Path


def configure_utf8_console():
    """Reconfigure stdout/stderr for UTF-8 on Windows (cp1252 -> utf-8)."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass  # Python < 3.7


def read_text_utf8(path: Path) -> str:
    """Read file with explicit UTF-8 encoding."""
    return Path(path).read_text(encoding="utf-8")


def write_text_utf8(path: Path, content: str) -> None:
    """Write file with explicit UTF-8 encoding."""
    Path(path).write_text(content, encoding="utf-8")
