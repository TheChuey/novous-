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

from test_environment import sandbox_env


LOCAL_RUN_TIMEOUT_SECONDS = 5
MAX_RUN_TIMEOUT_SECONDS = 600
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


def validate_arguments(function: ast.FunctionDef, arguments: dict) -> str | None:
    """Return an error message when arguments don't match the function signature."""
    schema = get_tool_schema(function)["function"]["parameters"]
    missing = [name for name in schema["required"] if name not in arguments]
    unknown = [name for name in arguments if name not in schema["properties"]]
    if missing:
        return f"Missing required argument(s): {', '.join(missing)}"
    if unknown:
        return f"Unknown argument(s): {', '.join(unknown)}"
    return None


_CODE_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

GENERATE_SYSTEM_PROMPT = (
    "You write standalone Python tool functions. Reply with exactly one fenced "
    "```python code block containing one public top-level synchronous function with "
    "type-hinted parameters (str, int, float, bool, list, dict), a docstring "
    "describing it, and a JSON-serializable return value. Put any imports at the top "
    "of the block. Do not include example calls, tests, or explanations."
)


def extract_code(text: str) -> str:
    match = _CODE_BLOCK.search(text or "")
    return (match.group(1) if match else (text or "")).strip()


def generate_python_function(description: str, model: str, chat=None) -> dict:
    """Ask the LLM for a tool function and validate it; retry once on invalid output."""
    if chat is None:
        import ollama
        chat = ollama.chat
    messages = [
        {"role": "system", "content": GENERATE_SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
    last_error = "No code returned."
    for _ in range(2):
        response = chat(model=model, messages=messages)
        text = (response.get("message") or {}).get("content", "")
        code = extract_code(text)
        try:
            function = get_function_definition(code)
            return {"code": code, "function_name": function.name}
        except ValueError as exc:
            last_error = str(exc)
            messages += [
                {"role": "assistant", "content": text},
                {"role": "user", "content": f"That code was invalid: {last_error} Fix it and reply with one python code block."},
            ]
    raise ValueError(last_error)


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


HARNESS_START = "# --- Novous test call (edit the values; removed when adding to the library) ---"
HARNESS_END = "# --- end Novous test call ---"
_HARNESS_BLOCK = re.compile(
    r"\n*" + re.escape(HARNESS_START) + r".*?" + re.escape(HARNESS_END) + r"[ \t]*\n?",
    re.DOTALL,
)
_PLACEHOLDERS = {
    "string": '"test"', "integer": "1", "number": "1.0",
    "boolean": "True", "array": "[]", "object": "{}",
}


def has_test_harness(source: str) -> bool:
    return HARNESS_START in source


def strip_test_harness(source: str) -> str:
    return _HARNESS_BLOCK.sub("\n", source).rstrip() + "\n" if has_test_harness(source) else source


def build_test_harness(source: str) -> str:
    """Return a ready-to-edit call block for the first public function in source."""
    function = get_function_definition(strip_test_harness(source))
    args = function.args
    positional = args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    params = list(zip(positional, defaults)) + list(zip(args.kwonlyargs, args.kw_defaults))
    lines = [HARNESS_START]
    for argument, default in params:
        if default is not None:
            value = ast.unparse(default)
        else:
            value = _PLACEHOLDERS[_json_type(argument.annotation)]
        lines.append(f"{argument.arg} = {value}")
    call_args = ", ".join(f"{argument.arg}={argument.arg}" for argument, _ in params)
    lines += [f"result = {function.name}({call_args})", "print(result)", HARNESS_END]
    return "\n".join(lines) + "\n"


def _run_locally(source: str, arguments: dict, function_name: str, script_mode: bool = False,
                 timeout: float | None = None) -> dict:
    timeout = min(timeout or LOCAL_RUN_TIMEOUT_SECONDS, MAX_RUN_TIMEOUT_SECONDS)
    marker = f"__NOVOUS2_RESULT_{secrets.token_hex(16)}__"
    wrapper = "" if script_mode else (
        "\n\nif __name__ == '__main__':\n"
        "    import json as __novous2_json\n"
        "    __novous2_arguments = __novous2_json.loads(input() or '{}')\n"
        f"    __novous2_result = {function_name}(**__novous2_arguments)\n"
        f"    print({marker!r} + __novous2_json.dumps("
        "__novous2_result, default=str))\n"
    )

    try:
        with tempfile.TemporaryDirectory(prefix="novous2-tool-test-") as temp_dir:
            script_path = Path(temp_dir) / "tool_test.py"
            script_path.write_text(source + wrapper, encoding="utf-8")
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen(
                    [sandbox_env.interpreter(), "-I", str(script_path)],
                    cwd=temp_dir,
                    env=_local_environment(temp_dir),
                    stdin=subprocess.PIPE,
                    stdout=stdout_file,
                    stderr=stderr_file,
                )
                try:
                    process.communicate(
                        input=json.dumps(arguments).encode("utf-8"),
                        timeout=timeout,
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
                            f"{timeout:g} seconds. Raise the time limit for GUI or long-running code."
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
                passed = process.returncode == 0 and (script_mode or marker_line is not None)
                try:
                    output = json.loads(marker_line[len(marker):]) if passed and not script_mode else None
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


def run_python_tool(source: str, arguments: dict, timeout: float | None = None) -> dict:
    if has_test_harness(source):
        # The edit-mode test call is the input: run the code exactly as written.
        try:
            function = get_function_definition(strip_test_harness(source))
        except ValueError as exc:
            return {"status": "ERROR", "status_code": 400,
                    "error_code": "ERR_INVALID_TOOL", "message": str(exc)}
        return _run_locally(source, arguments, function.name, script_mode=True, timeout=timeout)
    try:
        function = get_function_definition(source)
    except ValueError as exc:
        return {
            "status": "ERROR",
            "status_code": 400,
            "error_code": "ERR_INVALID_TOOL",
            "message": str(exc),
        }

    return _run_locally(source, arguments, function.name, timeout=timeout)


def promote_python_tool(source: str, expected_name: str) -> dict:
    function = get_function_definition(source)
    if function.name != expected_name:
        raise HTTPException(
            status_code=400,
            detail="The primary function changed; run the test again before adding it.",
        )
    from tools import interface as tools_interface
    return tools_interface.register_tool(source, expected_name)


def get_custom_tool_source(name: str) -> dict:
    if not _FUNCTION_NAME.fullmatch(name):
        raise ValueError("The tool name is not valid.")
    from tools import interface as tools_interface
    return tools_interface.get_tool_source(name)


def delete_custom_tool(name: str) -> dict:
    if not _FUNCTION_NAME.fullmatch(name):
        raise ValueError("The tool name is not valid.")
    from tools import interface as tools_interface
    return tools_interface.remove_tool(name)

