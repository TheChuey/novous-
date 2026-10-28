import json
from contextlib import nullcontext
import threading
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from agentMemory import indexer, interface, rag_config, rag_database, scratchpad
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
        self.rag_config_path_patch = patch.object(
            rag_config, "CONFIG_PATH", self.temp_path / "rag_config.json"
        )
        self.rag_data_dir_patch = patch.object(
            rag_config, "DATA_DIR", self.temp_path / "rag-data"
        )
        self.database_patch.start()
        self.scratchpad_path_patch.start()
        self.scratchpad_dir_patch.start()
        self.rag_config_path_patch.start()
        self.rag_data_dir_patch.start()
        self.addCleanup(self.database_patch.stop)
        self.addCleanup(self.scratchpad_path_patch.stop)
        self.addCleanup(self.scratchpad_dir_patch.stop)
        self.addCleanup(self.rag_config_path_patch.stop)
        self.addCleanup(self.rag_data_dir_patch.stop)
        rag_database.initialize()
        knowledge_folder = self.temp_path / "knowledge"
        knowledge_folder.mkdir()
        rag_config._write_config({
            "knowledge_bases": [{
                "id": "test",
                "name": "Test Knowledge",
                "path": str(knowledge_folder),
                "active": True,
                "legacy_index": True,
            }],
            "selected_knowledge_base": "test",
        })

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

    def test_invalid_rag_folder_is_rejected_without_default_folder(self):
        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "rag_config.json"):
            with self.assertRaises(ValueError):
                interface.set_rag_folder(str(self.temp_path / "missing"))
            with self.assertRaises(ValueError):
                interface.set_rag_folder("relative/path")
            with self.assertRaisesRegex(ValueError, "required"):
                interface.set_rag_folder("")

    def test_scanner_warns_and_retries_when_configured_folder_is_missing(self):
        stop_event = Mock()
        stop_event.is_set.side_effect = [False, True]

        with patch.object(
            indexer, "get_scan_job", return_value={"status": "idle"},
        ), patch.object(
            indexer, "start_scan_job",
            side_effect=FileNotFoundError("The RAG folder does not exist: missing"),
        ), patch.object(indexer, "_STOP_SCANNER", stop_event), \
                patch.object(indexer.LOGGER, "warning") as warning, \
                patch.object(indexer.LOGGER, "exception") as exception:
            indexer._scanner_loop()

        warning.assert_called_once()
        self.assertIn("Check the configured path", warning.call_args.args[0])
        self.assertEqual(
            str(warning.call_args.args[1]),
            "The RAG folder does not exist: missing",
        )
        stop_event.wait.assert_called_once_with(indexer.SCAN_INTERVAL_SECONDS)
        exception.assert_not_called()

    def test_named_knowledge_bases_keep_indexes_and_archived_records_separate(self):
        first_folder = self.temp_path / "first"
        second_folder = self.temp_path / "second"
        first_folder.mkdir()
        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "rag_config.json"), \
                patch.object(rag_config, "DATA_DIR", self.temp_path / "rag-data"), \
                patch.object(indexer, "_JOB_PATH", self.temp_path / "missing-folder-job.json"), \
                patch.object(indexer, "_SCAN_JOB", {"status": "idle"}), \
                patch("agentMemory.indexer.ollama.embed", return_value={"embeddings": [[0.1, 0.2]]}), \
                patch("agentMemory.interface.ollama.embed", return_value={"embeddings": [[0.1, 0.2]]}):
            first = interface.add_rag_base("Business Decisions", str(first_folder))
            second = interface.add_rag_base("Marketing", str(second_folder))
            interface.add_text_document("Decision notes", "business knowledge", first["id"])
            interface.add_text_document("Campaign notes", "marketing knowledge", second["id"])

            self.assertEqual(interface.list_documents(first["id"])[0]["path"], "manual:Decision notes")
            self.assertEqual(interface.list_documents(second["id"])[0]["path"], "manual:Campaign notes")
            self.assertEqual(interface.get_rag_status(second["id"])["name"], "Marketing")
            self.assertFalse(second["exists"])
            self.assertEqual(
                interface.search_knowledge_base("marketing", top_k=1)["results"][0]["content"],
                "marketing knowledge",
            )
            first_results = interface.search_knowledge_base(
                "decision", top_k=1, base_id=first["id"]
            )["results"]
            self.assertEqual(first_results[0]["content"], "business knowledge")
            self.assertEqual(interface.clear_rag_index(second["id"])["removed"], 1)
            self.assertEqual(len(interface.list_documents(first["id"])), 1)
            self.assertEqual(interface.list_documents(second["id"]), [])
            with self.assertRaises(FileNotFoundError):
                interface.start_rag_scan(second["id"])
            self.assertEqual(interface.get_rag_scan_job()["status"], "unavailable")

            interface.archive_rag_base(first["id"])
            archived = next(
                item for item in interface.list_rag_bases()
                if item["id"] == first["id"]
            )
            self.assertFalse(archived["active"])
            self.assertEqual(archived["path"], str(first_folder.resolve()))
            self.assertEqual(archived["documents"], 1)
            archived_results = interface.search_knowledge_base(
                "decision", top_k=1, base_id=first["id"]
            )
            self.assertEqual(archived_results["knowledge_base_id"], first["id"])
            self.assertEqual(
                archived_results["results"][0]["content"],
                "business knowledge",
            )

    def test_default_configuration_migrates_to_a_named_legacy_branch(self):
        folder = self.temp_path / "OLC500"
        folder.mkdir()
        rag_config._write_config({
            "knowledge_base_path": str(folder),
            "knowledge_bases": [
                {
                    "id": "default",
                    "name": "Default Knowledge Base",
                    "path": str(folder),
                    "active": True,
                    "legacy_index": True,
                },
                {
                    "id": "named",
                    "name": "OLC500",
                    "path": str(folder),
                    "active": True,
                    "legacy_index": False,
                },
            ],
            "selected_knowledge_base": "named",
        })

        bases = rag_config.list_knowledge_bases()
        legacy = next(base for base in bases if base["id"] == "default")
        self.assertEqual(legacy["name"], "OLC500 (legacy index)")
        self.assertTrue(legacy["legacy_index"])
        self.assertNotIn("Default Knowledge Base", [base["name"] for base in bases])
        renamed = rag_config.rename_knowledge_base("default", "Historical OLC500")
        self.assertEqual(renamed["name"], "Historical OLC500")
        self.assertEqual(
            rag_config.get_knowledge_base("default")["name"],
            "Historical OLC500",
        )
        self.assertNotIn("knowledge_base_path", json.loads(
            rag_config.CONFIG_PATH.read_text(encoding="utf-8")
        ))

    def test_empty_configuration_has_no_implicit_default_branch(self):
        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "empty_config.json"):
            rag_config._write_config({"knowledge_bases": []})
            self.assertEqual(rag_config.list_knowledge_bases(), [])
            with self.assertRaisesRegex(ValueError, "No knowledge source"):
                rag_config.selected_knowledge_base_id()

    def test_deleting_legacy_branch_removes_its_index_not_folder(self):
        folder = self.temp_path / "legacy-branch"
        folder.mkdir()
        source_file = folder / "keep.txt"
        source_file.write_text("Keep this source file.", encoding="utf-8")
        legacy_database = self.temp_path / "legacy-index.sqlite3"
        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "legacy_config.json"), \
                patch.object(rag_database, "DATABASE_PATH", legacy_database), \
                patch.object(indexer, "_SCAN_JOB", {"status": "idle"}):
            rag_config._write_config({
                "knowledge_bases": [{
                    "id": "legacy",
                    "name": "Legacy source",
                    "path": str(folder),
                    "active": True,
                    "legacy_index": True,
                }],
                "selected_knowledge_base": "legacy",
            })
            rag_database.initialize()
            rag_database.replace_document(
                "manual:notes", 0, 1, "now", [("saved", [0.1, 0.2])]
            )

            result = interface.delete_rag_base("legacy")

        self.assertEqual(result["documents_removed"], 1)
        self.assertFalse(legacy_database.exists())
        self.assertTrue(source_file.exists())

    def test_named_branch_can_be_renamed_and_deleted_without_deleting_folder(self):
        folder = self.temp_path / "branch-files"
        folder.mkdir()
        source_file = folder / "keep.txt"
        source_file.write_text("Do not delete this file.", encoding="utf-8")
        with patch("agentMemory.indexer.ollama.embed", return_value={"embeddings": [[0.1, 0.2]]}):
            base = interface.add_rag_base("Course branch", str(folder))
            interface.add_text_document("notes", "indexed knowledge", base["id"])

        database_file = rag_config.database_path(base["id"])
        self.assertTrue(database_file.is_file())
        renamed = interface.rename_rag_base(base["id"], "Leadership course")
        self.assertEqual(renamed["name"], "Leadership course")
        self.assertEqual(renamed["path"], str(folder.resolve()))
        result = interface.delete_rag_base(base["id"])

        self.assertEqual(result["name"], "Leadership course")
        self.assertEqual(result["documents_removed"], 1)
        self.assertFalse(result["folder_deleted"])
        self.assertEqual(source_file.read_text(encoding="utf-8"), "Do not delete this file.")
        self.assertFalse(database_file.exists())
        self.assertNotIn(base["id"], {entry["id"] for entry in interface.list_rag_bases()})

    def test_deleting_paused_branch_cancels_scheduled_resume(self):
        folder = self.temp_path / "paused-branch"
        folder.mkdir()
        base = interface.add_rag_base("Paused source", str(folder))
        job = {
            "status": "paused",
            "base_id": base["id"],
            "resume_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }
        with patch.object(indexer, "_JOB_PATH", self.temp_path / "paused_job.json"), \
                patch.object(indexer, "_SCAN_JOB", job), \
                patch.object(indexer, "_JOB_THREAD", None), \
                patch.object(indexer, "_STOP_REQUESTED", threading.Event()), \
                patch.object(indexer, "_PAUSE_REQUESTED", threading.Event()), \
                patch.object(indexer, "_RESUME_EVENT", threading.Event()), \
                patch.object(indexer, "_ERROR_DECISION_EVENT", threading.Event()):
            result = interface.delete_rag_base(base["id"])

            self.assertTrue(result["deleted"])
            self.assertEqual(indexer.get_scan_job()["status"], "stopped")
            self.assertIsNone(indexer.get_scan_job()["resume_at"])
            self.assertNotIn(base["id"], indexer.get_scan_job()["stopped_base_ids"])

    def test_scan_error_choice_can_skip_one_file_or_skip_all(self):
        folder = self.temp_path / "error-policy"
        folder.mkdir()
        (folder / "first.md").write_text("first", encoding="utf-8")
        (folder / "second.md").write_text("second", encoding="utf-8")
        decisions = iter(["skip", "skip_all"])
        with patch.object(indexer, "knowledge_base_folder", return_value=folder), \
                patch.object(rag_config, "database_context", return_value=nullcontext()), \
                patch.object(indexer.rag_database, "initialize"), \
                patch.object(indexer, "_purge_previous_folder", return_value=[]), \
                patch.object(indexer.rag_database, "delete_documents_under", return_value=[]), \
                patch.object(indexer, "index_file", side_effect=ValueError("parse failed")):
            result = indexer._scan_knowledge_base(
                False,
                "test",
                None,
                None,
                lambda path, error: next(decisions),
            )

        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["skipped"]), 2)
        self.assertTrue(all(item["status"] == "skipped" for item in result["skipped"]))

    def test_scan_error_can_retry_same_file(self):
        folder = self.temp_path / "retry-error"
        folder.mkdir()
        (folder / "retry.md").write_text("retry", encoding="utf-8")
        decisions = iter(["retry"])
        with patch.object(indexer, "knowledge_base_folder", return_value=folder), \
                patch.object(rag_config, "database_context", return_value=nullcontext()), \
                patch.object(indexer.rag_database, "initialize"), \
                patch.object(indexer, "_purge_previous_folder", return_value=[]), \
                patch.object(indexer.rag_database, "delete_documents_under", return_value=[]), \
                patch.object(
                    indexer,
                    "index_file",
                    side_effect=[ValueError("temporary failure"), {"status": "indexed"}],
                ) as index_file:
            result = indexer._scan_knowledge_base(
                False,
                "test",
                None,
                None,
                lambda path, error: next(decisions),
            )

        self.assertEqual(index_file.call_count, 2)
        self.assertEqual(result["indexed"], 1)
        self.assertEqual(result["errors"], [])

    def test_scan_error_decision_endpoint_state_can_skip_all(self):
        decision_event = threading.Event()
        job = {
            "status": "awaiting_decision",
            "error_mode": "ask",
            "pending_error": {"path": "problem.pdf", "error": "parser failed"},
        }
        with patch.object(indexer, "_SCAN_JOB", job), \
                patch.object(indexer, "_ERROR_DECISION_EVENT", decision_event):
            updated = indexer.decide_scan_error("skip_all")

        self.assertEqual(updated["status"], "running")
        self.assertEqual(updated["error_mode"], "skip_all")
        self.assertTrue(decision_event.is_set())
        with patch.object(indexer, "_SCAN_JOB", {"status": "running"}):
            with self.assertRaisesRegex(ValueError, "no indexing error"):
                indexer.decide_scan_error("skip")

    def test_source_names_are_unique_across_archived_branches(self):
        one = self.temp_path / "one"
        two = self.temp_path / "two"
        one.mkdir()
        two.mkdir()
        first = rag_config.add_knowledge_base("First", str(one))
        rag_config.archive_knowledge_base(first["id"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            rag_config.add_knowledge_base("First", str(two))
        with self.assertRaisesRegex(ValueError, "reserved"):
            rag_config.add_knowledge_base("Default Knowledge Base", str(two))

    def test_scan_job_can_pause_schedule_resume_and_persist_progress(self):
        from agentMemory import rag_config

        folder = self.temp_path / "scheduled"
        folder.mkdir()
        entered_scan = threading.Event()
        pause_gate = threading.Event()
        finished_scan = threading.Event()
        resume_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

        def controlled_scan(**kwargs):
            kwargs["progress"](discovered=2, completed=0, current="first.md")
            entered_scan.set()
            pause_gate.wait(2)
            kwargs["pause_point"]()
            kwargs["progress"](completed=1, indexed=1, current="")
            finished_scan.set()
            return {"errors": [], "removed": []}

        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "scan_config.json"), \
                patch.object(indexer, "_JOB_PATH", self.temp_path / "rag_scan_job.json"), \
                patch.object(indexer, "_SCAN_JOB", {"status": "idle"}), \
                patch.object(indexer, "_JOB_THREAD", None), \
                patch.object(indexer, "scan_knowledge_base", side_effect=controlled_scan), \
                patch.object(rag_config, "DATA_DIR", self.temp_path / "rag-data"):
            base = rag_config.add_knowledge_base("Scheduled", str(folder))
            base_id = base["id"]
            indexer.start_scan_job(base_id)
            self.assertTrue(entered_scan.wait(2))
            indexer.pause_scan_job()
            pause_gate.set()
            deadline = datetime.now() + timedelta(seconds=2)
            while indexer.get_scan_job()["status"] != "paused" and datetime.now() < deadline:
                threading.Event().wait(0.01)
            self.assertEqual(indexer.get_scan_job()["status"], "paused")

            indexer.schedule_scan_resume(resume_time)
            saved = json.loads((self.temp_path / "rag_scan_job.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["resume_at"], resume_time)
            indexer.resume_scan_job()
            self.assertTrue(finished_scan.wait(2))
            thread = indexer._JOB_THREAD
            if thread:
                thread.join(2)
            self.assertEqual(indexer.get_scan_job()["status"], "completed")
            self.assertIsNone(indexer.get_scan_job()["resume_at"])

    def test_stopping_scan_wakes_worker_and_blocks_automatic_restarts(self):
        folder = self.temp_path / "stopping"
        folder.mkdir()
        entered_scan = threading.Event()
        stop_gate = threading.Event()

        def controlled_scan(**kwargs):
            entered_scan.set()
            stop_gate.wait(2)
            kwargs["pause_point"]()
            self.fail("scan continued after it was stopped")

        with patch.object(rag_config, "CONFIG_PATH", self.temp_path / "stop_config.json"), \
                patch.object(indexer, "_JOB_PATH", self.temp_path / "rag_scan_job.json"), \
                patch.object(indexer, "_SCAN_JOB", {"status": "idle"}), \
                patch.object(indexer, "_JOB_THREAD", None), \
                patch.object(indexer, "_STOP_REQUESTED", threading.Event()), \
                patch.object(indexer, "_PAUSE_REQUESTED", threading.Event()), \
                patch.object(indexer, "_RESUME_EVENT", threading.Event()), \
                patch.object(indexer, "_ERROR_DECISION_EVENT", threading.Event()), \
                patch.object(indexer, "scan_knowledge_base", side_effect=controlled_scan), \
                patch.object(rag_config, "DATA_DIR", self.temp_path / "rag-data"), \
                patch.object(rag_config, "list_knowledge_bases", return_value=[
                    {"id": "stopping", "active": True}
                ]):
            indexer._RESUME_EVENT.set()
            base = rag_config.add_knowledge_base("Stopping", str(folder))
            indexer.start_scan_job(base["id"])
            self.assertTrue(entered_scan.wait(2))
            result = indexer.stop_scan_job()
            stop_gate.set()
            thread = indexer._JOB_THREAD
            if thread:
                thread.join(2)

            self.assertEqual(result["status"], "stopping")
            self.assertEqual(indexer.get_scan_job()["status"], "stopped")
            self.assertIn(base["id"], indexer.get_scan_job()["stopped_base_ids"])
            self.assertFalse(thread and thread.is_alive())
            deleted = interface.delete_rag_base(base["id"])
            self.assertTrue(deleted["deleted"])
            self.assertNotIn(base["id"], indexer.get_scan_job()["stopped_base_ids"])

if __name__ == "__main__":
    unittest.main()
