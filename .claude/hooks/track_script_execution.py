#!/usr/bin/env python3
"""
track_script_execution.py — records skill-script Bash runs to
.claude/telemetry/hook-telemetry.jsonl. CM-local dev tooling (NOT shipped).
Registered on PostToolUse:Bash. Filters to commands that run a
.claude/skills/<skill>/scripts/<file>.(py|sh) — ignores plain git/ls/grep.

Exit signal (GATE H2): this Claude Code version exposes no reliable numeric
exit code in the PostToolUse payload, so exit is COARSELY inferred from
tool_response (is_error / interrupted) with a stderr-marker fallback. This
mirrors the shipped HA design — a precise exit_code field is not available.

Duration: if the PreToolUse:Bash counterpart (mark_bash_start.py) stamped a
start mark for this command, `ms` (wall-clock milliseconds) is included;
otherwise the record degrades gracefully without `ms`.

Fail-open + non-blocking: always emits {"continue": true}.

Hook stdin protocol: { tool_name, tool_input: { command }, tool_response, session_id }.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "_shared", "lib")
sys.path.insert(0, _LIB_DIR)

from telemetry_paths import append_event, read_and_clear_bash_start  # noqa: E402

# Capture the skill-relative script path: skills/<skill>/scripts/<file>.py|sh
SCRIPT_RE = re.compile(r"\.claude/skills/([^\s/]+/scripts/[^\s]+\.(?:py|sh))")


def infer_exit(resp, stderr: str) -> int:
    if isinstance(resp, dict) and (resp.get("interrupted") or resp.get("is_error")):
        return 1
    if re.search(r"\b(Traceback|Error|Exception|exit code [1-9])\b", stderr, re.IGNORECASE):
        return 1
    return 0


def main(raw: str) -> None:
    try:
        data = json.loads(raw or "{}")
        tool_input = data.get("tool_input") or {}
        cmd = tool_input.get("command") or ""
        m = SCRIPT_RE.search(cmd)
        if m:
            resp = data.get("tool_response")
            stderr = (resp.get("stderr") or "") if isinstance(resp, dict) else ""
            session = data.get("session_id") or os.environ.get("CK_SESSION_ID") or ""
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "hook:bash",
                "script": m.group(1),
                "exit": infer_exit(resp, stderr),
            }
            # Pair with the PreToolUse start mark, if present. Missing → no `ms`.
            ms = read_and_clear_bash_start(session, cmd)
            if ms is not None:
                record["ms"] = ms
            append_event("hook-telemetry.jsonl", record)
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
