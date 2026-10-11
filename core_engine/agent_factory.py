import json
from pathlib import Path
from core_engine.runtime import AgentProfile

AGENTS_ROOT = Path(__file__).resolve().parent.parent / "workspace" / "agents"
CODEBUILDER_AGENTS_ROOT = Path(__file__).resolve().parent.parent / "codebuilder" / "agents"
AGENT_ENVIRONMENTS = {
    "workspace": AGENTS_ROOT,
    "codebuilder": CODEBUILDER_AGENTS_ROOT,
}

AGENT_MD_TEMPLATE = """# {name}

## role
You are {name}, a Novous workspace agent. You act as a specialist in your domain and own every request end to end. Always think before answering and verify any claim you reuse.

## purpose
{purpose}

## boundaries
- Stay within the scope described in your purpose.
- Do not fabricate facts, citations, or tool results.
- Treat the workspace directory as the default destination for files. File tool paths are relative to the workspace root: use a bare filename for a file in its root, and do not add a `workspace/` prefix.
- For file requests, use write_file with the requested content; use create_file only for an intentionally empty file.
- Treat tool errors as failures, never as success. Claim a file was created or updated only after the write tool reports success.
- Never share secrets, credentials, or private user data.
- Report errors honestly instead of guessing.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use bullet lists for three or more items, use markdown headings for long responses, and keep every reply concise.
"""


def parse_markdown_sections(md_text: str) -> dict:
    sections = {}
    current_title = None
    current_lines = []

    for line in md_text.splitlines():
        if line.startswith("## "):
            if current_title:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip().lower()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title:
        sections[current_title] = "\n".join(current_lines).strip()

    return sections


def _get_agents_root(environment: str = "workspace") -> Path:
    try:
        return AGENT_ENVIRONMENTS[environment]
    except KeyError as exc:
        raise ValueError(f"Unknown agent environment: {environment}") from exc


def find_agent_dir(agent_id: str, environment: str = "workspace") -> Path | None:
    clean = str(agent_id or "").strip().replace("\\", "/")
    if not clean or "/" in clean or clean in (".", ".."):
        return None
    candidate = _get_agents_root(environment) / clean
    if candidate.is_dir() and (candidate / "agent.json").is_file():
        return candidate
    return None


def load_agent_definition(json_path: Path, md_path: Path) -> AgentProfile:
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    sections = parse_markdown_sections(md_text)

    profile = AgentProfile(
        id=meta.get("id", json_path.parent.name),
        name=meta.get("name", json_path.parent.name),
        description=meta.get("description", ""),
        mode=meta.get("mode", "agent"),
        role=sections.get("role", ""),
        purpose=sections.get("purpose", ""),
        boundaries=sections.get("boundaries", ""),
        model=meta.get("model", ""),
        tools=list(meta.get("tools", []) or []),
        extras=sections
    )

    prompt_parts = [
        f"You are {profile.name}.",
        f"ROLE:\n{profile.role}" if profile.role else "",
        f"PURPOSE:\n{profile.purpose}" if profile.purpose else "",
        f"BOUNDARIES:\n{profile.boundaries}" if profile.boundaries else "",
    ]

    for title, content in sections.items():
        if title not in ("role", "purpose", "boundaries") and content:
            prompt_parts.append(f"{title.upper()}:\n{content}")

    profile.system_prompt = "\n\n".join(p for p in prompt_parts if p)
    return profile


def load_agent(agent_id: str, environment: str = "workspace") -> AgentProfile:
    agent_dir = find_agent_dir(agent_id, environment)
    if not agent_dir:
        raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
    return load_agent_definition(agent_dir / "agent.json", agent_dir / "agent.md")


def list_agents(environment: str = "workspace") -> list[dict]:
    agents_root = _get_agents_root(environment)
    agents = []
    if not agents_root.is_dir():
        return agents
    for child in sorted(agents_root.iterdir(), key=lambda p: p.name.lower()):
        json_path = child / "agent.json"
        if not json_path.is_file():
            continue
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        agents.append({
            "id": meta.get("id", child.name),
            "name": meta.get("name", child.name),
            "description": meta.get("description", ""),
            "mode": meta.get("mode", "chat"),
            "model": meta.get("model", ""),
            "squad": meta.get("squad", ""),
            "tools": meta.get("tools", []),
            "has_markdown": (child / "agent.md").is_file(),
            "environment": environment,
        })
    return agents
