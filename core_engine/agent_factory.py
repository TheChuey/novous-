import json
from pathlib import Path
from core_engine.runtime import AgentProfile

REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_ROOT = REPO_ROOT / "library"
AGENT_ENVIRONMENTS = {
    "workspace": LIBRARY_ROOT,
    "codebuilder": LIBRARY_ROOT,
    "prompt-creation": LIBRARY_ROOT,
}

AGENT_MD_TEMPLATE = """# {name}

## role
You are {name}, a Novous2 workspace agent. You act as a specialist in your domain and own every request end to end. Always think before answering and verify any claim you reuse.

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


def _coerce_yaml_scalar(value: str):
    text = (value or "").strip()
    if text == "":
        return ""
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "~"}:
        return None
    if text.startswith(('"', "'")) and text.endswith(('"', "'")):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        candidate = text.replace("'", '"')
        try:
            return json.loads(candidate)
        except Exception:
            return text
    if text.startswith("{") and text.endswith("}"):
        candidate = text.replace("'", '"')
        try:
            return json.loads(candidate)
        except Exception:
            return text
    if text.startswith("0") and text.count(".") == 0:
        try:
            return int(text)
        except ValueError:
            pass
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def parse_yaml_frontmatter(raw_text: str) -> dict:
    if raw_text is None:
        return {}
    stripped = raw_text.lstrip()
    if not stripped.startswith("---"):
        return {}
    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}

    data: dict[str, object] = {}
    current_key: str | None = None
    current_list: list | None = None
    nested_map: dict | None = None

    for line in lines[1:end_index]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indentation = len(line) - len(line.lstrip(" "))
        stripped_line = line.strip()

        if indentation == 0:
            key, sep, value = stripped_line.partition(":")
            if not sep:
                continue
            key = key.strip()
            value = value.strip()
            current_key = key
            current_list = None
            nested_map = None
            if value == "":
                data[key] = []
                current_list = data[key]
            else:
                data[key] = _coerce_yaml_scalar(value)
                current_key = None
            continue

        if current_key is None:
            continue

        if stripped_line.startswith("- "):
            item = stripped_line[2:].strip()
            if item.endswith(":"):
                item_key = item[:-1].strip()
                entry = {item_key: {}}
                if not isinstance(data[current_key], list):
                    data[current_key] = []
                data[current_key].append(entry)
                nested_map = entry[item_key]
                current_list = None
            else:
                if not isinstance(data[current_key], list):
                    data[current_key] = []
                data[current_key].append(_coerce_yaml_scalar(item))
                nested_map = None
                current_list = None
            continue

        if nested_map is not None and ":" in stripped_line:
            nested_key, nested_value = stripped_line.split(":", 1)
            nested_key = nested_key.strip()
            nested_value = nested_value.strip()
            nested_map[nested_key] = _coerce_yaml_scalar(nested_value) if nested_value else ""
            continue

        if current_list is not None and ":" in stripped_line:
            list_key, list_value = stripped_line.split(":", 1)
            list_key = list_key.strip()
            list_value = list_value.strip()
            if list_key and isinstance(current_list, list):
                current_list.append({list_key: _coerce_yaml_scalar(list_value) if list_value else ""})

    return data


def _normalize_agent_id(agent_id: str) -> str:
    clean = str(agent_id or "").strip().replace("\\", "/")
    if not clean or clean in (".", "..") or "/" in clean:
        raise ValueError(f"Invalid agent id: {agent_id!r}")
    return clean


def _get_agents_root(environment: str = "workspace") -> Path:
    try:
        return AGENT_ENVIRONMENTS[environment]
    except KeyError as exc:
        raise ValueError(f"Unknown agent environment: {environment}") from exc


def find_agent_file(agent_id: str, environment: str = "workspace") -> Path | None:
    clean = _normalize_agent_id(agent_id)
    candidate = _get_agents_root(environment) / f"{clean}.md"
    if candidate.is_file():
        return candidate
    return None


def _library_file_for(agent_id: str) -> Path:
    clean = _normalize_agent_id(agent_id)
    return LIBRARY_ROOT / f"{clean}.md"


def _read_agent_markdown(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if not text.startswith("---"):
        return "", text.strip("\n")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text.strip("\n")
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return "", text.strip("\n")
    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1:]).strip("\n")
    return frontmatter, body


def load_agent_definition_from_md(md_path: Path) -> AgentProfile:
    if not md_path.is_file():
        raise FileNotFoundError(f"Agent markdown file not found: {md_path}")
    raw_text = md_path.read_text(encoding="utf-8")
    frontmatter = parse_yaml_frontmatter(raw_text)
    body = raw_text
    if raw_text.startswith("---"):
        _, body = _read_agent_markdown(md_path)

    sections = parse_markdown_sections(body)
    meta = dict(frontmatter)
    agent_id = meta.get("id") or md_path.stem
    profile = AgentProfile(
        id=str(agent_id),
        name=str(meta.get("name") or md_path.stem.replace("-", " ").title()),
        description=str(meta.get("description") or ""),
        mode=str(meta.get("mode") or "agent"),
        role=sections.get("role", ""),
        purpose=sections.get("purpose", ""),
        boundaries=sections.get("boundaries", ""),
        model=str(meta.get("model") or ""),
        tools=list(meta.get("tools") or []),
        extras=sections,
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

    if profile.mode != "agent" or not profile.tools:
        prompt_parts.append(
            "NO TOOLS:\nYou have no tools, functions, or file access. Never output function "
            "calls, tool-call JSON, or claims of creating, writing, or saving files. "
            "Answer directly in plain Markdown text."
        )

    profile.system_prompt = "\n\n".join(p for p in prompt_parts if p)
    return profile


def load_agent(agent_id: str, environment: str = "workspace") -> AgentProfile:
    clean = _normalize_agent_id(agent_id)
    _get_agents_root(environment)
    library_file = find_agent_file(clean, environment)
    if library_file:
        metadata = parse_yaml_frontmatter(library_file.read_text(encoding="utf-8"))
        if metadata.get("environment", "workspace") == environment:
            return load_agent_definition_from_md(library_file)
    raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")


def list_agents(environment: str | None = None) -> list[dict]:
    seen: set[str] = set()
    agents: list[dict] = []
    roots: list[Path] = [LIBRARY_ROOT]

    if environment is not None:
        roots = [_get_agents_root(environment)]

    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if child.suffix.lower() != ".md":
                continue
            agent_id = child.stem
            if agent_id in seen:
                continue
            try:
                profile = load_agent_definition_from_md(child)
                metadata = parse_yaml_frontmatter(child.read_text(encoding="utf-8"))
            except Exception:
                continue
            agent_environment = metadata.get("environment", "workspace")
            if environment is not None and agent_environment != environment:
                continue
            seen.add(agent_id)
            agents.append({
                "id": profile.id,
                "name": profile.name,
                "description": profile.description,
                "mode": profile.mode,
                "model": profile.model,
                "squad": "",
                "tools": profile.tools,
                "has_markdown": True,
                "environment": agent_environment,
                "path": child.relative_to(REPO_ROOT).as_posix(),
            })

    return agents
