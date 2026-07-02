# ForgePilot Launcher

One-click Windows launcher for the workflow:

- Graphify
- Caveman
- AGENTS.md
- git hook
- repo kit setup

## Start

```powershell
python .\tools\workflow-launcher\workflow_launcher.py
```

## One-line bootstrap

```powershell
irm https://raw.githubusercontent.com/benjabenja6699-lgtm/forgepilot/main/bootstrap.ps1 | iex
```

## Build exe

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\workflow-launcher\build.ps1
```
