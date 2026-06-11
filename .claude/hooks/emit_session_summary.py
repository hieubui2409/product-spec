#!/usr/bin/env python3
"""
emit_session_summary.py — on session Stop, emits one line to
.claude/telemetry/sessions.jsonl: {ts, session, skills[], tools{},
files_modified, subagents, duration_s}. Ships in the release bundle.

Reconstructs activity from the transcript (the Stop payload carries no tool
list / duration). Reads the head (real start ts → duration) + a bounded tail
(recent activity) so it stays fast (<5s) on huge transcripts; counts over the
tail window are an approximation, sufficient for adoption trending. `tokens`
are deliberately dropped (not needed for CM v1). Fail-open + non-blocking +
config gate are owned by hook_runtime.run_telemetry_hook.

Hook stdin protocol: { session_id, transcript_path }.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "telemetry", "scripts")
sys.path.insert(0, _LIB_DIR)
if _HOOKS_DIR not in sys.path:
    sys.path.append(_HOOKS_DIR)
import hook_runtime  # noqa: E402

_STEM = Path(__file__).stem

TAIL_BYTES = 256 * 1024
HEAD_BYTES = 256 * 1024
FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def resolve_transcript(data: dict):
    from telemetry_paths import sessions_dir  # lazy: skipped when disabled
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


def scan_head(p: str):
    """Scan the bounded head and return (first_timestamp, early_skills).

    The first transcript record is often a meta/summary line with no timestamp;
    reading only the literal first line then yields no start ts, so duration was
    computed as zero. Scan forward to the first record that HAS a timestamp.
    Also capture Skill invocations in the head — they cluster early and would be
    missed by the recent-activity tail on a long session (the empty-`skills` bug).
    """
    first_ts = None
    skills: list = []
    try:
        with open(p, "rb") as fh:
            head = fh.read(HEAD_BYTES)
    except OSError:
        return None, []
    for line in head.split(b"\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if first_ts is None:
            first_ts = rec.get("timestamp") or (rec.get("message") or {}).get("timestamp")
        msg = rec.get("message")
        if msg and isinstance(msg.get("content"), list):
            for b in msg["content"]:
                if b and b.get("type") == "tool_use" and b.get("name") == "Skill":
                    sk = (b.get("input") or {}).get("skill")
                    if sk:
                        skills.append(sk)
    return first_ts, skills


def first_timestamp(p: str):
    """Back-compat thin wrapper: first record timestamp (scans past leading no-ts records)."""
    return scan_head(p)[0]


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


def core(data: dict) -> None:
    from telemetry_paths import append_event  # lazy: skipped when disabled
    p = resolve_transcript(data)
    if not p:
        return
    first_ts, head_skills = scan_head(p)
    s = summarize(read_tail(p), first_ts)
    # Merge skills seen early (head) with recent (tail); dedup, preserve order.
    s["skills"] = list(dict.fromkeys(head_skills + s["skills"]))
    session = data.get("session_id") or Path(p).stem
    append_event(
        "sessions.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session": session,
            **s,
        },
    )


def main(raw: str) -> None:
    """Test-compat shim: existing tests call main(raw) directly."""
    hook_runtime.run_telemetry_hook(_STEM, core, raw=raw)


if __name__ == "__main__":
    hook_runtime.run_telemetry_hook(_STEM, core)
