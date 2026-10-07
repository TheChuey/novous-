"""workspace_manager/logic.py

Workflows, step sequencing, conditional routing and error orchestration.

Component: Workspace Directory & Squad Hierarchies. Assembles the
project state payload (project info + root + filesystem tree) used by
the dashboard and API.
"""

from __future__ import annotations

from typing import Any

from directory_layout.interface import read_filesystem

from .code import read_project_info
from .data import PROJECT_ROOT


def get_project_state() -> dict[str, Any]:
    """
    Return complete project information.

    Project info comes from project.json; the tree is the managed
    workspace walked through the directory_layout doorway.
    """

    return {
        "project": read_project_info(),
        "root": str(PROJECT_ROOT),
        "filesystem": read_filesystem(),
    }
