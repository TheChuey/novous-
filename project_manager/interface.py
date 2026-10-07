"""project_manager/interface.py

Public doorway. The sole import surface for outside callers; exposes
public functions and the FastAPI router.

Component: Project Sessions, Filesystem Operations & Event Stream.

Other components import *only* this file for the editor controller,
filesystem mutations, sessions/events state, the bridge clients and
the /api/health, /api/project, /api/sessions, /api/file/*,
/api/directory/* and /api/ws endpoints.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from directory_layout.interface import normalize_roots, normalize_scope

from .code import (
    AsyncEditorClient,
    AsyncProjectManagerBridge,
    DirectProjectIO,
    EditorClient,
    EditorInterface,
    EditorManager,
    EditorSession,
    EventBus,
    ProjectManagerBridge,
    create_directory,
    create_file,
    delete_path,
    read_file,
    remove_tree,
    remove_tree_manual,
    rename_path,
    write_file,
)
from .logic import (
    get_events,
    get_interface,
    get_sessions,
    reset_for_tests,
)

__all__ = [
    "AsyncEditorClient",
    "AsyncProjectManagerBridge",
    "DirectProjectIO",
    "EditorClient",
    "EditorInterface",
    "EditorManager",
    "EditorSession",
    "EventBus",
    "FileCreateRequest",
    "FileWriteRequest",
    "ProjectManagerBridge",
    "create_directory",
    "create_file",
    "delete_path",
    "get_events",
    "get_interface",
    "get_sessions",
    "normalize_roots",
    "normalize_scope",
    "project_manager_error",
    "read_file",
    "remove_tree",
    "remove_tree_manual",
    "rename_path",
    "reset_for_tests",
    "router",
    "write_file",
]


# ============================================================
# SHARED ERROR MAPPING
# ============================================================

def project_manager_error(
    error: Exception,
) -> HTTPException:
    """
    Convert a Project Manager operation error into an HTTP error.

    This is the single translator for the HTTP API. Routers do
    not implement their own status-code logic.
    """

    if isinstance(
        error,
        HTTPException,
    ):

        return error

    if isinstance(
        error,
        FileNotFoundError,
    ):

        return HTTPException(
            status_code=404,
            detail=str(error),
        )

    if isinstance(
        error,
        FileExistsError,
    ):

        return HTTPException(
            status_code=409,
            detail=str(error),
        )

    if isinstance(
        error,
        ValueError,
    ):

        return HTTPException(
            status_code=400,
            detail=str(error),
        )

    # --------------------------------------------------------
    # WebSocket-disconnect / client errors
    # --------------------------------------------------------

    if isinstance(
        error,
        KeyError,
    ):

        return HTTPException(
            status_code=404,
            detail=str(error),
        )

    return HTTPException(
        status_code=500,
        detail=str(error),
    )


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class FileWriteRequest(BaseModel):

    path: str

    content: str

    scope: str | None = None


class FileCreateRequest(BaseModel):

    path: str

    content: str = ""

    scope: str | None = None


# ============================================================
# HEALTH
# ============================================================

@router.get("/api/health")
def health(
    request: Request,
):
    """
    Project Manager health and project information.
    """

    try:

        return request.app.state.editor.health()

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# PROJECT STATE
# ============================================================

@router.get("/api/project")
def get_project(
    request: Request,
    scope: str | None = None,
    roots: str | None = None,
):
    """
    Project information and filesystem tree.

    Query params:
        scope:
            Omit for the browser tree, whose top level is the
            configured browser roots. ``"workspace"`` or ``"app"``
            return the legacy single-root tree.
        roots:
            Comma-separated browser roots to include in the browser
            tree, e.g. ``?roots=test_environment``. Omit for all of
            them. This decides what a page is shown, not what it may
            read or write: an omitted root still resolves for file
            operations.
    """

    try:

        return request.app.state.editor.tree(
            scope=normalize_scope(scope),
            roots=normalize_roots(roots),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# SESSIONS
# ============================================================

@router.get("/api/sessions")
def get_sessions_endpoint(
    request: Request,
):
    """
    Active interface sessions.
    """

    try:

        return request.app.state.editor.sessions()

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# READ FILE
# ============================================================

@router.get("/api/file/read")
def read_file_endpoint(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Read a project text file.

    Query params:
        path:
            Browser-root-qualified or root-relative file path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        content = request.app.state.editor.open(
            path,
            scope=normalize_scope(scope),
        )
        return {
            "path": path,
            "content": content,
            "scope": scope,
        }

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# WRITE FILE
# ============================================================

@router.put("/api/file/write")
def write_file_endpoint(
    request: Request,
    payload: FileWriteRequest,
):
    """
    Create or overwrite a project text file.
    """

    try:

        return request.app.state.editor.save(
            payload.path,
            payload.content,
            scope=normalize_scope(payload.scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# CREATE FILE
# ============================================================

@router.post("/api/file/create")
def create_file_endpoint(
    request: Request,
    payload: FileCreateRequest,
):
    """
    Create a new project file.
    """

    try:

        return request.app.state.editor.create_file(
            payload.path,
            payload.content,
            scope=normalize_scope(payload.scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# DELETE FILE
# ============================================================

@router.delete("/api/file/delete")
def delete_file_endpoint(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Delete a project file.

    Query params:
        path:
            Browser-root-qualified or root-relative file path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        return request.app.state.editor.delete(
            path,
            scope=normalize_scope(scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# CREATE DIRECTORY
# ============================================================

@router.post("/api/directory/create")
def create_directory_endpoint(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Create a project directory.

    Query params:
        path:
            Browser-root-qualified or root-relative directory path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        return request.app.state.editor.create_directory(
            path,
            scope=normalize_scope(scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# DELETE DIRECTORY
# ============================================================

@router.delete("/api/directory/delete")
def delete_directory_endpoint(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Delete a project directory.

    Query params:
        path:
            Browser-root-qualified or root-relative directory path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        return request.app.state.editor.delete(
            path,
            scope=normalize_scope(scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# WEBSOCKET
# ============================================================

@router.websocket("/api/ws")
async def project_manager_socket(
    websocket: WebSocket,
) -> None:
    """
    Real-time Project Manager socket.

    Client -> Server (JSON messages):

        {"type": "open",        "path": "src/app.py"}
        {"type": "dirty",       "dirty": true}
        {"type": "subscribe",   "events": ["saved", "created"]}

    Server -> Client (JSON messages):

        {"type": "hello",        "client_id": "..."}
        {"type": "event",        "event": {publish payload}}
        {"type": "sessions",     "sessions": [...]}
    """

    await websocket.accept()

    controller = websocket.app.state.editor

    loop = asyncio.get_running_loop()

    session = controller.session_manager.register()

    try:

        await websocket.send_json(
            {
                "type": "hello",
                "client_id": session.client_id,
            }
        )

        def forward(
            event: dict[str, Any],
        ) -> None:
            """
            Forward a published event to this socket.

            ``EventBus.publish`` is called synchronously, and it can run on a
            worker thread (sync ``def`` endpoints run in the threadpool where
            there is no running event loop). We therefore capture the socket's
            loop up front and use ``loop.call_soon_threadsafe`` to hop back
            onto that loop before creating the send task -- a plain
            ``asyncio.create_task`` / ``get_running_loop`` here would raise
            ``RuntimeError`` on a worker thread and silently drop the event.
            """

            async def _send() -> None:

                try:

                    await websocket.send_json(
                        {
                            "type": "event",
                            "event": event,
                        }
                    )

                except Exception:

                    pass

            def _schedule() -> None:

                try:

                    loop.create_task(
                        _send()
                    )

                except Exception:

                    pass

            try:

                loop.call_soon_threadsafe(
                    _schedule
                )

            except Exception:

                pass

        subscription_id = controller.events.subscribe(
            forward,
        )

        async def _send_sessions() -> None:

            await websocket.send_json(
                {
                    "type": "sessions",
                    "sessions": controller.session_manager.snapshot(),
                }
            )

        await _send_sessions()

        while True:

            raw = await websocket.receive_text()

            try:

                message = json.loads(raw)

            except json.JSONDecodeError:

                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "Message was not valid JSON.",
                    }
                )

                continue

            message_type = message.get(
                "type"
            )

            if message_type == "open":

                controller.session_manager.update(
                    session.client_id,
                    open_file=message.get(
                        "path"
                    ),
                )

                await websocket.send_json(
                    {
                        "type": "hello",
                        "client_id": session.client_id,
                        "open_file": message.get(
                            "path"
                        ),
                    }
                )

            elif message_type == "dirty":

                controller.session_manager.update(
                    session.client_id,
                    dirty=bool(
                        message.get(
                            "dirty",
                            False,
                        )
                    ),
                )

            elif message_type == "sessions":

                await _send_sessions()

            else:

                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "Unknown message type: "
                        + str(message_type),
                    }
                )

    except WebSocketDisconnect:

        pass

    except Exception:

        pass

    finally:

        try:

            controller.events.unsubscribe(
                subscription_id  # type: ignore[possibly-undefined]
            )

        except Exception:

            pass

        controller.session_manager.unregister(
            session.client_id
        )
