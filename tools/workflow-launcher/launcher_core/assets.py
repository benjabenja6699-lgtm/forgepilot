from __future__ import annotations

import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
APP_DIR = PACKAGE_DIR.parent
BASE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
ASSET_DIR = BASE_DIR / "assets"

AGENTS_TEMPLATE = ASSET_DIR / "AGENTS.md"
HOOK_TEMPLATE = ASSET_DIR / "pre-commit.sh.example"
CODEX_CONFIG_TEMPLATE = ASSET_DIR / "codex.config.example.toml"
MCP_TEMPLATE = ASSET_DIR / "mcp.json.example"
