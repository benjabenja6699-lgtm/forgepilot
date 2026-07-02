# Persistence And AGENTS

## Problema

Un `.md` cualquiera no vuelve persistente una regla para Codex.

Si la regla vive solo en documentacion humana:

- es facil que se ignore
- no necesariamente se usa como instruccion operativa

## Solucion correcta

Para persistencia dentro de un repo, usa:

- `AGENTS.md` en la raiz

## Por que `AGENTS.md`

Es el lugar corto y operativo para dejar:

- reglas del repo
- flujo obligatorio
- prioridades de herramientas
- restricciones locales

## Que debe ir en `AGENTS.md`

Solo lo mas operativo:

- usar Graphify primero cuando la tarea no sea trivial
- usar una sola consulta fuerte a DeepSeek
- dejar a Codex en auditoria puntual, patch y validacion
- reglas especificas del repo

## Que no debe ir en `AGENTS.md`

- manuales largos
- explicaciones historicas
- contexto de una sola sesion
- tutoriales extensos

Eso debe vivir en docs como esta carpeta.

## Implementacion recomendada

1. crear `AGENTS.md` en la raiz del repo
2. dejar el flujo corto y obligatorio
3. apuntar desde ahi a la documentacion extensa
4. mantenerlo pequeno para que sea legible y estable

## Estructura ejemplo

```text
repo/
  AGENTS.md
  docs/
    ai_rules_kit/
      README.md
      01_RULES_AND_WORKFLOW.md
      02_PERSISTENCE_AND_AGENTS.md
      03_MCP_AND_DEEPSEEK_SETUP.md
      04_GRAPHIFY_STRATEGY.md
      05_NEW_PROJECT_IMPLEMENTATION.md
      templates/
```

## Regla practica

Fuente de verdad operativa:

- `AGENTS.md`

Explicacion extendida:

- `docs/ai_rules_kit/`
