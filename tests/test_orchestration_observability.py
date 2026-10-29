import asyncio
import json
from threading import BoundedSemaphore
from unittest.mock import patch

from orchestration import orchestration_router
from orchestration.orchestration_patterns import SequentialPattern
from orchestration.orchestration_schemas import OrchestrationRequest
from orchestration.orchestration_run_results import run_results
from orchestration.orchestration_telemetry import TelemetryBus, telemetry_bus
from orchestration import squad_registry
from orchestration import orchestration_interface
from agentMemory import interface as memory_interface
from core_engine import tool_catalog
from core_engine.runtime import Agent, AgentProfile


def test_squad_metrics_are_persisted_and_exposed(tmp_path, monkeypatch):
    metrics_path = tmp_path / "squad-metrics.json"
    monkeypatch.setattr(squad_registry, "METRICS_PATH", metrics_path)
    monkeypatch.setattr(squad_registry, "SQUADS_PATH", tmp_path / "squads.json")

    squad_registry.record_squad_run("rag-squad", True, 120)
    squad_registry.record_squad_run("rag-squad", False, 80)

    squad = squad_registry.get_squad("rag-squad")
    assert squad["primary_agent"] == "rag-presenter"
    assert squad["subagents"] == ["rag-retriever"]
    assert squad["metrics"] == {
        "total_runs": 2,
        "successful_runs": 1,
        "failed_runs": 1,
        "average_duration_ms": 100.0,
        "last_duration_ms": 80,
        "last_status": "failing",
    }
    assert json.loads(metrics_path.read_text(encoding="utf-8"))["rag-squad"][
        "total_runs"
    ] == 2


def test_code_squad_uses_planner_builder_tester_and_troubleshooter():
    squad = squad_registry.get_squad("code-squad")
    assert squad["primary_agent"] == "code-planer"
    assert squad["subagents"] == [
        "code-builder",
        "tester",
        "code-troubleshooter",
    ]


