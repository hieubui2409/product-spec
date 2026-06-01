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
#   ./install.sh --memory-hook      # opt-in: register the Tier-1 memory Stop hook
#                                   #   into .claude/settings.local.json (gitignored)
#   ./install.sh --memory-hook-shared
#                                   # same, but target the committed .claude/settings.json
#   ./install.sh --check-memory-hook
#                                   # passive ≤1/day recommend-nudge (no writes to settings)
#
# The memory hook is OPT-IN ONLY and NEVER auto-registered. A plain `./install.sh`
# (or the bundled recipient installer) does NOT touch your hooks. To remove the
# hook later, delete the two `memory_gap_hook.py` entries from the Stop and
# PostToolUse arrays of the settings file you registered into.
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
MEMORY_HOOK=0          # --memory-hook / --memory-hook-shared requested
MEMORY_HOOK_SHARED=0   # target settings.json (committed) instead of settings.local.json
CHECK_MEMORY_HOOK=0    # --check-memory-hook passive recommend-nudge
MEMORY_HOOK_OPTOUT=0   # --memory-hook-optout: user said "stop asking" → silence the nudge
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        --memory-hook) MEMORY_HOOK=1 ;;
        --memory-hook-shared) MEMORY_HOOK=1; MEMORY_HOOK_SHARED=1 ;;
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
# Opt-in Tier-1 memory hook: idempotent, non-destructive settings JSON merge.
# Parses the target settings file with python (NEVER string-replace), adds the
# Stop + PostToolUse(Write|Edit) entries only when the hook (matched by the
# memory_gap_hook.py command substring) is absent, and writes back. Pre-existing
# unrelated hooks are preserved verbatim. NEVER auto-registers — only this
# explicit flag touches your settings.
# ---------------------------------------------------------------------------
memory_hook_merge() {
    local target="$1" py
    py="$(pick_python)" || fail "python3 not found; cannot safely merge JSON settings"
    SETTINGS_TARGET="$target" PROJECT_DIR="$PROJECT_DIR" "$py" - <<'PYEOF'
import json
import os
import sys
from pathlib import Path

target = Path(os.environ["SETTINGS_TARGET"])

# The command strings use the LITERAL "$CLAUDE_PROJECT_DIR" token so they resolve
# at hook-run time (the documented Claude Code resolver), not at install time.
PROJ = '"$CLAUDE_PROJECT_DIR"'
PY = f'{PROJ}/.claude/skills/.venv/bin/python3'
HOOK = f'{PROJ}/.claude/hooks/memory_gap_hook.py'
STOP_CMD = f'{PY} {HOOK}'
POST_CMD = f'{PY} {HOOK} --post-tool-use'
POST_MATCHER = 'Write|Edit'

# Idempotency anchor: match on the durable script basename so a second run (or a
# settings file whose paths were hand-edited) is still recognised as "present".
MARK = 'memory_gap_hook.py'


def load(path):
    if not path.exists():
        return {}
    raw = path.read_text(encoding='utf-8').strip()
    if not raw:
        return {}
    data = json.loads(raw)  # surface malformed JSON loudly — never string-patch
    if not isinstance(data, dict):
        raise ValueError(f'{path} is not a JSON object')
    return data


def has_memory_hook(event_arr, *, want_post):
    """True if `event_arr` already carries a memory_gap_hook entry of the right
    mode (Stop = no --post-tool-use; PostToolUse = with --post-tool-use)."""
    for group in event_arr:
        for h in (group.get('hooks') or []):
            cmd = h.get('command', '')
            if MARK in cmd and (('--post-tool-use' in cmd) == want_post):
                return True
    return False


settings = load(target)
hooks = settings.setdefault('hooks', {})
if not isinstance(hooks, dict):
    raise ValueError(f'{target}: "hooks" is not an object')

stop_arr = hooks.setdefault('Stop', [])
post_arr = hooks.setdefault('PostToolUse', [])

added = []
if not has_memory_hook(stop_arr, want_post=False):
    stop_arr.append({'hooks': [{'type': 'command', 'command': STOP_CMD}]})
    added.append('Stop')
if not has_memory_hook(post_arr, want_post=True):
    post_arr.append({
        'matcher': POST_MATCHER,
        'hooks': [{'type': 'command', 'command': POST_CMD}],
    })
    added.append('PostToolUse(Write|Edit)')

if added:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    print('ADDED ' + ', '.join(added))
else:
    print('PRESENT')
PYEOF
}

# Run the memory-hook merge against the requested settings file and report.
do_memory_hook() {
    local rel target
    if [ "$MEMORY_HOOK_SHARED" -eq 1 ]; then
        rel=".claude/settings.json"
    else
        rel=".claude/settings.local.json"
    fi
    target="$PROJECT_DIR/$rel"
    step "Registering the opt-in memory Stop hook → $rel"
    local out
    out="$(memory_hook_merge "$target")" || exit 1
    case "$out" in
        PRESENT) ok "memory hook already registered in $rel (no change)" ;;
        ADDED*)  ok "memory hook registered in $rel (${out#ADDED })" ;;
        *)       ok "$out" ;;
    esac
    echo ""
    echo "  To remove later: delete the two memory_gap_hook.py entries from the"
    echo "  Stop and PostToolUse arrays of $rel."
}

# Marker dir for the recommend-nudge cadence (project-scoped, under docs/product).
MEMORY_MARKER_DIR="$PROJECT_DIR/docs/product/.memory"
HOOK_PROMPTED_LAST="$MEMORY_MARKER_DIR/hook-prompted-last"
HOOK_OPTOUT="$MEMORY_MARKER_DIR/hook-optout"

# True (0) when either settings file already carries the Stop memory hook.
memory_hook_registered() {
    local py f
    py="$(pick_python)" || return 1
    for f in "$PROJECT_DIR/.claude/settings.local.json" "$PROJECT_DIR/.claude/settings.json"; do
        [ -f "$f" ] || continue
        SETTINGS_TARGET="$f" "$py" - <<'PYEOF' && return 0
import json, os, sys
from pathlib import Path
p = Path(os.environ["SETTINGS_TARGET"])
try:
    data = json.loads(p.read_text(encoding="utf-8") or "{}")
except Exception:
    sys.exit(1)
stop = (data.get("hooks") or {}).get("Stop") or []
for group in stop:
    for h in (group.get("hooks") or []):
        cmd = h.get("command", "")
        if "memory_gap_hook.py" in cmd and "--post-tool-use" not in cmd:
            sys.exit(0)
sys.exit(1)
PYEOF
    done
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
