import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentMemory import interface as agent_memory
from fastapi.testclient import TestClient

from core_engine import tool_catalog
from core_engine.runtime import Agent, AgentProfile
from server import app
from tools import interface


class TestToolsInterface(unittest.TestCase):
    def setUp(self):
        tool_catalog.load_tools(reload=True)

    def tearDown(self):
        tool_catalog.load_tools(reload=True)

    def test_agent_tool_events_include_bounded_return_results(self):
        def successful_tool():
            return {"path": "notes/result.txt", "written": True}

        def failing_tool():
            raise ValueError("write failed")

        agent = Agent(
            model="test-model",
            tools=[successful_tool, failing_tool],
            profile=AgentProfile(mode="agent"),
        )
        agent.act(
            {"function": {"name": "successful_tool", "arguments": {}}},
            "native",
        )
        agent.act(
            {"function": {"name": "failing_tool", "arguments": {}}},
            "native",
        )

        success, failure = agent.tool_events
        self.assertEqual(success["status"], "success")
        self.assertEqual(
            json.loads(success["result"]),
            {"path": "notes/result.txt", "written": True},
        )
        self.assertEqual(failure["status"], "error")
        self.assertEqual(failure["error"], "write failed")

    def test_agent_executes_tool_json_embedded_in_explanatory_text(self):
        calls = []

        def read_agent_scratchpad(memory_type="all"):
            calls.append(memory_type)
            return '{"latest_subagent_result":{"status":"success"}}'

        agent = Agent(
            model="test-model",
            tools=[read_agent_scratchpad],
            profile=AgentProfile(mode="agent"),
        )
        responses = [
            {
                "message": {
                    "content": (
                        "Here is the JSON for a function call:\n"
                        '{"name": "read_agent_scratchpad", "parameters": '
                        '{"memory_type": "latest_subagent_result"}}'
                    )
                }
            },
            {"message": {"content": "Scratchpad retrieval succeeded."}},
        ]
        with patch("core_engine.runtime.ollama.chat", side_effect=responses):
            reply = agent.think("Check the latest sub-agent result")

        self.assertEqual(calls, ["latest_subagent_result"])
        self.assertEqual(reply, "Scratchpad retrieval succeeded.")
        self.assertEqual(agent.tool_events[0]["tool"], "read_agent_scratchpad")
        self.assertEqual(agent.tool_events[0]["origin"], "text_json")

    def test_rag_presenter_format_answer_json_becomes_markdown(self):
        agent = Agent(
            model="test-model",
            tools=[],
            profile=AgentProfile(id="rag-presenter", mode="agent"),
        )
        response = (
            "Here is the response:\n"
            '{"name":"format_answer","parameters":{"query":"leadership",'
            '"answer":"The plan emphasizes servant leadership.",'
            '"evidence":[{"path":"leadership-plan.docx","content":"Evidence"}]}}'
        )
        with patch(
            "core_engine.runtime.ollama.chat",
            return_value={"message": {"content": response}},
        ):
            reply = agent.think("Tell me about the leadership plan")

        self.assertEqual(
            reply,
            "The plan emphasizes servant leadership.\n\n"
            "**Sources**\n- leadership-plan.docx",
        )

    def test_streaming_agent_does_not_emit_embedded_tool_call_as_chat_text(self):
        calls = []

        def read_agent_scratchpad(memory_type="all"):
            calls.append(memory_type)
            return '{"latest_subagent_result":{"status":"success"}}'

        agent = Agent(
            model="test-model",
            tools=[read_agent_scratchpad],
            profile=AgentProfile(mode="agent"),
        )
        stream_responses = [
            [
                {"message": {"content": "Here is the JSON for a function call:\n"}},
                {
                    "message": {
                        "content": (
                            '{"name": "read_agent_scratchpad", "parameters": '
                            '{"memory_type": "latest_subagent_result"}}'
                        )
                    }
                },
            ],
            [{"message": {"content": "Scratchpad retrieval succeeded."}}],
        ]
        with patch(
            "core_engine.runtime.ollama.chat",
            side_effect=[
                iter(stream_responses[0]),
                iter(stream_responses[1]),
            ],
        ):
            events = list(agent.think_stream("Check the latest result"))

        self.assertEqual(calls, ["latest_subagent_result"])
        self.assertEqual(
            [event["text"] for event in events if event["type"] == "token"],
            ["Scratchpad retrieval succeeded."],
        )
        self.assertEqual(
            [event["event"]["tool"] for event in events if event["type"] == "tool_event"],
            ["read_agent_scratchpad"],
        )

    def test_scratchpad_api_reads_and_clears_saved_memory(self):
        from agentMemory import scratchpad

        client = TestClient(app)
        with patch.object(scratchpad, "read_memory", return_value={"latest_read": {"path": "a.txt"}}):
            response = client.get("/api/agent-memory/scratchpad")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"latest_read": {"path": "a.txt"}})

        with patch.object(scratchpad, "clear_memory", return_value={"cleared": True}):
            response = client.delete("/api/agent-memory/scratchpad")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"cleared": True})

    def test_agent_tool_event_truncates_large_return_results(self):
        def large_tool():
            return "x" * 4000

        agent = Agent(
            model="test-model",
            tools=[large_tool],
            profile=AgentProfile(mode="agent"),
        )
        agent.act(
            {"function": {"name": "large_tool", "arguments": {}}},
            "native",
        )

        event = agent.tool_events[0]
        self.assertEqual(len(event["result"]), 3000)
        self.assertTrue(event["result_truncated"])

    def test_python_doorway_delegates_to_file_and_editor_services(self):
        with (
            patch.object(
                interface.file_manager_service,
                "directory_tree",
                return_value={"path": "docs"},
            ) as tree,
            patch.object(
                interface.file_manager_service,
                "list_directory",
                return_value={"entries": []},
            ) as listing,
            patch.object(
                interface.file_manager_service,
                "read_file",
                return_value={"path": "docs/readme.md", "content": "hello"},
            ) as read,
            patch.object(
                interface.file_manager_service,
                "write_file",
                return_value={"path": "docs/readme.md", "bytes_written": 5},
            ) as write,
            patch.object(
                interface.file_manager_service,
                "delete",
                return_value={"path": "docs/old.txt", "deleted": True},
            ) as delete,
            patch.object(
                interface.editor_operations,
                "read_file_content",
                return_value={"path": "readme.md", "content": "editor"},
            ) as editor_read,
            patch.object(
                interface.editor_operations,
                "write_file_content",
                return_value={"path": "readme.md", "bytes_written": 6},
            ) as editor_write,
            patch.object(
                interface.editor_operations,
                "get_directory_tree",
                return_value={"path": "", "children": []},
            ) as editor_tree,
            patch.object(
                interface.editor_operations,
                "delete_path",
                return_value={"path": "old.txt", "deleted": True},
            ) as editor_delete,
        ):
            self.assertEqual(interface.map_files("docs"), {"path": "docs"})
            self.assertEqual(interface.list_directory("docs"), {"entries": []})
            self.assertEqual(
                interface.read_file("docs/readme.md")["content"], "hello"
            )
            self.assertEqual(
                interface.write_file("docs/readme.md", "hello")["bytes_written"], 5
            )
            self.assertTrue(interface.delete_file("docs/old.txt")["deleted"])
            self.assertEqual(
                interface.editor("read", path="readme.md")["content"], "editor"
            )
            self.assertEqual(
                interface.editor("write", path="readme.md", content="editor")[
                    "bytes_written"
                ],
                6,
            )
            self.assertEqual(
                interface.editor("tree")["children"], []
            )
            self.assertTrue(interface.editor("delete", path="old.txt")["deleted"])

        tree.assert_called_once_with("docs")
        listing.assert_called_once_with("docs")
        read.assert_called_once_with("docs/readme.md")
        write.assert_called_once_with("docs/readme.md", "hello")
        delete.assert_called_once_with("docs/old.txt")
        editor_read.assert_called_once_with("readme.md")
        editor_write.assert_called_once_with("readme.md", "editor")
        editor_tree.assert_called_once_with("")
        editor_delete.assert_called_once_with("old.txt")

    def test_editor_doorway_rejects_unknown_action(self):
        with self.assertRaisesRegex(ValueError, "Unsupported editor action"):
            interface.editor("rename", path="readme.md")

    def test_map_page_endpoint_uses_allowed_root_mapping_service(self):
        tree = {
            "name": "root",
            "type": "directory",
            "children": [{"name": "visible.txt", "type": "file"}],
        }
        with patch.object(interface, "map_files", return_value=tree):
            response = TestClient(app).post(
                "/api/tools/map-page",
                json={
                    "path": "",
                    "max_depth": 1,
                    "include_files": True,
                    "offset": 0,
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("visible.txt", response.json()["text"])

    def test_agent_file_tools_use_the_shared_doorway(self):
        functions = {
            name: tool_catalog.REGISTRY[name]["function"]
            for name in ("map_files", "read_file", "write_file", "editor", "delete_file")
        }
        with (
            patch.object(interface, "map_files", return_value={"name": "root"}) as map_files,
            patch.object(
                interface,
                "read_file_bytes",
                return_value={
                    "path": "docs/readme.md",
                    "resolved_path": Path("docs/readme.md"),
                    "size_bytes": 5,
                    "content": b"hello",
                },
            ) as read_file_bytes,
            patch.object(agent_memory, "store_read", return_value={
                "path": "agentMemory/data/scratchpad.json",
                "updated_at": "2026-10-21T00:00:00+00:00",
            }),
            patch.object(agent_memory, "store_map", return_value={
                "path": "agentMemory/data/scratchpad.json",
                "updated_at": "2026-10-21T00:00:00+00:00",
            }),
            patch.object(
                interface,
                "write_file",
                side_effect=[
                    {"path": "docs/readme.md", "bytes_written": 5},
                ],
            ) as write_file,
            patch.object(interface, "editor", return_value={"path": "readme.md"}) as editor,
            patch.object(
                interface,
                "delete_file",
                return_value={"path": "docs/old.txt", "deleted": True},
            ) as delete_file,
        ):
            self.assertEqual(
                json.loads(functions["map_files"]("docs"))["name"], "root"
            )
            self.assertEqual(
                json.loads(functions["read_file"]("docs/readme.md"))["content"],
                "hello",
            )
            read_file_bytes.assert_called_once_with(
                "docs/readme.md", 1_000_000
            )
            self.assertEqual(
                json.loads(functions["write_file"]("docs/readme.md", "hello"))[
                    "bytes_written"
                ],
                5,
            )
            self.assertEqual(
                json.loads(functions["editor"]("tree"))["path"], "readme.md"
            )
            self.assertTrue(
                json.loads(functions["delete_file"]("docs/old.txt"))["deleted"]
            )

        map_files.assert_called_once_with("docs")
        self.assertEqual(write_file.call_count, 1)
        editor.assert_called_once_with("tree", path="", content="")
        delete_file.assert_called_once_with("docs/old.txt")

    def test_register_get_remove_round_trip(self):
        source = (
            "def calc_square(n: int) -> int:\n"
            "    \"\"\"Calculate square of n.\"\"\"\n"
            "    return n * n\n"
        )
        with tempfile.TemporaryDirectory() as td:
            promoted_path = Path(td) / "promoted.py"
            header = (
                '"""Custom tools promoted from the Function Testing Workbench."""\n'
                'from core_engine.tool_catalog import tool\n\n'
                '# PROMOTION_MARKER: tools appended below will be registered as custom tools\n\n'
            )
            promoted_path.write_text(header, encoding="utf-8", newline="\n")
            initial_bytes = promoted_path.read_bytes()

            with patch("tools.interface.PROMOTED_MODULE_PATH", promoted_path):
                # 1. Register
                reg_result = interface.register_tool(source, "calc_square")
                self.assertEqual(reg_result["name"], "calc_square")
                self.assertEqual(reg_result["path"], "tools/promoted_tools.py")

                # 2. Get tool callable
                fn = interface.get_tool("calc_square")
                self.assertIsNotNone(fn)
                self.assertEqual(fn(5), 25)

                library = {t["name"]: t for t in interface.list_tools_directory()}
                self.assertTrue(library["calc_square"]["custom"])

                # 3. Get tool source
                src_info = interface.get_tool_source("calc_square")
                self.assertEqual(src_info["name"], "calc_square")
                self.assertIn("calc_square", src_info["source"])
                self.assertEqual(src_info["path"], "tools/promoted_tools.py")

                # 4. Remove tool
                del_result = interface.remove_tool("calc_square")
                self.assertTrue(del_result["deleted"])
                self.assertIsNone(interface.get_tool("calc_square"))

                # 5. Check byte-identical
                after_bytes = promoted_path.read_bytes()
                self.assertEqual(initial_bytes, after_bytes)

    def test_router_endpoints(self):
        client = TestClient(app)

        # GET /api/tools
        resp = client.get("/api/tools")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("tools", data)
        self.assertIn("providers", data)
        self.assertIn("warnings", data)
        self.assertIn("calculator", [t["name"] for t in data["tools"]])

        # GET /api/tools/calculator
        resp = client.get("/api/tools/calculator")
        self.assertEqual(resp.status_code, 200)
        calc_data = resp.json()
        self.assertEqual(calc_data["name"], "calculator")
        self.assertEqual(calc_data["provider"], "core_engine")

        # GET /api/tools/health
        resp = client.get("/api/tools/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

    def test_rag_branch_rename_and_delete_routes(self):
        client = TestClient(app)
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        (folder / "keep.txt").write_text("Keep user files.", encoding="utf-8")
        config_path = folder / "rag_config.json"
        index_dir = folder / "indexes"
        with patch("agentMemory.rag_config.CONFIG_PATH", config_path), \
                patch("agentMemory.rag_config.DATA_DIR", index_dir), \
                patch("agentMemory.indexer._SCAN_JOB", {"status": "idle"}):
            base = agent_memory.add_rag_base("Original branch", str(folder))
            renamed = client.put(
                f"/api/rag/bases/{base['id']}",
                json={"name": "Renamed branch"},
            )
            self.assertEqual(renamed.status_code, 200, renamed.text)
            self.assertEqual(renamed.json()["name"], "Renamed branch")

            deleted = client.delete(f"/api/rag/bases/{base['id']}")
            self.assertEqual(deleted.status_code, 200, deleted.text)
            self.assertEqual(deleted.json()["name"], "Renamed branch")
            self.assertFalse(deleted.json()["folder_deleted"])
            self.assertEqual((folder / "keep.txt").read_text(encoding="utf-8"), "Keep user files.")
            self.assertEqual(agent_memory.list_rag_bases(), [])

    def test_open_rag_branch_folder_route(self):
        client = TestClient(app)
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        config_path = folder / "rag_config.json"
        index_dir = folder / "indexes"
        with patch("agentMemory.rag_config.CONFIG_PATH", config_path), \
                patch("agentMemory.rag_config.DATA_DIR", index_dir), \
                patch("agentMemory.indexer._SCAN_JOB", {"status": "idle"}):
            base = agent_memory.add_rag_base("Local branch", str(folder))
            with patch("agentMemory.interface.os.startfile", create=True) as open_folder:
                response = client.post(f"/api/rag/bases/{base['id']}/open-folder")

            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), {"opened": True, "path": str(folder.resolve())})
            open_folder.assert_called_once_with(str(folder.resolve()))

            missing = client.post("/api/rag/bases/unknown/open-folder")
            self.assertEqual(missing.status_code, 404)

    def test_registered_tool_library_shows_only_tools_package_functions(self):
        client = TestClient(app)
        response = client.get("/api/tools/library")

        self.assertEqual(response.status_code, 200, response.text)
        names = {tool["name"] for tool in response.json()["tools"]}
        self.assertEqual(
            names,
            {
                "map_files",
                "read_file",
                "write_file",
                "create_folder",
                "editor",
                "delete_file",
                "read_agent_scratchpad",
                "call_subagent",
                "write_agent_scratchpad",
                "get_knowledge_catalog",
                "search_knowledge_branch",
                "list_knowledge_branch_documents",
                "read_knowledge_branch_document",
            },
        )
        self.assertGreater(len(tool_catalog.list_tools()), len(names))

        with tempfile.TemporaryDirectory() as td:
            promoted_path = Path(td) / "promoted.py"
            with patch("tools.interface.PROMOTED_MODULE_PATH", promoted_path):
                # POST /api/tools/register
                tool_code = "def custom_api_test(x: int) -> int:\n    return x + 10\n"
                reg_resp = client.post(
                    "/api/tools/register",
                    json={"source": tool_code, "name": "custom_api_test"},
                )
                self.assertEqual(reg_resp.status_code, 200)
                self.assertEqual(reg_resp.json()["name"], "custom_api_test")

                # GET /api/tools/{name}
                get_resp = client.get("/api/tools/custom_api_test")
                self.assertEqual(get_resp.status_code, 200)
                self.assertTrue(get_resp.json()["custom"])

                # DELETE /api/tools/{name}
                del_resp = client.delete("/api/tools/custom_api_test")
                self.assertEqual(del_resp.status_code, 200)

                # GET after delete -> 404
                get_after = client.get("/api/tools/custom_api_test")
                self.assertEqual(get_after.status_code, 404)


if __name__ == "__main__":
    unittest.main()