def test_saved_code_squad_migrates_legacy_members_to_tester_pipeline(
    tmp_path, monkeypatch
):
    squads_path = tmp_path / "squads.json"
    squads_path.write_text(
        json.dumps(
            {
                "code-squad": {
                    "squad_id": "code-squad",
                    "name": "Code Development Squad",
                    "description": "Existing saved squad.",
                    "primary_agent": "code-planer",
                    "subagents": ["code-builder", "code-troubleshooter"],
                    "default_pattern": "sequential",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(squad_registry, "SQUADS_PATH", squads_path)
    monkeypatch.setattr(squad_registry, "METRICS_PATH", tmp_path / "metrics.json")

    squad = squad_registry.get_squad("code-squad")

    assert squad["subagents"] == [
        "code-builder",
        "tester",
        "code-troubleshooter",
    ]


def test_code_planner_runs_as_a_read_only_tool_using_agent():
    metadata, prompt = orchestration_interface.load_agent("code-planer")
    assert metadata["mode"] == "agent"
    assert {"map_files", "read_file", "project_status"} <= set(metadata["tools"])
    assert "write_file" not in metadata["tools"]
    assert tool_catalog.unknown_tool_names(metadata["tools"]) == []
    assert "read-only" in prompt


def test_squad_catalog_includes_new_code_subagents():
    catalog = squad_registry.list_agent_catalog()
    agent_ids = {agent["id"] for agent in catalog["agents"]}
    subagent_ids = {agent["id"] for agent in catalog["subagents"]}
    assert "code-planer" in agent_ids
    assert {
        "code-builder",
        "tester",
        "code-troubleshooter",
    } <= subagent_ids


def test_new_code_subagents_load_with_registered_tools():
    for agent_id, required_tools in (
        (
            "code-builder",
            {
                "read_file",
                "preview_code_change",
                "write_file",
                "preview_editor_code",
                "write_agent_scratchpad",
            },
        ),
        (
            "code-troubleshooter",
            {
                "read_file",
                "preview_code_change",
                "write_file",
                "run_python_code",
                "inspect_http_routes",
                "preview_editor_code",
                "write_agent_scratchpad",
            },
        ),
        (
            "tester",
            {
                "read_file",
                "map_files",
                "project_status",
                "inspect_http_routes",
                "run_python_code",
                "write_agent_scratchpad",
            },
        ),
    ):
        metadata, prompt = orchestration_interface.load_agent(agent_id)
        assert metadata["id"] == agent_id
        assert required_tools <= set(metadata["tools"])
        assert tool_catalog.unknown_tool_names(metadata["tools"]) == []
        assert "write_agent_scratchpad" in prompt
        if agent_id == "tester":
            assert "write_file" not in metadata["tools"]
            assert "This agent is read-only" in prompt


def test_code_troubleshooter_is_instructed_to_fix_confirmed_issues_safely():
    metadata, prompt = orchestration_interface.load_agent("code-troubleshooter")
    assert "write_file" in metadata["tools"]
    assert "make minimal, targeted fixes" in prompt
    assert "Before every workspace write" in prompt
    assert "Do not delete files" in prompt
    assert "claim tests/commands not actually run" in prompt
    assert "Never add unrelated example/game functionality" in prompt
    assert "expected behavior is missing" in prompt


def test_code_planner_treats_user_request_as_authoritative():
    _metadata, prompt = orchestration_interface.load_agent("code-planer")

    assert "exact `User request`" in prompt
    assert "do not turn a reported 404" in prompt
    assert "If the handoff conflicts with the exact user request" in prompt


def test_code_squad_actions_select_only_the_requested_worker():
    from orchestration.orchestration_patterns import _squad_for_request

    for action, expected_workers in (
        ("plan", []),
        ("build", ["code-builder", "tester", "code-troubleshooter"]),
        ("troubleshoot", ["code-troubleshooter"]),
        (
            "all",
            ["code-builder", "tester", "code-troubleshooter"],
        ),
    ):
        request = OrchestrationRequest(
            squad_id="code-squad",
            workflow_action=action,
            user_query="Inspect the requested code change.",
        )
        assert _squad_for_request(request) == "code-squad"
        assert request.primary_agent == "code-planer"
        assert request.subagents == expected_workers


def test_tester_skips_failed_build_and_troubleshooter_gets_builder_error(
    tmp_path, monkeypatch
):
    from orchestration.codebuilder_run_state import codebuilder_run_state

    trace_id = "tr_tester_skips_failed_build"
    telemetry_bus.initialize_trace(trace_id)
    codebuilder_run_state.begin(trace_id, "print('active')\n")
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    turns = []

    def run_agent(agent_id, prompt, parameters=None, trace_id=None):
        turns.append((agent_id, prompt))
        if agent_id == "code-planer":
            return "Implement the requested change and run a focused check."
        if agent_id == "code-builder":
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_build",
                "error",
                {"error": "Focused check raised SyntaxError."},
            )
        elif agent_id == "code-troubleshooter":
            assert "Focused check raised SyntaxError." in prompt
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_troubleshooting",
                "success",
                {"summary": "Corrected the reported syntax error."},
            )
        elif agent_id == "tester":
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_test",
                "success",
                {"summary": "Post-fix focused check passed."},
            )
        return "Worker completed."

    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        run_agent,
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="build",
            user_query="Build the requested change.",
        )
    )

    assert [agent_id for agent_id, _prompt in turns] == [
        "code-planer",
        "code-builder",
        "code-troubleshooter",
        "tester",
        "code-planer",
    ]
    assert "write_agent_scratchpad" in turns[1][1]
    assert "Focused check raised SyntaxError." in turns[2][1]
    assert "post-troubleshooting recheck" in turns[3][1]
    assert response.status == "success"
    assert [
        handoff["subagent_id"]
        for handoff in run_results.get(trace_id)["scratchpad_snapshot"][
            "subagent_history"
        ]
    ] == ["code-builder", "code-troubleshooter", "tester"]


