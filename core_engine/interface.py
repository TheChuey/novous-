"""Core Engine Doorway: Python API & FastAPI Router (/api/chat, /api/agents, /api/tools)."""

import re
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from core_engine import agent_factory, tool_catalog
from core_engine.runtime import Agent, AgentProfile
from editor.editor_schemas import EditorEventType
from editor.editor_session import manager as editor_session_manager

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


class ExportSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


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
        "tool_stats": agent.tool_stats,
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
async def api_chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    result = await run_in_threadpool(
        run_single_agent, req.agent_id, req.message.strip(), req.model, req.session_id
    )
    for event in result["tool_events"]:
        event_data = {
            "tool": event["tool"],
            "args": event.get("args", {}),
            "status": event["status"],
            "origin": event["origin"],
        }
        if event.get("error") is not None:
            event_data["error"] = event["error"]
        editor_session_manager.publish(
            EditorEventType.TOOL_EXECUTED,
            event["tool"],
            result["session_id"],
            **event_data,
        )
    return result


@router.post("/api/chat/reset")
def api_chat_reset(session_id: str):
    return {"reset": reset_session(session_id)}


@router.post("/api/chat/export")
def api_export_chat_session(req: ExportSessionRequest):
    agent = SESSIONS.get(req.session_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found.")

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    safe_session_id = re.sub(r"[^A-Za-z0-9_.-]", "_", req.session_id).strip("._")
    if not safe_session_id:
        safe_session_id = "session"
    filename = f"novous_{safe_session_id}_{timestamp}.md"
    exported_at = now.strftime("%Y-%m-%d %H:%M:%S")
    agent_name = agent.profile.name or req.session_id

    lines = [
        f"# Novous Chat Session Log — {agent_name}",
        f"**Agent ID:** `{agent.profile.id}` | **Model:** `{agent.model}` | "
        f"**Session Key:** `{req.session_id}`",
        f"**Exported At:** `{exported_at}`",
        "",
        "---",
        "",
        "## Tool Execution Metrics",
        "",
    ]

    if agent.tool_stats:
        lines.extend([
            "| Tool Name | Total Calls | Successes | Errors | Success Rate |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ])
        for tool_name, metrics in agent.tool_stats.items():
            lines.append(
                f"| `{tool_name}` | {metrics['calls']} | {metrics['successes']} | "
                f"{metrics['errors']} | {metrics['success_rate']:.1%} |"
            )
    else:
        lines.append("*No tools executed in this session.*")

    lines.extend(["", "---", "", "## Conversation History", ""])
    for msg in agent.messages:
        role = str(msg.get("role", "unknown")).upper()
        if role == "SYSTEM":
            continue
        content = msg.get("content") or ""
        lines.extend([f"### {role.title()}", "", str(content), ""])

    full_markdown = "\n".join(lines)
    return Response(
        content=full_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
