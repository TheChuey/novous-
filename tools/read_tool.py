"""Verb-oriented file reading backed by the shared tools interface.

The tools interface delegates to file_manager_service, the single access
boundary: every path is validated against allowed_paths.json and constrained
to the active file-manager root.
The latest read is mirrored into the workspace scratchpad so downstream
tools (edit/write) can reference or modify it without re-reading the source.
"""

import json

from core_engine.tool_catalog import tool
from tools import interface

MAX_READ_SIZE_BYTES = 1_000_000  # ~1 MB. Raise or lower this cap here.
SCRATCHPAD_PATH = "scratchpad/latest_read.txt"
_UTF8 = "utf-8"


def _split_relative(path: str) -> tuple[str, str]:
    clean = path.replace("\\", "/").strip("/")
    if "/" not in clean:
        return "", clean
    parent, name = clean.rsplit("/", 1)
    return parent, name


def _listed_size(path: str) -> int | None:
    parent, name = _split_relative(path)
    try:
        entries = interface.list_directory(parent)["entries"]
    except Exception:
        return None
    for entry in entries:
        if entry["name"] == name:
            return int(entry.get("size") or 0)
    return None


def _size_guard(path: str, size_bytes: int) -> None:
    if size_bytes > MAX_READ_SIZE_BYTES:
        raise ValueError(
            f"Refusing to read '{path}': {size_bytes} bytes exceeds MAX_READ_SIZE_BYTES "
            f"({MAX_READ_SIZE_BYTES}). Adjust MAX_READ_SIZE_BYTES at the top of "
            f"tools/read_tool.py to raise the cap."
        )


def _copy_to_scratchpad(content: str) -> str | None:
    try:
        result = interface.write_file(SCRATCHPAD_PATH, content)
        return str(result.get("path", SCRATCHPAD_PATH))
    except Exception:
        return None


@tool(provider="tools")
def read_file(path: str, request: str = "") -> str:
    """Read a UTF-8 text file from the workspace by relative path; bare filenames go in the root.

    The raw content is mirrored to scratchpad/latest_read.txt, so later edit/write calls can
    target the scratchpad instead of the original path. Files larger than MAX_READ_SIZE_BYTES
    (~1 MB) are rejected; see tools/read_tool.py to adjust the limit.
    Returns JSON with the request echo, resolved path, raw content, and scratchpad context.
    """
    if not path or not path.strip():
        raise ValueError("A file path is required.")

    listed = _listed_size(path)
    if listed is not None:
        _size_guard(path, listed)

    try:
        result = interface.read_file(path)
    except Exception as exc:
        raise RuntimeError(f"Could not read '{path}': {exc}") from exc

    content = result["content"]
    size_bytes = len(content.encode(_UTF8))
    if listed is None:
        _size_guard(path, size_bytes)

    scratchpad_path = _copy_to_scratchpad(content)
    payload = {
        "request": request,
        "path": result["path"],
        "size_bytes": size_bytes,
        "content": content,
        "scratchpad": {
            "path": scratchpad_path,
            "context": (
                "Latest read mirrored here; point edit/write tools at this path to modify it."
                if scratchpad_path
                else "Scratchpad copy failed; the content in this payload is the only copy."
            ),
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
