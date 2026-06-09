#!/usr/bin/env python3
"""
track_script_execution.py — records skill-script Bash runs to
.claude/telemetry/hook-telemetry.jsonl. Ships in the release bundle.
Registered on PostToolUse:Bash. Filters to commands that run a
.claude/skills/<skill>/scripts/<file>.(py|sh) — ignores plain git/ls/grep.

Exit signal (GATE H2): this Claude Code version exposes no reliable numeric
exit code in the PostToolUse payload, so exit is COARSELY inferred from
tool_response (is_error / interrupted) with a stderr-marker fallback. This
mirrors the shipped HA design — a precise exit_code field is not available.

Duration: if the PreToolUse:Bash counterpart (mark_bash_start.py) stamped a
start mark for this command, `ms` (wall-clock milliseconds) is included;
otherwise the record degrades gracefully without `ms`.

Fail-open + non-blocking + config gate are owned by the shared
hook_runtime.run_telemetry_hook wrapper; this file holds only the record-building
logic.

Hook stdin protocol: { tool_name, tool_input: { command }, tool_response, session_id }.
"""

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "telemetry", "scripts")
sys.path.insert(0, _LIB_DIR)
if _HOOKS_DIR not in sys.path:
    sys.path.append(_HOOKS_DIR)
import hook_runtime  # noqa: E402

# Shared matcher (single home in hook_runtime) — paired with mark_bash_start.
# group(1) = the skill-relative path skills/<skill>/scripts/<file>.py|sh.
SCRIPT_RE = hook_runtime.SCRIPT_RE

_STEM = Path(__file__).stem


def infer_exit(resp, stderr: str) -> int:
    if isinstance(resp, dict) and (resp.get("interrupted") or resp.get("is_error")):
        return 1
    if re.search(r"\b(Traceback|Error|Exception|exit code [1-9])\b", stderr, re.IGNORECASE):
        return 1
    return 0


def core(data: dict) -> None:
    from telemetry_paths import append_event, read_and_clear_bash_start  # lazy
    tool_input = data.get("tool_input") or {}
    cmd = tool_input.get("command") or ""
    m = SCRIPT_RE.search(cmd)
    if not m:
        return
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


def main(raw: str) -> None:
    """Test-compat shim: existing tests call main(raw) directly."""
    hook_runtime.run_telemetry_hook(_STEM, core, raw=raw)


if __name__ == "__main__":
    hook_runtime.run_telemetry_hook(_STEM, core)
