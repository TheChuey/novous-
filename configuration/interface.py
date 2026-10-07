"""configuration/interface.py

Public doorway. The sole import surface for outside callers; exposes
public functions and the FastAPI router.

Component: Models & Environment Management. Other components import
*only* this file for model resolution, capability checks, model
discovery/refresh and the /api/models endpoint.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request

from project_manager.interface import project_manager_error

from .code import (
    capabilities,
    config_model_ids,
    installed_model_ids,
    refresh_models,
    scan_models,
    supports_tools,
)
from .data import CONFIG_DIR, MODELS_FILE, load_models
from .helperfunctions import model_entry_shape, model_ids, models_payload
from .logic import resolve_model

__all__ = [
    "CONFIG_DIR",
    "MODELS_FILE",
    "capabilities",
    "config_model_ids",
    "installed_model_ids",
    "list_models",
    "load_models",
    "model_entry_shape",
    "model_ids",
    "models_payload",
    "refresh_models",
    "resolve_model",
    "router",
    "scan_models",
    "supports_tools",
]


def list_models() -> list[dict]:
    """models.json in API shape; [] when the file is absent or unreadable."""

    return [model_entry_shape(m) for m in load_models()]


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


@router.get("/api/models")
def list_models_endpoint(
    request: Request,
):
    """
    Return the models in models.json for the frontend picker.
    Run refresh_models to re-scan installed Ollama models.
    """

    try:
        if MODELS_FILE.exists():
            data = json.loads(MODELS_FILE.read_text(encoding="utf-8"))
            models = data.get("models") or []
        else:
            models = []

        return models_payload(models)

    except Exception as error:
        raise project_manager_error(error)
