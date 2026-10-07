"""project_manager/logic.py

Orchestration & business rules: the single shared Project Manager state.

Builds the single, shared interface state so every router, the browser,
the WebSocket endpoint and the Python client all talk to the same
in-memory event bus, session pool and controller.

    project_manager routers ──┐
    engine / testing        ──┼──► get_interface()
    browser (WS)            ──┘         │
                                         ▼
                                   EditorInterface
                                         │
                    directory_layout / workspace_manager / mutations
"""

from __future__ import annotations

from .code import EditorInterface, EditorManager, EventBus

__all__ = [
    "get_events",
    "get_interface",
    "get_sessions",
    "reset_for_tests",
]


# ============================================================
# SHARED STATE
# ============================================================

_events: EventBus | None = None

_sessions: EditorManager | None = None

_interface: EditorInterface | None = None


def get_events() -> EventBus:
    """
    The shared project event bus.
    """

    global _events

    if _events is None:

        _events = EventBus()

    return _events


def get_sessions() -> EditorManager:
    """
    The shared editor session pool.
    """

    global _sessions

    if _sessions is None:

        _sessions = EditorManager()

    return _sessions


def get_interface() -> EditorInterface:
    """
    The shared Project Manager controller.

    Called by routers and by the web dashboard.
    """

    global _interface

    if _interface is None:

        _interface = EditorInterface(
            events=get_events(),
            sessions=get_sessions(),
        )

    return _interface


def reset_for_tests() -> None:
    """
    Clear all shared state (used by the verification suite).
    """

    global _events
    global _sessions
    global _interface

    _events = None

    _sessions = None

    _interface = None
