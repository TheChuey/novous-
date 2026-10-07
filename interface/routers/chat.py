"""Agent-backed chat with browser-supplied context and saved text sessions."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .errors import project_manager_error


# ------------------------------------------------------------
# Headless engine bootstrap (works from the server app or when imported
# from the headless bridge package).
# ------------------------------------------------------------

def _ensure_headless_on_path() -> None:
    here = Path(__file__).resolve()
    candidate = here.parents[2] / "headless_app"
    if not candidate.is_dir():
        candidate = here.parents[2]
    candidate = candidate.resolve()
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


_ensure_headless_on_path()

from engine.agents.loader import AgentNotFoundError  # noqa: E402
from engine.agents.registry import list_agents  # noqa: E402
try:
    from bridge.providers import DirectProjectIO  # noqa: E402
except Exception:
    DirectProjectIO = None  # type: ignore[assignment]


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

# ============================================================
# CHAT REQUEST LIMITS
# ============================================================

MAX_MESSAGE_LENGTH = 32000

MAX_HISTORY_ENTRIES = 200

MAX_SESSION_ENTRIES = 2000

_provider_cache: Any = None
_runner_cache: Any = None


def _provider() -> Any:
    """The active filesystem authority in the in-process server."""
    global _provider_cache
    if _provider_cache is None:
        if DirectProjectIO is None:
            raise RuntimeError(
                "DirectProjectIO is unavailable - the agent-backed chat "
                "router must run inside the Project Manager server."
            )
        _provider_cache = DirectProjectIO()
    return _provider_cache


def _runner() -> Any:
    """The shared AgentInterface, the single engine entry point.

    Holds no conversation state: each run builds a fresh agent and uses only
    the history supplied by the browser, so requests stay independent.
    """
    global _runner_cache
    if _runner_cache is None:
        from interface_runner import AgentInterface  # noqa: E402

        _runner_cache = AgentInterface(bridge=_provider())
    return _runner_cache


def _default_agent_id() -> str | None:
    agents = list_agents()
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
        message (str):   the user's message (required, non-empty, max 2000).
        agent_id (str):  agent to use; defaults to the first registered.
        model (str):     optional model override.

    The browser supplies the current thread as history. Chat turns are
    not written to the engine chat log; Save Session owns persistence.
    """

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

        result = _runner().run_chat(
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
#
# A session file is the only persistent record of one chat thread.
# Sessions live under the managed workspace and are excluded from git
# with workspace/data/.
#
#     workspace/data/chat_sessions/<agent_id>/<session_id>.txt

SESSIONS_DIRNAME = "data/chat_sessions"

SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")

MAX_TITLE_LENGTH = 80

EXPORT_FORMATS = ("txt",)


def _sessions_root() -> Path:
    """Absolute path of the sessions directory inside the workspace."""
    from parameters import filesystem

    return filesystem.resolve_project_path(SESSIONS_DIRNAME)


def _safe_id(value: str, kind: str) -> str:
    """
    Validate an id used as a single path segment.

    Agent and session ids both become directory or file names, so
    anything that could climb out of the sessions directory is
    refused rather than sanitized.
    """

    if not value or not SAFE_ID.match(value):
        raise ValueError(
            f"Invalid {kind}: {value!r}. Use letters, numbers, "
            "underscore or dash only."
        )

    return value


def _new_session_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _derive_title(entries: list[dict]) -> str:
    """Title from the first user turn, else a timestamp."""
    for entry in entries:
        if entry.get("sender") == "user":
            text = " ".join(str(entry.get("message", "")).split())
            if text:
                if len(text) > MAX_TITLE_LENGTH:
                    text = text[: MAX_TITLE_LENGTH - 1].rstrip() + "\u2026"
                return text
    return "Session " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _session_file(session_id: str, agent_id: str) -> Path:
    agent = _safe_id(agent_id, "agent id")
    session = _safe_id(session_id, "session id")
    return _sessions_root() / agent / f"{session}.txt"


def _summary(record: dict) -> dict:
    """List-view projection of a stored session."""
    return {
        "id": record.get("id", ""),
        "agent_id": record.get("agent_id", ""),
        "title": record.get("title", ""),
        "created": record.get("created", ""),
        "entry_count": len(record.get("entries", [])),
    }


def _read_session(session_id: str, agent_id: str) -> dict:
    path = _session_file(session_id, agent_id)
    if not path.exists():
        raise FileNotFoundError(f"No saved session {session_id!r}.")
    return _parse_session_text(path.read_text(encoding="utf-8"))


def _serialize_session(record: dict) -> str:
    """Write one readable text transcript with length-delimited messages."""
    display_title = " ".join(str(record.get("title") or "Chat session").split())
    metadata = {
        key: record.get(key, "")
        for key in ("id", "agent_id", "title", "created")
    }
    lines = [
        f"# {display_title}",
        "",
        "<!-- session: " + json.dumps(metadata, ensure_ascii=False) + " -->",
        "",
    ]
    for entry in record.get("entries", []):
        message = str(entry.get("message", ""))
        entry_metadata = {
            "sender": entry.get("sender", ""),
            "agent": entry.get("agent"),
            "ts": entry.get("ts", ""),
            "length": len(message),
        }
        who = (
            "You"
            if entry_metadata["sender"] == "user"
            else entry_metadata.get("agent") or "Agent"
        )
        lines.extend([
            f"## {who}",
            "<!-- entry: " + json.dumps(entry_metadata, ensure_ascii=False) + " -->",
            message,
            "",
        ])
    return "\n".join(lines)


def _parse_session_text(text: str) -> dict:
    """Parse the app's readable text session format without losing message text."""
    lines = text.splitlines(keepends=True)
    if len(lines) < 3 or not lines[2].startswith("<!-- session: ") or not lines[2].rstrip().endswith(" -->"):
        raise ValueError("Saved chat session has an invalid header.")

    metadata_text = lines[2].rstrip()[len("<!-- session: "):-len(" -->")]
    record = json.loads(metadata_text)
    content = "".join(lines[3:])
    entries = []
    position = 0

    while position < len(content):
        while position < len(content) and content[position] == "\n":
            position += 1
        if position >= len(content):
            break
        if content.startswith("## ", position):
            heading_end = content.find("\n", position)
            if heading_end < 0:
                raise ValueError("Saved chat session has an incomplete message heading.")
            position = heading_end + 1
        marker_end = content.find("\n", position)
        if marker_end < 0:
            raise ValueError("Saved chat session has an incomplete message header.")
        marker = content[position:marker_end]
        prefix, suffix = "<!-- entry: ", " -->"
        if not marker.startswith(prefix) or not marker.endswith(suffix):
            raise ValueError("Saved chat session has an invalid message header.")
        entry_metadata = json.loads(marker[len(prefix):-len(suffix)])
        length = entry_metadata.get("length")
        if not isinstance(length, int) or length < 0:
            raise ValueError("Saved chat session has an invalid message length.")
        body_start = marker_end + 1
        body_end = body_start + length
        if body_end > len(content):
            raise ValueError("Saved chat session message is truncated.")
        message = content[body_start:body_end]
        if body_end < len(content) and content[body_end] == "\n":
            body_end += 1
        entries.append({
            "sender": entry_metadata.get("sender"),
            "agent": entry_metadata.get("agent"),
            "ts": entry_metadata.get("ts", ""),
            "message": message,
        })
        position = body_end

    record["entries"] = entries
    return record


def _sole_owner(session_id: str) -> str:
    """The agent that owns a session id, when the id is unique.

    Session ids embed a timestamp, so two agents saving in the same
    millisecond could collide. Callers pass the agent explicitly in
    that case; this helper only resolves the unambiguous case.
    """
    _safe_id(session_id, "session id")
    root = _sessions_root()
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


def _list_sessions(agent_id: str | None) -> list[dict]:
    """Every stored session, newest first.

    With ``agent_id`` set only that agent's sessions are returned,
    which is what the chat panel shows.
    """
    root = _sessions_root()
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
            "sessions": _list_sessions(agent),
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

        path = _session_file(record["id"], record["agent_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_serialize_session(record), encoding="utf-8")

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
            agent = _sole_owner(session_id)

        return _read_session(session_id, agent)

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
            agent = _sole_owner(session_id)

        path = _session_file(session_id, agent)
        if not path.exists():
            raise project_manager_error(
                ValueError(
                    f"No saved session {session_id!r}."
                )
            )
        path.unlink()

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
            agent = _sole_owner(session_id)

        record = _read_session(session_id, agent)
        body = _session_file(session_id, agent).read_text(encoding="utf-8")
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


if __name__ == "__main__":
    print(__doc__)