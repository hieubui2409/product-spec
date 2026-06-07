#!/usr/bin/env python3
"""
emit_session_summary.py — on session Stop, emits one line to
.claude/telemetry/sessions.jsonl: {ts, session, skills[], tools{},
files_modified, subagents, duration_s}. Ships in the release bundle.

Reconstructs activity from the transcript (the Stop payload carries no tool
list / duration). Reads the head (real start ts → duration) + a bounded tail
(recent activity) so it stays fast (<5s) on huge transcripts; counts over the
tail window are an approximation, sufficient for adoption trending. `tokens`
are deliberately dropped (not needed for CM v1). Fail-open + non-blocking.

Hook stdin protocol: { session_id, transcript_path }.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "_shared", "lib")
sys.path.insert(0, _LIB_DIR)

from telemetry_paths import append_event, sessions_dir  # noqa: E402

TAIL_BYTES = 256 * 1024
FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def resolve_transcript(data: dict):
    # Prefer the explicit transcript_path from the Stop payload.
    tp = data.get("transcript_path") if data else None
    if tp and Path(tp).exists():
        return tp
    # Shared resolver (DRY): ~/.claude/projects/<encoded-root>/ — same dir the
    # lenses read, CK_SESSIONS_DIR-overridable.
    d = sessions_dir()
    sid = (data.get("session_id") if data else None) or os.environ.get("CK_SESSION_ID")
    if sid:
        p = d / f"{sid}.jsonl"
        if p.exists():
            return str(p)
    try:
        files = sorted(
            [(f, f.stat().st_mtime) for f in d.iterdir() if f.suffix == ".jsonl"],
            key=lambda x: x[1],
            reverse=True,
        )
        return str(files[0][0]) if files else None
    except OSError:
        return None


def first_timestamp(p: str):
    try:
        with open(p, "rb") as fh:
            chunk = fh.read(8192)
        first_line = chunk.split(b"\n")[0]
        rec = json.loads(first_line.decode("utf-8", errors="replace"))
        return rec.get("timestamp") or (rec.get("message") or {}).get("timestamp")
    except Exception:
        return None


def read_tail(p: str) -> str:
    with open(p, "rb") as fh:
        fh.seek(0, 2)
        size = fh.tell()
        start = max(0, size - TAIL_BYTES)
        fh.seek(start)
        return fh.read().decode("utf-8", errors="replace")


def summarize(text: str, start_ts) -> dict:
    skills = []
    tools: dict = {}
    files: set = set()
    subagents = 0
    last_ts = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        ts = rec.get("timestamp") or (rec.get("message") or {}).get("timestamp")
        if ts:
            last_ts = ts
        msg = rec.get("message")
        if not msg or not isinstance(msg.get("content"), list):
            continue
        for b in msg["content"]:
            if not b or b.get("type") != "tool_use":
                continue
            name = b.get("name", "")
            tools[name] = tools.get(name, 0) + 1
            inp = b.get("input") or {}
            if name == "Skill" and inp.get("skill"):
                skills.append(inp["skill"])
            elif name in FILE_TOOLS and inp.get("file_path"):
                files.add(inp["file_path"])
            elif name in ("Task", "Agent"):
                subagents += 1

    start = start_ts or last_ts
    dur = 0
    if start and last_ts:
        try:
            delta = (
                datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                - datetime.fromisoformat(start.replace("Z", "+00:00"))
            ).total_seconds()
            dur = max(0, round(delta))
        except Exception:
            dur = 0

    return {
        "skills": list(dict.fromkeys(skills)),  # deduplicate, preserve order
        "tools": tools,
        "files_modified": len(files),
        "subagents": subagents,
        "duration_s": dur,
    }


def main(raw: str) -> None:
    try:
        data = json.loads(raw or "{}")
        p = resolve_transcript(data)
        if p:
            s = summarize(read_tail(p), first_timestamp(p))
            session = data.get("session_id") or Path(p).stem
            append_event(
                "sessions.jsonl",
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "session": session,
                    **s,
                },
            )
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
