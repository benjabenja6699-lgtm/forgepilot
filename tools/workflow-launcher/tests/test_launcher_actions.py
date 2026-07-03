from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from launcher_core.actions import copy_file, copy_tree, install_hook


class LauncherActionTests(unittest.TestCase):
    def test_copy_file_writes_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src = root / "src.txt"
            dst = root / "nested" / "dst.txt"
            src.write_text("forgepilot", encoding="utf-8")

            logs: list[str] = []
            copy_file(src, dst, logs.append)

            self.assertTrue(dst.exists())
            self.assertEqual(dst.read_text(encoding="utf-8"), "forgepilot")
            self.assertIn(f"Copied {src} -> {dst}", logs)

    def test_copy_tree_copies_nested_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src = root / "src"
            src.mkdir()
            (src / "a.txt").write_text("a", encoding="utf-8")
            (src / "sub").mkdir()
            (src / "sub" / "b.txt").write_text("b", encoding="utf-8")
            dst = root / "dst"

            logs: list[str] = []
            copy_tree(src, dst, logs.append)

            self.assertEqual((dst / "a.txt").read_text(encoding="utf-8"), "a")
            self.assertEqual((dst / "sub" / "b.txt").read_text(encoding="utf-8"), "b")
            self.assertIn(f"Copied {src} -> {dst}", logs)

    def test_install_hook_runs_git_hooks_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            logs: list[str] = []

            with (
                patch("launcher_core.actions.copy_file") as copy_mock,
                patch("launcher_core.actions.shutil.which", return_value="git"),
                patch("launcher_core.actions.run_command") as run_mock,
            ):
                install_hook(repo, logs.append, False)

            copy_mock.assert_called_once()
            run_mock.assert_called_once_with(["git", "-C", str(repo), "config", "core.hooksPath", ".githooks"], repo, logs.append)

    def test_install_hook_dry_run_skips_git_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            logs: list[str] = []

            with (
                patch("launcher_core.actions.copy_file") as copy_mock,
                patch("launcher_core.actions.run_command") as run_mock,
            ):
                install_hook(repo, logs.append, True)

            copy_mock.assert_called_once()
            run_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
