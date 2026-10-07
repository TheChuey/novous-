"""workspace_manager/data.py

Schemas, dataclasses, constants, JSON loaders/savers and session state.

Component: Workspace Directory & Squad Hierarchies. The workspace's own
layout constants (folders, project.json, default project info) live
here. Paths are derived from __file__ so nothing outside this component
has to be imported.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The managed workspace directory.
PROJECT_ROOT = REPO_ROOT / "workspace"

PROJECT_JSON = PROJECT_ROOT / "project.json"

# ============================================================
# STANDARD PROJECT FOLDERS
# ============================================================

PROJECT_FOLDERS = [
    "documentation",
    "project_scope",
    "To Do",
    "updates",
    "config",
    "data",
    "Tests",
]

# ============================================================
# DEFAULT PROJECT INFORMATION
# ============================================================

DEFAULT_PROJECT = {
    "name": PROJECT_ROOT.name,
    "version": "1.0.0",
    "workspace_version": "1.0",
}


def load_project_json() -> dict[str, Any] | None:
    """Parse project.json, or None when it is absent or unreadable."""

    if not PROJECT_JSON.exists():
        return None

    try:
        return json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_default_project_json() -> None:
    """Create project.json with DEFAULT_PROJECT when it does not exist."""

    if not PROJECT_JSON.exists():
        PROJECT_JSON.write_text(
            json.dumps(DEFAULT_PROJECT, indent=4),
            encoding="utf-8",
        )
