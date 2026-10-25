"""Document discovery, parsing, chunking, and local Ollama embedding generation."""

import json
import logging
import os
import tempfile
import threading
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
SCAN_FILE_DELAY_SECONDS = max(
    0.0, float(os.environ.get("NOVOUS_RAG_SCAN_DELAY_SECONDS", "0.15"))
)
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
_JOB_PATH = Path(__file__).resolve().parent / "data" / "rag_scan_job.json"
_JOB_LOCK = threading.RLock()
_JOB_THREAD: threading.Thread | None = None
_PAUSE_REQUESTED = threading.Event()
_RESUME_EVENT = threading.Event()
_RESUME_EVENT.set()
_ERROR_DECISION_EVENT = threading.Event()
_ERROR_DECISION = None
try:
    _SCAN_JOB = json.loads(_JOB_PATH.read_text(encoding="utf-8"))
    if _SCAN_JOB.get("status") in {"running", "awaiting_decision"}:
        _SCAN_JOB["status"] = "paused"
except (OSError, json.JSONDecodeError, AttributeError):
    _SCAN_JOB = {"status": "idle"}


def _save_job() -> None:
    _JOB_PATH.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=_JOB_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(_SCAN_JOB, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, _JOB_PATH)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def get_scan_job() -> dict:
    with _JOB_LOCK:
        return dict(_SCAN_JOB)


def _update_job(**changes) -> None:
    with _JOB_LOCK:
        _SCAN_JOB.update(changes)
        _save_job()


def _pause_point() -> None:
    if _PAUSE_REQUESTED.is_set():
        _update_job(status="paused", current="")
        _RESUME_EVENT.wait()
        _PAUSE_REQUESTED.clear()
        _update_job(status="running")


def decide_scan_error(decision: str) -> dict:
    """Apply the user's choice for a document that failed during indexing."""
    global _ERROR_DECISION
    if decision not in {"retry", "skip", "skip_all"}:
        raise ValueError("Choose retry, skip, or skip_all.")
    with _JOB_LOCK:
        if _SCAN_JOB.get("status") != "awaiting_decision":
            raise ValueError("There is no indexing error waiting for a decision.")
        if decision == "skip_all":
            _SCAN_JOB["error_mode"] = "skip_all"
        _ERROR_DECISION = decision
        _SCAN_JOB["status"] = "running"
        _ERROR_DECISION_EVENT.set()
        _save_job()
        return dict(_SCAN_JOB)


def _await_error_decision(path: Path, error: Exception) -> str:
    global _ERROR_DECISION
    with _JOB_LOCK:
        if _SCAN_JOB.get("error_mode") == "skip_all":
            return "skip"
        _ERROR_DECISION = None
        _ERROR_DECISION_EVENT.clear()
        _SCAN_JOB.update(
            status="awaiting_decision",
            current="",
            pending_error={"path": str(path), "error": str(error)},
        )
        _save_job()
    _ERROR_DECISION_EVENT.wait()
    with _JOB_LOCK:
        decision = _ERROR_DECISION
        _ERROR_DECISION = None
        _SCAN_JOB.pop("pending_error", None)
        _save_job()
    return decision or "skip"


