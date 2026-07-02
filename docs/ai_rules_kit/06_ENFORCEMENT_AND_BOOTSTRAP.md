# Enforcement And Bootstrap

## Lo que si y lo que no

`AGENTS.md` persiste la regla operativa, pero no obliga al modelo a obedecer.
`MCP` expone herramientas y contexto, pero no impone disciplina por si solo.

Lo que si puede volver esto mas consistente en cualquier repo es:

- un `AGENTS.md` en la raiz
- Graphify como filtro previo
- un hook local para cambios no triviales
- un instalador corto que deje todo listo

## Regla realista

No existe un mecanismo universal que fuerce a cualquier cliente de IA a usar
DeepSeek primero. Lo maximo confiable es:

- documentar la regla
- hacerla visible en `AGENTS.md`
- instalar un gate mecanico en el repo

## Gate minimo recomendado

El gate minimo debe bloquear commits de codigo si no existe un `graphify-out/graph.json`
vigente o si el repo todavia no fue preparado con el flujo oficial.

No intentes hacer que el hook reemplace al modelo.
El hook solo debe impedir que el flujo se salte por accidente.

## Instalacion

Usa `templates/install-workflow.ps1` para:

- copiar `AGENTS.md` al repo destino si no existe
- crear `.githooks/pre-commit`
- configurar `core.hooksPath`

## Resultado

Despues de instalar esto en un proyecto nuevo, el flujo queda asi:

1. Graphify mapea
2. DeepSeek hace el trabajo pesado
3. Codex audita y ejecuta
4. el hook bloquea commits obvios sin grafo

