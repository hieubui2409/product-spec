# install.ps1 — one-shot installer for cleanmatic:spec-critique (Windows).
#
# spec-critique REUSES the shared skill venv (.claude\skills\.venv) created by
# cleanmatic:product-spec — it adds NO new runtime dependency (stdlib + pyyaml).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#       ensure shared venv only (no hooks)
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Dev
#       + dev deps (pytest) if product-spec's list is present
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -CritiqueHook
#       opt-in: register spec_critique_nudge.py into .claude\settings.local.json
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -CritiqueHookShared
#       same, but target the committed .claude\settings.json
#
# The drift-nudge hook is OPT-IN ONLY and NEVER auto-registered.

param(
    [switch]$Dev,
    [switch]$CritiqueHook,
    [switch]$CritiqueHookShared,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir  = Split-Path -Parent $ScriptDir
$ProjectDir = Split-Path -Parent (Split-Path -Parent $SkillsDir)
$VenvDir    = Join-Path $SkillsDir ".venv"
$PspReq     = Join-Path $SkillsDir "product-spec/scripts/requirements.txt"
$PspReqDev  = Join-Path $SkillsDir "product-spec/scripts/requirements-dev.txt"

function Step($msg) { Write-Host ""; Write-Host "▸ $msg" }
function Ok($msg)   { Write-Host "  ✓ $msg" }
function Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

if ($Help) { Get-Content $MyInvocation.MyCommand.Path | Select-Object -Skip 1 -First 24 | ForEach-Object { $_ -replace '^#\s?','' }; exit 0 }

function Get-MergePython {
    $venvPy = Join-Path $VenvDir "Scripts/python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    $sys = Get-Command python -ErrorAction SilentlyContinue
    if ($sys) { return $sys.Source }
    return $null
}

# Idempotent, non-destructive Stop-hook merge. Parses with python (never string
# patch), adds the entry only when absent (matched by spec_critique_nudge.py).
$CritiqueHookMergePy = @'
import json, os
from pathlib import Path

target = Path(os.environ["SETTINGS_TARGET"])
PROJ = '"$CLAUDE_PROJECT_DIR"'
interp = '.claude/skills/.venv/Scripts/python.exe' if os.name == 'nt' \
    else '.claude/skills/.venv/bin/python3'
PY = f'{PROJ}/{interp}'
HOOK = f'{PROJ}/.claude/hooks/spec_critique_nudge.py'
STOP_CMD = f'{PY} {HOOK}'
MARK = 'spec_critique_nudge.py'

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

def has_hook(arr):
    for group in arr:
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
    target.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('ADDED Stop')
'@

function Invoke-CritiqueHook {
    $rel = if ($CritiqueHookShared) { ".claude/settings.json" } else { ".claude/settings.local.json" }
    $target = Join-Path $ProjectDir $rel
    Step "Registering the opt-in drift-nudge Stop hook -> $rel"
    $py = Get-MergePython
    if (-not $py) { Fail "python not found; cannot safely merge JSON settings" }
    $env:SETTINGS_TARGET = $target
    $out = ($CritiqueHookMergePy | & $py -)
    if ($LASTEXITCODE -ne 0) { Fail "settings merge failed (is $rel valid JSON?)" }
    switch -Wildcard ($out) {
        "PRESENT" { Ok "drift-nudge hook already registered in $rel (no change)" }
        "ADDED*"  { Ok "drift-nudge hook registered in $rel" }
        default    { Ok $out }
    }
    Write-Host ""
    Write-Host "  To remove later: delete the spec_critique_nudge.py entry from the Stop array of $rel."
}

if ($CritiqueHook -or $CritiqueHookShared) {
    Invoke-CritiqueHook
    exit 0
}

# --- Step 1: Python ---
Step "Checking Python"
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { Fail "python not found on PATH. Install Python 3.11+ first." }
Ok "python found"

# --- Step 2: shared venv (reuse, create only if absent) ---
Step "Ensuring shared venv at $VenvDir"
$VenvPy = Join-Path $VenvDir "Scripts/python.exe"
if (Test-Path $VenvPy) {
    Ok "shared venv already present (reused)"
} else {
    python -m venv $VenvDir
    & $VenvPy -m pip install --upgrade pip --quiet
    if (Test-Path $PspReq) {
        & $VenvPy -m pip install --quiet -r $PspReq
    } else {
        & $VenvPy -m pip install --quiet pyyaml
    }
    Ok "shared venv created (pyyaml installed)"
}

# --- Step 2b: dev deps (opt-in) ---
if ($Dev -and (Test-Path $PspReqDev)) {
    Step "Installing dev dependencies (-Dev)"
    & $VenvPy -m pip install --quiet -r $PspReqDev
    Ok "pytest installed"
}

# --- Step 3: smoke test ---
Step "Smoke-testing the install"
& $VenvPy -c "import yaml; print(f'  yaml={yaml.__version__}')"
& $VenvPy (Join-Path $ScriptDir "scripts/critique_scan.py") --help | Out-Null
if ($LASTEXITCODE -eq 0) { Ok "critique_scan.py runnable" } else { Fail "critique_scan.py not runnable" }

Write-Host ""
Write-Host "─────────────────────────────────────────────────────"
Write-Host "Install complete. Next: invoke the skill in Claude Code:"
Write-Host ""
Write-Host "    /spec-critique"
Write-Host ""
Write-Host "Opt-in drift nudge:  .\install.ps1 -CritiqueHook"
Write-Host "─────────────────────────────────────────────────────"
