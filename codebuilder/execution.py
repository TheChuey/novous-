"""Execution engine for Python snippets and structured diagnostics."""

import io
import sys
import traceback
import uuid
from typing import List

from .schemas import CodeExecutionRequest, CodeExecutionResult, DiagnosticItem


def execute_python_code(req: CodeExecutionRequest) -> CodeExecutionResult:
    """Execute Python code in an isolated namespace and capture diagnostics."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    diagnostics: List[DiagnosticItem] = []

    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_buffer, stderr_buffer

    status = "SUCCESS"
    try:
        try:
            compile(req.code, "<codebuilder>", "exec")
        except SyntaxError as exc:
            diagnostics.append(
                DiagnosticItem(
                    line=exc.lineno,
                    column=exc.offset,
                    message=f"SyntaxError: {exc.msg}",
                    severity="error",
                    run_id=run_id,
                )
            )
            raise
        exec_globals = {"__name__": "__main__"}
        exec(req.code, exec_globals)
    except Exception as exc:  # noqa: BLE001 - surface structured runtime diagnostics
        status = "ERROR"
        tb = traceback.extract_tb(exc.__traceback__)
        last_frame = tb[-1] if tb else None
        diagnostics.append(
            DiagnosticItem(
                path=getattr(exc, "filename", None),
                line=last_frame.lineno if last_frame else None,
                column=getattr(exc, "offset", None),
                message=f"{type(exc).__name__}: {exc}",
                severity="error",
                run_id=run_id,
            )
        )
        stderr_buffer.write(traceback.format_exc())
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

    return CodeExecutionResult(
        run_id=run_id,
        status=status,
        stdout=stdout_buffer.getvalue(),
        stderr=stderr_buffer.getvalue(),
        diagnostics=diagnostics,
    )
