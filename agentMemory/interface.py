"""The public doorway to agent scratchpad memory and the document knowledge base."""

import math
import os
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


def store_subagent_result(
    subagent_id: str, task_type: str, status: str, payload: Any
) -> dict[str, Any]:
    """Store a sub-agent execution result in the shared agent scratchpad."""
    return scratchpad.store_subagent_result(subagent_id, task_type, status, payload)


def read_memory(memory_type: str = "all") -> dict[str, Any]:
    """Read scratchpad memory, including the latest sub-agent result."""
    return scratchpad.read_memory(memory_type)


def list_documents(base_id: str | None = None) -> list[dict[str, Any]]:
    """List documents currently indexed in the SQLite knowledge base."""
    with rag_config.database_context(base_id):
        rag_database.initialize()
        return rag_database.list_documents()


def get_document(path: str, base_id: str | None = None) -> dict[str, Any]:
    """Read the indexed chunks for one document."""
    with rag_config.database_context(base_id):
        rag_database.initialize()
        metadata = next((item for item in rag_database.list_documents() if item["path"] == path), None)
        if metadata is None:
            raise FileNotFoundError(f"Knowledge-base document is not indexed: {path}")
        metadata["chunks_data"] = rag_database.get_document_chunks(path)
        return metadata


def index_document(relative_path: str, force: bool = False) -> dict:
    """Index one file inside the Knowledge Base folder."""
    base_id = rag_config.selected_knowledge_base_id()
    root = indexer.knowledge_base_folder(base_id)
    requested_path = root / relative_path
    if requested_path.is_symlink():
        raise ValueError("Symbolic links cannot be indexed.")
    candidate = requested_path.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        raise ValueError("Document path must stay inside the Knowledge Base folder.") from None
    with rag_config.database_context(base_id):
        return indexer.index_file(candidate, force=force)


def get_rag_status(base_id: str | None = None) -> dict[str, Any]:
    """Describe the selected or specified folder and its isolated index."""
    selected_id = base_id or rag_config.selected_knowledge_base_id()
    with rag_config.database_context(selected_id):
        rag_database.initialize()
        folder = indexer.knowledge_base_folder(selected_id)
        documents = rag_database.list_documents()
    base = rag_config.get_knowledge_base(selected_id)
    return {
        "base_id": base["id"],
        "name": base["name"],
        "path": str(folder),
        "configured_path": str(base["path"]),
        "exists": folder.is_dir(),
        "documents": len(documents),
        "chunks": sum(item["chunks"] for item in documents),
    }


def get_rag_overview(base_id: str | None = None) -> dict[str, Any]:
    """Status plus every indexed document with its type, for the Chat Console dialog."""
    status = get_rag_status(base_id)
    documents = []
    types: dict[str, int] = {}
    for item in list_documents(base_id):
        manual = item["path"].startswith(indexer.MANUAL_PREFIX)
        kind = "manual" if manual else (Path(item["path"]).suffix.lower().lstrip(".") or "none")
        types[kind] = types.get(kind, 0) + 1
        documents.append({**item, "type": kind, "name": item["path"] if manual else Path(item["path"]).name})
    return {**status, "types": types, "files": documents}


def add_text_document(title: str, text: str, base_id: str | None = None) -> dict:
    """Embed pasted text into the vector database."""
    with indexer._SCAN_LOCK:
        with rag_config.database_context(base_id):
            return indexer.index_text(title, text)


def set_rag_folder(path: str) -> dict[str, Any]:
    """Change the selected named source folder."""
    rag_config.set_knowledge_base_path(path)
    return get_rag_status()


def list_rag_bases() -> list[dict[str, Any]]:
    bases = rag_config.list_knowledge_bases()
    for base in bases:
        base["exists"] = Path(base["path"]).is_dir()
        with rag_config.database_context(str(base["id"])):
            rag_database.initialize()
            documents = rag_database.list_documents()
        base["documents"] = len(documents)
        base["chunks"] = sum(item["chunks"] for item in documents)
    return bases


def open_rag_base_folder(base_id: str) -> dict[str, Any]:
    """Open a saved knowledge-source folder in the local Windows file manager."""
    path = rag_config.knowledge_base_path(base_id)
    if not path.is_dir():
        raise FileNotFoundError(f"Knowledge-source folder is unavailable: {path}")
    if os.name != "nt":
        raise RuntimeError("Opening knowledge-source folders is supported only on Windows.")
    os.startfile(str(path))
    return {"opened": True, "path": str(path)}


def add_rag_base(name: str, path: str) -> dict[str, Any]:
    base = rag_config.add_knowledge_base(name, path)
    return {**base, **get_rag_status(str(base["id"]))}


def rename_rag_base(base_id: str, name: str) -> dict[str, Any]:
    return rag_config.rename_knowledge_base(base_id, name)


