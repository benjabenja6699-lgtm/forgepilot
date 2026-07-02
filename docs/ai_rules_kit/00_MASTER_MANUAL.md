# AI Rules Kit Master Manual

## Para que sirve esta carpeta

Esta carpeta existe para exportar a otros proyectos un flujo de trabajo estable:

- `Graphify` mapea el repo
- `DeepSeek` hace el trabajo pesado
- `Codex` audita, aplica y valida
- `AGENTS.md` deja la regla persistente dentro del repo
- un hook opcional evita commits obvios sin grafo

Si el proyecto no tiene API para automatizar modelos, el flujo sigue sirviendo igual en modo manual.

## Idea central

No se busca que `MCP` "obligue" a un modelo a portarse bien.
`MCP` solo conecta herramientas.
La persistencia real se logra con:

- `AGENTS.md` en la raiz
- documentacion operativa en `docs/ai_rules_kit/`
- Graphify como filtro de contexto
- hooks locales para disciplina mecanica

## Reglas de trabajo

### Graphify

Usar primero cuando la tarea:

- toca varias capas
- toca mas de dos archivos
- necesita entender relaciones entre modulos
- requiere revisar arquitectura

No usar para:

- assets pesados
- spritesheets
- binarios
- carpetas gigantes que no explican codigo

### DeepSeek

DeepSeek debe hacer:

- analisis pesado
- root cause analysis
- comparacion de enfoques
- planes tecnicos
- documentacion tecnica
- propuesta de patch
- review masiva

DeepSeek no debe hacer directamente:

- editar el workspace
- ejecutar comandos locales
- validar el repo real por si solo

### Codex

Codex debe hacer:

- juntar el contexto minimo
- correr Graphify o usar el grafo existente
- verificar archivos, imports y supuestos
- aplicar cambios locales
- hacer validaciones cortas

Codex no debe reescribir el analisis pesado si DeepSeek ya lo hizo.

## Flujo oficial

### Caso simple

Si es una tarea chica y local:

1. revisar directo
2. aplicar cambio
3. validar

### Caso no trivial

Si toca varias piezas:

1. usar Graphify para acotar
2. armar un packet corto
3. mandar una sola consulta fuerte a DeepSeek
4. auditar solo viabilidad minima
5. aplicar patch
6. validar corto

### Regla de ahorro de tokens

El patron correcto es:

`Graphify -> packet corto -> 1 consulta DeepSeek -> auditoria puntual -> patch -> validacion corta`

El anti-patron es:

`Graphify insuficiente + demasiada lectura manual + demasiadas iteraciones con DeepSeek + auditoria demasiado grande`

## Persistencia

### Archivo operativo

El archivo que debe existir en la raiz de cada repo es:

- `AGENTS.md`

Ese archivo debe ser corto y operativo.

Debe decir, como minimo:

- cuando usar Graphify
- que DeepSeek hace el trabajo pesado
- que Codex audita y ejecuta
- que no se debe repetir analisis

### Documentacion extendida

La explicacion completa vive en:

- `docs/ai_rules_kit/00_MASTER_MANUAL.md`
- `docs/ai_rules_kit/01_RULES_AND_WORKFLOW.md`
- `docs/ai_rules_kit/02_PERSISTENCE_AND_AGENTS.md`
- `docs/ai_rules_kit/03_MCP_AND_DEEPSEEK_SETUP.md`
- `docs/ai_rules_kit/04_GRAPHIFY_STRATEGY.md`
- `docs/ai_rules_kit/05_NEW_PROJECT_IMPLEMENTATION.md`
- `docs/ai_rules_kit/06_ENFORCEMENT_AND_BOOTSTRAP.md`

## Como exportar a otro proyecto

### Paso 1: copiar la carpeta

Copia completa:

- `docs/ai_rules_kit/`

### Paso 2: crear `AGENTS.md`

Pega `templates/AGENTS.md` en la raiz del nuevo repo como `AGENTS.md`.

### Paso 3: decidir modo de integracion

Si el nuevo proyecto usa automatizacion de modelos:

- configurar MCP global o por proyecto
- agregar DeepSeek bridge si existe
- agregar OpenAI Docs MCP si aplica

Si no tiene API:

- usar el flujo manual
- dejar `AGENTS.md`
- usar Graphify
- enviar el packet a DeepSeek manualmente

### Paso 4: instalar Graphify

Instalar Graphify si el entorno lo permite.
Luego generar el grafo del repo.

### Paso 5: instalar el gate

Usar `templates/install-workflow.ps1` para:

- copiar `AGENTS.md` si falta
- crear `.githooks/pre-commit`
- configurar `core.hooksPath`

## Que contiene cada archivo

### `README.md`

Indice corto para humanos.

### `01_RULES_AND_WORKFLOW.md`

Reglas de reparto de trabajo y flujo general.

### `02_PERSISTENCE_AND_AGENTS.md`

Como hacer persistente la regla en un repo.

### `03_MCP_AND_DEEPSEEK_SETUP.md`

Configuracion de MCP y DeepSeek.

### `04_GRAPHIFY_STRATEGY.md`

Como mapear sin ruido.

### `05_NEW_PROJECT_IMPLEMENTATION.md`

Checklist para un repo nuevo.

### `06_ENFORCEMENT_AND_BOOTSTRAP.md`

Que se puede automatizar y que sigue siendo manual.

### `templates/AGENTS.md`

Template listo para copiar a un nuevo repo.

### `templates/codex.config.example.toml`

Ejemplo de configuracion local.

### `templates/mcp.json.example`

Ejemplo alternativo para clientes que usan `mcp.json`.

### `templates/pre-commit.sh.example`

Hook base para bloquear cambios de codigo sin grafo.

### `templates/install-workflow.ps1`

Instalador portable del flujo.

## Regla para repos sin API

Si no hay API externa:

1. no intentar automatizar un router de modelos
2. dejar la regla en `AGENTS.md`
3. usar Graphify para acotar
4. usar DeepSeek manualmente cuando haga falta
5. dejar a Codex en auditoria y ejecucion

## Regla para repos con assets pesados

No mapear todo.
Mapear solo lo que explique el codigo:

- `src`
- `lib`
- `test`
- `docs`
- `scripts`
- `extensions`

## Checklist de exportacion

- `AGENTS.md` creado en la raiz
- carpeta `docs/ai_rules_kit/` copiada
- `Graphify` disponible o documentado
- `DeepSeek` disponible o flujo manual definido
- `core.hooksPath` configurado si se quiere gate
- no hay secretos incrustados en el repo

## Regla final

La carpeta no existe para reemplazar criterio.
Existe para que otro proyecto herede el mismo orden:

`Graphify acota -> DeepSeek piensa -> Codex ejecuta -> hook protege`

## Regla de salida

Usar `caveman full` solo en respuestas de salida para economizar tokens.