def test_tester_failure_is_passed_to_troubleshooter(tmp_path, monkeypatch):
    from orchestration.codebuilder_run_state import codebuilder_run_state

    trace_id = "tr_tester_failure_to_troubleshooter"
    telemetry_bus.initialize_trace(trace_id)
    codebuilder_run_state.begin(trace_id, "print('active')\n")
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    agent_calls = []
    tester_runs = 0

    def run_agent(agent_id, prompt, parameters=None, trace_id=None):
        nonlocal tester_runs
        agent_calls.append((agent_id, prompt))
        if agent_id == "code-planer":
            return "Implement the requested Python behavior and run a focused check."
        if agent_id == "code-builder":
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_build",
                "success",
                {"summary": "Implementation previewed."},
            )
        elif agent_id == "tester":
            tester_runs += 1
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_test",
                "error" if tester_runs == 1 else "success",
                (
                    {"error": "AssertionError: expected 2, received 1."}
                    if tester_runs == 1
                    else {"summary": "The post-fix assertion passed."}
                ),
            )
        elif agent_id == "code-troubleshooter":
            assert "AssertionError: expected 2, received 1." in prompt
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_troubleshooting",
                "success",
                {"summary": "Reviewed the exact tester failure."},
            )
        return "Worker completed."

    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        run_agent,
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="build",
            user_query="Fix the build error.",
        )
    )

    assert [agent_id for agent_id, _prompt in agent_calls] == [
        "code-planer",
        "code-builder",
        "tester",
        "code-troubleshooter",
        "tester",
        "code-planer",
    ]
    assert response.status == "success"


def test_build_passes_plan_to_builder_and_tests_before_synthesis(
    tmp_path, monkeypatch
):
    from orchestration.codebuilder_run_state import codebuilder_run_state

    trace_id = "tr_plan_build_test_sequence"
    source = "print('starting source')\n"
    telemetry_bus.initialize_trace(trace_id)
    codebuilder_run_state.begin(trace_id, source)
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    turns = []

    def run_agent(agent_id, prompt, parameters=None, trace_id=None):
        turns.append((agent_id, prompt))
        if agent_id == "code-planer":
            return "1. Implement the requested behavior. 2. Run a focused Python check."
        if agent_id == "code-builder":
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_build",
                "success",
                {"summary": "Requested implementation is ready."},
            )
        elif agent_id == "tester":
            assert "Requested implementation is ready." in prompt
            assert "focused Python check" in prompt
            assert source in prompt
            codebuilder_run_state.save_handoff(
                trace_id,
                agent_id,
                "code_test",
                "success",
                {"summary": "Focused Python check passed."},
            )
        return "Workflow completed."

    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        run_agent,
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="build",
            user_query="Implement the requested behavior.",
            parameters={"editor_code": source},
        )
    )

    assert [agent_id for agent_id, _prompt in turns] == [
        "code-planer",
        "code-builder",
        "tester",
        "code-planer",
    ]
    assert "Code Planner implementation plan" in turns[1][1]
    assert "focused Python check" in turns[1][1]
    assert response.status == "success"
    assert [
        handoff["subagent_id"]
        for handoff in run_results.get(trace_id)["scratchpad_snapshot"][
            "subagent_history"
        ]
    ] == ["code-builder", "tester"]


def test_code_plan_action_skips_stale_scratchpad_and_is_successful(
    tmp_path, monkeypatch
):
    trace_id = "tr_code_plan_action"
    telemetry_bus.initialize_trace(trace_id)
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    turns = []
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        lambda agent_id, prompt, parameters=None, trace_id=None: (
            turns.append((agent_id, prompt)) or "A verified implementation plan."
        ),
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_latest_subagent_scratchpad",
        lambda: (_ for _ in ()).throw(AssertionError("stale scratchpad was read")),
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_scratchpad_snapshot",
        lambda: (_ for _ in ()).throw(AssertionError("stale snapshot was read")),
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="plan",
            user_query="Plan a safe implementation.",
        )
    )

    assert response.status == "success"
    assert response.final_answer == "A verified implementation plan."
    assert len(turns) == 1
    assert turns[0][0] == "code-planer"
    assert "Do not claim that files were changed" in turns[0][1]


