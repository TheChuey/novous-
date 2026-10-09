"""Local Python execution and promotion for user-authored Python tools."""

import ast
import importlib.util
import inspect
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException


WORKSPACE_TOOLS_DIR = Path(__file__).resolve().parent.parent / "workspace" / "tools"
LOCAL_RUN_TIMEOUT_SECONDS = 5
MAX_OUTPUT_BYTES = 64 * 1024
_FUNCTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def get_function_definition(source: str) -> ast.FunctionDef:
    """Return the first public, top-level synchronous function in source."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Python syntax error: {exc}") from exc

    functions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]
    if not functions:
        raise ValueError("Define at least one public top-level function.")
    if isinstance(functions[0], ast.AsyncFunctionDef):
        raise ValueError("The primary tool function must be synchronous.")
    if not _FUNCTION_NAME.fullmatch(functions[0].name):
        raise ValueError("The primary function name is not a valid tool name.")
    if (functions[0].args.posonlyargs or functions[0].args.kwarg or
            functions[0].args.vararg):
        raise ValueError(
            "The primary function cannot use positional-only or variadic arguments."
        )
    return functions[0]


def _json_type(annotation: ast.expr | None) -> str:
    name = None
    if isinstance(annotation, ast.Name):
        name = annotation.id
    elif isinstance(annotation, ast.Attribute):
        name = annotation.attr
    if name:
        return {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "List": "array",
            "dict": "object",
            "Dict": "object",
        }.get(name, "string")
    if isinstance(annotation, ast.Subscript):
        value = annotation.value
        base_name = value.id if isinstance(value, ast.Name) else (
            value.attr if isinstance(value, ast.Attribute) else ""
        )
        if base_name.lower() == "list":
            return "array"
        if base_name.lower() == "dict":
            return "object"
    return "string"


def get_tool_schema(function: ast.FunctionDef) -> dict:
    positional_args = function.args.args
    positional_defaults = (
        [None] * (len(positional_args) - len(function.args.defaults))
        + list(function.args.defaults)
    )
    keyword_args = function.args.kwonlyargs
    keyword_defaults = function.args.kw_defaults
    properties = {}
    required = []
    for argument, default in (
        list(zip(positional_args, positional_defaults))
        + list(zip(keyword_args, keyword_defaults))
    ):
        properties[argument.arg] = {
            "type": _json_type(argument.annotation),
            "description": f"Parameter {argument.arg}",
        }
        if default is None:
            required.append(argument.arg)
    return {
        "type": "function",
        "function": {
            "name": function.name,
            "description": ast.get_docstring(function) or function.name,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


def _local_environment(temp_dir: str) -> dict[str, str]:
    env = {"PATH": os.environ.get("PATH", ""), "TEMP": temp_dir, "TMP": temp_dir}
    for key in ("SYSTEMROOT", "WINDIR"):
        if value := os.environ.get(key):
            env[key] = value
    if os.name == "nt":
        env["USERPROFILE"] = temp_dir
    else:
        env["HOME"] = temp_dir
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _read_output(output_file) -> str:
    output_file.seek(0, os.SEEK_END)
    size = output_file.tell()
    output_file.seek(max(0, size - MAX_OUTPUT_BYTES))
    text = output_file.read(MAX_OUTPUT_BYTES).decode("utf-8", errors="replace")
    if size > MAX_OUTPUT_BYTES:
        return f"[Earlier output truncated]\n{text}"
    return text


def _run_locally(source: str, arguments: dict, function_name: str) -> dict:
    marker = f"__NOVOUS_RESULT_{secrets.token_hex(16)}__"
    wrapper = (
        "\n\nif __name__ == '__main__':\n"
        "    import json as __novous_json\n"
        "    __novous_arguments = __novous_json.loads(input() or '{}')\n"
        f"    __novous_result = {function_name}(**__novous_arguments)\n"
        f"    print({marker!r} + __novous_json.dumps("
        "__novous_result, default=str))\n"
    )

    try:
        with tempfile.TemporaryDirectory(prefix="novous-tool-test-") as temp_dir:
            script_path = Path(temp_dir) / "tool_test.py"
            script_path.write_text(source + wrapper, encoding="utf-8")
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen(
                    [sys.executable, "-I", str(script_path)],
                    cwd=temp_dir,
                    env=_local_environment(temp_dir),
                    stdin=subprocess.PIPE,
                    stdout=stdout_file,
                    stderr=stderr_file,
                )
                try:
                    process.communicate(
                        input=json.dumps(arguments).encode("utf-8"),
                        timeout=LOCAL_RUN_TIMEOUT_SECONDS,
                    )
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    return {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status_code": 422,
                        "error_code": "ERR_TOOL_TIMEOUT",
                        "status": "ERROR",
                        "function_name": function_name,
                        "message": (
                            f"Local function test exceeded "
                            f"{LOCAL_RUN_TIMEOUT_SECONDS} seconds."
                        ),
                        "stdout": _read_output(stdout_file),
                        "stderr": _read_output(stderr_file),
                        "exit_code": process.returncode,
                    }

                stdout = _read_output(stdout_file)
                stderr = _read_output(stderr_file)
                marker_line = next(
                    (
                        line for line in reversed(stdout.splitlines())
                        if line.startswith(marker)
                    ),
                    None,
                )
                passed = process.returncode == 0 and marker_line is not None
                try:
                    output = json.loads(marker_line[len(marker):]) if passed else None
                except json.JSONDecodeError:
                    passed = False
                    output = None
                visible_stdout = "\n".join(
                    line for line in stdout.splitlines() if not line.startswith(marker)
                )
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status_code": 200 if passed else 422,
                    "error_code": None if passed else "ERR_TOOL_EXECUTION",
                    "status": "SUCCESS" if passed else "ERROR",
                    "function_name": function_name,
                    "output": output,
                    "stdout": visible_stdout,
                    "stderr": stderr,
                    "exit_code": process.returncode,
                }
    except OSError as exc:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": 500,
            "error_code": "ERR_LOCAL_RUNNER",
            "status": "ERROR",
            "function_name": function_name,
            "message": f"Could not start local Python: {exc}",
        }


def run_python_tool(source: str, arguments: dict) -> dict:
    try:
        function = get_function_definition(source)
    except ValueError as exc:
        return {
            "status": "ERROR",
            "status_code": 400,
            "error_code": "ERR_INVALID_TOOL",
            "message": str(exc),
        }

    return _run_locally(source, arguments, function.name)


def promote_python_tool(source: str, expected_name: str) -> dict:
    function = get_function_definition(source)
    if function.name != expected_name:
        raise HTTPException(
            status_code=400,
            detail="The primary function changed; run the test again before adding it.",
        )

    from core_engine import tool_catalog

    tool_catalog.load_custom_tools()
    if function.name in tool_catalog.REGISTRY:
        raise HTTPException(
            status_code=409, detail=f"Tool '{function.name}' is already registered."
        )

    WORKSPACE_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    destination = WORKSPACE_TOOLS_DIR / f"{function.name}.py"
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as tool_file:
            tool_file.write(source.rstrip() + "\n")
    except FileExistsError as exc:
        raise HTTPException(
            status_code=409, detail=f"Tool file '{destination.name}' already exists."
        ) from exc

    try:
        tool_catalog.load_custom_tools()
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return {
        "name": function.name,
        "path": f"tools/{destination.name}",
        "description": ast.get_docstring(function) or "",
        "signature": str(inspect.signature(tool_catalog.REGISTRY[function.name]["function"])),
    }
