#!/usr/bin/env bash
# install.sh — one-shot installer for the cleanmatic:product-spec skill.
#
# Run this ONCE after extracting the skill ZIP into your project. It:
#   1. Creates a Python virtual environment next to the skill folder.
#   2. Installs runtime dependencies (pyyaml).
#   3. Optionally installs dev dependencies (pytest + pytest-cov) via --dev.
#   4. Vendors the Mermaid JS runtime locally for offline HTML visualizations.
#   4b. Vendors marked + DOMPurify locally for offline body rendering
#       (board/explorer/export HTML).
#
# Re-running is safe (idempotent): each step skips if already done.
#
# Prerequisites:
#   - Python 3.11+ on PATH (`python3 --version`).
#   - curl OR wget (one-time download of Mermaid JS + marked + DOMPurify).
#
# Usage:
#   ./install.sh                    # runtime only (pyyaml)
#   ./install.sh --dev              # runtime + dev (pytest + pytest-cov)
#   ./install.sh --memory-hook      # opt-in: ENABLE the Tier-1 memory hook by
#                                   #   flipping memory_gap_hook:true in
#                                   #   .claude/hooks/product-spec-hooks.json
#   ./install.sh --memory-hook-shared
#                                   # accepted alias (the config is a single
#                                   #   committed file now — no local/shared split)
#   ./install.sh --check-memory-hook
#                                   # passive ≤1/day recommend-nudge (no writes)
#
# The memory hook is WIRED into the bundle's Stop chain but config-GATED: it is
# DISABLED by default and no-ops until you flip the flag. A plain `./install.sh`
# leaves it OFF. To disable later, set "memory_gap_hook": false in
# .claude/hooks/product-spec-hooks.json.
#
# After install, invoke the skill from Claude Code:
#   /cleanmatic:product-spec

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
# Project root hosts the `.claude/` tree (settings + hooks). The skill lives at
# .claude/skills/product-spec/ → two levels up from SKILLS_DIR (.claude/skills).
PROJECT_DIR="$( cd "$SKILLS_DIR/../.." && pwd )"
VENV_DIR="$SKILLS_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/scripts/requirements.txt"
REQUIREMENTS_DEV="$SCRIPT_DIR/scripts/requirements-dev.txt"
VENDOR_SHIM="$SCRIPT_DIR/scripts/install-vendor-mermaid.sh"
VENDOR_MARKDOWN_SHIM="$SCRIPT_DIR/scripts/install-vendor-markdown.sh"

DEV=0
MEMORY_HOOK=0          # --memory-hook (or its --memory-hook-shared alias): flip flag true
CHECK_MEMORY_HOOK=0    # --check-memory-hook passive recommend-nudge
MEMORY_HOOK_OPTOUT=0   # --memory-hook-optout: user said "stop asking" → silence the nudge
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        # --memory-hook-shared is a back-compat alias: the config is one committed
        # file now (no settings.local/shared split), so both flip the same flag.
        --memory-hook|--memory-hook-shared) MEMORY_HOOK=1 ;;
        --check-memory-hook) CHECK_MEMORY_HOOK=1 ;;
        --memory-hook-optout) MEMORY_HOOK_OPTOUT=1 ;;
        -h|--help) sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown arg: $arg (use --dev, --memory-hook, --memory-hook-shared, --check-memory-hook, --memory-hook-optout, or --help)" >&2; exit 2 ;;
    esac
done

step() { echo ""; echo "▸ $*"; }
ok()   { echo "  ✓ $*"; }
fail() { echo "  ✗ $*" >&2; exit 1; }

