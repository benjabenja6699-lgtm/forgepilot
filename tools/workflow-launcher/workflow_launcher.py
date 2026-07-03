from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable


APP_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
ASSET_DIR = BASE_DIR / "assets"
AGENTS_TEMPLATE = ASSET_DIR / "AGENTS.md"
HOOK_TEMPLATE = ASSET_DIR / "pre-commit.sh.example"
CODEX_CONFIG_TEMPLATE = ASSET_DIR / "codex.config.example.toml"
MCP_TEMPLATE = ASSET_DIR / "mcp.json.example"
LOCAL_CAVEMAN_SOURCES = [
    Path.home() / ".agents" / "skills" / "caveman",
    Path.home() / ".codex" / "skills" / "caveman",
]


@dataclass(frozen=True)
class ActionSpec:
    key: str
    label: str
    runner: Callable[[Path, Callable[[str], None], bool], None]
    default: bool = True
    group: str = "General"


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


class ActionPanel(ttk.Frame):
    def __init__(
        self,
        parent,
        title: str,
        description: str,
        actions: list[ActionSpec],
        repo_var: tk.StringVar,
        log_fn,
        dry_run_var: tk.BooleanVar,
        auto_open_var: tk.BooleanVar,
    ) -> None:
        super().__init__(parent, padding=14)
        self.repo_var = repo_var
        self.log = log_fn
        self.dry_run_var = dry_run_var
        self.auto_open_var = auto_open_var
        self.action_vars: dict[str, tk.BooleanVar] = {}

        ttk.Label(self, text=title, style="HeroTitle.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(self, text=description, style="Muted.TLabel", wraplength=960, justify="left").pack(anchor="w", pady=(0, 12))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        groups: dict[str, list[ActionSpec]] = {}
        order: list[str] = []
        for action in actions:
            if action.group not in groups:
                groups[action.group] = []
                order.append(action.group)
            groups[action.group].append(action)

        for group_name in order:
            group_box = ttk.Frame(body, padding=(0, 2, 0, 10))
            group_box.pack(fill="x", expand=False, pady=(0, 8))
            header = ttk.Frame(group_box)
            header.pack(fill="x", pady=(0, 8))
            ttk.Label(header, text=group_name, style="Section.TLabel").pack(side="left", anchor="w")
            ttk.Separator(header, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(10, 0))
            for action in groups[group_name]:
                var = tk.BooleanVar(value=action.default)
                self.action_vars[action.key] = var
                row = ttk.Frame(group_box)
                row.pack(fill="x", anchor="w", pady=2)
                ttk.Checkbutton(row, text=action.label, variable=var).pack(anchor="w")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(8, 0))
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
                if self.auto_open_var.get() and not dry_run:
                    open_path(repo)
                messagebox.showinfo("Done", "Selected actions finished.")
            except Exception as exc:  # noqa: BLE001
                self.log(f"ERROR: {exc}")
                messagebox.showerror("Error", str(exc))

        threading.Thread(target=worker, daemon=True).start()


