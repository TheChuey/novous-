"""project_manager/code.py

Core classes & active execution.

The Project Manager filesystem authority (text-file mutations), the
shared editor state (EventBus, sessions, EditorInterface) and the
bridge clients that reach a running Project Manager server.

    Router / Client
        ↓
    EditorInterface
        ↓
    directory_layout (path security & tree reading)
    workspace_manager (project info)
        ↓
    Filesystem
"""

from __future__ import annotations

import os
import shutil
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, AsyncIterator, Callable

import httpx
from websockets.asyncio.client import connect as ws_connect

from directory_layout.interface import (
    BROWSE_ROOTS,
    PROJECT_ROOT,
    REPO_ROOT,
    is_text_file,
    read_browse_filesystem,
    read_filesystem,
    require_writable,
    resolve_project_path,
    resolve_request_target as _target,
    root_for as _root_for,
)
from workspace_manager.interface import read_project_info

from .data import DELETE_ATTEMPTS, DELETE_BACKOFF
from .helperfunctions import (
    _apply_project_root,
    _decode_message,
    _default_base_url,
    _raise_for_error,
    _relpath,
    is_transient_delete_error,
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
    "ProjectManagerBridge",
    "create_directory",
    "create_file",
    "delete_path",
    "read_file",
    "remove_tree",
    "remove_tree_manual",
    "rename_path",
    "write_file",
]


# ============================================================
# READ FILE
# ============================================================

def read_file(
    relative_path: str,
    root: Path | None = None,
) -> str:
    """
    Read a text file.

    Args:
        relative_path:
            Project-relative file path.
        root:
            Filesystem root. Defaults to the managed workspace.

    Returns:
        File contents.

    Raises:
        ValueError:
            Invalid path or file type.
        FileNotFoundError:
            File does not exist.
    """

    file_path = resolve_project_path(
        relative_path,
        root,
    )

    if not file_path.exists():

        raise FileNotFoundError(
            "File not found."
        )

    if not file_path.is_file():

        raise ValueError(
            "Path is not a file."
        )

    if not is_text_file(file_path):

        raise ValueError(
            "This file type is not editable."
        )

    try:

        return file_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        raise ValueError(
            "File is not a UTF-8 text file."
        )


# ============================================================
# WRITE FILE
# ============================================================

def write_file(
    relative_path: str,
    content: str,
    root: Path | None = None,
) -> None:
    """
    Create or overwrite a text file.

    Parent directories are automatically created.
    """

    file_path = resolve_project_path(
        relative_path,
        root,
    )

    if not is_text_file(file_path):

        raise ValueError(
            "This file type cannot be edited."
        )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        content,
        encoding="utf-8",
    )


# ============================================================
# CREATE FILE
# ============================================================

def create_file(
    relative_path: str,
    content: str = "",
    root: Path | None = None,
) -> None:
    """
    Create a new file.

    Refuses to overwrite an existing file.
    """

    file_path = resolve_project_path(
        relative_path,
        root,
    )

    if file_path.exists():

        raise FileExistsError(
            "A file or directory with that "
            "name already exists."
        )

    if not is_text_file(file_path):

        raise ValueError(
            "This file type cannot be created "
            "by the text editor."
        )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        content,
        encoding="utf-8",
    )


# ============================================================
# CREATE DIRECTORY
# ============================================================

