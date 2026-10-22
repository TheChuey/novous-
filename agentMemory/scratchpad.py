"""Atomic, single-file storage for the latest agent memory snapshots."""

import json
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data"
SCRATCHPAD_PATH = DATA_DIR / "scratchpad.json"
MAX_READ_HISTORY = 20
_LOCK = threading.RLock()


def _read() -> dict[str, Any]:
    if not SCRATCHPAD_PATH.is_file():
        return {}
    try:
        data = json.loads(SCRATCHPAD_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read agent scratchpad '{SCRATCHPAD_PATH}': {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Agent scratchpad must contain a JSON object: {SCRATCHPAD_PATH}")
    return data


def _write(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=DATA_DIR,
            prefix=".scratchpad.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
        temp_path.replace(SCRATCHPAD_PATH)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def store_read(path: str, content: str, request: str = "") -> dict[str, Any]:
    """Store the latest read and retain a bounded history of prior reads."""
    entry = {
        "path": path,
        "request": request,
        "content": content,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        data = _read()
        history = data.get("read_history")
        if not isinstance(history, list):
            history = []
            previous = data.get("latest_read")
            if isinstance(previous, dict):
                history.append(previous)
        history.append(entry)
        data["read_history"] = history[-MAX_READ_HISTORY:]
        data["latest_read"] = entry
        _write(data)
    return {"path": "agentMemory/data/scratchpad.json", "updated_at": entry["updated_at"]}


def store_map(tree: dict[str, Any], requested_path: str = "") -> dict[str, Any]:
    """Store the latest workspace tree snapshot."""
    entry = {
        "requested_path": requested_path,
        "tree": tree,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        data = _read()
        data["latest_map"] = entry
        _write(data)
    return {"path": "agentMemory/data/scratchpad.json", "updated_at": entry["updated_at"]}


def read_memory(memory_type: str = "all") -> dict[str, Any]:
    """Read all, the latest file read, or the latest map snapshot."""
    if memory_type not in {"all", "latest_read", "latest_map"}:
        raise ValueError("memory_type must be 'all', 'latest_read', or 'latest_map'.")
    with _LOCK:
        data = _read()
    if memory_type == "all":
        return data
    return {memory_type: data[memory_type]} if memory_type in data else {}


def clear_memory() -> dict[str, Any]:
    """Clear saved reads and maps while retaining the scratchpad file."""
    with _LOCK:
        _write({})
    return {"cleared": True, "path": "agentMemory/data/scratchpad.json"}
