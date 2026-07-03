from __future__ import annotations

import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from launcher_core.actions import build_linux_config_actions, build_linux_install_actions, build_windows_config_actions, build_windows_install_actions
from launcher_core.catalog import TOOL_CATALOG
from launcher_core.prereqs import format_missing_prerequisites, missing_prerequisites
from launcher_core.theme import PALETTE
import workflow_launcher


class LauncherCoreTests(unittest.TestCase):
    def test_catalog_is_unique(self) -> None:
        names = [tool.name for tool in TOOL_CATALOG]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("Graphify", names)
        self.assertIn("Caveman", names)

    def test_palette_has_core_tokens(self) -> None:
        for key in ["bg", "panel", "text", "accent", "entry", "soft"]:
            self.assertIn(key, PALETTE)

    def test_windows_install_actions_are_unique(self) -> None:
        actions = build_windows_install_actions()
        keys = [action.key for action in actions]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("base-dev", keys)
        self.assertIn("graphify", keys)
        self.assertIn("caveman", keys)

    def test_linux_install_actions_include_codex(self) -> None:
        actions = build_linux_install_actions()
        keys = {action.key for action in actions}
        self.assertIn("codex", keys)
        self.assertIn("graphify", keys)

    def test_config_actions_use_git_identity_getters(self) -> None:
        calls: list[str] = []

        def name_getter() -> str:
            calls.append("name")
            return "Ada Lovelace"

        def email_getter() -> str:
            calls.append("email")
            return "ada@example.com"

        actions = build_windows_config_actions(name_getter, email_getter)
        git_id = next(action for action in actions if action.key == "git-id")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            git_id.runner(repo, calls.append, True)

        self.assertEqual(calls[:2], ["name", "email"])
        self.assertIn("config user.name Ada Lovelace", calls[2])

    def test_entrypoint_exports_main(self) -> None:
        self.assertTrue(callable(workflow_launcher.main))

    def test_missing_prerequisites_reports_command_and_action(self) -> None:
        actions = build_windows_install_actions()
        selected = [next(action for action in actions if action.key == "base-dev")]

        with mock.patch("launcher_core.prereqs.shutil.which", return_value=None):
            missing = missing_prerequisites(selected)

        self.assertEqual(missing[0].command_name, "winget")
        self.assertIn("Base Dev tools", missing[0].actions)
        self.assertIn("winget needed by", format_missing_prerequisites(missing))


if __name__ == "__main__":
    unittest.main()
