"""
engine_logic.py
===============

Workflows of the agent engine: what happens, in what order.

    build agent -> replay history -> think -> log both sides
    pipeline    -> feed-forward chain -> log the exchange untagged

No input validation (that is engine_interface) and no implementation
(that is engine_components).
"""

from __future__ import annotations

import json
from typing import Any, Callable

import engine_components as c

DEFAULT_HISTORY_LIMIT = 20


def _as_history(agent_id: str | None, limit: int | None = DEFAULT_HISTORY_LIMIT):
    """One agent's recent turns from the chat log, as model messages."""
    if not limit or limit <= 0:
        return None
    try:
        entries = c.read_history(limit=limit, agent=agent_id)
    except Exception as exc:  # a broken log must never block a conversation
        print(f"[ENGINE] history unavailable: {exc}")
        return None

    history = []
    for entry in entries:
        content = str(entry.get("message", "") or "")
        if not content:
            continue
        sender = str(entry.get("sender", ""))
        history.append({
            "role": "assistant" if sender in ("agent", "ai") else "user",
            "content": content,
        })
    return history or None


class EngineRuntime:
    """Runs agents. Holds configuration only; no conversation state."""

    def __init__(self, bridge: Any = None, model: str | None = None,
                 log_sink: Callable[[dict], None] | None = None) -> None:
        self.bridge = bridge
        self.model = model
        self.log_sink = log_sink

    # ---- internals -------------------------------------------------

    def _log(self, sender: str, message: str, agent_id: str | None) -> dict:
        entry = c.append_chat(sender, message, agent=agent_id)
        if self.log_sink is not None:
            try:
                self.log_sink(entry)
            except Exception as exc:
                print(f"[ENGINE] log sink failed: {exc}")
        return entry

    def _think(self, agent, message, agent_id, history):
        if history:
            c.replay_history(agent, history)
        reply = agent.think(message)
        entries = [self._log("user", message, agent_id),
                   self._log("agent", reply, agent_id)]
        return reply, entries

    def _default_agent_id(self) -> str:
        agents = self.list_agents()
        if not agents:
            raise RuntimeError("No agents are registered.")
        return agents[0]["id"]

    # ---- discovery -------------------------------------------------

    def list_agents(self) -> list[dict]:
        return c.list_agents()

    def get_agent(self, agent_id: str) -> dict | None:
        return c.get_agent_meta(agent_id)

    # ---- runs ------------------------------------------------------

    def run_chat(self, message, agent_id=None, model=None, history=None,
                 use_logged_history=True) -> dict:
        resolved = agent_id or self._default_agent_id()
        agent = c.build_agent(resolved, model=model or self.model, bridge=self.bridge)
        if history is None and use_logged_history:
            history = _as_history(resolved)
        reply, entries = self._think(agent, message, resolved, history)
        return {"reply": reply, "agent_id": resolved, "name": agent.profile.name,
                "model": agent.model, "tool_events": agent.tool_events,
                "entries": entries}

    def run_single_agent(self, user_input, json_path=None, md_path=None,
                         agent_id=None, model=None, history=None,
                         use_logged_history=False) -> dict:
        if json_path and md_path:
            agent = c.build_agent_from_definition(
                json_path, md_path, model=model or self.model, bridge=self.bridge)
            resolved = str(agent.profile.id)
        elif agent_id:
            resolved = agent_id
            agent = c.build_agent(agent_id, model=model or self.model,
                                  bridge=self.bridge)
        else:
            raise ValueError("Provide json_path + md_path, or an agent_id, to run.")
        if history is None and use_logged_history:
            history = _as_history(resolved)
        reply, entries = self._think(agent, user_input, resolved, history)
        return {"reply": reply, "agent_id": resolved, "name": agent.profile.name,
                "description": agent.profile.description, "model": agent.model,
                "tool_events": agent.tool_events, "entries": entries}

    def run_pipeline(self, user_input, agent_configs=None, model=None) -> dict:
        result = c.run_chain(user_input, model=model or self.model,
                             steps=agent_configs, bridge=self.bridge)
        # A cascade is not one agent: logged untagged.
        result["entries"] = [self._log("user", user_input, None),
                             self._log("agent", result["reply"], None)]
        result["model"] = model or self.model
        return result


# ---- read-only helpers (no runtime state needed) --------------------

def agent_definition(agent_id: str) -> dict:
    d = c.load_definition(agent_id)
    found = c.find_agent(agent_id)
    return {"source": found[0].source if found else "library",
            "meta": d["meta"], "sections": d["sections"],
            "json_path": c.agent_json_path(agent_id),
            "md_path": c.agent_md_path(agent_id)}


def list_models() -> list[dict]:
    path = c.CONFIG_DIR / "models.json"
    if not path.exists():
        return []
    models = json.loads(path.read_text(encoding="utf-8")).get("models") or []
    return [{"id": m.get("id", ""), "name": m.get("name", m.get("id", "")),
             "source": m.get("source", "ollama")} for m in models]


def tool_catalog() -> list[dict]:
    """Return UI descriptors from each registered LangChain tool schema."""
    out = []
    for tool_id in c.list_tools():
        registered_tool = c._TOOL_REGISTRY[tool_id]
        doc = registered_tool.description or ""
        params = [
            {
                "name": name,
                "required": field.is_required(),
                "default": None if field.is_required() else repr(field.default),
            }
            for name, field in registered_tool.args_schema.model_fields.items()
        ]
        out.append({"id": tool_id, "summary": doc.splitlines()[0] if doc else "",
                    "description": doc, "parameters": params})
    return out
