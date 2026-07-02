param(
    [string]$RepoRoot = (Get-Location).Path
)

$kitRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = (Resolve-Path $RepoRoot).Path
$agentsSource = Join-Path $kitRoot 'templates\AGENTS.md'
$agentsTarget = Join-Path $repoRoot 'AGENTS.md'
$hooksDir = Join-Path $repoRoot '.githooks'
$hookSource = Join-Path $kitRoot 'templates\pre-commit.sh.example'
$hookTarget = Join-Path $hooksDir 'pre-commit'

New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null

if (-not (Test-Path $agentsTarget)) {
    Copy-Item $agentsSource $agentsTarget
}

Copy-Item $hookSource $hookTarget -Force

git -C $repoRoot config core.hooksPath .githooks

Write-Host "Installed workflow in $repoRoot"
Write-Host "  - AGENTS.md present: $(Test-Path $agentsTarget)"
Write-Host "  - hooks path: .githooks"
