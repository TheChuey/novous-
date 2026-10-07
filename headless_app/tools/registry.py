"""Registry and per-agent provider binding for LangChain tools."""

from typing import Any

from langchain_core.tools import BaseTool

from tools.memory import search_chat_logs
from tools.state import FileSession
from tools.utility import get_current_date, tell_me_the_date_and_time
from tools.workspace import (
    create_directory,
    delete_files,
    map_files,
    read_file,
    search_workspace,
    write_text_file,
)
from tools.project_tools import configure as _configure_provider, using as _using_provider

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


def _replace_func(tool: BaseTool, func) -> BaseTool:
    """Copy a LangChain tool while preserving its validated input schema."""
    if not hasattr(tool, "func") or tool.func is None:
        raise TypeError(f"Tool '{tool.name}' does not have a synchronous function.")
    return tool.model_copy(update={"func": func})


def _bind(tool: BaseTool, provider: Any) -> BaseTool:
    """Bind one filesystem provider to a tool without changing its schema."""
    import functools

    original = tool.func

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        with _using_provider(provider):
            return original(*args, **kwargs)

    return _replace_func(tool, wrapper)


def configure(provider=None) -> None:
    """Set the fallback provider for tools used outside agent construction."""
    _configure_provider(provider)


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


__all__ = [
    "configure",
    "get",
    "list_tools",
    "available_tool_ids",
    "resolve_tools",
    "new_session",
    "get_session",
    "_TOOL_REGISTRY",
]
