"""
engine_components.py
====================

The ONLY module the logic layer imports implementation from.

Everything below already exists in engine/, tools/ and bridge/. This file
does not wrap or rewrite any of it; it names the surface the logic layer is
allowed to use, so a rename or move inside the engine touches one file.

    engine_interface  ->  engine_logic  ->  engine_components  ->  engine/ tools/ bridge/
"""

from engine.agents.factory import (  # noqa: F401
    AgentDefinitionError,
    build_agent,
    build_agent_from_definition,
    replay_history,
)
from engine.agents.loader import (  # noqa: F401
    AgentNotFoundError,
    agent_json_path,
    agent_md_path,
    load_definition,
)
from engine.agents.registry import get_agent_meta, list_agents  # noqa: F401
from engine.agents.roots import (  # noqa: F401
    find_agent,
    register_agent_root,
    unregister_agent_root,
)
from engine.core.llm import CONFIG_DIR, refresh_models  # noqa: F401
from engine.pipeline import load_pipeline, run_pipeline as run_chain  # noqa: F401
from tools.chatlog import (  # noqa: F401
    append_chat,
    clear_chat,
    read_history,
    use_data_dir,
)
from tools.registry import _TOOL_REGISTRY, list_tools  # noqa: F401


def direct_provider():
    """In-process filesystem provider (needs the Project Manager importable)."""
    from bridge.providers import DirectProjectIO

    return DirectProjectIO()


def http_provider(base_url: str | None = None):
    """HTTP bridge provider for the standalone CLI."""
    from bridge.client import ProjectManagerBridge

    return ProjectManagerBridge(base_url=base_url)
