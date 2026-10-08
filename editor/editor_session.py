"""Session Manager & Event Bus for the editor pillar."""

import asyncio
import time
import uuid

from editor.editor_schemas import EditorEvent, EditorEvent as Event, EditorEventType, EditorSessionInfo


class EditorSessionManager:
    """Tracks connected editor sessions and fans events out to subscribers."""

    def __init__(self):
        self._sessions: dict[str, EditorSessionInfo] = {}
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._event_log: list[dict] = []
        self._max_log = 200

    # --- session lifecycle -------------------------------------------------
    def create_session(self, client: str = "unknown") -> EditorSessionInfo:
        session_id = uuid.uuid4().hex[:12]
        info = EditorSessionInfo(session_id=session_id, client=client, joined_at=time.time())
        self._sessions[session_id] = info
        self._subscribers[session_id] = asyncio.Queue()
        self.broadcast(Event(type=EditorEventType.SESSION_JOIN, path="", session_id=session_id,
                             data={"client": client}))
        return info

    def drop_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self.broadcast(Event(type=EditorEventType.SESSION_LEAVE, path="",
                                 session_id=session_id))
        self._sessions.pop(session_id, None)
        self._subscribers.pop(session_id, None)

    def set_active_path(self, session_id: str, path: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].active_path = path

    def sessions(self) -> list[EditorSessionInfo]:
        return list(self._sessions.values())

    # --- event bus ---------------------------------------------------------
    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue = self._subscribers.get(session_id)
        if queue is None:
            queue = asyncio.Queue()
            self._subscribers[session_id] = queue
        return queue

    def unsubscribe(self, session_id: str) -> None:
        self._subscribers.pop(session_id, None)

    def broadcast(self, event: Event) -> dict:
        payload = event.to_dict()
        self._event_log.append(payload)
        if len(self._event_log) > self._max_log:
            self._event_log = self._event_log[-self._max_log:]
        for queue in self._subscribers.values():
            queue.put_nowait(payload)
        return payload

    def publish(self, event_type: EditorEventType, path: str, session_id: str, **data) -> dict:
        return self.broadcast(Event(type=event_type, path=path, session_id=session_id, data=data or None))

    def recent_events(self, limit: int = 50) -> list[dict]:
        return self._event_log[-limit:]


# Global doorway instance used across editor modules.
manager = EditorSessionManager()
