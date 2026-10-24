"""Permanent storage for custom tools promoted from the Prompt Testing Workbench.

Promoted tools are appended below the PROMOTION_MARKER by tools/interface.py,
which performs AST validation, registry updates, and rollback on failure.
"""
from core_engine.tool_catalog import tool

# PROMOTION_MARKER: tools appended below will be registered as custom tools

import json
import os


@tool
def create_folder(path: str) -> str:
    """Create workspace folders using relative paths.

    - Creates a folder, including any missing parent directories, at the specified path.
    - Uses exist_ok=True to avoid errors if the directory already exists.
    - Returns JSON describing the folder creation operation.
    """
    if not path or not path.strip():
        raise ValueError("A folder path is required.")

    try:
        # os.makedirs creates directories recursively. exist_ok=True prevents errors if the directory exists.
        os.makedirs(path, exist_ok=True)
        result = {"path": path, "type": "directory", "created": True}

    except Exception as exc:
        raise RuntimeError(
            f"Could not create folder '{path}': {exc}"
        ) from exc

    return json.dumps(result, ensure_ascii=False, indent=2)

