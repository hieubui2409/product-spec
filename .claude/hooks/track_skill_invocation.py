#!/usr/bin/env python3
"""
track_skill_invocation.py — records every skill invocation to
.claude/telemetry/invocations.jsonl. CM-local dev tooling (NOT shipped in the
pack bundle). Fail-open + non-blocking: always emits {"continue": true}.

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

import json
import os
import re
import sys
from datetime import datetime, timezone

# Resolve the shared lib relative to this file's location.
_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "_shared", "lib")
sys.path.insert(0, _LIB_DIR)

from telemetry_paths import append_event_once  # noqa: E402


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


def main(raw: str) -> None:
    try:
        data = json.loads(raw or "{}")
        skill, via = extract_skill(data)
        if skill:
            now = datetime.now(timezone.utc)
            session = data.get("session_id") or os.environ.get("CK_SESSION_ID") or ""
            minute = now.strftime("%Y-%m-%dT%H:%M")  # YYYY-MM-DDTHH:MM dedup bucket
            append_event_once(
                "invocations.jsonl",
                {"ts": now.isoformat(), "skill": skill, "session": session, "via": via},
                f"{session}|{skill}|{minute}",
            )
    except Exception:
        pass  # fail-open: telemetry must never break a skill
    sys.stdout.write(json.dumps({"continue": True}))
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    main(raw)