class ToolsPanel(ttk.Frame):
    def __init__(self, parent, log_fn) -> None:
        super().__init__(parent, padding=14)
        self.log = log_fn
        self.current_tool: ToolInfo | None = None

        ttk.Label(self, text="Herramientas", style="HeroTitle.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(
            self,
            text="Lista resumida de CLIs, automatizacion y proveedores usados por el launcher.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0, 12))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Selecciona una herramienta", style="Section.TLabel").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=30, height=22)
        self.listbox.pack(fill="y", expand=False, pady=(6, 0))
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        for tool in TOOL_CATALOG:
            self.listbox.insert("end", tool.name)

        self.tool_title = ttk.Label(right, text="Detalle de la herramienta", style="Section.TLabel")
        self.tool_title.pack(anchor="w")
        self.tool_summary = ttk.Label(right, text="", wraplength=560, justify="left", style="Muted.TLabel")
        self.tool_summary.pack(anchor="w", pady=(4, 8))
        self.tool_detail = tk.Text(right, height=14, wrap="word")
        self.tool_detail.pack(fill="both", expand=True)
        self.tool_detail.configure(state="disabled")

        buttons = ttk.Frame(right)
        buttons.pack(fill="x", pady=(8, 0))
        self.docs_button = ttk.Button(buttons, text="Open docs", command=self._open_docs)
        self.docs_button.pack(side="left")

        self.listbox.configure(
            bg=self.palette["entry"],
            fg=self.palette["text"],
            selectbackground=self.palette["accent"],
            selectforeground="#fffdf8",
            highlightthickness=1,
            highlightbackground="#ddd6c9",
            relief="flat",
            font=("Consolas", 10),
        )
        self.tool_detail.configure(
            bg=self.palette["entry"],
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            highlightthickness=1,
            highlightbackground="#ddd6c9",
            relief="flat",
            font=("Consolas", 10),
        )

        self.listbox.selection_set(0)
        self._show_tool(TOOL_CATALOG[0])

    def _on_select(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self._show_tool(TOOL_CATALOG[selection[0]])

    def _show_tool(self, tool: ToolInfo) -> None:
        self.current_tool = tool
        self.tool_title.configure(text=f"{tool.name}  [{tool.category}]")
        self.tool_summary.configure(text=tool.summary)
        self.tool_detail.configure(state="normal")
        self.tool_detail.delete("1.0", "end")
        self.tool_detail.insert("end", tool.detail)
        self.tool_detail.configure(state="disabled")
        if tool.docs_url:
            self.docs_button.state(["!disabled"])
        else:
            self.docs_button.state(["disabled"])

    def _open_docs(self) -> None:
        if self.current_tool and self.current_tool.docs_url:
            webbrowser.open(self.current_tool.docs_url)


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ForgePilot Launcher")
        self.geometry("1200x840")
        self.minsize(1060, 740)

        self.palette = {
            "bg": "#f4efe6",
            "panel": "#fcfaf6",
            "panel_2": "#f7f2ea",
            "text": "#1e1914",
            "muted": "#6f685f",
            "accent": "#c47b2b",
            "accent_2": "#8f5f1f",
            "entry": "#fffdf8",
        }

        self.repo_var = tk.StringVar(value=str(Path.cwd()))
        self.dry_run_var = tk.BooleanVar(value=False)
        self.auto_open_var = tk.BooleanVar(value=False)
        self.git_name_var = tk.StringVar(value="")
        self.git_email_var = tk.StringVar(value="")

        self._configure_style()
        self._build_ui()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.configure(bg=self.palette["bg"])
        style.configure("TFrame", background=self.palette["bg"])
        style.configure("Card.TFrame", background=self.palette["panel"], relief="flat")
        style.configure("Inner.TFrame", background=self.palette["panel_2"])
        style.configure("TLabel", background=self.palette["bg"], foreground=self.palette["text"], font=("Segoe UI", 10))
        style.configure("HeroTitle.TLabel", background=self.palette["bg"], foreground=self.palette["accent"], font=("Consolas", 19, "bold"))
        style.configure("Section.TLabel", background=self.palette["bg"], foreground=self.palette["text"], font=("Segoe UI", 11, "bold"))
        style.configure("Muted.TLabel", background=self.palette["bg"], foreground=self.palette["muted"], font=("Segoe UI", 9))
        style.configure("TNotebook", background=self.palette["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=self.palette["panel_2"],
            foreground=self.palette["muted"],
            padding=(16, 9),
            font=("Segoe UI", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.palette["panel"])],
            foreground=[("selected", self.palette["accent"])],
        )
        style.configure("TButton", background=self.palette["panel"], foreground=self.palette["text"], padding=(12, 8), relief="flat")
        style.map(
            "TButton",
            background=[("active", self.palette["panel_2"])],
            foreground=[("active", self.palette["text"])],
        )
        style.configure("TCheckbutton", background=self.palette["panel"], foreground=self.palette["text"], font=("Segoe UI", 10))
        style.map("TCheckbutton", foreground=[("active", self.palette["accent"])])
        style.configure("TLabelframe", background=self.palette["panel"], foreground=self.palette["accent"], borderwidth=0, relief="flat")
        style.configure("TLabelframe.Label", background=self.palette["panel"], foreground=self.palette["accent"], font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground=self.palette["entry"], foreground=self.palette["text"], insertcolor=self.palette["text"])
        style.configure("TScrollbar", background=self.palette["panel"], troughcolor=self.palette["bg"], arrowcolor=self.palette["text"])

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=18, style="Card.TFrame")
        outer.pack(fill="both", expand=True)

        hero = ttk.Frame(outer, padding=(18, 16), style="Inner.TFrame")
        hero.pack(fill="x", pady=(0, 14))
        ttk.Label(hero, text="ForgePilot Launcher", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Label(
            hero,
            text="Panel retro portable para instalar CLIs, escribir reglas, configurar hooks y lanzar Graphify.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        top = ttk.Frame(outer, padding=(2, 0))
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(top, text="Repo destino", style="Section.TLabel").pack(anchor="w")
        row = ttk.Frame(top)
        row.pack(fill="x", pady=(4, 0))
        ttk.Entry(row, textvariable=self.repo_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse", command=self._browse_repo).pack(side="left", padx=(8, 0))

        tabs = ttk.Notebook(outer)
        tabs.pack(fill="both", expand=True)

        installers_tab = ttk.Frame(tabs)
        configs_tab = ttk.Frame(tabs)
        tools_tab = ttk.Frame(tabs)
        logs_tab = ttk.Frame(tabs)
        settings_tab = ttk.Frame(tabs)
        tabs.add(installers_tab, text="Instaladores")
        tabs.add(configs_tab, text="Configuraciones")
        tabs.add(tools_tab, text="Herramientas")
        tabs.add(logs_tab, text="Logs")
        tabs.add(settings_tab, text="Ajustes")

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

        tools_panel = ToolsPanel(tools_tab, self._log)
        tools_panel.pack(fill="both", expand=True)

        self.log_text = tk.Text(logs_tab, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(logs_tab, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.configure(
            bg=self.palette["entry"],
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            highlightthickness=1,
            highlightbackground="#ddd6c9",
            relief="flat",
            font=("Consolas", 10),
        )

        settings = ttk.Frame(settings_tab, padding=14, style="Inner.TFrame")
        settings.pack(fill="both", expand=True)
        ttk.Checkbutton(settings, text="Dry run only", variable=self.dry_run_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(settings, text="Open repo folder after successful run", variable=self.auto_open_var).pack(anchor="w", pady=4)
        ttk.Label(settings, text="Git user.name").pack(anchor="w", pady=(14, 2))
        ttk.Entry(settings, textvariable=self.git_name_var).pack(fill="x")
        ttk.Label(settings, text="Git user.email").pack(anchor="w", pady=(10, 2))
        ttk.Entry(settings, textvariable=self.git_email_var).pack(fill="x")
        ttk.Button(
            settings,
            text="Open ForgePilot repo",
            command=lambda: webbrowser.open("https://github.com/benjabenja6699-lgtm/forgepilot"),
        ).pack(anchor="w", pady=(16, 0))
        ttk.Button(
            settings,
            text="Open Codex docs",
            command=lambda: webbrowser.open("https://developers.openai.com/codex/cli"),
        ).pack(anchor="w", pady=(8, 0))

        self._log("Ready.")

        windows_install_panel = ActionPanel(
            win_install,
            "Windows installers",
            "Instala los componentes mas usados en Windows. El grupo CLI base agrupa las herramientas que casi siempre hacen falta, mientras que Agents y Automation cubren los CLIs de trabajo y Graphify.",
            self._windows_install_actions(),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        )
        windows_install_panel.pack(fill="both", expand=True)

        linux_install_panel = ActionPanel(
            lin_install,
            "Linux installers",
            "Instaladores equivalentes para Linux. El grupo CLI base usa el gestor local cuando puede, y los CLIs de agentes se instalan con sus comandos oficiales.",
            self._linux_install_actions(),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        )
        linux_install_panel.pack(fill="both", expand=True)

        windows_config_panel = ActionPanel(
            win_config,
            "Windows configurations",
            "Escribe los archivos de configuracion que este launcher genera en cualquier proyecto: AGENTS.md, Codex config, MCP y hook de git.",
            self._windows_config_actions(),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        )
        windows_config_panel.pack(fill="both", expand=True)

        linux_config_panel = ActionPanel(
            lin_config,
            "Linux configurations",
            "Mismo flujo de configuracion, pero respetando la ruta y el comportamiento tipico de Linux.",
            self._linux_config_actions(),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        )
        linux_config_panel.pack(fill="both", expand=True)

    def _windows_install_actions(self) -> list[ActionSpec]:
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

    def _linux_install_actions(self) -> list[ActionSpec]:
        return [
            ActionSpec("base-dev", "CLI base (Git, GitHub CLI, Python, Node, etc.)", lambda repo, log, dry_run: install_base_dev_linux(repo, log, dry_run), group="CLI base"),
            ActionSpec("uv", "uv", lambda repo, log, dry_run: install_uv_linux(repo, log, dry_run), group="CLI base"),
            ActionSpec("codex", "Codex CLI", lambda repo, log, dry_run: install_codex_linux(repo, log, dry_run), group="Agents"),
            ActionSpec("claude", "Claude Code", lambda repo, log, dry_run: install_claude_linux(repo, log, dry_run), group="Agents"),
            ActionSpec("gemini", "Gemini CLI", lambda repo, log, dry_run: install_gemini(repo, log, dry_run), group="Agents"),
            ActionSpec("graphify", "Graphify", lambda repo, log, dry_run: install_graphify(repo, log, dry_run), group="Automation"),
            ActionSpec("caveman", "Caveman skill import", lambda repo, log, dry_run: install_caveman(log, dry_run), group="Automation"),
        ]

    def _windows_config_actions(self) -> list[ActionSpec]:
        return [
            ActionSpec("agents", "Write AGENTS.md", lambda repo, log, dry_run: copy_file(AGENTS_TEMPLATE, repo / "AGENTS.md", log, dry_run), group="Project files"),
            ActionSpec("codex-config", "Write .codex/config.toml", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log, dry_run), group="Project files"),
            ActionSpec("mcp", "Write mcp.json", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log, dry_run), group="Project files"),
            ActionSpec("hook", "Write git hook + hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run), group="Git"),
            ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, self.git_name_var.get().strip(), self.git_email_var.get().strip(), log, dry_run), group="Git"),
            ActionSpec("graphify", "Run Graphify on repo", lambda repo, log, dry_run: build_graph(repo, log, dry_run), default=False, group="Automation"),
        ]

    def _linux_config_actions(self) -> list[ActionSpec]:
        return [
            ActionSpec("agents", "Write AGENTS.md", lambda repo, log, dry_run: copy_file(AGENTS_TEMPLATE, repo / "AGENTS.md", log, dry_run), group="Project files"),
            ActionSpec("codex-config", "Write .codex/config.toml", lambda repo, log, dry_run: copy_file(CODEX_CONFIG_TEMPLATE, repo / ".codex" / "config.toml", log, dry_run), group="Project files"),
            ActionSpec("mcp", "Write mcp.json", lambda repo, log, dry_run: copy_file(MCP_TEMPLATE, repo / "mcp.json", log, dry_run), group="Project files"),
            ActionSpec("hook", "Write git hook + hooksPath", lambda repo, log, dry_run: install_hook(repo, log, dry_run), group="Git"),
            ActionSpec("git-id", "Set git name/email", lambda repo, log, dry_run: set_git_identity(repo, self.git_name_var.get().strip(), self.git_email_var.get().strip(), log, dry_run), group="Git"),
            ActionSpec("graphify", "Run Graphify on repo", lambda repo, log, dry_run: build_graph(repo, log, dry_run), default=False, group="Automation"),
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
