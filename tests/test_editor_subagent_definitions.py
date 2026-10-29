import pytest

from editor import editor_operations


def test_subagent_yaml_definition_can_be_opened_in_editor():
    result = editor_operations.read_file_content(
        "subAgentLibrary/code-builder.yaml"
    )

    assert result["path"] == "subAgentLibrary/code-builder.yaml"
    assert "id: code-builder" in result["content"]


def test_editor_rejects_subagent_paths_outside_yaml_library():
    with pytest.raises(ValueError, match="Only YAML files directly"):
        editor_operations.resolve_project_path("subAgentLibrary/../library/rag-presenter.md")

    with pytest.raises(ValueError, match="Only YAML files directly"):
        editor_operations.resolve_project_path("subAgentLibrary/nested/worker.yaml")


def test_editor_cannot_create_or_delete_subagent_definitions():
    with pytest.raises(ValueError, match="cannot be created"):
        editor_operations.create_path("subAgentLibrary/new-worker.yaml")

    with pytest.raises(ValueError, match="cannot be deleted"):
        editor_operations.delete_path("subAgentLibrary/code-builder.yaml")

    with pytest.raises(FileNotFoundError, match="cannot be created"):
        editor_operations.write_file_content(
            "subAgentLibrary/new-worker.yaml", "id: new-worker\n"
        )