# Pick an interpreter for the JSON merge. The merge is pure stdlib (json), so any
# python works; prefer the skill venv when present, fall back to system python3.
pick_python() {
    if [ -x "$VENV_DIR/bin/python3" ]; then
        echo "$VENV_DIR/bin/python3"
    elif command -v python3 >/dev/null 2>&1; then
        echo "python3"
    else
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Opt-in Tier-1 memory hook: flip the config flag (the hook is WIRED-ALWAYS in
# the bundle now; product-spec-hooks.json gates it, default false). Enabling =
# set `memory_gap_hook: true` in .claude/hooks/product-spec-hooks.json. The hook
# reads that flag per-invocation, so the change applies on the next Stop. We edit
# JSON with python (NEVER string-replace) and preserve every other key.
# ---------------------------------------------------------------------------
HOOK_CONFIG="$PROJECT_DIR/.claude/hooks/product-spec-hooks.json"

config_flag_flip() {
    # $1 = key, $2 = "true"|"false". Echoes ENABLED/DISABLED/ALREADY.
    local key="$1" val="$2" py
    py="$(pick_python)" || fail "python3 not found; cannot safely edit JSON config"
    CONFIG_TARGET="$HOOK_CONFIG" HOOK_KEY="$key" HOOK_VAL="$val" "$py" - <<'PYEOF'
import json
import os
from pathlib import Path

p = Path(os.environ["CONFIG_TARGET"])
key = os.environ["HOOK_KEY"]
val = os.environ["HOOK_VAL"] == "true"

data = {}
if p.exists():
    raw = p.read_text(encoding="utf-8").strip()
    if raw:
        data = json.loads(raw)  # malformed → loud failure, never string-patch
        if not isinstance(data, dict):
            raise ValueError(f'{p} is not a JSON object')

was = data.get(key)
data[key] = val
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("ALREADY" if was is val else ("ENABLED" if val else "DISABLED"))
PYEOF
}

# Enable the memory hook by flipping its config flag true.
do_memory_hook() {
    step "Enabling the memory hook (config flag in product-spec-hooks.json)"
    local out
    out="$(config_flag_flip "memory_gap_hook" "true")" || exit 1
    case "$out" in
        ALREADY) ok "memory_gap_hook already enabled (no change)" ;;
        ENABLED) ok "memory_gap_hook enabled in product-spec-hooks.json" ;;
        *)       ok "$out" ;;
    esac
    echo ""
    echo "  The hook is wired into Stop already; the flag gates it. To disable later,"
    echo "  set \"memory_gap_hook\": false in .claude/hooks/product-spec-hooks.json."
}

# Marker dir for the recommend-nudge cadence (project-scoped, under docs/product).
MEMORY_MARKER_DIR="$PROJECT_DIR/docs/product/.memory"
HOOK_PROMPTED_LAST="$MEMORY_MARKER_DIR/hook-prompted-last"
HOOK_OPTOUT="$MEMORY_MARKER_DIR/hook-optout"

# True (0) when the memory hook is ENABLED via the config flag (the hook is
# wired-always; the flag is what turns it on).
memory_hook_registered() {
    local py
    py="$(pick_python)" || return 1
    [ -f "$HOOK_CONFIG" ] || return 1
    CONFIG_TARGET="$HOOK_CONFIG" "$py" - <<'PYEOF' && return 0
import json, os, sys
from pathlib import Path
p = Path(os.environ["CONFIG_TARGET"])
try:
    data = json.loads(p.read_text(encoding="utf-8") or "{}")
except Exception:
    sys.exit(1)
sys.exit(0 if data.get("memory_gap_hook") is True else 1)
PYEOF
    return 1
}

# Passive ≤1/day recommend-nudge. Emits ONE line iff the hook is absent AND the
# user has not opted out AND we have not already prompted today. Stamps the date.
# Never writes settings, never blocks, never nags more than once per day.
do_check_memory_hook() {
    # Opted out → silent forever.
    [ -f "$HOOK_OPTOUT" ] && return 0
    # Already registered → nothing to recommend; degrade silently to Tier-0.
    if memory_hook_registered; then
        return 0
    fi
    local today last
    today="$(date +%Y-%m-%d)"
    last=""
    [ -f "$HOOK_PROMPTED_LAST" ] && last="$(cat "$HOOK_PROMPTED_LAST" 2>/dev/null || true)"
    # Already nudged today → silent.
    [ "$last" = "$today" ] && return 0
    # Stamp first (so the line fires at most once/day even if the caller loops).
    mkdir -p "$MEMORY_MARKER_DIR" 2>/dev/null || true
    printf '%s\n' "$today" > "$HOOK_PROMPTED_LAST" 2>/dev/null || true
    echo "Tip: memory-write enforcement is OFF (Tier-0). To opt in, run:  ./install.sh --memory-hook  (say \"stop asking\" to silence this)."
    return 0
}

# Record the "stop asking" opt-out: drop the optout marker so the nudge is silent
# forever. Project-scoped; reversible by deleting the marker file.
do_memory_hook_optout() {
    mkdir -p "$MEMORY_MARKER_DIR" 2>/dev/null || true
    printf '%s\n' "opted-out" > "$HOOK_OPTOUT" 2>/dev/null || true
    ok "memory-hook recommend-nudge silenced (delete $HOOK_OPTOUT to re-enable)"
}

