"""Workspace mapping tool backed by the shared tools interface."""

import json

from agentMemory import interface as agent_memory
from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="file_manager")
def map_files(path: str = "") -> str:
    """Return a directory tree and save a copy in the shared agent-memory scratchpad."""
    tree = interface.map_files(path)
    agent_memory.store_map(tree, path)
    return json.dumps(tree, ensure_ascii=False, indent=2)
