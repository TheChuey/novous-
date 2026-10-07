"""configuration/helperfunctions.py

Pure, stateless supporting utilities.

Component: Models & Environment Management. JSON response shaping for
the model picker; no I/O, no state.
"""

from __future__ import annotations

from typing import Any


def model_entry_shape(model: dict[str, Any]) -> dict[str, Any]:
    """One models.json entry in the /api/models response shape."""

    return {
        "id": model.get("id", ""),
        "name": model.get("name", model.get("id", "")),
        "source": model.get("source", "ollama"),
    }


def models_payload(models: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """The /api/models response body."""

    return {"models": [model_entry_shape(m) for m in models]}


def model_ids(models: list[dict[str, Any]]) -> list[str]:
    """The non-empty ``id`` of each entry, in file order."""

    return [m.get("id") for m in models if m.get("id")]
