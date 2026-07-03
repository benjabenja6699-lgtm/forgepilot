from __future__ import annotations

import os
import platform
import shutil
import subprocess
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent
KIT_DIR = REPO_ROOT / "docs" / "ai_rules_kit"
AGENTS_TEMPLATE = KIT_DIR / "templates" / "AGENTS.md"
HOOK_TEMPLATE = KIT_DIR / "templates" / "pre-commit.sh.example"
CODEX_CONFIG_TEMPLATE = KIT_DIR / "templates" / "codex.config.example.toml"
MCP_TEMPLATE = KIT_DIR / "templates" / "mcp.json.example"
LOCAL_CAVEMAN_SOURCES = [
    Path.home() / ".agents" / "skills" / "caveman",
    Path.home() / ".codex" / "skills" / "caveman",
]


@dataclass(frozen=True)
class ActionSpec:
    key: str
    label: str
    runner: callable
    default: bool = True


def shell_runner(command: str, windows: bool) -> callable:
    def _run(repo: Path, log, dry_run: bool) -> None:
        if windows:
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        else:
            cmd = ["bash", "-lc", command]
        run_command(cmd, repo, log, dry_run)

    return _run


def run_command(command: list[str], cwd: Path | None, log, dry_run: bool) -> None:
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


def copy_file(src: Path, dst: Path, log) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing source: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log(f"Copied {src} -> {dst}")


def copy_tree(src: Path, dst: Path, log) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing source: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    log(f"Copied {src} -> {dst}")


def install_graphify(repo: Path, log, dry_run: bool) -> None:
    run_command(["uv", "tool", "install", "graphifyy"], repo, log, dry_run)
    run_command(["graphify", "install", "--platform", "codex"], repo, log, dry_run)


def install_claude_windows(repo: Path, log, dry_run: bool) -> None:
    run_command(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "irm https://claude.ai/install.ps1 | iex"], repo, log, dry_run)


def install_claude_linux(repo: Path, log, dry_run: bool) -> None:
    run_command(["bash", "-lc", "curl -fsSL https://claude.ai/install.sh | bash"], repo, log, dry_run)


def install_codex_linux(repo: Path, log, dry_run: bool) -> None:
    run_command(["bash", "-lc", "curl -fsSL https://chatgpt.com/codex/install.sh | sh"], repo, log, dry_run)


def install_gemini(repo: Path, log, dry_run: bool) -> None:
    run_command(["npm", "install", "-g", "@google/gemini-cli"], repo, log, dry_run)


