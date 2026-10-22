import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentMemory import interface, rag_database, scratchpad
from agentMemory.indexer import _chunk_text


class TestAgentMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.database_patch = patch.object(
            rag_database, "DATABASE_PATH", self.temp_path / "knowledge.sqlite3"
        )
        self.scratchpad_path_patch = patch.object(
            scratchpad, "SCRATCHPAD_PATH", self.temp_path / "scratchpad.json"
        )
        self.scratchpad_dir_patch = patch.object(
            scratchpad, "DATA_DIR", self.temp_path
        )
        self.database_patch.start()
        self.scratchpad_path_patch.start()
        self.scratchpad_dir_patch.start()
        self.addCleanup(self.database_patch.stop)
        self.addCleanup(self.scratchpad_path_patch.stop)
        self.addCleanup(self.scratchpad_dir_patch.stop)
        rag_database.initialize()

    def test_scratchpad_stores_latest_read_and_map(self):
        read = interface.store_read("notes.txt", "remember this", "summarize")
        interface.store_read("second.txt", "also remember this", "compare")
        mapped = interface.store_map({"name": "workspace"}, "workspace")

        memory = interface.read_memory()
        self.assertEqual(memory["latest_read"]["content"], "also remember this")
        self.assertEqual(memory["latest_read"]["request"], "compare")
        self.assertEqual(
            [entry["path"] for entry in memory["read_history"]],
            ["notes.txt", "second.txt"],
        )
        self.assertEqual(memory["latest_map"]["tree"], {"name": "workspace"})
        self.assertEqual(read["path"], mapped["path"])

    def test_read_history_is_bounded_and_clear_removes_saved_memory(self):
        for index in range(scratchpad.MAX_READ_HISTORY + 3):
            interface.store_read(f"file-{index}.txt", str(index))

        history = interface.read_memory()["read_history"]
        self.assertEqual(len(history), scratchpad.MAX_READ_HISTORY)
        self.assertEqual(history[0]["path"], "file-3.txt")
        self.assertEqual(history[-1]["path"], f"file-{scratchpad.MAX_READ_HISTORY + 2}.txt")

        self.assertTrue(scratchpad.clear_memory()["cleared"])
        self.assertEqual(interface.read_memory(), {})

    def test_document_crud_and_semantic_search(self):
        rag_database.replace_document(
            "workspace/Knowledge Base/guide.md",
            1,
            12,
            "2025-01-01T00:00:00+00:00",
            [
                ("cats and kittens", [1.0, 0.0]),
                ("space and planets", [0.0, 1.0]),
            ],
        )
        with patch("agentMemory.interface.ollama.embed", return_value={"embeddings": [[0.9, 0.1]]}):
            result = interface.search_knowledge_base("cats", top_k=1)

        self.assertEqual(result["results"][0]["content"], "cats and kittens")
        self.assertEqual(interface.list_documents()[0]["chunks"], 2)
        self.assertTrue(interface.delete_document("workspace/Knowledge Base/guide.md")["deleted"])
        self.assertEqual(interface.list_documents(), [])

    def test_stale_document_cleanup_normalizes_path_separators(self):
        rag_database.replace_document(
            "workspace\\Knowledge Base\\keep.md", 1, 1, "now", []
        )
        rag_database.replace_document(
            "workspace/Knowledge Base/remove.md", 1, 1, "now", []
        )

        removed = rag_database.delete_documents_under(
            "workspace/Knowledge Base",
            {"workspace/Knowledge Base/keep.md"},
        )

        self.assertEqual(removed, ["workspace/Knowledge Base/remove.md"])
        self.assertEqual(
            [item["path"] for item in rag_database.list_documents()],
            ["workspace\\Knowledge Base\\keep.md"],
        )

    def test_chunking_preserves_text_and_bounds_chunk_size(self):
        text = ("line of knowledge\n\n" * 120).strip()

        chunks = _chunk_text(text)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 1400 for chunk in chunks))
        self.assertTrue(all(chunk in text for chunk in chunks))

    def test_configured_folder_is_scanned_and_root_change_purges_old_entries(self):
        from agentMemory import indexer, rag_config

        first = self.temp_path / "first"
        second = self.temp_path / "second"
        first.mkdir()
        second.mkdir()
        (first / "a.md").write_text("alpha", encoding="utf-8")
        (second / "b.md").write_text("beta", encoding="utf-8")
        embed = {"embeddings": [[0.1, 0.2]]}
        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "rag_config.json"), \
                patch("agentMemory.indexer.ollama.embed", return_value=embed):
            self.assertEqual(
                interface.set_rag_folder(str(first))["path"], str(first.resolve())
            )
            result = indexer.scan_knowledge_base()
            self.assertEqual(result["indexed"], 1)
            self.assertEqual(
                [d["path"] for d in interface.list_documents()],
                [(first / "a.md").resolve().as_posix()],
            )

            interface.set_rag_folder(str(second))
            result = indexer.scan_knowledge_base()
            self.assertEqual(len(result["removed"]), 1)
            self.assertEqual(
                [d["path"] for d in interface.list_documents()],
                [(second / "b.md").resolve().as_posix()],
            )

            cleared = interface.clear_rag_index()
            self.assertEqual(cleared["removed"], 1)
            self.assertEqual(cleared["documents"], 0)

    def test_manual_text_is_added_listed_and_deleted(self):
        with patch("agentMemory.indexer.ollama.embed", return_value={"embeddings": [[0.1, 0.2]]}):
            result = interface.add_text_document("  My   note ", "some knowledge")
        self.assertEqual(result["path"], "manual:My note")
        overview = interface.get_rag_overview()
        self.assertEqual(overview["types"], {"manual": 1})
        self.assertEqual(overview["files"][0]["chunks"], 1)
        with self.assertRaises(ValueError):
            interface.add_text_document("", "text")
        with self.assertRaises(ValueError):
            interface.add_text_document("title", "   ")
        interface.delete_document("manual:My note")
        self.assertEqual(interface.get_rag_overview()["documents"], 0)

    def test_invalid_rag_folder_is_rejected_and_empty_restores_default(self):
        from agentMemory import rag_config

        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "rag_config.json"):
            with self.assertRaises(ValueError):
                interface.set_rag_folder(str(self.temp_path / "missing"))
            with self.assertRaises(ValueError):
                interface.set_rag_folder("relative/path")
            self.assertEqual(
                interface.set_rag_folder("")["path"], str(rag_config.DEFAULT_KNOWLEDGE_BASE)
            )


if __name__ == "__main__":
    unittest.main()
