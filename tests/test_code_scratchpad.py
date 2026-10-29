"""Coding agents' shared scratchpad: store, tools, and code-squad integration."""

import json
import uuid

import pytest

from agentMemory import code_scratchpad
from core_engine.runtime import Agent, AgentProfile
from orchestration import code_squad_pipeline as pipeline
from orchestration import orchestration_interface as interface
from orchestration.codebuilder_run_state import codebuilder_run_state
from orchestration.orchestration_schemas import OrchestrationRequest
from orchestration.orchestration_telemetry import telemetry_bus
from tools.code_scratchpad_tool import post_code_scratchpad, read_code_scratchpad


GOOD = "def add(a, b):\n    return a + b\n"


def _block(code):
    return f"```python\n{code}```\nDone."


def test_post_and_read_newest_first_with_filters():
    code_scratchpad.post("code-planer", "plan", "Plan A", "steps", run_id="tr_1")
    code_scratchpad.post("codingagent", "note", "Use type hints", "please", run_id="chat")
    code_scratchpad.post("code-planer", "plan", "Plan B", "steps", run_id="tr_2")
    assert [e["title"] for e in code_scratchpad.entries()] == ["Plan B", "Use type hints", "Plan A"]
    assert [e["title"] for e in code_scratchpad.entries(kind="note")] == ["Use type hints"]
    assert [e["title"] for e in code_scratchpad.entries(author="code-planer", run_id="tr_1")] == ["Plan A"]
    assert code_scratchpad.latest("plan")["title"] == "Plan B"


def test_entry_and_content_caps(monkeypatch):
    monkeypatch.setattr(code_scratchpad, "MAX_ENTRIES", 3)
    for index in range(5):
        code_scratchpad.post("agent", "note", f"n{index}", "x")
    assert code_scratchpad.count() == 3
    entry = code_scratchpad.post("agent", "note", "big", "y" * (code_scratchpad.MAX_CONTENT_CHARS + 10))
    assert len(entry["content"]) == code_scratchpad.MAX_CONTENT_CHARS and entry["truncated"]


def test_rejects_unknown_kind_and_clears():
    with pytest.raises(ValueError):
        code_scratchpad.post("agent", "secret", "t", "c")
    code_scratchpad.post("agent", "note", "t", "c")
    code_scratchpad.clear()
    assert code_scratchpad.entries() == []


def test_post_tool_records_the_calling_agent():
    agent = Agent(
        model=None,
        tools=[post_code_scratchpad, read_code_scratchpad],
        profile=AgentProfile(id="codingagent", mode="agent"),
    )
    agent.act(
        {"function": {"name": "post_code_scratchpad", "arguments": {"title": "Hint", "content": "Use dataclasses"}}},
        "native",
    )
    entry = code_scratchpad.latest("note")
    assert entry["author"] == "codingagent" and entry["run_id"] == "chat"
    read = json.loads(read_code_scratchpad(kind="note"))
    assert read["entries"][0]["content"] == "Use dataclasses"


@pytest.fixture
def agents(monkeypatch):
    replies, prompts = {}, []

    def fake_stream(agent_id, prompt, trace_id, model=None, should_stop=None):
        prompts.append((agent_id, prompt))
        return replies.get(agent_id, "(no reply)")

    monkeypatch.setattr(interface, "run_agent_turn_stream", fake_stream)
    monkeypatch.setattr(pipeline, "record_squad_run", lambda *args: None)
    return replies, prompts


def _run(action, code=""):
    request = OrchestrationRequest(
        squad_id="code-squad", workflow_action=action,
        user_query="make an add function", parameters={"editor_code": code},
    )
    request.trace_id = f"tr_note_{uuid.uuid4().hex}"
    telemetry_bus.initialize_trace(request.trace_id)
    codebuilder_run_state.begin(request.trace_id, code, request.user_query, action)
    return pipeline.run_code_squad(request), request.trace_id


def test_run_all_records_each_step_and_emits_handoffs(agents):
    replies, _ = agents
    replies.update({
        "code-planer": "1. Add add(a, b).",
        "code-builder": _block(GOOD),
        "tester": _block("assert add(1, 2) == 3\n"),
    })
    response, trace_id = _run("all")
    assert response.status == "success"
    kinds = [e["kind"] for e in code_scratchpad.entries(run_id=trace_id)]
    assert kinds == ["summary", "test", "code", "plan"]
    writes = [
        e for e in telemetry_bus.get_trace_history(trace_id)
        if e["event_type"] == "SCRATCHPAD_HANDOFF" and e["data"]["direction"] == "write"
    ]
    assert len(writes) == 4


def test_build_alone_reuses_stored_plan_and_shared_notes(agents):
    replies, prompts = agents
    replies["code-builder"] = _block(GOOD)
    code_scratchpad.post("code-planer", "plan", "Plan", "Name the function add_numbers.", run_id="tr_old")
    code_scratchpad.post("codingagent", "note", "Style", "The user wants type hints.", run_id="chat")
    response, _ = _run("build")
    assert response.status == "success"
    builder_prompt = next(prompt for agent, prompt in prompts if agent == "code-builder")
    assert "Name the function add_numbers." in builder_prompt
    assert "The user wants type hints." in builder_prompt
