#!/usr/bin/env python3
"""
track_artifact_edits.py — PostToolUse hook that records ONE path-only event
for every Edit/Write/MultiEdit that touches a spec artifact under docs/product/.

Privacy by construction: `_build_record` is a WHITELIST — it builds the dict
from exactly {ts, artifact_path, op, session}. It never touches tool_response,
old_string, new_string, or any other content field. A new content field in a
future payload therefore cannot leak because it is simply never read.

Hook stdin protocol: { tool_name, tool_input: { file_path }, session_id }.
Everything else is ignored.

Fail-open: any error in core() is swallowed by hook_runtime.run_telemetry_hook.
Disabled under pytest (PYTEST_CURRENT_TEST) + CK_TELEMETRY_DISABLED via telemetry_paths.
"""

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

# The spec artifact root — only edits whose file_path starts with this prefix
# (or equals it) are recorded. Relative paths are matched as-is; absolute paths
# are matched after stripping the project root prefix.
_SPEC_PREFIX = "docs/product"

# Sink name — all artifact-edit events land in one file, one event per line.
_SINK_NAME = "artifact-events.jsonl"


def _is_spec_artifact(path: str) -> bool:
    """Return True when path is inside the spec artifact tree (docs/product/).

    Accepts both relative paths (docs/product/...) and absolute paths by
    normalizing away the project root prefix when present.

    Segment-boundary rule: only matches when the path segment is exactly
    'product' — i.e. the path equals 'docs/product' or starts with
    'docs/product/'.  Sibling dirs such as 'docs/productx/' or
    'docs/product-archive/' are NOT matched."""
    if not path:
        return False
    # Normalize separators for robustness
    norm = path.replace("\\", "/")
    # Strip any leading absolute prefix up to the 'docs/product' segment.
    # Find the position of 'docs/product' in the normalized path.
    needle = "docs/product"
    idx = norm.find(needle)
    if idx == -1:
        return False
    # Left boundary: must start at position 0 or immediately after a '/'.
    if idx != 0 and norm[idx - 1] != "/":
        return False
    # Right boundary: the character immediately after 'docs/product' must be
    # either absent (path equals 'docs/product') or a '/' (subdirectory).
    after = norm[idx + len(needle):]
    return after == "" or after.startswith("/")


def _build_record(path: str, op: str, session: str) -> dict:
    """Pure function: WHITELIST construction of the persisted record.

    Exactly {ts, artifact_path, op, session} — nothing else. Callers pass
    only the three values already extracted from the payload; no content
    field ever enters this function."""
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "artifact_path": path,
        "op": op,
        "session": session,
    }


def core(data: dict) -> None:
    from telemetry_paths import append_event  # lazy import

    tool_input = data.get("tool_input") or {}
    # file_path is present for Edit/Write; MultiEdit also uses file_path
    path = tool_input.get("file_path") or ""
    if not _is_spec_artifact(path):
        return

    op = data.get("tool_name") or "unknown"
    session = data.get("session_id") or os.environ.get("CK_SESSION_ID") or ""

    record = _build_record(path, op, session)
    append_event(_SINK_NAME, record)


def main(raw: str) -> None:
    """Test-compat shim: existing tests call main(raw) directly."""
    hook_runtime.run_telemetry_hook(_STEM, core, raw=raw)


if __name__ == "__main__":
    hook_runtime.run_telemetry_hook(_STEM, core)
