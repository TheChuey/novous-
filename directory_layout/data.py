"""directory_layout/data.py

Schemas, dataclasses, constants, JSON loaders/savers and session state.

Component: Multi-Root Security & Path Boundaries. Owns project roots,
path security and the browse tree.

Roots, browse configuration and file-classification constants live here.
Derived from __file__ so the component works from any install location.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The managed workspace (the default legacy root).
PROJECT_ROOT = REPO_ROOT / "workspace"

SOURCE_FILES_ROOT = REPO_ROOT / "source_files"

#: The isolated test environment. It is a repository sibling of the
#: application, not part of the managed workspace, but the prompt
#: builder reads its parts from there and publishes agents into it,
#: so it is browsable and writable in its own right.
TEST_ENVIRONMENT_ROOT = REPO_ROOT / "test_environment"

# ============================================================
# SCOPES
# ============================================================

#: Operations address files relative to an active root chosen by scope:
#: ``workspace`` -> the managed workspace (default);
#: ``app`` -> the application repository root (dev files).
VALID_SCOPES = ("workspace", "app")

# ============================================================
# BROWSER ROOTS
# ============================================================

# The folders the file browser shows. Add a folder here to
# make it appear in the tree; set ``writable`` to False to make it
# browse-only. Keys are the path prefixes the API understands, so
# ``source_files/APP_CODE_SNAPSHOT.md``, ``workspace/project.json`` and
# ``test_environment/test_agents/demo_agent/agent.md`` each resolve inside
# their own root.

BROWSE_ROOTS: dict[str, dict[str, Any]] = {
    "workspace": {
        "path": PROJECT_ROOT,
        "writable": True,
    },
    "test_environment": {
        "path": TEST_ENVIRONMENT_ROOT,
        "writable": True,
    },
    "source_files": {
        "path": SOURCE_FILES_ROOT,
        "writable": False,
    },
}

# Files above this size open read-only so the browser editor
# never tries to render a multi-megabyte document.

MAX_EDITABLE_BYTES = 512 * 1024

# ============================================================
# FILE TYPES
# ============================================================

TEXT_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".sql",
    ".xml",
    ".csv",
    ".env",
}

# ============================================================
# DIRECTORIES TO HIDE
# ============================================================

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
}
