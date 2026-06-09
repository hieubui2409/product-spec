#!/usr/bin/env python3
"""hook_runtime.py — one shared, zero-dependency runtime for the 7 project
Python hooks (5 telemetry + 2 enforcement).

WHY TOP-LEVEL (.claude/hooks/, NOT lib/): .gitignore re-includes ONLY top-level
`*.py` under .claude/hooks/ (`!/.claude/hooks/*.py`); everything else there —
including `lib/` — is ck-managed and ignored. A module placed under `lib/` would
never ship in the bundle and every hook's import would break on the recipient.
A sibling `*.py` is auto-tracked, so this is the single consistent home.

Every project hook imports it with the same 3-line snippet:

    import os, sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import hook_runtime

Responsibilities:
  - log_hook_error(name, exc)        crash audit  → .logs/hook-crashes.log
  - read_stdin_json() / emit_continue()   the deduplicated telemetry skeleton
  - hook_enabled(name)               per-hook config gate (product-spec-hooks.json)
  - run_telemetry_hook(name, core)   telemetry convenience wrapper (read → gate →
                                     fail-open core → always {"continue": true})

Contract: stdlib ONLY; NEVER imports telemetry/skill code (the 2 enforcement
hooks must stay decoupled from the telemetry skill). Every public function is
fail-open — it must never raise back into a hook's path.
"""

import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Shared "is this a skill script" matcher for the Pre/Post Bash duration pair
# (mark_bash_start + track_script_execution). ONE home so the two can never drift
# out of lockstep — a divergence would silently break `ms` pairing with no test
# to catch it. group(1) = the skill-relative path skills/<skill>/scripts/<f>.py|sh.
SCRIPT_RE = re.compile(r"\.claude/skills/([^\s/]+/scripts/[^\s]+\.(?:py|sh))")

# --- crash audit ------------------------------------------------------------

_LOG_NAME = "hook-crashes.log"
_LOG_MAX_BYTES = 256 * 1024  # coarse cap; over this we rotate to .1 then truncate


def _hooks_dir() -> Path:
    return Path(__file__).resolve().parent


def _log_dir() -> Path:
    # CK_HOOK_LOG_DIR lets tests redirect the crash log to a tmp dir.
    raw = os.environ.get("CK_HOOK_LOG_DIR")
    return Path(raw) if raw else _hooks_dir() / ".logs"


def _audit_disabled() -> bool:
    # Always-on by default; off via env, and silent under pytest so test runs
    # never write the real crash log (mirrors telemetry_paths.disabled()).
    return bool(
        os.environ.get("CK_HOOK_AUDIT_DISABLED")
        or os.environ.get("PYTEST_CURRENT_TEST")
    )


def log_hook_error(hook_name: str, exc: BaseException) -> None:
    """Append ONE line (UTC ts, hook, exc type, message, short traceback tail) to
    .logs/hook-crashes.log. Itself fail-open: any IO error is swallowed — the
    logger must NEVER raise into a hook's failure path. Logs exception metadata
    ONLY, never the stdin payload (no PII leak)."""
    if _audit_disabled():
        return
    try:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        tb_tail = tb.strip().splitlines()[-1] if tb.strip() else ""
        line = json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "hook": str(hook_name),
                "type": type(exc).__name__,
                "msg": str(exc)[:500],
                "tb": tb_tail[:500],
            },
            ensure_ascii=False,
        )
        d = _log_dir()
        d.mkdir(parents=True, exist_ok=True)
        p = d / _LOG_NAME
        try:
            if p.stat().st_size > _LOG_MAX_BYTES:
                # Coarse rotation: keep one prior generation, then start fresh.
                p.replace(d / (_LOG_NAME + ".1"))
        except OSError:
            pass  # no file yet, or unstattable — nothing to rotate
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass  # fail-open: a crash logger must never crash a hook


# --- stdin / stdout skeleton ------------------------------------------------

def _parse(raw) -> dict:
    if not raw or not str(raw).strip():
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_stdin_json() -> dict:
    """Read stdin and parse it as a JSON object. Empty/malformed → {} (fail-open)."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    return _parse(raw)


def emit_continue() -> None:
    """Emit the non-blocking telemetry contract: {"continue": true} on stdout."""
    try:
        sys.stdout.write(json.dumps({"continue": True}))
        sys.stdout.flush()
    except Exception:
        pass  # fail-open


# --- per-hook config gate ---------------------------------------------------

_CONFIG_NAME = "product-spec-hooks.json"

# Enforcement hooks: a missing key ⇒ DISABLED (a blocking hook must NEVER be
# fallback-enabled). Telemetry hooks: a missing key ⇒ ENABLED (mirror CK
# isHookEnabled). This asymmetry is the single most safety-critical rule here.
_ENFORCEMENT_STEMS = frozenset({"memory_gap_hook", "product_spec_critique_nudge"})

_config_cache = None  # module-level; None = not yet loaded


def _config_path() -> Path:
    # CK_HOOK_CONFIG (tests) wins; otherwise the JSON sits next to this module —
    # the same .claude/hooks/ dir, resolved off __file__ (durable, not CWD/env).
    raw = os.environ.get("CK_HOOK_CONFIG")
    return Path(raw) if raw else _hooks_dir() / _CONFIG_NAME


def _load_config() -> dict:
    """Parse the config once per process into a module dict. Malformed/unreadable
    ⇒ {} (every hook then falls to its SAFE per-class default) + a crash-log line."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    cfg: dict = {}
    try:
        p = _config_path()
        if p.is_file():
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                cfg = raw
    except Exception as e:  # noqa: BLE001 — malformed config must never crash a hook
        log_hook_error("hook_runtime", e)
        cfg = {}
    _config_cache = cfg
    return cfg


def _reset_config_cache() -> None:
    """Test seam: drop the per-process config cache so a fresh file is re-read."""
    global _config_cache
    _config_cache = None


def _telemetry_globally_disabled() -> bool:
    return bool(os.environ.get("CK_TELEMETRY_DISABLED"))


def hook_enabled(name: str) -> bool:
    """Is the hook named ``name`` (its file stem) enabled?

    Precedence:
      * telemetry stems: global CK_TELEMETRY_DISABLED forces OFF (parity with
        telemetry_paths.disabled()); else explicit bool key wins; else default ON.
      * enforcement stems: explicit bool key wins; else default OFF. The global
        telemetry kill-switch neither enables nor disables enforcement.
    Any non-bool/absent value falls to the per-class default.
    """
    cfg = _load_config()
    val = cfg.get(name)
    explicit = val if isinstance(val, bool) else None

    if name in _ENFORCEMENT_STEMS:
        return explicit if explicit is not None else False

    # telemetry stem
    if _telemetry_globally_disabled():
        return False
    return explicit if explicit is not None else True


# --- telemetry convenience wrapper ------------------------------------------

def run_telemetry_hook(name: str, core, raw=None) -> None:
    """The deduplicated skeleton for the 5 telemetry hooks.

    Reads stdin JSON (or parses ``raw`` when given — the test-compat ``main(raw)``
    path), checks ``hook_enabled(name)``; if disabled, emits {"continue": true}
    and returns WITHOUT running ``core`` (so a disabled hook never imports
    telemetry_paths). Otherwise runs ``core(data)`` inside a fail-open guard that
    routes any exception to ``log_hook_error``. ALWAYS emits {"continue": true}.
    """
    data = read_stdin_json() if raw is None else _parse(raw)
    try:
        if hook_enabled(name):
            core(data)
    except Exception as e:  # noqa: BLE001 — telemetry must never break the op
        log_hook_error(name, e)
    emit_continue()
