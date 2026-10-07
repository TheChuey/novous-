"""agents/code.py

Stateless implementation: the agent-root registry, filesystem discovery
and the agent factory.

    build_agent(agent_id, model, bridge)
        -> logic.load_definition()  (agent.md + agent.json, via the roots)
        -> resolve_tools()          (IDs -> Python functions, provider bound)
        -> PromptManager.build()    (sections + tool docstrings -> prompt)
        -> Agent                    (with its own FileSession)

Roots are searched most-recently-registered first, so a workspace agent
shadows a library agent declaring the same id - the precedence loader
and discovery use too, so building and listing can never disagree.

Nothing here is process-wide except the root list itself: each agent gets
its own tools (bound to its own filesystem provider) and its own
FileSession, so two agents can be built and run side by side without
sharing state.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import BaseTool

from engine.interface import Agent, PromptManager
from tools.interface import _replace_func, new_session, resolve_tools

from .data import (
    AGENT_LIBRARY_DIR,
    AGENT_MD_FILE,
    LIBRARY_ROOT_NAME,
    AgentDefinitionError,
    AgentNotFoundError,
    AgentRoot,
    DEFAULT_LIBRARY_DIR,
    _roots,
)
from .helperfunctions import _read_meta, _read_meta_logged

__all__ = [
    "AGENT_LIBRARY_DIR",
    "AgentDefinitionError",
    "AgentNotFoundError",
    "AgentRoot",
    "build_agent",
    "build_agent_from_definition",
    "find_agent",
    "get_agent_meta",
    "list_agents",
    "register_agent_root",
    "replay_history",
    "reset_agent_roots",
    "unregister_agent_root",
]


# ==========================================================================
# ROOT REGISTRY
# ==========================================================================

def register_agent_root(
    name: str,
    path: str | Path,
    source: str | None = None,
) -> AgentRoot:
    """Register (or re-register) an agent root and give it top precedence.

    Args:
        name:    unique key, e.g. ``"workspace"``.
        path:    directory holding one folder per agent.
        source:  value reported as each agent's ``source``; defaults to
                 ``name``.

    Returns:
        The registered :class:`AgentRoot`.
    """
    resolved = Path(path).expanduser().resolve()
    root = AgentRoot(name=name, path=resolved, source=source or name)
    unregister_agent_root(name)
    _roots.append(root)
    return root


def unregister_agent_root(name: str) -> bool:
    """Remove a root by name. Returns True when something was removed."""
    for index, existing in enumerate(_roots):
        if existing.name == name:
            del _roots[index]
            return True
    return False


def agent_roots() -> list[AgentRoot]:
    """Registered roots, highest precedence first."""
    return list(reversed(_roots))


def get_root(name: str) -> AgentRoot | None:
    for root in agent_roots():
        if root.name == name:
            return root
    return None


def reset_agent_roots() -> AgentRoot:
    """Drop every root except the built-in library root (used by tests)."""
    _roots.clear()
    return register_agent_root(
        LIBRARY_ROOT_NAME, DEFAULT_LIBRARY_DIR, source="library"
    )


# The component always has its bundled library available.
reset_agent_roots()


# ==========================================================================
# RESOLUTION
# ==========================================================================

def find_agent(agent_id: str) -> tuple[AgentRoot, Path] | None:
    """Locate an agent folder by id across every registered root.

    Two strategies per root, tried highest precedence first:
        1. Literal: ``<root>/<agent_id>`` is a directory.
        2. Scan: read ``agent.json`` in each child folder and match its
           ``id`` field, so folder names and ids may differ (e.g. the
           ``Planner`` folder declaring id ``feature_planner_agent``).

    Returns:
        ``(root, agent_dir)`` for the winning match, else ``None``.
    """
    if not agent_id:
        return None

    for root in agent_roots():
        literal = root.path / agent_id
        if literal.is_dir():
            return root, literal

    for root in agent_roots():
        for child in root.agent_dirs():
            meta = _read_meta(child)
            if meta is not None and meta.get("id") == agent_id:
                return root, child

    return None


# ==========================================================================
# DISCOVERY (registry)
# ==========================================================================

def list_agents() -> list[dict]:
    """One summary per discovered agent, highest-precedence root first.

        [{"id", "name", "description", "mode", "model", "tools",
          "source", "json_path", "md_path", "complete"}, ...]

    Deduplicated by id: the first root that provides an id wins, and
    lower-precedence roots with the same id are skipped. An agent whose
    agent.json parsed but whose agent.md is missing is still returned,
    with ``complete: False``, so the UI can show it as a work in
    progress instead of it silently disappearing.
    """
    summaries: list[dict] = []
    claimed: set[str] = set()

    for root in agent_roots():
        for agent_dir in root.agent_dirs():
            meta = _read_meta_logged(agent_dir)
            if meta is None:
                # No readable agent.json: not an agent folder. A folder
                # with no meta at all is silently ignored, exactly as
                # before, so a half-created folder cannot break the list.
                continue

            agent_id = str(meta.get("id") or agent_dir.name)
            if agent_id in claimed:
                # A higher-precedence root already owns this id.
                continue
            claimed.add(agent_id)

            md_file = agent_dir / AGENT_MD_FILE
            summaries.append({
                "id": agent_id,
                "name": meta.get("name") or agent_dir.name,
                "description": meta.get("description", "") or "",
                "mode": meta.get("mode", "chat") or "chat",
                "model": meta.get("model", "") or "",
                "tools": list(meta.get("tools") or []),
                "source": root.source,
                "json_path": root.json_path(agent_dir),
                "md_path": root.md_path(agent_dir),
                "complete": md_file.exists(),
            })

    return summaries


def get_agent_meta(agent_id: str) -> dict | None:
    """Return the summary for one agent id, or None if not registered."""
    for summary in list_agents():
        if summary["id"] == agent_id:
            return summary
    return None


# ==========================================================================
# FACTORY
# ==========================================================================

def _session_aware(tool: BaseTool, session) -> BaseTool:
    """Record useful file-operation results without changing tool schemas."""
    import functools
    original = tool.func

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        _record_result(result, session)
        return result

    return _replace_func(tool, wrapper)


def _record_result(result, session) -> None:
    """Translate a tool result dict into this agent's FileSession state."""
    if not (isinstance(result, dict) and session is not None):
        return
    data = result.get("data") or {}
    if result.get("tool") == "map_files":
        files = data.get("files") or []
        session.add_discovered([f["path"] for f in files])
    elif result.get("tool") == "read_file":
        session.record_read(data.get("path", ""), data.get("extracted_content", ""))
    elif result.get("tool") == "write_text_file" and data.get("path"):
        session.add_output(data["path"])


