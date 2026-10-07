"""engine/logic.py

Workflows of the agent engine: the shared runner state, the saved
chat-session store, definition queries and the tool catalog.

    configure / get_runtime  -> the shared AgentInterface configuration
    sessions                 -> workspace/data/chat_sessions/*.txt
    agent_definition         -> one agent's definition across all roots
    tool_catalog             -> UI descriptors for registered tools

No input validation (that is engine_interface) and no HTTP (the router
in engine_interface owns that).
"""

from __future__ import annotations

from pathlib import Path

from directory_layout.interface import resolve_project_path
from tools.interface import _TOOL_REGISTRY, list_tools

from .code import AgentInterface
from .data import SESSIONS_DIRNAME
from .helperfunctions import (
    _parse_session_text,
    _safe_id,
    _serialize_session,
    _summary,
)

__all__ = [
    "agent_definition",
    "configure",
    "delete_session",
    "get_runtime",
    "list_sessions",
    "read_session",
    "session_file",
    "sessions_root",
    "sole_owner",
    "tool_catalog",
    "write_session",
]


# ============================================================
# SHARED RUNTIME STATE
# ============================================================

_runtime: AgentInterface | None = None


def get_runtime() -> AgentInterface:
    """The shared, unbridged AgentInterface used by the facade."""
    global _runtime

    if _runtime is None:
        _runtime = AgentInterface()

    return _runtime


def configure(bridge=None, model: str | None = None, log_sink=None) -> None:
    """Set the filesystem provider, default model and log mirror."""
    global _runtime
    _runtime = AgentInterface(bridge=bridge, model=model, log_sink=log_sink)


# ============================================================
# SAVED CHAT SESSIONS
# ============================================================

def sessions_root() -> Path:
    """Absolute path of the sessions directory inside the workspace."""
    return resolve_project_path(SESSIONS_DIRNAME)


def session_file(session_id: str, agent_id: str) -> Path:
    """The text file holding one agent's saved session."""
    agent = _safe_id(agent_id, "agent id")
    session = _safe_id(session_id, "session id")
    return sessions_root() / agent / f"{session}.txt"


def read_session(session_id: str, agent_id: str) -> dict:
    """One stored session, parsed. FileNotFoundError when absent."""
    path = session_file(session_id, agent_id)
    if not path.exists():
        raise FileNotFoundError(f"No saved session {session_id!r}.")
    return _parse_session_text(path.read_text(encoding="utf-8"))


def write_session(record: dict) -> Path:
    """Persist one session record as a readable text transcript."""
    path = session_file(record["id"], record["agent_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_serialize_session(record), encoding="utf-8")
    return path


def delete_session(session_id: str, agent_id: str) -> None:
    """Delete the text file holding one saved chat session."""
    path = session_file(session_id, agent_id)
    if not path.exists():
        raise ValueError(f"No saved session {session_id!r}.")
    path.unlink()


def sole_owner(session_id: str) -> str:
    """The agent that owns a session id, when the id is unique.

    Session ids embed a timestamp, so two agents saving in the same
    millisecond could collide. Callers pass the agent explicitly in
    that case; this helper only resolves the unambiguous case.
    """
    _safe_id(session_id, "session id")
    root = sessions_root()
    owners = [
        path.parent.name
        for path in root.glob(f"*/{session_id}.txt")
    ] if root.is_dir() else []
    if not owners:
        raise FileNotFoundError(f"No saved session {session_id!r}.")
    if len(owners) > 1:
        raise ValueError(
            f"Session {session_id!r} exists for several agents "
            f"({', '.join(sorted(owners))}). Pass the agent explicitly."
        )
    return owners[0]


def list_sessions(agent_id: str | None) -> list[dict]:
    """Every stored session, newest first.

    With ``agent_id`` set only that agent's sessions are returned,
    which is what the chat panel shows.
    """
    root = sessions_root()
    if not root.is_dir():
        return []
    wanted = _safe_id(agent_id, "agent id") if agent_id else None
    records: list[dict] = []
    for path in root.glob("*/*.txt"):
        if wanted and path.parent.name != wanted:
            continue
        records.append(_parse_session_text(path.read_text(encoding="utf-8")))
    records.sort(key=lambda r: r.get("created", ""), reverse=True)
    return [_summary(record) for record in records]


# ============================================================
# DISCOVERY QUERIES
# ============================================================

def agent_definition(agent_id: str) -> dict:
    """One agent's full definition (source, meta, sections, paths)."""
    from agents.interface import (
        agent_json_path,
        agent_md_path,
        find_agent,
        load_definition,
    )

    d = load_definition(agent_id)
    found = find_agent(agent_id)
    return {"source": found[0].source if found else "library",
            "meta": d["meta"], "sections": d["sections"],
            "json_path": agent_json_path(agent_id),
            "md_path": agent_md_path(agent_id)}


def tool_catalog() -> list[dict]:
    """Return UI descriptors from each registered LangChain tool schema."""
    out = []
    for tool_id in list_tools():
        registered_tool = _TOOL_REGISTRY[tool_id]
        doc = registered_tool.description or ""
        params = [
            {
                "name": name,
                "required": field.is_required(),
                "default": None if field.is_required() else repr(field.default),
            }
            for name, field in registered_tool.args_schema.model_fields.items()
        ]
        out.append({"id": tool_id, "summary": doc.splitlines()[0] if doc else "",
                    "description": doc, "parameters": params})
    return out
