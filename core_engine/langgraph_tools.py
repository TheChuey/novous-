"""LangGraph & Docling Tool Suite for Novous Agent Factory.

Provides safe file CRUD, workspace directory mapping, AST docstring extraction,
Docling document extraction through the registered read tool, workspace search,
and grounded RAG capabilities.
"""

import ast
import json
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Internal Novous Editor operations for workspace security
from editor.editor_operations import (
    read_file_content,
    write_file_content,
    create_path,
    delete_path,
    get_directory_tree,
    resolve_project_path,
    PROJECT_ROOT,
)

# --- 1. Read File Tool ---
@tool
def read_file_tool(relative_path: str) -> str:
    """Read a file relative to workspace root; do not prefix paths with 'workspace/'."""
    try:
        data = read_file_content(relative_path)
        return data["content"]
    except Exception as exc:
        return f"Error reading file '{relative_path}': {exc}"


# --- 2. Write File Tool ---
@tool
def write_file_tool(relative_path: str, content: str) -> str:
    """Write and verify non-empty text at a workspace-root-relative path; bare filenames go in the root.

    Do not prefix paths with 'workspace/'.
    Supports formats such as .txt, .md, .py, .json, .html, .css, and .js.
    Use create_file_tool only when an intentionally empty file is requested.
    """
    if not content.strip():
        raise ValueError(
            "File content is empty; no file was written. Provide content, or use "
            "create_file_tool only when an empty file is explicitly requested."
        )

    res = write_file_content(relative_path, content)
    saved = read_file_content(relative_path)["content"]
    if saved != content:
        raise IOError(f"Verification failed after writing '{relative_path}'.")
    return (
        f"Successfully wrote and verified {res['bytes_written']} bytes "
        f"to '{relative_path}'."
    )


# --- 3. Create File or Folder Tool ---
@tool
def create_file_tool(relative_path: str, kind: str = "file") -> str:
    """Create an empty file or directory under workspace root; do not prefix paths with 'workspace/'."""
    try:
        res = create_path(relative_path, kind=kind)
        return f"Created {res['created']} at '{relative_path}'."
    except Exception as exc:
        return f"Error creating path '{relative_path}': {exc}"


# --- 4. Delete File Tool ---
@tool
def delete_file_tool(relative_path: str) -> str:
    """Safely delete a file or empty directory from the workspace."""
    try:
        res = delete_path(relative_path)
        return f"Deleted '{relative_path}' successfully."
    except Exception as exc:
        return f"Error deleting path '{relative_path}': {exc}"


# --- 5. Map Directory Tree Tool ---
@tool
def map_directory_tree_tool(relative_path: str = "") -> str:
    """Return a JSON map of the directory structure starting from relative_path."""
    try:
        tree = get_directory_tree(relative_path)
        return json.dumps(tree, indent=2)
    except Exception as exc:
        return f"Error mapping directory tree '{relative_path}': {exc}"


# --- 6. Extract Docstrings Tool ---
@tool
def extract_docstrings_tool(relative_path: str) -> str:
    """Parse a Python file and extract module, class, and function docstrings using AST."""
    try:
        abs_path = resolve_project_path(relative_path)
        code = abs_path.read_text(encoding="utf-8")
        parsed_tree = ast.parse(code)

        docstrings = {
            "file": relative_path,
            "module_docstring": ast.get_docstring(parsed_tree),
            "classes": {},
            "functions": {},
        }

        for node in ast.walk(parsed_tree):
            if isinstance(node, ast.ClassDef):
                docstrings["classes"][node.name] = ast.get_docstring(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstrings["functions"][node.name] = ast.get_docstring(node)

        return json.dumps(docstrings, indent=2)
    except Exception as exc:
        return f"Error extracting docstrings from '{relative_path}': {exc}"


# --- 7. Search Workspace Tool ---
@tool
def search_workspace_tool(query: str, extension: str = ".py") -> str:
    """Search workspace files for matching keyword or text snippet."""
    try:
        matches = []
        ext = extension if extension.startswith(".") else f".{extension}"
        for file_path in PROJECT_ROOT.rglob(f"*{ext}"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue
            try:
                rel = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for idx, line in enumerate(content.splitlines(), start=1):
                    if query.lower() in line.lower():
                        matches.append(f"{rel}:{idx} - {line.strip()}")
            except Exception:
                continue
        return (
            "\n".join(matches[:50])
            if matches
            else f"No matches found for query '{query}'."
        )
    except Exception as exc:
        return f"Error searching workspace: {exc}"


# --- 9. Docling-Enhanced RAG Agent Tool ---
@tool
def rag_agent_tool(
    query: str, relative_path: Optional[str] = None, top_k: int = 3
) -> str:
    """Search indexed Knowledge Base documents using semantic Ollama embeddings."""
    from agentMemory import interface as agent_memory

    return json.dumps(
        agent_memory.search_knowledge_base(query, top_k, relative_path or ""),
        ensure_ascii=False,
        indent=2,
    )
