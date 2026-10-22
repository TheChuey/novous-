"""Agent-facing tools for shared memory and semantic document retrieval."""

import json

from core_engine.tool_catalog import tool
from agentMemory import interface


@tool(provider="agentMemory")
def read_agent_memory(memory_type: str = "all") -> str:
    """Read the latest file content copied by read_file and/or the latest directory map copied by map_files."""
    return json.dumps(interface.read_memory(memory_type), ensure_ascii=False, indent=2)


@tool(provider="agentMemory")
def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """Search documents in workspace/Knowledge Base using semantic Ollama embeddings; returns passages with source paths and similarity scores."""
    return json.dumps(interface.search_knowledge_base(query, top_k), ensure_ascii=False, indent=2)


@tool(provider="agentMemory")
def list_knowledge_documents() -> str:
    """List documents currently indexed in the semantic Knowledge Base."""
    return json.dumps(interface.list_documents(), ensure_ascii=False, indent=2)
