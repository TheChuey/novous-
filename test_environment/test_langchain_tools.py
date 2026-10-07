from pathlib import Path
import sys

from ollama._types import Tool as OllamaTool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "headless_app"))

from bridge.client import _relpath
from engine.agents.factory import _session_aware
from engine.core.agent import Agent, AgentProfile
from engine.core.llm import _ollama_tool_schema
from tools.registry import list_tools, resolve_tools
from tools.state import FileSession


def test_registry_tools_have_ollama_compatible_langchain_schemas():
    assert len(list_tools()) == 9

    for tool in resolve_tools(list_tools()):
        assert OllamaTool.model_validate(_ollama_tool_schema(tool))


def test_file_tools_write_and_delete_without_approval(tmp_path):
    target = tmp_path / "result.txt"
    write_tool = resolve_tools(["write_text_file"])[0]
    delete_tool = resolve_tools(["delete_files"])[0]

    result = write_tool.invoke({
        "name": target.name,
        "content": "tool output",
        "output_path": str(tmp_path),
    })
    assert result["success"] is True
    assert target.read_text(encoding="utf-8") == "tool output"

    deleted = delete_tool.invoke({"file_list": [str(target)]})
    assert deleted["success"] is True
    assert deleted["data"]["results"][str(target)] == "deleted"
    assert not target.exists()


def test_workspace_directory_creation_and_text_search(tmp_path):
    directory = tmp_path / "nested" / "notes"
    created = resolve_tools(["create_directory"])[0].invoke({"path": str(directory)})
    assert created["success"] is True

    file_path = directory / "summary.md"
    file_path.write_text("LangChain tools are ready.\nAnother line.\n", encoding="utf-8")
    matches = resolve_tools(["search_workspace"])[0].invoke({
        "query": "LANGCHAIN TOOLS",
        "path": str(directory),
    })
    assert matches["success"] is True
    assert matches["data"]["matches"] == [
        {"path": str(file_path), "line": 1, "text": "LangChain tools are ready."}
    ]


def test_bound_tools_record_session_results_and_enforce_provider_root(tmp_path):
    class Provider:
        workspace_root = str(tmp_path)

        def __init__(self):
            self.files = {}

        def relpath(self, path):
            return _relpath(Path(self.workspace_root), path)

        def create(self, rel, content):
            self.files[rel] = content

        def exists(self, rel):
            return rel in self.files

        def delete(self, rel):
            del self.files[rel]

    provider = Provider()
    session = FileSession()
    write_tool = _session_aware(resolve_tools(["write_text_file"], provider)[0], session)

    result = write_tool.invoke({
        "name": "result.txt",
        "content": "saved through provider",
        "output_path": str(tmp_path),
    })
    assert result["success"] is True
    assert provider.files["result.txt"] == "saved through provider"
    assert session.output_files == [str(tmp_path / "result.txt")]

    blocked = write_tool.invoke({
        "name": "outside.txt",
        "content": "must not be written",
        "output_path": str(tmp_path.parent),
    })
    assert blocked["success"] is False
    assert provider.files == {"result.txt": "saved through provider"}


def test_agent_invokes_langchain_structured_tools():
    tool = resolve_tools(["get_current_date"])[0]
    agent = Agent(model=None, tools=[tool], profile=AgentProfile())

    result = agent.act(
        {"function": {"name": "get_current_date", "arguments": {}}},
        origin="test",
    )

    assert result
    assert agent.tool_events[0]["status"] == "success"
