"""configuration/data.py

Schemas, dataclasses, constants, JSON loaders/savers and session state.

Component: Models & Environment Management. models.json lives beside
this file; loaders/savers for it are here, everything else in the
component reads through them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

#: This component's directory; models.json sits next to it.
CONFIG_DIR = Path(__file__).resolve().parent

MODELS_FILE = CONFIG_DIR / "models.json"


def load_models() -> list[dict[str, Any]]:
    """The raw model entries in models.json ([] when absent/unreadable)."""

    try:
        data = json.loads(MODELS_FILE.read_text(encoding="utf-8"))
        return data.get("models") or []
    except (OSError, json.JSONDecodeError):
        return []


def save_models(models: list[dict[str, Any]]) -> None:
    """Write the model list to models.json (creates the file)."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_FILE.write_text(
        json.dumps({"models": models}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
