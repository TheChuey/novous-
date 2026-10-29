"""Atomic, single-file scratchpad shared by the coding agents and the code squad.

The RAG agents keep their own scratchpad in ``scratchpad.py``; this board only
holds coding work: plans, applied code, test results, fixes, and agent notes.
"""

import json
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data"
CODE_SCRATCHPAD_PATH = DATA_DIR / "code_scratchpad.json"
MAX_ENTRIES = 200
MAX_CONTENT_CHARS = 20_000
KINDS = {"plan", "code", "test", "fix", "summary", "note"}
_LOCK = threading.RLock()


def _path() -> Path:
    return CODE_SCRATCHPAD_PATH


def _read() -> list[dict[str, Any]]:
    path = _path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read code scratchpad '{path}': {exc}") from exc
    entries = data.get("entries") if isinstance(data, dict) else None
    return entries if isinstance(entries, list) else []


def _write(entries: list[dict[str, Any]]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=".code_scratchpad.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump({"entries": entries}, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
        temp_path.replace(path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def post(author: str, kind: str, title: str, content: str, run_id: str = "") -> dict[str, Any]:
    """Append one entry, keeping only the newest ``MAX_ENTRIES``."""
    if kind not in KINDS:
        raise ValueError("Scratchpad kind must be one of: " + ", ".join(sorted(KINDS)))
    text = str(content or "")
    entry = {
        "id": uuid.uuid4().hex[:12],
        "run_id": str(run_id or ""),
        "author": str(author or "unknown"),
        "kind": kind,
        "title": str(title or "")[:200],
        "content": text[:MAX_CONTENT_CHARS],
        "truncated": len(text) > MAX_CONTENT_CHARS,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        entries = _read()
        entries.append(entry)
        _write(entries[-MAX_ENTRIES:])
    return entry


def entries(limit: int = 50, kind: str = "", author: str = "", run_id: str = "") -> list[dict[str, Any]]:
    """Return matching entries, newest first."""
    with _LOCK:
        items = _read()
    matched = [
        entry
        for entry in reversed(items)
        if (not kind or entry.get("kind") == kind)
        and (not author or entry.get("author") == author)
        and (not run_id or entry.get("run_id") == run_id)
    ]
    return matched[: max(0, int(limit))]


def latest(kind: str) -> dict[str, Any] | None:
    found = entries(limit=1, kind=kind)
    return found[0] if found else None


def count() -> int:
    with _LOCK:
        return len(_read())


def clear() -> dict[str, Any]:
    with _LOCK:
        _write([])
    return {"cleared": True, "path": "agentMemory/data/code_scratchpad.json"}
