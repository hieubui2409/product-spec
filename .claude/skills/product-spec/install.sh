#!/usr/bin/env bash
# install.sh — one-shot installer for the cleanmatic:product-spec skill.
#
# Run this ONCE after extracting the skill ZIP into your project. It:
#   1. Creates a Python virtual environment next to the skill folder.
#   2. Installs Python dependencies (pyyaml, pytest, pytest-cov).
#   3. Vendors the Mermaid JS runtime locally for offline HTML visualizations.
#
# Re-running is safe (idempotent): each step skips if already done.
#
# Prerequisites:
#   - Python 3.11+ on PATH (`python3 --version`).
#   - curl OR wget (one-time download of Mermaid JS).
#
# Usage:
#   ./install.sh
#
# After install, invoke the skill from Claude Code:
#   /cleanmatic:product-spec

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
VENV_DIR="$SKILLS_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/scripts/requirements.txt"
VENDOR_SHIM="$SCRIPT_DIR/scripts/install-vendor-mermaid.sh"

step() { echo ""; echo "▸ $*"; }
ok()   { echo "  ✓ $*"; }
fail() { echo "  ✗ $*" >&2; exit 1; }

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

# --- Step 3: dependencies ---
step "Installing Python dependencies"
"$VENV_DIR/bin/python3" -m pip install --upgrade pip --quiet
"$VENV_DIR/bin/python3" -m pip install --quiet -r "$REQUIREMENTS"
ok "pyyaml + pytest installed"

# --- Step 4: Mermaid JS vendor ---
step "Vendoring Mermaid JS for offline HTML output"
if [ -x "$VENDOR_SHIM" ]; then
    bash "$VENDOR_SHIM"
else
    fail "vendor shim missing at $VENDOR_SHIM"
fi

# --- Step 5: smoke test ---
step "Smoke-testing the install"
"$VENV_DIR/bin/python3" -c "import yaml, pytest; print(f'  yaml={yaml.__version__} pytest={pytest.__version__}')"
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

echo ""
echo "─────────────────────────────────────────────────────"
echo "Install complete. Next: invoke the skill in Claude Code:"
echo ""
echo "    /cleanmatic:product-spec"
echo ""
echo "Run scripts manually via:"
echo "    $VENV_DIR/bin/python3 $SCRIPT_DIR/scripts/<script>.py --root <project-dir>"
echo "─────────────────────────────────────────────────────"
