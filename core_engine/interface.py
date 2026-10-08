"""Core Engine Doorway: Python API & FastAPI Router (/api/chat, /api/agents, /api/tools)."""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core_engine import agent_factory, tool_catalog
from core_engine.runtime import Agent, AgentProfile

router = APIRouter()

# In-memory conversation sessions, keyed by agent id.
SESSIONS: dict[str, Agent] = {}


class CreateAgentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    mode: str = "chat"
    squad: str = ""


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent_id: str
    model: str = "qwen2.5-coder:latest"
    session_id: str | None = None


def run_single_agent(agent_id: str, message: str, model: str | None = None,
                     session_id: str | None = None) -> dict:
    """Doorway function: run one agent turn through the Think-Act-Observe loop."""
    try:
        profile = agent_factory.load_agent(agent_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    session_key = session_id or agent_id
    agent = SESSIONS.get(session_key)
    if agent is None:
        tools = tool_catalog.get_tools(profile.tools) if profile.mode == "agent" else []
        agent = Agent(model=model or profile.model or None, tools=tools, profile=profile,
                      session=session_key)
        SESSIONS[session_key] = agent

    agent.tool_events = []
    try:
        reply = agent.think(message)
    except Exception as exc:  # Ollama down / model missing -> graceful error reply
        reply = (f"[engine] Could not reach the model runtime: {exc}\n"
                 f"Start Ollama (e.g. `ollama serve`) and pull the model "
                 f"`{model or profile.model or 'qwen2.5-coder:latest'}`, then retry.")
        if agent.messages and agent.messages[-1].get("role") == "user":
            agent.messages.pop()

    return {
        "reply": reply,
        "agent_id": agent_id,
        "session_id": session_key,
        "model": agent.model,
        "tool_events": list(agent.tool_events),
    }


def list_agents() -> list[dict]:
    """Doorway function: list all canonical agents from workspace/agents/."""
    return agent_factory.list_agents()


def reset_session(session_id: str) -> bool:
    return SESSIONS.pop(session_id, None) is not None


@router.get("/api/agents")
def api_list_agents():
    return {"agents": list_agents()}


@router.post("/api/agents/create")
def api_create_agent(req: CreateAgentRequest):
    from workspace import workspace_workflow
    try:
        result = workspace_workflow.scaffold_agent(
            agent_id=req.agent_id.strip(),
            name=req.name.strip(),
            description=req.description.strip(),
            mode=req.mode if req.mode in ("chat", "agent") else "chat",
            squad=req.squad.strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.delete("/api/agents/{agent_id}")
def api_delete_agent(agent_id: str):
    from workspace import workspace_workflow
    try:
        return workspace_workflow.delete_agent(agent_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/chat")
def api_chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    return run_single_agent(req.agent_id, req.message.strip(), req.model, req.session_id)


@router.post("/api/chat/reset")
def api_chat_reset(session_id: str):
    return {"reset": reset_session(session_id)}


@router.get("/api/tools")
def api_tools():
    return {"tools": tool_catalog.list_tools(),
            "providers": tool_catalog.PROVIDER_BINDINGS}


def list_models() -> dict:
    """Doorway function: list Ollama models installed on this host."""
    try:
        import ollama
        models = [m.get("model") or m.get("name") for m in ollama.list().get("models", [])]
    except Exception as exc:
        models = []
        error = str(exc)
    return {
        "models": sorted(models),
        "default": "qwen2.5-coder:latest",
        "error": error if not models else None,
    }


@router.get("/api/models")
def api_models():
    return list_models()
