import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from core_engine import tool_catalog
from test_environment import tool_workbench
from test_environment.interface import ToolWorkbenchRequest, api_promote_tool


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
        tool_name = "workbench_test_add"
        source = f"def {tool_name}(left: int, right: int):\n    return left + right\n"
        with tempfile.TemporaryDirectory() as directory:
            tools_dir = Path(directory)
            old_workbench_dir = tool_workbench.WORKSPACE_TOOLS_DIR
            old_catalog_dir = tool_catalog.CUSTOM_TOOLS_DIR
            tool_workbench.WORKSPACE_TOOLS_DIR = tools_dir
            tool_catalog.CUSTOM_TOOLS_DIR = tools_dir
            try:
                promoted = api_promote_tool(ToolWorkbenchRequest(
                    tool_code=source, function_input={"left": 2, "right": 3}
                ))
                self.assertEqual(promoted["promoted"]["name"], tool_name)
                self.assertEqual(tool_catalog.REGISTRY[tool_name]["function"](2, 3), 5)
            finally:
                tool_catalog.REGISTRY.pop(tool_name, None)
                tool_catalog._LOADED_CUSTOM_TOOLS.discard((tools_dir / f"{tool_name}.py").resolve())
                sys.modules.pop(f"novous_workspace_tool_{tool_name}", None)
                tool_workbench.WORKSPACE_TOOLS_DIR = old_workbench_dir
                tool_catalog.CUSTOM_TOOLS_DIR = old_catalog_dir


if __name__ == "__main__":
    unittest.main()
