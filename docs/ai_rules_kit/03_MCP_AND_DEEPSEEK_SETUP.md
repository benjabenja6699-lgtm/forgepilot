# MCP And DeepSeek Setup

## MCP en una frase

`MCP` conecta Codex con herramientas y contexto externo.

## Configuracion recomendada

### Global

Todo lo reusable entre proyectos:

- `~/.codex/config.toml`

Aqui van:

- MCPs globales
- modelo por defecto
- reglas compartidas

### Por proyecto

Solo cuando sea necesario:

- `.codex/config.toml`

Usalo si el repo necesita:

- un MCP especifico
- overrides de sandbox
- hooks o reglas locales

## OpenAI Docs MCP

Para preguntas sobre OpenAI, Codex o la API:

```powershell
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

## DeepSeek bridge

Rol correcto de DeepSeek:

- analisis pesado
- plan tecnico
- propuesta de patch
- review tecnica

No edita el repo directamente.

## Ejemplo de `config.toml`

```toml
[mcp_servers.deepseek-bridge]
command = "node"
args = ["<HOME>/.codex/mcp/mcp-deepseek-bridge/index.mjs"]
startup_timeout_sec = 60

[mcp_servers.deepseek-bridge.env]
DEEPSEEK_API_KEY_FILE = "<HOME>/.codex/.sandbox-secrets/deepseek_api_key.txt"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

## Seguridad

Nunca guardar:

- API keys en el repo
- rutas personales sensibles dentro del proyecto

Guardar secretos en:

- variables de entorno
- `~/.codex/.sandbox-secrets/`

## Verificacion minima

```powershell
codex mcp list
```

Luego:

1. prueba una consulta a OpenAI Docs
2. prueba una consulta corta a DeepSeek

## Regla de uso

No usar DeepSeek para:

- reemplazar shell local
- editar archivos por si solo
- validar que el repo compile

Ese trabajo queda en Codex.
