"""Save and open Python scripts for the Code Builder editor inside the allowed sandbox folders."""

import os
from pathlib import Path

from test_environment import sandbox_env, sandbox_paths

MAX_FILE_BYTES = 500_000
MAX_LISTED = 500
MAX_FOLDERS = 300
SKIP_DIRS = {"__pycache__", "venv", "node_modules"}
_BAD_NAME_CHARS = set('<>:"/\\|?*')


class FileRejected(ValueError):
    pass


def _walk(root: Path, depth: int = 3):
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return
    for entry in entries:
        if entry.name.startswith(".") or entry.name in SKIP_DIRS:
            continue
        yield entry
        if entry.is_dir() and depth > 1:
            yield from _walk(entry, depth - 1)


def listing() -> dict:
    sandbox_env.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    folders, files = [], []
    for root in sandbox_paths.allowed_roots():
        folders.append(str(root))
        for entry in _walk(root):
            if entry.is_dir():
                if len(folders) < MAX_FOLDERS:
                    folders.append(str(entry))
            elif entry.suffix.lower() == ".py" and len(files) < MAX_LISTED:
                files.append({"path": str(entry), "name": entry.name, "folder": str(entry.parent)})
    return {"default_folder": str(sandbox_env.SCRIPTS_DIR), "folders": folders, "files": files}


def read(path: str) -> dict:
    try:
        target = sandbox_paths.resolve(path)
    except sandbox_paths.PathNotAllowed as exc:
        raise FileRejected(str(exc)) from exc
    if target.suffix.lower() != ".py" or not target.is_file():
        raise FileRejected("Only existing .py files can be opened.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise FileRejected("File is too large to open in the editor.")
    return {"path": str(target), "name": target.name, "content": target.read_text(encoding="utf-8", errors="replace")}


def save(folder: str, name: str, content: str, overwrite: bool = False) -> dict:
    name = (name or "").strip()
    if not name.lower().endswith(".py"):
        name += ".py"
    if (
        name in {".py", "..py"} or any(ch in _BAD_NAME_CHARS for ch in name)
        or any(ord(ch) < 32 for ch in name) or name.endswith((" .py", "..py"))
    ):
        raise FileRejected("Use a simple file name such as app.py (no folders or special characters).")
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise FileRejected("File is too large to save.")
    try:
        directory = sandbox_paths.resolve(folder or str(sandbox_env.SCRIPTS_DIR))
    except sandbox_paths.PathNotAllowed as exc:
        raise FileRejected(str(exc)) from exc
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    if target.exists() and not overwrite:
        return {"saved": False, "exists": True, "path": str(target), "name": name}
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"saved": True, "exists": False, "path": str(target), "name": name}


def run_command(path: str, source: str) -> str:
    """Terminal command that runs a saved file; streamlit scripts use ``streamlit run``."""
    quoted = f'"{path}"' if " " in path else path
    imports = sandbox_env.imported_modules(source)
    return f"streamlit run {quoted}" if "streamlit" in imports else f"python {quoted}"
