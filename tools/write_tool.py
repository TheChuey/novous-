"""Verb-oriented file overwrite tool backed by the shared tools interface.

The tools interface delegates to file_manager_service, the single access
boundary: every path is validated against allowed_paths.json and constrained
to the active file-manager root.
"""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="tools")
def write_file(path: str, content: str) -> str:
    """Write UTF-8 content to a workspace file by relative path (bare filenames go in the root).

    Overwrites existing files and creates missing parent directories.
    Supports formats such as .txt, .md, .py, .json, .html, .css, and .js.
    Returns JSON with the resolved path and bytes written.
    """
    if not path or not path.strip():
        raise ValueError("A file path is required.")
    from orchestration.codebuilder_run_state import codebuilder_run_state
    from orchestration.orchestration_telemetry import telemetry_bus

    context = telemetry_bus.current_context()
    if context is not None:
        codebuilder_run_state.assert_code_changes_allowed(context[0])
    try:
        result = interface.write_file(path, content)
    except Exception as exc:
        raise RuntimeError(f"Could not write '{path}': {exc}") from exc
    return json.dumps(result, ensure_ascii=False, indent=2)
