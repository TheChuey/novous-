import json
import unittest
from unittest.mock import patch

from agentMemory import interface
from core_engine import langgraph_tools
from tools import agent_memory_tool


class TestKnowledgeSourceTools(unittest.TestCase):
    def test_search_tool_targets_archived_source_id(self):
        with patch.object(
            interface,
            "search_knowledge_base",
            return_value={"knowledge_base_id": "archived-id", "results": []},
        ) as search:
            result = json.loads(
                agent_memory_tool.search_knowledge_base(
                    "leadership", knowledge_base_id="archived-id"
                )
            )

        search.assert_called_once_with("leadership", 5, base_id="archived-id")
        self.assertEqual(result["knowledge_base_id"], "archived-id")

    def test_source_listing_includes_archived_records(self):
        archived_source = {"id": "archived-id", "name": "OLC500", "active": False}
        with patch.object(interface, "list_rag_bases", return_value=[archived_source]):
            result = json.loads(agent_memory_tool.list_knowledge_sources())

        self.assertEqual(result, [archived_source])

    def test_langgraph_search_accepts_archived_source_id(self):
        with patch(
            "agentMemory.interface.search_knowledge_base",
            return_value={"knowledge_base_id": "archived-id", "results": []},
        ) as search:
            langgraph_tools.rag_agent_tool.invoke(
                {
                    "query": "leadership",
                    "top_k": 3,
                    "knowledge_base_id": "archived-id",
                }
            )

        search.assert_called_once_with("leadership", 3, "", "archived-id")


if __name__ == "__main__":
    unittest.main()
