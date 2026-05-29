#!/usr/bin/env bash
# install.sh — one-shot installer for the cleanmatic:product-spec skill.
#
# Run this ONCE after extracting the skill ZIP into your project. It:
#   1. Creates a Python virtual environment next to the skill folder.
#   2. Installs runtime dependencies (pyyaml).
#   3. Optionally installs dev dependencies (pytest + pytest-cov) via --dev.
#   4. Vendors the Mermaid JS runtime locally for offline HTML visualizations.
#
# Re-running is safe (idempotent): each step skips if already done.
#
# Prerequisites:
#   - Python 3.11+ on PATH (`python3 --version`).
#   - curl OR wget (one-time download of Mermaid JS).
#
# Usage:
#   ./install.sh             # runtime only (pyyaml)
#   ./install.sh --dev       # runtime + dev (pytest + pytest-cov)
#
# After install, invoke the skill from Claude Code:
#   /cleanmatic:product-spec

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
VENV_DIR="$SKILLS_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/scripts/requirements.txt"
REQUIREMENTS_DEV="$SCRIPT_DIR/scripts/requirements-dev.txt"
VENDOR_SHIM="$SCRIPT_DIR/scripts/install-vendor-mermaid.sh"

DEV=0
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown arg: $arg (use --dev or --help)" >&2; exit 2 ;;
    esac
done

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
