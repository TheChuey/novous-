"""The public doorway to agent scratchpad memory and the document knowledge base."""

import math
from pathlib import Path
from typing import Any

import ollama

from agentMemory import indexer, rag_config, rag_database, scratchpad


def store_read(path: str, content: str, request: str = "") -> dict[str, str]:
    """Save a file read in the shared agent scratchpad."""
    return scratchpad.store_read(path, content, request)


def store_map(tree: dict[str, Any], requested_path: str = "") -> dict[str, str]:
    """Save the latest file structure map in the shared agent scratchpad."""
    return scratchpad.store_map(tree, requested_path)


def read_memory(memory_type: str = "all") -> dict[str, Any]:
    """Read the latest file read and/or file structure map."""
    return scratchpad.read_memory(memory_type)


def list_documents() -> list[dict[str, Any]]:
    """List documents currently indexed in the SQLite knowledge base."""
    rag_database.initialize()
    return rag_database.list_documents()


def get_document(path: str) -> dict[str, Any]:
    """Read the indexed chunks for one document."""
    rag_database.initialize()
    metadata = next((item for item in rag_database.list_documents() if item["path"] == path), None)
    if metadata is None:
        raise FileNotFoundError(f"Knowledge-base document is not indexed: {path}")
    metadata["chunks_data"] = rag_database.get_document_chunks(path)
    return metadata


def index_document(relative_path: str, force: bool = False) -> dict:
    """Index one file inside the Knowledge Base folder."""
    root = indexer.knowledge_base_folder()
    requested_path = root / relative_path
    if requested_path.is_symlink():
        raise ValueError("Symbolic links cannot be indexed.")
    candidate = requested_path.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        raise ValueError("Document path must stay inside the Knowledge Base folder.") from None
    return indexer.index_file(candidate, force=force)


def get_rag_status() -> dict[str, Any]:
    """Describe the configured folder and what is currently indexed."""
    rag_database.initialize()
    folder = indexer.knowledge_base_folder()
    documents = rag_database.list_documents()
    return {
        "path": str(folder),
        "configured_path": rag_config.configured_path(),
        "default_path": str(rag_config.DEFAULT_KNOWLEDGE_BASE),
        "exists": folder.is_dir(),
        "documents": len(documents),
        "chunks": sum(item["chunks"] for item in documents),
    }


def get_rag_overview() -> dict[str, Any]:
    """Status plus every indexed document with its type, for the Chat Console dialog."""
    status = get_rag_status()
    documents = []
    types: dict[str, int] = {}
    for item in rag_database.list_documents():
        manual = item["path"].startswith(indexer.MANUAL_PREFIX)
        kind = "manual" if manual else (Path(item["path"]).suffix.lower().lstrip(".") or "none")
        types[kind] = types.get(kind, 0) + 1
        documents.append({**item, "type": kind, "name": item["path"] if manual else Path(item["path"]).name})
    return {**status, "types": types, "files": documents}


def add_text_document(title: str, text: str) -> dict:
    """Embed pasted text into the vector database."""
    with indexer._SCAN_LOCK:
        return indexer.index_text(title, text)


def set_rag_folder(path: str) -> dict[str, Any]:
    """Point the Knowledge Base at a folder; empty restores the default."""
    rag_config.set_knowledge_base_path(path)
    return get_rag_status()


def clear_rag_index() -> dict[str, Any]:
    """Delete all indexed RAG data; source files are untouched."""
    with indexer._SCAN_LOCK:
        rag_database.initialize()
        removed = rag_database.clear_all()
    return {"removed": removed, **get_rag_status()}


def delete_document(path: str) -> dict[str, Any]:
    """Remove one indexed document and its chunks."""
    rag_database.initialize()
    if not rag_database.delete_document(path):
        raise FileNotFoundError(f"Knowledge-base document is not indexed: {path}")
    return {"deleted": True, "path": path}


def refresh_knowledge_base(force: bool = False) -> dict:
    """Scan Knowledge Base and index additions or changes."""
    return indexer.refresh_index(force=force)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise RuntimeError("Query and document embedding dimensions do not match.")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def search_knowledge_base(
    query: str,
    top_k: int = 5,
    relative_path: str = "",
) -> dict[str, Any]:
    """Return semantically relevant document passages and their source paths."""
    clean_query = str(query or "").strip()
    if not clean_query:
        raise ValueError("A search query is required.")
    if isinstance(top_k, bool) or not 1 <= int(top_k) <= 20:
        raise ValueError("top_k must be between 1 and 20.")

    rag_database.initialize()
    selected_path = ""
    if relative_path.strip():
        from editor.editor_operations import resolve_project_path

        source_path = resolve_project_path(relative_path)
        if not source_path.is_file():
            raise FileNotFoundError(f"Knowledge-base document not found: {source_path}")
        selected_path = source_path.resolve().as_posix()
        indexer.index_file(source_path, selected_path)

    chunks = rag_database.list_chunks()
    if selected_path:
        chunks = [chunk for chunk in chunks if chunk["path"] == selected_path]
    if not chunks:
        return {
            "query": clean_query,
            "results": [],
            "message": (
                "No documents are indexed yet. Place supported files in "
                f"'{indexer.knowledge_base_folder()}' and wait for the automatic scan."
            ),
        }

    try:
        response = ollama.embed(model=indexer.EMBEDDING_MODEL, input=clean_query)
    except Exception as exc:
        raise RuntimeError(
            f"Could not create a query embedding with '{indexer.EMBEDDING_MODEL}': {exc}"
        ) from exc
    vectors = response.get("embeddings") if isinstance(response, dict) else response.embeddings
    if not vectors:
        raise RuntimeError(f"Embedding model '{indexer.EMBEDDING_MODEL}' returned no query vector.")
    query_vector = [float(value) for value in vectors[0]]

    ranked = [
        {
            "path": chunk["path"],
            "chunk_index": chunk["chunk_index"],
            "score": _cosine_similarity(query_vector, chunk["embedding"]),
            "content": chunk["content"],
        }
        for chunk in chunks
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query": clean_query,
        "model": indexer.EMBEDDING_MODEL,
        "results": ranked[:int(top_k)],
    }


def start_document_scanner() -> bool:
    """Start automatic indexing of the workspace Knowledge Base folder."""
    return indexer.start_scanner()
