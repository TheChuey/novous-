"""Configurable location of the RAG Knowledge Base folder."""

import json
import os
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "rag_config.json"
DEFAULT_KNOWLEDGE_BASE = REPOSITORY_ROOT / "workspace" / "Knowledge Base"


def _read_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def configured_path() -> str:
    """The raw configured value, or an empty string when the default is used."""
    return str(_read_config().get("knowledge_base_path") or "").strip()


def knowledge_base_path() -> Path:
    """The folder to index; falls back to the workspace default when unset."""
    raw = configured_path()
    if not raw:
        return DEFAULT_KNOWLEDGE_BASE
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    return path.resolve()


def set_knowledge_base_path(raw_path: str) -> Path:
    """Validate and persist a folder path. An empty value restores the default."""
    raw = str(raw_path or "").strip().strip('"')
    if not raw:
        _write_config({})
        return DEFAULT_KNOWLEDGE_BASE
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ValueError("The RAG folder path must be absolute.")
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"The RAG folder does not exist or is not a directory: {path}")
    _write_config({"knowledge_base_path": str(path)})
    return path


def _write_config(data: dict) -> None:
    descriptor, temp_name = tempfile.mkstemp(dir=CONFIG_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, CONFIG_PATH)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise
