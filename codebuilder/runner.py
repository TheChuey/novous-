"""CodeBuilder execution runner: safe (in-process) and risky (isolated subprocess) modes.

The risky chain runs each snippet in a fresh Python subprocess so real interpreter
errors surface, ``input()`` reaches an immediate EOF instead of hanging, a hard
timeout is enforced, and output is streamed event-by-event to the caller.
"""

import io
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union

from .schemas import CodeExecutionRequest, CodeExecutionResult, DiagnosticItem

MAX_STREAM_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 10.0
_STDERR_LINE = re.compile(r"[Ll]ine (\d+)(?:,| )")


def _run_id() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"


def resolve_python() -> str:
    """Resolve the interpreter used for risky mode: env override, else server Python."""
    return os.environ.get("NOVOUS_PYTHON") or sys.executable


def _runner_environment(root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(root) + (os.pathsep + existing if existing else "")
    return env


def execute_safe(req: CodeExecutionRequest) -> CodeExecutionResult:
    """Execute Python in-process in an isolated namespace and capture diagnostics."""
    run_id = _run_id()
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


def run_risky(req: CodeExecutionRequest, run_id: Optional[str] = None) -> Iterator[dict]:
    """Stream an isolated subprocess execution as a sequence of event dicts.

    Events: ``start``, ``stdout``, ``stderr``, ``syntax_error``, ``done``.
    stdin is closed immediately so code calling ``input()`` streams its earlier
    output and then fails fast with ``EOFError`` instead of hanging.
    """
    run_id = run_id or _run_id()
    interpreter = resolve_python()
    timeout = max(0.1, req.timeout_seconds or DEFAULT_TIMEOUT_SECONDS)

    try:
        compile(req.code, "<codebuilder>", "exec")
    except SyntaxError as exc:
        yield {
            "type": "syntax_error",
            "run_id": run_id,
            "line": exc.lineno,
            "column": exc.offset,
            "message": f"SyntaxError: {exc.msg}",
        }
        yield {
            "type": "done",
            "run_id": run_id,
            "return_code": 1,
            "status": "ERROR",
            "timed_out": False,
        }
        return

    yield {
        "type": "start",
        "run_id": run_id,
        "mode": "risky",
        "python": interpreter,
        "timeout_seconds": timeout,
    }

    process: Optional[subprocess.Popen] = None
    timed_out = False
    return_code = None
    try:
        with tempfile.TemporaryDirectory(prefix="codebuilder-") as temp_dir:
            script_path = Path(temp_dir) / "codebuilder_script.py"
            script_path.write_text(req.code, encoding="utf-8")
            process = subprocess.Popen(
                [interpreter, "-u", str(script_path)],
                cwd=str(Path.cwd()),
                env=_runner_environment(Path.cwd()),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            if process.stdin is not None:
                process.stdin.close()  # immediate EOF for any input() calls

            line_queue: "queue.Queue[Optional[str]]" = queue.Queue()

            def _reader() -> None:
                try:
                    if process.stdout is not None:
                        for line in process.stdout:
                            line_queue.put(line)
                finally:
                    line_queue.put(None)

            threading.Thread(target=_reader, daemon=True).start()

            deadline = time.monotonic() + timeout
            emitted = 0
            truncated = False
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    break
                try:
                    line = line_queue.get(timeout=remaining)
                except queue.Empty:
                    timed_out = True
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    break

                if line is None:
                    if process.poll() is not None:
                        break
                    try:
                        process.wait(timeout=deadline - time.monotonic())
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        process.kill()
                        process.wait()
                    break

                if truncated:
                    continue

                if emitted + len(line) > MAX_STREAM_BYTES:
                    keep = max(0, MAX_STREAM_BYTES - emitted)
                    if keep:
                        yield {"type": "stdout", "text": line[:keep]}
                    yield {"type": "truncated", "run_id": run_id}
                    truncated = True
                    continue

                emitted += len(line)
                yield {"type": "stdout", "text": line}

            if process.poll() is None:
                process.kill()
                process.wait()
            return_code = process.returncode

            if timed_out:
                yield {
                    "type": "stderr",
                    "text": f"\nTimeoutError: code execution exceeded {timeout:g} seconds.\n",
                }
    except OSError as exc:
        yield {
            "type": "stderr",
            "text": f"Could not start Python interpreter: {exc}\n",
        }
        yield {
            "type": "done",
            "run_id": run_id,
            "return_code": None,
            "status": "ERROR",
            "timed_out": False,
            "error": str(exc),
        }
        return
    finally:
        if process is not None and process.poll() is None:
            try:
                process.kill()
                process.wait()
            except OSError:
                pass

    status = "ERROR" if (return_code or 0) != 0 else "SUCCESS"
    yield {
        "type": "done",
        "run_id": run_id,
        "return_code": return_code,
        "status": status,
        "timed_out": timed_out,
    }


def _diagnostic_from_output(text: str, run_id: str, return_code: Optional[int]) -> Optional[DiagnosticItem]:
    line: Optional[int] = None
    for match in _STDERR_LINE.finditer(text):
        line = int(match.group(1))
    last_words = [part.strip() for part in text.splitlines() if part.strip()]
    if last_words:
        message = last_words[-1][:200]
    elif return_code is not None:
        message = f"Process exited with code {return_code}"
    else:
        message = "Execution failed"
    return DiagnosticItem(line=line, message=message, severity="error", run_id=run_id)


def execute_risky(req: CodeExecutionRequest) -> CodeExecutionResult:
    """Run the risky chain to completion and return a CodeExecutionResult."""
    run_id = _run_id()
    out_parts: List[str] = []
    err_parts: List[str] = []
    diagnostics: List[DiagnosticItem] = []
    status = "SUCCESS"
    return_code = None
    timed_out = False

    for event in run_risky(req, run_id=run_id):
        event_type = event.get("type")
        if event_type == "stdout":
            out_parts.append(event["text"])
        elif event_type == "stderr":
            err_parts.append(event["text"])
        elif event_type == "syntax_error":
            diagnostics.append(
                DiagnosticItem(
                    line=event.get("line"),
                    column=event.get("column"),
                    message=event.get("message", "SyntaxError"),
                    severity="error",
                    run_id=run_id,
                )
            )
        elif event_type == "done":
            status = event.get("status", "ERROR")
            return_code = event.get("return_code")
            timed_out = event.get("timed_out", False)

    stdout = "".join(out_parts)
    stderr = "".join(err_parts)
    if timed_out and not stderr:
        stderr += f"TimeoutError: code execution exceeded {req.timeout_seconds:g} seconds.\n"
    if status == "ERROR" and not diagnostics:
        diagnostic = _diagnostic_from_output(stdout + stderr, run_id, return_code)
        if diagnostic:
            diagnostics.append(diagnostic)

    return CodeExecutionResult(
        run_id=run_id,
        status=status,
        stdout=stdout,
        stderr=stderr,
        diagnostics=diagnostics,
    )


def execute_python_code(req: CodeExecutionRequest) -> CodeExecutionResult:
    """Public dispatcher: pick the engine based on the requested mode."""
    if req.mode == "risky":
        return execute_risky(req)
    return execute_safe(req)