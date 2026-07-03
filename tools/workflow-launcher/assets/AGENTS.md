# Project AI Rules

- Use Graphify first when `graphify-out/graph.json` already exists and the task asks about architecture, dependencies, or cross-file behavior.
- For OpenAI or Codex questions, use the OpenAI developer documentation MCP server before general web search.
- Use DeepSeek for heavy analysis, root-cause work, refactor planning, and patch drafting.
- Keep Codex in audit mode: verify files, symbols, commands, and validation steps against the real repo before applying changes.
- Do not store secrets in the repository. Use user-level secrets or environment variables.
