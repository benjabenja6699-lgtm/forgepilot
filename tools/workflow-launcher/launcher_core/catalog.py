from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolInfo:
    name: str
    category: str
    summary: str
    detail: str
    docs_url: str | None = None


TOOL_CATALOG: list[ToolInfo] = [
    ToolInfo("Git", "CLI base", "Version control.", "Core VCS for repos, commits, hooks, and clone workflows."),
    ToolInfo("GitHub CLI", "CLI base", "GitHub in terminal.", "Auth, repo create, releases, PRs, issues, and automation."),
    ToolInfo("Python", "CLI base", "Interpreter + scripting.", "Needed for the launcher, utilities, and cross-platform helpers."),
    ToolInfo("Node.js", "CLI base", "JS runtime.", "Needed for npm-based CLIs and many agent toolchains."),
    ToolInfo("ripgrep", "CLI base", "Fast text search.", "Faster search tool for large repos."),
    ToolInfo("jq", "CLI base", "JSON filter.", "Terminal JSON inspection and scripting."),
    ToolInfo("fzf", "CLI base", "Interactive picker.", "Fuzzy selector for files, commands, and search results."),
    ToolInfo("direnv", "CLI base", "Per-folder env.", "Loads environment variables when entering a project folder."),
    ToolInfo("uv", "CLI base", "Python tool runner.", "Fast Python package and tool installer."),
    ToolInfo("Graphify", "Automation", "Codebase map.", "Builds a graph of code relationships so analysis can start from structure."),
    ToolInfo("Codex CLI", "Agents", "OpenAI terminal agent.", "OpenAI terminal workflow for coding and agentic tasks.", "https://developers.openai.com/codex/cli"),
    ToolInfo("Claude Code", "Agents", "Anthropic terminal agent.", "Terminal coding agent for analysis, edits, and repo work.", "https://docs.anthropic.com/en/docs/claude-code/overview"),
    ToolInfo("Gemini CLI", "Agents", "Google terminal agent.", "Terminal agent for Google-backed workflows and custom commands.", "https://github.com/google-gemini/gemini-cli"),
    ToolInfo("DeepSeek", "Providers", "DeepSeek provider.", "Provider slot for DeepSeek-backed analysis and reasoning."),
    ToolInfo("GLM", "Providers", "GLM provider.", "Provider slot for Z.ai / GLM-backed workflows."),
    ToolInfo("Antigravity CLI", "Agents", "Google agent CLI.", "Terminal surface for Antigravity multi-agent workflows.", "https://antigravity.google/product/antigravity-cli"),
    ToolInfo("Caveman", "Automation", "Token saver mode.", "Compresses assistant output so responses stay short.", "https://github.com/juliusbrussee/caveman"),
]
