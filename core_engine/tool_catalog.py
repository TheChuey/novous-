"""@tool registry & provider bindings for the Novous core engine.

Tools are plain Python functions decorated with @tool. Each tool declares a
provider (the pillar doorway that owns the capability). Providers are resolved
lazily so importing this module never creates circular imports. Promoted
workspace tools are loaded from workspace/tools/ when the registry is queried.
"""

import ast
import importlib.util
import inspect
import json
import operator
import sys
from pathlib import Path
from typing import Callable

from core_engine.agent_factory import load_agent
from core_engine import langgraph_tools

REGISTRY: dict[str, dict] = {}
CUSTOM_TOOLS_DIR = Path(__file__).resolve().parent.parent / "workspace" / "tools"
_LOADED_CUSTOM_TOOLS: set[Path] = set()

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


@tool(provider="codebuilder")
def run_python_code(code: str) -> str:
    """Run a Python snippet in CodeBuilder and return its output and diagnostics."""
    from codebuilder.execution import execute_python_code
    from codebuilder.schemas import CodeExecutionRequest

    result = execute_python_code(CodeExecutionRequest(code=code))
    return json.dumps(result.model_dump(), ensure_ascii=False)




# --- Core System Tools ---


@tool(provider="core_engine")
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression (numbers, + - * / // % ** and parentheses)."""
    result = _safe_eval(expression)
    return f"{expression} = {result}"


@tool(provider="editor")
def read_file(path: str) -> str:
    """Read a file by workspace-root-relative path; do not prefix paths with 'workspace/'."""
    return langgraph_tools.read_file_tool.invoke({"relative_path": path})


@tool(provider="editor")
def write_file(path: str, content: str) -> str:
    """Write and verify non-empty text at a workspace-root-relative path; bare filenames go in the root.

    Do not prefix paths with 'workspace/'.
    Supports formats such as .txt, .md, .py, .json, .html, .css, and .js.
    Use create_file only when an intentionally empty file is requested.
    """
    return langgraph_tools.write_file_tool.invoke(
        {"relative_path": path, "content": content}
    )


@tool(provider="editor")
def create_file(path: str, kind: str = "file") -> str:
    """Create an empty file or directory by workspace-root-relative path; bare names go in root. Use write_file for content."""
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
    "codebuilder": "codebuilder.interface",
}


def list_tools() -> list[dict]:
    load_custom_tools()
    return [
        {
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
            "custom": meta["function"].__module__.startswith(
                "novous_workspace_tool_"
            ),
        }
        for meta in REGISTRY.values()
    ]


def get_tools(names: list[str] | None = None) -> list[Callable]:
    """Resolve registered tool callables, filtered by an optional allow-list."""
    load_custom_tools()
    if not names:
        return [meta["function"] for meta in REGISTRY.values()]
    resolved = []
    for name in names:
        meta = REGISTRY.get(name)
        if meta:
            resolved.append(meta["function"])
    return resolved


def load_custom_tools(reload: bool = False) -> None:
    """Load promoted workspace tools into the runtime registry."""
    if reload:
        custom_names = [
            name for name, meta in REGISTRY.items()
            if meta["function"].__module__.startswith("novous_workspace_tool_")
        ]
        for name in custom_names:
            REGISTRY.pop(name, None)
        for module_name in list(sys.modules):
            if module_name.startswith("novous_workspace_tool_"):
                sys.modules.pop(module_name, None)
        _LOADED_CUSTOM_TOOLS.clear()

    if not CUSTOM_TOOLS_DIR.is_dir():
        return

    for path in sorted(CUSTOM_TOOLS_DIR.glob("*.py")):
        resolved_path = path.resolve()
        if resolved_path in _LOADED_CUSTOM_TOOLS:
            continue

        module_name = f"novous_workspace_tool_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, resolved_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load custom tool module '{path}'.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise

        if path.name == "tool_library.py":
            functions = []
            function_names = set()
            for node in ast.parse(path.read_text(encoding="utf-8")).body:
                if isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith("_"):
                    raise ValueError(
                        f"Tool library function '{node.name}' must be synchronous."
                    )
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    if node.name in function_names:
                        raise ValueError(
                            f"Tool library defines '{node.name}' more than once."
                        )
                    function_names.add(node.name)
                    function = getattr(module, node.name, None)
                    if not inspect.isfunction(function) or function.__module__ != module_name:
                        raise ValueError(
                            f"Could not load tool library function '{node.name}'."
                        )
                    functions.append((node.name, function))
        else:
            function = getattr(module, path.stem, None)
            if not inspect.isfunction(function) or function.__module__ != module_name:
                sys.modules.pop(module_name, None)
                raise ValueError(
                    f"Custom tool module '{path.name}' must define a function named '{path.stem}'."
                )
            functions = [(path.stem, function)]

        conflicts = [name for name, _ in functions if name in REGISTRY]
        if conflicts:
            sys.modules.pop(module_name, None)
            raise ValueError(
                f"Custom tool '{conflicts[0]}' conflicts with a registered tool."
            )

        for name, function in functions:
            doc = inspect.getdoc(function) or ""
            function.name = name
            function.provider = "core_engine"
            REGISTRY[name] = {
                "name": name,
                "function": function,
                "provider": "core_engine",
                "description": doc.splitlines() if doc else "",
                "signature": str(inspect.signature(function)),
            }
        _LOADED_CUSTOM_TOOLS.add(resolved_path)


# Register CodeBuilder's local tool library (imported last so the @tool
# decorator resolved above is available without a broken import cycle).
from codebuilder.tools import tool_library  # noqa: E402,F401
