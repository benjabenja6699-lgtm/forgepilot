# Graphify Strategy

## Regla principal

Si la tarea toca varias capas o mas de dos archivos:

- usar Graphify antes de releer el repo manualmente

## Objetivo

Graphify debe servir para acotar, no para meter ruido.

## Que mapear

Mapear:

- codigo fuente
- tests
- docs tecnicas
- scripts
- extensiones

## Que no mapear

No mapear si el objetivo es entender codigo:

- packs masivos de assets
- spritesheets
- `build`
- `dist`
- `.zip`
- `.rar`
- binarios pesados

## Patron para repos con muchos assets

1. identificar subarboles utiles
2. hacer `graphify extract` por subarbol
3. fusionar grafos
4. consultar el `graphify-out/graph.json` final

## Uso correcto con DeepSeek

1. Graphify responde que archivos y modulos importan
2. Codex arma un packet corto
3. DeepSeek analiza solo con ese contexto

## Error comun

Tener Graphify instalado pero no usarlo como filtro.

Eso produce:

- demasiada lectura manual
- demasiadas rondas con DeepSeek
- mas gasto de tokens

## Comandos base

```powershell
graphify extract .\lib
graphify extract .\test
graphify merge-graphs `
  .\lib\graphify-out\graph.json `
  .\test\graphify-out\graph.json `
  --out .\graphify-out\graph.json
graphify query "How does routing reach persistence?" --graph .\graphify-out\graph.json
```