def _append_grounding(agent_id: str, profile, bridge=None) -> None:
    """Append a compact grounding block to a tool-armed agent's system prompt.

    Small local models routinely call path tools with invented paths, bare
    filenames, or literally '/path/to/...' placeholders copied from a prompt.
    Pinning a real WORKSPACE ROOT plus the agent's own folder and skills dir
    gives the model deterministic places to start with map_files, and an
    explicit instruction to stop guessing once a lookup fails.

    When a Project Manager bridge is present it is the filesystem authority,
    so its workspace root becomes the grounding root instead of the local app.
    """
    from .logic import agent_dir

    if bridge is not None:
        workspace_root = str(getattr(bridge, "workspace_root", ""))
        if not workspace_root:
            bridge_health = getattr(bridge, "health", lambda: {})()
            workspace_root = str((bridge_health or {}).get("root", ""))
    else:
        workspace_root = str(Path(__file__).resolve().parents[1].resolve())

    root = Path(workspace_root)
    skill_dir = Path(__file__).resolve().parents[1] / "skills"
    skills = ", ".join(sorted(p.name for p in skill_dir.glob("*.md"))) if skill_dir.is_dir() else ""

    block = [
        "GROUNDING (read this before you call any file tool)",
        f"- WORKSPACE ROOT: {workspace_root}",
        f"- THIS AGENT FOLDER: {str(agent_dir(agent_id).resolve())}",
    ]
    if skills:
        block.append(f"- SKILLS DIRECTORY: {str(skill_dir.resolve())} (files: {skills})")
    block += [
        "- Use file paths relative to WORKSPACE ROOT. Start by calling map_files on the",
        "  root, then read_file only on a path map_files returned.",
        "- Never call readonly tools on a bare filename, a '/path/to/...' placeholder, or any",
        "  path you invented. If a tool reports 'not found', DO NOT guess another filename:",
        "  run map_files on WORKSPACE ROOT / THIS AGENT FOLDER first and read what exists.",
    ]
    profile.system_prompt = profile.system_prompt + "\n\n" + "\n".join(block)


