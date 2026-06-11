#!/usr/bin/env python3
"""
Cross-platform encoding utilities for Windows compatibility.

Mirrors skill-creator's helper. Fixes UnicodeEncodeError on Windows by
reconfiguring stdout/stderr to UTF-8 and providing encoding-aware file
I/O helpers.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any


def emit_json(obj: Any) -> None:
    """Print `obj` as indented JSON to stdout, surviving a closed downstream pipe.

    The analytical scripts emit large JSON and promise to "always exit 0". When their
    stdout is piped into a consumer that closes early (`check_consistency.py … | head`),
    the final write hits a broken pipe and — left unhandled — Python prints a traceback
    and exits non-zero, breaking that contract and noising the PO's terminal.

    On BrokenPipeError we swallow it and redirect stdout to os.devnull so the interpreter's
    flush-on-exit cannot re-raise. The single home every big-JSON CLI uses for this.
    """
    try:
        sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
        sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except OSError:
            pass


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
    """Write file with explicit UTF-8 encoding.

    Note: normalizes newlines — do NOT use where byte-for-byte CRLF/LF
    preservation matters (use open(..., newline='') instead).
    """
    Path(path).write_text(content, encoding="utf-8")
