#!/usr/bin/env bash
# install.sh — one-shot installer for the cleanmatic:release skill.
#
# Creates the shared venv at .claude/skills/.venv (if absent) and installs
# runtime deps (pyyaml). Pass --dev to also install pytest + pytest-cov.
#
# Re-running is safe (idempotent): each step skips if already done.
#
# Prerequisites:
#   - Python 3.11+ on PATH (`python3 --version`).
#
# Usage:
#   ./install.sh           # runtime only (pyyaml)
#   ./install.sh --dev     # runtime + dev (pyyaml + pytest + pytest-cov)
#
# After install, invoke the skill from Claude Code:
#   /cleanmatic:release

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
VENV_DIR="$SKILLS_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/scripts/requirements.txt"
REQUIREMENTS_DEV="$SCRIPT_DIR/scripts/requirements-dev.txt"

DEV=0
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        -h|--help)
            sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "unknown arg: $arg (use --dev or --help)" >&2; exit 2 ;;
    esac
done

step() { echo ""; echo "▸ $*"; }
ok()   { echo "  ✓ $*"; }
fail() { echo "  ✗ $*" >&2; exit 1; }

# --- Step 1: Python 3.11+ ---
step "Checking Python"
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found on PATH. Install Python 3.11+: https://www.python.org/downloads/"
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ok "python3 = $PY_VERSION"

# --- Step 2: venv ---
step "Setting up virtual environment at $VENV_DIR"
if [ -x "$VENV_DIR/bin/python3" ]; then
    ok "venv already present"
else
    python3 -m venv "$VENV_DIR"
    ok "venv created"
fi

# --- Step 3: runtime deps (pyyaml) ---
step "Installing runtime dependencies"
"$VENV_DIR/bin/python3" -m pip install --upgrade pip --quiet
"$VENV_DIR/bin/python3" -m pip install --quiet -r "$REQUIREMENTS"
ok "pyyaml installed"

# --- Step 3b: register scripts/ on venv sys.path so `python -m pack` resolves ---
step "Registering scripts/ on venv sys.path"
PYVER=$("$VENV_DIR/bin/python3" -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')
SITE_DIR="$VENV_DIR/lib/$PYVER/site-packages"
if [ -d "$SITE_DIR" ]; then
    PTH_FILE="$SITE_DIR/release.pth"
    echo "$SCRIPT_DIR/scripts" > "$PTH_FILE"
    ok "wrote $PTH_FILE"
else
    fail "venv site-packages not found at $SITE_DIR"
fi

# --- Step 4: dev deps (opt-in) ---
if [ "$DEV" -eq 1 ]; then
    step "Installing dev dependencies (--dev)"
    if [ ! -f "$REQUIREMENTS_DEV" ]; then
        fail "requirements-dev.txt missing at $REQUIREMENTS_DEV"
    fi
    "$VENV_DIR/bin/python3" -m pip install --quiet -r "$REQUIREMENTS_DEV"
    ok "pytest + pytest-cov installed"
fi

# --- Step 5: smoke ---
step "Smoke-testing the install"
"$VENV_DIR/bin/python3" -c "import yaml; print(f'  yaml={yaml.__version__}')"
if [ "$DEV" -eq 1 ]; then
    "$VENV_DIR/bin/python3" -c "import pytest; print(f'  pytest={pytest.__version__}')"
fi

echo ""
echo "─────────────────────────────────────────────────────"
echo "Install complete. Next: invoke the skill in Claude Code:"
echo ""
echo "    /cleanmatic:release"
echo ""
echo "Run pack manually via:"
echo "    $VENV_DIR/bin/python3 -m pack --manifest .claude/pack.manifest.yaml"
echo "─────────────────────────────────────────────────────"
