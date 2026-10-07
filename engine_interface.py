"""
engine_interface.py
===================

THE public doorway into the agent engine. Callers (CLI, server routers,
test runner) import this module and nothing else from headless_app.

    import engine_interface as engine
    engine.configure(bridge=engine.direct_provider())
    engine.run_chat("hello", agent_id="rag_assistant")

Contract
--------
* Validates input, then delegates to engine_logic. No workflow lives here.
* Returns plain dicts / lists (JSON-ready).
* Raises only:
    ValueError            bad input                (HTTP 400)
    AgentNotFoundError    unknown agent id/path    (HTTP 404, a FileNotFoundError)
    anything else         genuine failure          (HTTP 500)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_ENGINE_ROOT = Path(__file__).resolve().parent / "headless_app"
if _ENGINE_ROOT.is_dir() and str(_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENGINE_ROOT))

import engine_components as _c
import engine_logic as _logic
from engine_components import AgentDefinitionError, AgentNotFoundError  # noqa: F401
from engine_components import direct_provider, http_provider  # noqa: F401

MAX_MESSAGE_LENGTH = 2000

_runtime = _logic.EngineRuntime()


# ---- configuration -------------------------------------------------

def configure(bridge: Any = None, model: str | None = None,
              log_sink: Callable[[dict], None] | None = None) -> None:
    """Set the filesystem provider, default model and log mirror."""
    global _runtime
    _runtime = _logic.EngineRuntime(bridge=bridge, model=model, log_sink=log_sink)


def register_agent_root(name: str, path, source: str | None = None) -> None:
    """Make another folder of agent folders runnable (e.g. workspace/agents)."""
    _c.register_agent_root(name, path, source=source)


def unregister_agent_root(name: str) -> bool:
    return _c.unregister_agent_root(name)


# ---- validation ----------------------------------------------------

def _message(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("Chat message cannot be empty.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Chat message is too long (max {MAX_MESSAGE_LENGTH} characters).")
    return text


# ---- runs ----------------------------------------------------------

def run_chat(message: str, agent_id: str | None = None,
             model: str | None = None) -> dict:
    """One chat turn. {reply, agent_id, name, model, tool_events, entries}"""
    return _runtime.run_chat(_message(message), agent_id=agent_id, model=model)


def run_single_agent(message: str, json_path: str | None = None,
                     md_path: str | None = None, agent_id: str | None = None,
                     model: str | None = None) -> dict:
    """Run one agent from agent.json + agent.md paths, or from an id."""
    return _runtime.run_single_agent(_message(message), json_path=json_path,
                                     md_path=md_path, agent_id=agent_id, model=model)


def run_pipeline(message: str, steps: list | None = None,
                 model: str | None = None) -> dict:
    """Cascade agents. steps: ids or {json_path, md_path}; None = config default.
    {reply, outputs, tool_events, model, entries}"""
    text = _message(message)
    if steps is not None and not steps:
        raise ValueError("Pipeline requires at least one step.")
    for step in steps or []:
        if isinstance(step, dict) and not (step.get("json_path") and step.get("md_path")):
            raise ValueError(f"Pipeline step dicts need json_path + md_path: {step!r}")
    return _runtime.run_pipeline(text, agent_configs=steps, model=model)


# ---- discovery -----------------------------------------------------

def list_agents() -> list[dict]:
    return _runtime.list_agents()


def get_agent(agent_id: str) -> dict:
    """Definition of one agent. Raises AgentNotFoundError."""
    return _logic.agent_definition(agent_id)


def default_pipeline() -> list:
    return _c.load_pipeline()


def list_models() -> list[dict]:
    return _logic.list_models()


def refresh_models() -> list[dict]:
    return _c.refresh_models()


def list_tools() -> list[str]:
    return _c.list_tools()


def tool_catalog() -> list[dict]:
    """[{id, summary, description, parameters:[{name, required, default}]}]"""
    return _logic.tool_catalog()


# ---- chat history --------------------------------------------------

def read_history(limit: int = 50, agent: str | None = None) -> list[dict]:
    return _c.read_history(limit, agent=agent)


def clear_history(agent: str | None = None) -> int:
    return _c.clear_chat(agent=agent)


def use_data_dir(path):
    """Context manager: write chat/tool logs under `path` (used by tests)."""
    return _c.use_data_dir(path)
