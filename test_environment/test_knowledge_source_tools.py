import json
import tempfile
from contextlib import nullcontext
from pathlib import Path
import unittest
from unittest.mock import patch

from agentMemory import interface
from agentMemory import scratchpad
from core_engine import langgraph_tools
from orchestration import rag_retriever
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

    def test_rag_retriever_persists_success_nothing_found_and_error(self):
        cases = [
            (
                {
                    "knowledge_base_id": "branch-id",
                    "knowledge_base": "Leadership",
                    "results": [{"path": "notes.docx", "score": 0.8, "content": "Evidence"}],
                },
                "success",
            ),
            (
                {
                    "knowledge_base_id": "branch-id",
                    "knowledge_base": "Leadership",
                    "results": [],
                },
                "nothing_found",
            ),
            (RuntimeError("embedding service unavailable"), "error"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with patch.object(scratchpad, "DATA_DIR", temp_path), patch.object(
                scratchpad, "SCRATCHPAD_PATH", temp_path / "scratchpad.json"
            ), patch.object(
                rag_retriever.rag_config,
                "selected_knowledge_base_id",
                return_value="branch-id",
            ):
                for search_result, expected_status in cases:
                    with self.subTest(status=expected_status):
                        if isinstance(search_result, Exception):
                            search_patch = patch.object(
                                interface,
                                "search_knowledge_base",
                                side_effect=search_result,
                            )
                        else:
                            search_patch = patch.object(
                                interface,
                                "search_knowledge_base",
                                return_value=search_result,
                            )
                        with search_patch:
                            response = json.loads(
                                agent_memory_tool.call_subagent(
                                    "rag-retriever", "Find leadership evidence"
                                )
                            )

                        latest = interface.read_memory(
                            "latest_subagent_result"
                        )["latest_subagent_result"]
                        self.assertEqual(response["status"], expected_status)
                        self.assertEqual(latest["status"], expected_status)
                        self.assertEqual(latest["subagent_id"], "rag-retriever")
                        if expected_status == "error":
                            self.assertIn(
                                "embedding service unavailable",
                                latest["payload"]["error"],
                            )

    def test_vector_search_skips_incompatible_embedding_dimensions(self):
        chunks = [
            {
                "path": "notes.docx",
                "chunk_index": 0,
                "content": "Compatible evidence",
                "embedding": [1.0, 0.0, 0.0],
            },
            {
                "path": "old-notes.docx",
                "chunk_index": 0,
                "content": "Incompatible stale vector",
                "embedding": [1.0, 0.0],
            },
        ]
        with patch.object(
            interface.rag_config,
            "selected_knowledge_base_id",
            return_value="branch-id",
        ), patch.object(
            interface.rag_config,
            "get_knowledge_base",
            return_value={"id": "branch-id", "name": "Leadership"},
        ), patch.object(
            interface.rag_config,
            "database_context",
            return_value=nullcontext(),
        ), patch.object(
            interface.rag_database, "initialize"
        ), patch.object(
            interface.rag_database, "list_chunks", return_value=chunks
        ), patch.object(
            interface.ollama,
            "embed",
            return_value={"embeddings": [[1.0, 0.0, 0.0]]},
        ):
            result = interface.search_knowledge_base("leadership")

        self.assertEqual(result["skipped_incompatible_chunks"], 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["content"], "Compatible evidence")

    def test_scratchpad_rejects_unsupported_subagent_status(self):
        with self.assertRaisesRegex(ValueError, "Sub-agent status"):
            interface.store_subagent_result(
                "rag-retriever", "rag_retrieval", "no_results", {}
            )

    def test_rag_retriever_persists_bad_parameters_as_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with patch.object(scratchpad, "DATA_DIR", temp_path), patch.object(
                scratchpad, "SCRATCHPAD_PATH", temp_path / "scratchpad.json"
            ):
                response = json.loads(
                    agent_memory_tool.call_subagent(
                        "rag-retriever", "leadership query", parameters="{invalid"
                    )
                )
                latest = interface.read_memory(
                    "latest_subagent_result"
                )["latest_subagent_result"]

        self.assertEqual(response["status"], "error")
        self.assertEqual(latest["status"], "error")
        self.assertIn("JSON object", latest["payload"]["error"])

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
