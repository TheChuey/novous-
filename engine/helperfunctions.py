"""engine/helperfunctions.py

Pure supporting utilities for the engine: Ollama tool-schema conversion
and the saved chat-session text format (serialize / parse / shape).

No state, no workflows.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .data import MAX_TITLE_LENGTH, SAFE_ID


def _ollama_tool_schema(tool) -> dict:
    """Convert a LangChain input schema into Ollama's function-tool format."""
    args_schema = getattr(tool, "args_schema", None)
    if args_schema is None:
        raise TypeError(f"Tool '{getattr(tool, 'name', tool)}' has no argument schema.")
    schema = args_schema.model_json_schema()
    properties = {}
    for name, value in (schema.get("properties") or {}).items():
        prop = {
            key: value[key]
            for key in ("type", "description", "enum", "items")
            if key in value
        }
        properties[name] = prop
    parameters = {"type": "object", "properties": properties}
    if schema.get("required"):
        parameters["required"] = schema["required"]
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters,
        },
    }


# ============================================================
# ID VALIDATION
# ============================================================

def _safe_id(value: str, kind: str) -> str:
    """
    Validate an id used as a single path segment.

    Agent and session ids both become directory or file names, so
    anything that could climb out of the sessions directory is
    refused rather than sanitized.
    """

    if not value or not SAFE_ID.match(value):
        raise ValueError(
            f"Invalid {kind}: {value!r}. Use letters, numbers, "
            "underscore or dash only."
        )

    return value


def _new_session_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


# ============================================================
# SESSION SHAPING
# ============================================================

def _derive_title(entries: list[dict]) -> str:
    """Title from the first user turn, else a timestamp."""
    for entry in entries:
        if entry.get("sender") == "user":
            text = " ".join(str(entry.get("message", "")).split())
            if text:
                if len(text) > MAX_TITLE_LENGTH:
                    text = text[: MAX_TITLE_LENGTH - 1].rstrip() + "\u2026"
                return text
    return "Session " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _summary(record: dict) -> dict:
    """List-view projection of a stored session."""
    return {
        "id": record.get("id", ""),
        "agent_id": record.get("agent_id", ""),
        "title": record.get("title", ""),
        "created": record.get("created", ""),
        "entry_count": len(record.get("entries", [])),
    }


def _serialize_session(record: dict) -> str:
    """Write one readable text transcript with length-delimited messages."""
    display_title = " ".join(str(record.get("title") or "Chat session").split())
    metadata = {
        key: record.get(key, "")
        for key in ("id", "agent_id", "title", "created")
    }
    lines = [
        f"# {display_title}",
        "",
        "<!-- session: " + json.dumps(metadata, ensure_ascii=False) + " -->",
        "",
    ]
    for entry in record.get("entries", []):
        message = str(entry.get("message", ""))
        entry_metadata = {
            "sender": entry.get("sender", ""),
            "agent": entry.get("agent"),
            "ts": entry.get("ts", ""),
            "length": len(message),
        }
        who = (
            "You"
            if entry_metadata["sender"] == "user"
            else entry_metadata.get("agent") or "Agent"
        )
        lines.extend([
            f"## {who}",
            "<!-- entry: " + json.dumps(entry_metadata, ensure_ascii=False) + " -->",
            message,
            "",
        ])
    return "\n".join(lines)


def _parse_session_text(text: str) -> dict:
    """Parse the app's readable text session format without losing message text."""
    lines = text.splitlines(keepends=True)
    if len(lines) < 3 or not lines[2].startswith("<!-- session: ") or not lines[2].rstrip().endswith(" -->"):
        raise ValueError("Saved chat session has an invalid header.")

    metadata_text = lines[2].rstrip()[len("<!-- session: "):-len(" -->")]
    record = json.loads(metadata_text)
    content = "".join(lines[3:])
    entries = []
    position = 0

    while position < len(content):
        while position < len(content) and content[position] == "\n":
            position += 1
        if position >= len(content):
            break
        if content.startswith("## ", position):
            heading_end = content.find("\n", position)
            if heading_end < 0:
                raise ValueError("Saved chat session has an incomplete message heading.")
            position = heading_end + 1
        marker_end = content.find("\n", position)
        if marker_end < 0:
            raise ValueError("Saved chat session has an incomplete message header.")
        marker = content[position:marker_end]
        prefix, suffix = "<!-- entry: ", " -->"
        if not marker.startswith(prefix) or not marker.endswith(suffix):
            raise ValueError("Saved chat session has an invalid message header.")
        entry_metadata = json.loads(marker[len(prefix):-len(suffix)])
        length = entry_metadata.get("length")
        if not isinstance(length, int) or length < 0:
            raise ValueError("Saved chat session has an invalid message length.")
        body_start = marker_end + 1
        body_end = body_start + length
        if body_end > len(content):
            raise ValueError("Saved chat session message is truncated.")
        message = content[body_start:body_end]
        if body_end < len(content) and content[body_end] == "\n":
            body_end += 1
        entries.append({
            "sender": entry_metadata.get("sender"),
            "agent": entry_metadata.get("agent"),
            "ts": entry_metadata.get("ts", ""),
            "message": message,
        })
        position = body_end

    record["entries"] = entries
    return record
