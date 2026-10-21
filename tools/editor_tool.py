"""Editor operations tool backed by the shared tools interface."""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="editor")
def editor(action: str, path: str = "", content: str = "") -> str:
    """Read, write, list a tree, or delete a path through the editor pillar."""
    result = interface.editor(action, path=path, content=content)
    return json.dumps(result, ensure_ascii=False, indent=2)
