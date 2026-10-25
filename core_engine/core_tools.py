"""Non-file core tools (promoted custom tools live in tools/promoted_tools.py)."""

import ast
import json
import operator

from core_engine import langgraph_tools
from core_engine.agent_factory import load_agent
from core_engine.tool_catalog import tool


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


@tool(provider="core_engine")
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression (numbers, + - * / // % ** and parentheses)."""
    result = _safe_eval(expression)
    return f"{expression} = {result}"


@tool(provider="core_engine")
def rag_agent_tool(
    query: str,
    relative_path: str = "",
    top_k: int = 3,
    knowledge_base_id: str = "",
) -> str:
    """Query a named knowledge source by ID, including archived sources, for relevant passages."""
    return langgraph_tools.rag_agent_tool.invoke(
        {
            "query": query,
            "relative_path": relative_path,
            "top_k": top_k,
            "knowledge_base_id": knowledge_base_id,
        }
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


@tool(provider="codebuilder")
def run_python_code(code: str) -> str:
    """Run a Python snippet in CodeBuilder and return its output and diagnostics."""
    from codebuilder.execution import execute_python_code
    from codebuilder.schemas import CodeExecutionRequest

    result = execute_python_code(CodeExecutionRequest(code=code))
    return json.dumps(result.model_dump(), ensure_ascii=False)


@tool(provider="codebuilder")
def send_code_to_editor(code: str) -> str:
    """Queue generated Python code for insertion into the active CodeBuilder Monaco editor."""
    if not code.strip():
        raise ValueError("Code to send to the editor must not be empty.")
    return "CodeBuilder will insert this code into the active Monaco editor after the chat turn."


@tool(provider="codebuilder")
def run_code_in_editor() -> str:
    """Queue execution of the current contents of the active CodeBuilder editor."""
    return "CodeBuilder will run the active editor buffer after the chat turn."


def _codebuilder_host_supports_questionnaire() -> bool:
    try:
        from codebuilder import service

        return service.host_supports_questionnaire()
    except Exception:
        return False


if _codebuilder_host_supports_questionnaire():
    @tool(provider="codebuilder")
    def ask_user_questions(json_file_path: str, timeout_seconds: float = 300.0) -> str:
        """Pause the agent and ask the user a list of questions from a JSON file in the workspace."""
        from codebuilder import service

        return service.ask_user(json_file_path, timeout_seconds)


@tool(provider="workspace")
def project_status() -> str:
    """Return the current project state metadata for this workspace."""
    from workspace.interface import get_project_state

    return json.dumps(get_project_state(), indent=2)
