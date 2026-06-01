#!/usr/bin/env python3
"""memory_gap_hook — opt-in Tier-1 Stop hook for the product-spec memory layer.

A thin, deterministic POLICY wrapper around the `memory_gap` detector. It owns
NO detection logic: it resolves the product-spec skill `scripts/` dir from
`$CLAUDE_PROJECT_DIR`, imports `memory_gap.collect`, and only decides — per
signal — whether to BLOCK turn-end (force the LLM to record the missing memory)
or ALLOW it. Detection is the single DRY home `memory_gap.py`; this file never
re-implements it.

It ships at the top-level `.claude/hooks/` (the hook convention) ALONGSIDE the
ck-managed `*.cjs` handlers — which it never touches. It runs under the shared
skill venv (`./.claude/skills/.venv/bin/python3`); the installer registers it
in the gitignored `.claude/settings.local.json` (opt-in only, never auto).

Two modes (one file):
  - default (no flag) → `Stop` policy. Reads Stop stdin, runs the no-op guard,
    then the detector, then emits a block decision or exits 0.
  - `--post-tool-use`  → `PostToolUse` touched-flag writer. Reads tool stdin and
    sets an EPHEMERAL, session-keyed "touched docs/product" flag in $TMPDIR
    (NOT under docs/product/, NOT committed). The flag is the no-op guard's
    cheap "did this session touch the spec?" signal.

Per-signal policy (locked):
  - `fence_breach`            → PERSIST. Block while the gap remains; ignores
                                `stop_hook_active`. A working-tree write landed
                                outside docs/product/ — a hard fence violation,
                                independently caught by check_fence. Loop-safe
                                via an internal block-count backstop (the CC
                                8-cap is a bonus, never the sole guarantee).
  - `validate_no_marker`,    → NUDGE-ONCE. Block once with an actionable reason;
  - `approved_changed_no_dec`  honor `stop_hook_active` so the continuation's
                                Stop is allowed. A false positive (a legit
                                re-approval) costs exactly one re-judgment, never
                                a loop. The reason names the writer command + the
                                `--ack-no-dec` escape that silences a recurring
                                false fire.

Block contract (dual-path, so the model gets the reason whichever CC honors):
  JSON `{"ok": false, "decision": "block", "reason": ..., "signals": [...]}` on
  stdout, the same reason on stderr, exit 2.

The hook NEVER writes the memory layer — it only nudges; the LLM writes via the
existing writers (`--decision`, `--validate`, `--ack-no-dec`). The only file it
itself creates is the ephemeral touched-flag.
"""

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Exit codes. 2 = CC blocking error (stderr fed back to Claude); 0 = allow.
BLOCK_EXIT = 2
ALLOW_EXIT = 0

# Per-signal policy buckets. Fence breaches persist (block until fixed); the
# other gap signals nudge once (honor stop_hook_active).
_PERSIST_SIGNALS = frozenset({"fence_breach"})
_NUDGE_ONCE_SIGNALS = frozenset({"validate_no_marker", "approved_changed_no_dec"})

# Internal fence-persist backstop: after this many consecutive self-blocks for
# the same session, downgrade to a final allow so the user can never be stranded
# in a loop if the host's own consecutive-block cap is absent or named differently.
# The cap is an internal guarantee here, not a dependency on host behaviour; the
# fence breach is independently caught by the check_fence chokepoint regardless.
_FENCE_BLOCK_CAP = 8


# ---------------------------------------------------------------------------
# Skill-scripts resolution + detector import (DRY: reuse memory_gap, no copy)
# ---------------------------------------------------------------------------

def _project_dir(stdin_cwd: Optional[str] = None) -> Optional[str]:
    """The product-spec project root. CLAUDE_PROJECT_DIR (set by CC) wins; the
    Stop/PostToolUse stdin `cwd` is the fallback. None if neither is usable."""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or stdin_cwd
    return root or None


