"""Workspace mapping tool backed by the shared tools interface."""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="file_manager")
def map_files(path: str = "") -> str:
    """Return the directory tree for a path relative to the configured file-manager root."""
    return json.dumps(interface.map_files(path), ensure_ascii=False, indent=2)
