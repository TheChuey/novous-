"""agents/interface.py

Public doorway. The sole import surface for outside callers; exposes
public functions and the FastAPI router.

Component: Agent Discovery, Registry & Lifecycle. Other components import
*only* this file for agent building/discovery, definition loading, the
root registry and the /api/agents endpoints.

Every agent is built and run through ``engine.interface.get_runner()``,
the same seam the headless CLI uses, so behaviour cannot drift between
frontends. Discovery likewise has a single source of truth: the agent
root registry. The Project Manager registers ``<workspace>/agents/`` as
a root at startup, so an agent created in the workspace behaves exactly
like a bundled library agent.

    GET  /api/agents
        -> every agent across every registered root (library +
           workspace), highest-precedence root first.

    GET  /api/agents/{agent_id}
        -> {"source", "meta", "sections"} for one agent, resolved through
           the loader, so the editor can open/read its definition.

    POST /api/agents/run
        {"json_path", "md_path" | "agent_id", "message", "model"?}
        -> builds the agent (workspace-relative paths resolved through the
           directory layout), runs it without persisting chat, and
           returns {"reply", "agent_id", "name", "model", "tool_events"}.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from directory_layout.interface import PROJECT_ROOT, resolve_project_path
from engine.interface import MAX_MESSAGE_LENGTH, get_runner
from fastapi import APIRouter, Request
from pydantic import BaseModel

from project_manager.interface import project_manager_error

from .code import (
    AgentDefinitionError,
    _session_aware,
    build_agent,
    build_agent_from_definition,
    find_agent,
    get_agent_meta,
    list_agents,
    register_agent_root,
    replay_history,
    reset_agent_roots,
    unregister_agent_root,
)
from .data import (
    AGENT_LIBRARY_DIR,
    AGENT_MD_FILE,
    AGENT_META_FILE,
    LIBRARY_ROOT_NAME,
    AgentNotFoundError,
    AgentRoot,
)
from .logic import (
    agent_dir,
    agent_json_path,
    agent_md_path,
    load_definition,
    load_definition_from_paths,
    save_markdown,
    save_meta,
    save_tests,
)

__all__ = [
    "AGENT_LIBRARY_DIR",
    "AGENT_MD_FILE",
    "AGENT_META_FILE",
    "AgentDefinitionError",
    "AgentNotFoundError",
    "AgentRoot",
    "LIBRARY_ROOT_NAME",
    "agent_dir",
    "agent_json_path",
    "agent_md_path",
    "agent_payload",
    "build_agent",
    "build_agent_from_definition",
    "find_agent",
    "get_agent_meta",
    "list_agents",
    "load_definition",
    "load_definition_from_paths",
    "register_agent_root",
    "replay_history",
    "reset_agent_roots",
    "router",
    "save_markdown",
    "save_meta",
    "save_tests",
    "unregister_agent_root",
    "_session_aware",
]


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class AgentRunRequest(BaseModel):

    message: str

    agent_id: str | None = None

    json_path: str | None = None

    md_path: str | None = None

    model: str | None = None


# ============================================================
# WORKSPACE PATH HELPERS
# ============================================================

def _resolve(relative_path: str) -> Path:
    """Safe absolute path for an agent file path.

    Workspace-relative paths ("agents/demo/agent.json") are the documented
    input. An absolute path is also accepted, but only when it really is
    inside the workspace, so a queue saved from a previous session cannot
    reach outside the project.
    """
    return resolve_project_path(relative_path)


def _api_path(path: str | None) -> str | None:
    """Translate an engine path into a workspace-relative API path.

    The engine reports absolute paths (its own truth), but the API contract is
    workspace-relative ("agents/<name>/agent.md") because that is what the
    frontend stores in the pipeline queue and sends back to the run endpoints.
    Returns None for anything outside the workspace (a library agent).
    """
    if not path:
        return None
    try:
        rel = Path(path).resolve().relative_to(Path(PROJECT_ROOT).resolve())
    except (ValueError, OSError):
        return None
    return rel.as_posix()


def agent_payload(summary: dict) -> dict:
    """Shape one registry summary for /api/agents.

    json_path/md_path are present only for workspace agents, matching the
    contract the pipeline queue and editor already depend on.
    """
    payload = {
        "id": summary["id"],
        "name": summary["name"],
        "description": summary["description"],
        "mode": summary["mode"],
        "model": summary["model"],
        "tools": summary["tools"],
        "source": summary["source"],
        "complete": summary["complete"],
    }
    json_path = _api_path(summary.get("json_path"))
    if json_path is not None:
        payload["json_path"] = json_path
        payload["md_path"] = _api_path(summary.get("md_path"))
    return payload


# ============================================================
# MESSAGE VALIDATION
# ============================================================

def _validated_message(message: str) -> str:
    text = message.strip()
    if not text:
        raise project_manager_error(ValueError("Chat message cannot be empty."))
    if len(text) > MAX_MESSAGE_LENGTH:
        raise project_manager_error(
            ValueError(
                f"Chat message is too long "
                f"(max {MAX_MESSAGE_LENGTH} characters)."
            )
        )
    return text


# ============================================================
# LIST AGENTS
# ============================================================

@router.get("/api/agents")
def list_all_agents(
    request: Request,
):
    """
    Return every runnable agent, from every registered agent root.

    Discovery is the component's single source of truth
    (code.list_agents), so the library and workspace agents
    arrive through one code path. Workspace agents include
    json_path/md_path so the frontend can run or open them directly.
    """

    try:

        return {
            "agents": [agent_payload(a) for a in list_agents()],
        }

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# GET ONE AGENT DEFINITION
# ============================================================

@router.get("/api/agents/{agent_id}")
def get_agent_definition(
    request: Request,
    agent_id: str,
):
    """
    Return one agent's metadata + markdown sections.

    Resolution goes through the loader, so a workspace agent wins over
    a library agent with the same id - the same precedence discovery
    and ``build_agent`` use.
    """

    try:

        definition = load_definition(agent_id)

        found = find_agent(agent_id)
        source = found[0].source if found is not None else "library"

        payload = {
            "source": source,
            "meta": definition["meta"],
            "sections": definition["sections"],
        }

        json_path = _api_path(agent_json_path(agent_id))
        if json_path is not None:
            payload["json_path"] = json_path
            payload["md_path"] = _api_path(agent_md_path(agent_id))

        return payload

    except Exception as error:
        raise project_manager_error(
            ValueError(f"Agent not found: {agent_id} ({error})")
        )


# ============================================================
# RUN ONE AGENT (from agent.json / agent.md or a library id)
# ============================================================

@router.post("/api/agents/run")
def run_single_agent(
    request: Request,
    payload: AgentRunRequest,
):
    """
    Build and run one agent, then log the exchange.

    Body:
        message:   the user's instruction (required).
        json_path/md_path:
                   workspace-relative paths to agent.json + agent.md
                   (e.g. "agents/demo/agent.json"). When given, the agent
                   is built from those files; otherwise agent_id is used.
        agent_id:  agent id (any registered root) to run when json_path is
                   not given.
        model:     optional model override.
    """

    message = _validated_message(payload.message)

    try:

        # Workspace-relative paths must become absolute (and stay inside
        # the workspace) before the engine reads them.
        json_file = _resolve(str(payload.json_path)) if payload.json_path else None
        md_file = _resolve(str(payload.md_path)) if payload.md_path else None

        result = get_runner().run_single_agent(
            message,
            json_path=str(json_file) if json_file else None,
            md_path=str(md_file) if md_file else None,
            agent_id=payload.agent_id or None,
            model=payload.model,
            persist=False,
        )

        entries = result.get("entries") or []

        return {
            "status": "ok",
            "reply": result["reply"],
            "agent_id": result["agent_id"],
            "name": result.get("name", ""),
            "description": result.get("description", ""),
            "model": result.get("model"),
            "tool_events": result.get("tool_events") or [],
            "entry": entries[0] if entries else None,
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(f"Agent definition not found: {error}")
        )

    except ValueError as error:

        raise project_manager_error(error)

    except Exception as error:

        raise project_manager_error(error)
