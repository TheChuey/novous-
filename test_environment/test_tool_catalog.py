import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from core_engine import tool_catalog
from server import app


class TestToolCatalog(unittest.TestCase):
    def setUp(self):
        tool_catalog.load_tools(reload=True)

    def tearDown(self):
        tool_catalog.load_tools(reload=True)

    def test_expected_builtin_tools_load(self):
        tools = tool_catalog.list_tools()
        names = {t["name"] for t in tools}
        expected = {
            # core_engine/core_tools.py
            "calculator",
            "rag_agent_tool",
            "agent_info",
            "extract_docstrings",
            "search_workspace",
            "project_status",
            "run_python_code",
            "send_code_to_editor",
            "run_code_in_editor",
            "ask_user_questions",
            "read_file",
            "write_file",
            "editor",
            "delete_file",
            "map_files",
            "read_agent_scratchpad",
            "get_knowledge_catalog",
            "search_knowledge_branch",
            "list_knowledge_branch_documents",
            "read_knowledge_branch_document",
        }
        for exp in expected:
            self.assertIn(exp, names)
        self.assertEqual(len(tools), 21)

    def test_tools_directory_contains_only_the_file_tools_and_promoted_module(self):
        files = {path.name for path in tool_catalog.TOOLS_DIR.iterdir() if path.is_file()}
        self.assertEqual(
            files,
            {
                "__init__.py",
                "allowed_paths.json",
                "delete_file_tool.py",
                "editor_tool.py",
                "interface.py",
                "map_files_tool.py",
                "agent_memory_tool.py",
                "promoted_tools.py",
                "read_tool.py",
                "write_tool.py",
            },
        )

    def test_get_load_errors_exists(self):
        errors = tool_catalog.get_load_errors()
        self.assertIsInstance(errors, dict)
        self.assertEqual(errors, {})

    def test_temp_dir_good_and_broken_module(self):
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            good_file = temp_path / "good_tool.py"
            good_file.write_text(
                "from core_engine.tool_catalog import tool\n\n"
                "@tool\ndef sample_good_tool():\n    return 'ok'\n",
                encoding="utf-8",
            )
            broken_file = temp_path / "broken_tool.py"
            broken_file.write_text("invalid python code :::\n", encoding="utf-8")

            old_tools_dir = tool_catalog.TOOLS_DIR
            try:
                tool_catalog.TOOLS_DIR = temp_path
                tool_catalog.load_tools(reload=True)

                errors = tool_catalog.get_load_errors()
                self.assertIn("broken_tool.py", errors)
                self.assertIn("sample_good_tool", tool_catalog.REGISTRY)

                client = TestClient(app)
                resp = client.get("/api/tools")
                self.assertEqual(resp.status_code, 200)
                body = resp.json()
                registered_names = [t["name"] for t in body["tools"]]
                self.assertIn("sample_good_tool", registered_names)
                self.assertTrue(any("broken_tool.py" in w for w in body["warnings"]))
            finally:
                tool_catalog.TOOLS_DIR = old_tools_dir
                tool_catalog.load_tools(reload=True)

    def test_all_agent_refs_resolve_and_report(self):
        report = tool_catalog.get_catalog_report()
        self.assertIn("tools", report)
        self.assertIn("providers", report)
        self.assertIn("load_errors", report)
        self.assertIn("missing_agent_tools", report)
        self.assertIn("warnings", report)

        self.assertEqual(report["missing_agent_tools"], {})
        self.assertEqual(tool_catalog.unknown_tool_names(["calculator", "read_file"]), [])
        self.assertEqual(
            tool_catalog.unknown_tool_names(["calculator", "unknown_tool_xyz"]),
            ["unknown_tool_xyz"],
        )


if __name__ == "__main__":
    unittest.main()
