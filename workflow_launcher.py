from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent
KIT_DIR = REPO_ROOT / "docs" / "ai_rules_kit"
AGENTS_TEMPLATE = KIT_DIR / "templates" / "AGENTS.md"
HOOK_TEMPLATE = KIT_DIR / "templates" / "pre-commit.sh.example"
CAVEMAN_SOURCE_CANDIDATES = [
    Path.home() / ".agents" / "skills" / "caveman",
    Path.home() / ".codex" / "skills" / "caveman",
]


@dataclass
class StepResult:
    name: str
    ok: bool
    output: str


def run_command(command: list[str], cwd: Path | None, log) -> StepResult:
    log(f"$ {' '.join(command)}")
    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        shell=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if out.strip():
        log(out.rstrip())
    return StepResult(" ".join(command), proc.returncode == 0, out)


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


def install_caveman(log) -> list[StepResult]:
    source = next((p for p in CAVEMAN_SOURCE_CANDIDATES if p.exists()), None)
    if source is None:
        raise FileNotFoundError(
            "No caveman skill source found in ~/.agents/skills/caveman or ~/.codex/skills/caveman"
        )

    results: list[StepResult] = []
    targets = [
        Path.home() / ".agents" / "skills" / "caveman",
        Path.home() / ".codex" / "skills" / "caveman",
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_tree(source, target, log)
        results.append(StepResult(f"copy caveman -> {target}", True, ""))
    return results


def install_graphify(log) -> list[StepResult]:
    results = []
    results.append(run_command(["uv", "tool", "install", "graphifyy"], REPO_ROOT, log))
    if not results[-1].ok:
        return results
    results.append(run_command(["graphify", "install", "--platform", "codex"], REPO_ROOT, log))
    return results


def install_repo_kit(repo: Path, overwrite_agents: bool, overwrite_hook: bool, log) -> list[StepResult]:
    results: list[StepResult] = []
    if not KIT_DIR.exists():
        raise FileNotFoundError(f"Missing kit directory: {KIT_DIR}")

    target_kit = repo / "docs" / "ai_rules_kit"
    copy_tree(KIT_DIR, target_kit, log)
    results.append(StepResult("copy ai_rules_kit", True, ""))

    agents_target = repo / "AGENTS.md"
    if overwrite_agents or not agents_target.exists():
        shutil.copy2(AGENTS_TEMPLATE, agents_target)
        log(f"Installed {agents_target}")
        results.append(StepResult("write AGENTS.md", True, ""))

    hooks_dir = repo / ".githooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_target = hooks_dir / "pre-commit"
    if overwrite_hook or not hook_target.exists():
        shutil.copy2(HOOK_TEMPLATE, hook_target)
        log(f"Installed {hook_target}")
        results.append(StepResult("write pre-commit hook", True, ""))

    git = shutil.which("git")
    if git:
        results.append(run_command([git, "-C", str(repo), "config", "core.hooksPath", ".githooks"], repo, log))
    else:
        raise FileNotFoundError("git not found in PATH")

    return results


def build_graph(repo: Path, log) -> StepResult:
    return run_command(["graphify", "."], repo, log)


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Workflow Launcher")
        self.geometry("920x680")
        self.minsize(860, 620)

        self.repo_var = tk.StringVar(value=str(Path.cwd()))
        self.graphify_var = tk.BooleanVar(value=True)
        self.caveman_var = tk.BooleanVar(value=True)
        self.kit_var = tk.BooleanVar(value=True)
        self.agents_var = tk.BooleanVar(value=True)
        self.hook_var = tk.BooleanVar(value=True)
        self.build_graph_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)

        top = ttk.Frame(outer)
        top.pack(fill="x")

        ttk.Label(top, text="Repo destino").pack(anchor="w")
        row = ttk.Frame(top)
        row.pack(fill="x", pady=(4, 10))
        entry = ttk.Entry(row, textvariable=self.repo_var)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse", command=self._browse_repo).pack(side="left", padx=(8, 0))

        checks = ttk.LabelFrame(outer, text="Acciones")
        checks.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(checks, text="Install Graphify CLI + Codex registration", variable=self.graphify_var).grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ttk.Checkbutton(checks, text="Install Caveman skill to user skills", variable=self.caveman_var).grid(row=1, column=0, sticky="w", padx=10, pady=6)
        ttk.Checkbutton(checks, text="Copy ai_rules_kit into repo", variable=self.kit_var).grid(row=2, column=0, sticky="w", padx=10, pady=6)
        ttk.Checkbutton(checks, text="Write AGENTS.md", variable=self.agents_var).grid(row=3, column=0, sticky="w", padx=10, pady=6)
        ttk.Checkbutton(checks, text="Install git hook (.githooks/pre-commit)", variable=self.hook_var).grid(row=4, column=0, sticky="w", padx=10, pady=6)
        ttk.Checkbutton(checks, text="Run Graphify on repo after install", variable=self.build_graph_var).grid(row=5, column=0, sticky="w", padx=10, pady=6)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Run Selected", command=self._run_selected).pack(side="left")
        ttk.Button(actions, text="Open Repo Folder", command=self._open_repo).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear Log", command=self._clear_log).pack(side="left")

        log_frame = ttk.LabelFrame(outer, text="Log")
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, wrap="word", height=20)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

        self._log("Ready.")

    def _log(self, text: str) -> None:
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", "end")

    def _browse_repo(self) -> None:
        selected = filedialog.askdirectory(title="Select repo folder", initialdir=self.repo_var.get() or str(Path.cwd()))
        if selected:
            self.repo_var.set(selected)

    def _open_repo(self) -> None:
        repo = Path(self.repo_var.get()).expanduser()
        if repo.exists():
            os.startfile(str(repo))  # noqa: S606 - local file explorer launch
        else:
            messagebox.showerror("Error", "Repo path does not exist.")

    def _run_selected(self) -> None:
        repo = Path(self.repo_var.get()).expanduser()
        if not repo.exists():
            messagebox.showerror("Error", f"Repo path does not exist:\n{repo}")
            return

        selected = {
            "graphify": self.graphify_var.get(),
            "caveman": self.caveman_var.get(),
            "kit": self.kit_var.get(),
            "agents": self.agents_var.get(),
            "hook": self.hook_var.get(),
            "build_graph": self.build_graph_var.get(),
        }

        def worker() -> None:
            try:
                self._log(f"Repo: {repo}")
                if selected["graphify"]:
                    self._log("Installing Graphify...")
                    graphify_results = install_graphify(self._log)
                    if any(not item.ok for item in graphify_results):
                        raise RuntimeError("Graphify install failed.")

                if selected["caveman"]:
                    self._log("Installing Caveman skill...")
                    install_caveman(self._log)

                if selected["kit"] or selected["agents"] or selected["hook"]:
                    self._log("Installing repo workflow kit...")
                    install_repo_kit(
                        repo,
                        overwrite_agents=selected["agents"],
                        overwrite_hook=selected["hook"],
                        log=self._log,
                    )

                if selected["build_graph"]:
                    self._log("Building Graphify map...")
                    result = build_graph(repo, self._log)
                    if not result.ok:
                        raise RuntimeError("Graphify build failed.")

                self._log("Done.")
                messagebox.showinfo("Done", "Selected actions finished.")
            except Exception as exc:  # noqa: BLE001
                self._log(f"ERROR: {exc}")
                messagebox.showerror("Error", str(exc))

        threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
