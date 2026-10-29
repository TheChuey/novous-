"""Shared file-scope rules for the generated Novous application documents.

``gen_app_snapshot.py`` and ``gen_master_copy.py`` both import these rules so the
two documents always describe exactly the same set of files.

The scope deliberately omits local, user-owned content: the agent scratchpad and
RAG database, the configuration files that record the author's private folder
paths, and everything the author keeps inside ``workspace/`` other than the
package source itself. The rules are expressed as patterns rather than as lists
of personal file names, so the generated documents never disclose them.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    "app_documentation",
    "test_agents",
    "test_reports",
    "model_logs",
}

INCLUDE_EXT = {
    ".py",
    ".js",
    ".css",
    ".html",
    ".json",
    ".md",
    ".txt",
    ".bat",
    ".sh",
    ".yaml",
    ".yml",
    ".cfg",
    ".ini",
}

EXTENSIONLESS_INCLUDE = {"Dockerfile", "Procfile"}

# Local runtime state, regenerated on demand.
PRIVATE_DIRS = ("agentMemory/data",)

# Configuration files whose values point at the author's private folders.
PRIVATE_CONTENT_FILES = (
    "agentMemory/rag_config.json",
    "tools/allowed_paths.json",
)

# The workspace package holds the canonical project state next to locally
# authored content. Only its Python modules and ``project.json`` are documented;
# every subdirectory and every other file type is treated as private content.
WORKSPACE_PACKAGE = "workspace"
WORKSPACE_SOURCE_EXT = {".py"}
WORKSPACE_SOURCE_FILES = {"project.json"}

SKIP_FILES = {
    "novous2-ai-builder-prompt-v2.md",
    "rag_config.json",
    "SubAgentOrchastrationPlan.md",
}
SKIP_PREFIXES = ("NOVOUS_APP_SNAPSHOT", "NOVOUS2_APP_SNAPSHOT", "MASTER_COPY")


def _norm(rel: str) -> str:
    return rel.replace("\\", "/")


def is_private_dir(rel: str) -> bool:
    """True for directories that hold local, user-owned content."""
    rel = _norm(rel)
    if any(rel == prefix or rel.startswith(prefix + "/") for prefix in PRIVATE_DIRS):
        return True
    return rel.startswith(WORKSPACE_PACKAGE + "/")


def is_private_file(rel: str) -> bool:
    """True for files that must not appear in the documented file structure."""
    rel = _norm(rel)
    if any(rel.startswith(prefix + "/") for prefix in PRIVATE_DIRS):
        return True
    if not rel.startswith(WORKSPACE_PACKAGE + "/"):
        return False
    name = rel[len(WORKSPACE_PACKAGE) + 1:]
    if "/" in name:
        return True
    if Path(name).suffix.lower() in WORKSPACE_SOURCE_EXT:
        return False
    return name not in WORKSPACE_SOURCE_FILES


def is_private_content(rel: str) -> bool:
    """True for files whose contents must not be embedded in the documents."""
    rel = _norm(rel)
    if rel in PRIVATE_CONTENT_FILES:
        return True
    return is_private_file(rel)


def is_skipped_name(name: str) -> bool:
    return name in SKIP_FILES or name.startswith(SKIP_PREFIXES)


def is_included_file(path: Path) -> bool:
    if path.suffix.lower() in INCLUDE_EXT:
        return True
    return path.name in EXTENSIONLESS_INCLUDE


def _relative_dir(root: Path, dirpath: str) -> str:
    rel = Path(dirpath).relative_to(root).as_posix()
    return "" if rel == "." else rel


def iter_source_files(root: Path = ROOT):
    """Yield ``(relative_posix_path, path)`` for every file inside the documented scope."""
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = _relative_dir(root, dirpath)
        kept_dirs = []
        for name in sorted(dirnames):
            child = f"{rel_dir}/{name}" if rel_dir else name
            if name in EXCLUDE_DIRS or is_private_dir(child):
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            if name in EXCLUDE_DIRS or is_skipped_name(name):
                continue
            child = f"{rel_dir}/{name}" if rel_dir else name
            if is_private_content(child):
                continue
            path = Path(dirpath) / name
            if not is_included_file(path):
                continue
            yield child, path


def iter_tree(root: Path = ROOT):
    """Return ``(relative_posix_path, is_dir)`` entries for the documented file structure."""
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = _relative_dir(root, dirpath)
        kept_dirs = []
        for name in sorted(dirnames):
            child = f"{rel_dir}/{name}" if rel_dir else name
            if name in EXCLUDE_DIRS or is_private_dir(child):
                continue
            kept_dirs.append(name)
            entries.append((child, True))
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            if name in EXCLUDE_DIRS or is_skipped_name(name):
                continue
            child = f"{rel_dir}/{name}" if rel_dir else name
            if is_private_file(child):
                continue
            entries.append((child, False))
    entries.sort(key=lambda item: item[0])
    return entries


def fence_for(text: str, minimum: int = 3) -> str:
    """Return a backtick fence long enough to wrap ``text`` without being closed by it."""
    longest = 0
    run = 0
    for char in text:
        if char == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return "`" * max(minimum, longest + 1)
