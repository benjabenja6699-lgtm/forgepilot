from __future__ import annotations

import shutil
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .actions import ActionSpec


def command_available(command_name: str) -> bool:
    return shutil.which(command_name) is not None


def missing_prerequisites(actions: Iterable["ActionSpec"]) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for action in actions:
        for command_name in action.requires:
            if command_available(command_name):
                continue
            missing.setdefault(command_name, []).append(action.label)
    return missing
