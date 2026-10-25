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
                agent_memory_tool.search_knowledge_branch(
                    "leadership", knowledge_branch_id="archived-id"
                )
            )

        search.assert_called_once_with("leadership", 5, base_id="archived-id")
        self.assertEqual(result["knowledge_base_id"], "archived-id")

    def test_knowledge_catalog_uses_branch_names_and_ids(self):
        saved_branch = {
            "id": "branch-id",
            "name": "OLC500 Introduction To Leadership",
            "active": True,
            "selected": True,
            "exists": True,
            "documents": 4,
            "chunks": 12,
        }
        with patch.object(interface, "list_rag_bases", return_value=[saved_branch]):
            result = json.loads(agent_memory_tool.get_knowledge_catalog())

        self.assertEqual(result["title"], "Knowledge TOC")
        self.assertEqual(result["branches"], [{
            "name": "OLC500 Introduction To Leadership",
            "id": "branch-id",
            "status": "active",
            "selected": True,
            "folder_available": True,
            "indexed_documents": 4,
            "chunks": 12,
        }])

    def test_document_read_returns_indexed_text_without_embeddings(self):
        with patch.object(
            interface,
            "get_document",
            return_value={
                "path": "manual:Leadership notes",
                "chunks_data": [
                    {"content": "First passage", "embedding": [0.1, 0.2]},
                    {"content": "Second passage", "embedding": [0.3, 0.4]},
                ],
            },
        ) as read_document:
            result = json.loads(
                agent_memory_tool.read_knowledge_branch_document(
                    "manual:Leadership notes", "branch-id"
                )
            )

        read_document.assert_called_once_with("manual:Leadership notes", "branch-id")
        self.assertEqual(result["content"], "First passage\n\nSecond passage")
        self.assertEqual(result["chunks"], 2)
        self.assertNotIn("embedding", result)

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
