import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import HTTPException

from core_engine import tool_catalog
from test_environment import tool_workbench
from test_environment.interface import (
    ToolWorkbenchLLMRequest,
    ToolWorkbenchRequest,
    api_promote_tool,
    api_test_tool_with_llm,
)


class ToolWorkbenchTests(unittest.TestCase):
    def test_extracts_primary_function_and_builds_typed_schema(self):
        function = tool_workbench.get_function_definition(
            'def calculate(weight: float, *, region: str = "US"):\n'
            '    """Calculate a value."""\n'
            "    return weight\n"
        )

        schema = tool_workbench.get_tool_schema(function)["function"]
        self.assertEqual(schema["name"], "calculate")
        self.assertEqual(schema["parameters"]["properties"]["weight"]["type"], "number")
        self.assertEqual(schema["parameters"]["properties"]["region"]["type"], "string")
        self.assertEqual(schema["parameters"]["required"], ["weight"])

    def test_rejects_syntax_errors_and_variadic_arguments(self):
        with self.assertRaises(ValueError):
            tool_workbench.get_function_definition("def broken(:\n")
        with self.assertRaisesRegex(ValueError, "variadic"):
            tool_workbench.get_function_definition("def unsafe(*args):\n    return args\n")

    def test_runs_source_locally_and_decodes_output(self):
        source = "def add(left: int, right: int):\n    return left + right\n"
        result = tool_workbench.run_python_tool(source, {"left": 2, "right": 3})

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["output"], 5)
        self.assertEqual(result["exit_code"], 0)

    def test_returns_python_errors_and_times_out_long_running_code(self):
        error_result = tool_workbench.run_python_tool(
            "def fail():\n    raise ValueError('test error')\n", {}
        )
        self.assertEqual(error_result["status"], "ERROR")
        self.assertIn("ValueError: test error", error_result["stderr"])

        with patch.object(tool_workbench, "LOCAL_RUN_TIMEOUT_SECONDS", 0.1):
            timeout_result = tool_workbench.run_python_tool(
                "import time\ndef wait():\n    time.sleep(2)\n", {}
            )
        self.assertEqual(timeout_result["error_code"], "ERR_TOOL_TIMEOUT")

    def test_llm_tool_call_returns_and_executes_function_arguments(self):
        source = "def add(left: int, right: int):\n    return left + right\n"
        arguments = {"left": 8, "right": 5}
        execution = {"status": "SUCCESS", "error_code": None, "output": 13}
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "",
                "tool_calls": [{
                    "function": {"name": "add", "arguments": arguments}
                }],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code=source,
            user_prompt="Add eight and five.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            with patch.object(
                tool_workbench, "run_python_tool", return_value=execution
            ) as run_tool:
                result = api_test_tool_with_llm(request)

        run_tool.assert_called_once_with(source, arguments)
        self.assertEqual(result["function_input"], arguments)
        self.assertEqual(result["tool_execution_result"], execution)

    def test_llm_response_is_returned_when_model_does_not_call_tool(self):
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "I could not determine the required values.",
                "tool_calls": [],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code="def add(left: int, right: int):\n    return left + right\n",
            user_prompt="Add eight and five.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            result = api_test_tool_with_llm(request)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["error_code"], "ERR_NO_TOOL_CALL")
        self.assertEqual(
            result["llm_text_response"],
            "I could not determine the required values.",
        )
        self.assertEqual(result["tool_calls_detected"], [])

    def test_failed_function_execution_still_returns_llm_arguments(self):
        source = "def divide(left: int, right: int):\n    return left // right\n"
        arguments = {"left": 8, "right": 0}
        execution = {
            "status": "ERROR",
            "error_code": "ERR_TOOL_EXECUTION",
            "stderr": "ZeroDivisionError",
        }
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "Dividing eight by zero.",
                "tool_calls": [{
                    "function": {"name": "divide", "arguments": arguments}
                }],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code=source,
            user_prompt="Divide eight by zero.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            with patch.object(
                tool_workbench, "run_python_tool", return_value=execution
            ):
                result = api_test_tool_with_llm(request)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["function_input"], arguments)
        self.assertEqual(result["llm_text_response"], "Dividing eight by zero.")

    def test_unexpected_llm_tool_call_is_returned_for_diagnostics(self):
        tool_call = {
            "function": {"name": "other_function", "arguments": {"value": 8}}
        }
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "Trying an unrelated function.",
                "tool_calls": [tool_call],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code="def add(left: int, right: int):\n    return left + right\n",
            user_prompt="Add eight and five.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            result = api_test_tool_with_llm(request)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["error_code"], "ERR_UNEXPECTED_TOOL_CALL")
        self.assertEqual(result["llm_text_response"], "Trying an unrelated function.")
        self.assertEqual(result["tool_calls_detected"], [tool_call])

    def test_rejects_failed_test_before_promotion(self):
        request = ToolWorkbenchRequest(
            tool_code="def add(left: int, right: int):\n    return left + right\n",
            function_input={"left": 2, "right": 3},
        )
        failed_result = {"status": "ERROR", "error_code": "ERR_TOOL_EXECUTION"}
        with patch.object(tool_workbench, "run_python_tool", return_value=failed_result):
            with patch.object(tool_workbench, "promote_python_tool") as promote:
                with self.assertRaises(HTTPException) as error:
                    api_promote_tool(request)

        self.assertEqual(error.exception.status_code, 400)
        promote.assert_not_called()

    def test_promotes_passing_tool_into_catalog(self):
        first_name = "workbench_test_add"
        second_name = "workbench_test_double"
        first_source = (
            f"def {first_name}(left: int, right: int):\n"
            "    return left + right\n"
        )
        second_source = f"def {second_name}(value: int):\n    return value * 2\n"
        with tempfile.TemporaryDirectory() as directory:
            tools_dir = Path(directory)
            old_workbench_dir = tool_workbench.WORKSPACE_TOOLS_DIR
            old_catalog_dir = tool_catalog.CUSTOM_TOOLS_DIR
            tool_workbench.WORKSPACE_TOOLS_DIR = tools_dir
            tool_catalog.CUSTOM_TOOLS_DIR = tools_dir
            try:
                promoted = api_promote_tool(ToolWorkbenchRequest(
                    tool_code=first_source, function_input={"left": 2, "right": 3}
                ))
                self.assertEqual(promoted["promoted"]["name"], first_name)
                self.assertEqual(
                    promoted["promoted"]["path"], "workspace/tools/tool_library.py"
                )
                second_promoted = api_promote_tool(ToolWorkbenchRequest(
                    tool_code=second_source, function_input={"value": 3}
                ))
                self.assertEqual(second_promoted["promoted"]["name"], second_name)
                library_source = (tools_dir / "tool_library.py").read_text(
                    encoding="utf-8"
                )
                self.assertLess(
                    library_source.index(first_name), library_source.index(second_name)
                )
                self.assertEqual(
                    tool_catalog.REGISTRY[first_name]["function"](2, 3), 5
                )
                self.assertEqual(
                    tool_catalog.REGISTRY[second_name]["function"](3), 6
                )
            finally:
                tool_catalog.REGISTRY.pop(first_name, None)
                tool_catalog.REGISTRY.pop(second_name, None)
                tool_catalog._LOADED_CUSTOM_TOOLS.discard(
                    (tools_dir / "tool_library.py").resolve()
                )
                sys.modules.pop("novous_workspace_tool_tool_library", None)
                tool_workbench.WORKSPACE_TOOLS_DIR = old_workbench_dir
                tool_catalog.CUSTOM_TOOLS_DIR = old_catalog_dir

    def test_custom_tool_source_can_be_loaded_and_removed_from_library(self):
        tool_name = "workbench_library_tool"
        remaining_name = "workbench_library_remaining"
        source = (
            f"def {tool_name}(value: int):\n    return value * 2\n\n\n"
            f"def {remaining_name}(value: int):\n    return value + 1\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            tools_dir = Path(directory)
            tool_path = tools_dir / "tool_library.py"
            tool_path.write_text(source, encoding="utf-8")
            old_workbench_dir = tool_workbench.WORKSPACE_TOOLS_DIR
            old_catalog_dir = tool_catalog.CUSTOM_TOOLS_DIR
            tool_workbench.WORKSPACE_TOOLS_DIR = tools_dir
            tool_catalog.CUSTOM_TOOLS_DIR = tools_dir
            try:
                loaded = tool_workbench.get_custom_tool_source(tool_name)
                self.assertEqual(
                    loaded["source"],
                    f"def {tool_name}(value: int):\n    return value * 2\n",
                )
                self.assertEqual(loaded["path"], "workspace/tools/tool_library.py")
                self.assertIn(tool_name, tool_catalog.REGISTRY)
                self.assertIn(remaining_name, tool_catalog.REGISTRY)

                removed = tool_workbench.delete_custom_tool(tool_name)
                self.assertTrue(removed["deleted"])
                self.assertTrue(tool_path.exists())
                self.assertNotIn(tool_name, tool_catalog.REGISTRY)
                self.assertIn(remaining_name, tool_catalog.REGISTRY)
                self.assertIn(remaining_name, tool_path.read_text(encoding="utf-8"))

                tool_workbench.delete_custom_tool(remaining_name)
                self.assertNotIn(remaining_name, tool_catalog.REGISTRY)
                self.assertTrue(tool_path.exists())
                self.assertNotIn(remaining_name, tool_path.read_text(encoding="utf-8"))
            finally:
                tool_catalog.REGISTRY.pop(tool_name, None)
                tool_catalog.REGISTRY.pop(remaining_name, None)
                tool_catalog._LOADED_CUSTOM_TOOLS.discard(tool_path.resolve())
                sys.modules.pop("novous_workspace_tool_tool_library", None)
                tool_workbench.WORKSPACE_TOOLS_DIR = old_workbench_dir
                tool_catalog.CUSTOM_TOOLS_DIR = old_catalog_dir


if __name__ == "__main__":
    unittest.main()
