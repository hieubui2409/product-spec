#!/usr/bin/env python3
"""
track_skill_invocation.py — records every skill invocation to
.claude/telemetry/invocations.jsonl. Ships in the release bundle.
Fail-open + non-blocking + config gate are owned by hook_runtime.run_telemetry_hook.
ONE config key (track_skill_invocation) gates BOTH registrations below.

GATE C1 (ship-both): the runtime event that carries a skill invocation is not
empirically pinned for this Claude Code version, so this hook is registered on
BOTH candidate events and reads either payload shape:
  - PreToolUse with tool_name "Skill"   → tool_input.skill | tool_input.name
  - UserPromptExpansion (slash-command) → command (first token, slash stripped)
append_event_once collapses a same (session|skill|minute) double-fire to one
record, so if both events fire for one invocation it is logged exactly once.

Hook stdin protocol (either): { tool_name, tool_input, session_id, command,
hook_event_name }.
"""

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve the shared lib relative to this file's location.
_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "telemetry", "scripts")
sys.path.insert(0, _LIB_DIR)
if _HOOKS_DIR not in sys.path:
    sys.path.append(_HOOKS_DIR)
import hook_runtime  # noqa: E402

_STEM = Path(__file__).stem


def extract_skill(data: dict) -> tuple[str, str]:
    """Return (skill_name, via_label) from a hook payload dict."""
    # PreToolUse path: the Skill tool carries the skill name in tool_input.
    if data.get("tool_name") == "Skill":
        inp = data.get("tool_input") or {}
        skill = inp.get("skill") or inp.get("name") or ""
        return str(skill), "PreToolUse:Skill"
    # UserPromptExpansion path: `command` is the invoked command/skill name.
    if data.get("command") or data.get("hook_event_name") == "UserPromptExpansion":
        cmd = str(data.get("command") or "").strip().lstrip("/")
        skill = re.split(r"\s+", cmd)[0] if cmd else ""
        return skill, "UserPromptExpansion"
    return "", ""


def core(data: dict) -> None:
    from telemetry_paths import append_event_once  # lazy: skipped when disabled
    skill, via = extract_skill(data)
    if not skill:
        return
    now = datetime.now(timezone.utc)
    session = data.get("session_id") or os.environ.get("CK_SESSION_ID") or ""
    minute = now.strftime("%Y-%m-%dT%H:%M")  # YYYY-MM-DDTHH:MM dedup bucket
    append_event_once(
        "invocations.jsonl",
        {"ts": now.isoformat(), "skill": skill, "session": session, "via": via},
        f"{session}|{skill}|{minute}",
    )


def main(raw: str) -> None:
    """Test-compat shim: existing tests call main(raw) directly."""
    hook_runtime.run_telemetry_hook(_STEM, core, raw=raw)


if __name__ == "__main__":
    hook_runtime.run_telemetry_hook(_STEM, core)
