from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from launcher_core.actions import build_prereq_install_actions, copy_file, copy_tree, install_base_dev_linux, install_base_dev_windows, install_hook


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

    def test_install_base_dev_windows_runs_pack_and_uv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            logs: list[str] = []

            with (
                patch("launcher_core.actions.shutil.which", return_value="winget"),
                patch("launcher_core.actions.install_via_winget") as winget_mock,
                patch("launcher_core.actions.install_uv_windows") as uv_mock,
            ):
                install_base_dev_windows(repo, logs.append, False)

            self.assertGreaterEqual(winget_mock.call_count, 8)
            uv_mock.assert_called_once_with(repo, logs.append, False)

    def test_install_base_dev_linux_includes_runtime_prereqs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            logs: list[str] = []

            with (
                patch("launcher_core.actions.run_command") as run_mock,
                patch("launcher_core.actions.install_uv_linux") as uv_mock,
            ):
                install_base_dev_linux(repo, logs.append, False)

            run_mock.assert_called_once()
            command = run_mock.call_args.args[0]
            script = command[2]
            self.assertIn("python3-tk", script)
            self.assertIn("curl", script)
            self.assertIn("ca-certificates", script)
            uv_mock.assert_called_once_with(repo, logs.append, False)

    def test_prereq_plan_suggests_base_dev_and_graphify(self) -> None:
        with mock.patch("launcher_core.actions.resolve_command", return_value=None), mock.patch("launcher_core.actions.shutil.which", return_value="winget"):
            actions = build_prereq_install_actions(
                [
                    type("Dummy", (), {"requires": ("graphify",)})(),
                ]
            )
        keys = [action.key for action in actions]
        self.assertIn("base-dev", keys)
        self.assertIn("graphify", keys)


if __name__ == "__main__":
    unittest.main()
