"""Tools interface: FastAPI router and Python doorway for tool registry."""

import ast
import inspect
from pathlib import Path
import re
import sys
from typing import Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core_engine import tool_catalog
from editor import editor_operations
from file_manager.service import file_manager_service

router = APIRouter()

PROMOTED_MODULE_PATH = (
    Path(__file__).resolve().parent / "promoted_tools.py"
)
PROMOTED_MARKER = "# PROMOTION_MARKER: tools appended below will be registered as custom tools"
REPO_ROOT = Path(__file__).resolve().parent.parent

_FUNCTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class FileReadLimitError(ValueError):
    """Raised when a bounded file read exceeds its configured byte limit."""


def map_files(path: str = "") -> dict:
    """Return the file-manager directory tree for a workspace-relative path."""
    return file_manager_service.directory_tree(_workspace_relative(path))


def _workspace_relative(path: str) -> str:
    """Map '', '.', '/', and absolute paths inside the workspace root to relative paths."""
    from file_manager import backend

    clean = (path or "").strip().replace("\\", "/")
    if clean in ("", ".", "./", "/"):
        return ""
    if clean.startswith("/") or (len(clean) > 1 and clean[1] == ":"):
        try:
            relative = Path(clean).resolve().relative_to(backend.workspace_root())
        except ValueError:
            return clean
        return relative.as_posix() if relative.parts else ""
    return clean[2:] if clean.startswith("./") else clean


def list_directory(path: str = "") -> dict:
    """Return file-manager entries for a workspace-relative directory."""
    return file_manager_service.list_directory(path)


def read_file(path: str) -> dict:
    """Read a file through the configured file-manager root."""
    return file_manager_service.read_file(path)


def read_file_bytes(path: str, max_bytes: int) -> dict:
    """Read bounded binary contents through the configured file-manager root."""
    from file_manager import backend

    resolved = backend.resolve_workspace_path(path)
    if not resolved.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    with resolved.open("rb") as source:
        content = source.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise FileReadLimitError(
            f"File exceeds the {max_bytes}-byte read limit: {path}"
        )
    return {
        "path": resolved.relative_to(backend.workspace_root()).as_posix(),
        "resolved_path": resolved,
        "size_bytes": len(content),
        "content": content,
    }


def write_file(path: str, content: str) -> dict:
    """Write a file through the configured file-manager root."""
    return file_manager_service.write_file(path, content)


def delete_file(path: str) -> dict:
    """Delete a path through the configured file-manager root."""
    return file_manager_service.delete(path)


def render_map_page(
    path: str,
    max_depth: int = 3,
    include_files: bool = True,
    offset: int = 0,
) -> dict:
    """Render a page of the active file-manager root's directory tree."""
    depth = max(1, min(int(max_depth), 6))
    start = max(0, int(offset))
    listing = map_files(path)
    lines = [f"ðŸ“ {listing['name']}"]
    entry_count = [0]

    def append_children(node: dict, level: int, prefix: str = "") -> None:
        if level <= 0:
            return
        children = node.get("children", [])
        visible = [
            child for child in children
            if child.get("type") == "directory" or include_files
        ]
        for index, child in enumerate(visible):
            if entry_count[0] >= 5000:
                lines.append(f"{prefix}â””â”€â”€ â€¦ scan limit of 5000 entries reached")
                return
            entry_count[0] += 1
            last = index == len(visible) - 1
            connector = "â””â”€â”€ " if last else "â”œâ”€â”€ "
            if child.get("type") == "directory":
                lines.append(f"{prefix}{connector}ðŸ“ {child['name']}/")
                append_children(
                    child,
                    level - 1,
                    prefix + ("    " if last else "â”‚   "),
                )
            else:
                lines.append(f"{prefix}{connector}ðŸ“„ {child['name']}")

    append_children(listing, depth)
    page_size = 80
    page = lines[start:start + page_size]
    next_offset = start + len(page)
    remaining = max(0, len(lines) - next_offset)
    return {
        "text": "\n".join(page) if page else "(no more entries)",
        "next_offset": next_offset,
        "remaining": remaining,
        "total": len(lines),
    }


def editor(action: str, path: str = "", content: str = "") -> dict:
    """Dispatch a file operation through the editor pillar."""
    if not isinstance(action, str):
        raise ValueError("Editor action must be a string.")
    action_clean = action.strip().lower()
    if action_clean == "read":
        return editor_operations.read_file_content(path)
    if action_clean == "write":
        return editor_operations.write_file_content(path, content)
    if action_clean == "tree":
        return editor_operations.get_directory_tree(path)
    if action_clean == "delete":
        return editor_operations.delete_path(path)
    raise ValueError(f"Unsupported editor action: '{action}'")


class RegisterToolRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=50000)
    name: str | None = None


