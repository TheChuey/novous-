"""Agent-facing tools for scratchpad memory and named knowledge branches."""

import json

from core_engine.tool_catalog import tool
from agentMemory import interface


@tool(provider="agentMemory")
def read_agent_scratchpad(memory_type: str = "all") -> str:
    """Read recent file contents and/or the latest workspace map saved in agent scratchpad memory."""
    return json.dumps(interface.read_memory(memory_type), ensure_ascii=False, indent=2)


@tool(provider="agentMemory")
def get_knowledge_catalog() -> str:
    """Get the live Knowledge TOC: exact branch names, IDs, status, and indexed document/chunk counts. Use this first to find a branch ID."""
    branches = [
        {
            "name": base["name"],
            "id": str(base["id"]),
            "status": "active" if base.get("active", True) else "archived",
            "selected": bool(base.get("selected")),
            "folder_available": bool(base.get("exists")),
            "indexed_documents": int(base.get("documents", 0)),
            "chunks": int(base.get("chunks", 0)),
        }
        for base in interface.list_rag_bases()
    ]
    return json.dumps(
        {"title": "Knowledge TOC", "branches": branches},
        ensure_ascii=False,
        indent=2,
    )


@tool(provider="agentMemory")
def search_knowledge_branch(
    query: str, top_k: int = 5, knowledge_branch_id: str = ""
) -> str:
    """Find relevant passages for a question in one knowledge branch. Get its ID from get_knowledge_catalog and pass it as knowledge_branch_id; results are source text for answering the user."""
    return json.dumps(
        interface.search_knowledge_base(
            query, top_k, base_id=knowledge_branch_id or None
        ),
        ensure_ascii=False,
        indent=2,
    )


@tool(provider="agentMemory")
def list_knowledge_branch_documents(knowledge_branch_id: str = "") -> str:
    """List indexed document names, paths, and chunk counts in a branch. Use get_knowledge_catalog first and pass the matching branch ID; this lists metadata, not document contents."""
    return json.dumps(
        interface.list_documents(knowledge_branch_id or None),
        ensure_ascii=False,
        indent=2,
    )


@tool(provider="agentMemory")
def read_knowledge_branch_document(
    document_path: str, knowledge_branch_id: str = ""
) -> str:
    """Read the full indexed text of one document. Use get_knowledge_catalog and list_knowledge_branch_documents first, then pass the exact listed path and branch ID."""
    document = interface.get_document(document_path, knowledge_branch_id or None)
    return json.dumps(
        {
            "path": document["path"],
            "chunks": len(document["chunks_data"]),
            "content": "\n\n".join(
                chunk["content"] for chunk in document["chunks_data"]
            ),
        },
        ensure_ascii=False,
        indent=2,
    )
