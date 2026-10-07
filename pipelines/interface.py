"""pipelines/interface.py

Public doorway for the multi-agent cascade component.

Exposes the two /api/pipeline routes: read the default step chain plus
every selectable candidate, and run a cascade. Workflow lives in
pipelines.logic; this module only validates, delegates and translates
errors to HTTP.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from project_manager.interface import project_manager_error
from pydantic import BaseModel

from agents.interface import (
    AgentNotFoundError,
    _validated_message,
    agent_payload,
    list_agents,
)
from directory_layout.interface import resolve_project_path
from engine.interface import get_runner

from .code import load_pipeline
from .logic import run_pipeline

__all__ = [
    "PipelineRunRequest",
    "load_pipeline",
    "router",
    "run_agent_pipeline",
    "run_pipeline",
]

router = APIRouter()


class PipelineRunRequest(BaseModel):

    steps: list = []

    message: str

    model: str | None = None


# ============================================================
# PIPELINE OPTIONS
# ============================================================

@router.get("/api/pipeline")
def pipeline_options(
    request: Request,
):
    """
    Return the default step chain (config/pipeline.json) plus every
    selectable step candidate (library + workspace agents).

    The frontend starts with an empty selection and lets the user build an
    ordered, reorderable cascade from these candidates.
    """

    try:

        return {
            "default_steps": load_pipeline(),
            "candidates": [agent_payload(a) for a in list_agents()],
        }

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# RUN PIPELINE (multi-agent cascade)
# ============================================================

@router.post("/api/pipeline")
def run_agent_pipeline(
    request: Request,
    payload: PipelineRunRequest,
):
    """
    Cascade many agents one after another.

    Body:
        steps:   ordered list. Each element is either a library agent id
                 (str) or a dict with workspace-relative json_path + md_path
                 (workspace agent). Every later step receives the original
                 message plus all earlier steps' replies as its input.
        message: the original user request.
        model:   optional model override for every step.

    Returns {"reply", "outputs": [{agent_id, agent_name, output, tools_used}],
    "tool_events"} and logs the exchange.
    """

    message = _validated_message(payload.message)
    steps = list(payload.steps or [])

    if not steps:

        raise project_manager_error(
            ValueError("Pipeline requires at least one step.")
        )

    try:

        normalized: list = []
        for step in steps:
            if isinstance(step, dict):
                if not (step.get("json_path") and step.get("md_path")):
                    raise project_manager_error(
                        ValueError(
                            "Pipeline step dicts need json_path + md_path: "
                            f"{step!r}"
                        )
                    )
                normalized.append({
                    "json_path": str(resolve_project_path(str(step["json_path"]))),
                    "md_path": str(resolve_project_path(str(step["md_path"]))),
                })
            else:
                normalized.append(str(step))

        result = get_runner().run_pipeline(
            message,
            agent_configs=normalized,
            model=payload.model,
            persist=False,
        )

        return {
            "status": "ok",
            "reply": result["reply"],
            "outputs": result["outputs"],
            "tool_events": result["tool_events"],
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(f"Agent definition not found: {error}")
        )

    except ValueError as error:

        raise project_manager_error(error)

    except Exception as error:

        raise project_manager_error(error)