def install_uv_windows(repo: Path, log, dry_run: bool) -> None:
    run_command(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", 'irm https://astral.sh/uv/install.ps1 | iex'], repo, log, dry_run)


def install_uv_linux(repo: Path, log, dry_run: bool) -> None:
    run_command(["bash", "-lc", "curl -LsSf https://astral.sh/uv/install.sh | sh"], repo, log, dry_run)


def install_via_winget(package_id: str, repo: Path, log, dry_run: bool) -> None:
    run_command(["winget", "install", "--id", package_id, "-e"], repo, log, dry_run)


def install_caveman(repo: Path, log, dry_run: bool) -> None:
    source = next((p for p in LOCAL_CAVEMAN_SOURCES if p.exists()), None)
    if source is None:
        raise FileNotFoundError(
            "No caveman skill source found in ~/.agents/skills/caveman or ~/.codex/skills/caveman"
        )
    for target in [Path.home() / ".agents" / "skills" / "caveman", Path.home() / ".codex" / "skills" / "caveman"]:
        if dry_run:
            log(f"$ copy {source} -> {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            copy_tree(source, target, log)


def install_ai_rules_kit(repo: Path, log, dry_run: bool) -> None:
    target = repo / "docs" / "ai_rules_kit"
    if dry_run:
        log(f"$ copy {KIT_DIR} -> {target}")
        return
    copy_tree(KIT_DIR, target, log)


def install_agents(repo: Path, log, dry_run: bool) -> None:
    target = repo / "AGENTS.md"
    if dry_run:
        log(f"$ copy {AGENTS_TEMPLATE} -> {target}")
        return
    copy_file(AGENTS_TEMPLATE, target, log)


def install_hook(repo: Path, log, dry_run: bool) -> None:
    hook_target = repo / ".githooks" / "pre-commit"
    if dry_run:
        log(f"$ copy {HOOK_TEMPLATE} -> {hook_target}")
        log(f"$ git -C {repo} config core.hooksPath .githooks")
        return
    copy_file(HOOK_TEMPLATE, hook_target, log)
    run_command(["git", "-C", str(repo), "config", "core.hooksPath", ".githooks"], repo, log, dry_run)


def set_git_identity(repo: Path, name: str, email: str, log, dry_run: bool) -> None:
    if not name or not email:
        raise ValueError("Git name/email required")
    run_command(["git", "-C", str(repo), "config", "user.name", name], repo, log, dry_run)
    run_command(["git", "-C", str(repo), "config", "user.email", email], repo, log, dry_run)


class ActionPanel(ttk.Frame):
    def __init__(
        self,
        parent,
        title: str,
        actions: list[ActionSpec],
        repo_var: tk.StringVar,
        log_fn,
        dry_run_var: tk.BooleanVar,
        auto_open_var: tk.BooleanVar,
    ) -> None:
        super().__init__(parent, padding=12)
        self.repo_var = repo_var
        self.log = log_fn
        self.dry_run_var = dry_run_var
        self.auto_open_var = auto_open_var
        self.action_vars: dict[str, tk.BooleanVar] = {}

        header = ttk.Label(self, text=title, font=("Segoe UI", 13, "bold"))
        header.pack(anchor="w", pady=(0, 8))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        for idx, action in enumerate(actions):
            var = tk.BooleanVar(value=action.default)
            self.action_vars[action.key] = var
            ttk.Checkbutton(body, text=action.label, variable=var).grid(row=idx, column=0, sticky="w", padx=4, pady=4)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Run selected", command=lambda: self._run(actions)).pack(side="left")
        ttk.Button(buttons, text="Select all", command=lambda: self._set_all(True)).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear all", command=lambda: self._set_all(False)).pack(side="left")

    def _set_all(self, value: bool) -> None:
        for var in self.action_vars.values():
            var.set(value)

    def _run(self, actions: list[ActionSpec]) -> None:
        repo = Path(self.repo_var.get()).expanduser()
        if not repo.exists():
            messagebox.showerror("Error", f"Repo path does not exist:\n{repo}")
            return

        selected = [action for action in actions if self.action_vars[action.key].get()]
        if not selected:
            messagebox.showinfo("Nothing selected", "Choose at least one action.")
            return

        dry_run = self.dry_run_var.get()

        def worker() -> None:
            try:
                self.log(f"Repo: {repo}")
                self.log(f"Mode: {'dry-run' if dry_run else 'apply'}")
                for action in selected:
                    self.log(f"Running: {action.label}")
                    action.runner(repo, self.log, dry_run)
                self.log("Done.")
                if self.auto_open_var.get():
                    open_path(repo)
                messagebox.showinfo("Done", "Selected actions finished.")
            except Exception as exc:  # noqa: BLE001
                self.log(f"ERROR: {exc}")
                messagebox.showerror("Error", str(exc))

        threading.Thread(target=worker, daemon=True).start()


def build_windows_configs(repo_var, log_fn, dry_run_var, git_name_var, git_email_var) -> ActionPanel:
    actions = [
        ActionSpec("kit", "Copy ai_rules_kit into repo", lambda repo, log, dry_run: install_ai_rules_kit(repo, log, dry_run)),
        ActionSpec("agents", "Install AGENTS.md", lambda repo, log, dry_run: install_agents(repo, log, dry_run)),
        ActionSpec("hook", "Install git hook and hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run)),
        ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, git_name_var.get().strip(), git_email_var.get().strip(), log, dry_run)),
        ActionSpec("codex-config", "Copy Codex config template", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log) if not dry_run else log(f"$ copy {CODEX_CONFIG_TEMPLATE} -> {repo / '.codex/config.toml'}")),
        ActionSpec("mcp", "Copy MCP config template", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log) if not dry_run else log(f"$ copy {MCP_TEMPLATE} -> {repo / 'mcp.json'}")),
    ]
    return ActionPanel(None, "Windows configurations", actions, repo_var, log_fn, dry_run_var)