# Dispatch the standalone opt-in actions BEFORE the full venv/vendor install.
# These are independent capabilities: registering the hook (or checking it) does
# not require — and does not trigger — the dependency install.
if [ "$MEMORY_HOOK_OPTOUT" -eq 1 ]; then
    do_memory_hook_optout
    exit 0
fi
if [ "$CHECK_MEMORY_HOOK" -eq 1 ]; then
    do_check_memory_hook
    exit 0
fi
if [ "$MEMORY_HOOK" -eq 1 ]; then
    do_memory_hook
    exit 0
fi

# --- Step 1: Python 3.11+ available ---
step "Checking Python"
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found on PATH. Install Python 3.11+ first: https://www.python.org/downloads/"
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ok "python3 = $PY_VERSION"

# --- Step 2: virtual environment ---
step "Setting up virtual environment at $VENV_DIR"
if [ -x "$VENV_DIR/bin/python3" ]; then
    ok "venv already present"
else
    python3 -m venv "$VENV_DIR"
    ok "venv created"
fi

# --- Step 3: runtime dependencies ---
step "Installing runtime dependencies"
"$VENV_DIR/bin/python3" -m pip install --upgrade pip --quiet
"$VENV_DIR/bin/python3" -m pip install --quiet -r "$REQUIREMENTS"
ok "pyyaml installed"

# --- Step 3b: dev dependencies (opt-in) ---
if [ "$DEV" -eq 1 ]; then
    step "Installing dev dependencies (--dev)"
    if [ ! -f "$REQUIREMENTS_DEV" ]; then
        fail "requirements-dev.txt missing at $REQUIREMENTS_DEV"
    fi
    "$VENV_DIR/bin/python3" -m pip install --quiet -r "$REQUIREMENTS_DEV"
    ok "pytest + pytest-cov installed"
fi

# --- Step 4: Mermaid JS vendor ---
step "Vendoring Mermaid JS for offline HTML output"
if [ -x "$VENDOR_SHIM" ]; then
    bash "$VENDOR_SHIM"
else
    fail "vendor shim missing at $VENDOR_SHIM"
fi

# --- Step 4b: marked + DOMPurify vendor (body-render: export / board / explorer) ---
step "Vendoring marked + DOMPurify for offline body rendering"
if [ -x "$VENDOR_MARKDOWN_SHIM" ]; then
    bash "$VENDOR_MARKDOWN_SHIM"
else
    fail "markdown vendor shim missing at $VENDOR_MARKDOWN_SHIM"
fi

# --- Step 5: smoke test ---
step "Smoke-testing the install"
"$VENV_DIR/bin/python3" -c "import yaml; print(f'  yaml={yaml.__version__}')"
# pytest is dev-only (installed via --dev). Run the suite only when --dev was
# requested; a runtime-only install ships pyyaml and skips the test gate.
if [ "$DEV" -eq 1 ]; then
    "$VENV_DIR/bin/python3" -c "import pytest; print(f'  pytest={pytest.__version__}')"
    # Capture pytest output to a log so we can surface failures AND tail the
    # pass-line. Piping into `tail` directly masked the pytest exit code: under
    # `set -o pipefail` the rightmost non-zero wins, but `tail` always exits 0,
    # so a red test suite silently reported "Install complete".
    PYTEST_LOG=$(mktemp -t product-spec-pytest.XXXXXX.log)
    if "$VENV_DIR/bin/python3" -m pytest "$SCRIPT_DIR/scripts/tests/" -q --no-header > "$PYTEST_LOG" 2>&1; then
        tail -3 "$PYTEST_LOG"
        rm -f "$PYTEST_LOG"
    else
        PYTEST_EXIT=$?
        echo "  ✗ pytest failed (exit $PYTEST_EXIT). Full output:" >&2
        cat "$PYTEST_LOG" >&2
        rm -f "$PYTEST_LOG"
        fail "test suite failed; install did not complete cleanly"
    fi
fi

echo ""
echo "─────────────────────────────────────────────────────"
echo "Install complete. Next: invoke the skill in Claude Code:"
echo ""
echo "    /cleanmatic:product-spec"
echo ""
echo "Run scripts manually via:"
echo "    $VENV_DIR/bin/python3 $SCRIPT_DIR/scripts/<script>.py --root <project-dir>"
echo "─────────────────────────────────────────────────────"
