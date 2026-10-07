"""agents/logic.py

Definition loading and persistence workflows.

Locates, reads, parses and (when asked) writes one agent definition -
the find / read / parse / return half of the lifecycle. It never runs
agents; building belongs to code.build_agent.

An agent folder contains:
    agent.json  - metadata/configuration (id, name, mode, tools, model)
    agent.md    - behavior sections (## role, ## purpose, ## boundaries, ...)

load_definition() returns:
    {"meta": {...agent.json...}, "sections": {...parsed markdown sections...}}

Where agents live is decided by the root registry in code.py: the component
ships with ``agents/`` (the library), and a host application may register
more roots (the Project Manager registers ``workspace/agents/``). Lookups
here search every registered root, so an agent is found by id regardless
of which root owns it.
"""

from __future__ import annotations

import json
from pathlib import Path

from .code import find_agent, register_agent_root, unregister_agent_root
from .data import (
    AGENT_LIBRARY_DIR,
    AGENT_MD_FILE,
    AGENT_META_FILE,
    LIBRARY_ROOT_NAME,
    AgentNotFoundError,
    AgentRoot,
)
from .helperfunctions import _clean_body, _parse_sections

__all__ = [
    "AGENT_LIBRARY_DIR",
    "AGENT_MD_FILE",
    "AGENT_META_FILE",
    "AgentNotFoundError",
    "AgentRoot",
    "LIBRARY_ROOT_NAME",
    "agent_dir",
    "agent_json_path",
    "agent_md_path",
    "agent_root",
    "load_definition",
    "load_definition_from_paths",
    "register_agent_root",
    "save_markdown",
    "save_meta",
    "save_tests",
    "unregister_agent_root",
]


def agent_dir(agent_id: str) -> Path:
    """The folder for an agent id inside the highest-precedence root.

    Searches every registered root (see code.py): first the literal
    ``<root>/<agent_id>`` path, then each root's folders matched by
    their ``agent.json`` ``id`` field, so folder names and ids may differ.
    Falls back to the literal library path so callers that create folders
    (``save_markdown``) still work for brand-new agents.
    """
    found = find_agent(agent_id)
    if found is not None:
        return found[1]
    return AGENT_LIBRARY_DIR / agent_id


def agent_root(agent_id: str) -> AgentRoot | None:
    """The registered root that owns ``agent_id``, or None."""
    found = find_agent(agent_id)
    return found[0] if found is not None else None


def agent_json_path(agent_id: str) -> str | None:
    """Workspace-relative ``agent.json`` path for a registered agent."""
    found = find_agent(agent_id)
    if found is None:
        return None
    root, directory = found
    return root.json_path(directory)


def agent_md_path(agent_id: str) -> str | None:
    """Workspace-relative ``agent.md`` path for a registered agent."""
    found = find_agent(agent_id)
    if found is None:
        return None
    root, directory = found
    return root.md_path(directory)


def _resolve_agent_dir(agent_id: str) -> Path | None:
    """Find the on-disk folder for an agent by id across all roots.

    Returns ``None`` when nothing matches so callers can fall back to the
    literal path (which preserves the existing create-folder semantics for
    ``save_markdown`` on genuinely new agents).
    """
    found = find_agent(agent_id)
    return found[1] if found is not None else None


def save_meta(agent_id: str, meta: dict) -> dict:
    """Merge `meta` into the agent's agent.json (top-level keys only) and
    write it back pretty-printed. Unknown keys survive untouched."""
    agent_path = agent_dir(agent_id)
    meta_file = agent_path / AGENT_META_FILE
    if not meta_file.exists():
        raise AgentNotFoundError(f"Agent config not found: {meta_file}")

    stored = json.loads(meta_file.read_text(encoding="utf-8"))
    stored.update(meta)
    meta_file.write_text(
        json.dumps(stored, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return stored


def save_markdown(agent_id: str, markdown: str) -> str:
    """Write the agent's behavior prose to agent.md."""
    agent_path = agent_dir(agent_id)
    agent_path.mkdir(parents=True, exist_ok=True)
    md_file = agent_path / AGENT_MD_FILE
    md_file.write_text(str(markdown), encoding="utf-8")
    return str(markdown)


def save_tests(agent_id: str, tests: list) -> list:
    """Store the agent's own chat tests under agent.json#tests.

    Tests are scoped by their location, so any stored `agentId` is dropped;
    ensures every test keeps a unique id.
    """
    normalized = []
    for test in tests or []:
        if not isinstance(test, dict):
            continue
        entry = dict(test)
        entry.pop("agentId", None)
        if not entry.get("id"):
            entry["id"] = "t-" + json.dumps(entry, sort_keys=True)[:8]
        normalized.append(entry)
    save_meta(agent_id, {"tests": normalized})
    return normalized


def load_definition(agent_id: str) -> dict:
    """Load one agent definition from the registered roots (library fallback).

    Returns {"meta": dict, "sections": dict}. Raises AgentNotFoundError
    when the folder or either required file is missing/unreadable.
    """
    agent_path = _resolve_agent_dir(agent_id)
    if agent_path is None:
        agent_path = AGENT_LIBRARY_DIR / agent_id
    json_file = agent_path / AGENT_META_FILE
    md_file = agent_path / AGENT_MD_FILE

    if not json_file.exists():
        raise AgentNotFoundError(f"Agent not found: {json_file}")
    if not md_file.exists():
        raise AgentNotFoundError(f"Agent not found: {md_file}")

    try:
        meta = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentNotFoundError(f"Agent config unreadable: {json_file} ({exc})")

    try:
        md_text = md_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentNotFoundError(f"Agent markdown unreadable: {md_file} ({exc})")

    raw_sections = _parse_sections(md_text)
    # The '# Title' line before the first section is ignored; every
    # '## section' body gets whitespace/separator cleanup.
    sections = {name: _clean_body(body) for name, body in raw_sections.items()}

    return {"meta": meta, "sections": sections}


def load_definition_from_paths(
    json_path: str | Path,
    md_path: str | Path,
) -> dict:
    """Load one agent definition from explicit agent.json + agent.md paths.

    This is the headless entry point used when an agent's definition comes
    from arbitrary locations (e.g. ad-hoc agents built by run_single_agent)
    instead of the bundled library.

    Returns {"meta": dict, "sections": dict}. Raises AgentNotFoundError
    when either file is missing/unreadable.
    """
    json_file = Path(json_path)
    md_file = Path(md_path)

    if not json_file.exists():
        raise AgentNotFoundError(f"Agent config not found: {json_file}")
    if not md_file.exists():
        raise AgentNotFoundError(f"Agent markdown not found: {md_file}")

    try:
        meta = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentNotFoundError(f"Agent config unreadable: {json_file} ({exc})")

    try:
        md_text = md_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentNotFoundError(f"Agent markdown unreadable: {md_file} ({exc})")

    raw_sections = _parse_sections(md_text)
    sections = {name: _clean_body(body) for name, body in raw_sections.items()}

    return {"meta": meta, "sections": sections}
