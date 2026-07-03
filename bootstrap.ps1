$ErrorActionPreference = 'Stop'

$repoUrl = 'https://github.com/benjabenja6699-lgtm/forgepilot.git'
$root = Join-Path $env:LOCALAPPDATA 'ForgePilotLauncher'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git not found in PATH'
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'python not found in PATH'
}

if (-not (Test-Path $root)) {
    git clone --branch main --single-branch $repoUrl $root
} else {
    git -C $root pull --ff-only origin main
}

Set-Location $root
python .\tools\workflow-launcher\workflow_launcher.py