def test_troubleshooter_receives_editor_code_without_claiming_automatic_execution(
    tmp_path, monkeypatch
):
    from tools import agent_memory_tool

    trace_id = "tr_code_troubleshoot_editor_source"
    telemetry_bus.initialize_trace(trace_id)
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    monkeypatch.setattr(
        agent_memory_tool.interface,
        "store_subagent_result",
        lambda **_kwargs: {"updated_at": "test"},
    )
    source = "print(missing_value)\n"
    turns = []
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        lambda agent_id, prompt, parameters=None, trace_id=None: (
            turns.append((agent_id, prompt)) or f"{agent_id} completed"
        ),
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_latest_subagent_scratchpad",
        lambda: {
            "subagent_id": "code-troubleshooter",
            "status": "success",
            "payload": {"root_cause": "undefined name"},
        },
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_scratchpad_snapshot",
        lambda: {"latest_subagent_result": {"subagent_id": "code-troubleshooter"}},
    )

    SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="troubleshoot",
            user_query="Fix the current editor code.",
            parameters={"editor_code": source},
        )
    )

    worker_id, prompt = turns[0]
    assert worker_id == "code-troubleshooter"
    assert source in prompt
    assert "does not automatically run it" in prompt
    assert "inspect_http_routes" in prompt
    assert "ask for the missing details" in prompt
    assert "MUST call write_agent_scratchpad" in prompt


def test_build_workflow_falls_back_to_complete_code_block_for_editor_preview(
    tmp_path, monkeypatch
):
    from orchestration.codebuilder_run_state import codebuilder_run_state

    trace_id = "tr_code_builder_editor_fallback"
    original = "print('old')\n"
    proposed = "print('built')\n"
    telemetry_bus.initialize_trace(trace_id)
    codebuilder_run_state.begin(trace_id, original)
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    turns = []

    def run_agent(agent_id, prompt, parameters=None, trace_id=None):
        turns.append((agent_id, prompt))
        if agent_id == "code-builder":
            codebuilder_run_state.save_handoff(
                trace_id,
                "code-builder",
                "code_build",
                "success",
                {"summary": "Updated editor buffer."},
            )
            return f"Updated editor code:\n```python\n{proposed}```"
        if agent_id == "tester":
            codebuilder_run_state.save_handoff(
                trace_id,
                "tester",
                "code_test",
                "success",
                {"summary": "Focused test passed."},
            )
        return "The requested code has been built."

    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        run_agent,
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_latest_subagent_scratchpad",
        lambda: {
            "subagent_id": "code-builder",
            "status": "success",
            "payload": {"summary": "Updated editor buffer."},
        },
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_scratchpad_snapshot",
        lambda: {"latest_subagent_result": {"subagent_id": "code-builder"}},
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="build",
            user_query="Build the requested change in the editor.",
            parameters={"editor_code": original},
        )
    )

    assert response.status == "success"
    assert codebuilder_run_state.get_preview(trace_id) == {
        "content": proposed,
        "changed_lines": [1],
    }
    assert any(
        event["event_type"] == "EDITOR_CODE_PREVIEW"
        for event in telemetry_bus.get_trace_history(trace_id)
    )
    assert turns[0][0] == "code-planer"
    assert [agent_id for agent_id, _prompt in turns] == [
        "code-planer",
        "code-builder",
        "tester",
        "code-planer",
    ]


def test_code_workflow_does_not_use_stale_scratchpad_or_claim_success(
    tmp_path, monkeypatch
):
    from tools import agent_memory_tool
    from orchestration.codebuilder_run_state import codebuilder_run_state

    trace_id = "tr_code_missing_handoff"
    telemetry_bus.initialize_trace(trace_id)
    codebuilder_run_state.begin(trace_id, "print('active')\n")
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    stored_handoffs = []
    monkeypatch.setattr(
        agent_memory_tool.interface,
        "store_subagent_result",
        lambda **kwargs: stored_handoffs.append(kwargs) or {"updated_at": "test"},
    )
    primary_turns = []
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        lambda agent_id, prompt, parameters=None, trace_id=None: (
            primary_turns.append((agent_id, prompt)) or "This must not be used."
        ),
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_latest_subagent_scratchpad",
        lambda: {
            "subagent_id": "code-troubleshooter",
            "task_type": "code_troubleshooting",
            "status": "success",
            "payload": {"files_changed": ["main.py"], "fix": "Added Hangman."},
        },
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_scratchpad_snapshot",
        lambda: {
            "latest_subagent_result": {
                "subagent_id": "code-troubleshooter",
                "payload": {"fix": "Added Hangman."},
            }
        },
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="troubleshoot",
            user_query="The server returns a 404.",
            parameters={"editor_code": "print('active')\n"},
        )
    )

    assert response.status == "error"
    assert "returned without writing its required scratchpad handoff" in response.final_answer
    assert "This must not be used." in response.final_answer
    assert "Hangman" not in response.final_answer
    assert all(agent_id != "code-planer" for agent_id, _prompt in primary_turns)
    snapshot = run_results.get(trace_id)["scratchpad_snapshot"]
    handoff = snapshot["latest_subagent_result"]
    assert handoff["status"] == "error"
    assert handoff["payload"]["handoff_source"] == "orchestrator_fallback"
    assert handoff["payload"]["agent_response"] == "This must not be used."
    assert stored_handoffs[0]["status"] == "error"
    assert stored_handoffs[0]["subagent_id"] == "code-troubleshooter"
    assert "Hangman" not in json.dumps(snapshot)


