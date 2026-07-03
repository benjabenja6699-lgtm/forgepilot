from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from dataclasses import dataclass

from .assets import AGENTS_TEMPLATE, CODEX_CONFIG_TEMPLATE, HOOK_TEMPLATE, MCP_TEMPLATE
from .catalog import ToolInfo


@dataclass(frozen=True)
class ActionSpec:
    key: str
    label: str
    runner: Callable[[Path, Callable[[str], None], bool], None]
    default: bool = True
    group: str = "General"

LOCAL_CAVEMAN_SOURCES = [
    Path.home() / ".agents" / "skills" / "caveman",
    Path.home() / ".codex" / "skills" / "caveman",
]


def run_command(command: list[str], cwd: Path | None, log, dry_run: bool = False) -> None:
    log(f"$ {' '.join(command)}")
    if dry_run:
        return
    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        shell=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if output.strip():
        log(output.rstrip())
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}")


def open_path(path: Path) -> None:
    if platform.system() == "Windows":
        os.startfile(str(path))  # noqa: S606
        return
    subprocess.Popen(["xdg-open", str(path)])


def copy_file(src: Path, dst: Path, log, dry_run: bool = False) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing source: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        log(f"$ copy {src} -> {dst}")
        return
    shutil.copy2(src, dst)
    log(f"Copied {src} -> {dst}")


def copy_tree(src: Path, dst: Path, log, dry_run: bool = False) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing source: {src}")
    if dry_run:
        log(f"$ copytree {src} -> {dst}")
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    log(f"Copied {src} -> {dst}")


def install_via_winget(package_id: str, repo: Path, log, dry_run: bool) -> None:
    run_command(["winget", "install", "--id", package_id, "-e"], repo, log, dry_run)


def install_graphify(repo: Path, log, dry_run: bool) -> None:
    run_command(["uv", "tool", "install", "graphify"], repo, log, dry_run)
    run_command(["graphify", "install", "--platform", "codex"], repo, log, dry_run)


def install_caveman(log, dry_run: bool = False) -> None:
    source = next((p for p in LOCAL_CAVEMAN_SOURCES if p.exists()), None)
    if source is None:
        raise FileNotFoundError(
            "No caveman skill source found in ~/.agents/skills/caveman or ~/.codex/skills/caveman"
        )

    for target in [
        Path.home() / ".agents" / "skills" / "caveman",
        Path.home() / ".codex" / "skills" / "caveman",
    ]:
        copy_tree(source, target, log, dry_run=dry_run)


def install_claude_windows(repo: Path, log, dry_run: bool) -> None:
    run_command(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "irm https://claude.ai/install.ps1 | iex"],
        repo,
        log,
        dry_run,
    )


def install_claude_linux(repo: Path, log, dry_run: bool) -> None:
    run_command(["bash", "-lc", "curl -fsSL https://claude.ai/install.sh | bash"], repo, log, dry_run)


def install_codex_linux(repo: Path, log, dry_run: bool) -> None:
    run_command(["bash", "-lc", "curl -fsSL https://chatgpt.com/codex/install.sh | sh"], repo, log, dry_run)


def install_gemini(repo: Path, log, dry_run: bool) -> None:
    run_command(["npm", "install", "-g", "@google/gemini-cli"], repo, log, dry_run)


def install_uv_windows(repo: Path, log, dry_run: bool) -> None:
    run_command(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "irm https://astral.sh/uv/install.ps1 | iex"],
        repo,
        log,
        dry_run,
    )


def install_uv_linux(repo: Path, log, dry_run: bool) -> None:
    run_command(["bash", "-lc", "curl -LsSf https://astral.sh/uv/install.sh | sh"], repo, log, dry_run)


def install_base_dev_windows(repo: Path, log, dry_run: bool) -> None:
    for package_id in [
        "Git.Git",
        "GitHub.cli",
        "Python.Python.3.13",
        "OpenJS.NodeJS.LTS",
        "BurntSushi.ripgrep.MSVC",
        "jqlang.jq",
        "junegunn.fzf",
        "direnv.direnv",
    ]:
        install_via_winget(package_id, repo, log, dry_run)


def install_base_dev_linux(repo: Path, log, dry_run: bool) -> None:
    script = r"""
set -e
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y git gh python3 python3-pip nodejs npm ripgrep jq fzf direnv
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y git gh python3 python3-pip nodejs npm ripgrep jq fzf direnv
elif command -v pacman >/dev/null 2>&1; then
  sudo pacman -Sy --noconfirm git github-cli python nodejs npm ripgrep jq fzf direnv
else
  echo "No supported package manager found."
  exit 1
fi
"""
    run_command(["bash", "-lc", script], repo, log, dry_run)


def install_agents(repo: Path, log, dry_run: bool) -> None:
    copy_file(AGENTS_TEMPLATE, repo / "AGENTS.md", log, dry_run=dry_run)


def install_hook(repo: Path, log, dry_run: bool) -> None:
    hook_target = repo / ".githooks" / "pre-commit"
    copy_file(HOOK_TEMPLATE, hook_target, log, dry_run=dry_run)
    if dry_run:
        return
    git = shutil.which("git")
    if not git:
        raise FileNotFoundError("git not found in PATH")
    run_command(["git", "-C", str(repo), "config", "core.hooksPath", ".githooks"], repo, log)