def _scripts_dir_candidates(project_dir: Optional[str]) -> List[Path]:
    """Where the product-spec `scripts/` dir might live, most-specific first.

    The hook and the skill SHIP together, so the hook's own location is the most
    reliable anchor (`.claude/hooks/ -> .claude/skills/product-spec/scripts/`).
    `$CLAUDE_PROJECT_DIR` is the documented resolver and comes first when set, but
    it can point at a spec project that does not host the install (e.g. a test
    fixture), so the `__file__`-relative sibling is the durable fallback."""
    rel = Path(".claude") / "skills" / "product-spec" / "scripts"
    candidates: List[Path] = []
    if project_dir:
        candidates.append(Path(project_dir) / rel)
    # .claude/hooks/memory_gap_hook.py -> .claude/ -> skills/product-spec/scripts
    here = Path(__file__).resolve().parent.parent  # the .claude/ dir
    candidates.append(here / "skills" / "product-spec" / "scripts")
    return candidates


def _import_memory_gap(project_dir: Optional[str]):
    """sys.path.insert the skill scripts dir and import the detector. The single
    DRY home for the signals — never re-implemented here. Tries each candidate
    location (project-dir then the hook's own sibling) until the import resolves."""
    last_exc: Optional[Exception] = None
    for cand in _scripts_dir_candidates(project_dir):
        if not cand.is_dir():
            continue
        sd = str(cand)
        if sd not in sys.path:
            sys.path.insert(0, sd)
        try:
            import memory_gap  # noqa: E402  (resolved only after the path insert)
            return memory_gap
        except ImportError as exc:  # this candidate's dir is incomplete — try next
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc
    raise ModuleNotFoundError("product-spec scripts/ dir not found for memory_gap")


# ---------------------------------------------------------------------------
# Ephemeral, session-keyed touched-flag (in $TMPDIR — not under docs/product/,
# not committed, no fence needed: it is transient session state).
# ---------------------------------------------------------------------------

def _temp_dir() -> Path:
    """Read $TMPDIR fresh each call (tempfile.gettempdir() caches its first read,
    which breaks per-test TMPDIR isolation). Falls back to the stdlib default."""
    return Path(os.environ.get("TMPDIR") or tempfile.gettempdir())


def _flag_path(session_id: str) -> Path:
    # `safe_id` is the single sanitization home (resolved at call time, so its
    # definition below this function is fine) — never re-inline the char filter.
    return _temp_dir() / f"product-spec-touched-{safe_id(session_id)}"


def set_touched_flag(session_id: str) -> Path:
    """Mark "this session touched docs/product/". Ephemeral; best-effort (a write
    failure must never break the user's turn — the flag is an optimization)."""
    path = _flag_path(session_id)
    try:
        path.write_text("1", encoding="utf-8")
    except OSError:
        pass
    return path


def touched_flag_set(session_id: str) -> bool:
    return _flag_path(session_id).exists()


def _block_counter_path(session_id: str) -> Path:
    return _temp_dir() / f"product-spec-fenceblocks-{safe_id(session_id)}"


def safe_id(session_id: str) -> str:
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in (session_id or "_"))


def _bump_fence_block_count(session_id: str) -> int:
    """Track consecutive fence self-blocks for the session (the internal backstop).
    Best-effort; on any IO error treat as the first block (never crash the turn)."""
    path = _block_counter_path(session_id)
    try:
        n = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        n = 0
    n += 1
    try:
        path.write_text(str(n), encoding="utf-8")
    except OSError:
        pass
    return n


def _nudge_signal_hash(nudge: List[Dict[str, Any]]) -> str:
    """A stable 8-hex fingerprint of the nudge signal SET, keyed on the sorted
    (type, subject) pairs. Same set of nudge signals → same marker, so "we already
    nudged for exactly this gap" is decidable across turns. A new/changed gap (a
    different type or subject) yields a fresh marker and re-arms the one-time block."""
    pairs = sorted(
        (str(s.get("type") or ""), str(s.get("subject") or "")) for s in nudge
    )
    blob = "\n".join(f"{t}\x1f{subj}" for t, subj in pairs)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8]


