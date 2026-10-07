"""directory_layout/interface.py

Public doorway. The sole import surface for outside callers; exposes
public functions and the FastAPI router.

Component: Multi-Root Security & Path Boundaries (the root authority).

Other components import *only* this file for root resolution, path
security, scope normalization, tree reading and the /api/path router.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .code import (
    read_browse_filesystem,
    read_filesystem,
    require_writable,
    resolve_browse_path,
    resolve_browse_target,
    resolve_project_path,
)
from .data import (
    BROWSE_ROOTS,
    IGNORED_DIRECTORIES,
    MAX_EDITABLE_BYTES,
    PROJECT_ROOT,
    REPO_ROOT,
    SOURCE_FILES_ROOT,
    TEXT_EXTENSIONS,
    TEST_ENVIRONMENT_ROOT,
    VALID_SCOPES,
)
from .helperfunctions import is_oversized, is_text_file, should_ignore
from .logic import is_valid_scope, resolve_request_target, root_for

__all__ = [
    "BROWSE_ROOTS",
    "IGNORED_DIRECTORIES",
    "MAX_EDITABLE_BYTES",
    "PROJECT_ROOT",
    "REPO_ROOT",
    "SOURCE_FILES_ROOT",
    "TEST_ENVIRONMENT_ROOT",
    "TEXT_EXTENSIONS",
    "VALID_SCOPES",
    "is_oversized",
    "is_text_file",
    "is_valid_scope",
    "normalize_roots",
    "normalize_scope",
    "read_browse_filesystem",
    "read_filesystem",
    "require_writable",
    "resolve_browse_path",
    "resolve_browse_target",
    "resolve_project_path",
    "resolve_request_target",
    "root_for",
    "router",
    "should_ignore",
]


# ============================================================
# SCOPE HANDLING
# ============================================================

def normalize_scope(scope: str | None) -> str | None:
    """
    Validate and normalize a scope query parameter.

    Returns None when the parameter is absent, which selects the
    browser view (paths may carry a browser-root prefix). An
    explicit scope keeps the legacy single-root behaviour.

    Raises:
        HTTPException (422):
            If the scope is not a known scope.
    """

    if scope is None:
        return None

    if scope not in VALID_SCOPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown scope: {scope}",
        )

    return scope


def normalize_roots(
    roots: str | None,
) -> list[str] | None:
    """
    Validate and normalize the ``roots`` query parameter.

    A comma-separated list of browser-root names. Empty entries are
    dropped and order is preserved; None means "no filter", which is
    the whole browser tree.

    Raises:
        HTTPException (422):
            If a name is not a configured browser root. An unknown
            root is refused rather than dropped, because a typo
            that returned a smaller tree would read as a page that
            legitimately has less in it.
    """

    if roots is None:
        return None

    names = [
        name.strip() for name in roots.split(",") if name.strip()
    ]

    if not names:
        return None

    for name in names:
        if name not in BROWSE_ROOTS:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown browser root: {name}",
            )

    return names


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


class RenameRequest(BaseModel):

    old_path: str
    new_path: str
    scope: str | None = None


@router.put("/api/path/rename")
def rename_path(
    request: Request,
    payload: RenameRequest,
):
    """
    Rename or move a project file/directory.
    """

    # Imported inside the handler: project_manager's doorway imports
    # this component's doorway, so a module-level import here would
    # create an import cycle.
    from project_manager.interface import project_manager_error

    try:
        return request.app.state.editor.rename(
            payload.old_path,
            payload.new_path,
            scope=normalize_scope(payload.scope),
        )
    except Exception as error:
        raise project_manager_error(error)
