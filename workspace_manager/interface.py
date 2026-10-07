"""workspace_manager/interface.py

Public doorway. The sole import surface for outside callers; exposes
public functions and the FastAPI router.

Component: Workspace Directory & Squad Hierarchies. Other components
import *only* this file for workspace scaffolding, project.json access
and the project state payload.
"""

from __future__ import annotations

from typing import Any

from .code import build_project_filesystem, read_project_info
from .data import (
    DEFAULT_PROJECT,
    PROJECT_FOLDERS,
    PROJECT_JSON,
    PROJECT_ROOT,
    REPO_ROOT,
)
from .logic import get_project_state

__all__ = [
    "DEFAULT_PROJECT",
    "PROJECT_FOLDERS",
    "PROJECT_JSON",
    "PROJECT_ROOT",
    "REPO_ROOT",
    "build_project_filesystem",
    "get_project_state",
    "read_project_info",
]