def _nudge_marker_path(session_id: str, nudge: List[Dict[str, Any]]) -> Path:
    """Per-session + per-nudge-signal-set "already nudged once" marker in $TMPDIR
    (ephemeral, mirrors the touched-flag / fence-block-counter scheme)."""
    return _temp_dir() / (
        f"product-spec-nudged-{safe_id(session_id)}-{_nudge_signal_hash(nudge)}"
    )


def _nudge_already_shown(session_id: str, nudge: List[Dict[str, Any]]) -> bool:
    """True if this exact nudge signal set was already blocked once this session."""
    return _nudge_marker_path(session_id, nudge).exists()


def _mark_nudge_shown(session_id: str, nudge: List[Dict[str, Any]]) -> None:
    """Record that we blocked once for this nudge signal set. Best-effort: an IO
    error must never break the turn (worst case we nudge once more, never a loop
    of indefinite re-blocks — the marker, not stop_hook_active, is the backstop)."""
    try:
        _nudge_marker_path(session_id, nudge).write_text("1", encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

def _build_reason(persist: List[Dict[str, Any]],
                  nudge: List[Dict[str, Any]]) -> str:
    """One actionable, plain-language block reason naming the writer(s) — never a
    hard guarantee. Fence first (it blocks until fixed), then the nudges."""
    lines: List[str] = []
    if persist:
        files = sorted({s.get("subject") for s in persist if s.get("subject")})
        lines.append(
            "A write landed OUTSIDE docs/product/ "
            f"({', '.join(files) or 'see findings'}). The product-spec skill only "
            "writes specs under docs/product/. Move the file under docs/product/ "
            "(or remove it) before ending the turn — this gap persists until fixed."
        )
    for s in nudge:
        subj = s.get("subject")
        if s.get("type") == "approved_changed_no_dec":
            lines.append(
                f"Approved artifact {subj} changed with no Decision recorded. "
                "Re-judge it: record the ruling with `--decision` "
                "(decision_register) if warranted, else run "
                f"`memory_gap.py --ack-no-dec {subj}` then stop. "
                "This nudge fires once; the continuation is allowed."
            )
        elif s.get("type") == "validate_no_marker":
            lines.append(
                "The spec drifted from the last validated baseline (or was never "
                "validated). Run `--validate` to re-baseline, then stop. "
                "This nudge fires once; the continuation is allowed."
            )
    return " ".join(lines)


def _decide(signals: List[Dict[str, Any]],
            stop_hook_active: bool,
            session_id: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Apply the per-signal policy. Returns (block?, reason, blocking_signals).

    - Any persist signal → block, ignoring stop_hook_active (until the internal
      backstop trips, then allow with a final note so it can never loop).
    - Nudge-once signals → block only on the FIRST stop (stop_hook_active False);
      allowed on the continuation (stop_hook_active True).
    """
    persist = [s for s in signals if s.get("type") in _PERSIST_SIGNALS]
    nudge = [s for s in signals if s.get("type") in _NUDGE_ONCE_SIGNALS]

    if persist:
        count = _bump_fence_block_count(session_id)
        if count > _FENCE_BLOCK_CAP:
            # Backstop: never strand the user — check_fence still catches the
            # breach independently. Allow, leaving the breach to the chokepoint.
            return (False, "", [])
        # Fence persists regardless of stop_hook_active. Surface nudges alongside.
        blocking = persist + ([] if stop_hook_active else nudge)
        return (True, _build_reason(persist, [] if stop_hook_active else nudge), blocking)

    if nudge and not stop_hook_active:
        # Nudge-once with a backstop that does NOT rely on stop_hook_active flipping
        # true on the continuation (that host field is documentation-only on the
        # target CC version). An ephemeral per-session + per-signal-set marker
        # self-limits the nudge: block exactly once for this gap, then allow — so a
        # stuck-false stop_hook_active can never make a nudge re-block every turn.
        if _nudge_already_shown(session_id, nudge):
            return (False, "", [])  # already nudged once for this gap → allow
        _mark_nudge_shown(session_id, nudge)
        return (True, _build_reason([], nudge), nudge)

    # No persist signal, and either no nudge or this is the continuation → allow.
    return (False, "", [])


# ---------------------------------------------------------------------------
# Stop handler
# ---------------------------------------------------------------------------

def handle_stop(payload: Dict[str, Any], project_dir: Optional[str]) -> int:
    """Run the Stop policy. Returns the process exit code (BLOCK_EXIT / ALLOW_EXIT)
    and, on a block, prints the decision JSON to stdout + the reason to stderr."""
    project_dir = project_dir or _project_dir(payload.get("cwd"))
    if not project_dir:
        return ALLOW_EXIT  # no resolvable root → nothing to do (degrade)

    # No-op guard: skip everything unless the spec tree exists AND this session
    # actually touched it. Cheap; never imports the detector on unrelated turns.
    session_id = payload.get("session_id") or ""
    docs_product = Path(project_dir) / "docs" / "product"
    if not docs_product.is_dir():
        return ALLOW_EXIT
    if not touched_flag_set(session_id):
        return ALLOW_EXIT

    try:
        memory_gap = _import_memory_gap(project_dir)
        signals = memory_gap.collect(project_dir)
    except Exception:  # noqa: BLE001 — advisory: a hook must never break turn-end
        return ALLOW_EXIT

    stop_hook_active = bool(payload.get("stop_hook_active", False))
    block, reason, blocking = _decide(signals, stop_hook_active, session_id)
    if not block:
        return ALLOW_EXIT

    decision = {
        "ok": False,
        "decision": "block",
        "reason": reason,
        "signals": blocking,
    }
    # Dual-path block: JSON-decision on stdout, the same reason on stderr+exit 2,
    # so the reason reaches the model whichever path the installed CC honors.
    print(json.dumps(decision, ensure_ascii=False, default=str))
    print(reason, file=sys.stderr)
    return BLOCK_EXIT


# ---------------------------------------------------------------------------
# PostToolUse handler (touched-flag writer)
# ---------------------------------------------------------------------------

def handle_post_tool_use(payload: Dict[str, Any],
                         project_dir: Optional[str]) -> int:
    """Set the touched-flag when a Write/Edit landed under docs/product/. Reads
    ONLY `tool_input.file_path` (never the ambiguous result field). Always allows
    (exit 0) — this handler only records state, never blocks a tool."""
    project_dir = project_dir or _project_dir(payload.get("cwd"))
    if not project_dir:
        return ALLOW_EXIT

    tool_input = payload.get("tool_input")
    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(file_path, str) or not file_path:
        return ALLOW_EXIT

    docs_product = (Path(project_dir) / "docs" / "product").resolve()
    try:
        target = Path(file_path)
        if not target.is_absolute():
            target = Path(project_dir) / target
        target = target.resolve()
    except OSError:
        return ALLOW_EXIT

    # Set the flag only when the write is under docs/product/ (resolve-then-contain).
    if target == docs_product or docs_product in target.parents:
        set_touched_flag(payload.get("session_id") or "")
    return ALLOW_EXIT


# ---------------------------------------------------------------------------
# CLI entry (CC invokes this file with stdin)
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


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    post_mode = "--post-tool-use" in argv
    payload = _read_stdin()
    project_dir = _project_dir(payload.get("cwd"))
    try:
        if post_mode:
            return handle_post_tool_use(payload, project_dir)
        return handle_stop(payload, project_dir)
    except Exception:  # noqa: BLE001 — a hook crash must never break the turn
        return ALLOW_EXIT


if __name__ == "__main__":
    sys.exit(main())