def _assemble(
    meta: dict,
    sections: dict,
    agent_id: str,
    model: str | None,
    bridge=None,
) -> Agent:
    """Shared Agent construction from a parsed definition.

    Two things are deliberately per agent rather than per process:

    * the tools carry ``bridge`` as their own provider, so no build order or
      request ordering can redirect another agent's file operations;
    * the FileSession is created here, so discovered files and outputs
      belong to this agent alone.
    """
    definition = {"meta": meta, "sections": sections}

    mode = (meta.get("mode") or "chat").lower()
    tool_ids = [] if mode == "chat" else (meta.get("tools") or [])
    tools: list[BaseTool] = resolve_tools(tool_ids, provider=bridge)

    profile = PromptManager.build(definition, tools)

    if not (profile.system_prompt or "").strip():
        raise AgentDefinitionError(
            f"Agent '{agent_id}' has an empty system prompt, so it would "
            f"reply with no instructions. Its agent.md needs at least one "
            f"section the prompt composer reads - '## role', '## purpose', "
            f"'## personality', '## boundaries', '## communication', "
            f"'## principles' or '## decision style' (see "
            f"engine/code.py KNOWN_SECTIONS)."
        )

    if tools:
        _append_grounding(agent_id, profile, bridge=bridge)

    resolved_model = model or meta.get("model") or None
    session = new_session()
    tools = [_session_aware(fn, session) for fn in tools]
    return Agent(model=resolved_model, tools=tools, profile=profile, session=session)


def build_agent(agent_id: str, model: str | None = None, bridge=None) -> Agent:
    """Build a ready-to-use Agent for the given agent_id.

    Args:
        agent_id: id inside any registered agent root (see
                  register_agent_root) - the bundled library or the
                  Project Manager workspace.
        model:    explicit model override; when empty, falls back to the
                  agent's own "model" field, then to ask_llm's resolution
                  (models.json > first Ollama model).
        bridge:   optional Project Manager bridge (HTTP client or direct
                  filesystem authority). When present, the agent's file tools
                  route through the Project Manager instead of the local disk.
                  It is bound to this agent only.

    Raises AgentNotFoundError if the definition is missing, and
    AgentDefinitionError if it exists but cannot build a usable agent.
    """
    from .logic import load_definition

    definition = load_definition(agent_id)
    return _assemble(
        definition["meta"],
        definition["sections"],
        agent_id,
        model,
        bridge=bridge,
    )


def build_agent_from_definition(
    json_path: str,
    md_path: str,
    model: str | None = None,
    bridge=None,
) -> Agent:
    """Build a ready-to-use Agent from explicit agent.json + agent.md paths.

    This is the headless construction path (run_single_agent, pipelines that
    take raw configs): the definition is loaded from any location, not only
    the built-in library.

    Raises AgentNotFoundError if either file is missing/unreadable, and
    AgentDefinitionError if the definition cannot build a usable agent.
    """
    from .logic import load_definition_from_paths

    definition = load_definition_from_paths(json_path, md_path)
    meta = definition["meta"]
    agent_id = str(meta.get("id") or Path(json_path).parent.name or "custom")
    return _assemble(
        meta,
        definition["sections"],
        agent_id,
        model,
        bridge=bridge,
    )


def replay_history(agent: Agent, history: list[dict] | None) -> None:
    """Replay prior frontend turns ({role, content}) into the agent's history."""
    for m in (history or []):
        role = "assistant" if m.get("role") == "ai" else m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        agent.messages.append({"role": role, "content": content})
