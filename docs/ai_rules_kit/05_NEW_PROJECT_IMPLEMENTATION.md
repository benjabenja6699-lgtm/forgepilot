# New Project Implementation

## Objetivo

Aplicar este mismo stack en cualquier proyecto nuevo sin hardcodear nada a este repo.

## Paso 1: copiar la carpeta

Copia completa:

- `docs/ai_rules_kit/`

## Paso 2: crear `AGENTS.md`

Copiar:

- `templates/AGENTS.md`

A la raiz del nuevo repo como:

- `AGENTS.md`

## Paso 3: configurar MCP global

En `~/.codex/config.toml`:

1. agregar OpenAI Docs MCP
2. agregar DeepSeek bridge si vas a usar `DeepSeek-first`
3. confirmar que el bridge de DeepSeek y Graphify estan visibles antes de arrancar

## Paso 4: instalar Graphify

```powershell
uv tool install graphify
graphify install --platform codex
```

## Paso 5: instalar el gate

```powershell
pwsh .\docs\ai_rules_kit\templates\install-workflow.ps1
```

Eso deja:

- `AGENTS.md` en la raiz si faltaba
- `.githooks/pre-commit`
- `core.hooksPath=.githooks`

## Paso 6: definir estrategia de grafo

### Repo chico

Mapear directo el arbol fuente.

### Repo con assets pesados

Mapear solo:

- `src`
- `lib`
- `test`
- `docs`
- `scripts`
- `extensions`

Y luego fusionar.

## Paso 7: flujo diario

1. Graphify acota
2. packet corto
3. una consulta fuerte a DeepSeek
4. auditoria puntual de Codex
5. patch
6. validacion corta

## Paso 8: checklist rapido

```text
[ ] AGENTS.md creado en la raiz
[ ] OpenAI Docs MCP activo
[ ] DeepSeek bridge activo
[ ] Graphify instalado
[ ] estrategia de mapeo definida
[ ] no hay secrets en el repo
[ ] el flujo oficial ya esta documentado para el equipo
```

## Paso 9: errores a evitar

- meter keys al repo
- no usar Graphify como filtro
- abrir demasiadas rondas con DeepSeek
- hacer auditorias demasiado amplias
- tocar infraestructura global cuando el problema es local a un modulo
