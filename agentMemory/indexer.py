"""Document discovery, parsing, chunking, and local Ollama embedding generation."""

import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import ollama

from agentMemory import rag_config, rag_database


LOGGER = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
LEGACY_PREFIX = "workspace/Knowledge Base"
ROOT_META_KEY = "knowledge_root"
MANUAL_PREFIX = "manual:"
EMBEDDING_MODEL = os.environ.get("NOVOUS_EMBEDDING_MODEL", "nomic-embed-text:latest")
MAX_DOCUMENT_BYTES = 100_000_000
CHUNK_CHARACTERS = 1400
CHUNK_OVERLAP = 200
EMBEDDING_BATCH_SIZE = 16
SCAN_INTERVAL_SECONDS = 60
TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst", ".html", ".htm", ".csv",
    ".json", ".xml", ".yaml", ".yml", ".log",
    ".py", ".js", ".ts", ".css", ".toml", ".ini", ".sql", ".sh", ".ps1",
}
DOCLING_EXTENSIONS = {".pdf", ".docx", ".pptx", ".odt"}
_SCANNER_LOCK = threading.Lock()
_SCAN_LOCK = threading.RLock()
_SCANNER_THREAD: threading.Thread | None = None
_STOP_SCANNER = threading.Event()
_DOC_CONVERTER = None


def _document_text(path: Path) -> str:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in DOCLING_EXTENSIONS:
        global _DOC_CONVERTER
        if _DOC_CONVERTER is None:
            try:
                from docling.document_converter import DocumentConverter
            except ImportError as exc:
                raise RuntimeError(
                    "Docling is required to index PDF, DOCX, PPTX, and ODT files."
                ) from exc
            _DOC_CONVERTER = DocumentConverter()
        result = _DOC_CONVERTER.convert(str(path))
        return result.document.export_to_markdown()
    raise ValueError(f"Unsupported knowledge-base file type: {path.suffix or '(no extension)'}")


def _chunk_text(text: str) -> list[str]:
    clean = text.strip()
    if not clean:
        return []
    chunks = []
    start = 0
    while start < len(clean):
        end = min(start + CHUNK_CHARACTERS, len(clean))
        if end < len(clean):
            boundary = clean.rfind("\n\n", start, end)
            if boundary > start + CHUNK_CHARACTERS // 2:
                end = boundary
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    return chunks


def _embed(texts: list[str]) -> list[list[float]]:
    vectors = []
    for offset in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        response = ollama.embed(model=EMBEDDING_MODEL, input=texts[offset:offset + EMBEDDING_BATCH_SIZE])
        batch = response.get("embeddings") if isinstance(response, dict) else response.embeddings
        if len(batch) != len(texts[offset:offset + EMBEDDING_BATCH_SIZE]):
            raise RuntimeError("Embedding model returned a different number of vectors than requested.")
        vectors.extend([[float(value) for value in vector] for vector in batch])
    if vectors and any(len(vector) != len(vectors[0]) for vector in vectors):
        raise RuntimeError("Embedding model returned vectors with inconsistent dimensions.")
    return vectors


def index_file(path: Path, relative_path: str | None = None, force: bool = False) -> dict:
    """Extract, embed, and persist one supported document."""
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Knowledge-base document not found: {resolved}")
    stat = resolved.stat()
    if stat.st_size > MAX_DOCUMENT_BYTES:
        raise ValueError(f"Document exceeds the {MAX_DOCUMENT_BYTES}-byte indexing limit: {resolved}")
    path_key = relative_path or resolved.as_posix()
    existing = rag_database.document_metadata(path_key)
    if not force and existing and (
        existing["modified_ns"] == stat.st_mtime_ns and existing["size_bytes"] == stat.st_size
    ):
        return {"path": path_key, "status": "unchanged", "chunks": 0}

    chunks = _chunk_text(_document_text(resolved))
    embeddings = _embed(chunks)
    rag_database.replace_document(
        path_key,
        stat.st_mtime_ns,
        stat.st_size,
        datetime.now(timezone.utc).isoformat(),
        zip(chunks, embeddings),
    )
    return {"path": path_key, "status": "indexed", "chunks": len(chunks)}


