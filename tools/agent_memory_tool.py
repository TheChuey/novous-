"""Agent-facing tools for scratchpad memory and named knowledge branches."""

import json

from core_engine.tool_catalog import tool
from agentMemory import interface
from orchestration.rag_retriever import RAG_RETRIEVER_ID, run_rag_retriever


@tool(provider="agentMemory")
def read_agent_scratchpad(memory_type: str = "all") -> str:
    """Read scratchpad entries ('latest_subagent_result', 'latest_read', 'latest_map', or 'all')."""
    return json.dumps(interface.read_memory(memory_type), ensure_ascii=False, indent=2)


@tool(provider="agentMemory")
def call_subagent(subagent_id: str, task_prompt: str, parameters: str = "{}") -> str:
    """Dynamically invoke a background sub-agent from subAgentLibrary/ with a task prompt and parameters."""
    if subagent_id == RAG_RETRIEVER_ID:
        parsed_params = parameters
        if isinstance(parameters, str):
            try:
                parsed_params = json.loads(parameters or "{}")
            except json.JSONDecodeError:
                pass
        return run_rag_retriever(task_prompt, parsed_params)

    from orchestration.orchestration_interface import run_agent_turn

    parsed_params = {}
    if isinstance(parameters, dict):
        parsed_params = parameters
    elif isinstance(parameters, str) and parameters.strip().startswith("{"):
        parsed_params = json.loads(parameters)
    if not isinstance(parsed_params, dict):
        raise ValueError("Sub-agent parameters must be a JSON object.")

    full_prompt = f"Task: '{task_prompt}'. Parameters: {parsed_params}"
    result = run_agent_turn(subagent_id, full_prompt)
    return json.dumps(
        {"subagent_id": subagent_id, "result": result}, ensure_ascii=False, indent=2
    )


@tool(provider="agentMemory")
def write_agent_scratchpad(
    subagent_id: str = "subagent",
    task_type: str = "general",
    status: str = "success",
    payload: str = "",
) -> str:
    """Write structured sub-agent execution payloads into the shared scratchpad."""
    from orchestration.code_handoffs import TASK_TYPE_BY_AGENT
    from orchestration.codebuilder_run_state import codebuilder_run_state
    from orchestration.orchestration_telemetry import telemetry_bus

    trace_context = telemetry_bus.current_context()
    active_agent_id = ""
    if trace_context is not None:
        trace_id, active_agent_id = trace_context
        if active_agent_id in TASK_TYPE_BY_AGENT:
            subagent_id = active_agent_id
            task_type = TASK_TYPE_BY_AGENT[active_agent_id]

    parsed_payload = payload
    if isinstance(parsed_payload, str) and parsed_payload.strip().startswith(("[", "{")):
        try:
            parsed_payload = json.loads(parsed_payload)
        except Exception:
            pass

    result = interface.store_subagent_result(
        subagent_id=subagent_id,
        task_type=task_type,
        status=status,
        payload=parsed_payload,
    )

    if trace_context is not None:
        codebuilder_run_state.save_handoff(
            trace_id,
            subagent_id,
            task_type,
            status,
            parsed_payload,
        )
    return json.dumps(result, ensure_ascii=False, indent=2)


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
