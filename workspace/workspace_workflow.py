"""Agent Scaffolding & Squad Routing."""

import json
import re
from pathlib import Path

from core_engine.agent_factory import AGENTS_ROOT, AGENT_MD_TEMPLATE

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

DEFAULT_TOOLS = [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "project_status",
]


def _validate_id(agent_id: str) -> str:
    agent_id = agent_id.strip().lower()
    if not _ID_PATTERN.match(agent_id):
        raise ValueError(
            "agent_id must be lowercase letters, digits, '-' or '_', starting alphanumeric, max 64 chars.")
    return agent_id


def scaffold_agent(agent_id: str, name: str, description: str = "",
                   mode: str = "chat", squad: str = "") -> dict:
    """Create agent.json + agent.md in the canonical workspace/agents/ home."""
    agent_id = _validate_id(agent_id)
    if not name.strip():
        raise ValueError("Agent name must not be empty.")

    agent_dir = AGENTS_ROOT / agent_id
    if agent_dir.exists():
        raise ValueError(f"Agent already exists: {agent_id}")

    agent_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": agent_id,
        "name": name.strip(),
        "description": description.strip(),
        "mode": mode if mode in ("chat", "agent") else "chat",
        "model": "qwen2.5-coder:latest",
        "squad": squad.strip(),
        "tools": list(DEFAULT_TOOLS) if mode == "agent" else [],
    }

    purpose = description.strip() or f"Serve as the {name.strip()} for this workspace."
    purpose += " Act strategically toward that goal and always deliver a clear, structured result."
    (agent_dir / "agent.md").write_text(
        AGENT_MD_TEMPLATE.format(name=name.strip(), purpose=purpose), encoding="utf-8")
    (agent_dir / "agent.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    return {"created": True, "agent_id": agent_id, "path": f"agents/{agent_id}",
            "agent": meta}


def delete_agent(agent_id: str) -> dict:
    agent_id = _validate_id(agent_id)
    agent_dir = AGENTS_ROOT / agent_id
    if not agent_dir.is_dir():
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    for child in agent_dir.iterdir():
        if child.is_file():
            child.unlink()
        else:
            raise ValueError(f"Refusing to delete nested directory in agent folder: {child.name}")
    agent_dir.rmdir()
    return {"deleted": True, "agent_id": agent_id}


def save_agent_meta(agent_id: str, meta: dict) -> dict:
    """Persist edited agent.json metadata (keeps id stable)."""
    agent_id = _validate_id(agent_id)
    agent_dir = AGENTS_ROOT / agent_id
    if not agent_dir.is_dir():
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    meta = dict(meta)
    meta["id"] = agent_id
    (agent_dir / "agent.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"saved": True, "agent": meta}


def agents_for_squad(squad: str) -> list[dict]:
    """Squad routing: canonical agents filtered by their squad field."""
    agents = []
    if not AGENTS_ROOT.is_dir():
        return agents
    for child in sorted(AGENTS_ROOT.iterdir()):
        json_path = child / "agent.json"
        if not json_path.is_file():
            continue
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("squad", "") == squad:
            agents.append(meta)
    return agents