def test_nothing_found_handoff_cannot_invent_a_requested_feature(tmp_path, monkeypatch):
    from orchestration.codebuilder_run_state import codebuilder_run_state

    trace_id = "tr_code_nothing_found_authoritative_request"
    telemetry_bus.initialize_trace(trace_id)
    codebuilder_run_state.begin(trace_id, "print('Hello')\n")
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    agent_calls = []

    def run_agent(agent_id, _prompt, parameters=None, trace_id=None):
        agent_calls.append(agent_id)
        if agent_id == "code-troubleshooter":
            codebuilder_run_state.save_handoff(
                trace_id,
                "code-troubleshooter",
                "code_troubleshooting",
                "nothing_found",
                {
                    "summary": (
                        "The task asked to write a Hangman web app using Flask."
                    ),
                    "evidence": "Editor contains a simple print statement.",
                },
            )
        return "This unsupported feature must not be repeated."

    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        run_agent,
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="code-squad",
            workflow_action="troubleshoot",
            user_query="The server returns a 404.",
            parameters={"editor_code": "print('Hello')\n"},
        )
    )

    assert response.status == "nothing_found"
    assert agent_calls == ["code-troubleshooter"]
    assert "No code change or successful check is verified" in response.final_answer
    assert "will not infer a feature request" in response.final_answer
    assert "provide the exact error and steps to reproduce" in response.final_answer
    assert "Hangman" not in response.final_answer
    assert "Flask" not in response.final_answer
    assert "exact URL/path, HTTP method" in response.final_answer


def test_dynamic_squad_creation_and_deletion_preserve_agent_definitions(
    tmp_path, monkeypatch
):
    squads_path = tmp_path / "squads.json"
    metrics_path = tmp_path / "metrics.json"
    monkeypatch.setattr(squad_registry, "SQUADS_PATH", squads_path)
    monkeypatch.setattr(squad_registry, "METRICS_PATH", metrics_path)
    monkeypatch.setattr(
        squad_registry,
        "list_agent_catalog",
        lambda: {
            "agents": [{"id": "code-planer", "name": "Coding Planner", "description": ""}],
            "subagents": [
                {"id": "code-builder", "name": "Code Builder", "description": ""},
                {
                    "id": "code-troubleshooter",
                    "name": "Troubleshooter",
                    "description": "",
                },
            ],
        },
    )
    squad_registry.record_squad_run("code-squad", True, 10)

    created = squad_registry.create_squad(
        "My Code Team",
        "Build and troubleshoot.",
        "code-planer",
        ["code-builder", "code-troubleshooter"],
    )
    assert created["squad_id"] == "my-code-team"
    assert created["subagents"] == ["code-builder", "code-troubleshooter"]

    assert squad_registry.delete_squad("my-code-team")
    assert not squad_registry.delete_squad("my-code-team")
    assert squad_registry.get_squad("code-squad") is not None
    assert squad_registry.get_squad("code-squad")["metrics"]["total_runs"] == 1
    assert "code-builder" in {
        item["id"] for item in squad_registry.list_agent_catalog()["subagents"]
    }