def delete_rag_base(base_id: str) -> dict[str, Any]:
    job = indexer.get_scan_job()
    if job.get("base_id") == base_id and job.get("status") in {
        "paused", "awaiting_decision"
    }:
        indexer.stop_scan_job()
        worker = indexer._JOB_THREAD
        if worker and worker.is_alive():
            worker.join()

    with indexer._SCAN_LOCK:
        job = indexer.get_scan_job()
        if job.get("base_id") == base_id and job.get("status") in {
            "queued", "running", "pausing", "paused", "stopping", "awaiting_decision"
        }:
            raise RuntimeError("Stop or finish indexing before deleting this knowledge source.")

        rag_config.get_knowledge_base(base_id)
        database_file = rag_config.database_path(base_id)
        legacy_database_file = rag_database.DATABASE_PATH if database_file is None else None
        if legacy_database_file and any(
            str(other["id"]) != str(base_id) and other.get("legacy_index")
            for other in rag_config.list_knowledge_bases()
        ):
            raise RuntimeError(
                "This legacy index is shared by another source and cannot be deleted independently."
            )
        with rag_config.database_context(base_id):
            rag_database.initialize()
            documents = rag_database.list_documents()
            if database_file is None:
                rag_database.clear_all()

        deleted = rag_config.delete_knowledge_base(base_id)
        indexer._update_job(
            stopped_base_ids=[
                stopped_id
                for stopped_id in indexer.get_scan_job().get("stopped_base_ids", [])
                if stopped_id != base_id
            ]
        )
        index_file = database_file or legacy_database_file
        if index_file is not None:
            for suffix in ("", "-wal", "-shm"):
                Path(f"{index_file}{suffix}").unlink(missing_ok=True)
            try:
                index_file.parent.rmdir()
            except OSError:
                pass
        return {
            "deleted": True,
            "id": deleted["id"],
            "name": deleted["name"],
            "documents_removed": len(documents),
            "folder_deleted": False,
        }


def select_rag_base(base_id: str) -> dict[str, Any]:
    rag_config.select_knowledge_base(base_id)
    return get_rag_status(base_id)


def archive_rag_base(base_id: str) -> dict[str, Any]:
    job = indexer.get_scan_job()
    if job.get("base_id") == base_id and (
        job.get("status") in {"queued", "running", "pausing", "stopping", "awaiting_decision"}
        or (job.get("status") == "paused" and job.get("resume_at"))
    ):
        raise RuntimeError("Pause or finish indexing and clear its scheduled resume before archiving.")
    return rag_config.archive_knowledge_base(base_id)


def restore_rag_base(base_id: str) -> dict[str, Any]:
    base = rag_config.restore_knowledge_base(base_id)
    return {**base, **get_rag_status(base_id)}


def get_rag_scan_job() -> dict[str, Any]:
    job = indexer.get_scan_job()
    if job.get("base_id"):
        try:
            job["base_name"] = rag_config.get_knowledge_base(job["base_id"])["name"]
        except ValueError:
            job["base_name"] = "Unknown knowledge base"
    return job


def start_rag_scan(base_id: str | None = None, force: bool = False) -> dict[str, Any]:
    return indexer.start_scan_job(base_id, force=force)


def pause_rag_scan() -> dict[str, Any]:
    return indexer.pause_scan_job()


def stop_rag_scan() -> dict[str, Any]:
    return indexer.stop_scan_job()


def resume_rag_scan() -> dict[str, Any]:
    return indexer.resume_scan_job()


def schedule_rag_scan_resume(resume_at: str) -> dict[str, Any]:
    return indexer.schedule_scan_resume(resume_at)


def clear_rag_index(base_id: str | None = None) -> dict[str, Any]:
    """Delete all indexed RAG data; source files are untouched."""
    with indexer._SCAN_LOCK:
        with rag_config.database_context(base_id):
            rag_database.initialize()
            removed = rag_database.clear_all()
    return {"removed": removed, **get_rag_status(base_id)}


def delete_document(path: str, base_id: str | None = None) -> dict[str, Any]:
    """Remove one indexed document and its chunks."""
    with rag_config.database_context(base_id):
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
    base_id: str | None = None,
) -> dict[str, Any]:
    """Return semantically relevant document passages and their source paths."""
    clean_query = str(query or "").strip()
    if not clean_query:
        raise ValueError("A search query is required.")
    if isinstance(top_k, bool) or not 1 <= int(top_k) <= 20:
        raise ValueError("top_k must be between 1 and 20.")

    selected_id = base_id or rag_config.selected_knowledge_base_id()
    base = rag_config.get_knowledge_base(selected_id)
    with rag_config.database_context(selected_id):
        rag_database.initialize()
        chunks = rag_database.list_chunks()
    selected_path = ""
    if relative_path.strip():
        from editor.editor_operations import resolve_project_path

        source_path = resolve_project_path(relative_path)
        if not source_path.is_file():
            raise FileNotFoundError(f"Knowledge-base document not found: {source_path}")
        selected_path = source_path.resolve().as_posix()
        with rag_config.database_context(selected_id):
            indexer.index_file(source_path, selected_path)
            chunks = rag_database.list_chunks()
    if selected_path:
        chunks = [chunk for chunk in chunks if chunk["path"] == selected_path]
    if not chunks:
        return {
            "query": clean_query,
            "knowledge_base": base["name"],
            "knowledge_base_id": selected_id,
            "results": [],
            "message": (
                "No documents are indexed yet. Place supported files in "
                f"'{indexer.knowledge_base_folder(selected_id)}' and wait for the automatic scan."
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

    compatible_chunks = [
        chunk for chunk in chunks if len(chunk["embedding"]) == len(query_vector)
    ]
    skipped_chunks = len(chunks) - len(compatible_chunks)
    if not compatible_chunks:
        raise RuntimeError(
            "No indexed chunks have embeddings compatible with the query embedding "
            f"({len(query_vector)} dimensions). Reindex this knowledge base."
        )

    ranked = [
        {
            "path": chunk["path"],
            "chunk_index": chunk["chunk_index"],
            "score": _cosine_similarity(query_vector, chunk["embedding"]),
            "content": chunk["content"],
        }
        for chunk in compatible_chunks
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query": clean_query,
        "knowledge_base": base["name"],
        "knowledge_base_id": selected_id,
        "model": indexer.EMBEDDING_MODEL,
        "skipped_incompatible_chunks": skipped_chunks,
        "results": ranked[:int(top_k)],
    }


def start_document_scanner() -> bool:
    """Start automatic indexing of the workspace Knowledge Base folder."""
    return indexer.start_scanner()
