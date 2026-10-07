"""LangChain tools for workspace files and directories."""

from typing import Annotated

from langchain_core.tools import tool

from tools import project_tools as _implementation


@tool
def map_files(
    path: Annotated[str, "Directory path to inspect."],
    max_depth: Annotated[int, "Maximum directory depth to include."] = 8,
    max_entries: Annotated[int, "Maximum number of entries to return."] = 5000,
) -> dict:
    """Lists files and directories beneath a workspace path."""
    return _implementation.map_files(path, max_depth, max_entries)


@tool
def read_file(
    path: Annotated[str, "File path to read."],
    ocr: Annotated[bool, "Enable OCR when reading scanned documents."] = True,
) -> dict:
    """Reads text or extracts content from a workspace file."""
    return _implementation.read_file(path, ocr)


@tool
def write_text_file(
    name: Annotated[str, "Name of the file to write."],
    content: Annotated[str, "Complete text content to write."],
    output_path: Annotated[str, "Directory path in which to write the file."],
    overwrite: Annotated[bool, "Replace an existing file when true."] = False,
) -> dict:
    """Writes a text file to a workspace directory."""
    return _implementation.write_text_file(name, content, output_path, overwrite)


@tool
def delete_files(
    file_list: Annotated[list[str], "Workspace file paths to delete."],
) -> dict:
    """Deletes workspace files immediately."""
    return _implementation.delete_files(file_list)


@tool
def create_directory(
    path: Annotated[str, "Workspace directory path to create."],
) -> dict:
    """Creates a workspace directory and any missing parent directories."""
    return _implementation.create_directory(path)


@tool
def search_workspace(
    query: Annotated[str, "Case-insensitive phrase to find in text files."],
    path: Annotated[str, "Directory path to search."] = ".",
    max_results: Annotated[int, "Maximum number of matching lines to return."] = 20,
) -> dict:
    """Searches workspace text files and returns matching lines."""
    return _implementation.search_workspace(query, path, max_results)


__all__ = [
    "map_files",
    "read_file",
    "write_text_file",
    "delete_files",
    "create_directory",
    "search_workspace",
]
