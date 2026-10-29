import json

import pytest

from file_manager import backend
from tools.code_change_preview import (
    changed_line_numbers,
    preview_code_change,
)
from orchestration.orchestration_telemetry import telemetry_bus
from tools import interface


def test_changed_line_numbers_track_replacements_insertions_and_deletions():
    assert changed_line_numbers("one\ntwo\nthree", "one\nTWO\nthree", "before") == [2]
    assert changed_line_numbers("one\nthree", "one\ntwo\nthree", "before") == [1]
    assert changed_line_numbers("one\ntwo\nthree", "one\nthree", "after") == [2]


def test_preview_is_read_only_and_emits_only_relative_path_and_lines(
    tmp_path, monkeypatch
):
    file_path = tmp_path / "src" / "app.py"
    file_path.parent.mkdir()
    file_path.write_text("first\nsecond\n", encoding="utf-8")
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    trace_id = "tr_code_preview_test"
    telemetry_bus.initialize_trace(trace_id)
    source = "first\nchanged\n"

    with telemetry_bus.agent_context(trace_id, "code-builder"):
        preview = preview_code_change("src/app.py", source)

    assert preview == {
        "status": "success",
        "path": "src/app.py",
        "changed_lines": [2],
        "file_exists": True,
    }
    assert file_path.read_text(encoding="utf-8") == "first\nsecond\n"
    event = telemetry_bus.get_trace_history(trace_id)[0]
    assert event["event_type"] == "CODE_CHANGE_PREVIEW"
    assert event["data"] == {
        "path": "src/app.py",
        "changed_lines": [2],
        "file_exists": True,
    }
    assert source not in json.dumps(event)


def test_preview_rejects_paths_outside_the_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    with pytest.raises(ValueError, match="traversal"):
        preview_code_change("../outside.py", "print('not written')")


def test_preview_marks_new_files_until_they_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    trace_id = "tr_code_new_file_preview"
    telemetry_bus.initialize_trace(trace_id)

    with telemetry_bus.agent_context(trace_id, "code-builder"):
        preview = preview_code_change("new_file.py", "print('new')\n")

    assert preview["file_exists"] is False
    event = telemetry_bus.get_trace_history(trace_id)[0]
    assert event["data"]["file_exists"] is False
    assert not (tmp_path / "new_file.py").exists()


def test_workspace_write_emits_applied_line_event(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    trace_id = "tr_code_applied_test"
    telemetry_bus.initialize_trace(trace_id)

    with telemetry_bus.agent_context(trace_id, "code-builder"):
        result = interface.write_file("app.py", "updated\n")

    assert result["path"] == "app.py"
    event = telemetry_bus.get_trace_history(trace_id)[0]
    assert event["event_type"] == "CODE_CHANGE_APPLIED"
    assert event["data"] == {
        "path": "app.py",
        "changed_lines": [1],
        "file_exists": True,
    }
