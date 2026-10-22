"""Agent Scaffolding & Squad Routing."""

import re
from pathlib import Path

from core_engine.agent_factory import AGENT_ENVIRONMENTS, AGENT_MD_TEMPLATE, LIBRARY_ROOT, parse_yaml_frontmatter

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

DEFAULT_TOOLS = [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "project_status",
    "read_agent_memory",
    "search_knowledge_base",
    "list_knowledge_documents",
]

CODEBUILDER_DEFAULT_TOOLS = [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "run_python_code",
    "send_code_to_editor",
    "run_code_in_editor",
    "read_agent_memory",
    "search_knowledge_base",
    "list_knowledge_documents",
]


def _validate_id(agent_id: str, environment: str = "workspace") -> str:
    agent_id = agent_id.strip().lower()
    if not _ID_PATTERN.match(agent_id):
        raise ValueError(
            "agent_id must be lowercase letters, digits, '-' or '_', starting alphanumeric, max 64 chars.")
    if environment not in AGENT_ENVIRONMENTS:
        raise ValueError(f"Unknown agent environment: {environment}")
    return agent_id


def _agent_library_path(agent_id: str) -> Path:
    return LIBRARY_ROOT / f"{agent_id}.md"


def _render_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key in ["id", "name", "description", "mode", "model", "squad", "environment", "environment_name", "version"]:
        if key not in meta:
            continue
        value = meta[key]
        if value in (None, ""):
            continue
        if key == "tools":
            continue
        if isinstance(value, (bool, int, float)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    if "tools" in meta and meta["tools"]:
        lines.append("tools:")
        for tool in meta["tools"]:
            lines.append(f"  - {tool}")
    if "skills" in meta and meta["skills"]:
        lines.append("skills:")
        for skill in meta["skills"]:
            if isinstance(skill, dict):
                for skill_name, config in skill.items():
                    lines.append(f"  - {skill_name}:")
                    if isinstance(config, dict):
                        for nested_key, nested_value in config.items():
                            lines.append(f"      {nested_key}: {nested_value}")
            else:
                lines.append(f"  - {skill}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _read_agent_file(path: Path) -> tuple[dict, str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text.strip("\n")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip("\n")
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        return {}, text.strip("\n")
    frontmatter = parse_yaml_frontmatter(text)
    body = "\n".join(lines[end_index + 1:]).strip("\n")
    return frontmatter, body


def scaffold_agent(agent_id: str, name: str, description: str = "",
                   mode: str = "chat", squad: str = "",
                   environment: str = "workspace",
                   environment_name: str = "") -> dict:
    """Create a single-file agent definition in library/{agent_id}.md."""
    agent_id = _validate_id(agent_id, environment)
    environment_name = " ".join(str(environment_name or "").split())[:64]
    if not name.strip():
        raise ValueError("Agent name must not be empty.")

    library_path = _agent_library_path(agent_id)
    if library_path.exists():
        raise ValueError(f"Agent already exists in library: {agent_id}")

    LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": agent_id,
        "name": name.strip(),
        "description": description.strip(),
        "mode": mode if mode in ("chat", "agent") else "chat",
        "model": "qwen2.5-coder:latest",
        "squad": squad.strip(),
        "tools": (
            list(CODEBUILDER_DEFAULT_TOOLS if environment == "codebuilder" else DEFAULT_TOOLS)
            if mode == "agent" else []
        ),
        "environment": environment,
        "environment_name": environment_name,
        "version": 1,
    }

    purpose = description.strip() or (
        f"Serve as the {name.strip()} for the {environment_name or environment} environment."
    )
    purpose += " Act strategically toward that goal and always deliver a clear, structured result."
    agent_template = AGENT_MD_TEMPLATE
    if environment == "codebuilder":
        agent_template = AGENT_MD_TEMPLATE.replace(
            "Novous workspace agent",
            "Novous CodeBuilder agent",
        )
        if mode == "agent":
            agent_template += """

## codebuilder editor workflow
Whenever you provide or revise Python code, call `send_code_to_editor` with the complete code so it is placed in the active Monaco editor. Also include a fenced `python` code block in your reply so the user can review it and send it manually if needed. When the user asks to run the code, send any changed code first, then call `run_code_in_editor`.
"""

    markdown = agent_template.format(name=name.strip(), purpose=purpose)
    rendered = _render_frontmatter(meta) + "\n" + markdown + "\n"
    library_path.write_text(rendered, encoding="utf-8")

    return {"created": True, "agent_id": agent_id,
            "path": f"library/{agent_id}.md",
            "environment": environment,
            "environment_name": environment_name,
            "agent": meta}


def delete_agent(agent_id: str, environment: str = "workspace") -> dict:
    agent_id = _validate_id(agent_id, environment)
    library_path = _agent_library_path(agent_id)
    if library_path.is_file():
        metadata, _ = _read_agent_file(library_path)
        if metadata.get("environment", "workspace") != environment:
            raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
        library_path.unlink()
        return {"deleted": True, "agent_id": agent_id, "environment": environment, "path": f"library/{agent_id}.md"}
    raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")


def save_agent_meta(agent_id: str, meta: dict) -> dict:
    """Persist edited agent metadata while preserving the markdown body."""
    agent_id = _validate_id(agent_id)
    library_path = _agent_library_path(agent_id)
    if not library_path.is_file():
        raise FileNotFoundError(f"Agent not found: {agent_id}")

    existing_data, body = _read_agent_file(library_path)
    if existing_data.get("environment", "workspace") != "workspace":
        raise FileNotFoundError(f"Agent not found in workspace: {agent_id}")
    merged = dict(existing_data)
    merged.update(meta)
    merged["id"] = agent_id
    library_path.write_text(_render_frontmatter(merged) + "\n" + body.strip("\n") + "\n", encoding="utf-8")
    return {"saved": True, "agent": merged, "path": f"library/{agent_id}.md"}


def agents_for_squad(squad: str) -> list[dict]:
    """Squad routing: canonical agents filtered by their squad field."""
    agents = []
    library_root = LIBRARY_ROOT
    if library_root.is_dir():
        for file in sorted(library_root.glob("*.md")):
            frontmatter, _ = _read_agent_file(file)
            if frontmatter.get("environment", "workspace") == "workspace" and frontmatter.get("squad", "") == squad:
                agents.append({**frontmatter, "path": file.relative_to(Path(__file__).resolve().parent.parent).as_posix()})
    return agents
