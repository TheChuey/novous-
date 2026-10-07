"""pipelines/logic.py

The cascade workflow: run every step in order, feed each later step the
original message plus every earlier step's reply, collect every step's
tool events, and record the run.

Why this exists: chat sends one message to ONE agent. A Step-2 agent whose
prompt says "accepts the Feature Plan from Step 1" has nothing to work from when
the user sends it a fresh idea, so it stalls asking for that plan again and
again. The pipeline feeds each later step the OUTPUT of every earlier step as
part of its own message, so the planner's spec reaches the engineer and the
engineer's blueprint reaches the builder without any copy/paste.
"""

from __future__ import annotations

from agents.interface import build_agent, build_agent_from_definition

from .code import _record_run, load_pipeline
from .data import _STEP_FEED_TEMPLATE
from .helperfunctions import _step_label

__all__ = ["run_pipeline"]


def _build_step(step, model: str | None, bridge=None):
    """Build the Agent for one pipeline step.

    A step is either an agent id (registered roots) or a dict with
    explicit `json_path` + `md_path` (ad-hoc agents).
    """
    if isinstance(step, dict) and step.get("json_path") and step.get("md_path"):
        return build_agent_from_definition(
            step["json_path"],
            step["md_path"],
            model=model,
            bridge=bridge,
        )
    return build_agent(str(step), model=model, bridge=bridge)


def run_pipeline(user_message: str, model: str | None = None,
                 config_path=None, steps: list | None = None,
                 bridge=None) -> dict:
    """Run every step in order; return {reply, outputs, tool_events}.

    outputs is a list of {agent_id, agent_name, output, tools_used} - one entry
    per step, so callers can display each stage's contribution separately and
    the cascade's per-agent tool usage.

    Args:
        user_message: the original user idea to run through the chain.
        model:        optional model override for every step.
        config_path:  optional path to a pipeline.json (defaults to the
                      bundled pipeline.json).
        steps:        optional explicit step list (agent ids or
                      {json_path, md_path} dicts). Overrides the config file.
        bridge:       optional Project Manager bridge passed to every agent.
    """
    chain = steps if steps is not None else load_pipeline(config_path)
    if not chain:
        return {
            "reply": "(pipeline not configured - add config/pipeline.json or pass steps)",
            "outputs": [],
            "tool_events": [],
        }

    results: list[dict] = []
    tool_events: list[dict] = []

    for index, step in enumerate(chain):
        agent = _build_step(step, model=model, bridge=bridge)

        feed = user_message
        if results:
            chain_text = "\n\n".join(
                _STEP_FEED_TEMPLATE.format(name=r["agent_name"], output=r["output"])
                for r in results
            )
            feed = f"ORIGINAL USER REQUEST:\n{user_message}\n\n{chain_text}"

        reply = agent.think(feed)
        tools_used = sorted({
            e.get("tool")
            for e in agent.tool_events
            if isinstance(e, dict) and e.get("tool")
        })
        results.append({
            "agent_id": _step_label(step),
            "agent_name": agent.profile.name or _step_label(step),
            "output": reply,
            "tools_used": tools_used,
        })
        tool_events.extend(agent.tool_events)
        print(
            f"Agent {index + 1} ({_step_label(step)}) completed. "
            f"Tools used: {', '.join(tools_used) or 'none'}"
        )

    result = {
        "reply": results[-1]["output"],
        "outputs": results,
        "tool_events": tool_events,
    }
    print(
        f"PIPELINE COMPLETE ({len(chain)}/{len(chain)}) -> "
        f"{result['reply'][:80]!r}"
    )
    _record_run({
        "request": user_message,
        "model": model,
        "steps": [
            {
                "agent_id": r["agent_id"],
                "agent_name": r["agent_name"],
                "output": r["output"],
                "tools_used": r["tools_used"],
            }
            for r in results
        ],
        "reply": result["reply"],
    })
    return result
