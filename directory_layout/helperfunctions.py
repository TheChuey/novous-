"""directory_layout/helperfunctions.py

Pure, stateless supporting utilities.

Component: Multi-Root Security & Path Boundaries.

The single allowed intra-component edge is ``helperfunctions -> data``
(constants); nothing imports helperfunctions back, so the component
stays acyclic. Every function here is stateless and side-effect free.
"""

from __future__ import annotations

from pathlib import Path

from .data import (
    BROWSE_ROOTS,
    IGNORED_DIRECTORIES,
    MAX_EDITABLE_BYTES,
    TEXT_EXTENSIONS,
)


def normalize_slashes(relative_path: str) -> str:
    """Normalize Windows separators to forward slashes."""

    return relative_path.replace("\\", "/")


def split_root(
    relative_path: str,
) -> tuple[str | None, str]:
    """
    Split a path into its browser-root name and the remainder.

    Returns:
        ``(root_name, remainder)``. ``root_name`` is None when the
        first segment is not a known root, meaning the caller
        should treat the path as legacy and root-relative.
    """

    normalized = normalize_slashes(relative_path).strip()

    head, separator, tail = normalized.partition("/")

    if not separator:
        return None, normalized

    if head in BROWSE_ROOTS:
        return head, tail

    return None, normalized


def is_writable_root(
    root_name: str | None,
) -> bool:
    """
    Whether a browser root accepts writes.

    Legacy (root-less) paths are treated as writable so existing
    callers keep working.
    """

    if root_name is None:
        return True

    return bool(BROWSE_ROOTS[root_name].get("writable", False))


def should_ignore(path: Path) -> bool:
    """
    Determine whether a path should be hidden
    from the project browser.
    """

    return any(part in IGNORED_DIRECTORIES for part in path.parts)


def is_text_file(path: Path) -> bool:
    """
    Determine whether a file should be editable.

    Files without extensions are treated as text files.
    """

    if path.suffix == "":
        return True

    return path.suffix.lower() in TEXT_EXTENSIONS


def is_oversized(path: Path) -> bool:
    """
    Determine whether a file is too large to edit in the browser.

    Very large files are marked non-editable so the editor does
    not try to render a multi-megabyte document.
    """

    try:
        return path.stat().st_size > MAX_EDITABLE_BYTES
    except OSError:
        return False