def test_deleting_last_squad_keeps_registry_empty(tmp_path, monkeypatch):
    squads_path = tmp_path / "squads.json"
    monkeypatch.setattr(squad_registry, "SQUADS_PATH", squads_path)
    monkeypatch.setattr(squad_registry, "METRICS_PATH", tmp_path / "metrics.json")
    monkeypatch.setattr(
        squad_registry,
        "list_agent_catalog",
        lambda: {
            "agents": [{"id": "planner", "name": "Planner", "description": ""}],
            "subagents": [],
        },
    )
    squad = squad_registry.create_squad("Only Squad", "", "planner", [])

    assert squad_registry.delete_squad(squad["squad_id"])
    for remaining in squad_registry.list_squads():
        squad_registry.delete_squad(remaining["squad_id"])
    assert squad_registry.list_squads() == []


def test_telemetry_is_bounded_and_excludes_sensitive_payloads():
    bus = TelemetryBus(max_traces=2, max_events_per_trace=2)
    bus.initialize_trace("trace-safe")
    bus.log_event(
        "trace-safe",
        "TOOL_CALL_END",
        "rag-retriever",
        "search_knowledge_base",
        {
            "tool_name": "search_knowledge_base",
            "status": "success",
            "duration_ms": 12,
            "arguments": {"query": "private question"},
            "result": "private document text",
        },
    )
    bus.log_event(
        "trace-safe", "AGENT_MESSAGE", "orchestrator", "rag-presenter",
        {"summary": "Synthesis started", "prompt": "private question"},
    )
    bus.log_event(
        "trace-safe", "RUN_COMPLETE", "orchestrator", "rag-squad",
        {"status": "success", "duration_ms": 20},
    )

    history = bus.get_trace_history("trace-safe")
    assert len(history) == 2
    serialized = json.dumps(history)
    assert "private question" not in serialized
    assert "private document text" not in serialized
    assert "arguments" not in serialized


def test_sequential_run_emits_trace_and_persists_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    trace_id = "tr_observability_test"
    telemetry_bus.initialize_trace(trace_id)
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        lambda agent_id, prompt, parameters=None, trace_id=None: (
            f"{agent_id} completed"
        ),
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_latest_subagent_scratchpad",
        lambda: {
            "subagent_id": "rag-retriever",
            "status": "success",
            "payload": {"results": [{"path": "notes.md"}]},
        },
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_scratchpad_snapshot",
        lambda: {
            "latest_subagent_result": {
                "subagent_id": "rag-retriever",
                "status": "success",
                "payload": {"results": [{"path": "notes.md"}]},
            }
        },
    )

    response = SequentialPattern().execute(
        OrchestrationRequest(
            trace_id=trace_id,
            squad_id="rag-squad",
            primary_agent="rag-presenter",
            subagents=["rag-retriever"],
            user_query="do not include this private question in telemetry",
        )
    )

    events = telemetry_bus.get_trace_history(trace_id)
    event_types = [event["event_type"] for event in events]
    assert response.trace_id == trace_id
    assert response.status == "success"
    assert run_results.get(trace_id)["final_answer"] == "rag-presenter completed"
    assert run_results.get(trace_id)["scratchpad_snapshot"]["latest_subagent_result"][
        "subagent_id"
    ] == "rag-retriever"
    assert "SCRATCHPAD_HANDOFF" in event_types
    assert event_types[-1] == "RUN_COMPLETE"
    assert "private question" not in json.dumps(events)
    assert squad_registry.get_squad("rag-squad")["metrics"]["total_runs"] == 1
    assert list(telemetry_bus.subscribe(trace_id))[-1].startswith(
        f"id: {trace_id}:"
    )


