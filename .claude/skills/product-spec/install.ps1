# install.ps1 — Windows installer for the cleanmatic:product-spec skill.
#
# Run this ONCE after extracting the skill into your project. It mirrors
# install.sh:
#   1. Creates a Python virtual environment next to the skill folder.
#   2. Installs runtime dependencies (pyyaml).
#   3. Optionally installs dev dependencies (pytest + pytest-cov) via -Dev.
#   4. Vendors the Mermaid JS runtime locally for offline HTML visualizations.
#   4b. Vendors marked + DOMPurify locally for offline body rendering
#       (board/explorer/export HTML).
#
# Re-running is safe (idempotent): each step skips if already done. The vendored
# JS is committed to the repo, so a fresh clone is already offline-ready and the
# vendor steps just verify the sha256 and skip.
#
# Prerequisites:
#   - Python 3.11+ on PATH (`python --version`) OR the `py` launcher.
#   - Internet access ONLY if the vendored JS is missing (one-time download).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Dev
#
# After install, invoke the skill from Claude Code:
#   /cleanmatic:product-spec

[CmdletBinding()]
param(
    [switch]$Dev,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Get-Content $PSCommandPath | Select-Object -First 24 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 0
}

$ScriptDir       = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir       = Split-Path -Parent $ScriptDir
$VenvDir         = Join-Path $SkillsDir ".venv"
$Requirements    = Join-Path $ScriptDir "scripts/requirements.txt"
$RequirementsDev = Join-Path $ScriptDir "scripts/requirements-dev.txt"
$VendorDir       = Join-Path $ScriptDir "assets/vendor"

function Step($msg) { Write-Host ""; Write-Host "▸ $msg" }
function Ok($msg)   { Write-Host "  ✓ $msg" }
function Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

# Fetch + sha256-verify one vendored library. Idempotent: skips when the target
# is present and its hash matches. Mirrors scripts/install-vendor-*.sh.
function Get-Vendored($name, $url, $expectedSha) {
    $target = Join-Path $VendorDir $name
    if ((Test-Path $target) -and ((Get-Item $target).Length -gt 0)) {
        $have = (Get-FileHash $target -Algorithm SHA256).Hash
        if ($have -ieq $expectedSha) {
            Ok "$name already present (sha256 OK)"
            return
        }
        Write-Host "  ! $name sha256 mismatch, re-downloading" -ForegroundColor Yellow
    }
    Write-Host "  … fetching $url"
    Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing
    if (-not ((Test-Path $target) -and ((Get-Item $target).Length -gt 0))) {
        Fail "$name download was empty"
    }
    $got = (Get-FileHash $target -Algorithm SHA256).Hash
    if ($got -ine $expectedSha) {
        Remove-Item $target -Force
        Fail "$name sha256 mismatch (expected $expectedSha, got $got)"
    }
    Ok "$name vendored"
}

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

# --- Step 3: runtime dependencies ---
Step "Installing runtime dependencies"
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install --quiet -r $Requirements
Ok "pyyaml installed"

# --- Step 3b: dev dependencies (opt-in) ---
if ($Dev) {
    Step "Installing dev dependencies (-Dev)"
    if (-not (Test-Path $RequirementsDev)) {
        Fail "requirements-dev.txt missing at $RequirementsDev"
    }
    & $VenvPython -m pip install --quiet -r $RequirementsDev
    Ok "pytest + pytest-cov installed"
}

# --- Step 4: Mermaid JS vendor (offline HTML graph views) ---
# Pins must stay in lockstep with scripts/install-vendor-mermaid.sh.
Step "Vendoring Mermaid JS for offline HTML output"
New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null
Get-Vendored "mermaid.min.js" `
    "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js" `
    "a43bc1afd446f9c4cc66ac5dd45d02e8d65e26fc5344ec0ef787f88d6ddb6f9e"

# --- Step 4b: marked + DOMPurify vendor (body-render: export / board / explorer) ---
# Pins must stay in lockstep with scripts/install-vendor-markdown.sh.
Step "Vendoring marked + DOMPurify for offline body rendering"
Get-Vendored "marked.min.js" `
    "https://cdn.jsdelivr.net/npm/marked@18.0.4/lib/marked.umd.js" `
    "5d35f05a51554f8665066455535e3adf642df0da7e2a18d39766d5a3ecb4846c"
Get-Vendored "purify.min.js" `
    "https://cdn.jsdelivr.net/npm/dompurify@3.4.7/dist/purify.min.js" `
    "f84e522876a6cfadecb89c173356409acec39f580c69018559c9a50e96299b0c"

# --- Step 5: smoke test ---
Step "Smoke-testing the install"
& $VenvPython -c "import yaml; print(f'  yaml={yaml.__version__}')"
if ($Dev) {
    & $VenvPython -c "import pytest; print(f'  pytest={pytest.__version__}')"
    $TestsDir = Join-Path $ScriptDir "scripts/tests"
    & $VenvPython -m pytest $TestsDir -q --no-header
    if ($LASTEXITCODE -ne 0) {
        Fail "test suite failed; install did not complete cleanly"
    }
}

Write-Host ""
Write-Host "─────────────────────────────────────────────────────"
Write-Host "Install complete. Next: invoke the skill in Claude Code:"
Write-Host ""
Write-Host "    /cleanmatic:product-spec"
Write-Host ""
Write-Host "Run scripts manually via:"
Write-Host "    $VenvPython $ScriptDir\scripts\<script>.py --root <project-dir>"
Write-Host "─────────────────────────────────────────────────────"
