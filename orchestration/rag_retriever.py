"""Deterministic RAG retrieval worker and scratchpad handoff."""

import json

from agentMemory import interface, rag_config


RAG_RETRIEVER_ID = "rag-retriever"
RAG_RELEVANCE_THRESHOLD = 0.25


def run_rag_retriever(task_prompt: str, parameters: dict) -> str:
    query = str(task_prompt or "").strip()
    payload = {"query": query, "knowledge_branch_id": "", "results": []}
    status = "error"
    try:
        if not isinstance(parameters, dict):
            raise ValueError("Sub-agent parameters must be a JSON object.")
        if not query:
            raise ValueError("A retrieval query is required.")
        branch_id = str(
            parameters.get("knowledge_branch_id")
            or rag_config.selected_knowledge_base_id()
        )
        top_k = int(parameters.get("top_k", 5))
        result = interface.search_knowledge_base(query, top_k, base_id=branch_id)
        payload = {
            "query": query,
            "knowledge_branch_id": result["knowledge_base_id"],
            "knowledge_branch_name": result["knowledge_base"],
            "results": [
                item for item in result["results"]
                if float(item["score"]) >= RAG_RELEVANCE_THRESHOLD
            ],
            "skipped_incompatible_chunks": result.get(
                "skipped_incompatible_chunks", 0
            ),
        }
        status = "success" if payload["results"] else "nothing_found"
    except Exception as exc:
        payload["error"] = f"{type(exc).__name__}: {exc}"

    interface.store_subagent_result(
        subagent_id=RAG_RETRIEVER_ID,
        task_type="rag_retrieval",
        status=status,
        payload=payload,
    )
    return json.dumps(
        {
            "subagent_id": RAG_RETRIEVER_ID,
            "status": status,
            "payload": payload,
        },
        ensure_ascii=False,
        indent=2,
    )
