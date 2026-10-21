"""Shared terminal for the CodeBuilder: runs one shell command at a time in the sandbox environment.

A single session is shared by the docked panel and the pop-out window. Output is kept in a
capped buffer addressed by absolute offsets so a newly opened window can catch up.
"""

import codecs
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Optional

from .execution import _kill_tree, _popen_group_kwargs

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_BUFFER_CHARS = 200_000
MAX_COMMAND_CHARS = 2000
_CD = re.compile(r"^cd(?:\s+/d)?(?:\s+(.*))?$", re.IGNORECASE)
_SANDBOX = re.compile(r"^sandbox(?:\s+(\w+))?(?:\s+(.*))?$", re.IGNORECASE)


class TerminalBusy(Exception):
    pass


class TerminalSession:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buffer = ""
        self._base = 0  # absolute offset of _buffer[0]
        self._proc: Optional[subprocess.Popen] = None
        from test_environment import sandbox_env
        sandbox_env.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        self.cwd = sandbox_env.SCRIPTS_DIR

    # ---- buffer ----
    def _append(self, text: str) -> None:
        with self._lock:
            self._buffer += text
            overflow = len(self._buffer) - MAX_BUFFER_CHARS
            if overflow > 0:
                self._buffer = self._buffer[overflow:]
                self._base += overflow

    def read(self, offset: int) -> tuple[str, int]:
        """Text after ``offset`` and the new end offset. Offsets older than the buffer are clamped."""
        with self._lock:
            start = max(offset, self._base)
            end = self._base + len(self._buffer)
            return self._buffer[start - self._base:], end

    def clear(self) -> None:
        with self._lock:
            self._base += len(self._buffer)
            self._buffer = ""

    # ---- state ----
    @property
    def running(self) -> bool:
        proc = self._proc
        return proc is not None and proc.poll() is None

    def state(self) -> dict:
        from test_environment import sandbox_env
        return {
            "running": self.running,
            "cwd": str(self.cwd),
            "sandbox": sandbox_env.exists(),
        }

    # ---- environment ----
    def _environment(self) -> dict:
        from test_environment import sandbox_env
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        if sandbox_env.exists():
            scripts = str(sandbox_env.python_path().parent)
            env["PATH"] = scripts + os.pathsep + env.get("PATH", "")
            env["VIRTUAL_ENV"] = str(sandbox_env.SANDBOX_DIR)
            env.pop("PYTHONHOME", None)
        return env

    # ---- commands ----
    def _change_directory(self, target: str) -> None:
        target = (target or "").strip().strip('"')
        if not target:
            self._append(f"{self.cwd}\n")
            return
        from test_environment import sandbox_paths
        try:
            path = sandbox_paths.resolve(target, self.cwd)
        except (sandbox_paths.PathNotAllowed, OSError) as exc:
            self._append(f"{exc}\n")
            return
        if not path.is_dir():
            self._append(f"The system cannot find the path specified: {target}\n")
            return
        self.cwd = path
        self._append(f"{self.cwd}\n")

    def _sandbox_command(self, action: str, argument: str) -> None:
        from test_environment import sandbox_env, sandbox_paths
        action = (action or "paths").lower()
        argument = (argument or "").strip()
        try:
            if action == "paths":
                self._append("Allowed folders:\n" + "".join(f"  {r}\n" for r in sandbox_paths.allowed_roots()))
                self._append(f"Packages: {sandbox_env.SANDBOX_DIR}\n")
            elif action == "add":
                self._append(f"Added: {sandbox_paths.add_root(argument)}\n")
            elif action == "remove":
                removed = sandbox_paths.remove_root(argument)
                self._append("Removed.\n" if removed else "That folder is not in the allowed list.\n")
                if not sandbox_paths.is_allowed(self.cwd):
                    self.cwd = sandbox_env.SCRIPTS_DIR
            elif action == "clear":
                sandbox_paths.clear_roots()
                self.cwd = sandbox_env.SCRIPTS_DIR
                self._append(f"Allowed folders reset to {sandbox_env.SCRIPTS_DIR}\n")
            else:
                self._append("Usage: sandbox paths | add <folder> | remove <folder> | clear\n")
        except ValueError as exc:
            self._append(f"{exc}\n")

    def run(self, command: str) -> None:
        command = command.strip()
        if not command:
            return
        if len(command) > MAX_COMMAND_CHARS:
            raise ValueError(f"Command is longer than {MAX_COMMAND_CHARS} characters.")
        with self._lock:
            if self.running:
                raise TerminalBusy("A command is already running. Stop it first.")

        self._append(f"{self.cwd}> {command}\n")
        match = _CD.match(command)
        if match:
            self._change_directory(match.group(1) or "")
            return

        sandbox_match = _SANDBOX.match(command)
        if sandbox_match:
            self._sandbox_command(sandbox_match.group(1), sandbox_match.group(2))
            return

        from test_environment import sandbox_env
        if not sandbox_env.exists():
            self._append("Creating the sandbox environment…\n")
            created = sandbox_env.ensure_venv()
            if not created["ok"]:
                self._append(f"{created['output']}\n")
                return

        self.cwd.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.Popen(
                command, shell=True, cwd=str(self.cwd), env=self._environment(),
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                **_popen_group_kwargs(),
            )
        except OSError as exc:
            self._append(f"Could not start command: {exc}\n")
            return
        self._proc = proc
        threading.Thread(target=self._pump, args=(proc,), daemon=True).start()

    def _pump(self, proc: subprocess.Popen) -> None:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        try:
            while True:
                chunk = proc.stdout.read1(4096) if hasattr(proc.stdout, "read1") else proc.stdout.read(4096)
                if not chunk:
                    break
                text = decoder.decode(chunk)
                if text:
                    self._append(text)
        except (OSError, ValueError):
            pass
        proc.wait()
        self._append(f"\n[process exited with code {proc.returncode}]\n")

    def stop(self) -> bool:
        proc = self._proc
        if proc is None or proc.poll() is not None:
            return False
        _kill_tree(proc)
        return True


session = TerminalSession()
