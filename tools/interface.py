"""tools/interface.py

Public doorway. The sole import surface for outside callers; exposes
public functions and the FastAPI router.

Component: LangChain tool registry & filesystem tool implementations.

Other components import *only* this file for the registry (configure,
get, list_tools, available_tool_ids, resolve_tools, new_session,
get_session, _TOOL_REGISTRY), the registered @tool wrappers, the chatlog
store (append_chat, read_history, clear_chat, search_text,
append_tool_event, use_data_dir) and the /api/tools endpoint.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Request
from langchain_core.tools import BaseTool, tool

from project_manager.interface import project_manager_error

from .code import (
    append_chat,
    append_tool_event,
    clear_chat,
    create_directory as create_directory_impl,
    delete_files as delete_files_impl,
    map_files as map_files_impl,
    read_file as read_file_impl,
    read_history,
    search_text,
    search_workspace as search_workspace_impl,
    write_text_file as write_text_file_impl,
)
from .data import FileSession
from .logic import configure, current_provider, use_data_dir, using

__all__ = [
    "FileSession",
    "_TOOL_REGISTRY",
    "_bind",
    "_replace_func",
    "append_chat",
    "append_tool_event",
    "available_tool_ids",
    "clear_chat",
    "configure",
    "create_directory",
    "current_provider",
    "delete_files",
    "get",
    "get_current_date",
    "list_tools",
    "map_files",
    "new_session",
    "get_session",
    "read_file",
    "read_history",
    "resolve_tools",
    "router",
    "search_chat_logs",
    "search_text",
    "search_workspace",
    "tell_me_the_date_and_time",
    "use_data_dir",
    "using",
    "write_text_file",
]


# ============================================================
# LANGCHAIN TOOL WRAPPERS
# ============================================================

@tool
def map_files(
    path: Annotated[str, "Directory path to inspect."],
    max_depth: Annotated[int, "Maximum directory depth to include."] = 8,
    max_entries: Annotated[int, "Maximum number of entries to return."] = 5000,
) -> dict:
    """Lists files and directories beneath a workspace path."""
    return map_files_impl(path, max_depth, max_entries)


@tool
def read_file(
    path: Annotated[str, "File path to read."],
    ocr: Annotated[bool, "Enable OCR when reading scanned documents."] = True,
) -> dict:
    """Reads text or extracts content from a workspace file."""
    return read_file_impl(path, ocr)


@tool
def write_text_file(
    name: Annotated[str, "Name of the file to write."],
    content: Annotated[str, "Complete text content to write."],
    output_path: Annotated[str, "Directory path in which to write the file."],
    overwrite: Annotated[bool, "Replace an existing file when true."] = False,
) -> dict:
    """Writes a text file to a workspace directory."""
    return write_text_file_impl(name, content, output_path, overwrite)


@tool
def delete_files(
    file_list: Annotated[list[str], "Workspace file paths to delete."],
) -> dict:
    """Deletes workspace files immediately."""
    return delete_files_impl(file_list)


@tool
def create_directory(
    path: Annotated[str, "Workspace directory path to create."],
) -> dict:
    """Creates a workspace directory and any missing parent directories."""
    return create_directory_impl(path)


@tool
def search_workspace(
    query: Annotated[str, "Case-insensitive phrase to find in text files."],
    path: Annotated[str, "Directory path to search."] = ".",
    max_results: Annotated[int, "Maximum number of matching lines to return."] = 20,
) -> dict:
    """Searches workspace text files and returns matching lines."""
    return search_workspace_impl(query, path, max_results)


@tool
def get_current_date() -> str:
    """Returns today's local date in a readable format."""
    from datetime import datetime

    return datetime.now().strftime("%A, %B %d, %Y")


@tool
def tell_me_the_date_and_time() -> str:
    """Returns the current local date and time."""
    from datetime import datetime

    return f"The current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def search_chat_logs(query: Annotated[str, "Keyword or phrase to search for."]) -> str:
    """Searches saved conversation history for matching messages."""
    result = search_text(query)
    if not result:
        return f"No matches found in the chat log for the query: '{query}'."
    return result


# ============================================================
# REGISTRY
# ============================================================

_TOOL_REGISTRY: dict[str, BaseTool] = {
    "map_files": map_files,
    "read_file": read_file,
    "write_text_file": write_text_file,
    "delete_files": delete_files,
    "create_directory": create_directory,
    "search_workspace": search_workspace,
    "get_current_date": get_current_date,
    "tell_me_the_date_and_time": tell_me_the_date_and_time,
    "search_chat_logs": search_chat_logs,
}


def _replace_func(tool_: BaseTool, func) -> BaseTool:
    """Copy a LangChain tool while preserving its validated input schema."""
    if not hasattr(tool_, "func") or tool_.func is None:
        raise TypeError(f"Tool '{tool_.name}' does not have a synchronous function.")
    return tool_.model_copy(update={"func": func})


def _bind(tool_: BaseTool, provider: Any) -> BaseTool:
    """Bind one filesystem provider to a tool without changing its schema."""
    import functools

    original = tool_.func

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        with using(provider):
            return original(*args, **kwargs)

    return _replace_func(tool_, wrapper)


def get(tool_name: str) -> BaseTool | None:
    """Retrieve a registered LangChain tool by its ID."""
    return _TOOL_REGISTRY.get(tool_name)


def list_tools() -> list[str]:
    """Return all registered tool IDs."""
    return list(_TOOL_REGISTRY)


def available_tool_ids() -> list[str]:
    """Backward-compatible alias for list_tools()."""
    return list_tools()


def resolve_tools(tool_ids: list[str], provider: Any = None) -> list[BaseTool]:
    """Resolve agent tool IDs and optionally bind a workspace provider."""
    resolved = []
    for tool_id in tool_ids:
        registered = _TOOL_REGISTRY.get(tool_id)
        if registered is None:
            print(f"[registry] WARNING: tool '{tool_id}' not found - skipped.")
            continue
        resolved.append(_bind(registered, provider) if provider is not None else registered)
    return resolved


def new_session() -> FileSession:
    """Create an independent working-state record for one agent."""
    return FileSession()


_session = FileSession()


def get_session() -> FileSession:
    """Return the shared session kept for older CLI callers."""
    return _session


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


@router.get("/api/tools")
def list_tool_ids(
    request: Request,
):
    """
    Return tool IDs and descriptions the registry can resolve.

    The registry is the single source of truth for what ``agent.json``'s
    ``tools`` may name, so the Prompt Builder asks for this list instead of
    keeping its own copy that could silently drift.

    ``mode: "chat"`` attaches none of these; ``mode: "agent"`` attaches the
    ones an ``agent.json`` lists (the agent factory).
    """

    try:
        tool_ids = list_tools()
        details = []
        for tool_id in tool_ids:
            tool_ = get(tool_id)
            if tool_ is None:
                raise RuntimeError(
                    f"Registered tool '{tool_id}' could not be resolved."
                )
            details.append({
                "id": tool_id,
                "description": tool_.description or "",
            })

        return {
            "tools": tool_ids,
            "details": details,
        }

    except Exception as error:

        raise project_manager_error(error)
