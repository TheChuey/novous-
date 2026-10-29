"""Gateway interfacing orchestration with core_engine and agentMemory."""

from pathlib import Path
from contextlib import nullcontext
from typing import Any, Tuple

from agentMemory import interface as memory_interface
from core_engine import agent_factory, runtime, tool_catalog
from core_engine.runtime import AgentProfile

REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_ROOT = REPO_ROOT / "library"
SUBAGENT_LIBRARY_ROOT = REPO_ROOT / "subAgentLibrary"


def _normalize_agent_id(agent_id: str) -> str:
    clean = str(agent_id or "").strip().replace("\\", "/")
    if not clean or clean in (".", "..") or "/" in clean:
        raise ValueError(f"Invalid agent id: {agent_id!r}")
    return clean


def load_agent(agent_id: str) -> Tuple[dict[str, Any], str]:
    """Resolve Markdown agent from library/ or YAML sub-agent from subAgentLibrary/."""
    clean = _normalize_agent_id(agent_id)
    primary_file = LIBRARY_ROOT / f"{clean}.md"
    if primary_file.is_file():
        profile = agent_factory.load_agent_definition_from_md(primary_file)
        meta = {
            "id": profile.id,
            "name": profile.name,
            "description": profile.description,
            "mode": profile.mode,
            "model": profile.model,
            "tools": list(profile.tools),
            "role": profile.role,
            "purpose": profile.purpose,
            "boundaries": profile.boundaries,
        }
        return meta, profile.system_prompt

    subagent_yaml = SUBAGENT_LIBRARY_ROOT / f"{clean}.yaml"
    if subagent_yaml.is_file():
        return agent_factory.parse_subagent_yaml(clean)

    raise FileNotFoundError(
        f"Agent definition '{agent_id}' not found in library/ or subAgentLibrary/."
    )


def read_latest_subagent_scratchpad() -> dict[str, Any]:
    memory = memory_interface.read_memory("latest_subagent_result")
    return memory.get("latest_subagent_result", {})


def read_scratchpad_snapshot() -> dict[str, Any]:
    return memory_interface.read_memory()


def _build_profile(agent_id: str, meta: dict[str, Any], body: str) -> AgentProfile:
    tools = meta.get("tools") or []
    if not isinstance(tools, list):
        tools = [tools]
    return AgentProfile(
        id=str(meta.get("id") or agent_id),
        name=str(meta.get("name") or agent_id),
        description=str(meta.get("description") or ""),
        mode=str(meta.get("mode") or "agent"),
        system_prompt=body,
        role=str(meta.get("role") or ""),
        purpose=str(meta.get("purpose") or ""),
        boundaries=str(meta.get("boundaries") or ""),
        model=str(meta.get("model") or ""),
        tools=[str(tool) for tool in tools],
    )


def run_agent_turn(
    agent_id: str,
    prompt_input: str,
    parameters: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> str:
    from orchestration.orchestration_telemetry import telemetry_bus

    context = (
        telemetry_bus.agent_context(trace_id, agent_id)
        if trace_id
        else nullcontext()
    )
    with context:
        if _normalize_agent_id(agent_id) == "rag-retriever":
            from orchestration.rag_retriever import run_rag_retriever

            return run_rag_retriever(prompt_input, parameters or {})

        meta, body = load_agent(agent_id)
        profile = _build_profile(agent_id, meta, body)
        tools = (
            tool_catalog.get_tools(profile.tools)
            if profile.mode == "agent" and profile.tools
            else []
        )
        agent_instance = runtime.Agent(
            model=profile.model or None,
            tools=tools,
            profile=profile,
        )
        return str(agent_instance.think(prompt_input))
