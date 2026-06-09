#!/usr/bin/env bash
# install.sh — one-shot installer for the cleanmatic:product-spec-critique skill.
#
# product-spec-critique REUSES the shared skill venv (.claude/skills/.venv) created by
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
#   ./install.sh --critique-hook       # opt-in: ENABLE the drift-nudge hook by
#                                      #   flipping product_spec_critique_nudge:true
#                                      #   in .claude/hooks/product-spec-hooks.json
#   ./install.sh --critique-hook-shared
#                                      # accepted alias (config is one committed file now)
#
# The drift-nudge hook is WIRED into the bundle's Stop chain but config-GATED: it
# is DISABLED by default and no-ops until you flip the flag. A plain install
# leaves it OFF. To disable later, set "product_spec_critique_nudge": false in
# .claude/hooks/product-spec-hooks.json.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_DIR="$( cd "$SKILLS_DIR/../.." && pwd )"
VENV_DIR="$SKILLS_DIR/.venv"
# product-spec-critique adds no deps; reuse product-spec's requirements when present.
PSP_REQUIREMENTS="$SKILLS_DIR/product-spec/scripts/requirements.txt"
PSP_REQUIREMENTS_DEV="$SKILLS_DIR/product-spec/scripts/requirements-dev.txt"

DEV=0
CRITIQUE_HOOK=0          # --critique-hook (or its --critique-hook-shared alias): flip flag true
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        # --critique-hook-shared is a back-compat alias: the config is one committed
        # file now (no settings.local/shared split), so both flip the same flag.
        --critique-hook|--critique-hook-shared) CRITIQUE_HOOK=1 ;;
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
# Opt-in advisory drift-nudge hook: flip the config flag (the hook is WIRED-ALWAYS
# in the bundle now; product-spec-hooks.json gates it, default false). Enabling =
# set `product_spec_critique_nudge: true`. Edit JSON with python (NEVER string-
# replace); preserve every other key.
# ---------------------------------------------------------------------------
HOOK_CONFIG="$PROJECT_DIR/.claude/hooks/product-spec-hooks.json"

do_critique_hook() {
    local py out
    py="$(pick_python)" || fail "python3 not found; cannot safely edit JSON config"
    step "Enabling the drift-nudge hook (config flag in product-spec-hooks.json)"
    out="$(CONFIG_TARGET="$HOOK_CONFIG" "$py" - <<'PYEOF'
import json
import os
from pathlib import Path

p = Path(os.environ["CONFIG_TARGET"])
data = {}
if p.exists():
    raw = p.read_text(encoding="utf-8").strip()
    if raw:
        data = json.loads(raw)  # malformed → loud failure, never string-patch
        if not isinstance(data, dict):
            raise ValueError(f'{p} is not a JSON object')
was = data.get("product_spec_critique_nudge")
data["product_spec_critique_nudge"] = True
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("ALREADY" if was is True else "ENABLED")
PYEOF
)" || exit 1
    case "$out" in
        ALREADY) ok "product_spec_critique_nudge already enabled (no change)" ;;
        ENABLED) ok "product_spec_critique_nudge enabled in product-spec-hooks.json" ;;
        *)       ok "$out" ;;
    esac
    echo ""
    echo "  The hook is wired into Stop already; the flag gates it. To disable later,"
    echo "  set \"product_spec_critique_nudge\": false in .claude/hooks/product-spec-hooks.json."
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
echo "    /product-spec-critique"
echo ""
echo "Opt-in drift nudge:  ./install.sh --critique-hook"
echo "─────────────────────────────────────────────────────"
