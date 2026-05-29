# install.ps1 — Windows installer for cleanmatic:claude-pack skill.
#
# Creates the shared venv at .claude/skills/.venv (if absent) and installs
# runtime deps (pyyaml). Pass -Dev to also install pytest + pytest-cov.
#
# Re-running is safe (idempotent).
#
# Prerequisites:
#   - Python 3.11+ on PATH (`python --version`) OR the `py` launcher.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Dev

[CmdletBinding()]
param(
    [switch]$Dev,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Get-Content $PSCommandPath | Select-Object -First 14 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 0
}

$ScriptDir       = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir       = Split-Path -Parent $ScriptDir
$VenvDir         = Join-Path $SkillsDir ".venv"
$Requirements    = Join-Path $ScriptDir "scripts/requirements.txt"
$RequirementsDev = Join-Path $ScriptDir "scripts/requirements-dev.txt"

function Step($msg) { Write-Host ""; Write-Host "▸ $msg" }
function Ok($msg)   { Write-Host "  ✓ $msg" }
function Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

# --- Step 1: Python 3.11+ ---
Step "Checking Python"
$python = $null
foreach ($candidate in @("python", "python3", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    Fail "python not found on PATH. Install Python 3.11+: https://www.python.org/downloads/"
}
$pyVer = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Ok "python = $pyVer"

# --- Step 2: venv ---
Step "Setting up virtual environment at $VenvDir"
$VenvPython = Join-Path $VenvDir "Scripts/python.exe"
if (Test-Path $VenvPython) {
    Ok "venv already present"
} else {
    & $python -m venv $VenvDir
    Ok "venv created"
}

# --- Step 3: runtime deps ---
Step "Installing runtime dependencies"
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install --quiet -r $Requirements
Ok "pyyaml installed"

# --- Step 3b: register scripts/ on venv sys.path ---
Step "Registering scripts/ on venv sys.path"
$SiteDir = & $VenvPython -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
if (-not (Test-Path $SiteDir)) {
    Fail "venv site-packages not found at $SiteDir"
}
$PthFile = Join-Path $SiteDir "claude-pack.pth"
Set-Content -Path $PthFile -Value (Join-Path $ScriptDir "scripts") -Encoding ASCII
Ok "wrote $PthFile"

# --- Step 4: dev deps (opt-in) ---
if ($Dev) {
    Step "Installing dev dependencies (-Dev)"
    if (-not (Test-Path $RequirementsDev)) {
        Fail "requirements-dev.txt missing at $RequirementsDev"
    }
    & $VenvPython -m pip install --quiet -r $RequirementsDev
    Ok "pytest + pytest-cov installed"
}

# --- Step 5: smoke ---
Step "Smoke-testing the install"
& $VenvPython -c "import yaml; print(f'  yaml={yaml.__version__}')"
if ($Dev) {
    & $VenvPython -c "import pytest; print(f'  pytest={pytest.__version__}')"
}

Write-Host ""
Write-Host "─────────────────────────────────────────────────────"
Write-Host "Install complete. Next: invoke the skill in Claude Code:"
Write-Host ""
Write-Host "    /cleanmatic:claude-pack"
Write-Host ""
Write-Host "Run pack manually via:"
Write-Host "    $VenvPython -m pack --manifest .claude/pack.manifest.yaml"
Write-Host "─────────────────────────────────────────────────────"
