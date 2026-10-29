import json

from codebuilder.schemas import CodeExecutionResult, DiagnosticItem
from core_engine import tool_catalog
from core_engine.runtime import Agent, AgentProfile
from orchestration.codebuilder_run_state import CodeBuilderRunState, codebuilder_run_state
from orchestration import orchestration_router
from orchestration.orchestration_telemetry import telemetry_bus


def registered_tool(name):
    tool_catalog.load_tools()
    return tool_catalog.REGISTRY[name]["function"]


def test_run_state_keeps_preview_and_execution_scoped_to_trace():
    state = CodeBuilderRunState(max_traces=2)
    state.begin("trace-state-1", "print('before')\n")
    state.begin("trace-state-2", "print('second')\n")

    assert state.save_preview("trace-state-1", "print('after')\n", [1])
    assert state.get_preview("trace-state-1") == {
        "content": "print('after')\n",
        "changed_lines": [1],
    }
    assert state.get_preview("trace-state-2") is None
    assert state.save_execution(
        "trace-state-1",
        "print('before')\n",
        {"status": "ERROR", "stdout": "", "stderr": "NameError"},
    )
    assert state.get_execution("trace-state-1")["status"] == "ERROR"
    assert not state.save_execution(
        "trace-state-1", "print('unrelated')\n", {"status": "SUCCESS"}
    )


def test_preview_editor_code_persists_content_without_telemetry_source():
    trace_id = "tr_editor_preview_handoff"
    original = "def greet():\n    return 'old'\n"
    proposed = "def greet():\n    return 'new'\n"
    codebuilder_run_state.begin(trace_id, original)
    telemetry_bus.initialize_trace(trace_id)

    with telemetry_bus.agent_context(trace_id, "code-builder"):
        response = json.loads(registered_tool("preview_editor_code")(proposed))

    assert response == {"status": "success", "changed_lines": [2]}
    assert codebuilder_run_state.get_preview(trace_id) == {
        "content": proposed,
        "changed_lines": [2],
    }
    event = telemetry_bus.get_trace_history(trace_id)[0]
    assert event["event_type"] == "EDITOR_CODE_PREVIEW"
    assert event["data"] == {"changed_lines": [2]}
    assert proposed not in json.dumps(event)


def test_run_python_code_persists_only_matching_editor_execution(
    monkeypatch,
):
    trace_id = "tr_editor_execution_handoff"
    source = "print(missing_value)\n"
    result = CodeExecutionResult(
        run_id="run_test",
        status="ERROR",
        stderr="NameError: name 'missing_value' is not defined",
        diagnostics=[
            DiagnosticItem(
                line=1,
                message="NameError: name 'missing_value' is not defined",
            )
        ],
    )
    from codebuilder import execution

    monkeypatch.setattr(execution, "execute_python_code", lambda _request: result)
    codebuilder_run_state.begin(trace_id, source)
    telemetry_bus.initialize_trace(trace_id)

    with telemetry_bus.agent_context(trace_id, "code-troubleshooter"):
        response = json.loads(registered_tool("run_python_code")(source))

    assert response["status"] == "ERROR"
    assert codebuilder_run_state.get_execution(trace_id)["stderr"] == result.stderr
    event = telemetry_bus.get_trace_history(trace_id)[0]
    assert event["event_type"] == "EDITOR_CODE_EXECUTION"
    assert event["data"] == {"status": "error", "diagnostic_lines": [1]}
    assert source not in json.dumps(event)


def test_code_tester_execution_is_visible_without_highlighting_test_snippet_lines(
    monkeypatch,
):
    from codebuilder import execution

    trace_id = "tr_tester_execution_handoff"
    codebuilder_run_state.begin(trace_id, "def add(a, b):\n    return a + b\n")
    telemetry_bus.initialize_trace(trace_id)
    result = CodeExecutionResult(
        run_id="run_test",
        status="SUCCESS",
        stdout="Focused check passed",
    )
    monkeypatch.setattr(execution, "execute_python_code", lambda _request: result)

    with telemetry_bus.agent_context(trace_id, "tester"):
        response = json.loads(
            registered_tool("run_python_code")("assert 1 + 1 == 2\n")
        )

    assert response["status"] == "SUCCESS"
    assert codebuilder_run_state.get_execution(trace_id)[
        "source_matches_editor"
    ] is False
    event = telemetry_bus.get_trace_history(trace_id)[0]
    assert event["event_type"] == "EDITOR_CODE_EXECUTION"
    assert event["data"] == {"status": "success", "diagnostic_lines": []}


def test_applied_workspace_editor_source_can_match_tester_diagnostics():
    trace_id = "tr_workspace_editor_source"
    state = CodeBuilderRunState()
    state.begin(
        trace_id,
        "print('old')\n",
        editor_path="src/main.py",
    )
    updated = "def add(a, b):\n    return a + b\n"

    assert not state.save_workspace_source(trace_id, "src/other.py", updated)
    assert state.save_workspace_source(trace_id, "src/main.py", updated)
    assert state.matches_editor_source(trace_id, updated)


def test_editor_handoff_endpoints_return_trace_scoped_content():
    trace_id = "tr_editor_handoff_api"
    codebuilder_run_state.begin(trace_id, "print('old')\n")
    codebuilder_run_state.save_preview(trace_id, "print('new')\n", [1])
    codebuilder_run_state.save_execution(
        trace_id,
        "print('old')\n",
        {"status": "ERROR", "stdout": "", "stderr": "NameError"},
    )

    assert orchestration_router.get_orchestration_editor_preview(trace_id) == {
        "content": "print('new')\n",
        "changed_lines": [1],
    }
    assert orchestration_router.get_orchestration_editor_execution(trace_id)[
        "stderr"
    ] == "NameError"


def test_inspect_http_routes_lists_static_route_declarations(monkeypatch):
    from tools import interface as tools_interface

    source = (
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/health')\n"
        "def health(): pass\n"
        "@router.api_route('/items', methods=['GET', 'POST'])\n"
        "def items(): pass\n"
    )
    monkeypatch.setattr(
        tools_interface,
        "read_file_bytes",
        lambda path, _limit: {
            "path": path,
            "content": source.encode("utf-8"),
        },
    )

    routes = json.loads(registered_tool("inspect_http_routes")("server.py"))

    assert routes["routes"] == [
        {
            "line": 3,
            "function": "health",
            "route": "/health",
            "methods": ["GET"],
            "router": "router",
        },
        {
            "line": 5,
            "function": "items",
            "route": "/items",
            "methods": ["GET", "POST"],
            "router": "router",
        },
    ]


def test_scratchpad_tool_records_handoff_for_current_workflow_only(monkeypatch):
    from tools import agent_memory_tool

    trace_id = "tr_current_scratchpad_handoff"
    telemetry_bus.initialize_trace(trace_id)
    monkeypatch.setattr(
        agent_memory_tool.interface,
        "store_subagent_result",
        lambda **_kwargs: {"updated_at": "test"},
    )

    with telemetry_bus.agent_context(trace_id, "code-troubleshooter"):
        registered_tool("write_agent_scratchpad")(
            subagent_id="code-troubleshooter",
            task_type="code_troubleshooting",
            status="nothing_found",
            payload='{"reason":"URL was not provided"}',
        )

    assert codebuilder_run_state.get_handoff(trace_id) == {
        "subagent_id": "code-troubleshooter",
        "task_type": "code_troubleshooting",
        "status": "nothing_found",
        "payload": {"reason": "URL was not provided"},
    }
