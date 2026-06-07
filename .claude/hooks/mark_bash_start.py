#!/usr/bin/env python3
"""
mark_bash_start.py — PreToolUse:Bash hook. Stamps a monotonic start mark for a
skill-script Bash command so its PostToolUse counterpart (track_script_execution.py)
can compute wall-clock `ms`. CM-local dev tooling (NOT shipped).

Only marks commands that run a .claude/skills/<skill>/scripts/<file>.(py|sh) —
the same filter PostToolUse uses — so plain git/ls/grep never create markers.
If this Pre hook is missed, Post simply records without `ms` (graceful degrade).

Fail-open + non-blocking: always emits {"continue": true}; no-op under
CK_TELEMETRY_DISABLED / pytest.

Hook stdin protocol: { tool_name, tool_input: { command }, session_id }.
"""

import json
import os
import re
import sys

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "_shared", "lib")
sys.path.insert(0, _LIB_DIR)

from telemetry_paths import write_bash_start  # noqa: E402

# Same matcher as track_script_execution.py (one source of truth for "is this a
# skill script" would be nicer, but keeping the regex local avoids a cross-import
# between two fail-open hooks).
SCRIPT_RE = re.compile(r"\.claude/skills/([^\s/]+/scripts/[^\s]+\.(?:py|sh))")


def main(raw: str) -> None:
    try:
        data = json.loads(raw or "{}")
        tool_input = data.get("tool_input") or {}
        cmd = tool_input.get("command") or ""
        if SCRIPT_RE.search(cmd):
            session = data.get("session_id") or os.environ.get("CK_SESSION_ID") or ""
            write_bash_start(session, cmd)
    except Exception:
        pass  # fail-open
    sys.stdout.write(json.dumps({"continue": True}))
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    main(raw)