def set_git_identity(repo: Path, name: str, email: str, log, dry_run: bool) -> None:
    if not name or not email:
        raise ValueError("Git name/email required")
    run_command(["git", "-C", str(repo), "config", "user.name", name], repo, log, dry_run)
    run_command(["git", "-C", str(repo), "config", "user.email", email], repo, log, dry_run)


def build_graph(repo: Path, log, dry_run: bool) -> None:
    run_command(["graphify", "."], repo, log, dry_run)


def build_windows_install_actions() -> list[ActionSpec]:
    return [
        ActionSpec("git", "Git", lambda repo, log, dry_run: install_via_winget("Git.Git", repo, log, dry_run), group="CLI base"),
        ActionSpec("gh", "GitHub CLI", lambda repo, log, dry_run: install_via_winget("GitHub.cli", repo, log, dry_run), group="CLI base"),
        ActionSpec("python", "Python", lambda repo, log, dry_run: install_via_winget("Python.Python.3.13", repo, log, dry_run), group="CLI base"),
        ActionSpec("node", "Node.js", lambda repo, log, dry_run: install_via_winget("OpenJS.NodeJS.LTS", repo, log, dry_run), group="CLI base"),
        ActionSpec("rg", "ripgrep", lambda repo, log, dry_run: install_via_winget("BurntSushi.ripgrep.MSVC", repo, log, dry_run), group="CLI base"),
        ActionSpec("jq", "jq", lambda repo, log, dry_run: install_via_winget("jqlang.jq", repo, log, dry_run), group="CLI base"),
        ActionSpec("fzf", "fzf", lambda repo, log, dry_run: install_via_winget("junegunn.fzf", repo, log, dry_run), group="CLI base"),
        ActionSpec("direnv", "direnv", lambda repo, log, dry_run: install_via_winget("direnv.direnv", repo, log, dry_run), group="CLI base"),
        ActionSpec("uv", "uv", lambda repo, log, dry_run: install_uv_windows(repo, log, dry_run), group="CLI base"),
        ActionSpec("graphify", "Graphify", lambda repo, log, dry_run: install_graphify(repo, log, dry_run), group="Automation"),
        ActionSpec("claude", "Claude Code", lambda repo, log, dry_run: install_claude_windows(repo, log, dry_run), group="Agents"),
        ActionSpec("gemini", "Gemini CLI", lambda repo, log, dry_run: install_gemini(repo, log, dry_run), group="Agents"),
        ActionSpec("caveman", "Caveman skill import", lambda repo, log, dry_run: install_caveman(log, dry_run), group="Automation"),
    ]


def build_linux_install_actions() -> list[ActionSpec]:
    return [
        ActionSpec("base-dev", "CLI base (Git, GitHub CLI, Python, Node, etc.)", lambda repo, log, dry_run: install_base_dev_linux(repo, log, dry_run), group="CLI base"),
        ActionSpec("uv", "uv", lambda repo, log, dry_run: install_uv_linux(repo, log, dry_run), group="CLI base"),
        ActionSpec("codex", "Codex CLI", lambda repo, log, dry_run: install_codex_linux(repo, log, dry_run), group="Agents"),
        ActionSpec("claude", "Claude Code", lambda repo, log, dry_run: install_claude_linux(repo, log, dry_run), group="Agents"),
        ActionSpec("gemini", "Gemini CLI", lambda repo, log, dry_run: install_gemini(repo, log, dry_run), group="Agents"),
        ActionSpec("graphify", "Graphify", lambda repo, log, dry_run: install_graphify(repo, log, dry_run), group="Automation"),
        ActionSpec("caveman", "Caveman skill import", lambda repo, log, dry_run: install_caveman(log, dry_run), group="Automation"),
    ]


def build_windows_config_actions(name_getter: Callable[[], str], email_getter: Callable[[], str]) -> list[ActionSpec]:
    return [
        ActionSpec("agents", "Write AGENTS.md", lambda repo, log, dry_run: copy_file(AGENTS_TEMPLATE, repo / "AGENTS.md", log, dry_run), group="Project files"),
        ActionSpec("codex-config", "Write .codex/config.toml", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log, dry_run), group="Project files"),
        ActionSpec("mcp", "Write mcp.json", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log, dry_run), group="Project files"),
        ActionSpec("hook", "Write git hook + hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run), group="Git"),
        ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, name_getter().strip(), email_getter().strip(), log, dry_run), group="Git"),
        ActionSpec("graphify", "Run Graphify on repo", lambda repo, log, dry_run: build_graph(repo, log, dry_run), default=False, group="Automation"),
    ]


def build_linux_config_actions(name_getter: Callable[[], str], email_getter: Callable[[], str]) -> list[ActionSpec]:
    return [
        ActionSpec("agents", "Write AGENTS.md", lambda repo, log, dry_run: copy_file(AGENTS_TEMPLATE, repo / "AGENTS.md", log, dry_run), group="Project files"),
        ActionSpec("codex-config", "Write .codex/config.toml", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log, dry_run), group="Project files"),
        ActionSpec("mcp", "Write mcp.json", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log, dry_run), group="Project files"),
        ActionSpec("hook", "Write git hook + hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run), group="Git"),
        ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, name_getter().strip(), email_getter().strip(), log, dry_run), group="Git"),
        ActionSpec("graphify", "Run Graphify on repo", lambda repo, log, dry_run: build_graph(repo, log, dry_run), default=False, group="Automation"),
    ]