def test_async_run_requires_a_registered_squad(monkeypatch):
    class NoRunExecutor:
        def submit(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(orchestration_router, "_RUN_EXECUTOR", NoRunExecutor())
    from fastapi import HTTPException

    try:
        orchestration_router.start_orchestration_run(
            OrchestrationRequest(user_query="test")
        )
    except HTTPException as error:
        assert error.status_code == 400
    else:
        raise AssertionError("A registered squad is required.")


def test_rag_worker_reports_safe_scratchpad_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_interface.scratchpad, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        memory_interface.scratchpad, "SCRATCHPAD_PATH", tmp_path / "scratchpad.json"
    )
    trace_id = "tr_rag_handoff_test"
    telemetry_bus.initialize_trace(trace_id)
    result_payload = {
        "knowledge_base_id": "branch-1",
        "knowledge_base": "Test branch",
        "results": [{"path": "notes.md", "content": "private evidence", "score": 0.9}],
    }

    with patch(
        "orchestration.rag_retriever.interface.search_knowledge_base",
        return_value=result_payload,
    ), patch(
        "orchestration.rag_retriever.rag_config.selected_knowledge_base_id",
        return_value="branch-1",
    ), telemetry_bus.agent_context(trace_id, "rag-retriever"):
        from orchestration.rag_retriever import run_rag_retriever

        run_rag_retriever("private query", {})

    handoff = next(
        event
        for event in telemetry_bus.get_trace_history(trace_id)
        if event["event_type"] == "SCRATCHPAD_HANDOFF"
    )
    assert handoff["data"] == {
        "status": "success",
        "subagent_id": "rag-retriever",
        "result_count": 1,
        "direction": "write",
    }
    assert "private query" not in json.dumps(handoff)
    assert "private evidence" not in json.dumps(handoff)


def test_agent_tool_events_report_status_without_arguments_or_results():
    def private_tool(query):
        return f"document content for {query}"

    trace_id = "tr_tool_privacy_test"
    telemetry_bus.initialize_trace(trace_id)
    agent = Agent(
        model=None,
        tools=[private_tool],
        profile=AgentProfile(id="observed-agent", mode="agent"),
    )

    with telemetry_bus.agent_context(trace_id, "observed-agent"):
        agent.act(
            {
                "function": {
                    "name": "private_tool",
                    "arguments": {"query": "private user question"},
                }
            },
            "native",
        )

    events = telemetry_bus.get_trace_history(trace_id)
    assert [event["event_type"] for event in events] == [
        "TOOL_CALL_START",
        "TOOL_CALL_END",
    ]
    assert events[-1]["data"]["status"] == "success"
    serialized = json.dumps(events)
    assert "private user question" not in serialized
    assert "document content" not in serialized


def test_async_run_endpoint_streams_a_completed_trace(tmp_path, monkeypatch):
    class InlineExecutor:
        def submit(self, function, request):
            function(request)

    monkeypatch.setattr(orchestration_router, "_RUN_EXECUTOR", InlineExecutor())
    monkeypatch.setattr(
        orchestration_router, "_RUN_CAPACITY", BoundedSemaphore(1)
    )
    monkeypatch.setattr(
        squad_registry, "METRICS_PATH", tmp_path / "squad-metrics.json"
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        lambda agent_id, prompt, parameters=None, trace_id=None: "Completed.",
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_latest_subagent_scratchpad",
        lambda: {
            "subagent_id": "rag-retriever",
            "status": "nothing_found",
            "payload": {"results": []},
        },
    )
    monkeypatch.setattr(
        "orchestration.orchestration_patterns.interface.read_scratchpad_snapshot",
        lambda: {"latest_subagent_result": {"subagent_id": "rag-retriever"}},
    )

    started = orchestration_router.start_orchestration_run(
        OrchestrationRequest(
            squad_id="rag-squad",
            user_query="private request text",
        )
    )
    stream = orchestration_router.stream_orchestration_trace(started["trace_id"])
    assert stream.media_type == "text/event-stream"

    async def read_stream():
        return [chunk async for chunk in stream.body_iterator]

    frames = asyncio.run(read_stream())
    body = "".join(
        chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
        for chunk in frames
    )
    assert "RUN_COMPLETE" in body
    assert "private request text" not in body
    assert "SCRATCHPAD_HANDOFF" in body
    scratchpad_response = orchestration_router.get_orchestration_run_scratchpad(
        started["trace_id"]
    )
    assert scratchpad_response["latest_subagent_result"]["subagent_id"] == "rag-retriever"
    latest = orchestration_router.get_latest_squad_run("rag-squad")
    assert latest["result"]["trace_id"] == started["trace_id"]
