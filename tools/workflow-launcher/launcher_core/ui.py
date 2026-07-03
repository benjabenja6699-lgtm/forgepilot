from __future__ import annotations

import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .actions import (
    ActionSpec,
    TOOL_CATALOG,
    ToolInfo,
    build_linux_config_actions,
    build_linux_install_actions,
    build_windows_config_actions,
    build_windows_install_actions,
    open_path,
)


PALETTE = {
    "bg": "#ffffff",
    "panel": "#ffffff",
    "panel_2": "#faf8f4",
    "text": "#1e1914",
    "muted": "#6f685f",
    "accent": "#c47b2b",
    "accent_2": "#8f5f1f",
    "entry": "#ffffff",
    "line": "#ece6dc",
    "soft": "#f3eee5",
}


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
        super().__init__(parent, padding=14)
        self.repo_var = repo_var
        self.log = log_fn
        self.dry_run_var = dry_run_var
        self.auto_open_var = auto_open_var
        self.action_vars: dict[str, tk.BooleanVar] = {}

        ttk.Label(self, text=title, style="HeroTitle.TLabel").pack(anchor="w", pady=(0, 8))

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
    def __init__(self, parent, log_fn, palette: dict[str, str]) -> None:
        super().__init__(parent, padding=14)
        self.log = log_fn
        self.palette = palette
        self.current_tool: ToolInfo | None = None

        ttk.Label(self, text="Herramientas", style="HeroTitle.TLabel").pack(anchor="w", pady=(0, 8))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0, 12))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Selecciona una herramienta", style="Section.TLabel").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=30, height=22, borderwidth=0, highlightthickness=1)
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

        self.palette = PALETTE

        self.repo_var = tk.StringVar(value=str(Path.cwd()))
        self.dry_run_var = tk.BooleanVar(value=False)
        self.auto_open_var = tk.BooleanVar(value=False)
        self.git_name_var = tk.StringVar(value="")
        self.git_email_var = tk.StringVar(value="")
        self.current_page = tk.StringVar(value="installers")

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
        style.configure("Sidebar.TFrame", background=self.palette["panel"], relief="flat")
        style.configure("Surface.TFrame", background=self.palette["panel"], relief="flat")
        style.configure("Inner.TFrame", background=self.palette["panel_2"])
        style.configure("TLabel", background=self.palette["bg"], foreground=self.palette["text"], font=("Segoe UI", 10))
        style.configure("HeroTitle.TLabel", background=self.palette["panel"], foreground=self.palette["text"], font=("Segoe UI", 15, "bold"))
        style.configure("Section.TLabel", background=self.palette["panel"], foreground=self.palette["text"], font=("Segoe UI", 10, "bold"))
        style.configure("Muted.TLabel", background=self.palette["panel"], foreground=self.palette["muted"], font=("Segoe UI", 9))
        style.configure("TButton", background=self.palette["panel"], foreground=self.palette["text"], padding=(8, 6), relief="flat")
        style.map(
            "TButton",
            background=[("active", self.palette["panel_2"])],
            foreground=[("active", self.palette["text"])],
        )
        style.configure("Nav.TButton", background=self.palette["panel"], foreground=self.palette["text"], padding=(10, 8), relief="flat", anchor="w")
        style.map(
            "Nav.TButton",
            background=[("active", self.palette["soft"])],
            foreground=[("active", self.palette["text"])],
        )
        style.configure("TCheckbutton", background=self.palette["panel"], foreground=self.palette["text"], font=("Segoe UI", 10))
        style.map("TCheckbutton", foreground=[("active", self.palette["accent"])])
        style.configure("TEntry", fieldbackground=self.palette["entry"], foreground=self.palette["text"], insertcolor=self.palette["text"])
        style.configure("TScrollbar", background=self.palette["panel"], troughcolor=self.palette["bg"], arrowcolor=self.palette["text"])

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12, style="Card.TFrame")
        root.pack(fill="both", expand=True)

        sidebar = ttk.Frame(root, width=250, padding=(6, 8, 18, 8), style="Sidebar.TFrame")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = ttk.Frame(sidebar, padding=(8, 8, 8, 14), style="Sidebar.TFrame")
        brand.pack(fill="x")
        badge_row = ttk.Frame(brand, style="Sidebar.TFrame")
        badge_row.pack(anchor="w", pady=(0, 12))
        badge = tk.Canvas(badge_row, width=24, height=24, bg=self.palette["panel"], highlightthickness=0)
        badge.create_rectangle(2, 2, 22, 22, outline=self.palette["accent"], width=1)
        badge.create_text(13, 13, text="FP", fill=self.palette["text"], font=("Segoe UI", 8, "bold"))
        badge.pack(side="left")
        ttk.Label(brand, text="ForgePilot", style="HeroTitle.TLabel").pack(anchor="w", pady=(0, 1))

        for key, label in [
            ("installers", "Instaladores"),
            ("configs", "Configuraciones"),
            ("tools", "Herramientas"),
            ("logs", "Logs"),
            ("settings", "Ajustes"),
        ]:
            ttk.Button(
                sidebar,
                text=label,
                command=lambda page=key: self._show_page(page),
                style="Nav.TButton",
            ).pack(fill="x", padx=4, pady=2)

        content = ttk.Frame(root, padding=(22, 10, 10, 10), style="Card.TFrame")
        content.pack(side="left", fill="both", expand=True)

        top = ttk.Frame(content, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 18))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)
        ttk.Entry(top, textvariable=self.repo_var, width=60).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(top, text="Browse", command=self._browse_repo).grid(row=0, column=1, sticky="e")

        self.page_container = ttk.Frame(content, style="Card.TFrame")
        self.page_container.pack(fill="both", expand=True)

        self.pages: dict[str, ttk.Frame] = {}
        for key in ["installers", "configs", "tools", "logs", "settings"]:
            frame = ttk.Frame(self.page_container, style="Card.TFrame")
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.pages[key] = frame

        self._build_installers_page(self.pages["installers"])
        self._build_configs_page(self.pages["configs"])
        self._build_tools_page(self.pages["tools"])
        self._build_logs_page(self.pages["logs"])
        self._build_settings_page(self.pages["settings"])

        self._show_page("installers")
        self._log("Ready.")

    def _build_installers_page(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Instaladores", style="HeroTitle.TLabel").pack(anchor="w")

        env_row = ttk.Frame(parent, style="Card.TFrame")
        env_row.pack(fill="x", pady=(0, 12))
        ttk.Button(env_row, text="Windows", command=lambda: self._swap_installers("windows")).pack(side="left")
        ttk.Button(env_row, text="Linux", command=lambda: self._swap_installers("linux")).pack(side="left", padx=6)

        self.installers_stack = ttk.Frame(parent, style="Card.TFrame")
        self.installers_stack.pack(fill="both", expand=True)

        self.win_install = ttk.Frame(self.installers_stack, style="Card.TFrame")
        self.lin_install = ttk.Frame(self.installers_stack, style="Card.TFrame")
        self.win_install.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lin_install.place(relx=0, rely=0, relwidth=1, relheight=1)

        ActionPanel(
            self.win_install,
            "Windows",
            build_windows_install_actions(),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        ).pack(fill="both", expand=True)

        ActionPanel(
            self.lin_install,
            "Linux",
            build_linux_install_actions(),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        ).pack(fill="both", expand=True)

        self._swap_installers("windows")

    def _build_configs_page(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Configuraciones", style="HeroTitle.TLabel").pack(anchor="w")

        env_row = ttk.Frame(parent, style="Card.TFrame")
        env_row.pack(fill="x", pady=(0, 12))
        ttk.Button(env_row, text="Windows", command=lambda: self._swap_configs("windows")).pack(side="left")
        ttk.Button(env_row, text="Linux", command=lambda: self._swap_configs("linux")).pack(side="left", padx=6)

        self.configs_stack = ttk.Frame(parent, style="Card.TFrame")
        self.configs_stack.pack(fill="both", expand=True)

        self.win_config = ttk.Frame(self.configs_stack, style="Card.TFrame")
        self.lin_config = ttk.Frame(self.configs_stack, style="Card.TFrame")
        self.win_config.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lin_config.place(relx=0, rely=0, relwidth=1, relheight=1)

        ActionPanel(
            self.win_config,
            "Windows",
            build_windows_config_actions(lambda: self.git_name_var.get(), lambda: self.git_email_var.get()),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        ).pack(fill="both", expand=True)

        ActionPanel(
            self.lin_config,
            "Linux",
            build_linux_config_actions(lambda: self.git_name_var.get(), lambda: self.git_email_var.get()),
            self.repo_var,
            self._log,
            self.dry_run_var,
            self.auto_open_var,
        ).pack(fill="both", expand=True)

        self._swap_configs("windows")

    def _build_tools_page(self, parent: ttk.Frame) -> None:
        ToolsPanel(parent, self._log, self.palette).pack(fill="both", expand=True)

    def _build_logs_page(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Logs", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Frame(parent, height=8, style="Card.TFrame").pack(anchor="w")
        self.log_text = tk.Text(parent, wrap="word", borderwidth=0, highlightthickness=1)
        self.log_text.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=self.log_text.yview)
        scroll.place(relx=1.0, rely=0.16, relheight=0.84, anchor="ne")
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.configure(
            bg=self.palette["entry"],
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            highlightbackground="#ddd6c9",
            highlightcolor="#ddd6c9",
            relief="flat",
            font=("Consolas", 10),
        )

    def _build_settings_page(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Ajustes", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Frame(parent, height=8, style="Card.TFrame").pack(anchor="w")
        settings = ttk.Frame(parent, padding=0, style="Card.TFrame")
        settings.pack(fill="both", expand=True)
        ttk.Checkbutton(settings, text="Dry run only", variable=self.dry_run_var).pack(anchor="w", pady=6)
        ttk.Checkbutton(settings, text="Open repo folder after successful run", variable=self.auto_open_var).pack(anchor="w", pady=6)
        ttk.Label(settings, text="Git user.name").pack(anchor="w", pady=(16, 2))
        ttk.Entry(settings, textvariable=self.git_name_var).pack(fill="x")
        ttk.Label(settings, text="Git user.email").pack(anchor="w", pady=(10, 2))
        ttk.Entry(settings, textvariable=self.git_email_var).pack(fill="x")
        ttk.Button(settings, text="Open ForgePilot repo", command=lambda: webbrowser.open("https://github.com/benjabenja6699-lgtm/forgepilot")).pack(anchor="w", pady=(16, 0))
        ttk.Button(settings, text="Open Codex docs", command=lambda: webbrowser.open("https://developers.openai.com/codex/cli")).pack(anchor="w", pady=(8, 0))

    def _swap_installers(self, kind: str) -> None:
        self.win_install.lift() if kind == "windows" else self.lin_install.lift()

    def _swap_configs(self, kind: str) -> None:
        self.win_config.lift() if kind == "windows" else self.lin_config.lift()

    def _show_page(self, key: str) -> None:
        self.current_page.set(key)
        self.pages[key].tkraise()

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

