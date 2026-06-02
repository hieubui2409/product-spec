#!/usr/bin/env bash
# install.sh — one-shot installer for the cleanmatic:spec-critique skill.
#
# spec-critique REUSES the shared skill venv (.claude/skills/.venv) created by
# cleanmatic:product-spec — it adds NO new runtime dependency (stdlib + pyyaml).
# This installer:
#   1. Ensures the shared venv exists (reuse if present; create + install pyyaml
#      if absent, identical to product-spec's bootstrap).
#   2. Optionally registers the opt-in advisory drift-nudge Stop hook.
#
# Re-running is safe (idempotent).
#
# Usage:
#   ./install.sh                       # ensure shared venv only (no hooks)
#   ./install.sh --dev                 # + dev deps (pytest) if product-spec's list is present
#   ./install.sh --critique-hook       # opt-in: register spec_critique_nudge.py into
#                                      #   .claude/settings.local.json (gitignored)
#   ./install.sh --critique-hook-shared
#                                      # same, but target the committed .claude/settings.json
#
# The drift-nudge hook is OPT-IN ONLY and NEVER auto-registered. A plain install
# (or the bundled recipient installer) does NOT touch your hooks. To remove it
# later, delete the spec_critique_nudge.py entry from the Stop array of the
# settings file you registered into.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_DIR="$( cd "$SKILLS_DIR/../.." && pwd )"
VENV_DIR="$SKILLS_DIR/.venv"
# spec-critique adds no deps; reuse product-spec's requirements when present.
PSP_REQUIREMENTS="$SKILLS_DIR/product-spec/scripts/requirements.txt"
PSP_REQUIREMENTS_DEV="$SKILLS_DIR/product-spec/scripts/requirements-dev.txt"

DEV=0
CRITIQUE_HOOK=0          # --critique-hook / --critique-hook-shared requested
CRITIQUE_HOOK_SHARED=0   # target settings.json (committed) instead of settings.local.json
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        --critique-hook) CRITIQUE_HOOK=1 ;;
        --critique-hook-shared) CRITIQUE_HOOK=1; CRITIQUE_HOOK_SHARED=1 ;;
        -h|--help) sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown arg: $arg (use --dev, --critique-hook, --critique-hook-shared, or --help)" >&2; exit 2 ;;
    esac
done

step() { echo ""; echo "▸ $*"; }
ok()   { echo "  ✓ $*"; }
fail() { echo "  ✗ $*" >&2; exit 1; }

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
# Opt-in advisory drift-nudge hook: idempotent, non-destructive settings merge.
# Stop-only (the hook's cheap gate uses last_validated/last_critique stats, so it
# needs no PostToolUse touched-flag). Parses with python (NEVER string-replace),
# adds the Stop entry only when absent (matched by the spec_critique_nudge.py
# basename), preserves all unrelated hooks. NEVER auto-registers.
# ---------------------------------------------------------------------------
critique_hook_merge() {
    local target="$1" py
    py="$(pick_python)" || fail "python3 not found; cannot safely merge JSON settings"
    SETTINGS_TARGET="$target" "$py" - <<'PYEOF'
import json
import os
from pathlib import Path

target = Path(os.environ["SETTINGS_TARGET"])

# The command strings use the LITERAL "$CLAUDE_PROJECT_DIR" token (NOT shell-
# expanded here — this is inside a quoted heredoc) so they resolve at hook-run
# time, the documented Claude Code resolver, not at install time.
PROJ = '"$CLAUDE_PROJECT_DIR"'
PY = f'{PROJ}/.claude/skills/.venv/bin/python3'
HOOK = f'{PROJ}/.claude/hooks/spec_critique_nudge.py'
STOP_CMD = f'{PY} {HOOK}'
MARK = 'spec_critique_nudge.py'


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


def has_hook(event_arr):
    for group in event_arr:
        for h in (group.get('hooks') or []):
            if MARK in h.get('command', ''):
                return True
    return False


settings = load(target)
hooks = settings.setdefault('hooks', {})
if not isinstance(hooks, dict):
    raise ValueError(f'{target}: "hooks" is not an object')
stop_arr = hooks.setdefault('Stop', [])

if has_hook(stop_arr):
    print('PRESENT')
else:
    stop_arr.append({'hooks': [{'type': 'command', 'command': STOP_CMD}]})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + '\n',
                      encoding='utf-8')
    print('ADDED Stop')
PYEOF
}

do_critique_hook() {
    local rel target out
    if [ "$CRITIQUE_HOOK_SHARED" -eq 1 ]; then
        rel=".claude/settings.json"
    else
        rel=".claude/settings.local.json"
    fi
    target="$PROJECT_DIR/$rel"
    step "Registering the opt-in drift-nudge Stop hook → $rel"
    out="$(critique_hook_merge "$target")" || exit 1
    case "$out" in
        PRESENT) ok "drift-nudge hook already registered in $rel (no change)" ;;
        ADDED*)  ok "drift-nudge hook registered in $rel (${out#ADDED })" ;;
        *)       ok "$out" ;;
    esac
    echo ""
    echo "  To remove later: delete the spec_critique_nudge.py entry from the Stop"
    echo "  array of $rel."
}

# Dispatch the standalone opt-in hook action BEFORE the venv ensure. Registering
# the hook does not require the dependency install.
if [ "$CRITIQUE_HOOK" -eq 1 ]; then
    do_critique_hook
    exit 0
fi

# --- Step 1: Python 3.11+ available ---
step "Checking Python"
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found on PATH. Install Python 3.11+ first: https://www.python.org/downloads/"
fi
ok "python3 = $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

# --- Step 2: shared virtual environment (REUSE, create only if absent) ---
step "Ensuring shared venv at $VENV_DIR"
if [ -x "$VENV_DIR/bin/python3" ]; then
    ok "shared venv already present (reused)"
else
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python3" -m pip install --upgrade pip --quiet
    if [ -f "$PSP_REQUIREMENTS" ]; then
        "$VENV_DIR/bin/python3" -m pip install --quiet -r "$PSP_REQUIREMENTS"
    else
        "$VENV_DIR/bin/python3" -m pip install --quiet pyyaml
    fi
    ok "shared venv created (pyyaml installed)"
fi

# --- Step 2b: dev dependencies (opt-in) ---
if [ "$DEV" -eq 1 ] && [ -f "$PSP_REQUIREMENTS_DEV" ]; then
    step "Installing dev dependencies (--dev)"
    "$VENV_DIR/bin/python3" -m pip install --quiet -r "$PSP_REQUIREMENTS_DEV"
    ok "pytest installed"
fi

# --- Step 3: smoke test ---
step "Smoke-testing the install"
"$VENV_DIR/bin/python3" -c "import yaml; print(f'  yaml={yaml.__version__}')"
"$VENV_DIR/bin/python3" "$SCRIPT_DIR/scripts/critique_scan.py" --help >/dev/null 2>&1 \
    && ok "critique_scan.py runnable" || fail "critique_scan.py not runnable"

echo ""
echo "─────────────────────────────────────────────────────"
echo "Install complete. Next: invoke the skill in Claude Code:"
echo ""
echo "    /spec-critique"
echo ""
echo "Opt-in drift nudge:  ./install.sh --critique-hook"
echo "─────────────────────────────────────────────────────"
