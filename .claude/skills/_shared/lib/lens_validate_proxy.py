"""lens_validate_proxy.py — the one opted-in EFFECTIVENESS signal: after a
product-spec run, did validate pass? An INTERNAL-QUALITY proxy (spec well-formed)
— explicitly NOT E3 market/user outcome (deferred, untouched).

Source decision tree (Phase-6, evidence-based):
  1. last_validated.json marker (docs/product/.memory/, written on --validate)
     → EXACT "last status": validated vs never, + validated_at. Single-point
     (overwritten each validate), so it gives the last status, not a rate.
  2. hook-telemetry.jsonl validate-script exit history (check_*/strict_gate runs)
     → the directional pass RATE over a window (exit 0 = pass). Carries "approx".
  3. Neither trustworthy → available:False, honest "not available on current
     data" (no fabricated metric).

Pure gather → render-agnostic dict. READ-ONLY, fail-soft. Ships in the release bundle.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import telemetry_paths

# product-spec validate-flow scripts whose Bash exit is a pass/fail signal.
_VALIDATE_SCRIPT_RE = re.compile(r"product-spec/scripts/(check_[a-z_]+|strict_gate)\.py")


def _marker_path() -> Path:
    return Path(telemetry_paths.project_dir()) / "docs" / "product" / ".memory" / "last_validated.json"


def _hook_path():
    return telemetry_paths.TELEMETRY / "hook-telemetry.jsonl"


def _parse_ts(raw: str):
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _read_marker() -> dict | None:
    try:
        data = json.loads(_marker_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) and data.get("snapshot") else None


def _validate_runs(days: int) -> tuple[int, int]:
    """(runs, passes) of validate-flow scripts within the window."""
    p = _hook_path()
    if not p.exists():
        return 0, 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    runs = passes = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not _VALIDATE_SCRIPT_RE.search(rec.get("script", "")):
            continue
        ts = _parse_ts(rec.get("ts", ""))
        if ts and ts < cutoff:
            continue
        runs += 1
        if int(rec.get("exit", 0) or 0) == 0:
            passes += 1
    return runs, passes


def gather(days: int = 30) -> dict:
    marker = _read_marker()
    runs, passes = _validate_runs(days)
    if marker is None and runs == 0:
        return {
            "lens": "validate_proxy",
            "available": False,
            "reason": "not available on current data (no validate marker, no validate-script runs)",
            "internal_quality": True,
            "not_e3": True,
        }
    last_status = "validated" if marker else "never"
    # pass_rate is None (not 0) when there are no validate-script runs in the
    # window — 0 runs is "no rate", NOT "0% pass". The marker still gives the
    # last status, so the lens stays available on a marker alone.
    pass_rate = round(100 * passes / runs) if runs else None
    return {
        "lens": "validate_proxy",
        "available": True,
        "internal_quality": True,
        "not_e3": True,
        "validate_pass_rate": pass_rate,
        "last_status": last_status,
        "validated_at": (marker or {}).get("validated_at"),
        "total": runs,
        "source": "last_validated.json marker (exact) + hook-telemetry validate-script exits (approx)",
        "gated": telemetry_paths.low_volume_gate(runs),
    }
