from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .actions import ActionSpec


WINDOWS_KNOWN_PATHS: dict[str, tuple[Path, ...]] = {
    "git": (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "git.exe",
    ),
    "gh": (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "GitHub CLI" / "gh.exe",
        Path(os.environ.get("LocalAppData", str(Path.home() / "AppData" / "Local"))) / "Programs" / "GitHub CLI" / "gh.exe",
    ),
    "python": tuple(
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / f"Python3{minor}" / "python.exe"
        for minor in range(10, 15)
    ),
    "node": (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs" / "node.exe",
    ),
    "npm": (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs" / "npm.cmd",
    ),
    "uv": (
        Path(os.environ.get("LocalAppData", str(Path.home() / "AppData" / "Local"))) / "Programs" / "uv" / "uv.exe",
        Path.home() / ".local" / "bin" / "uv.exe",
    ),
    "powershell": (
        Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
    ),
    "curl": (
        Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "curl.exe",
    ),
    "bash": (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe",
    ),
}


@dataclass(frozen=True)
class PrereqIssue:
    command_name: str
    actions: tuple[str, ...]


def resolve_command(command_name: str) -> str | None:
    found = shutil.which(command_name)
    if found:
        return found

    if platform.system() != "Windows":
        return None

    for candidate in WINDOWS_KNOWN_PATHS.get(command_name, ()):
        if candidate.exists():
            return str(candidate)

    if command_name == "python" and sys.executable and Path(sys.executable).exists():
        return sys.executable

    return None


def command_available(command_name: str) -> bool:
    return resolve_command(command_name) is not None


def missing_prerequisites(actions: Iterable["ActionSpec"]) -> list[PrereqIssue]:
    missing: dict[str, set[str]] = {}
    for action in actions:
        for command_name in action.requires:
            if command_available(command_name):
                continue
            missing.setdefault(command_name, set()).add(action.label)
    return [
        PrereqIssue(command_name=command_name, actions=tuple(sorted(labels)))
        for command_name, labels in sorted(missing.items())
    ]


def format_missing_prerequisites(issues: Iterable[PrereqIssue]) -> str:
    lines = ["Missing prerequisites detected before running:"]
    for issue in issues:
        labels_text = ", ".join(issue.actions)
        lines.append(f"- {issue.command_name} needed by: {labels_text}")
    return "\n".join(lines)
