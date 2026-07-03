# AI Rules Kit

Carpeta unica para exportar el flujo `Graphify + DeepSeek + Codex` a cualquier proyecto.

Documento principal:

- [00_MASTER_MANUAL.md](00_MASTER_MANUAL.md)

## Contenido

- `01_RULES_AND_WORKFLOW.md`
  Reglas operativas y reparto de roles.
- `02_PERSISTENCE_AND_AGENTS.md`
  Como volver estas reglas persistentes en un repo.
- `03_MCP_AND_DEEPSEEK_SETUP.md`
  Como configurar MCP, OpenAI Docs y el bridge de DeepSeek.
- `04_GRAPHIFY_STRATEGY.md`
  Como usar Graphify sin meter ruido ni gastar tokens de mas.
- `05_NEW_PROJECT_IMPLEMENTATION.md`
  Playbook de arranque para un repo nuevo.
- `06_ENFORCEMENT_AND_BOOTSTRAP.md`
  Que si se puede automatizar y que sigue siendo manual.
- `templates/AGENTS.md`
  Template listo para pegar en la raiz de otro repo.
- `templates/codex.config.example.toml`
  Ejemplo de configuracion de Codex por proyecto o global.
- `templates/mcp.json.example`
  Ejemplo alternativo para clientes que usen `mcp.json`.
- `templates/pre-commit.sh.example`
  Hook base para bloquear cambios no triviales sin grafo vigente.
- `templates/install-workflow.ps1`
  Instalador portable para copiar reglas, hook y configurar `core.hooksPath`.

## Regla madre

El patron correcto es:

`Graphify -> packet corto -> 1 consulta DeepSeek -> auditoria puntual -> patch -> validacion corta`

El anti-patron que gasta tokens es:

`Graphify insuficiente + demasiada lectura manual + demasiadas iteraciones con DeepSeek + auditoria demasiado grande`

## Archivo persistente del repo actual

La regla operativa activa de cada repo destino vive en su propio `AGENTS.md`.
Este kit solo trae el template para copiarlo al repo que vayas a trabajar.

## Uso recomendado

Si vas a llevarte esta carpeta a otro proyecto:

1. copia esta carpeta completa
2. copia `templates/AGENTS.md` a la raiz del nuevo repo como `AGENTS.md`
3. revisa `05_NEW_PROJECT_IMPLEMENTATION.md`
4. instala el hook con `templates/install-workflow.ps1`
5. ajusta el template de `config.toml` y `mcp.json` si hace falta
6. usa `00_MASTER_MANUAL.md` como guia principal
