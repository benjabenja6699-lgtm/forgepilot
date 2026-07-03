# ForgePilot Launcher

One-click launcher for the workflow suite:

- `Tools` tab with small descriptions
- `Instaladores` tab with `Windows` and `Linux`
- `Configuraciones` tab with `Windows` and `Linux`
- `Logs`
- `Settings`

## Start

```powershell
python .\tools\workflow-launcher\workflow_launcher.py
```

## One-line bootstrap

```powershell
irm https://raw.githubusercontent.com/benjabenja6699-lgtm/forgepilot/main/bootstrap.ps1 | iex
```

That installs or updates the launcher in:

```text
%LOCALAPPDATA%\ForgePilotLauncher
```

## Build exe

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\workflow-launcher\build.ps1
```
