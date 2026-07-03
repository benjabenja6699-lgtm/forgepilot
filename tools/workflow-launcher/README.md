# Workflow Launcher

Portable launcher for:

- Windows and Linux CLI installers
- Graphify install
- Caveman skill install
- AGENTS.md install
- `.codex/config.toml` install
- `mcp.json` install
- git hook install
- optional Graphify map build

The launcher ships its own templates in `tools/workflow-launcher/assets/`.
It does not depend on `docs/ai_rules_kit/` or any project-specific paths.

Implementation is split into:

- `launcher_core/actions.py` for installer/config actions
- `launcher_core/ui.py` for the Tk interface
- `workflow_launcher.py` as the thin entrypoint

## UI layout

- `Instaladores`
- `Configuraciones`
- `Herramientas`
- `Logs`
- `Ajustes`

## Run

```powershell
python .\workflow_launcher.py
```

## Build exe

```powershell
.\build.ps1
```

The exe lands in:

```text
tools/workflow-launcher/dist/AIWorkflowLauncher.exe
```
