"""lens_forensics.py — per-session reconstruction from transcript JSONL: skills,
tool counts, token usage (input/output/cache), files touched, subagent spawns,
duration. Ported from human-analyzer's parse-session-jsonl-forensics.py; streams
line-by-line so large transcripts never load whole.

Pure gather → render-agnostic dict. READ-ONLY, fail-soft. CM-local (NOT shipped).
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import telemetry_paths

_TOKEN_KEYS = ("input_tokens", "output_tokens", "cache_read_input_tokens",
               "cache_creation_input_tokens")
_FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _parse_ts(raw: str):
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def parse_session(path: Path) -> dict:
    tools: dict[str, int] = defaultdict(int)
    skills: list[str] = []
    files: set[str] = set()
    subagents = 0
    tokens = {k: 0 for k in _TOKEN_KEYS}
    first_ts = last_ts = None
    try:
        fh = path.open(encoding="utf-8")
    except OSError:
        return {}
    with fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            ts = _parse_ts(rec.get("timestamp", "")) or _parse_ts(msg.get("timestamp", ""))
            if ts:
                first_ts = first_ts or ts
                last_ts = ts
            if not msg:
                continue
            usage = msg.get("usage")
            if isinstance(usage, dict):
                for k in _TOKEN_KEYS:
                    tokens[k] += int(usage.get(k, 0) or 0)
            for b in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                name = b.get("name", "?")
                tools[name] += 1
                inp = b.get("input") or {}
                if name == "Skill":
                    skills.append(inp.get("skill", "?"))
                elif name in _FILE_TOOLS and inp.get("file_path"):
                    files.add(inp["file_path"])
                elif name in ("Task", "Agent"):
                    subagents += 1
    dur = int((last_ts - first_ts).total_seconds()) if first_ts and last_ts else 0
    return {
        "session": path.stem,
        "skills": skills,
        "tool_counts": dict(sorted(tools.items(), key=lambda kv: -kv[1])),
        "tool_calls": sum(tools.values()),
        "files_modified": sorted(files),
        "subagents": subagents,
        "tokens": tokens,
        "total_tokens": tokens["input_tokens"] + tokens["output_tokens"],
        "duration_s": dur,
        "last_ts": last_ts.date().isoformat() if last_ts else None,
    }


def gather(session: str | None = None, all_sessions: bool = False) -> dict:
    sdir = telemetry_paths.sessions_dir()
    if not sdir.exists():
        return {"lens": "forensics", "count": 0, "sessions": [],
                "agg_total_tokens": 0, "agg_tool_counts": {}}
    if session:
        files = [sdir / f"{session}.jsonl"]
    else:
        files = sorted(sdir.glob("*.jsonl"))
        if not all_sessions:
            files = files[-1:]  # default: most recent session only
    parsed = []
    for f in files:
        if not f.exists():
            continue
        p = parse_session(f)
        if p:
            parsed.append(p)
    agg_tools: dict[str, int] = defaultdict(int)
    for p in parsed:
        for t, c in p["tool_counts"].items():
            agg_tools[t] += c
    return {
        "lens": "forensics",
        "count": len(parsed),
        "sessions": parsed,
        "agg_total_tokens": sum(p["total_tokens"] for p in parsed),
        "agg_tool_counts": dict(sorted(agg_tools.items(), key=lambda kv: -kv[1])),
    }
