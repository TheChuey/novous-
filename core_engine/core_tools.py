"""Non-file core tools (promoted custom tools live in tools/promoted_tools.py)."""

import ast
import json
import operator

from core_engine import langgraph_tools
from core_engine.agent_factory import load_agent
from core_engine.tool_catalog import tool
from tools.code_change_preview import preview_code_change as build_code_change_preview


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
    from orchestration.codebuilder_run_state import codebuilder_run_state
    from orchestration.orchestration_telemetry import telemetry_bus

    result = execute_python_code(CodeExecutionRequest(code=code))
    context = telemetry_bus.current_context()
    if context is not None:
        trace_id, agent_id = context
        result_data = result.model_dump()
        source_matches_editor = codebuilder_run_state.matches_editor_source(
            trace_id, code
        )
        if codebuilder_run_state.save_execution(
            trace_id,
            code,
            result_data,
            allow_non_editor_source=agent_id == "tester",
        ):
            diagnostic_lines = sorted(
                {
                    item.line
                    for item in result.diagnostics
                    if source_matches_editor and item.line is not None and item.line > 0
                }
            )[:120]
            telemetry_bus.log_event(
                trace_id,
                "EDITOR_CODE_EXECUTION",
                agent_id,
                "editor",
                {
                    "status": "success" if result.status == "SUCCESS" else "error",
                    "diagnostic_lines": diagnostic_lines,
                },
            )
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


@tool(provider="codebuilder")
def preview_editor_code(proposed_content: str) -> str:
    """Preview complete proposed code in the active CodeBuilder editor without saving it."""
    from orchestration.codebuilder_run_state import (
        MAX_EDITOR_CONTENT_BYTES,
        codebuilder_run_state,
    )
    from orchestration.orchestration_telemetry import telemetry_bus
    from tools.code_change_preview import changed_line_numbers

    if not isinstance(proposed_content, str):
        raise ValueError("The editor preview must be text.")
    if len(proposed_content.encode("utf-8")) > MAX_EDITOR_CONTENT_BYTES:
        raise ValueError("The editor preview exceeds the 1 MB limit.")
    context = telemetry_bus.current_context()
    if context is None:
        raise ValueError(
            "Editor-buffer previews are only available during a CodeBuilder workflow."
        )
    trace_id, agent_id = context
    original = codebuilder_run_state.get_editor_code(trace_id)
    if original is None:
        raise ValueError(
            "The original CodeBuilder editor buffer is unavailable for this workflow."
        )
    lines = changed_line_numbers(original, proposed_content, "after")
    if not codebuilder_run_state.save_preview(trace_id, proposed_content, lines):
        raise ValueError("The CodeBuilder workflow preview could not be saved.")
    telemetry_bus.log_event(
        trace_id,
        "EDITOR_CODE_PREVIEW",
        agent_id,
        "editor",
        {"changed_lines": lines},
    )
    return json.dumps(
        {"status": "success" if lines else "nothing_found", "changed_lines": lines},
        ensure_ascii=False,
    )


@tool(provider="codebuilder")
def inspect_http_routes(path: str) -> str:
    """Statically list HTTP route decorators in a workspace Python file without running the server."""
    from tools.interface import read_file_bytes

    if not isinstance(path, str) or not path.strip() or len(path) > 512:
        raise ValueError("Provide a workspace-relative Python file path.")
    if not path.lower().endswith(".py"):
        raise ValueError("HTTP route inspection only accepts Python source files.")
    source_info = read_file_bytes(path, 1_000_000)
    source = source_info["content"].decode("utf-8")
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise ValueError(
            f"Could not inspect routes in {path}: Python syntax error at line {exc.lineno}."
        ) from exc

    routes = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.lower()
            if method == "route":
                route_methods = next(
                    (
                        keyword.value
                        for keyword in decorator.keywords
                        if keyword.arg == "methods"
                    ),
                    None,
                )
            elif method in {"get", "post", "put", "patch", "delete", "options", "head", "api_route"}:
                method_names = (
                    []
                    if method == "api_route"
                    else [method.upper()]
                )
            else:
                continue
            if method in {"route", "api_route"}:
                methods_node = next(
                    (
                        keyword.value
                        for keyword in decorator.keywords
                        if keyword.arg == "methods"
                    ),
                    None,
                )
                method_names = (
                    sorted(
                        {
                            item.value.upper()
                            for item in methods_node.elts
                            if isinstance(item, ast.Constant)
                            and isinstance(item.value, str)
                        }
                    )
                    if isinstance(methods_node, (ast.List, ast.Tuple))
                    else []
                )
            path_node = decorator.args[0] if decorator.args else None
            route_path = (
                path_node.value
                if isinstance(path_node, ast.Constant)
                and isinstance(path_node.value, str)
                else None
            )
            routes.append(
                {
                    "line": decorator.lineno,
                    "function": node.name,
                    "route": route_path,
                    "methods": method_names,
                    "router": decorator.func.value.id
                    if isinstance(decorator.func.value, ast.Name)
                    else None,
                }
            )
    routes.sort(key=lambda route: route["line"])
    return json.dumps(
        {"path": source_info["path"], "routes": routes},
        ensure_ascii=False,
        indent=2,
    )


@tool(provider="workspace")
def project_status() -> str:
    """Return the current project state metadata for this workspace."""
    from workspace.interface import get_project_state

    return json.dumps(get_project_state(), indent=2)


@tool(provider="core_engine")
def preview_code_change(path: str, proposed_content: str) -> str:
    """Preview changed line numbers for a workspace file without writing its contents."""
    return json.dumps(
        build_code_change_preview(path, proposed_content),
        ensure_ascii=False,
    )
