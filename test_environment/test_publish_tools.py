import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core_engine import agent_factory
from test_environment import interface


class TestPublishTools(unittest.TestCase):
    def test_publish_writes_selected_registered_tools_to_frontmatter(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            library = root / "library"
            test_agents = root / "test_agents"
            library.mkdir()
            (library / "tool-agent.md").write_text(
                "---\nid: tool-agent\nname: Tool Agent\nmode: agent\ntools:\n"
                "  - calculator\n---\n\nOld prompt\n",
                encoding="utf-8",
            )
            manifest = test_agents / "manifest.json"
            test_agents.mkdir()
            manifest.write_text("[]\n", encoding="utf-8")
            app = FastAPI()
            app.include_router(interface.router)
            client = TestClient(app)

            with (
                patch.object(agent_factory, "LIBRARY_ROOT", library),
                patch.object(interface, "TEST_AGENTS_DIR", test_agents),
                patch.object(interface.test_runner, "run_header_tests", return_value={"verdict": "ok"}),
            ):
                response = client.post(
                    "/api/testing/publish",
                    json={
                        "agent_id": "tool-agent",
                        "label": "prompt-creation",
                        "markdown": "# Tool Agent\n\nUpdated prompt.",
                        "environment": "prompt-creation",
                        "tools": ["map_files", "read_file", "write_file"],
                    },
                )

            self.assertEqual(response.status_code, 200, response.text)
            saved = (library / "tool-agent.md").read_text(encoding="utf-8")
            metadata = agent_factory.parse_yaml_frontmatter(saved)
            self.assertEqual(
                metadata["tools"],
                ["map_files", "read_file", "write_file"],
            )
            snapshot_file = test_agents / response.json()["snapshot"] / "tool-agent.md"
            self.assertEqual(
                agent_factory.parse_yaml_frontmatter(snapshot_file.read_text(encoding="utf-8"))["tools"],
                metadata["tools"],
            )
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))[0]["agent_id"], "tool-agent")

    def test_publish_rejects_unregistered_tool_names(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            library = Path(temporary_directory)
            (library / "tool-agent.md").write_text(
                "---\nid: tool-agent\nmode: agent\n---\n\nPrompt\n",
                encoding="utf-8",
            )
            app = FastAPI()
            app.include_router(interface.router)
            client = TestClient(app)

            with patch.object(agent_factory, "LIBRARY_ROOT", library):
                response = client.post(
                    "/api/testing/publish",
                    json={
                        "agent_id": "tool-agent",
                        "markdown": "Updated prompt.",
                        "tools": ["not_a_registered_tool"],
                    },
                )

            self.assertEqual(response.status_code, 400)
            self.assertIn("Unknown tools", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
