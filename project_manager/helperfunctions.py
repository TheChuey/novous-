"""project_manager/helperfunctions.py

Pure utility functions. No imports from sibling components
(except data constants), no side effects.

Shared path helpers for the bridge clients plus the transient-delete
classifier used by remove_tree.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .data import (
    TRANSIENT_DELETE_ERRNOS,
    TRANSIENT_DELETE_WIN_ERRORS,
)

__all__ = [
    "_apply_project_root",
    "_decode_message",
    "_default_base_url",
    "_normalize",
    "_raise_for_error",
    "_relpath",
    "is_transient_delete_error",
]


# ============================================================
# TRANSIENT DELETE CLASSIFIER
# ============================================================

def is_transient_delete_error(
    error: OSError,
) -> bool:
    """
    Whether a delete failure is worth retrying.

    Args:
        error:
            The failure raised by the delete attempt.

    Returns:
        True when the failure means "the tree has not settled yet".
    """

    win_error = getattr(
        error,
        "winerror",
        None,
    )

    if win_error is not None:

        return (
            win_error
            in TRANSIENT_DELETE_WIN_ERRORS
        )

    return (
        error.errno
        in TRANSIENT_DELETE_ERRNOS
    )


# ============================================================
# BRIDGE CLIENT HELPERS
# ============================================================

def _default_base_url() -> str:
    """
    Best-effort default: localhost on the standard Project Manager port.
    """

    return os.environ.get(
        "PROJECT_MANAGER_BASE_URL",
        "http://127.0.0.1:8000",
    )


def _apply_project_root(
    path: str,
    project_root: str = "",
) -> str:
    """
    Normalize a project-relative path into the API path form.
    """

    path = path.replace("\\", "/").strip("/")

    return path


def _raise_for_error(
    response: Any,
) -> None:
    """
    Turn a non-2xx response into a useful Python error.
    """

    if response.is_success:
        return

    detail = ""

    try:

        detail = response.json().get(
            "detail",
            "",
        )

    except Exception:
        pass

    message = detail or f"Project Manager error (HTTP {response.status_code})."

    raise RuntimeError(
        message
    )


def _decode_message(message: Any) -> dict[str, Any]:
    """
    Turn a raw WebSocket message into a dict (bytes or str payload).
    """

    if isinstance(message, bytes):
        return json.loads(
            message.decode(
                "utf-8"
            )
        )

    try:

        return json.loads(
            message
        )

    except Exception:

        return {
            "type": "message",
            "data": message,
        }


# ============================================================
# PATH HELPERS (shared by both clients)
# ============================================================

def _normalize(raw: str) -> str:
    return str(raw).replace("\\", "/").strip("/")


def _relpath(root: Path, path: str) -> str:
    """Translate an absolute-or-relative path into a posix relative path that
    stays inside the Project Manager workspace root. The root itself maps to
    "". Raises ValueError when the path would escape the root."""
    raw = str(path).strip()
    if not raw:
        return ""
    if raw in (".", "/", "\\"):
        return ""

    root = root.resolve()

    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve()
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            raise ValueError(
                f"Path '{raw}' is outside the Project Manager workspace root "
                f"({root})."
            )
        return "" if rel == Path(".") else rel.as_posix()

    joined = (root / _normalize(raw)).resolve()
    try:
        rel = joined.relative_to(root)
    except ValueError:
        raise ValueError(
            f"Path '{raw}' is outside the Project Manager workspace root "
            f"({root})."
        )
    as_posix = rel.as_posix()
    return "" if as_posix == "." else as_posix
