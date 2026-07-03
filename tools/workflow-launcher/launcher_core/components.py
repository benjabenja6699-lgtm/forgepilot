from __future__ import annotations

import threading
import platform
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

from .actions import ActionSpec, build_prereq_install_actions, open_path
from .catalog import TOOL_CATALOG, ToolInfo
from .prereqs import format_missing_prerequisites, missing_prerequisites


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

        missing = missing_prerequisites(selected)
        prereq_actions = build_prereq_install_actions(selected)
        if missing:
            message = format_missing_prerequisites(missing)
            self.log(message)
            if not prereq_actions:
                messagebox.showerror("Missing prerequisites", message)
                return
            install = messagebox.askyesno(
                "Missing prerequisites",
                f"{message}\n\nInstall prerequisites now?",
            )
            if not install:
                return

        dry_run = self.dry_run_var.get()

        def worker() -> None:
            try:
                self.log(f"Repo: {repo}")
                self.log(f"Mode: {'dry-run' if dry_run else 'apply'}")
                for prereq_action in prereq_actions:
                    self.log(f"Installing prerequisite: {prereq_action.label}")
                    prereq_action.runner(repo, self.log, dry_run)
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
