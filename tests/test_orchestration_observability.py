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


def test_code_subagents_are_text_only_and_return_one_python_block():
    for agent_id in ("code-builder", "tester", "code-troubleshooter"):
        metadata, prompt = orchestration_interface.load_agent(agent_id)
        assert metadata["id"] == agent_id
        assert metadata["tools"] == []
        assert "```python block" in prompt


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