def _ensure_promoted_file() -> None:
    if not PROMOTED_MODULE_PATH.exists():
        PROMOTED_MODULE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROMOTED_MODULE_PATH.write_text(
            '"""Permanent storage for promoted custom tools."""\n'
            'from core_engine.tool_catalog import tool\n\n'
            f"{PROMOTED_MARKER}\n\n",
            encoding="utf-8",
            newline="\n",
        )
    else:
        content = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
        if PROMOTED_MARKER not in content:
            sep = "\n\n" if not content.endswith("\n") else "\n"
            PROMOTED_MODULE_PATH.write_text(
                content + sep + PROMOTED_MARKER + "\n\n",
                encoding="utf-8",
                newline="\n",
            )


def list_promoted_tool_names() -> list[str]:
    """Return names of promoted custom tools defined after the marker in promoted_tools.py."""
    if not PROMOTED_MODULE_PATH.is_file():
        return []
    try:
        source = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return []
    marker_line = 0
    for line_number, line in enumerate(source.splitlines(), start=1):
        if line.startswith("# PROMOTION_MARKER"):
            marker_line = line_number
            break
    names = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            if node.lineno > marker_line:
                names.append(node.name)
    return names


def _decorated_source(first: str, second: str = "") -> str:
    """Ensure tool source has the @tool decorator."""
    source = second if second else first
    src = source.strip()
    if src.startswith("@tool"):
        return src + "\n"
    return f"@tool\n{src}\n"


def _function_span(source: str, name: str) -> tuple[int, int, ast.FunctionDef]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start_line = min(
                (decorator.lineno for decorator in node.decorator_list),
                default=node.lineno,
            )
            return start_line - 1, node.end_lineno, node
    raise FileNotFoundError(f"Custom tool '{name}' was not found in the promoted module.")


def _function_source(source: str, name: str) -> str:
    start, end, _ = _function_span(source, name)
    return "\n".join(source.splitlines()[start:end]).strip() + "\n"


def _source_for_name(name: str, full_source: str) -> str:
    return _function_source(full_source, name)


def _remove_function(source: str, name: str) -> str:
    start, end, _ = _function_span(source, name)
    lines = source.splitlines(keepends=True)
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    del lines[start:end]
    return "".join(lines)


