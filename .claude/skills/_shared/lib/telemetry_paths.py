"""
telemetry_paths.py — single source of truth for the append-only telemetry
sinks written by CM-local hooks (skill invocation, script execution, session
summary). One directory (.claude/telemetry/) so a jq read-back touches one place.

Contract: a telemetry write must NEVER break the hook/op it observes. Every
function here is fail-open — any error (unwritable dir, non-serializable
record) is swallowed. json.dumps is the ONLY serialization path (no manual
field concat → no forged-record injection from skill names / script paths).

CM-local dev tooling, NOT shipped in the pack bundle. Zero third-party deps
(stdlib only).
"""

import json
import os
import time
from pathlib import Path

MAX_SINK_BYTES = 8 * 1024 * 1024  # 8 MB → one .bak generation, then overwrite
DEDUP_TTL_S = 60 * 60  # 1 h — bounds the marker dir size


def project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def telemetry_dir() -> Path:
    # CK_TELEMETRY_DIR override lets tests redirect writes to a tmp dir.
    raw = os.environ.get("CK_TELEMETRY_DIR")
    d = Path(raw) if raw else Path(project_dir()) / ".claude" / "telemetry"
    d.mkdir(parents=True, exist_ok=True)
    return d


def sink_path(name: str) -> Path:
    return telemetry_dir() / name


def disabled() -> bool:
    # Telemetry is off when explicitly disabled OR during a pytest run
    # (PYTEST_CURRENT_TEST is set per-test by pytest) — keeps test runs from
    # polluting real sinks.
    return bool(os.environ.get("CK_TELEMETRY_DISABLED") or os.environ.get("PYTEST_CURRENT_TEST"))


def append_event(name: str, record: dict) -> None:
    if disabled():
        return
    try:
        # Serialize FIRST: a non-serializable record raises here, before any
        # file side-effect, so a bad record never leaves a half-written sink.
        line = json.dumps(record) + "\n"
        p = sink_path(name)
        try:
            if p.stat().st_size > MAX_SINK_BYTES:
                p.rename(str(p) + ".bak")
        except OSError:
            pass  # sink may not exist yet — nothing to rotate
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass  # fail-open: telemetry must never break the observed op


def _dedup_marker_path(key: str) -> Path:
    # Sanitize to a safe filename; key carries its own uniqueness (session|skill|minute).
    safe = "".join(c if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._|-" else "_" for c in str(key))[:200]
    return telemetry_dir() / ".dedup" / safe


def _prune_dedup(d: Path) -> None:
    try:
        now = time.time()
        for entry in d.iterdir():
            try:
                if now - entry.stat().st_mtime > DEDUP_TTL_S:
                    entry.unlink()
            except OSError:
                pass  # skip un-stat-able / racing entries
    except OSError:
        pass  # dir may not exist yet — nothing to prune


def append_event_once(name: str, record: dict, dedup_key: str) -> None:
    """
    append_event guarded by a cross-process dedup marker. Used by the ship-both
    skill-invocation hooks: if BOTH the Skill-tool event and the prompt-expansion
    event fire for one invocation, only the first (same dedup_key) is recorded.
    An atomic O_EXCL create is the lock; FileExistsError → already logged, skip.
    """
    if disabled():
        return
    try:
        marker = _dedup_marker_path(dedup_key)
        marker.parent.mkdir(parents=True, exist_ok=True)
        _prune_dedup(marker.parent)
        try:
            # O_CREAT | O_EXCL — atomic claim; FileExistsError → duplicate
            fd = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileExistsError:
            return  # another event already logged this invocation
        except OSError:
            pass  # any other marker error → fall through and still record
        append_event(name, record)
    except Exception:
        pass  # fail-open