def index_text(title: str, text: str) -> dict:
    """Embed and store pasted text under a manual:<title> key, replacing any entry with that title."""
    clean_title = " ".join(str(title or "").split())
    if not clean_title:
        raise ValueError("A title is required.")
    chunks = _chunk_text(str(text or ""))
    if not chunks:
        raise ValueError("Text is required.")
    path_key = f"{MANUAL_PREFIX}{clean_title}"
    embeddings = _embed(chunks)
    rag_database.initialize()
    rag_database.replace_document(
        path_key,
        0,
        len(text.encode("utf-8")),
        datetime.now(timezone.utc).isoformat(),
        zip(chunks, embeddings),
    )
    return {"path": path_key, "status": "indexed", "chunks": len(chunks)}


def knowledge_base_folder() -> Path:
    """The currently configured Knowledge Base folder."""
    return rag_config.knowledge_base_path()


def _purge_previous_folder(root: Path) -> list[str]:
    """Remove documents indexed from a different folder than the current one."""
    root_key = root.as_posix()
    previous = rag_database.get_meta(ROOT_META_KEY)
    removed: list[str] = []
    if previous != root_key:
        if previous:
            removed += rag_database.delete_documents_under(previous, set())
        removed += rag_database.delete_documents_under(LEGACY_PREFIX, set())
        rag_database.set_meta(ROOT_META_KEY, root_key)
    return removed


def scan_knowledge_base(force: bool = False) -> dict:
    """Index supported files in the configured folder and remove stale records."""
    with _SCAN_LOCK:
        return _scan_knowledge_base(force)


def _scan_knowledge_base(force: bool) -> dict:
    root = knowledge_base_folder()
    if root == rag_config.DEFAULT_KNOWLEDGE_BASE:
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise FileNotFoundError(f"The RAG folder does not exist: {root}")
    rag_database.initialize()
    removed = _purge_previous_folder(root)
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink() or any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS | DOCLING_EXTENSIONS:
            continue
        files.append(path)

    results = []
    for path in files:
        key = path.resolve().as_posix()
        try:
            results.append(index_file(path, key, force=force))
        except Exception as exc:
            LOGGER.exception("Could not index knowledge-base document %s", path)
            results.append({"path": key, "status": "error", "error": str(exc)})

    keep = {path.resolve().as_posix() for path in files}
    stale = rag_database.delete_documents_under(root.as_posix(), keep)
    return {
        "folder": str(root),
        "discovered": len(files),
        "indexed": sum(result["status"] == "indexed" for result in results),
        "unchanged": sum(result["status"] == "unchanged" for result in results),
        "errors": [result for result in results if result["status"] == "error"],
        "removed": removed + stale,
    }


def _scanner_loop() -> None:
    while not _STOP_SCANNER.is_set():
        try:
            result = scan_knowledge_base()
            if result["errors"]:
                LOGGER.warning("Knowledge-base scan completed with %d errors.", len(result["errors"]))
        except Exception:
            LOGGER.exception("Knowledge-base scan failed.")
        _STOP_SCANNER.wait(SCAN_INTERVAL_SECONDS)


def start_scanner() -> bool:
    """Start one background scan loop; performs a scan immediately."""
    global _SCANNER_THREAD
    with _SCANNER_LOCK:
        if _SCANNER_THREAD and _SCANNER_THREAD.is_alive():
            return False
        _STOP_SCANNER.clear()
        _SCANNER_THREAD = threading.Thread(
            target=_scanner_loop,
            name="agent-memory-document-indexer",
            daemon=True,
        )
        _SCANNER_THREAD.start()
    return True


def stop_scanner() -> None:
    _STOP_SCANNER.set()


def refresh_index(force: bool = False) -> dict:
    """Synchronously scan the knowledge-base folder and return indexing results."""
    return scan_knowledge_base(force=force)