def _run_scan_job(base_id: str, force: bool) -> None:
    global _JOB_THREAD
    try:
        _update_job(
            base_id=base_id,
            status="running",
            current="",
            discovered=0,
            completed=0,
            indexed=0,
            unchanged=0,
            errors=[],
            skipped=[],
            pending_error=None,
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=None,
        )

        def update_progress(**changes):
            _update_job(**changes)

        result = scan_knowledge_base(
            force=force,
            base_id=base_id,
            progress=update_progress,
            pause_point=_pause_point,
            error_decider=_await_error_decision,
        )
        status = (
            "completed_with_errors" if result["errors"]
            else "completed_with_skips" if result.get("skipped")
            else "completed"
        )
        _update_job(
            status=status,
            current="",
            removed=result["removed"],
            errors=result["errors"],
            skipped=result.get("skipped", []),
            pending_error=None,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except FileNotFoundError as exc:
        LOGGER.warning("Knowledge-base scan skipped: %s", exc)
        _update_job(
            status="unavailable",
            current="",
            errors=[{"error": str(exc)}],
            pending_error=None,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        LOGGER.exception("Knowledge-base scan failed.")
        _update_job(
            status="failed",
            current="",
            errors=[{"error": str(exc)}],
            pending_error=None,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        _JOB_THREAD = None


def start_scan_job(
    base_id: str | None = None,
    force: bool = False,
    resume_paused: bool = False,
) -> dict:
    """Start or resume a persistent background scan for a knowledge base."""
    global _JOB_THREAD
    selected_id = base_id or rag_config.selected_knowledge_base_id()
    if not rag_config.get_knowledge_base(selected_id).get("active", True):
        raise ValueError("Restore the archived knowledge base before indexing it.")
    root = knowledge_base_folder(selected_id)
    if not root.is_dir():
        message = f"The RAG folder does not exist: {root}"
        _update_job(
            base_id=selected_id,
            status="unavailable",
            current="",
            errors=[{"error": message}],
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        raise FileNotFoundError(message)
    with _JOB_LOCK:
        if _JOB_THREAD and _JOB_THREAD.is_alive():
            if _SCAN_JOB.get("base_id") != selected_id:
                raise RuntimeError("Another knowledge-base scan is already running.")
            return dict(_SCAN_JOB)
        if _SCAN_JOB.get("status") == "paused":
            if _SCAN_JOB.get("base_id") != selected_id:
                raise RuntimeError("Resume or finish the paused knowledge-base scan first.")
            if not resume_paused:
                return dict(_SCAN_JOB)
        _PAUSE_REQUESTED.clear()
        _RESUME_EVENT.set()
        _SCAN_JOB["resume_at"] = None
        error_mode = (
            _SCAN_JOB.get("error_mode", "ask")
            if resume_paused
            else "ask"
        )
        _ERROR_DECISION_EVENT.clear()
        _JOB_THREAD = threading.Thread(
            target=_run_scan_job,
            args=(selected_id, force),
            name="agent-memory-rag-scan",
            daemon=True,
        )
        _SCAN_JOB.update(status="queued", base_id=selected_id, error_mode=error_mode)
        _save_job()
        _JOB_THREAD.start()
        return dict(_SCAN_JOB)


def pause_scan_job() -> dict:
    with _JOB_LOCK:
        if _SCAN_JOB.get("status") not in {"running", "queued"}:
            return dict(_SCAN_JOB)
        _PAUSE_REQUESTED.set()
        _RESUME_EVENT.clear()
        _SCAN_JOB["status"] = "pausing"
        _save_job()
        return dict(_SCAN_JOB)


def resume_scan_job() -> dict:
    with _JOB_LOCK:
        base_id = _SCAN_JOB.get("base_id") or rag_config.selected_knowledge_base_id()
        if not rag_config.get_knowledge_base(base_id).get("active", True):
            raise RuntimeError("Restore the archived knowledge base before resuming indexing.")
        if _SCAN_JOB.get("status") == "paused" and _JOB_THREAD and _JOB_THREAD.is_alive():
            _PAUSE_REQUESTED.clear()
            _RESUME_EVENT.set()
            _SCAN_JOB["status"] = "running"
            _SCAN_JOB["resume_at"] = None
            _save_job()
            return dict(_SCAN_JOB)
    return start_scan_job(base_id, resume_paused=True)


def schedule_scan_resume(resume_at: str) -> dict:
    try:
        scheduled = datetime.fromisoformat(resume_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("A valid scheduled resume time is required.") from exc
    if scheduled.tzinfo is None:
        raise ValueError("The scheduled resume time must include a timezone.")
    scheduled = scheduled.astimezone(timezone.utc)
    if scheduled <= datetime.now(timezone.utc):
        raise ValueError("The scheduled resume time must be in the future.")
    with _JOB_LOCK:
        if _SCAN_JOB.get("status") != "paused":
            raise ValueError("Pause indexing before scheduling its resume.")
        _SCAN_JOB["resume_at"] = scheduled.isoformat()
        _save_job()
        return dict(_SCAN_JOB)


def _document_text(path: Path) -> str:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in DOCLING_EXTENSIONS:
        global _DOC_CONVERTER
        if _DOC_CONVERTER is None:
            try:
                from docling.document_converter import DocumentConverter
            except ImportError as exc:
                if path.suffix.lower() == ".pdf":
                    return _pdf_text_fallback(path, exc)
                raise RuntimeError(
                    "Docling is required to index PDF, DOCX, PPTX, and ODT files."
                ) from exc
            _DOC_CONVERTER = DocumentConverter()
        try:
            result = _DOC_CONVERTER.convert(str(path))
        except ImportError as exc:
            if path.suffix.lower() == ".pdf":
                return _pdf_text_fallback(path, exc)
            raise
        return result.document.export_to_markdown()
    raise ValueError(f"Unsupported knowledge-base file type: {path.suffix or '(no extension)'}")


def _pdf_text_fallback(path: Path, docling_error: ImportError) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "Docling's PDF parser could not load and the PyMuPDF fallback is unavailable."
        ) from exc

    LOGGER.warning("Docling PDF parser unavailable; using PyMuPDF for %s: %s", path, docling_error)
    with fitz.open(path) as document:
        text = "\n\n".join(page.get_text("text") for page in document)
    if not text.strip():
        raise RuntimeError(
            f"No selectable text could be extracted from {path}; scanned PDFs require a working OCR parser."
        )
    return text


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


def knowledge_base_folder(base_id: str | None = None) -> Path:
    """The selected or specified Knowledge Base folder."""
    return rag_config.knowledge_base_path(base_id)


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


def scan_knowledge_base(
    force: bool = False,
    base_id: str | None = None,
    progress=None,
    pause_point=None,
    error_decider=None,
) -> dict:
    """Index supported files in one knowledge base and remove stale records."""
    with _SCAN_LOCK:
        with rag_config.database_context(base_id):
            return _scan_knowledge_base(
                force, base_id, progress, pause_point, error_decider
            )


def _scan_knowledge_base(
    force: bool, base_id: str | None, progress, pause_point, error_decider=None
) -> dict:
    root = knowledge_base_folder(base_id)
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
    skipped = []
    if progress:
        progress(discovered=len(files), current="")
    for index, path in enumerate(files, start=1):
        if pause_point:
            pause_point()
        if progress:
            progress(current=str(path), completed=index - 1)
        key = path.resolve().as_posix()
        while True:
            try:
                results.append(index_file(path, key, force=force))
                break
            except Exception as exc:
                LOGGER.exception("Could not index knowledge-base document %s", path)
                decision = error_decider(path, exc) if error_decider else "error"
                if decision == "retry":
                    continue
                failed = {"path": key, "status": "error", "error": str(exc)}
                if decision in {"skip", "skip_all"}:
                    skipped.append({**failed, "status": "skipped"})
                    results.append({"path": key, "status": "skipped"})
                else:
                    results.append(failed)
                break
        if progress:
            result = results[-1]
            progress(
                completed=index,
                indexed=sum(item["status"] == "indexed" for item in results),
                unchanged=sum(item["status"] == "unchanged" for item in results),
                errors=[item for item in results if item["status"] == "error"],
                skipped=skipped,
                current="",
            )
        if SCAN_FILE_DELAY_SECONDS:
            _STOP_SCANNER.wait(SCAN_FILE_DELAY_SECONDS)

    if pause_point:
        pause_point()
    keep = {path.resolve().as_posix() for path in files}
    stale = rag_database.delete_documents_under(root.as_posix(), keep)
    return {
        "folder": str(root),
        "discovered": len(files),
        "indexed": sum(result["status"] == "indexed" for result in results),
        "unchanged": sum(result["status"] == "unchanged" for result in results),
        "errors": [result for result in results if result["status"] == "error"],
        "skipped": skipped,
        "removed": removed + stale,
    }


def _scanner_loop() -> None:
    while not _STOP_SCANNER.is_set():
        try:
            job = get_scan_job()
            if job.get("status") == "paused" and job.get("resume_at"):
                try:
                    resume_at = datetime.fromisoformat(job["resume_at"].replace("Z", "+00:00"))
                    if resume_at <= datetime.now(timezone.utc):
                        resume_scan_job()
                except ValueError:
                    LOGGER.warning("Ignoring invalid scheduled RAG resume time: %s", job["resume_at"])
            elif job.get("status") not in {"running", "queued", "pausing", "paused"}:
                bases = rag_config.list_knowledge_bases(include_archived=False)
                base_ids = [str(base["id"]) for base in bases]
                if base_ids:
                    last_id = job.get("last_auto_base_id")
                    if last_id in base_ids:
                        next_index = (base_ids.index(last_id) + 1) % len(base_ids)
                        next_id = base_ids[next_index]
                    else:
                        next_id = rag_config.selected_knowledge_base_id()
                        if next_id not in base_ids:
                            next_id = base_ids[0]
                    _update_job(last_auto_base_id=next_id)
                    start_scan_job(next_id)
        except FileNotFoundError as exc:
            LOGGER.warning(
                "Knowledge-base folder is unavailable; skipping this scan: %s. "
                "Check the configured path or reconnect the drive. The scanner will retry in %d seconds.",
                exc,
                SCAN_INTERVAL_SECONDS,
            )
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
