"""agents/helperfunctions.py

Pure parsing and meta-reading helpers for the agents component.

No state, no workflows: reading one agent.json, splitting agent.md into
'## sections', and trimming section bodies.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .data import AGENT_MD_FILE, AGENT_META_FILE


def _read_meta(agent_dir) -> dict | None:
    """Parsed agent.json, or None when missing/unreadable/malformed."""
    meta_file = Path(agent_dir) / AGENT_META_FILE
    if not meta_file.exists():
        return None
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return meta if isinstance(meta, dict) else None


def _read_meta_logged(agent_dir) -> dict | None:
    """Parsed agent.json, or None when missing/unreadable/malformed.

    Logs a skip line for unreadable files so the registry can show why a
    folder did not appear in discovery.
    """
    meta_file = Path(agent_dir) / AGENT_META_FILE
    if not meta_file.exists():
        return None
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[REGISTRY] skipping {agent_dir}: unreadable agent.json ({exc})")
        return None
    return meta if isinstance(meta, dict) else None


def _parse_sections(text: str) -> dict:
    """Split agent.md into '## <name>' sections (section name lowercased)."""
    sections = {}
    current = None
    buffer = []
    for line in text.splitlines(keepends=True):
        match = re.match(r"^\s*##\s+(.+?)\s*$", line)
        if match:
            if current is not None:
                sections[current] = "".join(buffer)
            current, buffer = match.group(1).strip().lower(), []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = "".join(buffer)
    return sections


def _clean_body(text: str) -> str:
    """Trim blank lines and '---' separators from the edges of a section body."""
    lines = text.splitlines()
    while lines and (not lines[0].strip() or lines[0].strip() in ("---", "***")):
        lines.pop(0)
    while lines and (not lines[-1].strip() or lines[-1].strip() in ("---", "***")):
        lines.pop()
    return "\n".join(lines).strip("\n")
