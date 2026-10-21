"""Workspace file deletion tool backed by the shared tools interface."""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="tools")
def delete_file(path: str) -> str:
    """Delete a file or directory from the workspace by relative path."""
    if not path or not path.strip():
        raise ValueError("A path is required.")
    result = interface.delete_file(path)
    return json.dumps(result, ensure_ascii=False, indent=2)
