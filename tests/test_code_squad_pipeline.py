"""Code-squad pipeline: agents are mocked; code execution is real."""

import json
import uuid

import pytest

from orchestration import code_squad_pipeline as pipeline
from orchestration import orchestration_interface as interface
from orchestration.codebuilder_run_state import codebuilder_run_state
from orchestration.orchestration_run_results import run_results
from orchestration.orchestration_schemas import OrchestrationRequest
from orchestration.orchestration_telemetry import telemetry_bus


GOOD = "def add(a, b):\n    return a + b\n"
BROKEN = "def add(a, b):\n    return a + c\n"


def _block(code):
    return f"Here it is:\n```python\n{code}```\nDone."


@pytest.fixture
def agents(monkeypatch):
    """Queue canned replies per agent and record the prompts each one received."""
    replies, prompts = {}, []

    def fake_stream(agent_id, prompt, trace_id, model=None, should_stop=None):
        prompts.append((agent_id, prompt))
        queue = replies.get(agent_id) or ["(no reply)"]
        reply = queue.pop(0) if len(queue) > 1 else queue[0]
        telemetry_bus.log_event(trace_id, "AGENT_TOKEN", agent_id, "orchestrator", {"agent_id": agent_id, "text": reply})
        return reply

    monkeypatch.setattr(interface, "run_agent_turn_stream", fake_stream)
    monkeypatch.setattr(pipeline, "record_squad_run", lambda *args: None)
    return replies, prompts


def _start(action, code="", **params):
    request = OrchestrationRequest(
        squad_id="code-squad",
        workflow_action=action,
        user_query="make an add function",
        parameters={"editor_code": code, **params},
    )
    request.trace_id = f"tr_test_{action}_{uuid.uuid4().hex}"
    telemetry_bus.initialize_trace(request.trace_id)
    codebuilder_run_state.begin(request.trace_id, code, request.user_query, action)
    return request


def _events(trace_id, event_type):
    return [e for e in telemetry_bus.get_trace_history(trace_id) if e["event_type"] == event_type]


def test_build_applies_code_and_emits_editor_update(agents):
    replies, _ = agents
    replies["code-builder"] = [_block(GOOD)]
    request = _start("build")
    response = pipeline.run_code_squad(request)
    assert response.status == "success"
    updates = _events(request.trace_id, "EDITOR_CODE_UPDATE")
    assert updates and updates[-1]["data"]["content"] == GOOD
    assert codebuilder_run_state.get_preview(request.trace_id)["content"] == GOOD


def test_build_without_code_block_is_an_error(agents):
    replies, _ = agents
    replies["code-builder"] = ["I cannot do that."]
    response = pipeline.run_code_squad(_start("build"))
    assert response.status == "error"


def test_test_step_captures_real_traceback(agents):
    replies, _ = agents
    replies["tester"] = [_block("assert add(1, 2) == 3\n")]
    request = _start("test", BROKEN)
    response = pipeline.run_code_squad(request)
    assert response.status == "error"
    last_test = response.result_payload["last_test"]
    assert "NameError" in (last_test.get("stderr") or "")
    assert _events(request.trace_id, "EDITOR_CODE_EXECUTION")[-1]["data"]["status"] == "error"


def test_test_step_does_not_run_main_guard(agents):
    replies, _ = agents
    replies["tester"] = [_block("assert add(2, 2) == 4\n")]
    code = "def add(a, b):\n    return a + b\n\nif __name__ == '__main__':\n    input('blocked?')\n"
    response = pipeline.run_code_squad(_start("test", code))
    assert response.status == "success"


def test_syntax_error_maps_to_editor_line(agents):
    request = _start("test", "x = 1\ndef broken(:\n    pass\n")
    response = pipeline.run_code_squad(request)
    assert response.status == "error"
    assert _events(request.trace_id, "EDITOR_CODE_EXECUTION")[-1]["data"]["diagnostic_lines"] == [2]