def create_directory(
    relative_path: str,
    root: Path | None = None,
) -> None:
    """
    Create a directory.
    """

    directory = resolve_project_path(
        relative_path,
        root,
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# RENAME
# ============================================================

def rename_path(
    old_path: str,
    new_path: str,
    root: Path | None = None,
) -> None:
    """
    Rename or move a file/directory within the active root.

    Both paths must remain inside the active root.
    """

    source = resolve_project_path(
        old_path,
        root,
    )

    destination = resolve_project_path(
        new_path,
        root,
    )

    if not source.exists():

        raise FileNotFoundError(
            "The source path does not exist."
        )

    if destination.exists():

        raise FileExistsError(
            "The destination already exists."
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source.rename(
        destination
    )


# ============================================================
# DELETE
# ============================================================

def delete_path(
    relative_path: str,
    root: Path | None = None,
) -> None:
    """
    Delete a file or directory.

    Directories are deleted recursively through
    :func:`remove_tree`, which tolerates a tree that is still
    settling instead of leaving it half-deleted.

    The active root itself cannot be deleted.
    """

    target = resolve_project_path(
        relative_path,
        root,
    )

    if target == root or target == PROJECT_ROOT:

        raise ValueError(
            "The project root cannot be deleted."
        )

    if not target.exists():

        raise FileNotFoundError(
            "Path not found."
        )

    if target.is_dir():

        remove_tree(target)

    else:

        target.unlink()


# ============================================================
# RECURSIVE DELETE
# ============================================================

def remove_tree_manual(
    target: Path,
) -> None:
    """
    Remove a directory tree bottom-up.

    The last resort for :func:`remove_tree`: ``shutil.rmtree`` has
    already failed, so every entry is unlinked individually and each
    directory is then removed empty. Entries that vanished on their own
    are ignored, since a retry race means the work is already done.

    Raises:
        OSError:
            If an entry survives.
    """

    for parent, directories, files in os.walk(
        target,
        topdown=False,
    ):

        for name in files:

            child = Path(parent) / name

            try:

                # A read-only attribute is the usual reason unlink is
                # refused, and clearing it is harmless.
                os.chmod(child, 0o666)

            except OSError:
                pass

            try:

                child.unlink()

            except FileNotFoundError:
                pass

        for name in directories:

            try:

                (Path(parent) / name).rmdir()

            except FileNotFoundError:
                pass

    target.rmdir()


def remove_tree(
    target: Path,
) -> None:
    """
    Delete a directory tree, surviving a tree that is still settling.

    A bare ``shutil.rmtree`` is not enough: on a filesystem without
    transactional deletes (exFAT, for instance) it can fail partway
    with "directory not empty" and leave the tree half-deleted, which
    is how a folder ends up listed but permanently inaccessible. So the
    tree is removed with retries first, then bottom-up by hand, and the
    original error is only reported if entries genuinely survive.

    Args:
        target:
            The directory to remove.

    Raises:
        OSError:
            If the tree could not be fully removed.
    """

    last_error: OSError | None = None

    for attempt in range(DELETE_ATTEMPTS):

        try:

            shutil.rmtree(target)
            return

        except FileNotFoundError:
            return

        except OSError as error:

            if not is_transient_delete_error(error):
                raise

            last_error = error

            if attempt + 1 < DELETE_ATTEMPTS:
                time.sleep(
                    DELETE_BACKOFF * (attempt + 1)
                )

    remove_tree_manual(target)

    if target.exists():

        raise last_error


# ============================================================
# DEFAULT FILESYSTEM NAMESPACE
# ============================================================
#
# The sovereign authority EditorInterface and DirectProjectIO drive:
# directory_layout owns path security and tree reading, workspace_manager
# owns project info, and the mutation functions above live here.

_filesystem = SimpleNamespace(
    PROJECT_ROOT=PROJECT_ROOT,
    REPO_ROOT=REPO_ROOT,
    BROWSE_ROOTS=BROWSE_ROOTS,
    read_project_info=read_project_info,
    read_filesystem=read_filesystem,
    read_browse_filesystem=read_browse_filesystem,
    read_file=read_file,
    write_file=write_file,
    create_file=create_file,
    create_directory=create_directory,
    rename_path=rename_path,
    delete_path=delete_path,
    require_writable=require_writable,
)


# ============================================================
# EVENT BUS
# ============================================================

class EventBus:
    """
    Simple in-memory publish/subscribe event bus.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, Callable[[dict[str, Any]], None]] = {}

    def subscribe(
        self,
        callback: Callable[[dict[str, Any]], None],
    ) -> str:
        """
        Subscribe a callback to every project event.

        Args:
            callback:
                Function called with each published event dict.

        Returns:
            Subscription id (use with unsubscribe()).
        """

        subscription_id = uuid.uuid4().hex

        self._subscribers[subscription_id] = callback

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> None:
        """
        Remove a subscription.
        """

        self._subscribers.pop(subscription_id, None)

    def publish(
        self,
        event_type: str,
        path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type:
                One of EVENT_TYPES.
            path:
                Optional project-relative path the event refers to.
            kwargs:
                Extra fields merged into the event payload.
        """

        event: dict[str, Any] = {
            "type": event_type,
        }

        if path is not None:
            event["path"] = path

        event.update(kwargs)

        for callback in list(self._subscribers.values()):
            callback(event)


# ============================================================
# EDITOR SESSION
# ============================================================

class EditorSession:
    """
    State for a single connected interface client.
    """

    def __init__(
        self,
        client_id: str | None = None,
    ) -> None:
        self.client_id = client_id or uuid.uuid4().hex
        self.open_file: str | None = None
        self.dirty: bool = False
        self.last_modified: float | None = None

    def snapshot(self) -> dict[str, Any]:
        """
        JSON-friendly copy of this session.
        """

        return {
            "client_id": self.client_id,
            "open_file": self.open_file,
            "dirty": self.dirty,
            "last_modified": self.last_modified,
        }

    def touch(self) -> None:
        """
        Update the last-modified timestamp.
        """

        self.last_modified = time.time()


# ============================================================
# EDITOR MANAGER
# ============================================================

class EditorManager:
    """
    Maintains the active in-memory interface sessions.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, EditorSession] = {}

    def register(self, client_id: str | None = None) -> EditorSession:
        """
        Register a new connected client.
        """

        session = EditorSession(client_id=client_id)
        session.touch()

        self._sessions[session.client_id] = session

        return session

    def unregister(self, client_id: str) -> None:
        """
        Remove a client session.
        """

        self._sessions.pop(client_id, None)

    def get(self, client_id: str) -> EditorSession | None:
        """
        Fetch a session by client id.
        """

        return self._sessions.get(client_id)

    def update(
        self,
        client_id: str,
        *,
        open_file: str | None = None,
        dirty: bool | None = None,
    ) -> EditorSession | None:
        """
        Update one field of a client session.

        Returns the session, or None if the client is unknown.
        """

        session = self._sessions.get(client_id)

        if session is None:
            return None

        session.touch()

        if open_file is not None:
            session.open_file = open_file

        if dirty is not None:
            session.dirty = dirty

        return session

    def snapshot(self) -> list[dict[str, Any]]:
        """
        JSON-friendly list of all active sessions.
        """

        return [
            session.snapshot()
            for session in self._sessions.values()
        ]


# ============================================================
# EDITOR INTERFACE
# ============================================================

class EditorInterface:
    """
    The Project Manager operation/interface layer.

    Provides a narrow set of high-level operations agents and the
    web editor can use. All filesystem work goes through the
    component filesystem authority.
    """

    def __init__(
        self,
        filesystem: Any = None,
        events: EventBus | None = None,
        sessions: EditorManager | None = None,
    ) -> None:

        # The Project Manager remains the filesystem authority.
        self.filesystem = (
            filesystem
            if filesystem is not None
            else _filesystem
        )

        self.events = (
            events
            if events is not None
            else EventBus()
        )

        self.session_manager = (
            sessions
            if sessions is not None
            else EditorManager()
        )

    # ========================================================
    # HEALTH / STATE
    # ========================================================

    def health(self) -> dict[str, Any]:
        """
        Project Manager health and project information.
        """

        return {
            "status": "healthy",
            "project": self.filesystem.read_project_info(),
            "root": str(self.filesystem.PROJECT_ROOT),
        }

    def tree(
        self,
        scope: str | None = None,
        roots: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Project state: project info, active root and filesystem tree.

        Args:
            scope:
                None (default) returns the browser tree, whose top
                level is the configured ``BROWSE_ROOTS`` folders.
                ``"workspace"`` or ``"app"`` return the legacy
                single-root tree for that scope.
            roots:
                Browser roots to include, or None for all of them.
                Ignored when ``scope`` is set: the legacy view is
                already a single root, so there is nothing to
                choose between. This filters the listing only --
                the returned roots stay resolvable everywhere.
        """

        try:

            if not scope:

                browse_roots = (
                    self.filesystem.BROWSE_ROOTS
                )

                if roots is not None:

                    wanted = set(roots)

                    browse_roots = {
                        name: config
                        for name, config in browse_roots.items()
                        if name in wanted
                    }

                return {
                    "scope": None,
                    "project": self.filesystem.read_project_info(),
                    "roots": [
                        {
                            "name": name,
                            "writable": bool(
                                config.get(
                                    "writable",
                                    False,
                                )
                            ),
                        }
                        for name, config
                        in browse_roots.items()
                    ],
                    "root": str(
                        self.filesystem.PROJECT_ROOT
                    ),
                    "filesystem": (
                        self.filesystem.read_browse_filesystem(
                            roots=roots
                        )
                    ),
                }

            root = _root_for(scope)

            return {
                "scope": scope,
                "project": self.filesystem.read_project_info(),
                "root": str(root),
                "filesystem": self.filesystem.read_filesystem(
                    directory=root
                ),
            }

        except Exception as error:

            raise self._to_error(
                error
            )

    def sessions(self) -> list[dict[str, Any]]:
        """
        Snapshot of all connected interface sessions.
        """

        return self.session_manager.snapshot()

    # ========================================================
    # READ / WRITE
    # ========================================================

    def open(
        self,
        path: str,
        scope: str | None = None,
    ) -> str:
        """
        Open a project file and return its contents.

        Args:
            path:
                Root-qualified or root-relative file path.
            scope:
                ``None`` (default) or ``"workspace"`` or ``"app"``.

        Returns:
            The file contents.
        """

        stripped, root, _ = _target(path, scope)

        return self.filesystem.read_file(
            stripped,
            root=root,
        )

    def save(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Write file contents back to the project filesystem.

        Publishes a ``saved`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.write_file(
            stripped,
            content,
            root=root,
        )

        self.events.publish(
            "saved",
            path=path,
            scope=scope,
        )

        return {
            "status": "saved",
            "path": path,
            "scope": scope,
        }

    # ========================================================
    # CREATE
    # ========================================================

    def create_file(
        self,
        path: str,
        content: str = "",
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new project file.

        Publishes a ``created`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.create_file(
            stripped,
            content,
            root=root,
        )

        self.events.publish(
            "created",
            path=path,
            scope=scope,
        )

        return {
            "status": "created",
            "path": path,
            "scope": scope,
        }

    def create_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new project directory.

        Publishes a ``created`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.create_directory(
            stripped,
            root=root,
        )

        self.events.publish(
            "created",
            path=path,
            scope=scope,
        )

        return {
            "status": "created",
            "path": path,
            "scope": scope,
        }

    # ========================================================
    # RENAME
    # ========================================================

    def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Rename or move a project file/directory.

        Publishes a ``renamed`` event on success. Raises ValueError
        if either path targets a read-only browser root, or if the
        two paths belong to different browser roots.
        """

        self.filesystem.require_writable(
            old_path,
            _root_for(scope),
        )

        self.filesystem.require_writable(
            new_path,
            _root_for(scope),
        )

        old_stripped, old_root, old_name = _target(
            old_path,
            scope,
        )

        new_stripped, new_root, new_name = _target(
            new_path,
            scope,
        )

        if old_root != new_root:

            raise ValueError(
                "Cannot rename across browser roots "
                f"({old_name or 'scope'} -> "
                f"{new_name or 'scope'})."
            )

        self.filesystem.rename_path(
            old_stripped,
            new_stripped,
            root=old_root,
        )

        self.events.publish(
            "renamed",
            path=new_path,
            old_path=old_path,
            scope=scope,
        )

        return {
            "status": "renamed",
            "old_path": old_path,
            "new_path": new_path,
            "scope": scope,
        }

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Delete a project file or directory.

        Publishes a ``deleted`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.delete_path(
            stripped,
            root=root,
        )

        self.events.publish(
            "deleted",
            path=path,
            scope=scope,
        )

        return {
            "status": "deleted",
            "path": path,
            "scope": scope,
        }

    # ========================================================
    # ERROR MAPPING
    # ========================================================

    # Kept on the controller so every interface shares the same
    # error behaviour. See interface.project_manager_error for
    # the HTTP mapping.
    _to_error = staticmethod(
        lambda error: error
    )


# ============================================================
# DIRECT PROVIDER
# ============================================================

class DirectProjectIO:
    """
    Filesystem provider backed directly by the Project Manager's
    filesystem authority.

    Used when the agent engine is mounted INSIDE a running Project
    Manager server (the agent-backed /api/chat router), keeping the
    Project Manager as the single filesystem owner even in-process.
    """

    def __init__(self) -> None:
        self._filesystem = _filesystem
        self._root = Path(_filesystem.PROJECT_ROOT)
        self.scope = "workspace"

    # --------------------------------------------------------
    # PROVIDER SURFACE
    # --------------------------------------------------------

    @property
    def workspace_root(self) -> str:
        return str(self._root)

    def relpath(self, path: str) -> str:
        return _relpath(self._root, path)

    def list_tree(self) -> list:
        return self._filesystem.read_filesystem()

    def read(self, rel: str) -> str:
        return self._filesystem.read_file(rel)

    def write(self, rel: str, content: str) -> dict[str, Any]:
        self._filesystem.write_file(rel, content)
        return {"status": "saved", "path": rel, "scope": self.scope}

    def create(self, rel: str, content: str) -> dict[str, Any]:
        self._filesystem.create_file(rel, content)
        return {"status": "created", "path": rel, "scope": self.scope}

    def create_directory(self, rel: str) -> dict[str, Any]:
        self._filesystem.create_directory(rel)
        return {"status": "created", "path": rel, "scope": self.scope}

    def delete(self, rel: str) -> dict[str, Any]:
        self._filesystem.delete_path(rel)
        return {"status": "deleted", "path": rel, "scope": self.scope}

    def exists(self, rel: str) -> bool:
        target = (self._root / rel.replace("\\", "/").strip("/")).resolve()
        try:
            target.relative_to(self._root.resolve())
        except ValueError:
            return False
        return target.exists()

    # --------------------------------------------------------
    # PROJECT MANAGER CONVENIENCES
    # --------------------------------------------------------

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "project": self._filesystem.read_project_info(),
            "root": str(self._root),
        }

    def tree(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "project": self._filesystem.read_project_info(),
            "root": str(self._root),
            "filesystem": self._filesystem.read_filesystem(),
        }

    def project(self) -> dict[str, Any]:
        return self.tree()

    def sessions(self) -> list:
        return []

    def expose(self) -> dict[str, Any]:
        return {
            "mode": "direct",
            "workspace_root": self.workspace_root,
            "scope": self.scope,
        }


# ============================================================
# SYNC CLIENT
# ============================================================

class ProjectManagerBridge:
    """Synchronous HTTP bridge to the Project Manager server.

    Implements the provider surface used by the headless file tools and the
    Project Manager operations exposed by the original Python client.
    """

    #: how long a project tree snapshot is trusted (list/exists lookups)
    _TREE_TTL = 2.0

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout
        self.scope = "workspace"

        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

        self._root: str | None = None
        self._tree_cache: tuple[float, list] = (0.0, [])

    # ========================================================
    # PROVIDER SURFACE
    # ========================================================

    @property
    def workspace_root(self) -> str:
        """The Project Manager workspace root (from /api/health)."""
        if self._root is None:
            health = self.health()
            self._root = str((health or {}).get("root", ""))
        if not self._root:
            raise RuntimeError(
                "Project Manager did not report a workspace root."
            )
        return self._root

    def relpath(self, path: str) -> str:
        return _relpath(Path(self.workspace_root), path)

    def _fresh_tree(self) -> list:
        now = time.monotonic()
        if now - self._tree_cache[0] < self._TREE_TTL:
            return self._tree_cache[1]
        tree: list = (self.tree() or {}).get("filesystem") or []
        self._tree_cache = (now, tree)
        return tree

    def list_tree(self) -> list:
        """Nested project tree ([{name, path, type, children?, size?}...])."""
        return self._fresh_tree()

    def read(self, rel: str) -> str:
        """Read a workspace text file; returns the content."""
        return self.open(rel)["content"]

    def write(self, rel: str, content: str) -> dict[str, Any]:
        return self.save(rel, content)

    def create(self, rel: str, content: str) -> dict[str, Any]:
        return self.create_file(rel, content)

    def delete(self, rel: str) -> dict[str, Any]:
        return self.delete_file(rel)

    def exists(self, rel: str) -> bool:
        rel = rel.replace("\\", "/").strip("/")
        for entry in self._flatten_paths():
            if entry == rel:
                return True
        return False

    def _flatten_paths(self) -> list[str]:
        paths: list[str] = []

        def walk(entries):
            for entry in entries or []:
                rel = entry.get("path", "")
                if rel:
                    paths.append(rel)
                walk(entry.get("children") or [])

        walk(self._fresh_tree())
        return paths

    # ========================================================
    # GET HELPERS
    # ========================================================

    def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # PROJECT OPERATIONS
    # ========================================================

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def project(self) -> dict[str, Any]:
        return self._get("/api/project", scope=self.scope)

    def tree(self) -> dict[str, Any]:
        return self.project()

    def sessions(self) -> dict[str, Any]:
        return self._get("/api/sessions")

    # ========================================================
    # FILE OPERATIONS
    # ========================================================

    def read_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    def open(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Open a project file and return its contents.
        """

        return self.read_file(path, scope=scope)

    def write_file(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    def save(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Save file content. Alias for write_file().
        """

        return self.write_file(path, content, scope=scope)

    def create_file(
        self,
        path: str,
        content: str = "",
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    def delete_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    # ========================================================
    # DIRECTORY OPERATIONS
    # ========================================================

    def create_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope or self.scope,
            },
        )

    def delete_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    # ========================================================
    # RENAME / MOVE OPERATIONS
    # ========================================================

    def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope or self.scope,
            },
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def subscribe(
        self,
        *,
        timeout: float | None = None,
    ):
        """
        Open a WebSocket and yield Project Manager frames as they arrive.

        Frames keep the server contract: {"type": "event", "event": {...}}
        for project changes, {"type": "hello", ...} and
        {"type": "sessions", ...} for session state.
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        import websockets.sync.client as ws_sync

        with ws_sync.connect(
            ws_url,
            timeout=timeout,
        ) as socket:

            while True:

                message = socket.recv()

                if message is None:
                    break

                yield _decode_message(message)

    def expose(
        self,
    ) -> dict[str, Any]:
        """Self-description: which Project Manager endpoints the bridge uses."""
        return {
            "base_url": self.base_url,
            "workspace_root": self.workspace_root,
            "scope": self.scope,
        }

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "ProjectManagerBridge":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# ============================================================
# ASYNC CLIENT
# ============================================================

class AsyncProjectManagerBridge:
    """Asynchronous HTTP + WebSocket bridge to the Project Manager.

    Provides the same operations as ProjectManagerBridge with async/await,
    plus subscribe() for real-time project events.
    """

    _TREE_TTL = 2.0

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout
        self.scope = "workspace"

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

        self._root: str | None = None
        self._tree_cache: tuple[float, list] = (0.0, [])

    # ========================================================
    # PROVIDER SURFACE (async)
    # ========================================================

    @property
    async def workspace_root(self) -> str:
        if self._root is None:
            health = await self.health()
            self._root = str((health or {}).get("root", ""))
        if not self._root:
            raise RuntimeError(
                "Project Manager did not report a workspace root."
            )
        return self._root

    def relpath(self, path: str) -> str:
        root = self._root or "."
        return _relpath(Path(root), path)

    async def _fresh_tree(self) -> list:
        now = time.monotonic()
        if now - self._tree_cache[0] < self._TREE_TTL:
            return self._tree_cache[1]
        payload = await self.tree()
        tree: list = (payload or {}).get("filesystem") or []
        self._tree_cache = (now, tree)
        return tree

    async def list_tree(self) -> list:
        return await self._fresh_tree()

    async def read(self, rel: str) -> str:
        return (await self.open(rel))["content"]

    async def write(self, rel: str, content: str) -> dict[str, Any]:
        return await self.save(rel, content)

    async def create(self, rel: str, content: str) -> dict[str, Any]:
        return await self.create_file(rel, content)

    async def delete(self, rel: str) -> dict[str, Any]:
        return await self.delete_file(rel)

    async def exists(self, rel: str) -> bool:
        rel = rel.replace("\\", "/").strip("/")
        for path in await self._flatten_paths():
            if path == rel:
                return True
        return False

    async def _flatten_paths(self) -> list[str]:
        paths: list[str] = []

        def walk(entries):
            for entry in entries or []:
                rel = entry.get("path", "")
                if rel:
                    paths.append(rel)
                walk(entry.get("children") or [])

        walk(await self._fresh_tree())
        return paths

    # ========================================================
    # ASYNC HELPERS
    # ========================================================

    async def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # OPERATIONS (ASYNC)
    # ========================================================

    async def health(self) -> dict[str, Any]:
        return await self._get("/api/health")

    async def project(self) -> dict[str, Any]:
        return await self._get("/api/project", scope=self.scope)

    async def tree(self) -> dict[str, Any]:
        return await self.project()

    async def sessions(self) -> dict[str, Any]:
        return await self._get("/api/sessions")

    async def read_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    async def open(
        self,
        path: str,
        scope: str | None = None,
    ):
        return await self.read_file(path, scope=scope)

    async def write_file(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    async def save(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ):
        return await self.write_file(path, content, scope=scope)

    async def create_file(
        self,
        path: str,
        content: str = "",
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    async def delete_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    async def create_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope or self.scope,
            },
        )

    async def delete_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    async def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope or self.scope,
            },
        )

    # ========================================================
    # REAL-TIME SUBSCRIPTION
    # ========================================================

    async def subscribe(
        self,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Open a WebSocket and yield Project Manager event frames.

        Example:
            >>> async for frame in client.subscribe():
            ...     if frame.get("type") == "event":
            ...         event = frame["event"]
            ...         if event["type"] == "saved":
            ...             print("Saved", event["path"])
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        async with ws_connect(
            ws_url
        ) as socket:

            async for message in socket:

                yield _decode_message(
                    message
                )

    async def expose(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "workspace_root": await self.workspace_root,
            "scope": self.scope,
        }

    async def close(self) -> None:
        await self._http.aclose()


# ============================================================
# EDITOR CLIENTS (public Python SDK)
# ============================================================

class EditorClient:
    """
    Synchronous HTTP client for the Project Manager interface.

    All calls hit the running Project Manager server. Nothing is
    done directly against the filesystem.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout

        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

    # ========================================================
    # GET HELPERS
    # ========================================================

    def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # PROJECT OPERATIONS
    # ========================================================

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def project(self) -> dict[str, Any]:
        return self._get("/api/project")

    def tree(self) -> dict[str, Any]:
        return self.project()

    def sessions(self) -> dict[str, Any]:
        return self._get("/api/sessions")

    # ========================================================
    # FILE OPERATIONS
    # ========================================================

    def read(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope,
        )

    def open(
        self,
        path: str,
        scope: str = "workspace",
    ):
        """
        Open a project file and return its contents.

        Alias for read().
        """

        return self.read(path, scope=scope)

    def write(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    def save(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ):
        """
        Save file content. Alias for write().
        """

        return self.write(path, content, scope=scope)

    def create_file(
        self,
        path: str,
        content: str = "",
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    def delete_file(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    # ========================================================
    # DIRECTORY OPERATIONS
    # ========================================================

    def create_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope,
            },
        )

    def delete_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    # ========================================================
    # RENAME / MOVE OPERATIONS
    # ========================================================

    def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope,
            },
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def subscribe(
        self,
        *,
        timeout: float | None = None,
    ):
        """
        Open a WebSocket and yield events as they arrive.

        Returns:
            Synchronous iterator over Project Manager event dicts.
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        import websockets.sync.client as ws_sync

        with ws_sync.connect(
            ws_url,
            timeout=timeout,
        ) as socket:

            while True:

                message = socket.recv()

                if message is None:
                    break

                yield _decode_message(message)

    def close(self) -> None:
        self._http.close()

    # context-manager support
    def __enter__(self) -> "EditorClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class AsyncEditorClient:
    """
    Asynchronous HTTP + WebSocket client for AI agents.

    Provides the same operations as EditorClient but with
    async/await, plus ``subscribe()`` for real-time events.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

    # ========================================================
    # ASYNC HELPERS
    # ========================================================

    async def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # OPERATIONS (ASYNC)
    # ========================================================

    async def health(self) -> dict[str, Any]:
        return await self._get("/api/health")

    async def project(self) -> dict[str, Any]:
        return await self._get("/api/project")

    async def tree(self) -> dict[str, Any]:
        return await self.project()

    async def sessions(self) -> dict[str, Any]:
        return await self._get("/api/sessions")

    async def read(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope,
        )

    async def open(
        self,
        path: str,
        scope: str = "workspace",
    ):
        return await self.read(path, scope=scope)

    async def write(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    async def save(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ):
        return await self.write(path, content, scope=scope)

    async def create_file(
        self,
        path: str,
        content: str = "",
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    async def delete_file(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    async def create_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope,
            },
        )

    async def delete_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    async def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope,
            },
        )

    # ========================================================
    # REAL-TIME SUBSCRIPTION
    # ========================================================

    async def subscribe(
        self,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Open a WebSocket and yield Project Manager events.

        Example:
            >>> async for event in client.subscribe():
            ...     if event["type"] == "saved":
            ...         print("Saved", event["path"])
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        async with ws_connect(
            ws_url
        ) as socket:

            async for message in socket:

                yield _decode_message(
                    message
                )