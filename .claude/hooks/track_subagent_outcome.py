#!/usr/bin/env python3
"""
track_subagent_outcome.py — SubagentStop hook. Records one line per finished
subagent to .claude/telemetry/subagent-outcomes.jsonl:
  {ts, agent_type, outcome, session}
outcome ∈ {success, api_error, timeout, blocked, unknown}. Powers the
reliability lens. Ships in the release bundle.

Outcome inference (in priority order):
  1. An explicit `outcome` field in the Stop payload, if it is a known enum.
  2. Classification of the subagent transcript tail (clean stop → success;
     terminal error text → api_error / timeout / blocked).
  3. Default `unknown` — NEVER fabricate `success` when the signal is absent
     (the reliability lens shows `unknown` honestly).

agent_type comes from the payload (`agent_type`/`subagent_type`) or, failing
that, the transcript filename (agent-<type>-<id>.jsonl).

Fail-open + non-blocking: always emits {"continue": true}; no-op under
CK_TELEMETRY_DISABLED / pytest.

Hook stdin protocol: { session_id, transcript_path, agent_type?, outcome? }.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_DIR = os.path.join(_HOOKS_DIR, "..", "skills", "telemetry", "scripts")
sys.path.insert(0, _LIB_DIR)

from telemetry_paths import append_event  # noqa: E402

OUTCOMES = {"success", "api_error", "timeout", "blocked", "unknown"}

# Vendored error taxonomy (small inline dict, not an import — keeps the hook
# self-contained and outside any shipped code path). Order matters: the first
# pattern that matches the terminal error text wins.
_TAXONOMY = [
    ("api_error", re.compile(r"rate.?limit|overloaded|api error|status 5\d\d|\b429\b|\b529\b|connection error|ECONNRESET", re.I)),
    ("timeout",   re.compile(r"timed?\s?out|timeout|deadline exceeded", re.I)),
    ("blocked",   re.compile(r"permission denied|not allowed|blocked by|refused|forbidden", re.I)),
]

TAIL_BYTES = 64 * 1024


def _agent_type_from_filename(transcript_path: str) -> str:
    """agent-<type>-<id>.jsonl → keep leading pure-alpha tokens as the type."""
    try:
        stem = Path(transcript_path).stem
    except Exception:
        return "unknown"
    parts = stem.split("-")
    if parts and parts[0] == "agent":
        parts = parts[1:]
    type_parts = []
    for p in parts:
        if any(ch.isdigit() for ch in p):  # id-like segment → stop
            break
        type_parts.append(p)
    return "-".join(type_parts) or "unknown"


def _read_tail_records(path: str) -> list:
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - TAIL_BYTES))
            text = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    recs = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except Exception:
            continue
    return recs


def _error_text(rec: dict) -> str:
    """Best-effort terminal-error text from a transcript record."""
    chunks = []
    msg = rec.get("message") if isinstance(rec, dict) else None
    if isinstance(msg, dict):
        content = msg.get("content")
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            for b in content:
                if isinstance(b, dict):
                    chunks.append(str(b.get("text") or b.get("content") or ""))
        if msg.get("error"):
            chunks.append(str(msg.get("error")))
    if isinstance(rec, dict) and rec.get("error"):
        chunks.append(str(rec.get("error")))
    return " ".join(c for c in chunks if c)


def classify_from_transcript(path: str) -> str:
    recs = _read_tail_records(path)
    if not recs:
        return "unknown"
    last = recs[-1]
    msg = last.get("message", {}) if isinstance(last.get("message"), dict) else {}
    # Clean stop with no pending tool_use → success.
    if msg.get("stop_reason") in ("end_turn", "stop_sequence"):
        content = msg.get("content") or []
        if not any(isinstance(c, dict) and c.get("type") == "tool_use" for c in content):
            return "success"
    text = _error_text(last)
    for label, pat in _TAXONOMY:
        if pat.search(text):
            return label
    return "unknown"


def infer_outcome(data: dict) -> str:
    explicit = str(data.get("outcome") or "").strip().lower()
    if explicit in OUTCOMES:
        return explicit
    tp = data.get("transcript_path")
    if tp:
        return classify_from_transcript(tp)
    return "unknown"


def main(raw: str) -> None:
    try:
        data = json.loads(raw or "{}")
        agent_type = str(
            data.get("agent_type") or data.get("subagent_type")
            or _agent_type_from_filename(data.get("transcript_path") or "")
        ) or "unknown"
        outcome = infer_outcome(data)
        session = data.get("session_id") or os.environ.get("CK_SESSION_ID") or ""
        append_event(
            "subagent-outcomes.jsonl",
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "agent_type": agent_type,
                "outcome": outcome,
                "session": session,
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