def test_fix_loops_until_tests_pass(agents):
    replies, prompts = agents
    replies["tester"] = [_block("assert add(1, 2) == 3\n")]
    replies["code-troubleshooter"] = [_block(BROKEN.replace("c", "d")), _block(GOOD)]
    request = _start("fix", BROKEN)
    response = pipeline.run_code_squad(request)
    assert response.status == "success"
    assert response.result_payload["code"] == GOOD
    fixer_prompts = [p for agent, p in prompts if agent == "code-troubleshooter"]
    assert len(fixer_prompts) == 2 and "NameError" in fixer_prompts[0]


def test_fix_stops_after_max_attempts(agents):
    replies, _ = agents
    replies["tester"] = [_block("assert add(1, 2) == 3\n")]
    replies["code-troubleshooter"] = [
        _block(BROKEN.replace("c", name)) for name in ("d", "e", "f", "g")
    ]
    response = pipeline.run_code_squad(_start("fix", BROKEN))
    assert response.status == "error"
    fixes = [s for s in response.execution_trace if s.phase == "FIX"]
    assert len(fixes) == pipeline.MAX_FIX_ATTEMPTS


def test_run_all_plans_builds_and_tests(agents):
    replies, prompts = agents
    replies["code-planer"] = ["1. Add an add(a, b) function."]
    replies["code-builder"] = [_block(GOOD)]
    replies["tester"] = [_block("assert add(1, 2) == 3\n")]
    request = _start("all")
    response = pipeline.run_code_squad(request)
    assert response.status == "success"
    builder_prompt = next(p for agent, p in prompts if agent == "code-builder")
    assert "Add an add(a, b) function" in builder_prompt
    steps = [e["data"]["step"] for e in _events(request.trace_id, "STEP_STATUS")]
    assert steps[0] == "plan" and "build" in steps and "test" in steps


def test_cancel_stops_between_steps(agents, monkeypatch):
    replies, _ = agents
    replies["code-planer"] = ["plan"]
    request = _start("all")

    def cancel_after_plan(*args, **kwargs):
        codebuilder_run_state.cancel(request.trace_id)
        return "plan"

    monkeypatch.setattr(interface, "run_agent_turn_stream", cancel_after_plan)
    response = pipeline.run_code_squad(request)
    assert response.status == "cancelled"
    assert not _events(request.trace_id, "EDITOR_CODE_UPDATE")


def test_result_is_saved_before_run_complete(agents, monkeypatch):
    replies, _ = agents
    replies["code-builder"] = [_block(GOOD)]
    request = _start("build")
    seen = {}
    original = telemetry_bus.log_event

    def spy(trace_id, event_type, *args, **kwargs):
        if event_type == "RUN_COMPLETE":
            seen["result"] = run_results.get(trace_id)
        return original(trace_id, event_type, *args, **kwargs)

    monkeypatch.setattr(telemetry_bus, "log_event", spy)
    pipeline.run_code_squad(request)
    assert seen["result"] is not None and seen["result"]["status"] == "success"


def test_stream_resume_skips_seen_events():
    trace_id = "tr_test_resume"
    telemetry_bus.initialize_trace(trace_id)
    for index in range(3):
        telemetry_bus.log_event(trace_id, "STEP_STATUS", "orchestrator", "x", {"step": "plan", "status": "running", "attempt": index})
    telemetry_bus.log_event(trace_id, "AGENT_TOKEN", "a", "b", {"agent_id": "a", "text": "live only"})
    telemetry_bus.log_event(trace_id, "RUN_COMPLETE", "orchestrator", "x", {"status": "success", "duration_ms": 1})
    telemetry_bus.finish_trace(trace_id)
    frames = list(telemetry_bus.subscribe(trace_id, after=2))
    sequences = [json.loads(f.split("data: ", 1)[1])["sequence"] for f in frames]
    assert sequences == [3, 4]
    assert all("live only" not in f for f in frames)
