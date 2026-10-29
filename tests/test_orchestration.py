"""Automated Pytest suite for multi-subagent orchestration and hardware-aware patterns."""

from pathlib import Path
from unittest.mock import patch

import yaml

from agentMemory import interface as memory_interface
from orchestration.orchestration_schemas import OrchestrationRequest
from orchestration.orchestration_service import run_orchestration

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_subagent_yaml_loading():
    yaml_path = REPO_ROOT / "subAgentLibrary" / "code-analyzer.yaml"
    assert yaml_path.is_file()
    content = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert content["id"] == "code-analyzer"
    assert content["type"] == "subagent"


def test_readme_orchestration_exists():
    readme_path = REPO_ROOT / "orchestration" / "README_orchestration.md"
    assert readme_path.is_file()
    text = readme_path.read_text(encoding="utf-8")
    assert "Prompt Design Principles" in text


def test_orchestration_sequential_default_pattern():
    req = OrchestrationRequest(
        pattern="sequential",
        primary_agent="rag-presenter",
        subagents=["code-analyzer", "rag-retriever"],
        user_query="Run hardware-safe sequential execution",
        parameters={"test": True},
    )

    def fake_turn(agent_id, prompt_input, parameters=None, trace_id=None):
        return f"{agent_id} completed: {prompt_input[:40]}"

    with patch(
        "orchestration.orchestration_patterns.interface.run_agent_turn",
        side_effect=fake_turn,
    ), patch(
        "orchestration.orchestration_patterns.interface.read_latest_subagent_scratchpad",
        return_value={"status": "success", "payload": {"test": True}},
    ), patch(
        "orchestration.orchestration_patterns.interface.read_scratchpad_snapshot",
        return_value={"latest_subagent_result": {"status": "success"}},
    ):
        res = run_orchestration(req)

    assert res.pattern == "sequential"
    assert res.trace_id.startswith("tr_")
    assert len(res.execution_trace) >= 3
    assert res.final_answer.startswith("rag-presenter completed: User request:")
    assert res.result_payload == {"test": True}


def test_scratchpad_subagent_result_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_interface.scratchpad, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        memory_interface.scratchpad, "SCRATCHPAD_PATH", tmp_path / "scratchpad.json"
    )

    memory_interface.store_subagent_result(
        "code-analyzer", "code_analysis", "success", {"issues_found": []}
    )
    memory = memory_interface.read_memory("latest_subagent_result")

    assert memory["latest_subagent_result"]["subagent_id"] == "code-analyzer"
    assert memory["latest_subagent_result"]["payload"] == {"issues_found": []}


def test_rag_presenter_delegates_to_retriever_and_reads_scratchpad(tmp_path, monkeypatch):
    prompt = (REPO_ROOT / "library" / "rag-presenter.md").read_text(
        encoding="utf-8"
    )
    assert "Novous chat runtime calls `call_subagent`" in prompt
    assert "do not call the sub-agent a second time" in prompt.lower()

    monkeypatch.setattr(memory_interface.scratchpad, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        memory_interface.scratchpad, "SCRATCHPAD_PATH", tmp_path / "scratchpad.json"
    )

    retrieval_payload = {
        "query": "What does the source say?",
        "knowledge_branch_id": "branch-1",
        "knowledge_branch_name": "Test branch",
        "results": [
            {"path": "notes.md", "content": "Relevant evidence", "score": 0.9}
        ],
        "skipped_incompatible_chunks": 0,
    }

    def fake_chat(**kwargs):
        assert any(
            "Relevant evidence" in str(message.get("content", ""))
            for message in kwargs["messages"]
        )
        if fake_chat.calls == 0:
            fake_chat.calls += 1
            return {
                "message": {
                    "content": (
                        "Here is the JSON for a function call:\n"
                        '{"name": "read_agent_scratchpad", "parameters": '
                        '{"memory_type": "latest_subagent_result"}}'
                    )
                }
            }
        return {"message": {"content": "The source says relevant evidence."}}

    fake_chat.calls = 0

    with patch(
        "tools.agent_memory_tool.interface.search_knowledge_base",
        return_value={
            "knowledge_base_id": "branch-1",
            "knowledge_base": "Test branch",
            "results": retrieval_payload["results"],
        },
    ) as search, patch(
        "orchestration.rag_retriever.rag_config.selected_knowledge_base_id",
        return_value="branch-1",
    ), patch(
        "core_engine.runtime.ollama.chat",
        side_effect=fake_chat,
    ) as chat:
        from core_engine.interface import reset_session, run_single_agent

        try:
            answer = run_single_agent(
                "rag-presenter",
                "What does the source say?",
                session_id="test-rag-presenter-delegation",
            )
        finally:
            reset_session("test-rag-presenter-delegation")

    assert answer["reply"] == "The source says relevant evidence."
    search.assert_called_once_with("What does the source say?", 5, base_id="branch-1")
    assert chat.call_count == 2
    assert [event["tool"] for event in answer["tool_events"]] == [
        "call_subagent",
        "read_agent_scratchpad",
        "read_agent_scratchpad",
    ]
    result = memory_interface.read_memory("latest_subagent_result")
    assert result["latest_subagent_result"]["subagent_id"] == "rag-retriever"
    assert result["latest_subagent_result"]["payload"] == retrieval_payload
