"""Generate a comprehensive, AI-agent-readable snapshot of the Novous application."""
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now().strftime("%Y%m%d")
try:
    COMMIT = os.popen("git rev-parse --short HEAD").read().strip()
except Exception:
    COMMIT = "unknown"

EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "node_modules", "dist", "build"}
INCLUDE_EXT = {".py", ".js", ".css", ".html", ".json", ".md", ".txt", ".bat", ".sh", ".yaml", ".yml", ".cfg", ".ini"}
SKIP_FILES = {"MASTER_COPY.md", "novous-ai-builder-prompt-v2.md"}

OUT = ROOT / "app_documentation" / f"NOVOUS_APP_SNAPSHOT_{TODAY}_new.md"


def get_lang(ext: str) -> str:
    ext = ext.lower().lstrip('.')
    return {
        "py": "python",
        "js": "javascript",
        "json": "json",
        "html": "html",
        "css": "css",
        "md": "markdown",
        "txt": "text",
        "bat": "batch",
        "sh": "bash",
        "yaml": "yaml",
        "yml": "yaml",
        "cfg": "ini",
        "ini": "ini",
    }.get(ext, ext)


def collect_files():
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES or path.name.startswith("NOVOUS_APP_SNAPSHOT") or path.name.startswith("MASTER_COPY"):
            continue
        if path.suffix.lower() not in INCLUDE_EXT and path.name in {"Dockerfile", "Procfile"}:
            pass
        elif path.suffix.lower() not in INCLUDE_EXT:
            continue
        files.append(path)
    return files


def write_tree(f):
    f.write("## 3) File Structure Snapshot\n\n")
    for path in sorted(ROOT.rglob("*")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.name in SKIP_FILES or path.name.startswith("NOVOUS_APP_SNAPSHOT") or path.name.startswith("MASTER_COPY"):
            continue
        f.write(f"- {rel}{'/' if path.is_dir() else ''}\n")
    f.write("\n")


def main():
    files = collect_files()
    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Name: Novous Application Snapshot\n")
        f.write(f"Filename: {OUT.name}\n")
        f.write(f"Commit: {COMMIT}\n")
        f.write(f"Description: Self-contained reference for an AI agent. Captures Novous app purpose, architecture, file structure, and complete source code. Designed for grounding/understanding without repo access.\n\n")
        f.write("# NOVOUS APPLICATION SNAPSHOT\n\n")
        f.write("## 1) Overview\n\n")
        f.write("Novous is an agent orchestration/workspace system with FastAPI backend, static frontend, core engine for agents/tools, editor integration, workspace/agents configuration, and test environment.\n\n")
        f.write("Key components:\n- server.py: FastAPI app entrypoint serving static UI and API routes\n- core_engine/: agent factory, runtime, tool catalog, langgraph tools\n- editor/: editor session/operations/schemas/interface\n- frontend/: static assets and HTML pages (chat, editor, index, testing)\n- workspace/: agent definitions and workflow utilities\n- test_environment/: prompt builder, test runner, test agents\n\n")
        f.write("## 2) Table of Contents\n\n")
        f.write("1. Overview\n")
        f.write("2. File Structure Snapshot\n")
        f.write("3. Complete Source Code (by file)\n\n")
        write_tree(f)
        f.write("## 4) Complete Source Code (by file)\n\n")
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            lang = get_lang(path.suffix)
            f.write(f"### {rel}\n\n")
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                text = f"<unreadable: {e}>"
            f.write(f"`{lang}\n{text}\n`\n\n")

    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()
