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

import hashlib
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


# --- TELEMETRY constant (read-side convenience for the lenses) ---------------
# A no-side-effect Path at the telemetry root (telemetry_dir() mkdir's; the
# lenses only READ, so they want a plain path). Env-aware at import; tests that
# need a different root reload the module after setting CK_TELEMETRY_DIR
# (mirrors test_telemetry_paths.py's _load helper).
TELEMETRY = (
    Path(os.environ["CK_TELEMETRY_DIR"])
    if os.environ.get("CK_TELEMETRY_DIR")
    else Path(project_dir()) / ".claude" / "telemetry"
)


def _encoded_project_slug() -> str:
    """Claude Code's per-project id: the absolute repo root with '/' → '-'.

    One home for the slug derivation; sessions_dir / memory_dir derive off it so
    the lenses and emit_session_summary.py share ONE resolver (DRY). Resolves
    dynamically per checkout — never a hardcoded machine path."""
    return project_dir().replace("/", "-")


def sessions_dir() -> Path:
    """Claude Code's per-project session-JSONL (transcript) dir:
    ~/.claude/projects/<encoded-root>/.

    CK_SESSIONS_DIR overrides it (tests point it at a tmp dir)."""
    env = os.environ.get("CK_SESSIONS_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "projects" / _encoded_project_slug()


def memory_dir() -> Path:
    """Claude Code's per-project persistent memory dir: <sessions_dir>/memory.

    CK_MEMORY_DIR overrides it (tests point it at a tmp dir)."""
    env = os.environ.get("CK_MEMORY_DIR")
    if env:
        return Path(env)
    return sessions_dir() / "memory"


# --- Low-volume gate --------------------------------------------------------
# Below this many data points a lens shows raw counts + a "chưa đủ dữ liệu"
# caveat and SUPPRESSES recommendations / prune advice (sparse data → noise).
LOW_VOLUME_THRESHOLD = 5


def low_volume_gate(count: int, threshold: int = LOW_VOLUME_THRESHOLD) -> bool:
    """True when ``count`` is below ``threshold`` → the lens is data-starved and
    must suppress advice (boundary: count == threshold is NOT gated)."""
    try:
        return int(count) < int(threshold)
    except (TypeError, ValueError):
        return True  # unknown volume → treat as gated (conservative)


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


# --- Bash-script duration timers (Pre/Post:Bash pairing) --------------------
# mark_bash_start.py (PreToolUse:Bash) stamps a monotonic start under
# .bashtimers/<key>; track_script_execution.py (PostToolUse:Bash) reads + clears
# it to compute `ms`. Dumb + fail-open; lives under the gitignored telemetry
# dir. Monotonic is system-wide on Linux → comparable across the two hook PIDs.
#
# Key = hash of the COMMAND ONLY (session deliberately excluded): the live
# PreToolUse and PostToolUse Bash payloads do not reliably carry the same
# session_id, so including it desynchronized the pair and dropped `ms`. Keying
# on the command alone makes pairing robust; the only cost is a rare collision
# when the identical command runs concurrently — acceptable for a single-user
# tool whose duration is explicitly "approx". `session` is kept in the helper
# signatures for call-site clarity but is not part of the key.
_BASHTIMER_MAX = 256  # cap the timer dir; opportunistic prune over this


def _bash_timer_path(session: str, command: str) -> Path:
    key = hashlib.sha1(command.encode("utf-8")).hexdigest()[:16]
    return telemetry_dir() / ".bashtimers" / key


def _prune_bash_timers(d: Path) -> None:
    try:
        entries = list(d.iterdir())
        if len(entries) <= _BASHTIMER_MAX:
            return
        # Oldest-first; drop the excess. Stale markers are harmless (a missing
        # pair just degrades to no-`ms`), so a coarse prune is fine.
        entries.sort(key=lambda e: e.stat().st_mtime)
        for e in entries[:-_BASHTIMER_MAX]:
            try:
                e.unlink()
            except OSError:
                pass
    except OSError:
        pass


def write_bash_start(session: str, command: str) -> None:
    """Stamp a monotonic start mark for a (session, command) Bash run. Fail-open."""
    if disabled():
        return
    try:
        p = _bash_timer_path(session, command)
        p.parent.mkdir(parents=True, exist_ok=True)
        _prune_bash_timers(p.parent)
        p.write_text(repr(time.monotonic()), encoding="utf-8")
    except Exception:
        pass  # fail-open: a missing mark just means no `ms`


def read_and_clear_bash_start(session: str, command: str):
    """Return elapsed milliseconds since the matching start mark (int ≥ 0), or
    None if no mark exists / it is unreadable. Clears the mark on read so it is
    never reused. Fail-open."""
    try:
        p = _bash_timer_path(session, command)
        if not p.exists():
            return None
        try:
            start = float(p.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            start = None
        try:
            p.unlink()
        except OSError:
            pass
        if start is None:
            return None
        return max(0, round((time.monotonic() - start) * 1000))
    except Exception:
        return None


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
