"""Workspace Doorway: Python API & FastAPI Router (/api/project, /api/health, squads)."""

import json
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from workspace import squad_manager, workspace_workflow

router = APIRouter()

PROJECT_FILE = Path(__file__).resolve().parent / "project.json"
START_TIME = time.time()


def _default_project() -> dict:
    return {
        "name": "Novous Workspace",
        "version": "1.0.0",
        "description": "",
        "default_model": "qwen2.5-coder:latest",
        "squad_root": "",
        "active_agent": "",
    }


def get_project_state() -> dict:
    """Doorway function: read workspace/project.json."""
    if not PROJECT_FILE.is_file():
        return _default_project()
    try:
        return json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _default_project()


def save_project_state(state: dict) -> dict:
    """Doorway function: persist workspace/project.json."""
    current = get_project_state()
    current.update({k: v for k, v in state.items() if v is not None})
    PROJECT_FILE.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return current


def get_health() -> dict:
    """Doorway function: aggregated system health."""
    ollama_ok = False
    ollama_detail = "unreachable"
    try:
        import ollama
        ollama.list()
        ollama_ok = True
        ollama_detail = "connected"
    except Exception as exc:
        ollama_detail = str(exc)

    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": {"reachable": ollama_ok, "detail": ollama_detail},
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": time.time(),
    }


class ProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    default_model: str | None = None
    active_agent: str | None = None
    squad_root: str | None = None


class ScaffoldRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    mode: str = "chat"
    squad: str = ""


class SquadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: str = ""


class SquadRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    new_name: str = Field(..., min_length=1, max_length=64)


# --- Project & health ------------------------------------------------------

@router.get("/api/project")
def api_get_project():
    state = get_project_state()
    from core_engine.agent_factory import list_agents
    state["agents"] = list_agents()
    state["squads"] = squad_manager.list_squads()
    return state


@router.post("/api/project")
def api_save_project(req: ProjectRequest):
    try:
        return save_project_state(req.model_dump())
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/health")
def api_health():
    return get_health()


# --- Agent scaffolding (workspace owns the canonical storage) --------------

@router.post("/api/workspace/agents/scaffold")
def api_scaffold_agent(req: ScaffoldRequest):
    try:
        return workspace_workflow.scaffold_agent(
            req.agent_id, req.name, req.description, req.mode, req.squad)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/api/workspace/agents/{agent_id}")
def api_update_agent(agent_id: str, req: dict):
    try:
        return workspace_workflow.save_agent_meta(agent_id, req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/workspace/agents/{agent_id}/squad")
def api_agents_by_squad(squad: str = ""):
    return {"squad": squad, "agents": workspace_workflow.agents_for_squad(squad)}


# --- Squads ----------------------------------------------------------------

@router.get("/api/squads")
def api_list_squads():
    return {"squads": squad_manager.list_squads()}


@router.post("/api/squads/create")
def api_create_squad(req: SquadRequest):
    try:
        return squad_manager.create_squad(req.name, req.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/squads/rename")
def api_rename_squad(req: SquadRenameRequest):
    try:
        return squad_manager.rename_squad(req.name, req.new_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/squads/delete")
def api_delete_squad(req: SquadRequest):
    try:
        return squad_manager.delete_squad(req.name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
