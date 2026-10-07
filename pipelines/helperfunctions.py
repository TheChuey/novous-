"""pipelines/helperfunctions.py

Pure supporting utilities for cascades: timestamps and step labelling.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def _iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _step_label(step) -> str:
    # A workspace agent's json_path is .../agents/<name>/agent.json, so the
    # agent FOLDER name (not the file stem "agent") is the readable label.
    if isinstance(step, dict):
        json_file = Path(step.get("json_path", ""))
        folder = json_file.parent.name
        return str(step.get("id") or folder or json_file.stem or "custom")
    return str(step)
