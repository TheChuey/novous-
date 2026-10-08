"""Scope & Event Payload Types for the editor session layer."""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class EditorScope(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    AGENTS = "agents"
    TESTING = "testing"


class EditorEventType(str, Enum):
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    CURSOR_MOVED = "cursor_moved"
    SESSION_JOIN = "session_join"
    SESSION_LEAVE = "session_leave"


@dataclass
class EditorEvent:
    """Payload broadcast to every subscriber of the editor event bus."""
    type: EditorEventType
    path: str
    session_id: str
    scope: EditorScope = EditorScope.WORKSPACE
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["type"] = self.type.value
        payload["scope"] = self.scope.value
        return payload


@dataclass
class EditorSessionInfo:
    session_id: str
    client: str = "unknown"
    active_path: str = ""
    joined_at: float = 0.0
