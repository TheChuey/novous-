"""@tool registry & provider bindings for the Novous core engine.

Tools are plain Python functions decorated with @tool. Each tool declares a
provider (the pillar doorway that owns the capability). Providers are resolved
lazily so importing this module never creates circular imports.
"""

import ast
import inspect
import json
import operator
from pathlib import Path
from typing import Callable

from core_engine.agent_factory import load_agent
from core_engine import langgraph_tools

REGISTRY: dict[str, dict] = {}

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def tool(name: str | None = None, provider: str = "core_engine"):
    """Decorator that registers a function as an invocable agent tool."""

    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        doc = inspect.getdoc(func) or ""
        func.name = tool_name
        func.provider = provider
        REGISTRY[tool_name] = {
            "name": tool_name,
            "function": func,
            "provider": provider,
            "description": doc.splitlines() if doc else "",
            "signature": str(inspect.signature(func)),
        }
        return func

    return decorator


def _safe_eval(expr: str):
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression element: {ast.dump(node)}")

    return _eval(ast.parse(expr, mode="eval"))


# --- Core System Tools ---


@tool(provider="core_engine")
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression (numbers, + - * / // % ** and parentheses)."""
    result = _safe_eval(expression)
    return f"{expression} = {result}"


@tool(provider="editor")
def read_file(path: str) -> str:
    """Read a file from the workspace and return its text content."""
    return langgraph_tools.read_file_tool.invoke({"relative_path": path})


@tool(provider="editor")
def write_file(path: str, content: str) -> str:
    """Write or update text content in a workspace file."""
    return langgraph_tools.write_file_tool.invoke(
        {"relative_path": path, "content": content}
    )


@tool(provider="editor")
def create_file(path: str, kind: str = "file") -> str:
    """Create a new empty file or directory inside the workspace."""
    return langgraph_tools.create_file_tool.invoke(
        {"relative_path": path, "kind": kind}
    )


@tool(provider="editor")
def delete_file(path: str) -> str:
    """Delete a file or empty directory from the workspace."""
    return langgraph_tools.delete_file_tool.invoke({"relative_path": path})


@tool(provider="editor")
def list_directory(path: str = "") -> str:
    """List the workspace directory tree (optionally rooted at a relative path)."""
    return langgraph_tools.map_directory_tree_tool.invoke({"relative_path": path})


@tool(provider="editor")
def extract_docstrings(path: str) -> str:
    """Parse Python code AST to extract module, class, and function docstrings."""
    return langgraph_tools.extract_docstrings_tool.invoke({"relative_path": path})


@tool(provider="editor")
def search_workspace(query: str, extension: str = ".py") -> str:
    """Search workspace files for matching keyword or snippet."""
    return langgraph_tools.search_workspace_tool.invoke(
        {"query": query, "extension": extension}
    )


@tool(provider="core_engine")
def docling_parse(path: str, output_format: str = "markdown") -> str:
    """Parse PDF, DOCX, PPTX, or HTML files into structured Markdown/JSON via Docling."""
    return langgraph_tools.docling_parse_tool.invoke(
        {"relative_path": path, "output_format": output_format}
    )


@tool(provider="core_engine")
def rag_agent_tool(query: str, relative_path: str = "", top_k: int = 3) -> str:
    """Query workspace knowledge base or parse a document via Docling for relevant passages."""
    return langgraph_tools.rag_agent_tool.invoke(
        {"query": query, "relative_path": relative_path, "top_k": top_k}
    )


@tool(provider="core_engine")
def agent_info(agent_id: str) -> str:
    """Return the metadata and composed system prompt of a workspace agent."""
    profile = load_agent(agent_id)
    return json.dumps(
        {
            "id": profile.id,
            "name": profile.name,
            "mode": profile.mode,
            "description": profile.description,
            "role": profile.role,
            "purpose": profile.purpose,
            "boundaries": profile.boundaries,
            "system_prompt": profile.system_prompt,
        },
        indent=2,
    )


@tool(provider="workspace")
def project_status() -> str:
    """Return the current project state metadata for this workspace."""
    from workspace.interface import get_project_state

    return json.dumps(get_project_state(), indent=2)


PROVIDER_BINDINGS = {
    "core_engine": "core_engine.interface",
    "editor": "editor.interface",
    "workspace": "workspace.interface",
    "test_environment": "test_environment.interface",
}


def list_tools() -> list[dict]:
    return [
        {
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
        }
        for meta in REGISTRY.values()
    ]


def get_tools(names: list[str] | None = None) -> list[Callable]:
    """Resolve registered tool callables, filtered by an optional allow-list."""
    if not names:
        return [meta["function"] for meta in REGISTRY.values()]
    resolved = []
    for name in names:
        meta = REGISTRY.get(name)
        if meta:
            resolved.append(meta["function"])
    return resolved