def build_linux_configs(repo_var, log_fn, dry_run_var, git_name_var, git_email_var) -> ActionPanel:
    actions = [
        ActionSpec("kit", "Copy ai_rules_kit into repo", lambda repo, log, dry_run: install_ai_rules_kit(repo, log, dry_run)),
        ActionSpec("agents", "Install AGENTS.md", lambda repo, log, dry_run: install_agents(repo, log, dry_run)),
        ActionSpec("hook", "Install git hook and hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run)),
        ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, git_name_var.get().strip(), git_email_var.get().strip(), log, dry_run)),
        ActionSpec("codex-config", "Copy Codex config template", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log) if not dry_run else log(f"$ copy {CODEX_CONFIG_TEMPLATE} -> {repo / '.codex/config.toml'}")),
        ActionSpec("mcp", "Copy MCP config template", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log) if not dry_run else log(f"$ copy {MCP_TEMPLATE} -> {repo / 'mcp.json'}")),
    ]
    return ActionPanel(None, "Linux configurations", actions, repo_var, log_fn, dry_run_var)


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ForgePilot Suite")
        self.geometry("1100x760")
        self.minsize(980, 680)

        self.repo_var = tk.StringVar(value=str(Path.cwd()))
        self.dry_run_var = tk.BooleanVar(value=False)
        self.auto_open_var = tk.BooleanVar(value=False)
        self.git_name_var = tk.StringVar(value="")
        self.git_email_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)

        top = ttk.Frame(outer)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="Repo destino").pack(anchor="w")
        row = ttk.Frame(top)
        row.pack(fill="x", pady=(4, 0))
        entry = ttk.Entry(row, textvariable=self.repo_var)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse", command=self._browse_repo).pack(side="left", padx=(8, 0))

        tabs = ttk.Notebook(outer)
        tabs.pack(fill="both", expand=True)

        installers_tab = ttk.Frame(tabs)
        configs_tab = ttk.Frame(tabs)
        logs_tab = ttk.Frame(tabs)
        settings_tab = ttk.Frame(tabs)
        tabs.add(installers_tab, text="Instaladores")
        tabs.add(configs_tab, text="Configuraciones")
        tabs.add(logs_tab, text="Logs")
        tabs.add(settings_tab, text="Settings")

        install_nb = ttk.Notebook(installers_tab)
        install_nb.pack(fill="both", expand=True, padx=2, pady=2)
        win_install = ttk.Frame(install_nb)
        lin_install = ttk.Frame(install_nb)
        install_nb.add(win_install, text="Windows")
        install_nb.add(lin_install, text="Linux")

        config_nb = ttk.Notebook(configs_tab)
        config_nb.pack(fill="both", expand=True, padx=2, pady=2)
        win_config = ttk.Frame(config_nb)
        lin_config = ttk.Frame(config_nb)
        config_nb.add(win_config, text="Windows")
        config_nb.add(lin_config, text="Linux")

        self.log_text = tk.Text(logs_tab, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(logs_tab, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

        settings = ttk.Frame(settings_tab, padding=14)
        settings.pack(fill="both", expand=True)
        ttk.Checkbutton(settings, text="Dry run only", variable=self.dry_run_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(settings, text="Open repo folder after successful run", variable=self.auto_open_var).pack(anchor="w", pady=4)
        ttk.Label(settings, text="Git user.name").pack(anchor="w", pady=(14, 2))
        ttk.Entry(settings, textvariable=self.git_name_var).pack(fill="x")
        ttk.Label(settings, text="Git user.email").pack(anchor="w", pady=(10, 2))
        ttk.Entry(settings, textvariable=self.git_email_var).pack(fill="x")
        ttk.Button(settings, text="Open ForgePilot repo", command=lambda: webbrowser.open("https://github.com/benjabenja6699-lgtm/forgepilot")).pack(anchor="w", pady=(16, 0))
        ttk.Button(settings, text="Open Codex docs", command=lambda: webbrowser.open("https://developers.openai.com/codex/cli")).pack(anchor="w", pady=(8, 0))

        self._log("Ready.")

        windows_install_panel = ActionPanel(win_install, "Windows installers", self._windows_install_actions(), self.repo_var, self._log, self.dry_run_var, self.auto_open_var)
        windows_install_panel.pack(fill="both", expand=True)
        linux_install_panel = ActionPanel(lin_install, "Linux installers", self._linux_install_actions(), self.repo_var, self._log, self.dry_run_var, self.auto_open_var)
        linux_install_panel.pack(fill="both", expand=True)

        windows_config_panel = ActionPanel(win_config, "Windows configurations", self._windows_config_actions(), self.repo_var, self._log, self.dry_run_var, self.auto_open_var)
        windows_config_panel.pack(fill="both", expand=True)
        linux_config_panel = ActionPanel(lin_config, "Linux configurations", self._linux_config_actions(), self.repo_var, self._log, self.dry_run_var, self.auto_open_var)
        linux_config_panel.pack(fill="both", expand=True)

    def _windows_install_actions(self) -> list[ActionSpec]:
        return [
            ActionSpec("graphify", "Graphify", lambda repo, log, dry_run: install_graphify(repo, log, dry_run)),
            ActionSpec("claude", "Claude Code", lambda repo, log, dry_run: install_claude_windows(repo, log, dry_run)),
            ActionSpec("gemini", "Gemini CLI", lambda repo, log, dry_run: install_gemini(repo, log, dry_run)),
            ActionSpec("uv", "uv", lambda repo, log, dry_run: install_uv_windows(repo, log, dry_run)),
            ActionSpec("caveman", "Caveman skill import", lambda repo, log, dry_run: install_caveman(repo, log, dry_run)),
        ]

    def _linux_install_actions(self) -> list[ActionSpec]:
        return [
            ActionSpec("codex", "Codex CLI", lambda repo, log, dry_run: install_codex_linux(repo, log, dry_run)),
            ActionSpec("claude", "Claude Code", lambda repo, log, dry_run: install_claude_linux(repo, log, dry_run)),
            ActionSpec("gemini", "Gemini CLI", lambda repo, log, dry_run: install_gemini(repo, log, dry_run)),
            ActionSpec("graphify", "Graphify", lambda repo, log, dry_run: install_graphify(repo, log, dry_run)),
            ActionSpec("uv", "uv", lambda repo, log, dry_run: install_uv_linux(repo, log, dry_run)),
            ActionSpec("caveman", "Caveman skill import", lambda repo, log, dry_run: install_caveman(repo, log, dry_run)),
        ]

    def _windows_config_actions(self) -> list[ActionSpec]:
        return [
            ActionSpec("kit", "Copy ai_rules_kit into repo", lambda repo, log, dry_run: install_ai_rules_kit(repo, log, dry_run)),
            ActionSpec("agents", "Install AGENTS.md", lambda repo, log, dry_run: copy_file(AGENTS_TEMPLATE, repo / "AGENTS.md", log) if not dry_run else log(f"$ copy {AGENTS_TEMPLATE} -> {repo / 'AGENTS.md'}")),
            ActionSpec("hook", "Install git hook and hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run)),
            ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, self.git_name_var.get().strip(), self.git_email_var.get().strip(), log, dry_run)),
            ActionSpec("codex-config", "Copy Codex config template", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log) if not dry_run else log(f"$ copy {CODEX_CONFIG_TEMPLATE} -> {repo / '.codex/config.toml'}")),
            ActionSpec("mcp", "Copy MCP config template", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log) if not dry_run else log(f"$ copy {MCP_TEMPLATE} -> {repo / 'mcp.json'}")),
        ]

    def _linux_config_actions(self) -> list[ActionSpec]:
        return [
            ActionSpec("kit", "Copy ai_rules_kit into repo", lambda repo, log, dry_run: install_ai_rules_kit(repo, log, dry_run)),
            ActionSpec("agents", "Install AGENTS.md", lambda repo, log, dry_run: copy_file(AGENTS_TEMPLATE, repo / "AGENTS.md", log) if not dry_run else log(f"$ copy {AGENTS_TEMPLATE} -> {repo / 'AGENTS.md'}")),
            ActionSpec("hook", "Install git hook and hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run)),
            ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, self.git_name_var.get().strip(), self.git_email_var.get().strip(), log, dry_run)),
            ActionSpec("codex-config", "Copy Codex config template", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log) if not dry_run else log(f"$ copy {CODEX_CONFIG_TEMPLATE} -> {repo / '.codex/config.toml'}")),
            ActionSpec("mcp", "Copy MCP config template", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log) if not dry_run else log(f"$ copy {MCP_TEMPLATE} -> {repo / 'mcp.json'}")),
        ]

    def _log(self, text: str) -> None:
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _browse_repo(self) -> None:
        selected = filedialog.askdirectory(title="Select repo folder", initialdir=self.repo_var.get() or str(Path.cwd()))
        if selected:
            self.repo_var.set(selected)


def main() -> None:
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
