#!/usr/bin/env python3
"""product_spec_critique_nudge: opt-in, ADVISORY Stop hook for cleanmatic:product-spec-critique.

After the PO runs `--validate`, if the spec has drifted by at least
`critique_drift_threshold` node bodies since the last critique, this hook drops a
ONE-LINE nudge suggesting `/product-spec-critique`. It never auto-runs the critique (token
+ web cost) and, unlike `memory_gap_hook`, it NEVER blocks: a critique is opinion,
not a hard gate. Output is `hookSpecificOutput.additionalContext` + exit 0, never a
`decision: block`, never exit 2.

Posture (mirrors memory_gap_hook's SCAFFOLDING, not its block protocol):
  * recommend-and-ask, nudge-once per session per drift-state (honor stop_hook_active)
  * cheap no-op early-exit; never builds the graph on an ordinary Stop
  * never registers itself (the installer's `--critique-hook` does, opt-in only)
  * never writes under docs/product/: its only files are ephemeral $TMPDIR markers
  * any failure degrades to a silent allow (exit 0), since a hook must never break Stop

Cheap gate (the reason this is near-free on ordinary stops): it first stats
`last_validated.json` vs `last_critique.json`. It proceeds ONLY when a `--validate`
has happened since the last critique (last_validated newer / critique absent). Only
then does it shell to `critique_scan.py --drift --vs-validated`, which compares
marker-vs-marker (no live graph build) WHEN a judgment cache exists. Caveat: if the
PO validated but `judgments.json` is absent/empty, critique_scan falls back to ONE
live graph build; still gated behind the cheap mtime check + a short subprocess
timeout, so it runs at most once per qualifying Stop, never on ordinary stops.
Drift logic lives once in critique_scan (DRY).
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

ALLOW_EXIT = 0


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def _project_dir(stdin_cwd: Optional[str] = None) -> Optional[str]:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or stdin_cwd
    return root or None


def _critique_scan_path() -> Path:
    """`.claude/hooks/product_spec_critique_nudge.py` -> `.claude/skills/product-spec-critique/scripts/critique_scan.py`."""
    claude_dir = Path(__file__).resolve().parent.parent  # .claude/
    return claude_dir / "skills" / "product-spec-critique" / "scripts" / "critique_scan.py"


def _memory_dir(project_dir: str) -> Path:
    return Path(project_dir) / "docs" / "product" / ".memory"


# ---------------------------------------------------------------------------
# Ephemeral, session-keyed nudge-once marker (in $TMPDIR, never committed)
# ---------------------------------------------------------------------------

def _temp_dir() -> Path:
    return Path(os.environ.get("TMPDIR") or tempfile.gettempdir())


def safe_id(session_id: str) -> str:
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in (session_id or "_"))


def _nudge_marker_path(session_id: str, changed_count: int) -> Path:
    """Per-session + per-drift-bucket "already nudged" marker. A new drift count
    (more nodes changed since) re-arms the nudge; the same count stays silent."""
    return _temp_dir() / f"product-spec-critique-nudged-{safe_id(session_id)}-{changed_count}"


def _nudge_already_shown(session_id: str, changed_count: int) -> bool:
    return _nudge_marker_path(session_id, changed_count).exists()


def _mark_nudge_shown(session_id: str, changed_count: int) -> None:
    try:
        _nudge_marker_path(session_id, changed_count).write_text("1", encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Cheap gate + drift
# ---------------------------------------------------------------------------

def _validate_newer_than_critique(project_dir: str) -> bool:
    """The cheap gate: proceed only if a `--validate` happened since the last
    critique. Two stats, no graph build.

    - last_validated.json absent  → PO never validated → no nudge (False).
    - last_critique.json absent   → validated but never critiqued → proceed (True);
      drift returns first_run (over False) so no nudge actually fires, but the gate
      stays cheap and the logic single-homed in critique_scan.
    - both present                → proceed only if last_validated is strictly newer.
    """
    mem = _memory_dir(project_dir)
    lv = mem / "last_validated.json"
    lc = mem / "last_critique.json"
    if not lv.exists():
        return False
    if not lc.exists():
        return True
    try:
        return lv.stat().st_mtime > lc.stat().st_mtime
    except OSError:
        return False


def _run_drift(project_dir: str) -> Optional[Dict[str, Any]]:
    """Shell to critique_scan --drift --vs-validated. Returns the parsed result, or
    None on any failure (missing script, bad JSON, non-zero exit) → caller no-ops."""
    scan = _critique_scan_path()
    if not scan.is_file():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(scan), "--drift", "--vs-validated",
             "--root", project_dir],
            # Short budget: this is an advisory nudge on the Stop path. If a
            # pathological spec makes the (rare) live-build fallback slow, fail
            # silent fast rather than stall turn-end; the PO can run it manually.
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _nudge_text(changed_count: int) -> str:
    return (
        f"spec đã đổi {changed_count} node kể từ lần critique gần nhất, "
        "muốn nghe chửi thật? chạy `/product-spec-critique`."
    )


# ---------------------------------------------------------------------------
# Stop handler
# ---------------------------------------------------------------------------

def handle_stop(payload: Dict[str, Any], project_dir: Optional[str]) -> int:
    project_dir = project_dir or _project_dir(payload.get("cwd"))
    if not project_dir:
        return ALLOW_EXIT

    docs_product = Path(project_dir) / "docs" / "product"
    if not docs_product.is_dir():
        return ALLOW_EXIT

    # Cheap gate: only a fresh `--validate` since the last critique is worth checking.
    if not _validate_newer_than_critique(project_dir):
        return ALLOW_EXIT

    result = _run_drift(project_dir)
    if not result or not result.get("over"):
        return ALLOW_EXIT

    # Nudge-once. Honor stop_hook_active (don't re-nudge on a continuation) AND a
    # per-session+drift-count marker (so a stuck-false stop_hook_active can't loop).
    if bool(payload.get("stop_hook_active", False)):
        return ALLOW_EXIT
    session_id = payload.get("session_id") or ""
    changed_count = int(result.get("changed_count") or 0)
    if _nudge_already_shown(session_id, changed_count):
        return ALLOW_EXIT
    _mark_nudge_shown(session_id, changed_count)

    nudge = _nudge_text(changed_count)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": nudge,
        }
    }
    # Advisory only: additionalContext + exit 0. NEVER decision:block / exit 2.
    print(json.dumps(output, ensure_ascii=False))
    return ALLOW_EXIT


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

def _read_stdin() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def main(argv: Optional[list] = None) -> int:
    payload = _read_stdin()
    project_dir = _project_dir(payload.get("cwd"))
    try:
        return handle_stop(payload, project_dir)
    except Exception:  # noqa: BLE001 - a hook crash must never break Stop
        return ALLOW_EXIT


if __name__ == "__main__":
    sys.exit(main())
