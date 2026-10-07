"""engine/interface.py

Public doorway. The sole import surface for outside callers; exposes
public functions and the FastAPI router.

Component: Core Reasoning & Think-Loop Runtime.

THE public doorway into the agent engine. Callers (CLI, server routers,
test runner) import this module and nothing else from the engine.

    import engine.interface as engine
    engine.configure(bridge=engine.direct_provider())
    engine.run_chat("hello", agent_id="rag_assistant")

Contract
--------
* Validates input, then delegates. No workflow lives here.
* Returns plain dicts / lists (JSON-ready).
* Raises only:
    ValueError            bad input                (HTTP 400)
    AgentNotFoundError    unknown agent id/path    (HTTP 404, a FileNotFoundError)
    anything else         genuine failure          (HTTP 500)

Also hosts the /api/chat router: one chat turn plus the saved text
sessions under workspace/data/chat_sessions/.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Request
from fastapi.responses import Response
from project_manager.interface import (
    DirectProjectIO,
    ProjectManagerBridge,
    project_manager_error,
)
from pydantic import BaseModel, Field

from configuration.interface import list_models, refresh_models
from tools.interface import clear_chat, list_tools, read_history, use_data_dir

from .code import (
    Agent,
    AgentInterface,
    AgentProfile,
    PromptManager,
    ask_llm,
)
from .code import _ollama_tool_schema  # noqa: F401  (test support export)
from .data import (
    DEFAULT_HISTORY_LIMIT,
    MAX_HISTORY_ENTRIES,
    MAX_SESSION_ENTRIES,
    MAX_TITLE_LENGTH,
    EXPORT_FORMATS,
)
from .helperfunctions import (
    _derive_title,
    _new_session_id,
    _safe_id,
    _serialize_session,
    _summary,
)
from .logic import (
    agent_definition,
    configure,
    delete_session,
    get_runtime,
    list_sessions,
    read_session,
    session_file,
    sole_owner,
    tool_catalog,
    write_session,
)

__all__ = [
    "Agent",
    "AgentDefinitionError",
    "AgentInterface",
    "AgentNotFoundError",
    "AgentProfile",
    "DEFAULT_HISTORY_LIMIT",
    "PromptManager",
    "agent_definition",
    "ask_llm",
    "clear_history",
    "configure",
    "default_pipeline",
    "direct_provider",
    "get_agent",
    "http_provider",
    "list_agents",
    "list_models",
    "list_tools",
    "read_history",
    "refresh_models",
    "register_agent_root",
    "router",
    "run_chat",
    "run_pipeline",
    "run_single_agent",
    "tool_catalog",
    "unregister_agent_root",
    "use_data_dir",
]

# ============================================================
# MESSAGE LIMITS
# ============================================================

#: Router-wide chat message limit (shared with the agents router).
MAX_MESSAGE_LENGTH = 32000

#: Facade run_*() limit (engine_interface contract).
_FACADE_MESSAGE_LIMIT = 2000


def __getattr__(name: str):
    """Lazy re-exports that would otherwise cycle on the agents component."""
    if name in ("AgentDefinitionError", "AgentNotFoundError"):
        from agents.interface import (
            AgentDefinitionError,
            AgentNotFoundError,
        )

        return {
            "AgentDefinitionError": AgentDefinitionError,
            "AgentNotFoundError": AgentNotFoundError,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ============================================================
# RUNNER (shared, bridged, stateless between requests)
# ============================================================

_runner_cache: Any = None


def get_runner() -> AgentInterface:
    """The shared AgentInterface, the single engine entry point.

    Holds no conversation state: each run builds a fresh agent and uses only
    the history supplied by the browser, so requests stay independent.
    All server routers share one instance.
    """
    global _runner_cache
    if _runner_cache is None:
        _runner_cache = AgentInterface(bridge=DirectProjectIO())
    return _runner_cache


# ============================================================
# FACADE CONFIGURATION
# ============================================================

def register_agent_root(name: str, path, source: str | None = None) -> None:
    """Make another folder of agent folders runnable (e.g. workspace/agents)."""
    from agents.interface import register_agent_root as _register

    _register(name, path, source=source)


def unregister_agent_root(name: str) -> bool:
    from agents.interface import unregister_agent_root as _unregister

    return _unregister(name)


def direct_provider():
    """In-process filesystem provider (needs the Project Manager importable)."""
    return DirectProjectIO()


def http_provider(base_url: str | None = None):
    """HTTP bridge provider for the standalone CLI."""
    return ProjectManagerBridge(base_url=base_url)


# ============================================================
# FACADE VALIDATION
# ============================================================

def _message(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("Chat message cannot be empty.")
    if len(text) > _FACADE_MESSAGE_LIMIT:
        raise ValueError(f"Chat message is too long (max {_FACADE_MESSAGE_LIMIT} characters).")
    return text


# ============================================================
# FACADE RUNS
# ============================================================

def run_chat(message: str, agent_id: str | None = None,
             model: str | None = None) -> dict:
    """One chat turn. {reply, agent_id, name, model, tool_events, entries}"""
    return get_runtime().run_chat(_message(message), agent_id=agent_id, model=model)


def run_single_agent(message: str, json_path: str | None = None,
                     md_path: str | None = None, agent_id: str | None = None,
                     model: str | None = None) -> dict:
    """Run one agent from agent.json + agent.md paths, or from an id."""
    return get_runtime().run_single_agent(_message(message), json_path=json_path,
                                          md_path=md_path, agent_id=agent_id,
                                          model=model)


def run_pipeline(message: str, steps: list | None = None,
                 model: str | None = None) -> dict:
    """Cascade agents. steps: ids or {json_path, md_path}; None = config default.
    {reply, outputs, tool_events, model, entries}"""
    text = _message(message)
    if steps is not None and not steps:
        raise ValueError("Pipeline requires at least one step.")
    for step in steps or []:
        if isinstance(step, dict) and not (step.get("json_path") and step.get("md_path")):
            raise ValueError(f"Pipeline step dicts need json_path + md_path: {step!r}")
    return get_runtime().run_pipeline(text, agent_configs=steps, model=model)


# ============================================================
# FACADE DISCOVERY
# ============================================================

def list_agents() -> list[dict]:
    return get_runtime().list_agents()


def get_agent(agent_id: str) -> dict:
    """Definition of one agent. Raises AgentNotFoundError."""
    return agent_definition(agent_id)


def default_pipeline() -> list:
    from pipelines.interface import load_pipeline

    return load_pipeline()


def clear_history(agent: str | None = None) -> int:
    return clear_chat(agent=agent)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatHistoryEntry(BaseModel):

    role: Literal["user", "assistant"]

    content: str


class ChatMessage(BaseModel):

    message: str

    agent_id: str | None = None

    model: str | None = None

    history: list[ChatHistoryEntry] = Field(default_factory=list)


class ChatSessionEntry(BaseModel):

    sender: Literal["user", "agent"]

    message: str

    ts: str = ""

    agent: str | None = None


class SessionSave(BaseModel):

    agent_id: str

    title: str | None = None

    entries: list[ChatSessionEntry]


def _default_agent_id() -> str | None:
    from agents.interface import list_agents as _list_agents

    agents = _list_agents()
    if not agents:
        return None
    return agents[0]["id"]


# ============================================================
# SEND MESSAGE
# ============================================================

@router.post("/api/chat")
def send_chat_message(
    request: Request,
    payload: ChatMessage,
):
    """
    Send a message to the agent engine and return its reply.

    Body:
        message (str):   the user's message (required, non-empty, max 32000).
        agent_id (str):  agent to use; defaults to the first registered.
        model (str):     optional model override.

    The browser supplies the current thread as history. Chat turns are
    not written to the engine chat log; Save Session owns persistence.
    """
    from agents.interface import AgentNotFoundError

    message = payload.message.strip()

    if not message:

        raise project_manager_error(
            ValueError(
                "Chat message cannot be empty."
            )
        )

    if len(message) > MAX_MESSAGE_LENGTH:

        raise project_manager_error(
            ValueError(
                f"Chat message is too long "
                f"(max {MAX_MESSAGE_LENGTH} characters)."
            )
        )

    if len(payload.history) > MAX_HISTORY_ENTRIES:
        raise project_manager_error(
            ValueError(
                f"Chat history is too long (max {MAX_HISTORY_ENTRIES} messages)."
            )
        )

    agent_id = payload.agent_id or _default_agent_id()

    if not agent_id:

        raise project_manager_error(
            RuntimeError(
                "No agents are registered. Register an agent root and check "
                "that its agent.json files exist."
            )
        )

    try:

        result = get_runner().run_chat(
            message,
            agent_id=agent_id,
            model=payload.model,
            history=[entry.model_dump() for entry in payload.history],
            use_logged_history=False,
            persist=False,
        )

        entries = result.get("entries") or []

        return {
            "status": "ok",
            "reply": result["reply"],
            "agent_id": result.get("agent_id", agent_id),
            "name": result.get("name", ""),
            "model": result.get("model"),
            "tool_events": result.get("tool_events") or [],
            "entry": entries[0] if entries else None,
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(
                f"Agent not found: {agent_id} ({error})"
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# SAVED CHAT SESSIONS
# ============================================================

@router.get("/api/chat/sessions")
def list_saved_sessions(
    request: Request,
    agent: str | None = None,
):
    """
    List saved chat sessions, newest first.

    Query params:
        agent:
            Only this agent's sessions. Omit to list every agent's.
    """

    try:

        return {
            "sessions": list_sessions(agent),
        }

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.post("/api/chat/sessions")
def save_chat_session(
    request: Request,
    payload: SessionSave,
):
    """
    Save the browser's current thread as its only persistent transcript.

    Body:
        agent_id (str):  whose thread to save (required).
        title (str?):    optional; defaults to the first user turn.

    The browser's live thread stays in memory and is not otherwise logged.
    """

    try:

        agent_id = _safe_id(payload.agent_id, "agent id")
        entries = [
            entry.model_dump()
            for entry in payload.entries
        ]

        if not entries:
            raise project_manager_error(
                ValueError(
                    "Nothing to save: the current chat has no messages."
                )
            )
        if len(entries) > MAX_SESSION_ENTRIES:
            raise project_manager_error(
                ValueError(
                    f"A session can contain at most {MAX_SESSION_ENTRIES} messages."
                )
            )

        title = (payload.title or "").strip()
        if len(title) > MAX_TITLE_LENGTH:
            raise project_manager_error(
                ValueError(
                    f"Session title is too long (max {MAX_TITLE_LENGTH} characters)."
                )
            )

        record = {
            "id": _new_session_id(),
            "agent_id": agent_id,
            "title": title or _derive_title(entries),
            "created": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        }

        write_session(record)

        return {
            "status": "ok",
            "session": _summary(record),
        }

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.get("/api/chat/sessions/{session_id}")
def get_saved_session(
    request: Request,
    session_id: str,
    agent: str | None = None,
):
    """
    Return one saved session, entries included.

    Query params:
        agent:
            Required when the session id is not unique across agents.
    """

    try:

        if not agent:
            agent = sole_owner(session_id)

        return read_session(session_id, agent)

    except FileNotFoundError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.delete("/api/chat/sessions/{session_id}")
def delete_saved_session(
    request: Request,
    session_id: str,
    agent: str | None = None,
):
    """
    Delete the text file holding one saved chat session.
    """

    try:

        if not agent:
            agent = sole_owner(session_id)

        delete_session(session_id, agent)

        return {
            "status": "ok",
            "deleted": session_id,
        }

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.get("/api/chat/sessions/{session_id}/export")
def export_saved_session(
    request: Request,
    session_id: str,
    agent: str | None = None,
    format: str = "txt",
):
    """
    Download a saved session as a file.

    Query params:
        agent:
            Required when the session id is not unique across agents.
        format:
            Only ``txt`` is supported so downloads remain the exact
            saved source file.
    """

    try:

        if format not in EXPORT_FORMATS:
            raise ValueError(
                f"Unsupported export format {format!r}. "
                f"Use one of: {', '.join(EXPORT_FORMATS)}."
            )

        if not agent:
            agent = sole_owner(session_id)

        record = read_session(session_id, agent)
        body = session_file(session_id, agent).read_text(encoding="utf-8")
        media_type = "text/plain; charset=utf-8"
        extension = "txt"

        safe_title = re.sub(
            r"[^A-Za-z0-9_-]+",
            "-",
            record.get("title", "chat-session"),
        ).strip("-") or "chat-session"

        filename = f"{safe_title[:60]}-{session_id}.{extension}"

        return Response(
            content=body,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except FileNotFoundError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )
