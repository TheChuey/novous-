"""tools/helperfunctions.py

Pure utility functions. No side effects, no component imports except
this component's data constants.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .data import PLAIN_TEXT_EXTENSIONS

__all__ = [
    "_flatten_tree",
    "_iso_ts",
    "_is_plain_text",
    "_unquote_path",
]


def _iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_plain_text(path) -> bool:
    """True for files whose raw text is already the well-formatted content."""
    return Path(str(path)).suffix.lower() in PLAIN_TEXT_EXTENSIONS


def _unquote_path(value) -> str:
    """Strip one level of surrounding quotes a model may have left on a path.

    Small local models frequently emit tool args that still include the
    double/single quotes from the prompt (e.g. output_path='"E:\\data\\x"').
    Quote characters are invalid inside Windows path components, so passing
    them through makes read/map/write/delete fail with WinError 123 - even
    though the underlying path was perfectly real. Only matching quote pairs
    at the very edges are stripped, and only for string arguments that are
    really paths, so ordinary quoted prose is never mangled.
    """
    v = str(value).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    return v


def _flatten_tree(entries: list, prefix: str = "") -> list[dict]:
    """Flatten a nested provider tree into one flat list of {path, type, name, size}."""
    flat = []
    for entry in entries or []:
        name = entry.get("name", "")
        rel = entry.get("path", "")
        if not rel and name:
            rel = f"{prefix}/{name}" if prefix else name
        flat.append({
            "name": name or Path(rel).name,
            "path": rel,
            "type": entry.get("type", "file"),
        })
        for child in entry.get("children") or []:
            flat.extend(_flatten_tree([child], prefix=rel))
    return flat
