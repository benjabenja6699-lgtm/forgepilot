# Rules And Workflow

## Objetivo

Separar claramente responsabilidades para ahorrar tokens y subir calidad:

- `Graphify` mapea
- `DeepSeek` analiza, planifica, documenta y revisa
- `Codex` solo ejecuta, audita breve y valida

## Reparto de roles

### Graphify

Hace:

- mapa del repo
- query de relaciones
- path entre modulos
- contexto estructural

No hace:

- corregir bugs
- validar compilacion
- reemplazar tests

### DeepSeek

Hace:

- analisis pesado
- root cause analysis
- comparacion de enfoques
- plan tecnico
- documentacion tecnica
- propuesta de patch
- review tecnica masiva

No hace:

- editar archivos del workspace
- ejecutar shell local
- verificar el estado real del repo

### Codex

Hace:

- leer solo el contexto minimo necesario
- verificar archivos, simbolos, imports y supuestos criticos
- aplicar cambios
- correr validaciones cortas
- reportar riesgos reales

## Flujo obligatorio

### Tarea local o pequena

Si toca uno o dos archivos y no necesita arquitectura:

1. Codex inspecciona directo
2. DeepSeek opcional
3. Codex aplica
4. Codex valida

### Tarea de varias capas

Si toca varios archivos, pipeline o arquitectura:

1. usar Graphify primero
2. construir packet corto
3. hacer una sola consulta fuerte a DeepSeek
4. Codex audita solo viabilidad minima
5. Codex aplica patch
6. Codex valida

## Modo austero de tokens

Cuando la prioridad sea gastar menos tokens de Codex:

1. si ya existe `graphify-out/graph.json`, consultar ese grafo antes de releer codigo
2. armar un solo packet corto
3. hacer una sola consulta fuerte a DeepSeek
4. evitar segundas o terceras rondas salvo fallo real
5. auditar solo simbolos, imports, archivos y supuestos concretos
6. no convertir la auditoria en un segundo analisis completo

## Anti-patron

Esto es lo que no debe pasar:

1. Graphify no acota suficiente
2. Codex relee demasiado codigo manualmente
3. se abren varias rondas con DeepSeek por detalles pequenos
4. la auditoria crece y replica el analisis
5. Codex termina escribiendo el plan o la documentacion tecnica

Resultado:

- se gastan tokens de Codex innecesariamente
- se rompe el flujo `DeepSeek-first`

## Patron correcto

`Graphify acota -> packet corto -> 1 consulta DeepSeek -> auditoria breve -> patch -> validacion corta`
