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
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -MemoryHook
#       opt-in: register the Tier-1 memory Stop hook into
#       .claude\settings.local.json (gitignored)
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -MemoryHookShared
#       same, but target the committed .claude\settings.json
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -CheckMemoryHook
#       passive <=1/day recommend-nudge (no writes to settings)
#
# The memory hook is OPT-IN ONLY and NEVER auto-registered. A plain install
# (or the bundled recipient installer) does NOT touch your hooks. To remove the
# hook later, delete the two memory_gap_hook.py entries from the Stop and
# PostToolUse arrays of the settings file you registered into.
#
# After install, invoke the skill from Claude Code:
#   /cleanmatic:product-spec

[CmdletBinding()]
param(
    [switch]$Dev,
    [switch]$MemoryHook,
    [switch]$MemoryHookShared,
    [switch]$CheckMemoryHook,
    [switch]$MemoryHookOptout,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Get-Content $PSCommandPath | Select-Object -First 38 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 0
}

$ScriptDir       = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir       = Split-Path -Parent $ScriptDir
# Project root hosts the .claude\ tree (settings + hooks). The skill lives at
# .claude\skills\product-spec\ -> two levels up from SkillsDir (.claude\skills).
$ProjectDir      = Split-Path -Parent (Split-Path -Parent $SkillsDir)
$VenvDir         = Join-Path $SkillsDir ".venv"
$Requirements    = Join-Path $ScriptDir "scripts/requirements.txt"
$RequirementsDev = Join-Path $ScriptDir "scripts/requirements-dev.txt"
$VendorDir       = Join-Path $ScriptDir "assets/vendor"

function Step($msg) { Write-Host ""; Write-Host "▸ $msg" }
function Ok($msg)   { Write-Host "  ✓ $msg" }
function Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

# Pick an interpreter for the JSON merge. The merge is pure stdlib (json), so any
# python works; prefer the skill venv when present, fall back to system python.
function Get-MergePython {
    $venvPy = Join-Path $VenvDir "Scripts/python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    foreach ($candidate in @("python", "python3", "py")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) { return $candidate }
    }
    return $null
}

# The Python merge body, shared by the .sh twin (same semantics). Idempotent,
# non-destructive: parses the target settings file, adds the Stop +
# PostToolUse(Write|Edit) memory_gap_hook entries only when absent, writes back.
# NEVER string-replaces; surfaces malformed JSON loudly. Reads SETTINGS_TARGET
# from the environment.
$MemoryHookMergePy = @'
import json
import os
import sys
from pathlib import Path

target = Path(os.environ["SETTINGS_TARGET"])

PROJ = '"$CLAUDE_PROJECT_DIR"'
# The shared skill venv lays its interpreter at a different relative path per OS:
# Scripts/python.exe on Windows, bin/python3 on POSIX. Derive it from os.name so
# the hook command written into settings runs on the host this installer is on
# (settings.json tolerates forward slashes on Windows).
interp = '.claude/skills/.venv/Scripts/python.exe' if os.name == 'nt' \
    else '.claude/skills/.venv/bin/python3'
PY = f'{PROJ}/{interp}'
HOOK = f'{PROJ}/.claude/hooks/memory_gap_hook.py'
STOP_CMD = f'{PY} {HOOK}'
POST_CMD = f'{PY} {HOOK} --post-tool-use'
POST_MATCHER = 'Write|Edit'
MARK = 'memory_gap_hook.py'


def load(path):
    if not path.exists():
        return {}
    raw = path.read_text(encoding='utf-8').strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f'{path} is not a JSON object')
    return data


def has_memory_hook(event_arr, *, want_post):
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
'@

# Probe: True when either settings file already carries the Stop memory hook.
$MemoryHookProbePy = @'
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
'@

$MemoryMarkerDir   = Join-Path $ProjectDir "docs/product/.memory"
$HookPromptedLast  = Join-Path $MemoryMarkerDir "hook-prompted-last"
$HookOptout        = Join-Path $MemoryMarkerDir "hook-optout"

# Register the opt-in memory Stop hook (idempotent, non-destructive merge).
function Invoke-MemoryHook {
    $rel = if ($MemoryHookShared) { ".claude/settings.json" } else { ".claude/settings.local.json" }
    $target = Join-Path $ProjectDir $rel
    Step "Registering the opt-in memory Stop hook -> $rel"
    $py = Get-MergePython
    if (-not $py) { Fail "python not found; cannot safely merge JSON settings" }
    $env:SETTINGS_TARGET = $target
    $out = ($MemoryHookMergePy | & $py -)
    if ($LASTEXITCODE -ne 0) { Fail "settings merge failed (is $rel valid JSON?)" }
    if ($out -eq "PRESENT") {
        Ok "memory hook already registered in $rel (no change)"
    } else {
        Ok "memory hook registered in $rel ($($out -replace '^ADDED ', ''))"
    }
    Write-Host ""
    Write-Host "  To remove later: delete the two memory_gap_hook.py entries from the"
    Write-Host "  Stop and PostToolUse arrays of $rel."
}

# True when either settings file already carries the Stop memory hook.
function Test-MemoryHookRegistered {
    $py = Get-MergePython
    if (-not $py) { return $false }
    foreach ($f in @(
        (Join-Path $ProjectDir ".claude/settings.local.json"),
        (Join-Path $ProjectDir ".claude/settings.json")
    )) {
        if (-not (Test-Path $f)) { continue }
        $env:SETTINGS_TARGET = $f
        $MemoryHookProbePy | & $py - | Out-Null
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    return $false
}

# Passive <=1/day recommend-nudge. Emits ONE line iff the hook is absent AND the
# user has not opted out AND we have not already prompted today. Stamps the date.
# Never writes settings, never blocks, never nags more than once per day.
function Invoke-CheckMemoryHook {
    if (Test-Path $HookOptout) { return }
    if (Test-MemoryHookRegistered) { return }
    $today = Get-Date -Format "yyyy-MM-dd"
    $last = ""
    if (Test-Path $HookPromptedLast) { $last = (Get-Content $HookPromptedLast -Raw).Trim() }
    if ($last -eq $today) { return }
    New-Item -ItemType Directory -Force -Path $MemoryMarkerDir | Out-Null
    Set-Content -Path $HookPromptedLast -Value $today -NoNewline
    Write-Host 'Tip: memory-write enforcement is OFF (Tier-0). To opt in, run:  install.ps1 -MemoryHook  (say "stop asking" to silence this).'
}

# Record the "stop asking" opt-out: drop the optout marker so the nudge is silent
# forever. Project-scoped; reversible by deleting the marker file.
function Invoke-MemoryHookOptout {
    New-Item -ItemType Directory -Force -Path $MemoryMarkerDir | Out-Null
    Set-Content -Path $HookOptout -Value "opted-out"
    Ok "memory-hook recommend-nudge silenced (delete $HookOptout to re-enable)"
}

# Dispatch the standalone opt-in actions BEFORE the full venv/vendor install.
# Registering the hook (or checking it) does not require — and does not trigger —
# the dependency install.
if ($MemoryHookOptout) { Invoke-MemoryHookOptout; exit 0 }
if ($CheckMemoryHook)  { Invoke-CheckMemoryHook; exit 0 }
if ($MemoryHook -or $MemoryHookShared) { Invoke-MemoryHook; exit 0 }

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
