$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    python -m pip install --upgrade pyinstaller
}

pyinstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name "AIWorkflowLauncher" `
    .\workflow_launcher.py

Write-Host "Built: $here\dist\AIWorkflowLauncher.exe"