def register_tool(source: str, name: str | None = None) -> dict:
    """Register a custom tool by appending to promoted_tools.py and execing into that module."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Python syntax error: {exc}") from exc

    fn_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            fn_node = node
            break
    if fn_node is None:
        raise ValueError("Define at least one public top-level function.")

    func_name = fn_node.name
    if name and name != func_name:
        raise HTTPException(
            status_code=400,
            detail="The primary function changed; run the test again before adding it.",
        )
    name = func_name

    _ensure_promoted_file()
    tool_catalog.load_tools()
    if name in tool_catalog.REGISTRY:
        raise HTTPException(
            status_code=409, detail=f"Tool '{name}' is already registered."
        )

    previous_content = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
    block = _decorated_source(name, source)
    sep = "\n" if not previous_content.endswith("\n\n") else ""
    new_content = previous_content + sep + block + "\n"
    PROMOTED_MODULE_PATH.write_text(new_content, encoding="utf-8", newline="\n")

    try:
        promoted_module = sys.modules.get("tools.promoted_tools")
        namespace = (
            promoted_module.__dict__
            if promoted_module is not None
            else {"tool": tool_catalog.tool, "__name__": "tools.promoted_tools"}
        )
        exec(block, namespace)
    except Exception as exc:
        PROMOTED_MODULE_PATH.write_text(previous_content, encoding="utf-8", newline="\n")
        tool_catalog.REGISTRY.pop(name, None)
        raise ValueError(f"Failed to execute tool '{name}': {exc}") from exc

    fn = tool_catalog.REGISTRY[name]["function"]
    tool_catalog.REGISTRY[name]["custom"] = True
    return {
        "name": name,
        "path": "tools/promoted_tools.py",
        "description": ast.get_docstring(fn_node) or "",
        "signature": str(inspect.signature(fn)),
    }


def remove_tool(name: str) -> dict:
    """Remove a custom tool from promoted_tools.py and tool_catalog.REGISTRY."""
    tool_catalog.load_tools()
    if name not in tool_catalog.REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")

    _ensure_promoted_file()
    previous_content = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
    try:
        new_content = _remove_function(previous_content, name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        PROMOTED_MODULE_PATH.write_text(new_content, encoding="utf-8", newline="\n")
    except Exception as exc:
        PROMOTED_MODULE_PATH.write_text(previous_content, encoding="utf-8", newline="\n")
        raise OSError(f"Could not update promoted module: {exc}") from exc

    tool_catalog.REGISTRY.pop(name, None)
    return {
        "name": name,
        "path": "tools/promoted_tools.py",
        "deleted": True,
    }


def get_tool_source(name: str) -> dict:
    """Retrieve source code of a tool (either promoted or builtin)."""
    if not _FUNCTION_NAME.fullmatch(name):
        raise ValueError("The tool name is not valid.")

    if PROMOTED_MODULE_PATH.is_file():
        full_source = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
        try:
            source = _function_source(full_source, name)
            return {
                "name": name,
                "path": "tools/promoted_tools.py",
                "source": source,
            }
        except FileNotFoundError:
            pass

    tool_catalog.load_tools()
    meta = tool_catalog.REGISTRY.get(name)
    if meta and "function" in meta:
        fn = meta["function"]
        try:
            source = inspect.getsource(fn)
            sourcefile = inspect.getsourcefile(fn)
            rel_path = (
                str(Path(sourcefile).relative_to(REPO_ROOT).as_posix())
                if sourcefile
                else "tools"
            )
            return {
                "name": name,
                "path": rel_path,
                "source": source,
            }
        except Exception:
            pass

    raise FileNotFoundError(f"Custom tool '{name}' was not found.")


def list_tools() -> list[dict]:
    """Return tool metadata with custom-tool flags."""
    tool_catalog.load_tools()
    promoted = set(list_promoted_tool_names())
    tools = []
    for meta in tool_catalog.REGISTRY.values():
        tools.append({
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
            "custom": meta["name"] in promoted or meta.get("custom", False),
        })
    return tools


def list_tools_directory() -> list[dict]:
    """Return registered tools defined by modules in the tools package."""
    return [
        tool
        for tool in list_tools()
        if (
            (meta := tool_catalog.REGISTRY[tool["name"]])["function"].__module__.startswith(
                "tools."
            )
            and meta["function"].__module__ != "tools.interface"
        )
    ]


def get_tool(name: str) -> Callable | None:
    """Resolve registered tool callable."""
    tool_catalog.load_tools()
    meta = tool_catalog.REGISTRY.get(name)
    return meta["function"] if meta else None


def provider_bindings() -> dict[str, str]:
    """Return provider mappings."""
    return tool_catalog.get_provider_bindings()


def catalog_report() -> dict:
    """Return catalog diagnostic report."""
    return tool_catalog.get_catalog_report()


@router.get("/api/agent-memory/scratchpad")
def api_read_agent_scratchpad():
    """Return scratchpad data for the Chat Console."""
    from agentMemory import scratchpad

    return scratchpad.read_memory()


@router.delete("/api/agent-memory/scratchpad")
def api_clear_agent_scratchpad():
    """Clear saved agent reads and workspace maps."""
    from agentMemory import scratchpad

    return scratchpad.clear_memory()


@router.get("/api/rag/config")
def api_get_rag_config():
    from agentMemory import interface as memory

    return memory.get_rag_status()


@router.get("/api/rag/documents")
def api_list_rag_documents():
    from agentMemory import interface as memory

    return memory.get_rag_overview()


@router.post("/api/rag/documents")
def api_add_rag_text(payload: dict):
    from agentMemory import interface as memory

    try:
        return memory.add_text_document(str(payload.get("title", "")), str(payload.get("text", "")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {exc}") from exc


@router.post("/api/rag/documents/delete")
def api_delete_rag_document(payload: dict):
    from agentMemory import interface as memory

    try:
        return memory.delete_document(str(payload.get("path", "")))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/api/rag/config")
def api_set_rag_config(payload: dict):
    from agentMemory import interface as memory

    try:
        return memory.set_rag_folder(str(payload.get("path", "")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/rag/reindex")
def api_reindex_rag():
    from agentMemory import interface as memory

    try:
        result = memory.refresh_knowledge_base()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {**result, **memory.get_rag_status()}


@router.delete("/api/rag/index")
def api_clear_rag_index():
    from agentMemory import interface as memory

    return memory.clear_rag_index()


@router.get("/api/tools")
def api_list_tools():
    rep = catalog_report()
    return {
        "tools": list_tools(),
        "providers": provider_bindings(),
        "warnings": rep.get("warnings", []),
    }


@router.get("/api/tools/library")
def api_tool_library():
    return {"tools": list_tools_directory()}


@router.get("/api/tools/health")
def api_tools_health():
    errors = tool_catalog.get_load_errors()
    return {
        "status": "healthy" if not errors else "degraded",
        "load_errors": errors,
        "warnings": catalog_report().get("warnings", []),
    }


@router.post("/api/tools/register")
def api_register_tool(req: RegisterToolRequest):
    try:
        return register_tool(req.source, req.name)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class MapPageRequest(BaseModel):
    path: str
    max_depth: int = 3
    include_files: bool = True
    offset: int = 0


@router.post("/api/tools/map-page")
def api_map_page(req: MapPageRequest):
    tool_catalog.load_tools()
    try:
        return render_map_page(req.path, req.max_depth, req.include_files, req.offset)
    except (PermissionError, ValueError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/tools/{name}")
def api_get_tool(name: str):
    tool_catalog.load_tools()
    meta = tool_catalog.REGISTRY.get(name)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")
    promoted = set(list_promoted_tool_names())
    return {
        "name": meta["name"],
        "provider": meta["provider"],
        "description": meta["description"],
        "signature": meta["signature"],
        "custom": meta["name"] in promoted or meta.get("custom", False),
    }


@router.delete("/api/tools/{name}")
def api_delete_tool(name: str):
    try:
        return remove_tool(name)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
