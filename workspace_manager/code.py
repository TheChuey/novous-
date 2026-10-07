"""workspace_manager/code.py

Stateful engine classes, core objects and active execution loops.

Component: Workspace Directory & Squad Hierarchies. Builds and reads the
physical workspace: the standard folder set and project.json.
"""

from __future__ import annotations

from typing import Any

from .data import (
    DEFAULT_PROJECT,
    PROJECT_FOLDERS,
    PROJECT_ROOT,
    load_project_json,
    write_default_project_json,
)


def build_project_filesystem() -> None:
    """
    Create the standard Project Manager filesystem.

    Existing files and folders are never deleted.

    Safe to run every time the server starts.
    """

    # --------------------------------------------------------
    # Create standard directories
    # --------------------------------------------------------

    for folder_name in PROJECT_FOLDERS:
        folder_path = PROJECT_ROOT / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Create project.json
    # --------------------------------------------------------

    write_default_project_json()


def read_project_info() -> dict[str, Any]:
    """
    Read project.json.

    Returns:
        Project information dictionary.
    """

    loaded = load_project_json()

    if loaded is None:
        return DEFAULT_PROJECT.copy()

    return loaded
