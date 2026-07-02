# Project AI Rules

## Flujo obligatorio

Cuando la tarea no sea trivial:

1. usar `Graphify` primero
2. acotar con el grafo antes de releer codigo manualmente
3. armar un packet corto
4. hacer una sola consulta fuerte a `DeepSeek`
5. dejar a Codex solo en auditoria breve de viabilidad, patch y validacion corta

## Regla de propiedad

`DeepSeek` hace el trabajo pesado:

- analisis
- planes
- documentacion tecnica
- revisiones masivas
- propuesta de patch

`Codex` no debe rehacer eso.
`Codex` solo:

- verifica lo minimo necesario
- aplica cambios
- valida localmente

## Regla de ahorro de tokens

No rehacer el analisis pesado si ya existe:

- `graphify-out/graph.json`
- una propuesta viable de `DeepSeek`

Evitar:

- varias rondas con `DeepSeek` por detalles pequenos
- relectura manual amplia del repo cuando el grafo ya acoto
- auditorias largas que repliquen el analisis

Patron correcto:

- `Graphify -> packet corto -> 1 consulta DeepSeek -> auditoria puntual -> patch -> validacion corta`

## Reparto de roles

### DeepSeek

Hace:

- analisis pesado
- root cause analysis
- plan tecnico
- documentacion tecnica
- propuesta de patch
- review tecnica masiva

No hace:

- editar archivos del workspace
- ejecutar shell local

### Codex

Hace:

- verificar archivos, simbolos, imports y supuestos
- aplicar cambios
- validar localmente

## Reglas locales del repo

- completar aqui reglas especificas del proyecto
