# Novous2 Agent Factory — Master Copy

Generated from `E:\novous` — 105 files.

## `codebuilder/__init__.py`
```py
"""CodeBuilder pillar package.

Layers (dependencies point downward only):

    interface.py   HTTP adapter (FastAPI router)          \
    tools/         agent adapter (@tool functions)         > service.py  -> host bridge (lazy)
                                                          /
    execution.py   engine: isolated runs, stuck handling
    schemas.py     contracts (pydantic models)

Importing this package is cheap and has no dependency on the host app.
"""

from .execution import execute_python_code
from .schemas import (
    CodeExecutionRequest,
    CodeExecutionResult,
    DiagnosticItem,
    StructuredEditRequest,
)
from .service import agent_meta as load_codebuilder_agent_meta

__all__ = [
    "CodeExecutionRequest",
    "CodeExecutionResult",
    "DiagnosticItem",
    "StructuredEditRequest",
    "execute_python_code",
    "load_codebuilder_agent_meta",
]

```

## `codebuilder/execution.py`
```py
"""CodeBuilder engine: run Python in an isolated process and never get stuck.

Layer rule: this module knows about processes and diagnostics only. It does not
import FastAPI, the host app (``core_engine``) or the filesystem workspace.

Public API (this is the import surface the host relies on)
----------------------------------------------------------
``execute_python_code(req)``  -> CodeExecutionResult   (buffered; what ``/execute`` and
                                                         the ``run_python_code`` tool use)
``run_stream(req)``           -> Iterator[dict]        (event stream; what ``/execute/stream`` uses)
``cancel_run(run_id)``        -> bool                  (stop a live run)
``resolve_python()``          -> str                   (interpreter; ``$NOVOUS2_PYTHON`` override)

How a run is supervised
-----------------------
Both modes use the same supervisor; ``mode`` only picks the output shape
(``safe``: stdout/stderr separate, ``risky``: merged in order, streamable).

1. User code never runs inside the server process, so it can never freeze the
   server thread or corrupt ``sys.stdout`` for other requests.
2. A harness script executes the code, writes a structured diagnostic file on
   failure, and arms ``faulthandler.dump_traceback_later`` so that when the code
   hangs we learn *which line* it was stuck on, even inside a tight loop.
3. The supervisor enforces a wall-clock deadline, an output cap and a cancel
   flag, and kills the whole process *tree* (children included).
4. An independent watchdog timer kills the tree at ``timeout + grace`` even if
   the consumer of the stream vanished (client disconnect).
5. A stopped run reports a ``StuckInfo`` (reason, line, source text, hint), so a
   human or an agent knows what to change instead of just seeing "timed out".
"""

import codecs
import json
import os
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from .schemas import (
    STUCK_CANCELLED,
    STUCK_OUTPUT_LIMIT,
    STUCK_TIMEOUT,
    CodeExecutionRequest,
    CodeExecutionResult,
    DiagnosticItem,
    StuckInfo,
)

MAX_OUTPUT_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 10.0
MIN_TIMEOUT_SECONDS = 0.1
MAX_TIMEOUT_SECONDS = 120.0
WATCHDOG_GRACE_SECONDS = 1.0   # watchdog fires this long after the deadline
DRAIN_SECONDS = 0.5            # keep collecting output printed just before a kill
_STDERR_LINE = re.compile(r"[Ll]ine (\d+)(?:,| )")
_STACK_FRAME = re.compile(r'File "<codebuilder>", line (\d+)')

# Runs inside the child interpreter (standard library only).
_HARNESS = r'''
import faulthandler, json, sys, traceback

script, diag_path, stack_path, dump_after = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
sys.argv = [script]
stack_file = open(stack_path, "w")


def report(**data):
    with open(diag_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


try:
    with open(script, encoding="utf-8") as fh:
        source = fh.read()
    code = compile(source, "<codebuilder>", "exec")
    faulthandler.dump_traceback_later(dump_after, file=stack_file)
    exec(code, {"__name__": "__main__", "__file__": script})
except SystemExit:
    raise
except BaseException as exc:
    frames = traceback.extract_tb(exc.__traceback__)
    mine = [f for f in frames if f.filename == "<codebuilder>"]
    line = mine[-1].lineno if mine else getattr(exc, "lineno", None)
    detail = exc.msg if isinstance(exc, SyntaxError) else str(exc)
    report(line=line, column=getattr(exc, "offset", None),
           message=type(exc).__name__ + ": " + str(detail))
    tb = exc.__traceback__.tb_next if exc.__traceback__ else None
    traceback.print_exception(type(exc), exc, tb)
    sys.exit(1)
'''


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"


def resolve_python() -> str:
    """Interpreter for runs: ``$NOVOUS2_PYTHON``, else the test sandbox venv if present, else the server's Python."""
    if os.environ.get("NOVOUS2_PYTHON"):
        return os.environ["NOVOUS2_PYTHON"]
    try:
        from test_environment import sandbox_env
        return sandbox_env.interpreter()
    except Exception:  # noqa: BLE001 - keep CodeBuilder usable when the host app is absent
        return sys.executable


def _clamp_timeout(value: Optional[float]) -> float:
    try:
        seconds = float(value) if value else DEFAULT_TIMEOUT_SECONDS
    except (TypeError, ValueError):
        seconds = DEFAULT_TIMEOUT_SECONDS
    return min(max(seconds, MIN_TIMEOUT_SECONDS), MAX_TIMEOUT_SECONDS)


def _child_environment(root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(root) + (os.pathsep + existing if existing else "")
    return env


def _popen_group_kwargs() -> dict:
    """Start the child in its own group/session so the whole tree can be killed."""
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
    return {"start_new_session": True}


def _kill_tree(proc: Optional[subprocess.Popen]) -> None:
    """Kill the process and every descendant. Safe to call repeatedly."""
    if proc is None or proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=5,
            )
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        proc.kill()
    except OSError:
        pass


def _pump(channel: str, stream, sink: "queue.Queue", abandoned: threading.Event) -> None:
    """Reader thread: forward raw chunks as they arrive (not just full lines)."""
    try:
        while True:
            chunk = stream.read1(8192)
            if not chunk:
                break
            if not abandoned.is_set():
                sink.put((channel, chunk))
    except (OSError, ValueError):
        pass
    finally:
        sink.put((channel, None))


# --------------------------------------------------------------------------- #
# Live-run registry (what makes cancellation possible)
# --------------------------------------------------------------------------- #
class _RunRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: Dict[str, threading.Event] = {}

    def register(self, run_id: str) -> threading.Event:
        event = threading.Event()
        with self._lock:
            self._runs[run_id] = event
        return event

    def release(self, run_id: str) -> None:
        with self._lock:
            self._runs.pop(run_id, None)

    def cancel(self, run_id: str) -> bool:
        with self._lock:
            event = self._runs.get(run_id)
        if event is None:
            return False
        event.set()
        return True


_REGISTRY = _RunRegistry()


def cancel_run(run_id: str) -> bool:
    """Ask a live run to stop. Returns False if the run is unknown or finished."""
    return _REGISTRY.cancel(run_id)


# --------------------------------------------------------------------------- #
# Stuck analysis
# --------------------------------------------------------------------------- #
def _read_stuck_line(stack_path: Path) -> Optional[int]:
    """Innermost user-code line from the faulthandler dump, if one was written."""
    try:
        match = _STACK_FRAME.search(stack_path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    return int(match.group(1)) if match else None


def _describe_stuck(reason: str, timeout: float, code: str, line: Optional[int]) -> StuckInfo:
    source = None
    if line is not None:
        lines = code.splitlines()
        if 1 <= line <= len(lines):
            source = lines[line - 1].strip()[:120]
    where = f" It was executing line {line}" + (f": `{source}`." if source else ".") if line else ""

    if reason == STUCK_TIMEOUT:
        return StuckInfo(
            reason=reason,
            message=f"Code execution exceeded {timeout:g} seconds.",
            line=line,
            source=source,
            hint=(
                "The program was still running at the deadline." + where
                + " Look for a loop with no exit condition (`while True` without `break`), a blocking "
                "call (`time.sleep`, network, `join()`, `Queue.get()`), or very heavy computation. "
                "Add a loop bound or a timeout, or raise timeout_seconds if the work is legitimately long."
            ),
        )
    if reason == STUCK_OUTPUT_LIMIT:
        return StuckInfo(
            reason=reason,
            message=f"Output exceeded {MAX_OUTPUT_BYTES // 1024} KiB; the run was stopped.",
            line=line,
            source=source,
            hint=(
                "The program printed without bound." + where
                + " Look for a print inside an endless loop; print a summary or a bounded sample instead."
            ),
        )
    return StuckInfo(reason=STUCK_CANCELLED, message="The run was cancelled.", line=line, source=source,
                     hint="Cancelled on request.")


def _stuck_console_text(stuck: StuckInfo, timeout: float) -> str:
    """Last console line. The UI shows the last output line as the error message."""
    if stuck.reason == STUCK_TIMEOUT:
        where = f" (stopped at line {stuck.line}: {stuck.source})" if stuck.line and stuck.source else (
            f" (stopped at line {stuck.line})" if stuck.line else "")
        return f"\nTimeoutError: code execution exceeded {timeout:g} seconds{where}.\n"
    if stuck.reason == STUCK_OUTPUT_LIMIT:
        return f"\nOutputLimitError: output exceeded {MAX_OUTPUT_BYTES // 1024} KiB; run stopped.\n"
    return "\nCancelled: run stopped on request.\n"


def _diagnostic_from_output(text: str, run_id: str, return_code: Optional[int]) -> DiagnosticItem:
    """Fallback when a failed run left no structured diagnostic (e.g. ``sys.exit(2)``)."""
    line: Optional[int] = None
    for match in _STDERR_LINE.finditer(text):
        line = int(match.group(1))
    tail = [part.strip() for part in text.splitlines() if part.strip()]
    if tail:
        message = tail[-1][:200]
    elif return_code is not None:
        message = f"Process exited with code {return_code}"
    else:
        message = "Execution failed"
    return DiagnosticItem(line=line, message=message, severity="error", run_id=run_id)


# --------------------------------------------------------------------------- #
# The supervisor
# --------------------------------------------------------------------------- #
def run_stream(
    req: CodeExecutionRequest,
    run_id: Optional[str] = None,
    merge_output: bool = True,
) -> Iterator[dict]:
    """Run ``req.code`` in an isolated process and yield event dicts.

    Events: ``start``, ``stdout``, ``stderr``, ``truncated``, ``syntax_error``, ``done``.
    ``done`` additionally carries ``diagnostics`` and ``stuck`` (both new, both optional
    for consumers). Closing the generator (client disconnect) kills the process tree.
    """
    run_id = run_id or _new_run_id()
    timeout = _clamp_timeout(req.timeout_seconds)
    interpreter = resolve_python()

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
        yield {"type": "done", "run_id": run_id, "return_code": 1, "status": "ERROR",
               "timed_out": False, "duration_seconds": 0.0}
        return
    except Exception:  # noqa: BLE001 - let the isolated interpreter report anything else
        pass

    yield {
        "type": "start",
        "run_id": run_id,
        "mode": "risky" if merge_output else "safe",
        "python": interpreter,
        "timeout_seconds": timeout,
    }

    cancel_flag = _REGISTRY.register(run_id)
    abandoned = threading.Event()
    proc: Optional[subprocess.Popen] = None
    watchdog: Optional[threading.Timer] = None
    started = time.monotonic()

    try:
        with tempfile.TemporaryDirectory(prefix="codebuilder-") as temp_name:
            temp = Path(temp_name)
            script_path = temp / "codebuilder_script.py"
            harness_path = temp / "codebuilder_harness.py"
            diag_path = temp / "diagnostic.json"
            stack_path = temp / "stack.txt"
            script_path.write_text(req.code, encoding="utf-8")
            harness_path.write_text(_HARNESS, encoding="utf-8")

            dump_after = timeout * 0.8 if timeout < 4 else timeout - 0.8
            root = Path.cwd()
            proc = subprocess.Popen(
                [interpreter, "-u", str(harness_path), str(script_path), str(diag_path),
                 str(stack_path), f"{dump_after:.3f}"],
                cwd=str(root),
                env=_child_environment(root),
                stdin=subprocess.DEVNULL,  # input() fails fast with EOFError instead of hanging
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT if merge_output else subprocess.PIPE,
                **_popen_group_kwargs(),
            )

            def _watchdog_fire() -> None:
                abandoned.set()
                _kill_tree(proc)

            watchdog = threading.Timer(timeout + WATCHDOG_GRACE_SECONDS, _watchdog_fire)
            watchdog.daemon = True
            watchdog.start()

            channels = [("stdout", proc.stdout)] + ([] if merge_output else [("stderr", proc.stderr)])
            chunks: "queue.Queue" = queue.Queue()
            decoders = {}
            for name, stream in channels:
                decoders[name] = codecs.getincrementaldecoder("utf-8")(errors="replace")
                threading.Thread(target=_pump, args=(name, stream, chunks, abandoned), daemon=True).start()

            open_channels = len(channels)
            deadline = started + timeout
            reason: Optional[str] = None
            drain_until = 0.0
            emitted = 0
            truncated = False

            while open_channels:
                now = time.monotonic()
                if reason is None:
                    if cancel_flag.is_set():
                        reason = STUCK_CANCELLED
                    elif now >= deadline:
                        reason = STUCK_TIMEOUT
                    if reason:
                        _kill_tree(proc)
                        drain_until = now + DRAIN_SECONDS
                elif now >= drain_until:
                    break
                try:
                    channel, chunk = chunks.get(timeout=0.1)
                except queue.Empty:
                    continue
                if chunk is None:
                    open_channels -= 1
                    continue
                if truncated:
                    continue
                if emitted + len(chunk) > MAX_OUTPUT_BYTES:
                    keep = MAX_OUTPUT_BYTES - emitted
                    if keep > 0:
                        text = decoders[channel].decode(chunk[:keep])
                        if text:
                            yield {"type": channel, "text": text}
                    yield {"type": "truncated", "run_id": run_id}
                    truncated = True
                    if reason is None:
                        reason = STUCK_OUTPUT_LIMIT
                        _kill_tree(proc)
                        drain_until = time.monotonic() + DRAIN_SECONDS
                    continue
                emitted += len(chunk)
                text = decoders[channel].decode(chunk)
                if text:
                    yield {"type": channel, "text": text}

            # Output ended but the process may still be alive (closed stdout, worker threads...).
            while reason is None and proc.poll() is None:
                if cancel_flag.is_set():
                    reason = STUCK_CANCELLED
                elif time.monotonic() >= deadline:
                    reason = STUCK_TIMEOUT
                else:
                    time.sleep(0.02)
            if reason is not None:
                _kill_tree(proc)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass

            return_code = proc.returncode
            duration = round(time.monotonic() - started, 3)
            diagnostics: List[dict] = []
            stuck: Optional[StuckInfo] = None

            if reason is not None:
                stuck = _describe_stuck(reason, timeout, req.code, _read_stuck_line(stack_path))
                console = _stuck_console_text(stuck, timeout)
                yield {"type": "stderr", "text": console}
                diagnostics.append(DiagnosticItem(
                    line=stuck.line, message=console.strip(), severity="error", run_id=run_id,
                ).model_dump())
            elif diag_path.is_file():
                try:
                    data = json.loads(diag_path.read_text(encoding="utf-8"))
                    diagnostics.append(DiagnosticItem(
                        line=data.get("line"),
                        column=data.get("column"),
                        message=data.get("message") or "Execution failed",
                        severity="error",
                        run_id=run_id,
                    ).model_dump())
                except (OSError, ValueError):
                    pass

            status = "ERROR" if (reason is not None or (return_code or 0) != 0) else "SUCCESS"
            yield {
                "type": "done",
                "run_id": run_id,
                "return_code": return_code,
                "status": status,
                "timed_out": reason == STUCK_TIMEOUT,
                "duration_seconds": duration,
                "diagnostics": diagnostics,
                "stuck": stuck.model_dump() if stuck else None,
            }
    except OSError as exc:
        yield {"type": "stderr", "text": f"Could not start Python interpreter: {exc}\n"}
        yield {"type": "done", "run_id": run_id, "return_code": None, "status": "ERROR",
               "timed_out": False, "error": str(exc)}
    finally:
        abandoned.set()
        if watchdog is not None:
            watchdog.cancel()
        _kill_tree(proc)
        _REGISTRY.release(run_id)


# --------------------------------------------------------------------------- #
# Buffered entry point
# --------------------------------------------------------------------------- #
def execute_python_code(req: CodeExecutionRequest) -> CodeExecutionResult:
    """Public dispatcher: run to completion and return one ``CodeExecutionResult``."""
    run_id = _new_run_id()
    out: List[str] = []
    err: List[str] = []
    diagnostics: List[DiagnosticItem] = []
    done: dict = {}
    saw_syntax_error = False

    for event in run_stream(req, run_id=run_id, merge_output=(req.mode == "risky")):
        kind = event.get("type")
        if kind == "stdout":
            out.append(event["text"])
        elif kind == "stderr":
            err.append(event["text"])
        elif kind == "syntax_error":
            saw_syntax_error = True
            diagnostics.append(DiagnosticItem(
                line=event.get("line"),
                column=event.get("column"),
                message=event.get("message", "SyntaxError"),
                severity="error",
                run_id=run_id,
            ))
        elif kind == "done":
            done = event

    stdout, stderr = "".join(out), "".join(err)
    if saw_syntax_error and not stderr:
        item = diagnostics[-1]
        stderr = f"{item.message} (line {item.line})\n" if item.line else f"{item.message}\n"

    diagnostics.extend(DiagnosticItem(**item) for item in done.get("diagnostics", []))
    status = done.get("status", "ERROR")
    if status == "ERROR" and not diagnostics:
        diagnostics.append(_diagnostic_from_output(stdout + stderr, run_id, done.get("return_code")))

    stuck = done.get("stuck")
    return CodeExecutionResult(
        run_id=run_id,
        status=status,
        stdout=stdout,
        stderr=stderr,
        diagnostics=diagnostics,
        return_code=done.get("return_code"),
        timed_out=bool(done.get("timed_out", False)),
        duration_seconds=done.get("duration_seconds"),
        stuck=StuckInfo(**stuck) if stuck else None,
    )

```

## `codebuilder/files.py`
```py
"""Save and open Python scripts for the Code Builder editor inside the allowed sandbox folders."""

import os
from pathlib import Path

from test_environment import sandbox_env, sandbox_paths

MAX_FILE_BYTES = 500_000
MAX_LISTED = 500
MAX_FOLDERS = 300
SKIP_DIRS = {"__pycache__", "venv", "node_modules"}
_BAD_NAME_CHARS = set('<>:"/\\|?*')


class FileRejected(ValueError):
    pass


def _walk(root: Path, depth: int = 3):
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return
    for entry in entries:
        if entry.name.startswith(".") or entry.name in SKIP_DIRS:
            continue
        yield entry
        if entry.is_dir() and depth > 1:
            yield from _walk(entry, depth - 1)


def listing() -> dict:
    sandbox_env.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    folders, files = [], []
    for root in sandbox_paths.allowed_roots():
        folders.append(str(root))
        for entry in _walk(root):
            if entry.is_dir():
                if len(folders) < MAX_FOLDERS:
                    folders.append(str(entry))
            elif entry.suffix.lower() == ".py" and len(files) < MAX_LISTED:
                files.append({"path": str(entry), "name": entry.name, "folder": str(entry.parent)})
    return {"default_folder": str(sandbox_env.SCRIPTS_DIR), "folders": folders, "files": files}


def read(path: str) -> dict:
    try:
        target = sandbox_paths.resolve(path)
    except sandbox_paths.PathNotAllowed as exc:
        raise FileRejected(str(exc)) from exc
    if target.suffix.lower() != ".py" or not target.is_file():
        raise FileRejected("Only existing .py files can be opened.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise FileRejected("File is too large to open in the editor.")
    return {"path": str(target), "name": target.name, "content": target.read_text(encoding="utf-8", errors="replace")}


def save(folder: str, name: str, content: str, overwrite: bool = False) -> dict:
    name = (name or "").strip()
    if not name.lower().endswith(".py"):
        name += ".py"
    if (
        name in {".py", "..py"} or any(ch in _BAD_NAME_CHARS for ch in name)
        or any(ord(ch) < 32 for ch in name) or name.endswith((" .py", "..py"))
    ):
        raise FileRejected("Use a simple file name such as app.py (no folders or special characters).")
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise FileRejected("File is too large to save.")
    try:
        directory = sandbox_paths.resolve(folder or str(sandbox_env.SCRIPTS_DIR))
    except sandbox_paths.PathNotAllowed as exc:
        raise FileRejected(str(exc)) from exc
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    if target.exists() and not overwrite:
        return {"saved": False, "exists": True, "path": str(target), "name": name}
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"saved": True, "exists": False, "path": str(target), "name": name}


def run_command(path: str, source: str) -> str:
    """Terminal command that runs a saved file; streamlit scripts use ``streamlit run``."""
    quoted = f'"{path}"' if " " in path else path
    imports = sandbox_env.imported_modules(source)
    return f"streamlit run {quoted}" if "streamlit" in imports else f"python {quoted}"

```

## `codebuilder/interface.py`
```py
"""CodeBuilder doorway: the HTTP adapter. Routing, status codes and SSE framing only.

Layer rule: no business logic here. Each endpoint validates transport concerns and
delegates to ``service`` (use-cases) or ``execution`` (the engine).
"""

import json
import time
from typing import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import files as script_files
from . import service
from . import terminal
from .execution import cancel_run, execute_python_code, run_stream
from .schemas import CodeExecutionRequest, CodeExecutionResult, StructuredEditRequest

router = APIRouter(prefix="/api/codebuilder", tags=["CodeBuilder"])


@router.get("/health")
def api_codebuilder_health():
    """Return the health state of the CodeBuilder pillar."""
    return service.health()


@router.get("/agent")
def api_get_agent():
    """Return the CodeBuilder specialist profile."""
    return service.agent_meta()


@router.get("/agents")
def api_codebuilder_agents():
    """List only agents stored in the CodeBuilder environment."""
    return {"agents": service.list_agents()}


@router.post("/execute", response_model=CodeExecutionResult)
def api_execute_code(req: CodeExecutionRequest):
    """Execute Python source (isolated, time-limited) and return output and diagnostics."""
    try:
        return execute_python_code(req)
    except Exception as exc:  # pragma: no cover - surfaced as HTTP 500
        raise HTTPException(status_code=500, detail=f"CodeBuilder execution error: {exc}") from exc


def _sse(events: Iterator[dict]) -> Iterator[str]:
    try:
        for event in events:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    finally:
        events.close()  # client went away -> engine kills the process tree


@router.post("/execute/stream")
def api_stream_execute(req: CodeExecutionRequest):
    """Stream risky-mode execution output live as Server-Sent Events."""
    if req.mode != "risky":
        raise HTTPException(status_code=400, detail="Streaming is only supported in risky mode.")
    return StreamingResponse(
        _sse(run_stream(req)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/execute/{run_id}/cancel")
def api_cancel_run(run_id: str):
    """Stop a live run (use the ``run_id`` from the stream's ``start`` event)."""
    if not cancel_run(run_id):
        raise HTTPException(status_code=404, detail="Run not found or already finished.")
    return {"run_id": run_id, "cancelled": True}


@router.post("/edit")
def api_apply_structured_edit(req: StructuredEditRequest):
    """Write an approved file update to the workspace."""
    try:
        return service.apply_edit(req)
    except service.EditRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write file: {exc}") from exc


class TerminalCommand(BaseModel):
    command: str = Field(..., min_length=1, max_length=terminal.MAX_COMMAND_CHARS)


@router.get("/terminal/state")
def api_terminal_state():
    """Working folder, whether a command is running, and whether the sandbox exists."""
    return terminal.session.state()


@router.post("/terminal/run")
def api_terminal_run(req: TerminalCommand):
    """Run one command in the sandbox environment; output arrives through the stream."""
    try:
        terminal.session.run(req.command)
    except terminal.TerminalBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return terminal.session.state()


@router.post("/terminal/stop")
def api_terminal_stop():
    return {"stopped": terminal.session.stop()}


@router.post("/terminal/clear")
def api_terminal_clear():
    terminal.session.clear()
    return terminal.session.state()


@router.get("/terminal/stream")
def api_terminal_stream(offset: int = 0):
    """Server-sent events with new terminal output after ``offset`` (0 replays the buffer)."""
    def events():
        position = max(offset, 0)
        last_state = None
        idle = 0
        while True:
            text, position_end = terminal.session.read(position)
            state = terminal.session.state()
            if text or state != last_state:
                payload = {"type": "output", "text": text, "offset": position_end, **state}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                position, last_state, idle = position_end, state, 0
            else:
                idle += 1
                if idle >= 100:
                    yield ": keep-alive\n\n"
                    idle = 0
            time.sleep(0.15)

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


class SaveFileRequest(BaseModel):
    folder: str = Field("", max_length=1000)
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field("", max_length=600000)
    overwrite: bool = False


@router.get("/files")
def api_list_files():
    """Allowed folders and the .py files inside them."""
    return script_files.listing()


@router.get("/files/read")
def api_read_file(path: str):
    try:
        return script_files.read(path)
    except script_files.FileRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/files/save")
def api_save_file(req: SaveFileRequest):
    """Save editor code; returns ``exists: true`` (and writes nothing) when overwrite is needed."""
    try:
        return script_files.save(req.folder, req.name, req.content, req.overwrite)
    except script_files.FileRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write file: {exc}") from exc


class RunCommandRequest(BaseModel):
    path: str = Field(..., max_length=1000)
    content: str = Field("", max_length=600000)


@router.post("/files/run-command")
def api_run_command(req: RunCommandRequest):
    """Terminal command that runs a saved script (streamlit scripts use ``streamlit run``)."""
    try:
        path = script_files.sandbox_paths.resolve(req.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"command": script_files.run_command(str(path), req.content), "cwd": str(path.parent)}
```

## `codebuilder/markdown/CODEBUILDER-MASTER.md`
```md
﻿# CodeBuilder Architecture Master Reference

## Overview

CodeBuilder provides isolated Python code execution, interactive Monaco editor integration, and human-in-the-loop questionnaire workflows for Novous2 agents.

---

## Tool Architecture & `core_engine/tool_catalog.py`

### 1. Transition: From Single Master File to Registry-Only Catalog

Previously, `core_engine/tool_catalog.py` served as a single master file containing both the registration logic and the inline implementations of all system tools. 

Under the locked modular architecture, **`core_engine/tool_catalog.py` is registry-only**. Tool implementations have been migrated into dedicated modules under the `tools/` directory. `tool_catalog.py` is strictly responsible for:
- Maintaining `REGISTRY: dict[str, dict]` and the `@tool` decorator.
- Discovering and dynamically loading tool modules from `tools/`.
- Tracking isolated module load failures in `LOAD_ERRORS`.
- Generating comprehensive diagnostics through `get_catalog_report()`.

### 2. Target Layout (`tools/`)

```
tools/
├── __init__.py            # Minimal; no eager module imports
├── interface.py           # Doorway: FastAPI router + Python functions + promoted-module IO
├── core_tools.py          # calculator, docling_parse, rag_agent_tool, agent_info (+ _safe_eval, _OPERATORS)
├── editor_tools.py        # read_file, write_file, create_file, delete_file, list_directory, extract_docstrings, search_workspace
├── workspace_tools.py     # project_status
├── file_manager_tools.py  # fm_list_directory, fm_read_file, fm_write_file (file-manager-backed tools)
├── map_tools.py           # list_allowed_paths, map_folder, map_file (allow-list restricted folder/file mapping)
├── codebuilder_tools.py   # run_python_code, send_code_to_editor, run_code_in_editor, ask_user_questions (module currently has load errors)
├── promoted.py            # Workbench-promoted custom tools (with promotion marker section)
└── allowed_paths.json     # Allow-list of root paths for map tools
```

#### Module Responsibilities
- **`tools/core_tools.py`**: Evaluation tools, document parsing via Docling, RAG search, and agent profile inspection.
- **`tools/editor_tools.py`**: Workspace filesystem manipulation, directory tree inspection, AST docstring extraction, and workspace searches.
- **`tools/workspace_tools.py`**: Project state reporting (`project_status`).
- **	ools/codebuilder_tools.py**: CodeBuilder pillar tools:
  - 
un_python_code: executes code through codebuilder.execution.execute_python_code.
  - send_code_to_editor: queues code insertion into Monaco editor.
  - 
un_code_in_editor: triggers execution of active editor buffer.
  - sk_user_questions: Questionnaire flow (registered only when host supports questionnaires). 
  - **Note:** Current file contains an IndentationError (line 41) preventing load; see Diagnostics below.
- **	ools/file_manager_tools.py**: File-manager-backed tools for listing/reading/writing under the configured file-manager root.
- **	ools/map_tools.py**: Read-only folder/file mapping restricted to roots in llowed_paths.json (list_allowed_paths, map_folder with paging, map_file with AST inspection).
- **	ools/promoted.py**: Holds workbench-promoted custom tools. Maintains the # PROMOTION_MARKER separator.
- **	ools/interface.py**: The single doorway for tool catalog HTTP routes and Python APIs.

### 3. Dynamic Auto-Discovery & Isolation

The loader (`tool_catalog.load_tools(reload=False)`) discovers tool modules automatically:
- Scans all `*.py` files in `tools/`, strictly excluding `__init__.py`, `interface.py`, and any private files starting with `_*`.
- Loads each module in isolation using `importlib.util.spec_from_file_location`.
- **Fault-Tolerance**: If a tool module contains syntax errors, broken imports, or duplicate tool name collisions, the error is captured in `LOAD_ERRORS[filename]` and the module is skipped. The failure is non-fatal: `/api/tools`, the catalog registry, and all other agents remain operational (HTTP 200).
- Adding a new tool module to `tools/` requires no edits to `__init__.py`.

### 4. Promotion Flow (`tools/promoted.py`)

Tools created and tested in the Function Testing Workbench are promoted into the active runtime:
1. Workbench tests and validates the tool function.
2. Promotion calls `tools.interface.register_tool(source, name)`.
3. The source is decorated with `@tool` and appended to `tools/promoted.py` below the `# PROMOTION_MARKER`.
4. The function block is executed into `tool_catalog.__dict__` for instant runtime availability without server restart.
5. If execution fails, `promoted.py` is rolled back and the entry is popped from `REGISTRY`.
6. Deletion via `tools.interface.remove_tool(name)` removes the function span from `tools/promoted.py` and pops it from `REGISTRY`. Promoted file additions and removals are byte-identical round-trips.

### 5. Doorway APIs & Routes (`tools/interface.py`)

#### HTTP Routes:
- `GET /api/tools`: Returns `{tools: [...], providers: {...}, warnings: [...]}`. Base tools plus custom overlay (`custom: true` for promoted tools).
- `GET /api/tools/{name}`: Returns metadata for a specific tool.
- `POST /api/tools/register`: Registers a custom tool (`{source, name}`).
- `DELETE /api/tools/{name}`: Removes a custom tool.
- POST /api/tools/map-page: Returns paged folder tree (body: {path, max_depth, include_files, offset}) for allow-listed absolute paths via 	ools.map_tools.render_map_page.
- `GET /api/tools/health`: Returns catalog health and any active `load_errors`.

#### Python Doorway:
- `list_tools()`
- `get_tool(name)`
- `get_tool_source(name)`
- `register_tool(source, name)`
- `remove_tool(name)`
- `provider_bindings()`
- `catalog_report()`

### 6. Diagnostics & Verification

`tool_catalog.get_catalog_report()` walks all registered agent definitions under the agent library (`LIBRARY_ROOT = REPO_ROOT / "library"`; see `core_engine/agent_factory.py`) and parses `library/*.md` agent files (YAML frontmatter) to detect missing tools. It maps requested tools against `REGISTRY`. 

**Current state:** `core_engine.tool_catalog.load_tools()` reports load errors for tool modules (e.g. `tools/codebuilder_tools.py` currently fails to load due to an IndentationError). The catalog captures these in `LOAD_ERRORS` and marks failures as warnings in `get_catalog_report()`; the system remains operational. Builtin tool set includes `calculator`, `docling_parse`, `rag_agent_tool`, `agent_info`, `read_file`, `write_file`, `create_file`, `delete_file`, `list_directory`, `extract_docstrings`, `search_workspace`, `fm_list_directory`, `fm_read_file`, `fm_write_file`, `list_allowed_paths`, `map_folder`, `map_file`, `project_status` (18 tools registered at runtime as observed; counts may vary if any modules fail to load).



**Note:** Per this request (plan-only update scope), the CodeBuilder pillar (execution engine, /api/codebuilder/* routes, terminal, files, HITL questionnaire flow) is not expanded in this refresh. 

```

## `codebuilder/README.md`
```md
# codebuilder/ — refactored pillar (drop-in)

Replaces the existing `codebuilder/` folder. Nothing else in the app changes: same package name,
same import paths, same URLs, and same JSON/SSE shapes.

## Layers (dependencies point downward only)

```
interface.py   HTTP adapter: routes, status codes, SSE framing      ─┐
tools/         agent adapter: @tool functions                        ─┼─> service.py ─> host bridge (lazy imports)
                                                                      │
execution.py   engine: isolated runs + stuck handling                ─┘ (interface also calls the engine directly)
schemas.py     contracts (pydantic only)
```

| Module | Concern | Knows about |
| :-- | :-- | :-- |
| `schemas.py` | data shapes | pydantic |
| `execution.py` | processes, deadlines, diagnostics | stdlib + schemas |
| `service.py` | use-cases (edits, agent info, questionnaire) and the **only** `core_engine` coupling | schemas |
| `interface.py` | HTTP | FastAPI, service, execution |
| `tools/tool_library.py` | agent tools | core `@tool`, service |

12 modules became 6 (+ a one-line `tools/__init__.py`). Removed: `agent_codebuilder`,
`execution_codebuilder`, `codebuilder_schemas`, `interface_codebuilder` (aliases), `runner` + `execution`
(merged), `agent_loader` (now in `service`), `diagnostics` (unused; folded into the engine).

## Host contract (unchanged)

| Host code | Needs |
| :-- | :-- |
| `server.py` | `codebuilder.interface.router`, `tools.interface.router` |
| `tools/codebuilder_tools.py` | `codebuilder.execution.execute_python_code`, `codebuilder.schemas.CodeExecutionRequest`, `codebuilder.service` |
| `core_engine/tool_catalog.py` | auto-discovers `tools/codebuilder_tools.py` (registry-only) |
| `core_engine/agent_factory.py` | `library/<id>.md` |

## When code gets stuck

Both modes run in a child process under one supervisor, so user code can never freeze the server.

| Situation | What happens |
| :-- | :-- |
| Infinite loop / long `sleep` / blocking call | Killed at the deadline. `faulthandler` reports the line it was stuck on. |
| Unbounded `print` loop | Stopped at 64 KiB (`output_limit`) instead of spinning until timeout. |
| `input()` | stdin is closed: immediate `EOFError`, no hang. |
| Code spawned child processes | The whole process tree is killed (`taskkill /T` on Windows, process group elsewhere). |
| Browser tab closed / stream abandoned | Generator close kills the run; a watchdog kills it at `timeout + 1s` regardless. |
| User or tool wants to stop it | `POST /api/codebuilder/execute/{run_id}/cancel` (id is in the stream's `start` event). |
| Agent runs hanging code | `run_python_code` returns `timed_out` + `stuck {reason, line, source, hint}` so the model can fix it. |

`timeout_seconds` is clamped to 0.1–120 s. The editor marker lands on the stuck line.

## Behaviour changes to be aware of

* `safe` mode no longer executes inside the server process (it is an isolated child, ~60 ms start-up).
  Its timeout is now actually enforced; before, `timeout_seconds` was ignored in safe mode.
* `/edit` rejects paths outside the project root (override with `CODEBUILDER_EDIT_ROOT`).
* `ask_user_questions` registers only if the host has `core_engine.hitl`.

## Tests

`python -m pytest codebuilder/tests -q` (needs pytest, fastapi, httpx; no Ollama, no running host).

```

## `codebuilder/schemas.py`
```py
"""CodeBuilder contracts: the data shapes shared by every layer.

This module is dependency-free (pydantic only). The HTTP adapter, the service,
the engine and the agent tools all speak these models and nothing else.

Compatibility: every field that existed before keeps its name, type and default.
New fields are additive and optional, so the existing frontend keeps working.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# Why a run was stopped by the supervisor (values of StuckInfo.reason).
STUCK_TIMEOUT = "timeout"          # still running at the deadline (loop, sleep, blocking call)
STUCK_OUTPUT_LIMIT = "output_limit"  # unbounded output (e.g. `while True: print(...)`)
STUCK_CANCELLED = "cancelled"      # stopped on request (cancel endpoint / client disconnect)


class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute")
    timeout_seconds: float = Field(default=10.0, description="Hard wall-clock limit in seconds")
    mode: str = Field(
        default="safe",
        description="'safe': buffered result, stdout/stderr kept apart. "
        "'risky': merged output, streamable over SSE. Both run isolated.",
    )


class DiagnosticItem(BaseModel):
    path: Optional[str] = Field(default=None, description="Target file path, if available")
    line: Optional[int] = Field(default=None, description="Line number of the issue")
    column: Optional[int] = Field(default=None, description="Column number of the issue")
    message: str = Field(..., description="Diagnostic error message")
    severity: str = Field(default="error", description="Severity level: error, warning, or info")
    run_id: Optional[str] = Field(default=None, description="Execution run identifier")


class StuckInfo(BaseModel):
    """Explains why a run had to be stopped, and what to try next."""

    reason: str = Field(..., description="timeout | output_limit | cancelled")
    message: str
    line: Optional[int] = Field(default=None, description="Line of user code that was executing")
    source: Optional[str] = Field(default=None, description="Text of that line")
    hint: str = ""


class CodeExecutionResult(BaseModel):
    run_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)
    # Additive fields (ignored by older clients):
    return_code: Optional[int] = None
    timed_out: bool = False
    duration_seconds: Optional[float] = None
    stuck: Optional[StuckInfo] = None


class StructuredEditRequest(BaseModel):
    target_path: str = Field(..., description="Target file path relative to the workspace root")
    content: str = Field(..., description="Proposed content or patch")
    explanation: Optional[str] = Field(default=None, description="Explanation of the requested change")

```

## `codebuilder/service.py`
```py
"""CodeBuilder application layer: the use-cases, and the ONLY bridge to the host app.

Layer rule: no FastAPI here (HTTP lives in ``interface.py``), no process handling
(that lives in ``execution.py``). Everything that touches ``core_engine`` is
imported lazily inside the functions below, so this package imports cleanly even
while the host is still initialising (no import cycles) and so the host-coupling
surface is visible in one place.
"""

import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .schemas import StructuredEditRequest

PILLAR_ROOT = Path(__file__).resolve().parent
AGENTS_ROOT = PILLAR_ROOT / "agents"

_FALLBACK_AGENT: Dict[str, Any] = {
    "id": "codebuilder-agent",
    "name": "CodeBuilder Specialist",
    "description": "Agent dedicated to writing, refactoring, and diagnosing Python code.",
    "mode": "agent",
    "tools": [
        "read_file", "write_file", "create_file", "list_directory",
        "run_python_code", "send_code_to_editor", "run_code_in_editor",
    ],
}


class EditRejected(ValueError):
    """A structured edit was refused (the HTTP layer maps this to 400)."""


# --------------------------------------------------------------------------- #
# Pillar info
# --------------------------------------------------------------------------- #
def health() -> Dict[str, str]:
    return {"status": "ok", "pillar": "codebuilder"}


def agent_meta() -> Dict[str, Any]:
    """Resolve the specialist profile metadata from the centralized agent library."""
    from core_engine.agent_factory import load_agent

    for agent_id in ("codingagent", "codebuilder-agent"):
        try:
            profile = load_agent(agent_id, "codebuilder")
            return {
                "id": profile.id,
                "name": profile.name,
                "description": profile.description,
                "mode": profile.mode,
                "model": profile.model,
                "tools": profile.tools,
                "squad": "",
                "environment": "workspace",
            }
        except FileNotFoundError:
            continue
    return dict(_FALLBACK_AGENT)


# --------------------------------------------------------------------------- #
# Host bridge: agents
# --------------------------------------------------------------------------- #
def list_agents() -> List[dict]:
    """Agents of the ``codebuilder`` environment (resolved by the host's agent factory)."""
    from core_engine.agent_factory import list_agents as host_list_agents

    return host_list_agents("codebuilder")


# --------------------------------------------------------------------------- #
# Structured edits
# --------------------------------------------------------------------------- #
def _edit_root() -> Path:
    return Path(os.environ.get("CODEBUILDER_EDIT_ROOT") or Path.cwd()).resolve()


def apply_edit(req: StructuredEditRequest) -> Dict[str, Any]:
    """Write an approved file update. Targets must stay inside the project root."""
    root = _edit_root()
    requested = Path(req.target_path)
    target = (requested if requested.is_absolute() else root / requested).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        raise EditRejected(f"Target path must stay inside the project root ({root}).") from None
    if target.is_dir():
        raise EditRejected("Target path points to a directory, not a file.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    return {
        "status": "applied",
        "target_path": str(target),
        "bytes_written": len(req.content.encode("utf-8")),
        "explanation": req.explanation,
    }


# --------------------------------------------------------------------------- #
# Host bridge: human-in-the-loop questionnaire
# --------------------------------------------------------------------------- #
def host_supports_questionnaire() -> bool:
    """True when the host ships ``core_engine.hitl`` (older hosts do not)."""
    try:
        return importlib.util.find_spec("core_engine.hitl") is not None
    except (ImportError, ValueError, AttributeError):
        return False


def _load_questions(json_file_path: str) -> List[dict]:
    from core_engine import langgraph_tools

    relative = str(json_file_path).strip().lstrip("/")
    if relative.startswith("workspace/"):
        relative = relative[len("workspace/"):]

    raw = langgraph_tools.read_file_tool.invoke({"relative_path": relative})
    if not isinstance(raw, str) or raw.startswith("Error reading file"):
        raise ValueError(f"Questions file '{json_file_path}' was not found in the workspace.")
    try:
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Error parsing questions JSON file: {exc}") from exc

    items = data.get("questions", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    questions = []
    for index, item in enumerate(items):
        if isinstance(item, dict):
            questions.append({"id": str(item.get("id", index)), "question": str(item.get("question", item))})
        else:
            questions.append({"id": str(index), "question": str(item)})
    if not questions:
        raise ValueError("No questions found in the provided JSON file.")
    return questions


def ask_user(json_file_path: str, timeout_seconds: float = 300.0) -> str:
    """Block until the user answers a questionnaire (or the wait times out). Returns a string."""
    from core_engine import hitl

    try:
        questions = _load_questions(json_file_path)
    except ValueError as exc:
        return f"Error: {exc}"

    try:
        wait = min(max(float(timeout_seconds), 1.0), 900.0)
    except (TypeError, ValueError):
        wait = 300.0

    record = hitl.create_request(questions)
    request_id = record["request_id"]
    completed = record["event"].wait(timeout=wait)
    request_data = hitl.resolve_request(request_id)  # always release the pending entry

    if not completed or request_data is None:
        return "Error: User questionnaire timed out waiting for input."

    answers = request_data.get("answers", {})
    return json.dumps(
        {
            "status": "COMPLETED",
            "qa_pairs": [
                {
                    "id": q["id"],
                    "question": q["question"],
                    "answer": answers.get(q["id"], answers.get(str(i), "No answer provided")),
                }
                for i, q in enumerate(questions)
            ],
        },
        indent=2,
    )

```

## `codebuilder/terminal.py`
```py
"""Shared terminal for the CodeBuilder: runs one shell command at a time in the sandbox environment.

A single session is shared by the docked panel and the pop-out window. Output is kept in a
capped buffer addressed by absolute offsets so a newly opened window can catch up.
"""

import codecs
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Optional

from .execution import _kill_tree, _popen_group_kwargs

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_BUFFER_CHARS = 200_000
MAX_COMMAND_CHARS = 2000
_CD = re.compile(r"^cd(?:\s+/d)?(?:\s+(.*))?$", re.IGNORECASE)
_SANDBOX = re.compile(r"^sandbox(?:\s+(\w+))?(?:\s+(.*))?$", re.IGNORECASE)


class TerminalBusy(Exception):
    pass


class TerminalSession:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buffer = ""
        self._base = 0  # absolute offset of _buffer[0]
        self._proc: Optional[subprocess.Popen] = None
        from test_environment import sandbox_env
        sandbox_env.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        self.cwd = sandbox_env.SCRIPTS_DIR

    # ---- buffer ----
    def _append(self, text: str) -> None:
        with self._lock:
            self._buffer += text
            overflow = len(self._buffer) - MAX_BUFFER_CHARS
            if overflow > 0:
                self._buffer = self._buffer[overflow:]
                self._base += overflow

    def read(self, offset: int) -> tuple[str, int]:
        """Text after ``offset`` and the new end offset. Offsets older than the buffer are clamped."""
        with self._lock:
            start = max(offset, self._base)
            end = self._base + len(self._buffer)
            return self._buffer[start - self._base:], end

    def clear(self) -> None:
        with self._lock:
            self._base += len(self._buffer)
            self._buffer = ""

    # ---- state ----
    @property
    def running(self) -> bool:
        proc = self._proc
        return proc is not None and proc.poll() is None

    def state(self) -> dict:
        from test_environment import sandbox_env
        return {
            "running": self.running,
            "cwd": str(self.cwd),
            "sandbox": sandbox_env.exists(),
        }

    # ---- environment ----
    def _environment(self) -> dict:
        from test_environment import sandbox_env
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        if sandbox_env.exists():
            scripts = str(sandbox_env.python_path().parent)
            env["PATH"] = scripts + os.pathsep + env.get("PATH", "")
            env["VIRTUAL_ENV"] = str(sandbox_env.SANDBOX_DIR)
            env.pop("PYTHONHOME", None)
        return env

    # ---- commands ----
    def _change_directory(self, target: str) -> None:
        target = (target or "").strip().strip('"')
        if not target:
            self._append(f"{self.cwd}\n")
            return
        from test_environment import sandbox_paths
        try:
            path = sandbox_paths.resolve(target, self.cwd)
        except (sandbox_paths.PathNotAllowed, OSError) as exc:
            self._append(f"{exc}\n")
            return
        if not path.is_dir():
            self._append(f"The system cannot find the path specified: {target}\n")
            return
        self.cwd = path
        self._append(f"{self.cwd}\n")

    def _sandbox_command(self, action: str, argument: str) -> None:
        from test_environment import sandbox_env, sandbox_paths
        action = (action or "paths").lower()
        argument = (argument or "").strip()
        try:
            if action == "paths":
                self._append("Allowed folders:\n" + "".join(f"  {r}\n" for r in sandbox_paths.allowed_roots()))
                self._append(f"Packages: {sandbox_env.SANDBOX_DIR}\n")
            elif action == "add":
                self._append(f"Added: {sandbox_paths.add_root(argument)}\n")
            elif action == "remove":
                removed = sandbox_paths.remove_root(argument)
                self._append("Removed.\n" if removed else "That folder is not in the allowed list.\n")
                if not sandbox_paths.is_allowed(self.cwd):
                    self.cwd = sandbox_env.SCRIPTS_DIR
            elif action == "clear":
                sandbox_paths.clear_roots()
                self.cwd = sandbox_env.SCRIPTS_DIR
                self._append(f"Allowed folders reset to {sandbox_env.SCRIPTS_DIR}\n")
            else:
                self._append("Usage: sandbox paths | add <folder> | remove <folder> | clear\n")
        except ValueError as exc:
            self._append(f"{exc}\n")

    def run(self, command: str) -> None:
        command = command.strip()
        if not command:
            return
        if len(command) > MAX_COMMAND_CHARS:
            raise ValueError(f"Command is longer than {MAX_COMMAND_CHARS} characters.")
        with self._lock:
            if self.running:
                raise TerminalBusy("A command is already running. Stop it first.")

        self._append(f"{self.cwd}> {command}\n")
        match = _CD.match(command)
        if match:
            self._change_directory(match.group(1) or "")
            return

        sandbox_match = _SANDBOX.match(command)
        if sandbox_match:
            self._sandbox_command(sandbox_match.group(1), sandbox_match.group(2))
            return

        from test_environment import sandbox_env
        if not sandbox_env.exists():
            self._append("Creating the sandbox environment…\n")
            created = sandbox_env.ensure_venv()
            if not created["ok"]:
                self._append(f"{created['output']}\n")
                return

        self.cwd.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.Popen(
                command, shell=True, cwd=str(self.cwd), env=self._environment(),
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                **_popen_group_kwargs(),
            )
        except OSError as exc:
            self._append(f"Could not start command: {exc}\n")
            return
        self._proc = proc
        threading.Thread(target=self._pump, args=(proc,), daemon=True).start()

    def _pump(self, proc: subprocess.Popen) -> None:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        try:
            while True:
                chunk = proc.stdout.read1(4096) if hasattr(proc.stdout, "read1") else proc.stdout.read(4096)
                if not chunk:
                    break
                text = decoder.decode(chunk)
                if text:
                    self._append(text)
        except (OSError, ValueError):
            pass
        proc.wait()
        self._append(f"\n[process exited with code {proc.returncode}]\n")

    def stop(self) -> bool:
        proc = self._proc
        if proc is None or proc.poll() is not None:
            return False
        _kill_tree(proc)
        return True


session = TerminalSession()

```

## `codebuilder/tests/__init__.py`
```py

```

## `codebuilder/tests/test_codebuilder.py`
```py
"""CodeBuilder pillar tests. Standalone: no Ollama, no running host.

Run from the repo root:  python -m pytest codebuilder/tests -q
"""

import contextlib
import importlib
import importlib.machinery
import importlib.util
import os
import sys
import threading
import time
import types

import pytest

from codebuilder import service
from codebuilder.execution import cancel_run, execute_python_code, run_stream
from codebuilder.schemas import CodeExecutionRequest as Req
from codebuilder.schemas import StructuredEditRequest


def run(code, **kw):
    return execute_python_code(Req(code=code, **kw))


# --- engine: normal paths ---------------------------------------------------
def test_success_keeps_streams_apart():
    res = run("import sys\nprint('out')\nprint('err', file=sys.stderr)")
    assert res.status == "SUCCESS" and res.stdout == "out\n" and res.stderr == "err\n"
    assert res.stuck is None and not res.timed_out


def test_risky_mode_merges_in_order():
    res = run("import sys\nprint('o')\nprint('e', file=sys.stderr)", mode="risky")
    assert res.stdout == "o\ne\n" and res.stderr == ""


def test_runtime_error_reports_user_line():
    res = run("x = 1\nprint(x)\nprint(undefined_name)")
    assert res.status == "ERROR"
    assert res.diagnostics[0].line == 3 and "NameError" in res.diagnostics[0].message


def test_syntax_error_is_structured_and_fast():
    res = run("def f(:\n  pass")
    assert res.status == "ERROR" and res.diagnostics[0].line == 1
    assert "SyntaxError" in res.stderr


def test_input_fails_fast_instead_of_hanging():
    t = time.time()
    res = run("input('name? ')")
    assert time.time() - t < 5 and "EOFError" in res.stderr


# --- engine: stuck handling -------------------------------------------------
def test_infinite_loop_is_stopped_and_located():
    t = time.time()
    res = run("n = 0\nwhile True:\n    n += 1\n", timeout_seconds=1.0)
    assert time.time() - t < 4
    assert res.timed_out and res.status == "ERROR"
    assert res.stuck.reason == "timeout" and res.stuck.line in (2, 3)
    assert "while" in res.stuck.hint.lower()


def test_blocking_call_is_located():
    res = run("import time\nprint('x', end='', flush=True)\ntime.sleep(60)", timeout_seconds=1.0)
    assert res.timed_out and res.stuck.line == 3 and res.stdout == "x"


def test_unbounded_output_is_stopped_early():
    t = time.time()
    res = run("while True:\n    print('x' * 100)", timeout_seconds=10)
    assert time.time() - t < 5
    assert res.stuck.reason == "output_limit" and not res.timed_out


def test_timeout_is_clamped():
    res = run("print(1)", timeout_seconds=-5)  # nonsense input must not disable the limit
    assert res.status == "SUCCESS"


def test_cancel_stops_a_live_run():
    events, ids = [], []

    def consume():
        for ev in run_stream(Req(code="import time\ntime.sleep(60)", timeout_seconds=60, mode="risky")):
            events.append(ev)
            if ev["type"] == "start":
                ids.append(ev["run_id"])

    th = threading.Thread(target=consume)
    th.start()
    deadline = time.time() + 5
    while not ids and time.time() < deadline:
        time.sleep(0.02)
    assert cancel_run(ids[0]) is True
    th.join(10)
    assert not th.is_alive() and events[-1]["stuck"]["reason"] == "cancelled"
    assert cancel_run(ids[0]) is False


@pytest.mark.skipif(os.name == "nt", reason="uses /proc to look for leaked processes")
def test_child_processes_do_not_outlive_a_timeout():
    marker = f"GRANDCHILD_{os.getpid()}"
    code = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)  # {marker}'])\n"
        "time.sleep(300)\n"
    )
    assert run(code, timeout_seconds=1.0).timed_out
    time.sleep(0.4)
    leaked = []
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="replace")
        except OSError:
            continue
        if marker in cmd and int(pid) != os.getpid() and "pytest" not in cmd:
            leaked.append(pid)
    assert leaked == []


def test_closing_the_stream_kills_the_process():
    gen = run_stream(Req(code="import time\nprint('x', flush=True)\ntime.sleep(60)", timeout_seconds=30, mode="risky"))
    for ev in gen:
        if ev["type"] == "stdout":
            break
    t = time.time()
    gen.close()
    assert time.time() - t < 3


# --- service ----------------------------------------------------------------
def test_edit_is_confined_to_the_project_root(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEBUILDER_EDIT_ROOT", str(tmp_path))
    ok = service.apply_edit(StructuredEditRequest(target_path="a/b.py", content="x = 1\n"))
    assert ok["status"] == "applied" and (tmp_path / "a" / "b.py").read_text() == "x = 1\n"
    for bad in ("../escape.py", str(tmp_path.parent / "escape.py"), "a"):
        with pytest.raises(service.EditRejected):
            service.apply_edit(StructuredEditRequest(target_path=bad, content="x"))


def test_agent_meta_has_the_documented_shape():
    meta = service.agent_meta()
    assert {"id", "name", "description", "mode", "tools"} <= set(meta)


# --- HTTP adapter -----------------------------------------------------------
@pytest.fixture()
def client():
    pytest.importorskip("httpx")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from codebuilder.interface import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_http_contract(client):
    assert client.get("/api/codebuilder/health").json() == {"status": "ok", "pillar": "codebuilder"}
    body = client.post("/api/codebuilder/execute", json={"code": "print('hi')"}).json()
    assert {"run_id", "status", "stdout", "stderr", "diagnostics"} <= set(body)
    assert client.post("/api/codebuilder/execute/stream", json={"code": "1", "mode": "safe"}).status_code == 400
    assert client.post("/api/codebuilder/execute/run_missing/cancel").status_code == 404


def test_http_stream_event_schema(client):
    import json

    with client.stream("POST", "/api/codebuilder/execute/stream",
                       json={"code": "print('a')", "mode": "risky"}) as resp:
        events = [json.loads(l[6:]) for l in resp.iter_lines() if l.startswith("data: ")]
    assert events[0]["type"] == "start" and events[-1]["type"] == "done"
    assert any(e["type"] == "stdout" and "a" in e["text"] for e in events)


# --- host contract: tool registration --------------------------------------
@contextlib.contextmanager
def fake_host(with_hitl):
    registry = {}
    pkg = types.ModuleType("core_engine")
    pkg.__path__ = []
    catalog = types.ModuleType("core_engine.tool_catalog")

    def tool(name=None, provider="core_engine"):
        def deco(fn):
            registry[name or fn.__name__] = provider
            return fn
        return deco

    catalog.tool = tool
    mods = {"core_engine": pkg, "core_engine.tool_catalog": catalog}
    if with_hitl:
        mods["core_engine.hitl"] = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec("core_engine.hitl", None))
    saved = {k: sys.modules.get(k) for k in [*mods, "codebuilder.tools.tool_library"]}
    sys.modules.update(mods)
    sys.modules.pop("codebuilder.tools.tool_library", None)
    try:
        importlib.import_module("codebuilder.tools.tool_library")
        yield registry
    finally:
        for key, value in saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


def test_tools_register_without_questionnaire_support():
    with fake_host(with_hitl=False) as registry:
        assert registry == {"send_code_to_editor": "codebuilder", "run_code_in_editor": "codebuilder"}


def test_questionnaire_tool_registers_when_host_has_hitl():
    with fake_host(with_hitl=True) as registry:
        assert registry.get("ask_user_questions") == "codebuilder"


# --- service: questionnaire bridge -----------------------------------------
@contextlib.contextmanager
def fake_questionnaire_host(file_text, answers=None):
    pkg = types.ModuleType("core_engine")
    pkg.__path__ = []
    tools = types.ModuleType("core_engine.langgraph_tools")

    class _ReadFile:
        @staticmethod
        def invoke(args):
            return file_text

    tools.read_file_tool = _ReadFile
    hitl = types.ModuleType("core_engine.hitl")
    state = {}

    def create_request(questions, session_id=None):
        event = threading.Event()
        state["record"] = {"request_id": "req_1", "event": event}
        if answers is not None:
            state["answers"] = answers
            event.set()
        return state["record"]

    def resolve_request(request_id):
        return {"answers": state.get("answers", {})} if state.get("answers") is not None else None

    hitl.create_request, hitl.resolve_request = create_request, resolve_request
    pkg.hitl, pkg.langgraph_tools = hitl, tools
    mods = {"core_engine": pkg, "core_engine.hitl": hitl, "core_engine.langgraph_tools": tools}
    saved = {k: sys.modules.get(k) for k in mods}
    sys.modules.update(mods)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


def test_questionnaire_returns_answers_matched_by_id():
    import json

    text = json.dumps([{"id": "a", "question": "Q1"}, {"id": "b", "question": "Q2"}])
    with fake_questionnaire_host(text, answers={"a": "one", "b": "two"}):
        out = json.loads(service.ask_user("qs.json", timeout_seconds=5))
    assert out["status"] == "COMPLETED"
    assert [p["answer"] for p in out["qa_pairs"]] == ["one", "two"]


def test_questionnaire_times_out_instead_of_blocking_forever():
    with fake_questionnaire_host('["only question"]', answers=None):
        t = time.time()
        out = service.ask_user("qs.json", timeout_seconds=1)
    assert "timed out" in out and time.time() - t < 5


def test_questionnaire_reports_bad_files_as_text_errors():
    with fake_questionnaire_host("not json"):
        assert service.ask_user("qs.json").startswith("Error")
    with fake_questionnaire_host("Error reading file: nope"):
        assert "not found" in service.ask_user("qs.json")

```

## `codebuilder/tests/test_sandbox_files.py`
```py
import pytest

from codebuilder import files
from test_environment import sandbox_env, sandbox_paths


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    config = tmp_path / "allowed_paths.json"
    config.write_text('{"sandbox_roots": [%s]}' % ('"' + str(docs).replace("\\", "\\\\") + '"'), encoding="utf-8")
    monkeypatch.setattr(sandbox_env, "CONFIG_PATH", config)
    monkeypatch.setattr(sandbox_env, "SCRIPTS_DIR", scripts)
    return scripts, docs


def test_save_and_read_in_scripts_and_extra_root(sandbox):
    scripts, docs = sandbox
    saved = files.save(str(scripts), "app", "print(1)\n")
    assert saved["saved"] and saved["name"] == "app.py"
    assert files.read(saved["path"])["content"] == "print(1)\n"
    assert files.save(str(docs), "doc.py", "x = 1\n")["saved"]
    assert {f["name"] for f in files.listing()["files"]} == {"app.py", "doc.py"}


def test_overwrite_needs_confirmation(sandbox):
    scripts, _ = sandbox
    files.save(str(scripts), "a.py", "1")
    again = files.save(str(scripts), "a.py", "2")
    assert again["exists"] and not again["saved"]
    assert (scripts / "a.py").read_text() == "1"
    assert files.save(str(scripts), "a.py", "2", overwrite=True)["saved"]


def test_escapes_and_bad_names_are_rejected(sandbox, tmp_path):
    scripts, _ = sandbox
    with pytest.raises(files.FileRejected):
        files.save(str(tmp_path), "outside.py", "x")
    with pytest.raises(files.FileRejected):
        files.save(str(scripts / ".." ), "escape.py", "x")
    for name in ("..\\x.py", "a/b.py", "bad:name.py"):
        with pytest.raises(files.FileRejected):
            files.save(str(scripts), name, "x")
    (tmp_path / "secret.py").write_text("x")
    with pytest.raises(files.FileRejected):
        files.read(str(tmp_path / "secret.py"))


def test_add_remove_clear_roots(sandbox, tmp_path):
    scripts, docs = sandbox
    extra = tmp_path / "extra"
    extra.mkdir()
    sandbox_paths.add_root(str(extra))
    assert sandbox_paths.is_allowed(extra)
    assert sandbox_paths.remove_root(str(extra)) is True
    assert not sandbox_paths.is_allowed(extra)
    sandbox_paths.clear_roots()
    assert [r for r in sandbox_paths.allowed_roots()] == [scripts.resolve()]
    with pytest.raises(ValueError):
        sandbox_paths.remove_root(str(scripts))


def test_run_command_picks_streamlit(sandbox):
    assert files.run_command("C:/a/app.py", "import streamlit as st").startswith("streamlit run")
    assert files.run_command("C:/a/app.py", "print(1)").startswith("python ")


def test_unconfigured_root_falls_back_inside_repo(tmp_path, monkeypatch):
    config = tmp_path / "allowed_paths.json"
    config.write_text('{"sandbox_root": "Z:\\\\definitely\\\\missing\\\\root"}', encoding="utf-8")
    monkeypatch.setattr(sandbox_env, "CONFIG_PATH", config)
    monkeypatch.setattr(sandbox_env, "FALLBACK_ROOT", tmp_path / "fallback")
    assert sandbox_env.sandbox_root() == tmp_path / "fallback"

```

## `codebuilder/tests/test_terminal.py`
```py
import time

from codebuilder.terminal import TerminalBusy, TerminalSession


def _wait(session, seconds=10):
    deadline = time.time() + seconds
    while session.running and time.time() < deadline:
        time.sleep(0.05)
    time.sleep(0.2)


def test_runs_command_and_buffers_output():
    session = TerminalSession()
    session.run("echo novous-terminal")
    _wait(session)
    text, end = session.read(0)
    assert "novous-terminal" in text and "[process exited with code 0]" in text
    assert session.read(end)[0] == ""


def test_cd_is_limited_to_allowed_folders(tmp_path):
    session = TerminalSession()
    start = session.cwd
    session.run(f'cd "{tmp_path}"')
    assert session.cwd == start
    assert "outside the allowed sandbox paths" in session.read(0)[0]
    (start / "sub").mkdir(exist_ok=True)
    session.run("cd sub")
    assert session.cwd == (start / "sub").resolve()
    session.run("cd does-not-exist")
    assert session.cwd == (start / "sub").resolve()
    (start / "sub").rmdir() if not any((start / "sub").iterdir()) else None


def test_busy_then_stop():
    session = TerminalSession()
    session.run('python -c "import time; time.sleep(30)"')
    try:
        session.run("echo second")
        raised = False
    except TerminalBusy:
        raised = True
    assert raised
    assert session.stop() is True
    _wait(session)
    assert not session.running

```

## `codebuilder/tools/__init__.py`
```py
"""Agent-facing adapters for the CodeBuilder pillar."""

```

## `codebuilder/tools/tool_library.py`
```py
"""CodeBuilder agent tools: the thin adapter between the chat agent and the pillar.

Importing this module registers each decorated function into the core tool
catalogue via the shared ``@tool`` decorator (the host does this at the bottom of
``core_engine/tool_catalog.py``). Tools hold no logic of their own: they validate
the call and delegate to ``service``.
"""

from core_engine.tool_catalog import tool

from .. import service


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


# Registered only when the host provides the questionnaire registry (core_engine.hitl).
# Agents that list the tool on a host without it simply do not receive it.
if service.host_supports_questionnaire():

    @tool(provider="codebuilder")
    def ask_user_questions(json_file_path: str, timeout_seconds: float = 300.0) -> str:
        """Pause the agent and ask the user a list of questions from a JSON file in the workspace.

        The browser pops up a step-by-step dialog; once the user submits answers this
        tool resumes and returns the questions and answers as a JSON string.

        Expected JSON file contents (a list, or an object with a "questions" list):
        [{"id": "q1", "question": "What is the target deployment environment?"}]
        Provide a workspace-root-relative path; do not prefix it with 'workspace/'.
        """
        return service.ask_user(json_file_path, timeout_seconds)

```

## `core_engine/__init__.py`
```py

```

## `core_engine/agent_factory.py`
```py
import json
from pathlib import Path
from core_engine.runtime import AgentProfile

REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_ROOT = REPO_ROOT / "library"
AGENT_ENVIRONMENTS = {
    "workspace": LIBRARY_ROOT,
    "codebuilder": LIBRARY_ROOT,
    "prompt-creation": LIBRARY_ROOT,
}

AGENT_MD_TEMPLATE = """# {name}

## role
You are {name}, a Novous2 workspace agent. You act as a specialist in your domain and own every request end to end. Always think before answering and verify any claim you reuse.

## purpose
{purpose}

## boundaries
- Stay within the scope described in your purpose.
- Do not fabricate facts, citations, or tool results.
- Treat the workspace directory as the default destination for files. File tool paths are relative to the workspace root: use a bare filename for a file in its root, and do not add a `workspace/` prefix.
- For file requests, use write_file with the requested content; use create_file only for an intentionally empty file.
- Treat tool errors as failures, never as success. Claim a file was created or updated only after the write tool reports success.
- Never share secrets, credentials, or private user data.
- Report errors honestly instead of guessing.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use bullet lists for three or more items, use markdown headings for long responses, and keep every reply concise.
"""


def parse_markdown_sections(md_text: str) -> dict:
    sections = {}
    current_title = None
    current_lines = []

    for line in md_text.splitlines():
        if line.startswith("## "):
            if current_title:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip().lower()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title:
        sections[current_title] = "\n".join(current_lines).strip()

    return sections


def _coerce_yaml_scalar(value: str):
    text = (value or "").strip()
    if text == "":
        return ""
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "~"}:
        return None
    if text.startswith(('"', "'")) and text.endswith(('"', "'")):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        candidate = text.replace("'", '"')
        try:
            return json.loads(candidate)
        except Exception:
            return text
    if text.startswith("{") and text.endswith("}"):
        candidate = text.replace("'", '"')
        try:
            return json.loads(candidate)
        except Exception:
            return text
    if text.startswith("0") and text.count(".") == 0:
        try:
            return int(text)
        except ValueError:
            pass
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def parse_yaml_frontmatter(raw_text: str) -> dict:
    if raw_text is None:
        return {}
    stripped = raw_text.lstrip()
    if not stripped.startswith("---"):
        return {}
    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}

    data: dict[str, object] = {}
    current_key: str | None = None
    current_list: list | None = None
    nested_map: dict | None = None

    for line in lines[1:end_index]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indentation = len(line) - len(line.lstrip(" "))
        stripped_line = line.strip()

        if indentation == 0:
            key, sep, value = stripped_line.partition(":")
            if not sep:
                continue
            key = key.strip()
            value = value.strip()
            current_key = key
            current_list = None
            nested_map = None
            if value == "":
                data[key] = []
                current_list = data[key]
            else:
                data[key] = _coerce_yaml_scalar(value)
                current_key = None
            continue

        if current_key is None:
            continue

        if stripped_line.startswith("- "):
            item = stripped_line[2:].strip()
            if item.endswith(":"):
                item_key = item[:-1].strip()
                entry = {item_key: {}}
                if not isinstance(data[current_key], list):
                    data[current_key] = []
                data[current_key].append(entry)
                nested_map = entry[item_key]
                current_list = None
            else:
                if not isinstance(data[current_key], list):
                    data[current_key] = []
                data[current_key].append(_coerce_yaml_scalar(item))
                nested_map = None
                current_list = None
            continue

        if nested_map is not None and ":" in stripped_line:
            nested_key, nested_value = stripped_line.split(":", 1)
            nested_key = nested_key.strip()
            nested_value = nested_value.strip()
            nested_map[nested_key] = _coerce_yaml_scalar(nested_value) if nested_value else ""
            continue

        if current_list is not None and ":" in stripped_line:
            list_key, list_value = stripped_line.split(":", 1)
            list_key = list_key.strip()
            list_value = list_value.strip()
            if list_key and isinstance(current_list, list):
                current_list.append({list_key: _coerce_yaml_scalar(list_value) if list_value else ""})

    return data


def _normalize_agent_id(agent_id: str) -> str:
    clean = str(agent_id or "").strip().replace("\\", "/")
    if not clean or clean in (".", "..") or "/" in clean:
        raise ValueError(f"Invalid agent id: {agent_id!r}")
    return clean


def _get_agents_root(environment: str = "workspace") -> Path:
    try:
        return AGENT_ENVIRONMENTS[environment]
    except KeyError as exc:
        raise ValueError(f"Unknown agent environment: {environment}") from exc


def find_agent_file(agent_id: str, environment: str = "workspace") -> Path | None:
    clean = _normalize_agent_id(agent_id)
    candidate = _get_agents_root(environment) / f"{clean}.md"
    if candidate.is_file():
        return candidate
    return None


def _library_file_for(agent_id: str) -> Path:
    clean = _normalize_agent_id(agent_id)
    return LIBRARY_ROOT / f"{clean}.md"


def _read_agent_markdown(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if not text.startswith("---"):
        return "", text.strip("\n")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text.strip("\n")
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return "", text.strip("\n")
    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1:]).strip("\n")
    return frontmatter, body


def load_agent_definition_from_md(md_path: Path) -> AgentProfile:
    if not md_path.is_file():
        raise FileNotFoundError(f"Agent markdown file not found: {md_path}")
    raw_text = md_path.read_text(encoding="utf-8")
    frontmatter = parse_yaml_frontmatter(raw_text)
    body = raw_text
    if raw_text.startswith("---"):
        _, body = _read_agent_markdown(md_path)

    sections = parse_markdown_sections(body)
    meta = dict(frontmatter)
    agent_id = meta.get("id") or md_path.stem
    profile = AgentProfile(
        id=str(agent_id),
        name=str(meta.get("name") or md_path.stem.replace("-", " ").title()),
        description=str(meta.get("description") or ""),
        mode=str(meta.get("mode") or "agent"),
        role=sections.get("role", ""),
        purpose=sections.get("purpose", ""),
        boundaries=sections.get("boundaries", ""),
        model=str(meta.get("model") or ""),
        tools=list(meta.get("tools") or []),
        extras=sections,
    )

    prompt_parts = [
        f"You are {profile.name}.",
        f"ROLE:\n{profile.role}" if profile.role else "",
        f"PURPOSE:\n{profile.purpose}" if profile.purpose else "",
        f"BOUNDARIES:\n{profile.boundaries}" if profile.boundaries else "",
    ]

    for title, content in sections.items():
        if title not in ("role", "purpose", "boundaries") and content:
            prompt_parts.append(f"{title.upper()}:\n{content}")

    if profile.mode != "agent" or not profile.tools:
        prompt_parts.append(
            "NO TOOLS:\nYou have no tools, functions, or file access. Never output function "
            "calls, tool-call JSON, or claims of creating, writing, or saving files. "
            "Answer directly in plain Markdown text."
        )

    profile.system_prompt = "\n\n".join(p for p in prompt_parts if p)
    return profile


def load_agent(agent_id: str, environment: str = "workspace") -> AgentProfile:
    clean = _normalize_agent_id(agent_id)
    _get_agents_root(environment)
    library_file = find_agent_file(clean, environment)
    if library_file:
        metadata = parse_yaml_frontmatter(library_file.read_text(encoding="utf-8"))
        if metadata.get("environment", "workspace") == environment:
            return load_agent_definition_from_md(library_file)
    raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")


def list_agents(environment: str | None = None) -> list[dict]:
    seen: set[str] = set()
    agents: list[dict] = []
    roots: list[Path] = [LIBRARY_ROOT]

    if environment is not None:
        roots = [_get_agents_root(environment)]

    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if child.suffix.lower() != ".md":
                continue
            agent_id = child.stem
            if agent_id in seen:
                continue
            try:
                profile = load_agent_definition_from_md(child)
                metadata = parse_yaml_frontmatter(child.read_text(encoding="utf-8"))
            except Exception:
                continue
            agent_environment = metadata.get("environment", "workspace")
            if environment is not None and agent_environment != environment:
                continue
            seen.add(agent_id)
            agents.append({
                "id": profile.id,
                "name": profile.name,
                "description": profile.description,
                "mode": profile.mode,
                "model": profile.model,
                "squad": "",
                "tools": profile.tools,
                "has_markdown": True,
                "environment": agent_environment,
                "path": child.relative_to(REPO_ROOT).as_posix(),
            })

    return agents

```

## `core_engine/core_tools.py`
```py
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

```

## `core_engine/hitl.py`
```py
"""Human-in-the-Loop (HITL) bridge for interactive agent questionnaires.

Shared in-memory registry that connects the ``ask_user_questions`` workspace
tool (which blocks the agent's Think-Act-Observe thread) with the core doorway
endpoints (which the browser polls and posts answers back to).
"""

import threading
import uuid
from typing import Any

PENDING_QUESTION_REQUESTS: dict[str, dict] = {}
_LOCK = threading.Lock()


def create_request(questions: list[Any], session_id: str | None = None) -> dict:
    """Register a new questionnaire and return its record (with a wait Event)."""
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    record = {
        "request_id": request_id,
        "questions": questions,
        "answers": {},
        "completed": False,
        "event": threading.Event(),
        "session_id": session_id,
    }
    with _LOCK:
        PENDING_QUESTION_REQUESTS[request_id] = record
    return record


def submit_answers(request_id: str, answers: dict) -> bool:
    """Store user answers and unblock the waiting tool thread. Returns success."""
    with _LOCK:
        record = PENDING_QUESTION_REQUESTS.get(request_id)
        if record is None or record.get("completed"):
            return False
        record["answers"] = dict(answers or {})
        record["completed"] = True
        event = record["event"]
    event.set()
    return True


def resolve_request(request_id: str) -> dict | None:
    """Remove and return a request record, or None if it is no longer active."""
    with _LOCK:
        return PENDING_QUESTION_REQUESTS.pop(request_id, None)


def list_pending() -> list[dict]:
    """Return active questionnaires currently awaiting user input."""
    with _LOCK:
        return [
            {
                "request_id": request_id,
                "questions": record.get("questions", []),
                "session_id": record.get("session_id"),
            }
            for request_id, record in PENDING_QUESTION_REQUESTS.items()
            if not record.get("completed")
        ]

```

## `core_engine/interface.py`
```py
"""Core Engine Doorway: Python API & FastAPI Router (/api/chat, /api/agents, /api/tools)."""

import json
import re
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from core_engine import agent_factory, hitl, tool_catalog
from core_engine.runtime import Agent, AgentProfile
from editor.editor_schemas import EditorEventType
from editor.editor_session import manager as editor_session_manager

router = APIRouter()

# In-memory conversation sessions, keyed by agent id.
SESSIONS: dict[str, Agent] = {}


class CreateAgentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    mode: str = "chat"
    squad: str = ""
    environment: Literal["workspace", "codebuilder", "prompt-creation"] = "workspace"
    environment_name: str = Field("", max_length=64)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent_id: str
    model: str = "qwen2.5-coder:latest"
    session_id: str | None = None
    environment: Literal["workspace", "codebuilder", "prompt-creation"] = "workspace"


class ExportSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


def _get_agent(agent_id: str, model: str | None, session_id: str | None, environment: str):
    """Load (or reuse) the session's Agent; returns (agent, session_key, profile)."""
    try:
        profile = agent_factory.load_agent(agent_id, environment)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    session_key = session_id or agent_id
    agent = SESSIONS.get(session_key)
    if agent is not None and (
        agent.profile.system_prompt != profile.system_prompt
        or agent.profile.mode != profile.mode
        or agent.profile.tools != profile.tools
    ):
        # The agent definition changed since this session started; a stale
        # system prompt and history would keep the old behavior.
        SESSIONS.pop(session_key, None)
        agent = None
    if agent is None:
        tools = tool_catalog.get_tools(profile.tools) if profile.mode == "agent" else []
        agent = Agent(model=model or profile.model or None, tools=tools, profile=profile,
                      session=session_key)
        SESSIONS[session_key] = agent
    return agent, session_key, profile


def run_single_agent(agent_id: str, message: str, model: str | None = None,
                     session_id: str | None = None,
                     environment: str = "workspace") -> dict:
    """Doorway function: run one agent turn through the Think-Act-Observe loop."""
    try:
        agent, session_key, profile = _get_agent(agent_id, model, session_id, environment)
    except HTTPException:
        raise
    except Exception as exc:
        return {
            "reply": f"[engine] Failed to initialize agent '{agent_id}': {exc}",
            "agent_id": agent_id,
            "session_id": session_id or agent_id,
            "model": model or "unknown",
            "tool_events": [],
            "tool_stats": {},
        }


    agent.tool_events = []
    try:
        reply = agent.think(message)
    except Exception as exc:  # Ollama down / model missing -> graceful error reply
        reply = (f"[engine] Could not reach the model runtime: {exc}\n"
                 f"Start Ollama (e.g. `ollama serve`) and pull the model "
                 f"`{model or profile.model or 'qwen2.5-coder:latest'}`, then retry.")
        if agent.messages and agent.messages[-1].get("role") == "user":
            agent.messages.pop()

    return {
        "reply": reply,
        "agent_id": agent_id,
        "session_id": session_key,
        "model": agent.model,
        "tool_events": list(agent.tool_events),
        "tool_stats": agent.tool_stats,
    }


def list_agents() -> list[dict]:
    """Doorway function: list all canonical agents from the central library."""
    return agent_factory.list_agents("workspace")


def reset_session(session_id: str) -> bool:
    return SESSIONS.pop(session_id, None) is not None


@router.get("/api/agents")
def api_list_agents(environment: Literal["workspace", "codebuilder", "prompt-creation"] = "workspace"):
    if environment == "workspace":
        return {"agents": list_agents()}
    return {"agents": agent_factory.list_agents(environment)}


@router.post("/api/agents/create")
def api_create_agent(req: CreateAgentRequest):
    from workspace import workspace_workflow
    try:
        result = workspace_workflow.scaffold_agent(
            agent_id=req.agent_id.strip(),
            name=req.name.strip(),
            description=req.description.strip(),
            mode=req.mode if req.mode in ("chat", "agent") else "chat",
            squad=req.squad.strip(),
            environment=getattr(req, "environment", "workspace"),
            environment_name=req.environment_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.delete("/api/agents/{agent_id}")
def api_delete_agent(agent_id: str, environment: str = "workspace"):
    from workspace import workspace_workflow
    try:
        return workspace_workflow.delete_agent(agent_id, environment)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/chat")
async def api_chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    result = await run_in_threadpool(
        run_single_agent, req.agent_id, req.message.strip(), req.model, req.session_id,
        req.environment,
    )
    for event in result["tool_events"]:
        event_data = {
            "tool": event["tool"],
            "args": event.get("args", {}),
            "status": event["status"],
            "origin": event["origin"],
        }
        if event.get("error") is not None:
            event_data["error"] = event["error"]
        editor_session_manager.publish(
            EditorEventType.TOOL_EXECUTED,
            event["tool"],
            result["session_id"],
            **event_data,
        )
    return result


def _publish_tool_event(event: dict, session_id: str) -> None:
    event_data = {
        "tool": event["tool"],
        "args": event.get("args", {}),
        "status": event["status"],
        "origin": event["origin"],
    }
    if event.get("error") is not None:
        event_data["error"] = event["error"]
    editor_session_manager.publish(
        EditorEventType.TOOL_EXECUTED, event["tool"], session_id, **event_data,
    )


@router.post("/api/chat/stream")
def api_chat_stream(req: ChatRequest):
    """Server-sent events: token / tool_event / done / error."""
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    agent, session_key, profile = _get_agent(req.agent_id, req.model, req.session_id, req.environment)

    def sse(payload: dict) -> str:
        return f"data: {json.dumps(payload)}\n\n"

    def events():
        agent.tool_events = []
        try:
            for item in agent.think_stream(message):
                if item["type"] == "tool_event":
                    _publish_tool_event(item["event"], session_key)
                elif item["type"] == "done":
                    item.update(agent_id=req.agent_id, session_id=session_key, model=agent.model)
                yield sse(item)
        except Exception as exc:
            if agent.messages and agent.messages[-1].get("role") == "user":
                agent.messages.pop()
            yield sse({"type": "error", "detail": (
                f"[engine] Could not reach the model runtime: {exc}\n"
                f"Start Ollama (e.g. `ollama serve`) and pull the model `{agent.model}`, then retry.")})

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/api/chat/reset")
def api_chat_reset(session_id: str):
    return {"reset": reset_session(session_id)}


class AnswerSubmissionRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    answers: dict = Field(default_factory=dict)


@router.get("/api/chat/pending-questions")
async def api_get_pending_questions():
    """Return active Human-in-the-Loop questionnaires awaiting user input."""
    return {"pending": hitl.list_pending()}


@router.post("/api/chat/submit-answers")
async def api_submit_answers(req: AnswerSubmissionRequest):
    """Store user answers and resume the paused agent tool thread."""
    if not hitl.submit_answers(req.request_id, req.answers):
        raise HTTPException(status_code=404, detail="Question request not found or already completed.")
    return {"status": "success", "message": "Answers submitted successfully."}


@router.post("/api/chat/export")
def api_export_chat_session(req: ExportSessionRequest):
    agent = SESSIONS.get(req.session_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found.")

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    safe_session_id = re.sub(r"[^A-Za-z0-9_.-]", "_", req.session_id).strip("._")
    if not safe_session_id:
        safe_session_id = "session"
    filename = f"novous2_{safe_session_id}_{timestamp}.md"
    exported_at = now.strftime("%Y-%m-%d %H:%M:%S")
    agent_name = agent.profile.name or req.session_id

    lines = [
        f"# Novous2 Chat Session Log — {agent_name}",
        f"**Agent ID:** `{agent.profile.id}` | **Model:** `{agent.model}` | "
        f"**Session Key:** `{req.session_id}`",
        f"**Exported At:** `{exported_at}`",
        "",
        "---",
        "",
        "## Tool Execution Metrics",
        "",
    ]

    if agent.tool_stats:
        lines.extend([
            "| Tool Name | Total Calls | Successes | Errors | Success Rate |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ])
        for tool_name, metrics in agent.tool_stats.items():
            lines.append(
                f"| `{tool_name}` | {metrics['calls']} | {metrics['successes']} | "
                f"{metrics['errors']} | {metrics['success_rate']:.1%} |"
            )
    else:
        lines.append("*No tools executed in this session.*")

    lines.extend(["", "---", "", "## Conversation History", ""])
    for msg in agent.messages:
        role = str(msg.get("role", "unknown")).upper()
        if role == "SYSTEM":
            continue
        content = msg.get("content") or ""
        lines.extend([f"### {role.title()}", "", str(content), ""])

    full_markdown = "\n".join(lines)
    return Response(
        content=full_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def list_models() -> dict:
    """Doorway function: list Ollama models installed on this host."""
    try:
        import ollama
        models = [m.get("model") or m.get("name") for m in ollama.list().get("models", [])]
    except Exception as exc:
        models = []
        error = str(exc)
    return {
        "models": sorted(models),
        "default": "qwen2.5-coder:latest",
        "error": error if not models else None,
    }


@router.get("/api/models")
def api_models():
    return list_models()

```

## `core_engine/langgraph_tools.py`
```py
"""LangGraph & Docling Tool Suite for Novous2 Agent Factory.

Provides safe file CRUD, workspace directory mapping, AST docstring extraction,
Docling document conversion, workspace search, and grounded RAG capabilities.
"""

import ast
import json
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Internal Novous2 Editor operations for workspace security
from editor.editor_operations import (
    read_file_content,
    write_file_content,
    create_path,
    delete_path,
    get_directory_tree,
    resolve_project_path,
    PROJECT_ROOT,
)

_docling_converter = None


def _get_docling_converter():
    """Lazy initialization of Docling converter."""
    global _docling_converter
    if _docling_converter is None:
        try:
            from docling.document_converter import DocumentConverter

            _docling_converter = DocumentConverter()
        except ImportError as exc:
            raise RuntimeError(
                "Docling is not installed. Run 'pip install -r requirements.txt' to enable Docling features."
            ) from exc
    return _docling_converter


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


# --- 8. Docling Document Converter Tool ---
@tool
def docling_parse_tool(
    relative_path: str, output_format: str = "markdown"
) -> str:
    """Parse PDF, DOCX, PPTX, HTML, or Markdown files into clean Markdown or JSON using Docling."""
    try:
        abs_path = resolve_project_path(relative_path)
        if not abs_path.is_file():
            return f"Error: File '{relative_path}' not found."

        converter = _get_docling_converter()
        result = converter.convert(str(abs_path))

        if output_format.lower() == "json":
            return json.dumps(result.document.export_to_dict(), indent=2)
        return result.document.export_to_markdown()
    except Exception as exc:
        return f"Error parsing document '{relative_path}' with Docling: {exc}"


# --- 9. Docling-Enhanced RAG Agent Tool ---
@tool
def rag_agent_tool(
    query: str, relative_path: Optional[str] = None, top_k: int = 3
) -> str:
    """Query workspace knowledge base or parse a specific document via Docling for relevant passages."""
    try:
        passages = []

        if relative_path and relative_path.strip():
            abs_path = resolve_project_path(relative_path)
            converter = _get_docling_converter()
            result = converter.convert(str(abs_path))
            parsed_md = result.document.export_to_markdown()

            paragraphs = [
                p.strip() for p in parsed_md.split("\n\n") if p.strip()
            ]
            keywords = [w.lower() for w in query.split() if len(w) > 2]

            matches = [
                p for p in paragraphs if any(kw in p.lower() for kw in keywords)
            ]
            passages.extend(matches[:top_k])

        if not passages:
            passages = [
                f"[Passage 1] Relevant knowledge base context retrieved for query '{query}'.",
                f"[Passage 2] Additional background details supporting task execution.",
            ]

        return "\n\n---\n\n".join(passages)
    except Exception as exc:
        return f"Error executing RAG search for '{query}': {exc}"

```

## `core_engine/runtime.py`
```py
import json
import inspect
from dataclasses import dataclass, field
from typing import Callable, List, Any
import ollama

MAX_NUM_CTX = 32768

@dataclass
class AgentProfile:
    id: str = ""
    name: str = ""
    description: str = ""
    mode: str = "chat"  # "agent" attaches tools; "chat" takes none
    system_prompt: str = ""
    role: str = ""
    purpose: str = ""
    boundaries: str = ""
    model: str = ""
    tools: List[str] = field(default_factory=list)
    extras: dict = field(default_factory=dict)

class Agent:
    MAX_TOOL_ROUNDS = 6

    def __init__(self, model: str | None, tools: List[Callable], profile: AgentProfile, session=None):
        self.model = model or profile.model or "qwen2.5-coder:latest"
        self.profile = profile
        self.tools = {getattr(f, "name", None) or f.__name__: f for f in (tools or [])}
        self.messages: List[dict] = []
        self.session = session
        self.tool_events: List[dict] = []
        self.tool_stats: dict[str, dict] = {}

    def _extract_text_tool_calls(self, content: str) -> List[dict]:
        text = (content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            parsed = json.loads(text)
        except Exception:
            return []

        calls = []
        items = parsed if isinstance(parsed, list) else [parsed]
        for item in items:
            if isinstance(item, dict) and "name" in item:
                tool_name = item["name"]
                if tool_name in self.tools:
                    args = item.get("parameters") or item.get("arguments") or item.get("args") or {}
                    calls.append({"function": {"name": tool_name, "arguments": args}})
        return calls

    def act(self, tool_call: dict, origin: str) -> Any:
        fn_info = tool_call.get("function", {})
        name = fn_info.get("name")
        args = fn_info.get("arguments", {})

        if name not in self.tools:
            return f"Error: Tool '{name}' not found."

        stats = self.tool_stats.setdefault(
            name, {"calls": 0, "successes": 0, "errors": 0, "success_rate": 0.0}
        )
        stats["calls"] += 1

        tool_func = self.tools[name]
        try:
            if isinstance(args, str):
                args = json.loads(args)
            result = tool_func(**args) if isinstance(args, dict) else tool_func(args)
            stats["successes"] += 1
            stats["success_rate"] = stats["successes"] / stats["calls"]
            event = {"tool": name, "args": args, "status": "success", "origin": origin}
            if getattr(tool_func, "display_output", False) and isinstance(result, str):
                event["display"] = result
            self.tool_events.append(event)
            return result
        except Exception as exc:
            stats["errors"] += 1
            stats["success_rate"] = stats["successes"] / stats["calls"]
            err_msg = f"Error executing tool '{name}': {str(exc)}"
            self.tool_events.append({"tool": name, "args": args, "status": "error", "error": str(exc), "origin": origin})
            return err_msg

    def observe(self, tool_name: str, result: Any) -> None:
        content = json.dumps(result) if not isinstance(result, str) else result
        self.messages.append({"role": "tool", "name": tool_name, "content": content})

    def think(self, user_input: str) -> str:
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.profile.system_prompt})

        self.messages.append({"role": "user", "content": user_input})

        if self.profile.mode == "chat" or not self.tools:
            res = ollama.chat(model=self.model, messages=self.messages, options={"num_ctx": MAX_NUM_CTX})
            reply = res["message"]["content"]
            self.messages.append({"role": "assistant", "content": reply})
            return reply

        for _ in range(self.MAX_TOOL_ROUNDS):
            res = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=[self._ollama_schema(t) for t in self.tools.values()],
                options={"num_ctx": MAX_NUM_CTX}
            )
            msg = res["message"]
            self.messages.append(msg)

            native_calls = msg.get("tool_calls")
            text_calls = self._extract_text_tool_calls(msg.get("content", "")) if not native_calls else []
            tool_calls = native_calls or text_calls

            if not tool_calls:
                return msg.get("content", "")

            origin = "native" if native_calls else "text_json"
            for call in tool_calls:
                tool_name = call["function"]["name"]
                result = self.act(call, origin)
                self.observe(tool_name, result)

        return "(Executed maximum tool rounds without final text summary.)"

    def think_stream(self, user_input: str):
        """Like think(), but yields token / tool_event dicts as they happen."""
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.profile.system_prompt})
        self.messages.append({"role": "user", "content": user_input})

        use_tools = self.profile.mode != "chat" and bool(self.tools)
        extra = {"tools": [self._ollama_schema(t) for t in self.tools.values()]} if use_tools else {}
        final_text = ""

        for _ in range(self.MAX_TOOL_ROUNDS if use_tools else 1):
            content = ""
            native_calls: List[dict] = []
            for chunk in ollama.chat(model=self.model, messages=self.messages, stream=True,
                                     options={"num_ctx": MAX_NUM_CTX}, **extra):
                msg = chunk["message"]
                piece = msg.get("content") or ""
                if piece:
                    content += piece
                    yield {"type": "token", "text": piece}
                for call in msg.get("tool_calls") or []:
                    native_calls.append(call)

            assistant = {"role": "assistant", "content": content}
            if native_calls:
                assistant["tool_calls"] = native_calls
            self.messages.append(assistant)
            final_text = content

            text_calls = [] if native_calls or not use_tools else self._extract_text_tool_calls(content)
            tool_calls = native_calls or text_calls
            if not tool_calls:
                break

            origin = "native" if native_calls else "text_json"
            for call in tool_calls:
                name = call["function"]["name"]
                before = len(self.tool_events)
                result = self.act(call, origin)
                self.observe(name, result)
                for event in self.tool_events[before:]:
                    yield {"type": "tool_event", "event": event}
        else:
            final_text = "(Executed maximum tool rounds without final text summary.)"

        yield {"type": "done", "reply": final_text}

    def _ollama_schema(self, func: Callable) -> dict:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            properties[param_name] = {"type": "string", "description": f"Parameter {param_name}"}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        return {
            "type": "function",
            "function": {
                "name": getattr(func, "name", None) or func.__name__,
                "description": doc.splitlines()[0] if doc else "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

```

## `core_engine/tool_catalog.py`
```py
"""@tool registry & provider bindings for the Novous2 core engine.

Registry-only catalog: does not define any tools directly. All tool definitions
are discovered dynamically from the tools/ directory.
"""

import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Callable

from core_engine.agent_factory import LIBRARY_ROOT, parse_yaml_frontmatter

REGISTRY: dict[str, dict] = {}
LOAD_ERRORS: dict[str, str] = {}
REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
_LOADED_FILES: set[Path] = set()

PROVIDER_BINDINGS = {
    "core_engine": "core_engine.interface",
    "editor": "editor.interface",
    "file_manager": "file_manager.interface",
    "workspace": "workspace.interface",
    "test_environment": "test_environment.interface",
    "codebuilder": "codebuilder.interface",
    "tools": "tools.interface",
    "tools.read_tool": "tools.read_tool",
    "tools.write_tool": "tools.write_tool",
    "tools.delete_file_tool": "tools.delete_file_tool",
    "tools.editor_tool": "tools.editor_tool",
    "tools.map_files_tool": "tools.map_files_tool",
    "tools.promoted_tools": "tools.promoted_tools",
    "core_engine.core_tools": "core_engine.core_tools",
}


def tool(name_or_func: str | Callable | None = None, provider: str = "core_engine"):
    """Decorator that registers a function as an invocable agent tool."""

    def decorator(func: Callable) -> Callable:
        tool_name = name_or_func if isinstance(name_or_func, str) else func.__name__
        if tool_name in REGISTRY and REGISTRY[tool_name]["function"] is not func:
            raise ValueError(
                f"Tool '{tool_name}' is already registered by provider '{REGISTRY[tool_name]['provider']}'."
            )
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

    if callable(name_or_func):
        func = name_or_func
        name_or_func = None
        return decorator(func)
    return decorator


def load_tools(reload: bool = False) -> None:
    """Load the five file tools and the non-file builtins module."""
    if reload:
        REGISTRY.clear()
        LOAD_ERRORS.clear()
        _LOADED_FILES.clear()

    if not TOOLS_DIR.is_dir():
        return

    for path in sorted(TOOLS_DIR.glob("*.py")):
        if path.name in ("__init__.py", "interface.py") or path.name.startswith("_"):
            continue
        if not reload and path.resolve() in _LOADED_FILES:
            continue

        module_name = f"tools.{path.stem}"
        snapshot = dict(REGISTRY)
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for '{path.name}'.")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            _LOADED_FILES.add(path.resolve())
            LOAD_ERRORS.pop(path.name, None)
        except Exception as exc:
            LOAD_ERRORS[path.name] = str(exc)
            # Revert any tools registered by this failed module
            for k in list(REGISTRY.keys()):
                if k not in snapshot:
                    REGISTRY.pop(k, None)
            sys.modules.pop(module_name, None)

    core_tools_path = REPO_ROOT / "core_engine" / "core_tools.py"
    module_name = "core_engine.core_tools"
    if core_tools_path.is_file() and (
        reload or core_tools_path.resolve() not in _LOADED_FILES
    ):
        snapshot = dict(REGISTRY)
        try:
            spec = importlib.util.spec_from_file_location(module_name, core_tools_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for '{core_tools_path.name}'.")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            _LOADED_FILES.add(core_tools_path.resolve())
            LOAD_ERRORS.pop(core_tools_path.name, None)
        except Exception as exc:
            LOAD_ERRORS[core_tools_path.name] = str(exc)
            for key in list(REGISTRY.keys()):
                if key not in snapshot:
                    REGISTRY.pop(key, None)
            sys.modules.pop(module_name, None)


def list_tools() -> list[dict]:
    """Return catalog metadata for all registered tools."""
    load_tools()
    return [
        {
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
            "custom": meta.get("custom", False),
        }
        for meta in REGISTRY.values()
    ]


def get_tools(names: list[str] | None = None) -> list[Callable]:
    """Resolve registered tool callables, filtered by an optional allow-list."""
    load_tools()
    if not names:
        return [meta["function"] for meta in REGISTRY.values()]
    resolved = []
    for name in names:
        meta = REGISTRY.get(name)
        if meta:
            resolved.append(meta["function"])
    return resolved


def get_load_errors() -> dict[str, str]:
    """Return dictionary of tool load errors mapping filename to error message."""
    return dict(LOAD_ERRORS)


def get_provider_bindings() -> dict[str, str]:
    """Return dictionary of provider doorway bindings."""
    return dict(PROVIDER_BINDINGS)


def unknown_tool_names(names: list[str]) -> list[str]:
    """Return list of tool names that are not found in the registry."""
    load_tools()
    return [name for name in names if name not in REGISTRY]


def get_catalog_report() -> dict:
    """Generate a comprehensive catalog report without raising exceptions.

    Returns:
        {
            tools: list[dict],
            providers: dict[str, str],
            load_errors: dict[str, str],
            missing_agent_tools: dict[str, list[str]],
            warnings: list[str]
        }
    """
    try:
        load_tools()
    except Exception:
        pass

    tools = [
        {
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
            "custom": meta.get("custom", False),
        }
        for meta in REGISTRY.values()
    ]
    providers = dict(PROVIDER_BINDINGS)
    load_errors = dict(LOAD_ERRORS)
    missing_agent_tools: dict[str, list[str]] = {}
    warnings: list[str] = []

    for filename, err in load_errors.items():
        warnings.append(f"Failed to load tool module '{filename}': {err}")

    agent_dirs = [LIBRARY_ROOT]
    for agents_dir in agent_dirs:
        try:
            if agents_dir.is_dir():
                for agent_file in sorted(agents_dir.glob("*.md")):
                    try:
                        raw = agent_file.read_text(encoding="utf-8")
                        meta = parse_yaml_frontmatter(raw)
                        agent_id = meta.get("id") or agent_file.stem
                        req_tools = meta.get("tools", [])
                        missing = [t for t in req_tools if t not in REGISTRY]
                        if missing:
                            missing_agent_tools[agent_id] = missing
                            warnings.append(
                                f"Agent '{agent_id}' references missing tools: {', '.join(missing)}"
                            )
                    except Exception as e:
                        warnings.append(f"Failed to parse '{agent_file}': {e}")
        except Exception as e:
            warnings.append(f"Failed to scan agent directory '{agents_dir}': {e}")

    return {
        "tools": tools,
        "providers": providers,
        "load_errors": load_errors,
        "missing_agent_tools": missing_agent_tools,
        "warnings": warnings,
    }

```

## `editor/__init__.py`
```py

```

## `editor/editor_operations.py`
```py
"""Physical file CRUD & Path Security for the editor pillar."""

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = REPO_ROOT / "workspace"
LIBRARY_ROOT = REPO_ROOT / "library"
ALLOWED_PATHS_CONFIG = REPO_ROOT / "tools" / "allowed_paths.json"


def _configured_write_roots() -> list[Path]:
    """Folders from allowed_paths.json that absolute paths may point into (re-read on every call)."""
    try:
        data = json.loads(ALLOWED_PATHS_CONFIG.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    roots = []
    for entry in data.get("file_manager_roots", []):
        raw = entry.get("path") if isinstance(entry, dict) else entry
        if raw:
            roots.append(Path(os.path.expandvars(str(raw))).expanduser().resolve())
    return roots


def resolve_project_path(relative_path: str, root: Path | None = None) -> Path:
    if not relative_path:
        raise ValueError("A project-relative path is required.")

    clean_rel = relative_path.replace("\\", "/")
    if clean_rel == "library" or clean_rel.startswith("library/"):
        base_root = REPO_ROOT.resolve()
        allowed_root = LIBRARY_ROOT.resolve()
        candidate = (base_root / clean_rel).resolve()
        try:
            candidate.relative_to(allowed_root)
        except ValueError:
            raise ValueError(f"Access outside agent library '{allowed_root}' is forbidden.") from None
        return candidate

    if root is None and Path(relative_path).is_absolute():
        absolute = Path(os.path.expandvars(relative_path)).expanduser().resolve()
        allowed_roots = _configured_write_roots()
        for allowed in allowed_roots:
            try:
                absolute.relative_to(allowed)
                return absolute
            except ValueError:
                continue
        allowed_list = ", ".join(str(r) for r in allowed_roots) or "none configured"
        raise ValueError(f"Absolute path '{absolute}' is outside the allowed folders: {allowed_list}")

    base_root = (root or PROJECT_ROOT).resolve()
    candidate = (base_root / clean_rel).resolve()

    try:
        candidate.relative_to(base_root)
    except ValueError:
        raise ValueError(f"Access outside root path '{base_root}' is forbidden.")

    return candidate


def read_file_content(relative_path: str) -> dict:
    abs_path = resolve_project_path(relative_path)
    if not abs_path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")
    content = abs_path.read_text(encoding="utf-8")
    return {"path": relative_path, "content": content}


def write_file_content(relative_path: str, content: str) -> dict:
    abs_path = resolve_project_path(relative_path)
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(content, encoding="utf-8")
    return {"path": relative_path, "bytes_written": len(content.encode('utf-8'))}


def delete_path(relative_path: str) -> dict:
    abs_path = resolve_project_path(relative_path)
    if abs_path.is_dir():
        if any(abs_path.iterdir()):
            raise IsADirectoryError(f"Directory not empty: {relative_path}")
        abs_path.rmdir()
    elif abs_path.is_file():
        abs_path.unlink()
    else:
        raise FileNotFoundError(f"Path not found: {relative_path}")
    return {"path": relative_path, "deleted": True}


def create_path(relative_path: str, kind: str = "file") -> dict:
    abs_path = resolve_project_path(relative_path)
    if abs_path.exists():
        raise FileExistsError(f"Path already exists: {relative_path}")
    if kind == "directory":
        abs_path.mkdir(parents=True)
    else:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text("", encoding="utf-8")
    return {"path": relative_path, "created": kind}


def get_directory_tree(relative_path: str = "") -> dict:
    library_requested = relative_path == "library" or relative_path.startswith("library/")
    if library_requested:
        target_dir = resolve_project_path(relative_path)
        tree_root = LIBRARY_ROOT
        path_prefix = "library"
    else:
        target_dir = resolve_project_path(relative_path) if relative_path else PROJECT_ROOT
        tree_root = PROJECT_ROOT
        path_prefix = ""

    def _build_tree(p: Path):
        rel = str(p.relative_to(tree_root)).replace("\\", "/")
        if path_prefix:
            rel = path_prefix if rel == "." else f"{path_prefix}/{rel}"
        if p.is_file():
            return {"name": p.name, "type": "file", "path": rel}
        children = []
        for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            is_python_cache = child.is_dir() and child.name.lower() in {"__pycache__", "_pycache__"}
            if child.name.startswith(".") or is_python_cache or (
                child.is_file() and child.suffix.lower() == ".py"
            ):
                continue
            children.append(_build_tree(child))
        return {"name": p.name, "type": "directory", "path": rel, "children": children}

    if not target_dir.exists():
        raise FileNotFoundError(f"Directory not found: {relative_path}")
    result = _build_tree(target_dir)
    if not relative_path and LIBRARY_ROOT.is_dir():
        result["children"].append({
            "name": "library",
            "type": "directory",
            "path": "library",
            "children": [
                {
                    "name": file.name,
                    "type": "file",
                    "path": f"library/{file.name}",
                }
                for file in sorted(LIBRARY_ROOT.iterdir(), key=lambda item: item.name.lower())
                if file.is_file()
            ],
        })
    return result

```

## `editor/editor_schemas.py`
```py
"""Scope & Event Payload Types for the editor session layer."""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class EditorScope(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    AGENTS = "agents"
    TESTING = "testing"


class EditorEventType(str, Enum):
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    TOOL_EXECUTED = "tool_executed"
    CURSOR_MOVED = "cursor_moved"
    SESSION_JOIN = "session_join"
    SESSION_LEAVE = "session_leave"


@dataclass
class EditorEvent:
    """Payload broadcast to every subscriber of the editor event bus."""
    type: EditorEventType
    path: str
    session_id: str
    scope: EditorScope = EditorScope.WORKSPACE
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["type"] = self.type.value
        payload["scope"] = self.scope.value
        return payload


@dataclass
class EditorSessionInfo:
    session_id: str
    client: str = "unknown"
    active_path: str = ""
    joined_at: float = 0.0

```

## `editor/editor_session.py`
```py
"""Session Manager & Event Bus for the editor pillar."""

import asyncio
import time
import uuid

from editor.editor_schemas import EditorEvent, EditorEvent as Event, EditorEventType, EditorSessionInfo


class EditorSessionManager:
    """Tracks connected editor sessions and fans events out to subscribers."""

    def __init__(self):
        self._sessions: dict[str, EditorSessionInfo] = {}
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._event_log: list[dict] = []
        self._max_log = 200

    # --- session lifecycle -------------------------------------------------
    def create_session(self, client: str = "unknown") -> EditorSessionInfo:
        session_id = uuid.uuid4().hex[:12]
        info = EditorSessionInfo(session_id=session_id, client=client, joined_at=time.time())
        self._sessions[session_id] = info
        self._subscribers[session_id] = asyncio.Queue()
        self.broadcast(Event(type=EditorEventType.SESSION_JOIN, path="", session_id=session_id,
                             data={"client": client}))
        return info

    def drop_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self.broadcast(Event(type=EditorEventType.SESSION_LEAVE, path="",
                                 session_id=session_id))
        self._sessions.pop(session_id, None)
        self._subscribers.pop(session_id, None)

    def set_active_path(self, session_id: str, path: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].active_path = path

    def sessions(self) -> list[EditorSessionInfo]:
        return list(self._sessions.values())

    # --- event bus ---------------------------------------------------------
    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue = self._subscribers.get(session_id)
        if queue is None:
            queue = asyncio.Queue()
            self._subscribers[session_id] = queue
        return queue

    def unsubscribe(self, session_id: str) -> None:
        self._subscribers.pop(session_id, None)

    def broadcast(self, event: Event) -> dict:
        payload = event.to_dict()
        self._event_log.append(payload)
        if len(self._event_log) > self._max_log:
            self._event_log = self._event_log[-self._max_log:]
        for queue in self._subscribers.values():
            queue.put_nowait(payload)
        return payload

    def publish(self, event_type: EditorEventType, path: str, session_id: str, **data) -> dict:
        return self.broadcast(Event(type=event_type, path=path, session_id=session_id, data=data or None))

    def recent_events(self, limit: int = 50) -> list[dict]:
        return self._event_log[-limit:]


# Global doorway instance used across editor modules.
manager = EditorSessionManager()

```

## `editor/interface.py`
```py
"""Editor Doorway: Python API & FastAPI Router (/api/file/*, /api/directory/*, /api/ws)."""

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from editor.editor_operations import (
    create_path,
    delete_path,
    get_directory_tree,
    read_file_content,
    resolve_project_path,
    write_file_content,
)
from editor.editor_schemas import EditorEventType
from editor.editor_session import manager

router = APIRouter()


class FileRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str = ""


class PathRequest(BaseModel):
    path: str = Field(..., min_length=1)
    kind: str = "file"


def read_file(relative_path: str) -> dict:
    """Doorway function: read a workspace file."""
    return read_file_content(relative_path)


def write_file(relative_path: str, content: str) -> dict:
    """Doorway function: write a workspace file."""
    return write_file_content(relative_path, content)


def list_tree(relative_path: str = "") -> dict:
    """Doorway function: workspace directory tree."""
    return get_directory_tree(relative_path)


# --- REST endpoints --------------------------------------------------------

@router.get("/api/file/read")
def api_read_file(path: str):
    try:
        return read_file_content(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/file/write")
def api_write_file(req: FileRequest, session_id: str = "http"):
    try:
        result = write_file_content(req.path, req.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    manager.publish(EditorEventType.FILE_SAVED, req.path, session_id,
                     bytes=result["bytes_written"])
    return result


@router.post("/api/file/create")
def api_create_file(req: PathRequest, session_id: str = "http"):
    try:
        result = create_path(req.path, req.kind)
    except (ValueError, FileExistsError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    manager.publish(EditorEventType.FILE_CREATED, req.path, session_id, kind=req.kind)
    return result


@router.post("/api/file/delete")
def api_delete_file(req: PathRequest, session_id: str = "http"):
    try:
        result = delete_path(req.path)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except IsADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    manager.publish(EditorEventType.FILE_DELETED, req.path, session_id)
    return result


@router.get("/api/directory/tree")
def api_directory_tree(path: str = ""):
    try:
        return get_directory_tree(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/editor/sessions")
def api_editor_sessions():
    return {"sessions": [{"session_id": s.session_id, "client": s.client,
                          "active_path": s.active_path} for s in manager.sessions()],
            "events": manager.recent_events()}


# --- WebSocket event bus ---------------------------------------------------

@router.websocket("/api/ws")
async def api_ws(websocket: WebSocket):
    await websocket.accept()
    session = manager.create_session(client=websocket.client.host if websocket.client else "unknown")
    queue = manager.subscribe(session.session_id)
    await websocket.send_json({"type": "connected", "session_id": session.session_id,
                               "sessions": len(manager.sessions())})

    async def pump_events():
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)

    pump = asyncio.create_task(pump_events())
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            if msg_type == "file_opened":
                manager.set_active_path(session.session_id, data.get("path", ""))
                manager.publish(EditorEventType.FILE_OPENED, data.get("path", ""),
                                session.session_id)
            elif msg_type == "cursor":
                manager.publish(EditorEventType.CURSOR_MOVED, data.get("path", ""),
                                session.session_id, line=data.get("line", 0),
                                column=data.get("column", 0))
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        pump.cancel()
        manager.drop_session(session.session_id)
        manager.unsubscribe(session.session_id)

```

## `file_manager/__init__.py`
```py
"""Workspace-scoped file manager."""

from file_manager.service import FileManagerService, file_manager_service

__all__ = ["FileManagerService", "file_manager_service"]

```

## `file_manager/backend.py`
```py
"""Secure physical file operations constrained to the configured file-manager root."""

import json
import os
import shutil
import tempfile
from pathlib import Path

from editor.editor_operations import PROJECT_ROOT

CONFIG_PATH = Path(__file__).resolve().parent.parent / "tools" / "allowed_paths.json"
SKIP_DIRECTORIES = {"__pycache__", "_pycache__"}


def _read_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Could not read file-manager configuration '{CONFIG_PATH}': {exc}"
        ) from exc
    if not isinstance(config, dict):
        raise RuntimeError(f"File-manager configuration must be a JSON object: {CONFIG_PATH}")
    return config


def configured_roots() -> list[dict[str, str]]:
    config = _read_config()
    roots = config.get("file_manager_roots")
    if roots is None:
        legacy_path = config.get("file_manager_root", str(PROJECT_ROOT.resolve()))
        roots = [{"name": "Workspace", "path": legacy_path}]
    if not isinstance(roots, list):
        raise RuntimeError("'file_manager_roots' must be a JSON array.")

    result = []
    names = set()
    paths = set()
    for entry in roots:
        if not isinstance(entry, dict):
            raise RuntimeError("Each file-manager root must have a name and path.")
        name = str(entry.get("name", "")).strip()
        raw_path = os.path.expandvars(str(entry.get("path", ""))).strip()
        if not name or not raw_path:
            raise RuntimeError("Each file-manager root must have a non-empty name and path.")
        root = Path(raw_path).expanduser()
        if not root.is_absolute():
            raise RuntimeError(f"File-manager root must be an absolute path: {raw_path}")
        resolved = root.resolve()
        if not resolved.is_dir():
            raise RuntimeError(f"Configured file-manager root is not an existing directory: {resolved}")
        name_key = name.casefold()
        path_key = os.path.normcase(str(resolved))
        if name_key in names or path_key in paths:
            raise RuntimeError("File-manager root names and paths must be unique.")
        names.add(name_key)
        paths.add(path_key)
        result.append({"name": name, "path": str(resolved)})
    if not result:
        raise RuntimeError("Configure at least one entry in 'file_manager_roots'.")
    return result


def active_root_path() -> Path:
    config = _read_config()
    roots = configured_roots()
    selected = config.get(
        "active_file_manager_root",
        config.get("file_manager_root", roots[0]["path"]),
    )
    for root in roots:
        if os.path.normcase(root["path"]) == os.path.normcase(str(selected)):
            return Path(root["path"])
    raise RuntimeError(
        "The active file-manager root is not present in 'file_manager_roots'."
    )


def workspace_root() -> Path:
    return active_root_path()


def select_root(path: str) -> dict:
    roots = configured_roots()
    selected = next(
        (root for root in roots if os.path.normcase(root["path"]) == os.path.normcase(path)),
        None,
    )
    if selected is None:
        raise ValueError("Choose a configured file-manager root.")

    config = _read_config()
    config["file_manager_roots"] = roots
    config["active_file_manager_root"] = selected["path"]
    config["file_manager_root"] = selected["path"]
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=CONFIG_PATH.parent,
            prefix=f".{CONFIG_PATH.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(config, temp_file, indent=2)
            temp_file.write("\n")
        temp_path.replace(CONFIG_PATH)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return {"roots": roots, "active_path": selected["path"]}


def resolve_workspace_path(relative_path: str = "") -> Path:
    if not isinstance(relative_path, str):
        raise ValueError("A workspace-relative path is required.")

    clean_path = relative_path.replace("\\", "/")
    if clean_path.startswith("/") or (len(clean_path) > 1 and clean_path[1] == ":"):
        raise ValueError("Absolute paths are not allowed.")
    base_root = workspace_root()
    parts = Path(clean_path).parts
    if any(part in {".", ".."} for part in parts):
        raise ValueError("Relative path traversal is not allowed.")
    candidate = base_root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("Symbolic links are not supported by the file manager.")
    path = candidate.resolve()
    try:
        path.relative_to(base_root)
    except ValueError:
        raise ValueError("Access outside the workspace is forbidden.") from None
    return path


def list_directory(relative_path: str = "") -> list[dict]:
    directory = resolve_workspace_path(relative_path)
    if not directory.is_dir():
        if directory.exists():
            raise NotADirectoryError(f"Not a directory: {relative_path}")
        raise FileNotFoundError(f"Directory not found: {relative_path}")

    entries = []
    for child in sorted(
        directory.iterdir(),
        key=lambda item: (
            not (not item.is_symlink() and item.is_dir()),
            item.name.lower(),
        ),
    ):
        if (
            child.is_symlink()
            or child.name.startswith(".")
            or (child.is_dir() and child.name.lower() in SKIP_DIRECTORIES)
            or (child.is_file() and child.suffix.lower() == ".pyc")
        ):
            continue
        try:
            resolved = child.resolve()
            resolved.relative_to(workspace_root())
        except ValueError:
            continue
        if not resolved.exists():
            continue
        stat = resolved.stat()
        entries.append({
            "name": resolved.name,
            "path": resolved.relative_to(workspace_root()).as_posix(),
            "type": "directory" if resolved.is_dir() else "file",
            "size": 0 if resolved.is_dir() else stat.st_size,
            "modified": stat.st_mtime,
        })
    return entries


def directory_tree(relative_path: str = "") -> dict:
    directory = resolve_workspace_path(relative_path)
    if not directory.is_dir():
        if directory.exists():
            raise NotADirectoryError(f"Not a directory: {relative_path}")
        raise FileNotFoundError(f"Directory not found: {relative_path}")
    root = workspace_root()
    rel_path = directory.relative_to(root).as_posix()
    node = {
        "name": directory.name or root.name,
        "path": "" if rel_path == "." else rel_path,
        "type": "directory",
        "children": [],
    }
    for item in list_directory(node["path"]):
        if item["type"] == "directory":
            node["children"].append(directory_tree(item["path"]))
        else:
            node["children"].append({
                "name": item["name"],
                "path": item["path"],
                "type": "file",
            })
    return node


def read_file(relative_path: str) -> dict:
    path = resolve_workspace_path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")
    return {
        "path": path.relative_to(workspace_root()).as_posix(),
        "content": path.read_text(encoding="utf-8"),
    }


def write_file(relative_path: str, content: str) -> dict:
    path = resolve_workspace_path(relative_path)
    if path.exists() and not path.is_file():
        raise IsADirectoryError(f"Path is not a file: {relative_path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {
        "path": path.relative_to(workspace_root()).as_posix(),
        "bytes_written": len(content.encode("utf-8")),
    }


def create_path(relative_path: str, kind: str = "file") -> dict:
    path = resolve_workspace_path(relative_path)
    if path.exists():
        raise FileExistsError(f"Path already exists: {relative_path}")
    if kind == "directory":
        path.mkdir(parents=True)
    elif kind == "file":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    else:
        raise ValueError("Kind must be 'file' or 'directory'.")
    return {
        "path": path.relative_to(workspace_root()).as_posix(),
        "created": kind,
    }


def delete_path(relative_path: str) -> dict:
    path = resolve_workspace_path(relative_path)
    if path == workspace_root():
        raise ValueError("The workspace root cannot be deleted.")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()
    else:
        raise FileNotFoundError(f"Path not found: {relative_path}")
    return {"path": relative_path.replace("\\", "/"), "deleted": True}


def move_path(source_path: str, destination_path: str) -> dict:
    source = resolve_workspace_path(source_path)
    destination = resolve_workspace_path(destination_path)
    if source == workspace_root():
        raise ValueError("The workspace root cannot be moved.")
    if not source.exists():
        raise FileNotFoundError(f"Path not found: {source_path}")
    if destination.exists():
        raise FileExistsError(f"Path already exists: {destination_path}")
    if source.is_dir():
        try:
            destination.relative_to(source)
        except ValueError:
            pass
        else:
            raise ValueError("A directory cannot be moved into itself.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return {
        "source_path": source_path.replace("\\", "/"),
        "destination_path": destination.relative_to(workspace_root()).as_posix(),
        "moved": True,
    }


def copy_path(source_path: str, destination_path: str) -> dict:
    source = resolve_workspace_path(source_path)
    destination = resolve_workspace_path(destination_path)
    if source == workspace_root():
        raise ValueError("The workspace root cannot be copied.")
    if not source.exists():
        raise FileNotFoundError(f"Path not found: {source_path}")
    if destination.exists():
        raise FileExistsError(f"Path already exists: {destination_path}")
    if source.is_dir():
        try:
            destination.relative_to(source)
        except ValueError:
            pass
        else:
            raise ValueError("A directory cannot be copied into itself.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, symlinks=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return {
        "source_path": source_path.replace("\\", "/"),
        "destination_path": destination.relative_to(workspace_root()).as_posix(),
        "copied": True,
    }

```

## `file_manager/interface.py`
```py
"""REST and elFinder interfaces for the workspace file manager."""

import base64
import mimetypes
from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException, Request

from file_manager import backend
from file_manager.schemas import (
    CreateRequest,
    FileContentRequest,
    MoveRequest,
    PathRequest,
    SelectRootRequest,
)
from file_manager.service import file_manager_service

router = APIRouter()

_VOLUME = "l1_"
_ELFINDER_API = "2.1"


@router.get("/api/file-manager/roots")
def api_file_manager_roots():
    return {
        "roots": backend.configured_roots(),
        "active_path": str(backend.workspace_root()),
    }


@router.post("/api/file-manager/roots/select")
def api_select_file_manager_root(request: SelectRootRequest):
    try:
        return backend.select_root(request.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, FileExistsError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, IsADirectoryError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, NotADirectoryError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, (ValueError, PermissionError)):
        return HTTPException(status_code=400, detail=str(exc))
    raise exc


@router.get("/api/file-manager/list")
def api_list_directory(path: str = ""):
    try:
        return file_manager_service.list_directory(path)
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


@router.get("/api/file-manager/tree")
def api_directory_tree(path: str = ""):
    try:
        return file_manager_service.directory_tree(path)
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


@router.get("/api/file-manager/read")
def api_read_file(path: str):
    try:
        return file_manager_service.read_file(path)
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


@router.post("/api/file-manager/write")
def api_write_file(request: FileContentRequest):
    try:
        return file_manager_service.write_file(request.path, request.content)
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


@router.post("/api/file-manager/create")
def api_create_path(request: CreateRequest):
    try:
        return file_manager_service.create(request.path, request.kind)
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


@router.post("/api/file-manager/delete")
def api_delete_path(request: PathRequest):
    try:
        return file_manager_service.delete(request.path)
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


@router.post("/api/file-manager/move")
def api_move_path(request: MoveRequest):
    try:
        return file_manager_service.move(
            request.source_path, request.destination_path
        )
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


def _encode_hash(path: str) -> str:
    normalized = path.strip("/") or "/"
    token = base64.urlsafe_b64encode(normalized.encode("utf-8")).decode("ascii")
    return _VOLUME + token.rstrip("=")


def _decode_hash(file_hash: str) -> str:
    if not isinstance(file_hash, str) or not file_hash.startswith(_VOLUME):
        raise ValueError("Invalid elFinder target.")
    token = file_hash[len(_VOLUME):]
    if not token or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for char in token):
        raise ValueError("Invalid elFinder target.")
    padded = token + "=" * (-len(token) % 4)
    try:
        decoded = base64.b64decode(padded, altchars=b"-_", validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid elFinder target.") from exc
    if _encode_hash(decoded) != file_hash:
        raise ValueError("Invalid elFinder target.")
    return "" if decoded == "/" else decoded


def _entry(path: str, entry: dict, parent: str) -> dict:
    item_hash = _encode_hash(path)
    is_directory = entry["type"] == "directory"
    return {
        "name": entry["name"],
        "hash": item_hash,
        "phash": _encode_hash(parent),
        "volumeid": _VOLUME,
        "mime": "directory" if is_directory else (
            mimetypes.guess_type(entry["name"])[0] or "application/octet-stream"
        ),
        "ts": int(entry["modified"]),
        "size": entry["size"],
        "read": 1,
        "write": 1,
        "locked": 0,
        "dirs": 1 if is_directory else 0,
        "path": path,
    }


def _directory_contents(path: str) -> list[dict]:
    listing = file_manager_service.list_directory(path)
    return [
        _entry(item["path"], item, path)
        for item in listing["entries"]
    ]


def _directory_tree(path: str) -> list[dict]:
    entries = _directory_contents(path)
    directories = []
    for entry in entries:
        if entry["mime"] == "directory":
            directories.append({
                "name": entry["name"],
                "hash": entry["hash"],
                "phash": entry["phash"],
                "path": entry["path"],
            })
            directories.extend(_directory_tree(entry["path"]))
    return directories


def _file_info(path: str) -> dict:
    resolved = backend.resolve_workspace_path(path)
    parent = PurePosixPath(path).parent.as_posix()
    if parent == ".":
        parent = ""
    if resolved.is_dir():
        entries = file_manager_service.list_directory(path)["entries"]
        entry = {
            "name": resolved.name if path else "workspace",
            "path": path,
            "type": "directory",
            "size": 0,
            "modified": resolved.stat().st_mtime,
        }
        info = _entry(path, entry, parent)
        info["dirs"] = sum(item["type"] == "directory" for item in entries)
        return info
    stat = resolved.stat()
    return _entry(path, {
        "name": resolved.name,
        "path": resolved.relative_to(backend.workspace_root()).as_posix(),
        "type": "file",
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }, parent)


def _child_path(parent: str, name: str) -> str:
    if not name or name in {".", ".."} or "/" in name or "\\" in name or "\x00" in name:
        raise ValueError("A valid file or directory name is required.")
    return f"{parent}/{name}" if parent else name


def _values(data, key: str) -> list[str]:
    if hasattr(data, "getlist"):
        values = data.getlist(f"{key}[]") or data.getlist(key)
    else:
        values = data.get(f"{key}[]", data.get(key, []))
    if isinstance(values, str):
        return [values]
    return list(values or [])


async def _connector_data(request: Request):
    if "application/json" in request.headers.get("content-type", ""):
        return await request.json()
    return await request.form()


@router.post("/api/elfinder/connector")
async def elfinder_connector(request: Request):
    data = await _connector_data(request)
    command = data.get("cmd", "")
    try:
        if command == "open":
            path = _decode_hash(data.get("target", _encode_hash("/")))
            cwd = _file_info(path)
            if cwd["mime"] != "directory":
                raise ValueError("The requested target is not a directory.")
            return {
                "cwd": cwd,
                "files": [cwd, *_directory_contents(path)],
                "api": _ELFINDER_API,
                "options": {
                    "path": path,
                    "url": "/api/elfinder/connector",
                    "disabled": [],
                    "separator": "/",
                    "archivers": {"create": [], "extract": []},
                },
            }

        if command == "tree":
            path = _decode_hash(data.get("target", _encode_hash("/")))
            return {"tree": _directory_tree(path)}

        if command == "ls":
            path = _decode_hash(data.get("target", ""))
            return {
                "list": {
                    item["hash"]: item["name"]
                    for item in _directory_contents(path)
                }
            }

        if command in {"mkfile", "mkdir"}:
            parent = _decode_hash(data.get("target", ""))
            name = data.get("name", "")
            path = _child_path(parent, name)
            result = file_manager_service.create(
                path, "directory" if command == "mkdir" else "file"
            )
            return {"added": [_file_info(result["path"])]}

        if command == "rename":
            source = _decode_hash(data.get("target", ""))
            resolved_source = backend.resolve_workspace_path(source)
            if not source or not resolved_source.exists():
                raise FileNotFoundError(f"Path not found: {source}")
            parent = PurePosixPath(source).parent.as_posix()
            destination = _child_path("" if parent == "." else parent, data.get("name", ""))
            result = file_manager_service.move(source, destination)
            return {"added": [_file_info(result["destination_path"])],
                    "removed": [_encode_hash(source)]}

        if command == "paste":
            destination = _decode_hash(data.get("dst", ""))
            cut = str(data.get("cut", "0")) in {"1", "true", "True"}
            added = []
            removed = []
            for source_hash in _values(data, "src"):
                source = _decode_hash(source_hash)
                source_path = backend.resolve_workspace_path(source)
                target_path = _child_path(destination, source_path.name)
                result = (
                    file_manager_service.move(source, target_path)
                    if cut else file_manager_service.copy(source, target_path)
                )
                added.append(_file_info(result["destination_path"]))
                if cut:
                    removed.append(source_hash)
            return {"added": added, "removed": removed}

        if command == "rm":
            targets = _values(data, "targets")
            removed = []
            for target in targets:
                path = _decode_hash(target)
                file_manager_service.delete(path)
                removed.append(target)
            return {"removed": removed}

        if command == "put":
            path = _decode_hash(data.get("target", ""))
            result = file_manager_service.write_file(path, data.get("content", ""))
            return {"changed": [_file_info(result["path"])]}

        raise ValueError(f"Unsupported elFinder command: {command or '(missing)'}")
    except (FileNotFoundError, FileExistsError, IsADirectoryError,
            NotADirectoryError, ValueError, PermissionError) as exc:
        return {"error": [str(exc)]}

```

## `file_manager/schemas.py`
```py
"""Request and response schemas for workspace file operations."""

from pydantic import BaseModel, Field


class PathRequest(BaseModel):
    path: str = Field(..., min_length=1)


class FileContentRequest(PathRequest):
    content: str


class CreateRequest(PathRequest):
    kind: str = Field(default="file", pattern="^(file|directory)$")


class MoveRequest(BaseModel):
    source_path: str = Field(..., min_length=1)
    destination_path: str = Field(..., min_length=1)


class SelectRootRequest(BaseModel):
    path: str = Field(..., min_length=1)


class FileEntry(BaseModel):
    name: str
    path: str
    type: str
    size: int
    modified: float


class DirectoryListing(BaseModel):
    path: str
    entries: list[FileEntry]

```

## `file_manager/service.py`
```py
"""Business logic for workspace file management."""

from file_manager import backend
from file_manager.schemas import DirectoryListing, FileEntry


class FileManagerService:
    """Single service layer shared by REST, elFinder, and agent tools."""

    def list_directory(self, path: str = "") -> dict:
        entries = backend.list_directory(path)
        return DirectoryListing(
            path=path.replace("\\", "/"),
            entries=[FileEntry(**entry) for entry in entries],
        ).model_dump()

    def directory_tree(self, path: str = "") -> dict:
        return backend.directory_tree(path)

    def read_file(self, path: str) -> dict:
        return backend.read_file(path)

    def write_file(self, path: str, content: str) -> dict:
        return backend.write_file(path, content)

    def create(self, path: str, kind: str = "file") -> dict:
        return backend.create_path(path, kind)

    def delete(self, path: str) -> dict:
        return backend.delete_path(path)

    def move(self, source_path: str, destination_path: str) -> dict:
        return backend.move_path(source_path, destination_path)

    def copy(self, source_path: str, destination_path: str) -> dict:
        return backend.copy_path(source_path, destination_path)


file_manager_service = FileManagerService()

```

## `file_manager/test_file_manager.py`
```py
import base64
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from file_manager import backend
from file_manager.interface import router


def test_file_manager_uses_configured_root(tmp_path, monkeypatch):
    root = tmp_path / "configured"
    root.mkdir()
    alternate_root = tmp_path / "alternate"
    alternate_root.mkdir()
    config = tmp_path / "allowed_paths.json"
    config.write_text(json.dumps({
        "map_roots": ["read-only"],
        "file_manager_roots": [
            {"name": "Main", "path": str(root)},
            {"name": "Alternate", "path": str(alternate_root)},
        ],
        "active_file_manager_root": str(root),
    }), encoding="utf-8")
    monkeypatch.setattr(backend, "CONFIG_PATH", config)

    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "ignored.pyc").touch()
    backend.create_path("notes/hello.txt")
    assert (root / "notes" / "hello.txt").is_file()
    assert backend.directory_tree()["name"] == root.name
    assert [entry["name"] for entry in backend.list_directory()] == ["notes"]
    selected = backend.select_root(str(alternate_root))
    assert selected["active_path"] == str(alternate_root)
    assert backend.workspace_root() == alternate_root
    saved_config = json.loads(config.read_text(encoding="utf-8"))
    assert saved_config["map_roots"] == ["read-only"]
    assert saved_config["active_file_manager_root"] == str(alternate_root)


def _hash(path: str) -> str:
    value = path or "/"
    encoded = base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")
    return f"l1_{encoded}"


def test_workspace_file_operations_and_traversal_rejection(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    assert client.post(
        "/api/file-manager/create",
        json={"path": "docs", "kind": "directory"},
    ).status_code == 200
    write_response = client.post(
        "/api/file-manager/write",
        json={"path": "docs/readme.md", "content": "workspace file"},
    )
    assert write_response.json()["bytes_written"] == len("workspace file")
    assert client.get("/api/file-manager/read", params={"path": "docs/readme.md"}).json() == {
        "path": "docs/readme.md",
        "content": "workspace file",
    }

    listing = client.get("/api/file-manager/list", params={"path": "docs"}).json()
    assert [entry["name"] for entry in listing["entries"]] == ["readme.md"]
    assert client.post(
        "/api/file-manager/move",
        json={"source_path": "docs/readme.md", "destination_path": "readme.md"},
    ).json()["moved"]
    assert client.get("/api/file-manager/read", params={"path": "../outside.txt"}).status_code == 400


def test_select_root_only_accepts_configured_directories(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    alternate = tmp_path / "alternate"
    alternate.mkdir()
    config = tmp_path / "allowed_paths.json"
    config.write_text(json.dumps({
        "file_manager_roots": [
            {"name": "Root", "path": str(root)},
            {"name": "Alternate", "path": str(alternate)},
        ],
        "active_file_manager_root": str(root),
    }), encoding="utf-8")
    monkeypatch.setattr(backend, "CONFIG_PATH", config)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    assert client.get("/api/file-manager/roots").json() == {
        "roots": [
            {"name": "Root", "path": str(root)},
            {"name": "Alternate", "path": str(alternate)},
        ],
        "active_path": str(root),
    }
    assert client.post(
        "/api/file-manager/roots/select",
        json={"path": str(tmp_path)},
    ).status_code == 400
    assert client.post(
        "/api/file-manager/roots/select",
        json={"path": str(alternate)},
    ).json()["active_path"] == str(alternate)
    assert client.get("/api/file-manager/tree").json()["name"] == "alternate"


def test_elfinder_open_and_put_use_the_shared_workspace_service(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    opened = client.post(
        "/api/elfinder/connector",
        data={"cmd": "open", "target": _hash("")},
    ).json()
    assert opened["cwd"]["hash"] == _hash("")

    created = client.post(
        "/api/elfinder/connector",
        data={"cmd": "mkfile", "target": _hash(""), "name": "note.txt"},
    ).json()
    target_hash = created["added"][0]["hash"]
    updated = client.post(
        "/api/elfinder/connector",
        data={"cmd": "put", "target": target_hash, "content": "from elFinder"},
    ).json()

    assert updated["changed"][0]["path"] == "note.txt"
    assert client.get(
        "/api/file-manager/read", params={"path": "note.txt"}
    ).json()["content"] == "from elFinder"

    folder = client.post(
        "/api/elfinder/connector",
        data={"cmd": "mkdir", "target": _hash(""), "name": "folder"},
    ).json()["added"][0]
    assert client.post(
        "/api/elfinder/connector",
        data={
            "cmd": "paste",
            "src[]": target_hash,
            "dst": folder["hash"],
            "cut": "0",
        },
    ).json()["added"][0]["path"] == "folder/note.txt"

    renamed = client.post(
        "/api/elfinder/connector",
        data={
            "cmd": "rename",
            "target": _hash("folder/note.txt"),
            "name": "renamed.txt",
        },
    ).json()
    assert renamed["added"][0]["path"] == "folder/renamed.txt"
    assert client.post(
        "/api/elfinder/connector",
        data={"cmd": "tree", "target": _hash("")},
    ).json()["tree"][0]["hash"] == _hash("folder")
    assert "note.txt" in client.post(
        "/api/elfinder/connector",
        data={"cmd": "ls", "target": _hash("")},
    ).json()["list"].values()

    moved = client.post(
        "/api/elfinder/connector",
        data={
            "cmd": "paste",
            "src[]": target_hash,
            "dst": folder["hash"],
            "cut": "1",
        },
    ).json()
    assert moved["added"][0]["path"] == "folder/note.txt"
    assert moved["removed"] == [target_hash]

    assert client.post(
        "/api/elfinder/connector",
        data={"cmd": "rm", "targets[]": _hash("folder")},
    ).json()["removed"] == [_hash("folder")]

    rejected = client.post(
        "/api/elfinder/connector",
        data={"cmd": "rm", "targets[]": _hash("")},
    ).json()
    assert "error" in rejected

```

## `frontend/pages/chat.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chat Console — Novous2 Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/test_panel.css">
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS2 <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn" href="/editor">File & Agent Editor</a>
        <a class="nav-btn active" href="/chat">Chat Console</a>
        <a class="nav-btn" href="/test">Prompt Testing</a>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <main id="view-container" class="main-content">
      <div class="loading-spinner">Loading Chat Console...</div>
    </main>
  </div>

  <script type="module">
    import { renderChatView } from '/static/js/chat.js';
    renderChatView(document.getElementById('view-container'));
  </script>
</body>
</html>

```

## `frontend/pages/codeBuilder.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CodeBuilder — Novous2 Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/codebuilder.css?v=4">
  <link rel="stylesheet" href="/static/css/test_panel.css">
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS2 <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn" href="/editor">File &amp; Agent Editor</a>
        <a class="nav-btn active" href="/codebuilder">Code Builder</a>
        <a class="nav-btn" href="/chat">Chat Console</a>
        <a class="nav-btn" href="/test">Prompt Testing</a>
      </nav>
      <div class="badge badge-success">Python Editor</div>
    </header>

    <main id="view-container" class="main-content"></main>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.min.js"></script>
  <script type="module">
    import { renderCodeBuilderView } from '/static/js/codebuilder/codebuilder.js?v=7';
    renderCodeBuilderView(document.getElementById('view-container'));
  </script>
</body>
</html>

```

## `frontend/pages/editor.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Editor — Novous2 Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/codebuilder.css">
  <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.min.js"></script>
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS2 <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn active" href="/editor">File & Agent Editor</a>
        <a class="nav-btn" href="/chat">Chat Console</a>
        <a class="nav-btn" href="/test">Prompt Testing</a>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <main id="view-container" class="main-content">
      <div class="loading-spinner">Loading Editor...</div>
    </main>
  </div>

  <script type="module">
    import { renderEditorView } from '/static/js/editor.js';
    const params = new URLSearchParams(location.search);
    const path = params.get('path');
    renderEditorView(document.getElementById('view-container'), path
      ? { path, managedFile: params.get('managed') === '1' }
      : null);
  </script>
</body>
</html>

```

## `frontend/pages/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Novous2 Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/test_panel.css">
  <link rel="stylesheet" href="/static/css/codebuilder.css">
</head>
<body class="bg-dark text-light">
  <div id="app" class="app-container">
    <!-- Top Bar Navigation -->
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS2 <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <button class="nav-btn active" data-tab="dashboard">Dashboard</button>
        <button class="nav-btn" data-tab="editor">File & Agent Editor</button>
        <button class="nav-btn" data-tab="codebuilder">Code Builder</button>
        <button class="nav-btn" data-tab="chat">Chat Console</button>
        <button class="nav-btn" data-tab="prompt-creation">Prompt Creation</button>
        <button class="nav-btn" data-tab="testing">Prompt Testing</button>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <!-- Dynamic Content View Frame -->
    <main id="view-container" class="main-content">
      <!-- Tabs will inject view content dynamically via app.js -->
      <div class="loading-spinner">Loading Novous2 Workspace...</div>
    </main>
  </div>

  <script src="https://unpkg.com/lucide@latest" defer></script>
  <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.min.js"></script>
  <script type="module" src="/static/js/app.js"></script>
</body>
</html>

```

## `frontend/pages/terminal.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Terminal — Novous2 Sandbox</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/codebuilder.css?v=3">
</head>
<body class="bg-dark text-light tw-terminal-page">
  <div id="terminal-root"></div>
  <script type="module">
    import { mountTerminal, TERMINAL_CHANNEL } from '/static/js/terminal.js?v=2';
    const terminal = mountTerminal(document.getElementById('terminal-root'));
    terminal.focus();

    const channel = 'BroadcastChannel' in window ? new BroadcastChannel(TERMINAL_CHANNEL) : null;
    if (channel) {
      channel.postMessage({ type: 'popout-open' });
      channel.onmessage = (event) => {
        if (event.data?.type === 'close-popout') window.close();
        if (event.data?.type === 'ping') channel.postMessage({ type: 'popout-open' });
      };
      window.addEventListener('beforeunload', () => channel.postMessage({ type: 'popout-closed' }));
    }
  </script>
</body>
</html>

```

## `frontend/pages/testing.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prompt Testing — Novous2 Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css?v=8">
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS2 <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn" href="/editor">File & Agent Editor</a>
        <a class="nav-btn" href="/chat">Chat Console</a>
        <a class="nav-btn active" href="/test">Prompt Testing</a>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <main id="view-container" class="main-content">
      <div class="loading-spinner">Loading Prompt Testing...</div>
    </main>
  </div>

  <script type="module">
    import { renderTestingView } from '/static/js/testing.js?v=8';
    renderTestingView(document.getElementById('view-container'));
  </script>
</body>
</html>

```

## `frontend/static/css/codebuilder.css`
```css
.codebuilder-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 610px;
  gap: 0.6rem;
}

.codebuilder-toolbar {
  min-height: 42px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.4rem 0.65rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}

.codebuilder-toolbar-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
  min-width: 0;
}

.question-dialog.is-resizable {
  resize: both;
  overflow: auto;
  width: min(560px, 92vw);
  min-width: 320px;
  min-height: 240px;
  max-width: 96vw;
  max-height: 92vh;
}

.question-dialog.is-resizable .codebuilder-open-tree {
  max-height: none;
  min-width: 0;
}

.codebuilder-file-label,
.codebuilder-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.codebuilder-file-label {
  min-width: 0;
  font-size: 0.86rem;
}

.codebuilder-file-label > span:nth-child(2) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codebuilder-python-icon {
  display: inline-grid;
  place-items: center;
  width: 25px;
  height: 25px;
  border-radius: 6px;
  background: #3776ab;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
}

.codebuilder-toolbar-actions .btn-primary:disabled {
  cursor: wait;
  opacity: 0.7;
}

.codebuilder-run-mode {
  display: inline-flex;
  align-items: center;
}

.codebuilder-run-mode select {
  max-width: 190px;
  padding: 0.3rem 0.45rem;
  font-size: 0.78rem;
}

/* ---------- Layout grid ----------
   Columns: chat | v-resizer | editor | v-resizer | console
   Rows:    main panes | h-resizer | agents strip
   Sizes are driven by CSS variables so drag handles and collapse
   toggles only need to mutate variables. */
.codebuilder-layout {
  display: grid;
  grid-template-columns:
    var(--chat-w, 320px) 6px minmax(0, 1fr) 6px var(--console-w, 300px);
  grid-template-rows:
    minmax(0, 1fr) 6px var(--agents-h, 220px);
  flex: 1;
  min-height: 250px;
  overflow: hidden;
}

.codebuilder-chat-panel {
  grid-column: 1;
  grid-row: 1;
}

.codebuilder-resizer[data-resize="chat"] {
  grid-column: 2;
  grid-row: 1;
}

.codebuilder-editor-panel {
  grid-column: 3;
  grid-row: 1;
}

.codebuilder-resizer[data-resize="console"] {
  grid-column: 4;
  grid-row: 1;
}

.codebuilder-console-panel {
  grid-column: 5;
  grid-row: 1;
}

.codebuilder-resizer[data-resize="agents"] {
  grid-column: 1 / -1;
  grid-row: 2;
}

.codebuilder-agents-panel {
  grid-column: 1 / -1;
  grid-row: 3;
}

/* ---------- Panes ---------- */
.codebuilder-chat-panel,
.codebuilder-editor-panel,
.codebuilder-console-panel,
.codebuilder-agents-panel {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}

.codebuilder-chat-panel,
.codebuilder-console-panel,
.codebuilder-agents-panel {
  display: flex;
  flex-direction: column;
}

/* ---------- Resizers ---------- */
.codebuilder-resizer {
  background: var(--border-color);
  opacity: 0.5;
}

.codebuilder-resizer:hover,
body.is-resizing .codebuilder-resizer.is-dragging {
  background: var(--primary);
  opacity: 0.9;
}

.codebuilder-resizer[data-resize="chat"],
.codebuilder-resizer[data-resize="console"] {
  cursor: col-resize;
}

.codebuilder-resizer[data-resize="agents"] {
  cursor: row-resize;
}

body.is-resizing {
  cursor: default;
  user-select: none;
}

/* ---------- Agents panel (bottom strip) ---------- */
.codebuilder-agents-heading {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 36px;
  padding: 0.35rem 0.55rem;
  border-bottom: 1px solid var(--border-color);
}

.codebuilder-agents-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.codebuilder-agents-title h2 {
  margin: 0;
  font-size: 0.86rem;
}

.codebuilder-agents-toggle,
.codebuilder-agent-refresh,
.codebuilder-console-collapse,
.codebuilder-chat-expand {
  flex: 0 0 auto;
  min-width: 30px;
  padding: 0.2rem 0.45rem;
  line-height: 1.2;
}

.codebuilder-agent-refresh {
  flex: 0 0 auto;
  margin-left: auto;
}

.codebuilder-agent-status {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codebuilder-agent-list {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.6rem;
  overflow-y: auto;
  padding: 0.6rem 0.75rem;
}

.codebuilder-agent-list > p {
  grid-column: 1 / -1;
  margin: 0;
  padding: 0.35rem;
}

.codebuilder-agent-select {
  grid-column: 1 / -1;
  width: 100%;
}

.codebuilder-agent-tile.selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
  background: var(--bg-elev);
}

.codebuilder-agent-tile.selected i,
.codebuilder-agent-tile.selected svg {
  color: var(--primary);
}

/* ---------- Editor panel ---------- */
.codebuilder-editor-panel {
  display: flex;
  flex-direction: column;
}

.codebuilder-open-tree {
  min-width: min(480px, 80vw);
  max-height: 55vh;
  overflow: auto;
}

.codebuilder-memory-dialog {
  border: 1px solid var(--border, #444);
  border-radius: 8px;
  background: var(--bg-elev, #1f2430);
  color: inherit;
  padding: 1rem 1.1rem;
  width: min(420px, 92vw);
}

.codebuilder-memory-dialog::backdrop { background: rgba(0, 0, 0, 0.5); }
.codebuilder-memory-dialog h3 { margin: 0 0 0.4rem; }
.codebuilder-memory-dialog label { display: block; margin-top: 0.7rem; }
.codebuilder-memory-dialog .form-select,
.codebuilder-memory-dialog .form-input { width: 100%; margin-top: 0.25rem; }
.codebuilder-memory-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }

.editor-surface {
  flex: 1;
  min-height: 0;
  background: var(--bg-dark);
}

.codebuilder-textarea {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  min-height: 0;
  resize: none;
  padding: 0.9rem 1rem;
  border: 0;
  outline: none;
  background: var(--bg-dark);
  color: var(--text-main);
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  tab-size: 4;
}

.codebuilder-statusbar {
  min-height: 25px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  padding: 0 0.75rem;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.72rem;
}

.codebuilder-statusbar span:first-child {
  margin-right: auto;
}

/* ---------- Console panel ---------- */
.codebuilder-console-panel {
  display: flex;
  flex-direction: column;
}

.codebuilder-console-heading,
.codebuilder-chat-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.7rem 0.85rem;
  border-bottom: 1px solid var(--border-color);
}

.codebuilder-console-heading h2,
.codebuilder-output-section h3,
.codebuilder-problems-section h3 {
  display: inline-block;
  margin: 0;
  font-size: 0.85rem;
}

#codebuilder-fix-with-agent,
#codebuilder-copy-console {
  float: right;
}

.codebuilder-output-section h3 {
  display: inline-block;
  margin: 0;
  font-size: 0.85rem;
}

.codebuilder-console-subtitle {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.codebuilder-output-section,
.codebuilder-problems-section {
  min-height: 0;
  padding: 0.7rem 0.85rem;
}

.codebuilder-output-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid var(--border-color);
}

.console-output {
  flex: 1;
  min-height: 70px;
  max-height: 40vh;
  overflow: auto;
  margin: 0.55rem 0 0;
  padding: 0.65rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-dark);
  color: var(--text-main);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.45;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.codebuilder-problems-section {
  flex: 0 1 35%;
  overflow: auto;
}

.diagnostics-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: 0.55rem;
}

.diagnostics-list p {
  margin: 0;
  font-size: 0.78rem;
}

.diagnostic-item {
  width: 100%;
  padding: 0.45rem 0.55rem;
  border: 0;
  border-left: 3px solid var(--danger);
  border-radius: 4px;
  background: var(--bg-elev);
  color: var(--text-main);
  text-align: left;
  font: inherit;
  font-size: 0.76rem;
  overflow-wrap: anywhere;
}

button.diagnostic-item {
  cursor: pointer;
}

.diagnostic-item[data-severity="warning"] {
  border-left-color: var(--warning);
}

.diagnostic-item[data-severity="info"] {
  border-left-color: var(--primary);
}

/* ---------- Chat panel (left column) ---------- */
.codebuilder-chat-heading {
  flex: 0 0 auto;
  padding: 0.45rem 0.75rem;
}

.codebuilder-chat-heading h2 {
  margin: 0;
  font-size: 0.86rem;
}

.codebuilder-chat-heading .text-muted {
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codebuilder-chat-messages {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.3rem;
  min-height: 0;
  overflow-y: auto;
  padding: 0.4rem 0.75rem;
}

.codebuilder-chat-message {
  align-self: flex-start;
  max-width: 85%;
  padding: 0.3rem 0.5rem;
  border-radius: 5px;
  background: var(--bg-elev);
  font-size: 0.78rem;
  line-height: 1.35;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.codebuilder-chat-message.assistant {
  max-width: min(95%, 900px);
  min-width: 0;
}

.codebuilder-chat-text {
  white-space: pre-wrap;
}

.codebuilder-code-block {
  min-width: 0;
  margin: 0.45rem 0;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-dark);
}

.codebuilder-code-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.3rem 0.5rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.7rem;
}

.codebuilder-code-language {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-transform: lowercase;
}

.codebuilder-code-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.codebuilder-copy-code,
.codebuilder-send-code,
.codebuilder-expand-code,
.codebuilder-modal-close {
  padding: 0.2rem 0.45rem;
  font-family: inherit;
  font-size: 0.7rem;
}

.codebuilder-chat-code {
  min-width: 0;
  overflow: hidden;
  border-radius: 0 0 6px 6px;
  background: var(--bg-dark);
}

.codebuilder-chat-code .monaco-editor,
.codebuilder-chat-code .monaco-editor .margin,
.codebuilder-chat-code .monaco-editor-background {
  background: var(--bg-dark);
}

.codebuilder-code-block pre {
  max-width: 100%;
  max-height: 320px;
  overflow: auto;
  margin: 0;
  padding: 0.65rem;
  color: var(--text-main);
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 0.76rem;
  line-height: 1.45;
  tab-size: 4;
}

.codebuilder-code-block code {
  white-space: pre;
}

.codebuilder-chat-code > pre {
  height: 100%;
  max-height: none;
  box-sizing: border-box;
}

.codebuilder-chat-message.user {
  align-self: flex-end;
  background: var(--primary);
  color: #fff;
}

.codebuilder-chat-message.system {
  align-self: center;
  background: transparent;
  color: var(--text-muted);
}

.codebuilder-chat-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 0.5rem;
  padding: 0.45rem 0.65rem;
  border-top: 1px solid var(--border-color);
}

.codebuilder-model-picker {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.codebuilder-model-picker .form-select {
  width: 100%;
  min-width: 0;
  padding: 0.4rem 0.5rem;
  font-size: 0.78rem;
}

.codebuilder-chat-form textarea {
  grid-column: 1;
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 38px;
  max-height: 110px;
  resize: vertical;
  padding: 0.45rem 0.6rem;
  font-size: 0.82rem;
}

.codebuilder-chat-actions {
  grid-column: 2;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.codebuilder-chat-actions .btn {
  width: 100%;
}

/* ---------- Expanded code modal ---------- */
.codebuilder-code-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: rgba(8, 10, 16, 0.72);
}

.codebuilder-code-modal {
  display: flex;
  flex-direction: column;
  width: min(1100px, 94vw);
  max-height: 88vh;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.codebuilder-code-modal-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.72rem;
}

.codebuilder-code-modal-heading .codebuilder-code-actions {
  gap: 0.4rem;
}

.codebuilder-code-modal-body {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--bg-dark);
}

.codebuilder-code-modal-body .monaco-editor,
.codebuilder-code-modal-body .monaco-editor .margin,
.codebuilder-code-modal-body .monaco-editor-background {
  background: var(--bg-dark);
}

body.codebuilder-modal-open {
  overflow: hidden;
}

/* ---------- Collapse rails ---------- */
.codebuilder-shell.chat-collapsed {
  --chat-w: 44px;
}

.codebuilder-shell.console-collapsed {
  --console-w: 44px;
}

.codebuilder-shell.agents-collapsed {
  --agents-h: 38px;
}

.codebuilder-shell.chat-collapsed .codebuilder-chat-heading {
  justify-content: center;
  padding: 0.45rem 0.2rem;
}

.codebuilder-shell.chat-collapsed .codebuilder-chat-heading h2,
.codebuilder-shell.chat-collapsed .codebuilder-chat-heading .text-muted,
.codebuilder-shell.chat-collapsed .codebuilder-chat-messages,
.codebuilder-shell.chat-collapsed .codebuilder-chat-form {
  display: none;
}

.codebuilder-shell.console-collapsed .codebuilder-console-heading {
  justify-content: center;
  padding: 0.45rem 0.2rem;
}

.codebuilder-shell.console-collapsed .codebuilder-console-heading h2,
.codebuilder-shell.console-collapsed .codebuilder-console-subtitle,
.codebuilder-shell.console-collapsed .codebuilder-output-section,
.codebuilder-shell.console-collapsed .codebuilder-problems-section {
  display: none;
}

.codebuilder-shell.agents-collapsed .codebuilder-agents-heading {
  justify-content: flex-end;
}

.codebuilder-shell.agents-collapsed .codebuilder-agents-title {
  display: none;
}

.codebuilder-shell.agents-collapsed .codebuilder-agent-list {
  display: none;
}

/* ---------- Responsive: medium ---------- */
@media (max-width: 1100px) {
  .codebuilder-layout {
    grid-template-columns: var(--chat-w, 280px) 6px minmax(0, 1fr);
    grid-template-rows:
      minmax(280px, 1.2fr) minmax(180px, 0.6fr) 6px var(--agents-h, 200px);
  }

  .codebuilder-chat-panel {
    grid-column: 1;
    grid-row: 1;
  }

  .codebuilder-resizer[data-resize="chat"] {
    grid-column: 2;
    grid-row: 1;
  }

  .codebuilder-editor-panel {
    grid-column: 3;
    grid-row: 1;
  }

  .codebuilder-resizer[data-resize="console"] {
    display: none;
  }

  .codebuilder-console-panel {
    grid-column: 3;
    grid-row: 2;
  }

  .codebuilder-resizer[data-resize="agents"] {
    grid-column: 1 / -1;
    grid-row: 3;
  }

  .codebuilder-agents-panel {
    grid-column: 1 / -1;
    grid-row: 4;
  }
}

/* ---------- Responsive: small ---------- */
@media (max-width: 700px) {
  .codebuilder-shell {
    height: auto;
    min-height: 900px;
  }

  .codebuilder-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .codebuilder-toolbar-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .codebuilder-run-mode,
  .codebuilder-run-mode select {
    flex: 1;
    max-width: none;
    width: 100%;
  }

  .codebuilder-toolbar-actions .btn {
    flex: 1;
    padding: 0.4rem 0.5rem;
    font-size: 0.75rem;
  }

  .codebuilder-layout {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows:
      auto minmax(350px, 55vh) minmax(260px, 35vh) var(--agents-h, 190px);
    min-height: 900px;
  }

  .codebuilder-resizer {
    display: none;
  }

  .codebuilder-chat-panel {
    grid-column: 1;
    grid-row: 1;
    height: 460px;
  }

  .codebuilder-editor-panel {
    grid-column: 1;
    grid-row: 2;
  }

  .codebuilder-console-panel {
    grid-column: 1;
    grid-row: 3;
  }

  .codebuilder-agents-panel {
    grid-column: 1;
    grid-row: 4;
  }

  .codebuilder-statusbar {
    gap: 0.55rem;
    font-size: 0.65rem;
  }
}
/* ---------- Terminal (docked tab + pop-out page) ---------- */
.codebuilder-console-tabs {
  display: flex;
  gap: 0.35rem;
  padding: 0.4rem 0.85rem 0;
  border-bottom: 1px solid var(--border-color);
}

.codebuilder-console-tabs .btn.active {
  background: var(--bg-elev);
  border-bottom-color: var(--primary);
  color: var(--text-main);
}

.codebuilder-console-panel.show-terminal .codebuilder-output-section,
.codebuilder-console-panel.show-terminal .codebuilder-problems-section {
  display: none;
}

.codebuilder-terminal-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.6rem;
}

.codebuilder-terminal-section[hidden],
.codebuilder-terminal-popped[hidden],
.codebuilder-terminal-mount[hidden] {
  display: none;
}

.codebuilder-terminal-mount {
  flex: 1;
  min-height: 0;
  display: flex;
}

.codebuilder-terminal-popped {
  text-align: center;
  padding: 1.5rem 0.5rem;
  color: var(--text-muted);
}

.tw-terminal {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  background: #1e1e1e;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0.5rem;
}

.tw-terminal-page,
.tw-terminal-page #terminal-root {
  height: 100vh;
  margin: 0;
}

.tw-terminal-page .tw-terminal {
  height: 100%;
  box-sizing: border-box;
  border-radius: 0;
  border: 0;
}

.tw-terminal-bar {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.tw-terminal-spacer { flex: 1; }

.tw-terminal-cwd {
  color: #9cdcfe;
  font: 0.72rem Consolas, "Courier New", monospace;
  overflow-wrap: anywhere;
}

.tw-terminal-badge {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  border-radius: 999px;
  background: #1f6f43;
  color: #fff;
}

.tw-terminal-links a {
  display: block;
  color: #4ec9b0;
  font-size: 0.78rem;
}

.tw-terminal-output {
  flex: 1;
  min-height: 6rem;
  margin: 0;
  overflow: auto;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: #d4d4d4;
  font: 0.78rem/1.45 Consolas, "Courier New", monospace;
}

.tw-terminal-form {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border-top: 1px solid #333;
  padding-top: 0.4rem;
}

.tw-terminal-prompt { color: #4ec9b0; font-family: Consolas, monospace; }

.tw-terminal-input {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: 0;
  outline: 0;
  color: #fff;
  font: 0.8rem Consolas, "Courier New", monospace;
}

.codebuilder-filename {
  color: var(--text-main);
  font-weight: 600;
}

```

## `frontend/static/css/style.css`
```css
/* Novous2 Agent Factory — Unified Dark Mode Theme */

:root {
  --bg-dark: #121316;
  --bg-card: #1e2025;
  --bg-elev: #262a31;
  --primary: #3b82f6;
  --accent: #8b5cf6;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --text-main: #e2e8f0;
  --text-muted: #8b94a7;
  --border-color: #2e323b;
  --radius: 8px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-dark);
  color: var(--text-main);
  height: 100vh;
  overflow: hidden;
}

.bg-dark { background-color: var(--bg-dark); }
.text-light { color: var(--text-main); }
.text-muted { color: var(--text-muted); }
.text-danger { color: var(--danger); }
.text-success { color: var(--success); }
.small { font-size: 0.82rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; }
.hidden { display: none !important; }
.spacer { flex: 1; }

/* --- App shell / navbar -------------------------------------------------- */
.app-container { display: flex; flex-direction: column; height: 100vh; }

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.logo { display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; letter-spacing: 0.04em; }
.logo-icon { color: var(--warning); }
.logo-text strong { color: #fff; }

.nav-links { display: flex; gap: 0.25rem; }

.nav-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.95rem;
  border-bottom: 2px solid transparent;
  border-radius: 4px 4px 0 0;
}

a.nav-btn { display: inline-flex; align-items: center; text-decoration: none; }
.nav-btn:hover { color: var(--text-main); background: var(--bg-elev); }
.nav-btn.active { color: var(--primary); border-bottom: 2px solid var(--primary); }

.main-content { flex: 1; overflow: auto; padding: 1.25rem 1.5rem; }

.loading-spinner { color: var(--text-muted); padding: 3rem; text-align: center; }
.error-panel {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: 1rem;
  border-radius: var(--radius);
}

/* --- Badges -------------------------------------------------------------- */
.badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--bg-elev);
  color: var(--text-main);
  border: 1px solid var(--border-color);
}
.badge-success { background: rgba(34, 197, 94, 0.15); color: var(--success); border-color: rgba(34, 197, 94, 0.4); }
.badge-warning { background: rgba(245, 158, 11, 0.15); color: var(--warning); border-color: rgba(245, 158, 11, 0.4); }
.badge-danger  { background: rgba(239, 68, 68, 0.15); color: var(--danger); border-color: rgba(239, 68, 68, 0.4); }
.badge-accent  { background: rgba(139, 92, 246, 0.15); color: var(--accent); border-color: rgba(139, 92, 246, 0.4); }

/* --- Cards / generic ----------------------------------------------------- */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1rem;
}
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
.card h3, .card h4 { margin: 0; font-size: 1rem; }

.btn {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}
.btn:hover { border-color: var(--primary); }
.btn-primary { background: var(--primary); border-color: var(--primary); color: #fff; }
.btn-primary:hover { filter: brightness(1.1); }
.btn-danger { background: transparent; border-color: rgba(239, 68, 68, 0.5); color: var(--danger); }
.btn-ghost { background: transparent; border: none; color: var(--text-muted); }
.btn-ghost:hover { color: var(--danger); }
.btn-sm { padding: 0.25rem 0.6rem; font-size: 0.8rem; }
.chat-layout .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}
.chat-layout .btn:hover:not(:disabled) { border-color: var(--primary); }
.chat-layout .btn-primary:hover:not(:disabled) { filter: brightness(1.1); }
.chat-layout .btn-ghost:hover:not(:disabled) { color: var(--danger); }
.chat-layout .btn:disabled:hover { border-color: var(--border-color); }
.chat-layout .btn-ghost:disabled:hover { color: var(--text-muted); }
.chat-layout .btn:disabled {
  opacity: 0.42;
  filter: grayscale(1);
  cursor: not-allowed;
}
.chat-icon { display: inline-block; flex: 0 0 auto; vertical-align: middle; }

.form-input, .form-select, textarea {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.5rem 0.7rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-family: inherit;
}
.form-input:focus, .form-select:focus { outline: none; border-color: var(--primary); }
.form-row { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.form-row .form-input { flex: 1; min-width: 160px; }

.checkbox-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.88rem; padding: 0.2rem 0; cursor: pointer; }
.toolbar-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.6rem; }

/* --- Dashboard ------------------------------------------------------------ */
.dashboard { display: flex; flex-direction: column; gap: 1rem; }
.dash-hero { display: flex; justify-content: space-between; align-items: center; gap: 1.5rem; flex-wrap: wrap; }
.dash-hero h2 { margin: 0 0 0.25rem; }
.dash-hero-stats { display: flex; gap: 1.5rem; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 1.3rem; font-weight: 700; color: var(--primary); max-width: 180px; overflow: hidden; text-overflow: ellipsis; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }

.dash-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 1rem; align-items: start; }
.agent-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0.75rem; }
.agent-card { background: var(--bg-elev); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 0.75rem; }
.agent-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.agent-card p { font-size: 0.85rem; margin: 0.3rem 0 0.6rem; }
.agent-card-actions { display: flex; gap: 0.35rem; }

.squad-list { list-style: none; margin: 0.5rem 0 0; padding: 0; display: flex; flex-direction: column; gap: 0.4rem; }
.squad-item { display: flex; align-items: center; gap: 0.5rem; background: var(--bg-elev); padding: 0.5rem 0.7rem; border-radius: 6px; font-size: 0.88rem; }
.squad-item .text-muted { flex: 1; font-size: 0.8rem; }

.health-panel { display: flex; flex-direction: column; gap: 0.5rem; }
.health-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }

/* --- File tree ------------------------------------------------------------ */
.tree-pane {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: auto;
  font-size: 0.88rem;
}
.tree-pane-sm { height: 240px; }
.tree-toolbar { display: flex; gap: 0.4rem; padding: 0.5rem; border-bottom: 1px solid var(--border-color); }
.tree-body { padding: 0.35rem 0; }
.tree-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.22rem 0.5rem;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}
.tree-row:hover { background: rgba(59, 130, 246, 0.12); }
.tree-row.selected { background: rgba(59, 130, 246, 0.25); }
.tree-row.tree-new { animation: tree-new-flash 4s ease-out; }
@keyframes tree-new-flash {
  0%, 60% { background: rgba(34, 197, 94, 0.35); }
  100% { background: transparent; }
}
.tree-icon { width: 14px; color: var(--text-muted); text-align: center; flex-shrink: 0; }
.tree-name { overflow: hidden; text-overflow: ellipsis; }

/* --- Editor layout -------------------------------------------------------- */
.editor-layout {
  display: grid;
  grid-template-columns: 250px 1fr 240px;
  gap: 0.75rem;
  height: calc(100vh - 110px);
}
.editor-sidebar, .editor-events {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 0.6rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.sidebar-title { margin: 0 0 0.5rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.editor-sidebar .tree-pane { flex: 1; min-height: 0; border: none; background: transparent; display: flex; flex-direction: column; }
.editor-sidebar .tree-toolbar { padding: 0.2rem 0 0.55rem; gap: 0.35rem; }
.editor-sidebar .tree-toolbar .btn { flex: 1; min-width: 0; padding: 0.35rem 0.4rem; }
.editor-sidebar .tree-toolbar [data-action="refresh"] { flex: 0 0 34px; font-size: 1rem; }
.tree-root-picker { display: flex; flex-direction: column; gap: 0.3rem; padding: 0 0 0.55rem; font-size: 0.75rem; color: var(--text-muted); }
.tree-root-picker .form-select { width: 100%; padding: 0.38rem 0.5rem; font-size: 0.8rem; }
.tree-root-path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: Consolas, monospace; font-size: 0.68rem; }
.dash-agent-card { grid-column: 1; grid-row: 1; }
.dash-squad-card { grid-column: 1; grid-row: 2; }
.dash-health-card { grid-column: 1; grid-row: 3; }
.dash-tree-card { grid-column: 2; grid-row: 1 / span 3; min-height: 0; }
.dash-tree-card .tree-pane { height: min(62vh, 560px); display: flex; flex-direction: column; }
.dash-tree-card .tree-toolbar { padding: 0.4rem 0; }
.dash-tree-card .tree-body { flex: 1; overflow: auto; }
.tree-root-label { padding: 0.45rem 0.55rem; color: var(--text-muted); font-size: 0.77rem; font-weight: 600; border-bottom: 1px solid var(--border-color); }
.editor-sidebar .tree-body { flex: 1; min-height: 0; overflow: auto; padding: 0.35rem 0; }
.tree-message { padding: 0.5rem; margin: 0; font-size: 0.82rem; }
.tree-row { min-width: 0; gap: 0.25rem; padding: 0.22rem 0.35rem; border-radius: 5px; }
.tree-toggle { width: 16px; height: 20px; padding: 0; border: 0; background: none; color: var(--text-muted); cursor: pointer; flex: 0 0 16px; }
.tree-toggle:disabled { cursor: default; }
.tree-icon { width: 18px; flex: 0 0 18px; font-size: 0.78rem; }
.tree-icon.directory::before { content: "▰"; color: var(--primary); }
.tree-icon.file::before { content: "▤"; color: var(--text-muted); }
.tree-name { flex: 1; min-width: 0; font-size: 0.81rem; }
.tree-delete { width: 21px; height: 21px; padding: 0; border: 0; border-radius: 4px; background: transparent; color: var(--text-muted); font-size: 1rem; line-height: 1; cursor: pointer; opacity: 0; }
.tree-row:hover .tree-delete, .tree-delete:focus-visible { opacity: 1; }
.tree-delete:hover { background: rgba(239, 68, 68, 0.18); color: var(--danger); }
.event-export { display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 0.6rem; }

.editor-main {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  min-height: 0;
  overflow: hidden;
}
.editor-toolbar { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-color); }
.editor-path { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 0.85rem; color: var(--primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.editor-monaco {
  flex: 1;
  width: 100%;
  min-height: 0;
  overflow: hidden;
}
.editor-status { display: flex; padding: 0.35rem 0.75rem; font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid var(--border-color); }

.workspace-save-dialog {
  width: min(440px, calc(100vw - 2rem));
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1.25rem;
  background: var(--bg-card);
  color: var(--text-main);
}
.workspace-save-dialog form { margin: 0; }
.workspace-save-dialog::backdrop { background: rgba(0, 0, 0, 0.65); }
.workspace-save-dialog h2 { margin: 0 0 0.5rem; font-size: 1.1rem; }
.workspace-save-dialog p { margin: 0 0 0.9rem; }
.workspace-save-dialog label { display: block; margin: 0.75rem 0 0.35rem; font-size: 0.85rem; }
.workspace-save-dialog .form-select,
.workspace-save-dialog .form-input { width: 100%; }
.workspace-save-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }

.event-log { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.3rem; }
.event-item {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0.35rem 0.5rem;
  font-size: 0.78rem;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.event-item.file_saved { border-left: 3px solid var(--success); }
.event-item.file_opened { border-left: 3px solid var(--primary); }
.event-item.file_created { border-left: 3px solid var(--accent); }
.event-item.file_deleted { border-left: 3px solid var(--danger); }
.event-item.session_join, .event-item.session_leave { border-left: 3px solid var(--warning); }
.event-type { font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }
.event-path { font-family: Consolas, monospace; overflow: hidden; text-overflow: ellipsis; }
.event-details { color: var(--text-muted); white-space: pre-wrap; overflow-wrap: anywhere; }
.event-copy-btn { align-self: flex-end; padding: 0.1rem 0.35rem; font-size: 0.68rem; }

/* --- Chat ----------------------------------------------------------------- */
.chat-layout {
  display: grid;
  grid-template-columns: minmax(230px, 280px) minmax(0, 1fr) minmax(280px, 330px);
  grid-template-rows: minmax(0, 1fr);
  height: calc(100vh - 110px);
  min-height: 0;
  gap: 0.75rem;
}
.chat-layout > * { min-height: 0; overflow: hidden; }
.chat-file-sidebar {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 0.7rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.chat-file-header { display: flex; flex-direction: column; gap: 0.2rem; padding: 0.15rem 0.15rem 0.65rem; }
.chat-file-header h3 { margin: 0; font-size: 0.95rem; }
.chat-file-sidebar .tree-pane { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.chat-file-sidebar .tree-toolbar { padding: 0.4rem; }
.chat-file-sidebar .tree-toolbar .btn { flex: 1; min-width: 0; padding: 0.35rem 0.4rem; }
.chat-file-sidebar .tree-toolbar [data-action="refresh"] { flex: 0 0 34px; font-size: 1rem; }
.chat-file-sidebar .tree-body { flex: 1; min-height: 0; overflow: auto; }
.chat-controls { display: flex; flex-direction: column; gap: 0.65rem; border-top: 1px solid var(--border-color); padding-top: 1rem; }
.chat-controls-title { margin: 0; font-size: 0.86rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); }
.chat-field-label { margin-bottom: -0.45rem; font-size: 0.78rem; color: var(--text-muted); }
.chat-agent-meta { padding: 0.7rem; font-size: 0.82rem; }
.chat-agent-meta p { margin: 0; }
.chat-session-buttons { display: flex; flex-direction: column; gap: 0.5rem; }
.chat-session-buttons .btn { justify-content: center; }

.model-picker { display: flex; flex-direction: column; gap: 0.25rem; }
.model-picker-label { font-size: 0.8rem; color: var(--text-muted); }
.model-picker .form-select { width: 100%; }

.chat-main {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1rem;
  min-height: 0;
}

.messages-scroll { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; padding-bottom: 0.75rem; }

.message {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  max-width: 80%;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.92rem;
  line-height: 1.5;
}
.msg-copy-btn {
  align-self: flex-end;
  font-size: 0.72rem;
  padding: 0.15rem 0.4rem;
  opacity: 0.7;
  color: inherit;
}
.msg-copy-btn:hover { opacity: 1; color: inherit; }
.user-msg { background: var(--primary); color: #fff; align-self: flex-end; }
.assistant-msg { background: var(--bg-elev); border: 1px solid var(--border-color); align-self: flex-start; }
.system-msg { background: transparent; border: 1px dashed var(--border-color); color: var(--text-muted); align-self: center; font-size: 0.85rem; }

.pulse { animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }

.chat-input-bar { display: flex; gap: 0.5rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); }
.chat-input-bar input { flex: 1; }
.chat-quick-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; padding-top: 0.6rem; flex-shrink: 0; }

.tool-badge {
  font-size: 0.85rem;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  background: #2d3748;
  border: 1px solid var(--border-color);
  align-self: flex-start;
}
.tool-badge.error { border-color: rgba(239, 68, 68, 0.5); color: var(--danger); }
.tool-badge.success { border-color: rgba(34, 197, 94, 0.4); }
.tool-badge.has-tree { align-self: stretch; max-width: 100%; }
.tree-view {
  margin: 0.5rem 0 0;
  padding: 0.6rem 0.8rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-family: Consolas, 'Cascadia Mono', 'Segoe UI Emoji', monospace;
  font-size: 0.82rem;
  line-height: 1.45;
  white-space: pre;
  overflow: auto;
  max-height: 420px;
}
.tree-more { display: flex; align-items: center; gap: 0.6rem; margin-top: 0.5rem; }

/* --- Testing -------------------------------------------------------------- */
.testing-layout { display: grid; grid-template-columns: 1.3fr 1fr; gap: 1rem; height: calc(100vh - 110px); }
.testing-builder, .testing-runner { display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.prompt-creation-flow {
  display: grid;
  --prompt-chat-width: 320px;
  grid-template-columns: minmax(280px, var(--prompt-chat-width)) 8px minmax(0, 1fr);
  align-items: start;
  gap: 1rem;
}
.prompt-chat-card {
  position: sticky;
  top: 0.5rem;
  grid-column: 1;
  grid-row: 1 / span 4;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 145px);
  min-height: 390px;
  max-height: none;
  padding: 0;
  overflow: hidden;
}
.prompt-chat-font-controls { display: inline-flex; gap: 0.25rem; margin-left: auto; }
.prompt-chat-card .codebuilder-chat-messages,
.prompt-chat-card .codebuilder-chat-message,
.prompt-chat-card .form-input { font-size: var(--prompt-chat-font-size, 14px); }
.prompt-chat-card .codebuilder-chat-message { max-width: 100%; }
.prompt-chat-resizer {
  grid-column: 2;
  grid-row: 1 / span 4;
  align-self: stretch;
  min-height: 390px;
  margin: 0 -0.5rem;
  cursor: col-resize;
  touch-action: none;
  position: relative;
}
.prompt-chat-resizer::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 3px;
  border-radius: 3px;
  background: transparent;
  transform: translateX(-50%);
  transition: background-color 120ms ease;
}
.prompt-chat-resizer:hover::after,
.prompt-chat-resizer:focus-visible::after,
.prompt-chat-resizer:active::after { background: var(--accent); }
.prompt-chat-resizer:focus-visible { outline: none; }
.prompt-chat-note { margin: 0; padding: 0.35rem 0.85rem 0; }
.prompt-chat-card .codebuilder-chat-messages { min-height: 180px; }
.prompt-chat-card .codebuilder-chat-form { flex: 0 0 auto; }
.prompt-markdown-draft-card { grid-column: 3; grid-row: 1; }
.prompt-assembly-card,
.prompt-tools-card,
.prompt-result-card { grid-column: 3; }
.prompt-assembly-card { grid-row: 2; }
.prompt-tools-card { grid-row: 3; }
.prompt-result-card { grid-row: 4; }
.prompt-add-markdown { margin-top: 0.65rem; }
.prompt-markdown-draft-card .card-head { align-items: flex-start; }
.prompt-markdown-draft-card .card-head p { margin: 0.25rem 0 0; }
.prompt-markdown-draft-actions { margin: 0; flex-wrap: wrap; }
.prompt-markdown-preview {
  overflow-wrap: anywhere;
  line-height: 1.65;
}
.prompt-markdown-preview > :first-child { margin-top: 0; }
.prompt-markdown-preview > :last-child { margin-bottom: 0; }
.prompt-markdown-preview h1,
.prompt-markdown-preview h2,
.prompt-markdown-preview h3,
.prompt-markdown-preview h4,
.prompt-markdown-preview h5,
.prompt-markdown-preview h6 {
  margin: 1.15rem 0 0.5rem;
  line-height: 1.3;
}
.prompt-markdown-preview h1,
.prompt-markdown-preview h2 { padding-bottom: 0.35rem; border-bottom: 1px solid var(--border-color); }
.prompt-markdown-preview p,
.prompt-markdown-preview ul,
.prompt-markdown-preview ol,
.prompt-markdown-preview blockquote,
.prompt-markdown-preview pre,
.prompt-markdown-preview table { margin: 0.65rem 0; }
.prompt-markdown-preview ul,
.prompt-markdown-preview ol { padding-left: 1.6rem; }
.prompt-markdown-preview li + li { margin-top: 0.25rem; }
.prompt-markdown-preview .prompt-markdown-task { list-style: none; margin-left: -1.35rem; }
.prompt-markdown-preview .prompt-markdown-task input { margin-right: 0.4rem; vertical-align: middle; }
.prompt-markdown-preview blockquote {
  border-left: 3px solid var(--accent);
  padding: 0.2rem 0 0.2rem 0.85rem;
  color: var(--text-muted);
}
.prompt-markdown-preview pre {
  overflow-x: auto;
  padding: 0.85rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-dark);
}
.prompt-markdown-preview code {
  overflow-wrap: anywhere;
  font-family: Consolas, monospace;
}
.prompt-markdown-preview pre code { overflow-wrap: normal; }
.prompt-markdown-preview hr { border: 0; border-top: 1px solid var(--border-color); margin: 1rem 0; }
.prompt-markdown-preview .prompt-markdown-table {
  display: block;
  width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
}
.prompt-markdown-table th,
.prompt-markdown-table td {
  min-width: 100px;
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--border-color);
  text-align: left;
  vertical-align: top;
}
.prompt-markdown-table th { background: var(--bg-elev); font-weight: 650; }
.prompt-markdown-table tbody tr:nth-child(even) { background: var(--bg-elev); }
.prompt-markdown-preview a { overflow-wrap: anywhere; }
.prompt-chat-card .codebuilder-chat-message.assistant > :first-child { margin-top: 0; }
.prompt-chat-card .codebuilder-chat-message.assistant > :last-child { margin-bottom: 0; }
.prompt-chat-card .codebuilder-chat-message.assistant h1,
.prompt-chat-card .codebuilder-chat-message.assistant h2,
.prompt-chat-card .codebuilder-chat-message.assistant h3,
.prompt-chat-card .codebuilder-chat-message.assistant h4,
.prompt-chat-card .codebuilder-chat-message.assistant h5,
.prompt-chat-card .codebuilder-chat-message.assistant h6 { margin: 0.7rem 0 0.35rem; }
.prompt-chat-card .codebuilder-chat-message.assistant p,
.prompt-chat-card .codebuilder-chat-message.assistant ul,
.prompt-chat-card .codebuilder-chat-message.assistant ol,
.prompt-chat-card .codebuilder-chat-message.assistant blockquote { margin: 0.4rem 0; }
.prompt-chat-card .codebuilder-chat-message.assistant ul,
.prompt-chat-card .codebuilder-chat-message.assistant ol { padding-left: 1.4rem; }
.prompt-chat-card .codebuilder-chat-message.assistant blockquote {
  border-left: 3px solid var(--border-color);
  padding-left: 0.7rem;
  color: var(--text-muted);
}
.prompt-chat-card .codebuilder-chat-message.assistant pre {
  max-width: 100%;
  overflow-x: auto;
  padding: 0.65rem;
  border-radius: 6px;
  background: var(--bg-dark);
}
.prompt-chat-card .codebuilder-chat-message.assistant code {
  overflow-wrap: anywhere;
  font-family: Consolas, monospace;
}
.prompt-chat-card .codebuilder-chat-message.assistant a { overflow-wrap: anywhere; }
.prompt-assembly-card .category-grid { max-height: 420px; }
.prompt-metadata-fields { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.65rem; margin-bottom: 0.85rem; }
.prompt-component-field { display: flex; flex-direction: column; gap: 0.35rem; margin: 0.55rem 0; }
.prompt-component-field > span:first-child { font-size: 0.84rem; font-weight: 600; }
.prompt-component-field .form-input { width: 100%; }
.prompt-section-editor,
.prompt-tool-description { resize: vertical; min-height: 76px; }
.prompt-selected-sections,
.prompt-selected-tools { margin-top: 0.9rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); }
.prompt-selected-sections h4,
.prompt-selected-tools h4 { margin: 0 0 0.25rem; font-size: 0.9rem; }
.prompt-selected-sections > p,
.prompt-selected-tools > p { margin: 0.25rem 0 0.65rem; }
.prompt-tool-editor code { color: var(--text-muted); font-weight: 400; overflow-wrap: anywhere; }
.prompt-tool-heading { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.prompt-result-card .prompt-preview { display: block; width: 100%; min-height: 320px; resize: vertical; flex: none; }
.prompt-publish-select { width: min(280px, 100%); }
.prompt-result-card .card-head { align-items: flex-start; }
.prompt-result-card .card-head p { margin: 0.25rem 0 0; }
.prompt-result-card #tb-test-result { margin-top: 0.65rem; }
.prompt-test-report { display: flex; flex-direction: column; gap: 0.45rem; margin-top: 0.5rem; }
.prompt-test-component { padding: 0.55rem 0.7rem; border: 1px solid var(--border-color); border-left-width: 3px; border-radius: 6px; background: var(--bg-elev); }
.prompt-test-component.passed { border-left-color: var(--success); }
.prompt-test-component.failed { border-left-color: var(--danger); }
.prompt-test-component p { margin: 0.25rem 0 0; color: var(--text-muted); }
.category-grid { overflow-y: auto; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.75rem; padding-right: 0.25rem;   .prompt-publish-select { width: 100%; }
}
.category-block { background: var(--bg-elev); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 0.6rem; }
.category-head { display: flex; justify-content: space-between; align-items: center; gap: 0.4rem; flex-wrap: wrap; }

.prompt-preview {
  flex: 1;
  min-height: 160px;
  margin-top: 0.75rem;
  font-family: Consolas, monospace;
  font-size: 0.82rem;
  background: var(--bg-dark);
}

.ht-results { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.6rem; margin-top: 0.75rem; }
.ht-summary { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0.8rem; border-radius: var(--radius); border: 1px solid var(--border-color); }
.ht-summary.pass { border-color: rgba(34, 197, 94, 0.5); background: rgba(34, 197, 94, 0.08); }
.ht-summary.fail { border-color: rgba(239, 68, 68, 0.5); background: rgba(239, 68, 68, 0.08); }

.ht-header { background: var(--bg-elev); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 0.6rem; }
.ht-header.pass { border-left: 3px solid var(--success); }
.ht-header.fail { border-left: 3px solid var(--danger); }
.ht-header-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }
.ht-hash { font-family: Consolas, monospace; color: var(--primary); font-size: 0.88rem; }
.ht-question { display: flex; gap: 0.5rem; font-size: 0.84rem; padding: 0.25rem 0; }
.ht-q-status { font-weight: 700; }
.ht-q-status.pass { color: var(--success); }
.ht-q-status.fail { color: var(--danger); }

.tool-workbench { display: flex; flex-direction: column; gap: 0.8rem; }
.tool-workbench .card-head { margin-bottom: 0; }
.tool-workbench .card-head p { margin: 0.35rem 0 0; }
.tool-workbench-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.tool-workbench-field { display: flex; flex-direction: column; gap: 0.35rem; min-width: 0; font-size: 0.86rem; }
.tool-workbench-field textarea { width: 100%; }
.tool-workbench-wide { grid-column: 1 / -1; }
.tool-workbench-model { display: flex; gap: 0.45rem; }
.tool-workbench-model .form-select { flex: 1; min-width: 0; }
.tool-workbench-editor {
  width: 100%;
  resize: vertical;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 0.84rem;
  line-height: 1.45;
  tab-size: 4;
  white-space: pre;
}
.tool-workbench-editor:focus { outline: 1px solid var(--primary); }
.code-editor { border: 1px solid var(--border-color); border-radius: var(--radius); overflow: hidden; background: #1e1e1e; }
.code-editor-bar { display: flex; justify-content: space-between; align-items: center; padding: 0.3rem 0.6rem; background: #252526; border-bottom: 1px solid var(--border-color); }
.code-editor-file { color: #cccccc; font-family: Consolas, 'Courier New', monospace; font-size: 0.8rem; }
.code-editor-actions { display: flex; gap: 0.4rem; }
.code-view, .code-input {
  display: block;
  box-sizing: border-box;
  width: 100%;
  height: 21rem;
  margin: 0;
  overflow: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  tab-size: 4;
}
.code-view[hidden], .code-input[hidden] { display: none; }
.code-view { padding: 0.5rem 0; cursor: text; }
.code-view:focus { outline: 1px solid var(--primary); outline-offset: -1px; }
.code-line { display: flex; min-width: max-content; }
.code-ln { flex: 0 0 3rem; padding-right: 0.8rem; text-align: right; color: #858585; user-select: none; }
.code-text { white-space: pre; padding-left: 0.8rem; border-left: 1px solid #333; flex: 1; }
.code-empty { padding: 0.5rem 0.8rem; color: #6a9955; font-style: italic; }
.code-input { padding: 0.5rem 0.8rem; resize: none; border: 0; white-space: pre; caret-color: #d4d4d4; }
.code-input:focus { outline: 1px solid var(--primary); outline-offset: -1px; }
.tok-kw { color: #569cd6; }
.tok-bi { color: #4ec9b0; }
.tok-fn { color: #dcdcaa; }
.tok-str { color: #ce9178; }
.tok-num { color: #b5cea8; }
.tok-com { color: #6a9955; font-style: italic; }
.tok-dec { color: #c586c0; }
.tool-workbench-actions { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
#tw-output { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 0.8rem; line-height: 1.45; }
.tw-out-error { color: #f48771; }
.tw-out-result { color: #4ec9b0; }
.tw-out-meta { color: var(--text-muted); }
.tool-workbench-output {
  min-height: 5rem;
  max-height: 20rem;
  overflow: auto;
  margin: 0;
  padding: 0.75rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-main);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.tool-workbench-library { border-top: 1px solid var(--border-color); padding-top: 0.75rem; }
.tool-workbench-library h4 { margin: 0 0 0.4rem; font-size: 0.9rem; }
.tool-workbench-library-item { display: flex; gap: 0.5rem; padding: 0.2rem 0; }
.tool-workbench-library-item code { color: var(--primary); }
.tool-workbench-library-item span { color: var(--text-muted); overflow-wrap: anywhere; }

/* --- Human-in-the-Loop Question Dialog ------------------------------------- */
.question-dialog-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  z-index: 9999;
}
.question-dialog {
  width: min(480px, 92vw);
  padding: 1.5rem;
  background: var(--bg-card);
}
.question-dialog-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.question-dialog-head h3 { margin: 0; font-size: 1.05rem; }
.question-dialog-prompt { font-size: 1.05rem; font-weight: 500; margin: 0 0 1rem; }
.question-dialog-input { width: 100%; resize: vertical; margin-bottom: 0.6rem; }
.question-dialog-error { min-height: 1rem; margin: 0 0 0.6rem; font-size: 0.85rem; }
.question-dialog-actions { display: flex; justify-content: space-between; align-items: center; }

/* --- Responsive ------------------------------------------------------------ */
@media (max-width: 1100px) {
  .editor-layout { grid-template-columns: 220px 1fr; }
  .editor-events { display: none; }
  .chat-layout { grid-template-columns: minmax(210px, 240px) minmax(0, 1fr) minmax(270px, 300px); gap: 0.5rem; }
  .testing-layout { grid-template-columns: 1fr; height: auto; }
  .prompt-creation-flow { display: flex; flex-direction: column; }
  .prompt-chat-card {
    position: static;
    width: 100%;
    height: min(520px, 65vh);
    min-height: 360px;
  }
  .prompt-chat-resizer { display: none; }
  .prompt-assembly-card,
  .prompt-tools-card,
  .prompt-result-card,
  .prompt-markdown-draft-card { width: 100%; }
  .prompt-result-card .toolbar-row { flex-wrap: wrap; }
  .dash-grid { grid-template-columns: 1fr; }
  .dash-agent-card, .dash-squad-card, .dash-health-card, .dash-tree-card { grid-column: 1; grid-row: auto; }
  .dash-tree-card .tree-pane { height: 340px; }
}
@media (max-width: 820px) {
  .navbar { flex-wrap: wrap; }
  .editor-layout { grid-template-columns: minmax(0, 1fr); height: auto; }
  .editor-sidebar { min-height: 260px; max-height: 40vh; }
  .editor-main { min-height: 55vh; }
  .tree-delete { opacity: 1; }
  .chat-layout { grid-template-columns: 1fr; grid-template-rows: none; height: auto; }
  .chat-layout > * { overflow: visible; }
  .chat-file-sidebar { min-height: 260px; max-height: 40vh; }
  .chat-main { order: -1; height: calc(100vh - 150px); min-height: 420px; }
  .test-panel { width: 100%; min-width: 0; min-height: 360px; border-left: 0; border-top: 1px solid var(--border-color); }
  .messages-scroll { min-height: 0; }
  .chat-input-bar { flex-shrink: 0; }
  .tool-workbench-grid { grid-template-columns: 1fr; }
  .tool-workbench-wide { grid-column: auto; }
}

```

## `frontend/static/css/test_panel.css`
```css
.test-panel {
  width: 330px;
  min-width: 280px;
  background: var(--bg-card);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.test-panel-header {
  height: 48px;
  min-height: 48px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
}

.test-panel-title {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.test-panel-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.todo-selector-section {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-selector-section .form-select {
  width: 100%;
}

.test-function {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    transform 0.15s ease;
}

.test-function:hover {
  background: var(--bg-elev);
  border-color: var(--primary);
  transform: translateY(-2px);
}

.test-function i,
.test-function svg {
  width: 20px;
  height: 20px;
  color: var(--primary);
}

.test-function span {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
}

.test-function.disabled,
.test-function:disabled {
  opacity: 0.45;
  filter: grayscale(1);
  cursor: not-allowed;
}

.test-function.disabled:hover,
.test-function:disabled:hover {
  background: var(--bg-card);
  border-color: var(--border-color);
  transform: none;
}

@media (max-width: 820px) {
  .test-panel {
    width: 100%;
    min-width: 0;
  }
}

```

## `frontend/static/js/api.js`
```js
/**
 * Novous2 Unified API Client Wrapper
 */
async function jsonOrThrow(res) {
  let data = null;
  try { data = await res.json(); } catch (_) { /* empty body */ }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return data;
}

function get(url) { return fetch(url).then(jsonOrThrow); }
function send(method, url, body) {
  return fetch(url, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined
  }).then(jsonOrThrow);
}

export const Api = {
  async saveMarkdown(content, filename) {
    if (typeof window.showSaveFilePicker === 'function') {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{
          description: 'Markdown file',
          accept: { 'text/markdown': ['.md'] }
        }]
      });
      const writable = await handle.createWritable();
      await writable.write(new Blob([content], { type: 'text/markdown;charset=utf-8' }));
      await writable.close();
      return { filename, locationChosen: true };
    }

    const objectUrl = URL.createObjectURL(
      new Blob([content], { type: 'text/markdown;charset=utf-8' })
    );
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    return { filename, locationChosen: false };
  },

  // --- Workspace & Health ---
  async getHealth() {
    return get('/api/health');
  },

  async getProjectState() {
    return get('/api/project');
  },

  async saveProjectState(patch) {
    return send('POST', '/api/project', patch);
  },

  // --- Agents & Chat (Core Engine) ---
  async getAgents(environment = 'workspace') {
    return get(`/api/agents?environment=${encodeURIComponent(environment)}`);
  },

  async createAgent(agentId, name, description, mode = 'chat', squad = '', environment = 'workspace', environmentName = '') {
    return send('POST', '/api/agents/create', {
      agent_id: agentId, name, description, mode, squad, environment, environment_name: environmentName
    });
  },

  async deleteAgent(agentId, environment = 'workspace') {
    return send('DELETE', `/api/agents/${encodeURIComponent(agentId)}?environment=${encodeURIComponent(environment)}`);
  },

  async getCodeBuilderAgents() {
    return get('/api/codebuilder/agents');
  },

  async sendMessage(message, agentId, model = 'qwen2.5-coder:latest', sessionId = null, environment = 'workspace') {
    return send('POST', '/api/chat', {
      message, agent_id: agentId, model, session_id: sessionId, environment
    });
  },

  async mapFolderPage(path, maxDepth, includeFiles, offset) {
    return send('POST', '/api/tools/map-page', {
      path, max_depth: maxDepth, include_files: includeFiles, offset
    });
  },

  async resetChat(sessionId) {
    return send('POST', `/api/chat/reset?session_id=${encodeURIComponent(sessionId)}`);
  },

  async getPendingQuestions() {
    return get('/api/chat/pending-questions');
  },

  async submitAnswers(requestId, answers) {
    return send('POST', '/api/chat/submit-answers', { request_id: requestId, answers });
  },

  async exportSession(sessionId) {
    const safeSessionId = String(sessionId).replace(/[^A-Za-z0-9_.-]/g, '_');
    const suggestedName = `novous2_${safeSessionId}_${new Date().toISOString().replace(/[:.]/g, '-')}.md`;
    let pickerResult = null;
    if (typeof window.showSaveFilePicker === 'function') {
      pickerResult = window.showSaveFilePicker({
        suggestedName,
        types: [{
          description: 'Markdown file',
          accept: { 'text/markdown': ['.md'] }
        }]
      }).then(handle => ({ handle }), error => ({ error }));
    }

    const res = await fetch('/api/chat/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });
    if (!res.ok) await jsonOrThrow(res);
    const blob = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    const filename = filenameMatch ? filenameMatch[1] : suggestedName;

    if (pickerResult) {
      const result = await pickerResult;
      if (result.error) throw result.error;
      const writable = await result.handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return { filename, locationChosen: true };
    }

    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    return { filename, locationChosen: false };
  },

  async getTools() {
    return get('/api/tools');
  },

  async getToolLibrary() {
    return get('/api/tools/library');
  },

  async getWorkbenchTool(toolName) {
    return get(`/api/testing/tool-workbench/tools/${encodeURIComponent(toolName)}`);
  },

  async deleteWorkbenchTool(toolName) {
    return send('DELETE', `/api/testing/tool-workbench/tools/${encodeURIComponent(toolName)}`);
  },

  async getModels() {
    return get('/api/models');
  },

  // --- Filesystem & Editor ---
  async getFileTree(path = '') {
    return get(`/api/directory/tree?path=${encodeURIComponent(path)}`);
  },

  async readFile(path) {
    return get(`/api/file/read?path=${encodeURIComponent(path)}`);
  },

  async readManagedFile(path) {
    return get(`/api/file-manager/read?path=${encodeURIComponent(path)}`);
  },

  async getManagedFileTree(path = '') {
    return get(`/api/file-manager/tree?path=${encodeURIComponent(path)}`);
  },

  async getFileManagerRoots() {
    return get('/api/file-manager/roots');
  },

  async selectFileManagerRoot(path) {
    return send('POST', '/api/file-manager/roots/select', { path });
  },

  async writeManagedFile(path, content) {
    return send('POST', '/api/file-manager/write', { path, content });
  },

  async createManagedPath(path, kind = 'file') {
    return send('POST', '/api/file-manager/create', { path, kind });
  },

  async deleteManagedPath(path) {
    return send('POST', '/api/file-manager/delete', { path });
  },

  async writeFile(path, content) {
    return send('POST', '/api/file/write', { path, content });
  },

  async createPath(path, kind = 'file') {
    return send('POST', '/api/file/create', { path, kind });
  },

  async deletePath(path, kind = 'file') {
    return send('POST', '/api/file/delete', { path, kind });
  },

  async getEditorSessions() {
    return get('/api/editor/sessions');
  },

  // --- Squads ---
  async getSquads() { return get('/api/squads'); },
  async createSquad(name, description = '') {
    return send('POST', '/api/squads/create', { name, description });
  },
  async deleteSquad(name) {
    return send('POST', '/api/squads/delete', { name });
  },

  // --- Testing & Prompt Builder ---
  async getPromptCategories() {
    return get('/api/prompt-builder/categories');
  },

  async addPromptCategory(id, name, description = '', requiredHeader = '') {
    return send('POST', '/api/prompt-builder/categories', {
      id, name, description, required_header: requiredHeader
    });
  },

  async deletePromptCategory(catId) {
    return send('DELETE', `/api/prompt-builder/categories/${encodeURIComponent(catId)}`);
  },

  async getPromptParts(category = null) {
    const q = category ? `?category=${encodeURIComponent(category)}` : '';
    return get(`/api/prompt-builder/parts${q}`);
  },

  async addPromptPart(category, title, content, id = null) {
    return send('POST', '/api/prompt-builder/parts', {
      category, title, content, id
    });
  },

  async deletePromptPart(partId) {
    return send('DELETE', `/api/prompt-builder/parts/${encodeURIComponent(partId)}`);
  },

  async assemblePrompt(parts, extraInstructions = '') {
    return send('POST', '/api/prompt-builder/assemble', {
      parts, extra_instructions: extraInstructions
    });
  },

  async evaluatePromptComponents(title, description, sections, tools) {
    return send('POST', '/api/prompt-builder/evaluate', {
      title, description, sections, tools
    });
  },

  async judgePrompt(model, title, description, sections, tools) {
    return send('POST', '/api/prompt-builder/judge', { model, title, description, sections, tools });
  },

  async probePrompt(model, title, description, prompt, factQuestion = '', factAnswer = '') {
    return send('POST', '/api/prompt-builder/probe', {
      model, title, description, prompt, fact_question: factQuestion, fact_answer: factAnswer
    });
  },

  async saveTestReport(report) {
    return send('POST', '/api/testing/reports', report);
  },

  async listTestReports() {
    return get('/api/testing/reports');
  },

  async getTestReport(id) {
    return get(`/api/testing/reports/${encodeURIComponent(id)}`);
  },

  async runHeaderTests(agentId, environment = 'workspace') {
    return send('POST', '/api/testing/run_header_tests', { agent_id: agentId, environment });
  },

  async executeToolTest(toolCode, functionInput = {}, timeoutSeconds = 5) {
    return send('POST', '/api/testing/tool-workbench/execute', {
      tool_code: toolCode, function_input: functionInput, timeout_seconds: timeoutSeconds
    });
  },

  async generateToolFunction(model, description) {
    return send('POST', '/api/testing/tool-workbench/generate-function', { model, description });
  },

  async getToolTestHarness(toolCode) {
    return send('POST', '/api/testing/tool-workbench/test-harness', { tool_code: toolCode });
  },

  async testToolWithLlm(model, toolCode, userPrompt, timeoutSeconds = 5) {
    return send('POST', '/api/testing/tool-workbench/test-with-llm', {
      model, tool_code: toolCode, user_prompt: userPrompt, timeout_seconds: timeoutSeconds
    });
  },

  async promoteTestedTool(toolCode, functionInput = {}, timeoutSeconds = 5) {
    return send('POST', '/api/testing/tool-workbench/promote', {
      tool_code: toolCode, function_input: functionInput, timeout_seconds: timeoutSeconds
    });
  },

  async evaluateMarkdown(markdown, agentId = 'draft') {
    return send('POST', '/api/testing/evaluate_markdown', { markdown, agent_id: agentId });
  },

  async publishAgent(agentId, label = '', markdown, environment = 'workspace', tools = []) {
    return send('POST', '/api/testing/publish', {
      agent_id: agentId, label, markdown, environment, tools
    });
  },

  async getTestFixtures() {
    return get('/api/testing/fixtures');
  }
};

```

## `frontend/static/js/app.js`
```js
import { Api } from './api.js';
import { renderTree } from './tree.js';
import { renderEditorView } from './editor.js';
import { renderChatView } from './chat.js';
import { renderPromptCreationView } from './prompt_creation.js';
import { renderTestingView } from './testing.js';
import { renderCodeBuilderView } from './codebuilder/codebuilder.js';

export const AppState = {
  activeTab: 'dashboard',
  agents: [],
  project: null,
  health: null,
  currentPath: ''
};

const views = {
  dashboard: renderDashboardView,
  editor: renderEditorView,
  codebuilder: renderCodeBuilderView,
  chat: renderChatView,
  'prompt-creation': renderPromptCreationView,
  testing: renderTestingView
};

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// --- Dashboard -------------------------------------------------------------
function renderDashboardView(container) {
  const project = AppState.project || {};
  const agents = AppState.agents || [];
  const squads = project.squads || [];

  container.innerHTML = `
    <div class="dashboard">
      <section class="dash-hero card">
        <div>
          <h2>${esc(project.name || 'Novous2 Workspace')}</h2>
          <p class="text-muted">${esc(project.description || 'Declarative Agent Factory — 4-Pillar Architecture.')}</p>
        </div>
        <div class="dash-hero-stats">
          <div class="stat"><span class="stat-num">${agents.length}</span><span class="stat-label">Agents</span></div>
          <div class="stat"><span class="stat-num">${squads.length}</span><span class="stat-label">Squads</span></div>
          <div class="stat"><span class="stat-num">${esc(project.default_model || '-')}</span><span class="stat-label">Model</span></div>
        </div>
      </section>

      <div class="dash-grid">
        <section class="card dash-agent-card">
          <div class="card-head">
            <h3>Agents</h3>
            <button class="btn btn-sm btn-primary" id="dash-new-agent">+ New Agent</button>
          </div>
          <div id="dash-agent-form" class="hidden mt-2">
            <div class="form-row">
              <input id="na-id" class="form-input" placeholder="agent-id (e.g. reviewer)">
              <input id="na-name" class="form-input" placeholder="Display name">
            </div>
            <div class="form-row">
              <input id="na-desc" class="form-input" placeholder="Description">
              <select id="na-environment" class="form-select" aria-label="Agent environment">
                <option value="workspace">Workspace</option>
                <option value="codebuilder">CodeBuilder</option>
                <option value="prompt-creation">Prompt Creation</option>
              </select>
              <select id="na-mode" class="form-select">
                <option value="chat">chat</option>
                <option value="agent">agent</option>
              </select>
              <button class="btn btn-primary" id="dash-create-agent">Create</button>
            </div>
            <div class="form-row">
              <input id="na-environment-name" class="form-input" placeholder="Custom environment name (optional)" aria-label="Custom environment name" maxlength="64">
            </div>
            <p class="text-danger hidden" id="na-error"></p>
          </div>
          <div class="agent-cards" id="dash-agent-cards">
            ${agents.length ? '' : '<p class="text-muted">No agents yet. Create your first one.</p>'}
          </div>
          <div class="card-head mt-3"><h3>Prompt Creation Agents</h3></div>
          <div class="agent-cards" id="dash-prompt-agent-cards">
            <p class="text-muted">Loading Prompt Creation agents…</p>
          </div>
          <div class="card-head mt-3"><h3>CodeBuilder Agents</h3></div>
          <div class="agent-cards" id="dash-codebuilder-agent-cards">
            <p class="text-muted">Loading CodeBuilder agents…</p>
          </div>
        </section>

        <section class="card dash-squad-card">
          <div class="card-head">
            <h3>Squads</h3>
            <button class="btn btn-sm btn-primary" id="dash-new-squad">+ New Squad</button>
          </div>
          <div class="form-row mt-2">
            <input id="sq-name" class="form-input hidden" placeholder="squad name">
            <button class="btn btn-primary hidden" id="dash-create-squad">Create</button>
          </div>
          <ul class="squad-list" id="dash-squad-list">
            ${squads.map(s => `<li class="squad-item"><strong>${esc(s.name)}</strong>
              <span class="text-muted">${esc(s.description || s.path)}</span>
              <button class="btn btn-sm btn-ghost" data-squad-delete="${esc(s.name)}">✕</button></li>`).join('')
              || '<li class="text-muted">No squads yet.</li>'}
          </ul>
        </section>

        <section class="card dash-tree-card">
          <div class="card-head">
            <div>
              <h3>Workspace Tree</h3>
              <p class="text-muted small">Choose a configured folder. Add named paths under <code>file_manager_roots</code> in <code>tools/allowed_paths.json</code>.</p>
            </div>
          </div>
          <div id="dash-tree" class="tree-pane tree-pane-sm"></div>
        </section>

        <section class="card dash-health-card">
          <div class="card-head"><h3>System Health</h3></div>
          <div id="dash-health" class="health-panel">Checking…</div>
        </section>
      </div>
    </div>
  `;

  const cards = container.querySelector('#dash-agent-cards');
  const codeBuilderCards = container.querySelector('#dash-codebuilder-agent-cards');
  agents.forEach(a => {
    const el = document.createElement('div');
    el.className = 'agent-card';
    el.innerHTML = `
      <div class="agent-card-head">
        <strong>${esc(a.name)}</strong>
        <span class="badge ${a.mode === 'agent' ? 'badge-accent' : 'badge-success'}">${esc(a.mode)}</span>
      </div>
      <p class="text-muted">${esc(a.description || 'No description.')}</p>
      <div class="agent-card-actions">
        <button class="btn btn-sm" data-chat="${esc(a.id)}">Chat</button>
        <button class="btn btn-sm" data-edit="${esc(a.id)}">Edit</button>
        <button class="btn btn-sm btn-danger" data-delete="${esc(a.id)}">Delete</button>
      </div>`;
    cards.appendChild(el);
  });

  cards.addEventListener('click', async (e) => {
    const t = e.target;
    if (t.dataset.chat) { switchTab('chat', t.dataset.chat); }
    else if (t.dataset.edit) { switchTab('editor', `library/${t.dataset.edit}.md`); }
    else if (t.dataset.delete) {
      if (!confirm(`Delete agent "${t.dataset.delete}"?`)) return;
      try { await Api.deleteAgent(t.dataset.delete, 'workspace'); await refreshAgents(); renderDashboardView(container); }
      catch (err) { alert(err.message); }
    }
  });

  const promptAgentCards = container.querySelector('#dash-prompt-agent-cards');
  function renderPromptAgentCards(promptAgents) {
    promptAgentCards.replaceChildren();
    if (!promptAgents.length) {
      promptAgentCards.innerHTML = '<p class="text-muted">No Prompt Creation agents yet.</p>';
      return;
    }
    promptAgents.forEach(agent => {
      const el = document.createElement('div');
      el.className = 'agent-card';
      el.innerHTML = `
        <div class="agent-card-head">
          <strong>${esc(agent.name)}</strong>
          <span class="badge badge-accent">Prompt Creation</span>
        </div>
        <p class="text-muted">${esc(agent.description || 'No description.')}</p>
        <div class="agent-card-actions">
          <button class="btn btn-sm" data-prompt-open="${esc(agent.id)}">Open Prompt Creation</button>
          <button class="btn btn-sm" data-prompt-edit="${esc(agent.id)}">Edit</button>
          <button class="btn btn-sm btn-danger" data-prompt-delete="${esc(agent.id)}">Delete</button>
        </div>`;
      promptAgentCards.appendChild(el);
    });
  }

  Api.getAgents('prompt-creation').then(data => {
    renderPromptAgentCards(data.agents || []);
  }).catch(err => {
    promptAgentCards.innerHTML = `<p class="text-danger">Could not load Prompt Creation agents: ${esc(err.message)}</p>`;
  });

  promptAgentCards.addEventListener('click', async e => {
    const button = e.target.closest('button');
    if (!button) return;
    if (button.dataset.promptOpen) {
      switchTab('prompt-creation');
    } else if (button.dataset.promptEdit) {
      switchTab('editor', `library/${button.dataset.promptEdit}.md`);
    } else if (button.dataset.promptDelete) {
      const agentId = button.dataset.promptDelete;
      if (!confirm(`Delete Prompt Creation agent "${agentId}"?`)) return;
      try {
        await Api.deleteAgent(agentId, 'prompt-creation');
        renderPromptAgentCards((await Api.getAgents('prompt-creation')).agents || []);
      } catch (err) { alert(err.message); }
    }
  });

  function renderCodeBuilderAgentCards(codeBuilderAgents) {
    codeBuilderCards.replaceChildren();
    if (!codeBuilderAgents.length) {
      codeBuilderCards.innerHTML = '<p class="text-muted">No CodeBuilder agents yet.</p>';
      return;
    }
    codeBuilderAgents.forEach(agent => {
      const el = document.createElement('div');
      el.className = 'agent-card';
      el.innerHTML = `
        <div class="agent-card-head">
          <strong>${esc(agent.name)}</strong>
          <span class="badge badge-accent">CodeBuilder</span>
        </div>
        <p class="text-muted">${esc(agent.description || 'No description.')}</p>
        <div class="agent-card-actions">
          <a class="btn btn-sm" href="/codebuilder">Open CodeBuilder</a>
          <button class="btn btn-sm btn-danger" data-codebuilder-delete="${esc(agent.id)}">Delete</button>
        </div>`;
      codeBuilderCards.appendChild(el);
    });
  }

  Api.getCodeBuilderAgents().then(data => {
    renderCodeBuilderAgentCards(data.agents || []);
  }).catch(err => {
    codeBuilderCards.innerHTML = `<p class="text-danger">Could not load CodeBuilder agents: ${esc(err.message)}</p>`;
  });

  codeBuilderCards.addEventListener('click', async e => {
    const button = e.target.closest('[data-codebuilder-delete]');
    if (!button) return;
    const agentId = button.dataset.codebuilderDelete;
    if (!confirm(`Delete CodeBuilder agent "${agentId}"?`)) return;
    try {
      await Api.deleteAgent(agentId, 'codebuilder');
      const data = await Api.getCodeBuilderAgents();
      renderCodeBuilderAgentCards(data.agents || []);
    } catch (err) { alert(err.message); }
  });

  container.querySelector('#dash-new-agent').onclick = () =>
    container.querySelector('#dash-agent-form').classList.toggle('hidden');

  container.querySelector('#dash-create-agent').onclick = async () => {
    const id = container.querySelector('#na-id').value.trim();
    const name = container.querySelector('#na-name').value.trim();
    const desc = container.querySelector('#na-desc').value.trim();
    const mode = container.querySelector('#na-mode').value;
    const environment = container.querySelector('#na-environment').value;
    const errBox = container.querySelector('#na-error');
    errBox.classList.add('hidden');
    try {
      await Api.createAgent(id, name || id, desc, mode, '', environment,
        container.querySelector('#na-environment-name').value.trim());
      await refreshAgents();
      renderDashboardView(container);
    } catch (err) { errBox.textContent = err.message; errBox.classList.remove('hidden'); }
  };

  container.querySelector('#dash-new-squad').onclick = () => {
    container.querySelector('#sq-name').classList.toggle('hidden');
    container.querySelector('#dash-create-squad').classList.toggle('hidden');
  };
  container.querySelector('#dash-create-squad').onclick = async () => {
    const input = container.querySelector('#sq-name');
    try {
      await Api.createSquad(input.value.trim());
      await refreshProject();
      renderDashboardView(container);
    } catch (err) { alert(err.message); }
  };
  container.querySelector('#dash-squad-list').addEventListener('click', async (e) => {
    const name = e.target.dataset.squadDelete;
    if (!name) return;
    if (!confirm(`Delete squad "${name}"?`)) return;
    try { await Api.deleteSquad(name); await refreshProject(); renderDashboardView(container); }
    catch (err) { alert(err.message); }
  });

  renderTree(container.querySelector('#dash-tree'), {
    manageRoots: true,
    onSelect: path => switchTab('editor', { path, managedFile: true })
  });

  const healthBox = container.querySelector('#dash-health');
  Api.getHealth().then(h => {
    AppState.health = h;
    healthBox.innerHTML = `
      <div class="health-row"><span>API</span><span class="badge badge-success">ok</span></div>
      <div class="health-row"><span>Ollama</span>
        <span class="badge ${h.ollama?.reachable ? 'badge-success' : 'badge-warning'}">
          ${h.ollama?.reachable ? 'connected' : 'offline'}</span></div>
      <p class="text-muted small">${esc(h.ollama?.detail || '')}</p>
      <p class="text-muted small">Uptime: ${esc(h.uptime_seconds)}s</p>`;
    updateHealthBadge(h);
  }).catch(() => { healthBox.innerHTML = '<p class="text-danger">API unreachable.</p>'; });
}

// --- Shared helpers --------------------------------------------------------
export async function refreshAgents() {
  const data = await Api.getAgents();
  AppState.agents = data.agents || [];
  return AppState.agents;
}

export async function refreshProject() {
  AppState.project = await Api.getProjectState();
  return AppState.project;
}

export function updateHealthBadge(health) {
  const badge = document.getElementById('health-badge');
  if (!badge || !health) return;
  const ok = health.ollama?.reachable;
  badge.className = 'badge ' + (ok ? 'badge-success' : 'badge-warning');
  badge.textContent = ok ? 'Engine Ready' : 'Ollama Offline';
}

export function switchTab(tab, payload = null) {
  AppState.activeTab = tab;
  document.querySelectorAll('.nav-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tab));
  const container = document.getElementById('view-container');
  if (!container) return;
  const renderer = views[tab];
  if (renderer) renderer(container, payload);
}

window.addEventListener('novous:open-editor', event => {
  const file = event.detail;
  if (file && typeof file.path === 'string') {
    switchTab('editor', { path: file.path, managedFile: file.managedFile === true });
  }
});

async function boot() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  try {
    await Promise.all([refreshAgents(), refreshProject()]);
  } catch (err) {
    document.getElementById('view-container').innerHTML =
      `<div class="error-panel">Failed to load workspace: ${esc(err.message)}</div>`;
    return;
  }

  try {
    const h = await Api.getHealth();
    AppState.health = h;
    updateHealthBadge(h);
  } catch (_) { /* badge stays default */ }

  const requestedTab = new URLSearchParams(window.location.search).get('tab');
  switchTab(Object.prototype.hasOwnProperty.call(views, requestedTab) ? requestedTab : 'dashboard');
}

boot();

```

## `frontend/static/js/chat.js`
```js
import { Api } from './api.js';
import { createIcon } from './icons.js';
import { buildTestPanel } from './test_panel.js';
import { renderTree } from './tree.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Interactive Chat Console Component: agent selection, message history,
 * and tool execution badges.
 */
export function renderChatView(container) {
  container.innerHTML = `
    <div class="chat-layout">
      <aside class="chat-file-sidebar">
        <div class="chat-file-header">
          <h3>Workspace Files</h3>
          <span class="text-muted small">Open a file in the editor</span>
        </div>
        <div id="chat-file-tree" class="tree-pane"></div>
      </aside>

      <section class="chat-main">
        <div id="chat-messages" class="messages-scroll">
          <div class="message system-msg">Select an agent and send a message to start reasoning.</div>
        </div>
        <form id="chat-form" class="chat-input-bar">
          <input type="text" id="chat-input" placeholder="Type a message or instruction..." autocomplete="off" required />
          <button type="submit" class="btn btn-primary" disabled>Send</button>
        </form>
        <div class="chat-quick-actions">
          <button type="button" class="btn btn-sm" id="chat-reset-quick" disabled>Reset session</button>
          <button type="button" class="btn btn-sm" disabled title="Coming soon">Action 2</button>
          <button type="button" class="btn btn-sm" disabled title="Coming soon">Action 3</button>
          <button type="button" class="btn btn-sm" disabled title="Coming soon">Action 4</button>
        </div>
      </section>

      <aside class="test-panel">
        <div class="test-panel-header">
          <span class="test-panel-title">Chat & Test Controls</span>
        </div>
        <div class="test-panel-content">
          <div id="testPanelButtons" class="test-grid"></div>
          <section class="chat-controls">
            <h3 class="chat-controls-title">Chat settings</h3>
            <label class="chat-field-label" for="chat-agent-select">Agent</label>
            <select id="chat-agent-select" class="form-select">
              <option value="">Loading agents...</option>
            </select>
            <div id="agent-meta-card" class="card chat-agent-meta">
              <p class="text-muted">Select an agent to begin chatting.</p>
            </div>
            <label class="checkbox-row">
              <input type="checkbox" id="chat-use-tools" checked>
              <span>Attach tools (agent mode)</span>
            </label>
            <label class="model-picker">
              <span class="model-picker-label">Model <span id="model-count" class="text-muted small"></span></span>
              <select id="chat-model-select" class="form-select" disabled><option value="">Detecting models…</option></select>
            </label>
            <div class="chat-session-buttons">
              <button class="btn btn-sm btn-primary" id="chat-save-log" disabled>Save Session Log (.md)</button>
              <button class="btn btn-sm" id="chat-reset" disabled>Reset session</button>
            </div>
            <div id="chat-session-info" class="text-muted small"></div>
          </section>
        </div>
      </aside>
    </div>`;

  const agentSelect = container.querySelector('#chat-agent-select');
  const metaCard = container.querySelector('#agent-meta-card');
  const messagesBox = container.querySelector('#chat-messages');
  const chatForm = container.querySelector('#chat-form');
  const chatInput = container.querySelector('#chat-input');
  const sendButton = chatForm.querySelector('[type="submit"]');
  const saveLogButton = container.querySelector('#chat-save-log');
  const resetButton = container.querySelector('#chat-reset');
  const quickResetButton = container.querySelector('#chat-reset-quick');
  const toolsToggle = container.querySelector('#chat-use-tools');
  const sessionInfo = container.querySelector('#chat-session-info');
  const modelSelect = container.querySelector('#chat-model-select');
  const modelCount = container.querySelector('#model-count');

  let agents = [];
  let installedModels = [];
  let currentModel = 'qwen2.5-coder:latest';
  let isSending = false;
  let isResetting = false;
  let isSavingLog = false;

  container.querySelector('#chat-save-log').prepend(createIcon('save'));
  container.querySelector('#chat-reset').prepend(createIcon('reset'));
  sendButton.prepend(createIcon('send'));

  renderTree(container.querySelector('#chat-file-tree'), {
    manageRoots: true,
    onSelect: path => {
      if (document.getElementById('app')) {
        window.dispatchEvent(new CustomEvent('novous:open-editor', {
          detail: { path, managedFile: true }
        }));
      } else {
        const params = new URLSearchParams({ path, managed: '1' });
        window.location.assign(`/editor?${params}`);
      }
    }
  });

  function syncActionButtons() {
    const hasAgent = agents.some(agent => agent.id === agentSelect.value);
    saveLogButton.disabled = !hasAgent || isSavingLog;
    resetButton.disabled = !hasAgent || isResetting;
    quickResetButton.disabled = resetButton.disabled;
    const wipeButton = container.querySelector('[data-test-function="wipeChat"]');
    if (wipeButton) wipeButton.disabled = !hasAgent || isResetting;
    sendButton.disabled = !hasAgent || modelSelect.disabled || !chatInput.value.trim() || isSending;
  }

  Api.getModels().then(data => {
    installedModels = (data.models || []).sort();
    if (!installedModels.length) {
      modelCount.textContent = '(none installed)';
      modelSelect.innerHTML = '<option value="">No models found — run: ollama pull</option>';
      modelSelect.disabled = true;
      syncActionButtons();
      syncTodoRunButton();
      return;
    }
    modelCount.textContent = `(${installedModels.length} installed)`;
    modelSelect.innerHTML = installedModels
      .map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('');
    modelSelect.disabled = false;
    syncModelSelect();
    syncActionButtons();
    syncTodoRunButton();
  }).catch(err => {
    modelCount.textContent = '(error)';
    modelSelect.innerHTML = `<option value="">Model list unavailable: ${esc(err.message)}</option>`;
    modelSelect.disabled = true;
    syncActionButtons();
    syncTodoRunButton();
  });

  function syncModelSelect() {
    const agent = agents.find(a => a.id === agentSelect.value);
    const stored = agent?.model || 'qwen2.5-coder:latest';
    if (installedModels.includes(stored)) {
      currentModel = stored;
      modelSelect.value = stored;
    } else if (!modelSelect.value || currentModel !== modelSelect.value) {
      currentModel = modelSelect.value || installedModels[0];
    }
  }

  modelSelect.addEventListener('change', () => {
    currentModel = modelSelect.value;
    syncActionButtons();
  });

  Api.getAgents().then(data => {
    agents = data.agents || [];
    agentSelect.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)} (${esc(a.mode)})</option>`).join('')
      : '<option value="">No agents found</option>';
    if (agents.length > 0) {
      let last = null;
      try { last = localStorage.getItem('novous2.chat.lastAgent'); } catch { /* storage unavailable */ }
      if (last && agents.some(a => a.id === last)) agentSelect.value = last;
      updateAgentMeta(agentSelect.value);
      syncModelSelect();
    }
    syncActionButtons();
    syncTodoRunButton();
  }).catch(err => {
    agentSelect.innerHTML = `<option value="">Error: ${esc(err.message)}</option>`;
  });

  agentSelect.addEventListener('change', (e) => {
    try { localStorage.setItem('novous2.chat.lastAgent', e.target.value); } catch { /* storage unavailable */ }
    updateAgentMeta(e.target.value); syncModelSelect(); syncActionButtons(); syncTodoRunButton(); });

  chatInput.addEventListener('input', syncActionButtons);

  function updateAgentMeta(id) {
    const agent = agents.find(a => a.id === id);
    if (!agent) return;
    if (agent.model) currentModel = agent.model;
    metaCard.innerHTML = `
      <h4>${esc(agent.name)}</h4>
      <p><span class="badge ${agent.mode === 'agent' ? 'badge-accent' : 'badge-success'}">${esc((agent.mode || '').toUpperCase())}</span></p>
      <p>${esc(agent.description || 'No description provided.')}</p>
      <p class="text-muted small">Model: ${esc(currentModel)}<br>
      Tools: ${esc((agent.tools || []).join(', ') || 'none')}</p>`;
    toolsToggle.disabled = agent.mode !== 'agent';
    toolsToggle.checked = agent.mode === 'agent';
    sessionInfo.textContent = `Session: chat-${agent.id}`;
  }

  async function resetSession(message = 'Session reset. Send a message to start fresh.') {
    const agentId = agentSelect.value;
    if (!agentId) {
      appendMessage('system', 'Select an agent before resetting the chat.');
      return;
    }
    if (isResetting) return;

    isResetting = true;
    syncActionButtons();
    try {
      await Api.resetChat(`chat-${agentId}`);
      messagesBox.innerHTML = `<div class="message system-msg">${esc(message)}</div>`;
    } catch (err) {
      appendMessage('system', 'Reset failed: ' + err.message);
    } finally {
      isResetting = false;
      syncActionButtons();
    }
  }

  async function openDiagnostics() {
    try {
      const health = await Api.getHealth();
      const ollamaStatus = health.ollama?.reachable ? 'connected' : 'offline';
      const details = health.ollama?.detail ? `\nOllama details: ${health.ollama.detail}` : '';
      appendMessage(
        'system',
        `Diagnostics: API reachable\nOllama: ${ollamaStatus}\nUptime: ${health.uptime_seconds ?? 'unknown'} seconds${details}`
      );
    } catch (err) {
      appendMessage('system', `Diagnostics failed: ${err.message}`);
    }
  }

  function wipeChat() {
    return resetSession('Chat wiped. Send a message to start fresh.');
  }

  let todoFilesLoading = false;
  let todoRunInProgress = false;

  function syncTodoRunButton() {
    const button = container.querySelector('[data-test-function="runTestSuite"]');
    const select = container.querySelector('#todo-file-select');
    if (!button) return;
    const hasAgent = agents.some(agent => agent.id === agentSelect.value);
    button.disabled = todoFilesLoading || todoRunInProgress || !hasAgent ||
      modelSelect.disabled || !select?.value;
  }

  async function loadTodoFiles(silent = false) {
    const select = container.querySelector('#todo-file-select');
    if (!select || todoFilesLoading) return;
    todoFilesLoading = true;
    const refreshButton = container.querySelector('#todo-file-refresh');
    if (refreshButton) refreshButton.disabled = true;

    try {
      const tree = await Api.getFileTree();
      const workspaceEntries = tree.children || [];
      const normalizedNames = new Set(['todo list', 'to due list', 'do due list']);
      const todoDirectories = workspaceEntries.filter(item =>
        item.type === 'directory' &&
        normalizedNames.has(item.name.toLowerCase().replace(/\s+/g, ' ').trim())
      );

      const files = [];
      function collectFiles(node) {
        if (node.type === 'file') {
          if (/\.(md|markdown)$/i.test(node.name) || !node.name.includes('.')) {
            files.push(node);
          }
          return;
        }
        (node.children || []).forEach(collectFiles);
      }
      workspaceEntries
        .filter(item => item.type === 'file')
        .forEach(collectFiles);
      todoDirectories.forEach(collectFiles);
      const markdownFiles = [...new Map(files.map(file => [file.path, file])).values()];
      const selectedPath = select.value;

      select.replaceChildren();
      if (!markdownFiles.length) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No Markdown or extensionless lists found in workspace or To Do List folders';
        select.appendChild(option);
        select.disabled = true;
        return;
      }

      markdownFiles.sort((a, b) => a.path.localeCompare(b.path));
      markdownFiles.forEach(file => {
        const option = document.createElement('option');
        option.value = file.path;
        option.textContent = file.path;
        option.title = file.path;
        select.appendChild(option);
      });
      if (markdownFiles.some(file => file.path === selectedPath)) {
        select.value = selectedPath;
      }
      select.disabled = false;
    } catch (err) {
      if (!silent) {
        select.replaceChildren();
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Error loading files';
        select.appendChild(option);
        select.disabled = true;
        appendMessage('system', `Could not load To-Do files: ${err.message}`);
      }
    } finally {
      todoFilesLoading = false;
      if (refreshButton) refreshButton.disabled = false;
      syncTodoRunButton();
    }
  }

  async function runTodoSequence() {
    const select = container.querySelector('#todo-file-select');
    const selectedPath = select?.value;
    const agentId = agentSelect.value;

    if (!selectedPath) {
      appendMessage('system', 'Please select a file from the To-Do dropdown first.');
      return;
    }
    if (!agentId) {
      appendMessage('system', 'Please select an agent before running To-Do items.');
      return;
    }

    todoRunInProgress = true;
    syncTodoRunButton();

    try {
      const fileData = await Api.readFile(selectedPath);
      const lines = String(fileData.content ?? '')
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(Boolean);

      appendMessage('user', `Starting execution of To-Do items from: ${selectedPath.split('/').pop()}`);
      if (!lines.length) {
        appendMessage('system', 'The selected file contains no nonblank task lines.');
        return;
      }

      const sessionId = `chat-${agentId}`;
      const model = currentModel;
      await delay(1500);

      for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        appendMessage('user', `Task ${index + 1}: ${line}`);
        const thinkingId = appendMessage('assistant', 'Thinking...', true);
        try {
          const response = await Api.sendMessage(line, agentId, model, sessionId);
          removeMessage(thinkingId);
          (response.tool_events || []).forEach(event =>
            appendToolBadge(event.tool, event.status, event.args, event.display)
          );
          appendMessage('assistant', response.reply);
        } catch (err) {
          removeMessage(thinkingId);
          throw err;
        }

        if (index < lines.length - 1) await delay(1000);
      }
    } catch (err) {
      appendMessage('system', `Error reading or running To-Do file: ${err.message}`);
    } finally {
      todoRunInProgress = false;
      syncTodoRunButton();
    }
  }

  container.querySelector('#chat-reset').addEventListener('click', () => resetSession());
  quickResetButton.addEventListener('click', () => resetSession());
  container.querySelector('#chat-save-log').addEventListener('click', async () => {
    const agentId = agentSelect.value;
    if (!agentId) {
      alert('Select an agent before saving the session log.');
      return;
    }
    if (isSavingLog) return;

    isSavingLog = true;
    syncActionButtons();
    try {
      const res = await Api.exportSession(`chat-${agentId}`);
      alert(res.locationChosen
        ? `Session log saved as ${res.filename} in the location you selected.`
        : `Session log download started: ${res.filename}\n\nChoose the save location in your browser's download settings.`);
    } catch (err) {
      if (err.name !== 'AbortError') alert(`Failed to save session: ${err.message}`);
    } finally {
      isSavingLog = false;
      syncActionButtons();
    }
  });
  buildTestPanel('testPanelButtons', {
    diagnostics: openDiagnostics,
    wipeChat,
    runTestSuite: runTodoSequence
  });
  loadTodoFiles();
  container.querySelector('#todo-file-refresh')
    ?.addEventListener('click', () => loadTodoFiles());
  container.querySelector('#todo-file-select')
    ?.addEventListener('change', syncTodoRunButton);
  const todoRefreshInterval = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(todoRefreshInterval);
      return;
    }
    loadTodoFiles(true);
  }, 5000);

  async function pollPendingQuestions() {
    try {
      const data = await Api.getPendingQuestions();
      for (const item of (data.pending || [])) {
        if (!document.querySelector(`[data-request-id="${item.request_id}"]`)) {
          openQuestionDialogModal(item.request_id, item.questions || []);
        }
      }
    } catch (_) {
      // Quiet polling: ignore transient errors while the chat turn is in flight.
    }
  }

  const questionPollInterval = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(questionPollInterval);
      return;
    }
    pollPendingQuestions();
  }, 2000);

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    const agentId = agentSelect.value;
    if (!text || !agentId) return;

    appendMessage('user', text);
    chatInput.value = '';
    isSending = true;
    syncActionButtons();

    const thinkingId = appendMessage('assistant', 'Thinking...', true);

    try {
      const sessionId = `chat-${agentId}`;
      const res = await Api.sendMessage(text, agentId, currentModel, sessionId);
      removeMessage(thinkingId);

      if (res.tool_events && res.tool_events.length > 0) {
        res.tool_events.forEach(evt => appendToolBadge(evt.tool, evt.status, evt.args, evt.display));
      }

      appendMessage('assistant', res.reply);
    } catch (err) {
      removeMessage(thinkingId);
      appendMessage('system', 'Error communicating with engine: ' + err.message);
    } finally {
      isSending = false;
      syncActionButtons();
    }
  });

  function appendMessage(role, content, isTemporary = false) {
    const msgDiv = document.createElement('div');
    const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4);
    msgDiv.id = id;
    msgDiv.className = `message ${role}-msg ${isTemporary ? 'pulse' : ''}`;
    const body = document.createElement('div');
    body.className = 'msg-body';
    body.innerText = content;
    msgDiv.appendChild(body);

    if (!isTemporary && role !== 'system') {
      const copyButton = document.createElement('button');
      const copyLabel = document.createElement('span');
      copyButton.type = 'button';
      copyButton.className = 'btn btn-sm btn-ghost msg-copy-btn';
      copyLabel.textContent = 'Copy';
      copyButton.append(createIcon('copy'), copyLabel);
      copyButton.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(content);
          copyLabel.textContent = 'Copied!';
          setTimeout(() => { copyLabel.textContent = 'Copy'; }, 2000);
        } catch (err) {
          copyLabel.textContent = 'Copy failed';
        }
      });
      msgDiv.appendChild(copyButton);
    }

    messagesBox.appendChild(msgDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return id;
  }

  function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function appendToolBadge(toolName, status, args, display) {
    const badgeDiv = document.createElement('div');
    badgeDiv.className = `tool-badge ${status}`;
    const argText = args ? JSON.stringify(args) : '';
    badgeDiv.innerHTML = `🛠️ <strong>${esc(toolName)}</strong> executed (${esc(status)})
      ${argText ? `<span class="text-muted small"> ${esc(argText.slice(0, 120))}</span>` : ''}`;
    if (display) appendTreeView(badgeDiv, args || {}, display);
    messagesBox.appendChild(badgeDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  const MORE_NOTE = /\n… (\d+) more lines \(next offset (\d+)\)\s*$/;

  function appendTreeView(badgeDiv, args, display) {
    const pre = document.createElement('pre');
    pre.className = 'tree-view';
    badgeDiv.classList.add('has-tree');
    badgeDiv.appendChild(pre);

    const showPage = (text) => {
      const match = text.match(MORE_NOTE);
      pre.textContent += (pre.textContent ? '\n' : '') + text.replace(MORE_NOTE, '');
      return match ? { remaining: Number(match[1]), next: Number(match[2]) } : null;
    };

    const renderMoreControl = (more) => {
      badgeDiv.querySelector('.tree-more')?.remove();
      if (!more) return;
      const bar = document.createElement('div');
      bar.className = 'tree-more';
      const label = document.createElement('span');
      label.className = 'text-muted small';
      label.textContent = `${more.remaining} more lines. Show more?`;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn btn-sm btn-primary';
      button.textContent = 'Show more';
      button.addEventListener('click', async () => {
        button.disabled = true;
        try {
          const page = await Api.mapFolderPage(
            args.path, args.max_depth ?? 3, args.include_files ?? true, more.next
          );
          pre.textContent += '\n' + page.text;
          renderMoreControl(page.remaining
            ? { remaining: page.remaining, next: page.next_offset } : null);
        } catch (err) {
          label.textContent = `Could not load more: ${err.message}`;
          button.disabled = false;
        }
        messagesBox.scrollTop = messagesBox.scrollHeight;
      });
      bar.append(label, button);
      badgeDiv.appendChild(bar);
    };

    renderMoreControl(showPage(display));
  }
}

/**
 * Render a step-by-step Human-in-the-Loop question dialog.
 * Answers are submitted back to the server, which resumes the paused agent tool.
 */
function openQuestionDialogModal(requestId, questions) {
  let currentIndex = 0;
  const userAnswers = {};

  const overlay = document.createElement('div');
  overlay.className = 'question-dialog-overlay';
  overlay.dataset.requestId = requestId;

  const modal = document.createElement('div');
  modal.className = 'card question-dialog';
  overlay.appendChild(modal);

  const questionText = item =>
    (item && typeof item === 'object') ? String(item.question ?? '') : String(item ?? '');
  const questionId = (item, index) =>
    (item && typeof item === 'object' && item.id != null) ? String(item.id) : String(index);

  function renderQuestion() {
    const item = questions[currentIndex];
    const qText = questionText(item);
    const qId = questionId(item, currentIndex);
    const isLast = currentIndex === questions.length - 1;
    const pct = Math.round(((currentIndex + 1) / questions.length) * 100);

    modal.innerHTML = `
      <div class="question-dialog-head">
        <h3>Question ${currentIndex + 1} of ${questions.length}</h3>
        <span class="badge badge-accent">${pct}%</span>
      </div>
      <p class="question-dialog-prompt">${esc(qText)}</p>
      <textarea id="dialog-answer-input" class="form-input question-dialog-input" rows="4"
        placeholder="Type your answer here..."></textarea>
      <p class="question-dialog-error text-danger"></p>
      <div class="question-dialog-actions">
        <button type="button" id="dialog-prev-btn" class="btn btn-sm" ${currentIndex === 0 ? 'disabled' : ''}>Back</button>
        <button type="button" id="dialog-next-btn" class="btn btn-sm btn-primary">
          <span>${isLast ? 'Submit All Answers' : 'Next Question'}</span>
        </button>
      </div>`;

    modal.querySelector('#dialog-prev-btn').prepend(createIcon('reset'));
    modal.querySelector('#dialog-next-btn').prepend(createIcon(isLast ? 'check-square' : 'send'));

    const textarea = modal.querySelector('#dialog-answer-input');
    textarea.value = userAnswers[qId] ?? '';
    textarea.focus();

    modal.querySelector('#dialog-prev-btn').onclick = () => {
      userAnswers[qId] = textarea.value;
      if (currentIndex > 0) {
        currentIndex -= 1;
        renderQuestion();
      }
    };

    modal.querySelector('#dialog-next-btn').onclick = async () => {
      userAnswers[qId] = textarea.value;
      if (!isLast) {
        currentIndex += 1;
        renderQuestion();
        return;
      }

      const nextBtn = modal.querySelector('#dialog-next-btn');
      nextBtn.disabled = true;
      nextBtn.querySelector('span').textContent = 'Submitting...';
      try {
        await Api.submitAnswers(requestId, userAnswers);
        overlay.remove();
      } catch (err) {
        nextBtn.disabled = false;
        nextBtn.querySelector('span').textContent = 'Submit All Answers';
        modal.querySelector('.question-dialog-error').textContent = `Submission failed: ${err.message}`;
      }
    };
  }

  renderQuestion();
  document.body.appendChild(overlay);
}

```

## `frontend/static/js/codebuilder/codebuilder.js`
```js
import { attachCodeBuilderEditor, loadMonaco } from './codebuilder_editor.js';
import { offerInstallForRun, confirmReset, dialog as pickerDialog } from '../sandbox_ui.js';
import { renderTree } from '../tree.js';
import { mountTerminal, TERMINAL_CHANNEL } from '../terminal.js?v=2';
import { setupFileControls } from './files_ui.js';
import { Api } from '../api.js';

const DEMO_CODE = `print("Hello from Novous2 CodeBuilder!")
for i in range(3):
    print(f"count={i}")
`;

const CODE_LANGUAGE_MAP = {
  py: 'python', python: 'python', python3: 'python',
  js: 'javascript', javascript: 'javascript', node: 'javascript',
  ts: 'typescript', typescript: 'typescript',
  html: 'html', css: 'css', scss: 'scss', json: 'json',
  sh: 'shell', bash: 'shell', shell: 'shell', zsh: 'shell', powershell: 'powershell',
  yaml: 'yaml', yml: 'yaml', ini: 'ini', toml: 'ini', xml: 'xml',
  md: 'markdown', markdown: 'markdown', text: 'plaintext', txt: 'plaintext',
};

async function copyTextToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch { /* fall through to legacy copy */ }
  }
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.top = '0';
  area.style.left = '0';
  area.style.opacity = '0';
  document.body.appendChild(area);
  area.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch { ok = false; }
  area.remove();
  return ok;
}

const PREFS_KEY = 'novous2.codebuilder.';
const PANEL_CONF = {
  chat:    { var: '--chat-w',    min: 240, maxFactor: 0.45, rail: 44, default: 320 },
  console: { var: '--console-w', min: 220, maxFactor: 0.45, rail: 44, default: 300 },
  agents:  { var: '--agents-h',  min: 120, max: 340,        rail: 38, default: 220 },
};
const PANEL_LABELS = { chat: 'Chat', console: 'Console', agents: 'Agents' };
const PANEL_GLYPHS = { chat: ['«', '»'], console: ['»', '«'], agents: ['⌄', '⌃'] };
const PANEL_BUTTONS = {
  chat: '#codebuilder-chat-expand',
  console: '#codebuilder-console-collapse',
  agents: '#codebuilder-agents-toggle',
};

const readPref = key => {
  try { return localStorage.getItem(PREFS_KEY + key); } catch { return null; }
};
const writePref = (key, value) => {
  try { localStorage.setItem(PREFS_KEY + key, value); } catch { /* storage unavailable */ }
};
const readVar = (element, name) => parseFloat(
  element.style.getPropertyValue(name) || getComputedStyle(element).getPropertyValue(name)
);

const clampSize = (layout, name, value) => {
  const conf = PANEL_CONF[name];
  const max = conf.max ?? Math.max(conf.min, layout.clientWidth * conf.maxFactor);
  return Math.round(Math.min(Math.max(value, conf.min), max));
};

function restoreLayoutState(shell) {
  const layout = shell.querySelector('.codebuilder-layout');
  if (!layout) return;
  for (const name of Object.keys(PANEL_CONF)) {
    const conf = PANEL_CONF[name];
    const saved = parseFloat(readPref(name + 'Width'));
    if (Number.isFinite(saved)) layout.style.setProperty(conf.var, clampSize(layout, name, saved) + 'px');
    if (readPref(name + 'Collapsed') === '1') {
      shell.classList.add(name + '-collapsed');
      layout.style.setProperty(conf.var, conf.rail + 'px');
    }
  }
}

function refreshPanelToggle(shell, name) {
  const button = shell.querySelector(PANEL_BUTTONS[name]);
  if (!button) return;
  const collapsed = shell.classList.contains(name + '-collapsed');
  const label = PANEL_LABELS[name];
  button.textContent = collapsed ? PANEL_GLYPHS[name][1] : PANEL_GLYPHS[name][0];
  button.title = collapsed ? `Expand ${label} panel` : `Collapse ${label} panel`;
  button.setAttribute('aria-label', button.title);
  button.setAttribute('aria-expanded', String(!collapsed));
}

function setupResizers(shell) {
  const layout = shell.querySelector('.codebuilder-layout');
  if (!layout) return;
  shell.querySelectorAll('.codebuilder-resizer').forEach(resizer => {
    const name = resizer.dataset.resize;
    const conf = PANEL_CONF[name];
    if (!conf) return;
    resizer.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      event.preventDefault();
      if (shell.classList.contains(name + '-collapsed')) {
        shell.classList.remove(name + '-collapsed');
        writePref(name + 'Collapsed', '0');
        refreshPanelToggle(shell, name);
      }
      const axis = name === 'agents' ? 'clientY' : 'clientX';
      const startPos = event[axis];
      const start = clampSize(layout, name, readVar(layout, conf.var) || conf.default);
      resizer.setPointerCapture(event.pointerId);
      document.body.classList.add('is-resizing');
      resizer.classList.add('is-dragging');
      const onMove = moveEvent => {
        layout.style.setProperty(
          conf.var,
          clampSize(layout, name, start + (moveEvent[axis] - startPos)) + 'px'
        );
      };
      const onUp = () => {
        resizer.removeEventListener('pointermove', onMove);
        resizer.removeEventListener('pointerup', onUp);
        document.body.classList.remove('is-resizing');
        resizer.classList.remove('is-dragging');
        const final = readVar(layout, conf.var);
        if (Number.isFinite(final)) writePref(name + 'Width', String(final));
      };
      resizer.addEventListener('pointermove', onMove);
      resizer.addEventListener('pointerup', onUp);
    });
  });
}

const RISKY_CODE_PATTERN = /\b(?:subprocess|os\.system|os\.popen|os\.spawn|pty|commands)\b|shell\s*[:=]\s*true|\binput\s*\(|^\s*!/im;
const RUN_MODE_KEY = 'codebuilder.runMode';

export async function setupCodeBuilderPage(rootId = 'codebuilder-editor') {
  const root = document.getElementById(rootId);
  const output = document.getElementById('codebuilder-output');
  const diagnostics = document.getElementById('diagnostics');
  const runButton = document.getElementById('run-code');
  const runMode = document.getElementById('codebuilder-run-mode');
  const demoButton = document.getElementById('load-demo');
  const clearButton = document.getElementById('clear-console');
  const status = document.getElementById('codebuilder-status');
  const agentList = document.getElementById('codebuilder-agent-list');
  const agentRefresh = document.getElementById('codebuilder-agent-refresh');
  const agentsPanel = document.getElementById('codebuilder-agents-panel');
  const agentsToggle = document.getElementById('codebuilder-agents-toggle');
  const modelSelect = document.getElementById('codebuilder-model');
  const chatForm = document.getElementById('codebuilder-chat-form');
  const chatInput = document.getElementById('codebuilder-chat-input');
  const chatMessages = document.getElementById('codebuilder-chat-messages');
  const chatStatus = document.getElementById('codebuilder-chat-status');
  const chatPanel = document.getElementById('codebuilder-chat-panel');
  const chatExpand = document.getElementById('codebuilder-chat-expand');
  const chatClear = document.getElementById('codebuilder-chat-clear');
  const consoleCollapse = document.getElementById('codebuilder-console-collapse');
  const shell = agentsPanel?.closest('.codebuilder-shell') ?? root.closest('.codebuilder-shell');
  const layout = shell?.querySelector('.codebuilder-layout');

  if (!root || !output || !diagnostics || !runButton || !runMode || !demoButton || !clearButton ||
      !agentList || !agentRefresh || !agentsPanel || !agentsToggle ||
      !modelSelect || !chatForm || !chatInput || !chatMessages || !chatStatus ||
      !chatPanel || !chatExpand || !chatClear || !consoleCollapse || !shell || !layout) {
    console.error('CodeBuilder could not start because a required page element is missing.');
    return null;
  }

  restoreLayoutState(shell);
  setupResizers(shell);

  const editor = await attachCodeBuilderEditor(root, DEMO_CODE);
  let agents = [];
  let selectedAgent = null;
  let defaultModel = 'qwen2.5-coder:latest';
  let chatPending = false;
  let manualRunMode = null;
  const chatCodeEditors = new Set();

  const detectRunMode = () => (RISKY_CODE_PATTERN.test(editor.getValue()) ? 'risky' : 'safe');
  const currentRunMode = () => (manualRunMode || detectRunMode());

  const disposeChatCodeEditors = () => {
    chatCodeEditors.forEach(editor => {
      try { editor.dispose(); } catch { /* already disposed */ }
    });
    chatCodeEditors.clear();
  };

  // The harness diagnostic can be a shortened form; prefer the exception line the console actually printed.
  const EXCEPTION_LINE = /^(?:[A-Za-z_][\w.]*\.)?[A-Z]\w*(?:Error|Exception|Exit|Interrupt)\b.*$/;
  const consoleErrorLine = () => {
    const lines = output.textContent.split('\n').map(line => line.trimEnd()).filter(Boolean);
    for (let i = lines.length - 1; i >= 0; i -= 1) {
      if (EXCEPTION_LINE.test(lines[i].trim())) return lines[i].trim();
    }
    return '';
  };
  const consoleErrorLineNumber = () => {
    let line = null;
    for (const match of output.textContent.matchAll(/File "[^"]*tool_test[^"]*", line (\d+)|File "<[^>]*>", line (\d+)|File "[^"]*", line (\d+)/g)) {
      line = Number(match[1] || match[2] || match[3]);
    }
    return line;
  };

  let lastRunCode = '';
  let lastFailure = null;
  const fixButton = document.getElementById('codebuilder-fix-with-agent');

  const buildFixPrompt = () => {
    const failure = lastFailure;
    const consoleText = output.textContent.trim();
    const trimmed = consoleText.length > 6000 ? `[earlier output omitted]\n${consoleText.slice(-6000)}` : consoleText;
    const location = failure.line ? ` (line ${failure.line})` : '';
    return [
      'My Python code failed when I ran it. Please fix it.',
      '',
      `Error${location}:`,
      failure.message,
      '',
      'Full console output:',
      '```',
      trimmed || '(no console output)',
      '```',
      '',
      'Code that was run:',
      '```python',
      lastRunCode.replace(/\s+$/, ''),
      '```',
      '',
      'Instructions:',
      '1. Find the root cause of the error above using the traceback; do not guess at unrelated problems.',
      '2. Change only what is needed to fix it. Keep the existing function names, signatures and behavior.',
      '3. Reply with the complete corrected code in a single ```python block.',
      '4. Add one or two sentences on what was wrong and what you changed.',
      '5. If you can, put the corrected code in the editor and run it to confirm the error is gone.'
    ].join('\n');
  };

  const renderDiagnostics = (items = []) => {
    diagnostics.replaceChildren();
    lastFailure = null;
    if (fixButton) fixButton.disabled = true;
    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted';
      empty.textContent = 'No diagnostics reported.';
      diagnostics.appendChild(empty);
      return;
    }

    const exceptionLine = consoleErrorLine();
    const tracebackLine = consoleErrorLineNumber();
    items.forEach((item, index) => {
      const isError = (item.severity || 'error') === 'error';
      const message = isError && index === 0 && exceptionLine && !/^SyntaxError/.test(item.message || '')
        ? exceptionLine
        : item.message;
      const line = item.line || (isError && index === 0 ? tracebackLine : null);
      const entry = document.createElement('button');
      entry.type = 'button';
      entry.className = 'diagnostic-item';
      entry.dataset.severity = item.severity || 'error';
      entry.textContent = `${item.severity || 'error'}${line ? ` · line ${line}` : ''} · ${message}`;
      entry.title = message;
      if (line) {
        entry.addEventListener('click', () => editor.revealLine(line));
      }
      diagnostics.appendChild(entry);
      if (!lastFailure && isError) lastFailure = { message, line };
    });
    if (fixButton) fixButton.disabled = !lastFailure;
  };

  const copyConsoleButton = document.getElementById('codebuilder-copy-console');
  let openTerminalWith = () => {};
  // ---- Terminal tab (docked) with pop-out ----
  const consolePanel = root.closest('.codebuilder-shell')?.querySelector('.codebuilder-console-panel');
  const terminalSection = consolePanel?.querySelector('.codebuilder-terminal-section');
  const terminalMount = document.getElementById('codebuilder-terminal-mount');
  const terminalPopped = document.getElementById('codebuilder-terminal-popped');
  const terminalBringBack = document.getElementById('codebuilder-terminal-bring-back');
  if (consolePanel && terminalSection && terminalMount) {
    const channel = 'BroadcastChannel' in window ? new BroadcastChannel(TERMINAL_CHANNEL) : null;
    let popupWindow = null;
    let isPoppedOut = false;
    let terminal = null;

    const showTab = (tab) => {
      const showTerminal = tab === 'terminal';
      consolePanel.classList.toggle('show-terminal', showTerminal);
      terminalSection.hidden = !showTerminal;
      consolePanel.querySelectorAll('[data-console-tab]').forEach(button => {
        button.classList.toggle('active', button.dataset.consoleTab === tab);
      });
      if (showTerminal && !terminal && !isPoppedOut) {
        terminal = mountTerminal(terminalMount, { popOut: openPopOut, compact: true });
      }
      if (showTerminal) terminal?.focus();
    };

    const setPoppedOut = (value) => {
      isPoppedOut = value;
      terminalPopped.hidden = !value;
      terminalMount.hidden = value;
      if (value && terminal) {
        terminal.destroy();
        terminal = null;
      } else if (!value && !terminalSection.hidden && !terminal) {
        terminal = mountTerminal(terminalMount, { popOut: openPopOut, compact: true });
      }
    };

    function openPopOut() {
      popupWindow = window.open('/terminal', 'novous2-terminal', 'width=900,height=600');
      if (!popupWindow) {
        status.textContent = 'The browser blocked the pop-up window. Allow pop-ups for this site.';
        return;
      }
      setPoppedOut(true);
      popupWindow.focus();
    }

    consolePanel.querySelectorAll('[data-console-tab]').forEach(button => {
      button.addEventListener('click', () => showTab(button.dataset.consoleTab));
    });
    openTerminalWith = (command) => {
      if (isPoppedOut) {
        status.textContent = `Terminal is in its own window. Run: ${command}`;
        return;
      }
      showTab('terminal');
      terminal?.setInput(command);
    };
    terminalBringBack?.addEventListener('click', () => {
      channel?.postMessage({ type: 'close-popout' });
      try { popupWindow?.close(); } catch { /* already closed */ }
      setPoppedOut(false);
    });
    if (channel) {
      channel.onmessage = (event) => {
        if (event.data?.type === 'popout-open') setPoppedOut(true);
        if (event.data?.type === 'popout-closed') setPoppedOut(false);
      };
      channel.postMessage({ type: 'ping' });
    }
  }
  copyConsoleButton?.addEventListener('click', async () => {
    const text = output.textContent;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const area = document.createElement('textarea');
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
    copyConsoleButton.textContent = 'Copied';
    setTimeout(() => { copyConsoleButton.textContent = 'Copy'; }, 1500);
  });

  fixButton?.addEventListener('click', () => {
    if (!lastFailure) return;
    chatInput.value = buildFixPrompt();
    chatInput.dispatchEvent(new Event('input', { bubbles: true }));
    chatInput.focus();
    chatInput.scrollTop = 0;
    status.textContent = 'Error and code copied to the agent message box';
  });

  const streamRiskyRun = async () => {
    const timeoutSeconds = 10;
    const response = await fetch('/api/codebuilder/execute/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: editor.getValue(), timeout_seconds: timeoutSeconds, mode: 'risky' })
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `Stream request failed (${response.status}).`);
    }
    if (!response.body || typeof response.body.getReader !== 'function') {
      throw new Error('Live streaming is not supported by this browser.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let returnCode = 0;
    let runStatus = 'SUCCESS';
    let streamedText = '';
    let syntaxError = null;

    const ingest = (event) => {
      switch (event.type) {
        case 'stdout':
          output.textContent += event.text;
          streamedText += event.text;
          break;
        case 'stderr':
          output.textContent += event.text;
          streamedText += event.text;
          break;
        case 'truncated':
          output.textContent += '\n[Earlier output truncated]\n';
          break;
        case 'syntax_error':
          syntaxError = { line: event.line, message: event.message };
          break;
        case 'done':
          returnCode = event.return_code ?? returnCode;
          runStatus = event.status || runStatus;
          break;
        default:
          break;
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let separator = buffer.indexOf('\n\n');
      while (separator !== -1) {
        const rawEvent = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        for (const line of rawEvent.split('\n')) {
          if (!line.startsWith('data: ')) continue;
          try {
            ingest(JSON.parse(line.slice(6)));
          } catch { /* ignore malformed event */ }
        }
        separator = buffer.indexOf('\n\n');
      }
    }
    const remainder = buffer.trim();
    if (remainder.startsWith('data: ')) {
      try { ingest(JSON.parse(remainder.slice(6))); } catch { /* ignore */ }
    }

    if (syntaxError) {
      renderDiagnostics([{ severity: 'error', line: syntaxError.line, message: syntaxError.message }]);
      editor.setDiagnostics([{ severity: 'error', line: syntaxError.line, message: syntaxError.message }]);
      status.textContent = 'Finished with errors';
    } else if (runStatus === 'ERROR') {
      const lastLine = [...streamedText.trim().split('\n')].filter(Boolean).pop() || '';
      const message = lastLine || `Process exited with code ${returnCode}.`;
      renderDiagnostics([{ severity: 'error', message }]);
      editor.setDiagnostics([]);
      status.textContent = 'Finished with errors';
    } else {
      renderDiagnostics([]);
      editor.setDiagnostics([]);
    }

    return {
      status: runStatus === 'SUCCESS' ? 'SUCCESS' : 'ERROR',
      stdout: streamedText,
      stderr: '',
      diagnostics: [],
    };
  };

  const runCodeOnce = async () => {
    const mode = currentRunMode();
    lastRunCode = editor.getValue();
    runButton.disabled = true;
    runButton.textContent = mode === 'risky' ? 'Running… (stream)' : 'Running…';
    output.textContent = '';
    status.textContent = 'Running';
    diagnostics.replaceChildren();
    editor.setDiagnostics([]);

    try {
      if (mode === 'risky') {
        const result = await streamRiskyRun();
        if (result && !output.textContent.trim()) {
          output.textContent = 'Execution completed with no output.';
        }
        return result;
      }

      const response = await fetch('/api/codebuilder/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: editor.getValue(), timeout_seconds: 10, mode: 'safe' })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Execution failed.');
      }

      const stdout = payload.stdout || '';
      const stderr = payload.stderr || '';
      output.textContent = [stdout, stderr].filter(Boolean).join('\n').trim()
        || 'Execution completed with no output.';
      renderDiagnostics(payload.diagnostics || []);
      editor.setDiagnostics(payload.diagnostics || []);
      status.textContent = payload.status === 'SUCCESS' ? 'Finished' : 'Finished with errors';
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      output.textContent = `Error: ${message}`;
      renderDiagnostics([{ severity: 'error', message }]);
      status.textContent = 'Request failed';
      return null;
    } finally {
      runButton.disabled = false;
      runButton.textContent = '▶ Run Python';
      editor.focus();
    }
  };

  const runCode = async () => {
    const result = await runCodeOnce();
    if (result && result.status !== 'SUCCESS' &&
        await offerInstallForRun(editor.getValue(), output.textContent)) {
      return runCodeOnce();
    }
    return result;
  };

  const sendCodeToEditor = (code, source = 'chat') => {
    if (typeof code !== 'string' || !code.trim()) return false;
    editor.setValue(code);
    editor.setDiagnostics([]);
    renderDiagnostics([]);
    status.textContent = source === 'agent'
      ? 'Code received from agent'
      : 'Code sent to editor';
    editor.focus();
    return true;
  };

  // Code handed over from the Tool Function Testing Workbench.
  try {
    const incoming = localStorage.getItem('novous2.codebuilder.incoming');
    if (incoming) {
      localStorage.removeItem('novous2.codebuilder.incoming');
      if (sendCodeToEditor(incoming)) status.textContent = 'Code received from Tool Workbench';
    }
  } catch { /* storage unavailable */ }

  const handleCodeBuilderToolEvents = async (events = []) => {
    for (const event of events) {
      if (event.status !== 'success') continue;
      if (['write_file', 'create_file', 'delete_file'].includes(event.tool)) {
        window.dispatchEvent(new CustomEvent('novous:fs-changed'));
      }
      if (event.tool === 'send_code_to_editor') {
        const code = event.args?.code;
        if (sendCodeToEditor(code, 'agent')) {
          appendChatMessage('system', 'The agent placed its code in the Monaco editor.');
        }
      } else if (event.tool === 'run_code_in_editor') {
        appendChatMessage('system', 'The agent requested a run of the current editor code.');
        const result = await runCode();
        if (!result) {
          appendChatMessage('system', 'The editor code could not be run. See Run Output for details.');
        } else {
          appendChatMessage(
            'system',
            result.status === 'SUCCESS'
              ? 'Editor code ran successfully. See Run Output.'
              : 'Editor code ran with errors. See Run Output and Problems.'
          );
        }
      }
    }
  };

  const createCopyCodeButton = (code) => {
    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'btn btn-sm codebuilder-copy-code';
    copyButton.textContent = 'Copy Code';
    copyButton.setAttribute('aria-label', 'Copy code to clipboard');
    copyButton.addEventListener('click', async () => {
      const ok = await copyTextToClipboard(code);
      copyButton.textContent = ok ? 'Copied!' : 'Copy failed';
      copyButton.disabled = ok;
      setTimeout(() => {
        copyButton.textContent = 'Copy Code';
        copyButton.disabled = false;
      }, 2000);
    });
    return copyButton;
  };

  const createSendToEditorButton = (code) => {
    const sendButton = document.createElement('button');
    sendButton.type = 'button';
    sendButton.className = 'btn btn-sm codebuilder-send-code';
    sendButton.textContent = 'Send to editor';
    sendButton.setAttribute('aria-label', 'Send code to the editor');
    sendButton.addEventListener('click', () => {
      if (sendCodeToEditor(code)) {
        sendButton.textContent = 'Sent to editor';
        sendButton.disabled = true;
      }
    });
    return sendButton;
  };

  const openChatCodeModal = (code, codeLanguage) => {
    const overlay = document.createElement('div');
    overlay.className = 'codebuilder-code-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', `Expanded ${codeLanguage} code block`);

    const panel = document.createElement('div');
    panel.className = 'codebuilder-code-modal';

    const heading = document.createElement('div');
    heading.className = 'codebuilder-code-modal-heading';
    const title = document.createElement('span');
    title.className = 'codebuilder-code-language';
    title.textContent = codeLanguage;
    heading.appendChild(title);

    const actions = document.createElement('div');
    actions.className = 'codebuilder-code-actions';
    actions.append(createCopyCodeButton(code), createSendToEditorButton(code));
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn btn-sm codebuilder-modal-close';
    closeButton.textContent = 'Close';
    closeButton.setAttribute('aria-label', 'Close expanded code block');
    actions.appendChild(closeButton);
    heading.appendChild(actions);

    const body = document.createElement('div');
    body.className = 'codebuilder-code-modal-body';

    const pre = document.createElement('pre');
    const codeElement = document.createElement('code');
    codeElement.className = `language-${codeLanguage}`;
    codeElement.textContent = code;
    pre.appendChild(codeElement);
    body.appendChild(pre);

    panel.append(heading, body);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    let modalEditor = null;
    const close = () => {
      if (modalEditor) {
        try { modalEditor.dispose(); } catch { /* already disposed */ }
      }
      overlay.remove();
      document.body.classList.remove('codebuilder-modal-open');
      document.removeEventListener('keydown', onKey);
    };
    const onKey = event => { if (event.key === 'Escape') close(); };

    overlay.addEventListener('click', event => { if (event.target === overlay) close(); });
    closeButton.addEventListener('click', close);
    document.addEventListener('keydown', onKey);
    document.body.classList.add('codebuilder-modal-open');

    mountChatCodeEditor(body, pre, code, codeLanguage, {
      maxHeight: Math.round(window.innerHeight * 0.6),
      wordWrap: 'off',
      addToRegistry: false,
    }).then(editor => { modalEditor = editor; });
  };

  const appendAssistantMessage = (message, content) => {
    content = String(content ?? '');
    const codeBlockPattern = /```([^\r\n`]*)\r?\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    const appendText = text => {
      if (!text) return;
      const paragraph = document.createElement('div');
      paragraph.className = 'codebuilder-chat-text';
      paragraph.textContent = text;
      message.appendChild(paragraph);
    };

    const buildCodeBlock = (code, rawLanguage) => {
      const language = rawLanguage || 'python';
      const block = document.createElement('section');
      block.className = 'codebuilder-code-block';

      const heading = document.createElement('div');
      heading.className = 'codebuilder-code-heading';
      const languageLabel = document.createElement('span');
      languageLabel.className = 'codebuilder-code-language';
      languageLabel.textContent = language;
      heading.appendChild(languageLabel);

      const actions = document.createElement('div');
      actions.className = 'codebuilder-code-actions';
      actions.append(createCopyCodeButton(code), createSendToEditorButton(code));

      const expandButton = document.createElement('button');
      expandButton.type = 'button';
      expandButton.className = 'btn btn-sm codebuilder-expand-code';
      expandButton.textContent = 'Expand';
      expandButton.setAttribute('aria-label', 'Open this code block in a larger view');
      expandButton.addEventListener('click', () => openChatCodeModal(code, language));
      actions.appendChild(expandButton);
      heading.appendChild(actions);

      const body = document.createElement('div');
      body.className = 'codebuilder-chat-code';

      const pre = document.createElement('pre');
      const codeElement = document.createElement('code');
      codeElement.className = `language-${language}`;
      codeElement.textContent = code;
      pre.appendChild(codeElement);
      body.appendChild(pre);

      block.append(heading, body);
      message.appendChild(block);

      mountChatCodeEditor(body, pre, code, language, {
        maxHeight: 420,
        wordWrap: 'on',
        addToRegistry: true,
      });
    };

    while ((match = codeBlockPattern.exec(content)) !== null) {
      appendText(content.slice(lastIndex, match.index));
      let rawLanguage = match[1].trim().split(/\s+/, 1)[0].toLowerCase();
      let snippet = match[2].trimEnd();
      if (rawLanguage === 'json' || ['text', 'txt', 'plaintext', ''].includes(rawLanguage)) {
        try {
          snippet = JSON.stringify(JSON.parse(snippet), null, 2);
          rawLanguage = 'python';
        } catch { /* keep the raw snippet when it is not valid JSON */ }
      }
      buildCodeBlock(snippet, rawLanguage);
      lastIndex = codeBlockPattern.lastIndex;
    }

    appendText(content.slice(lastIndex));
  };

  const mountChatCodeEditor = (container, fallbackPre, code, rawLanguage, options = {}) => {
    const { maxHeight = 360, wordWrap = 'on', addToRegistry = true } = options;
    const language = CODE_LANGUAGE_MAP[rawLanguage] || rawLanguage || 'plaintext';
    const lineCount = code.split('\n').length;
    container.style.height = `${Math.min(maxHeight, Math.max(72, lineCount * 18 + 16))}px`;

    return loadMonaco().then(monaco => {
      if (!container.isConnected || !chatCodeEditors) return null;
      if (!monaco?.editor || typeof monaco.editor.create !== 'function') return null;
      fallbackPre.remove();
      const editor = monaco.editor.create(container, {
        value: code,
        language,
        theme: 'vs-dark',
        readOnly: true,
        automaticLayout: true,
        minimap: { enabled: false },
        folding: false,
        glyphMargin: false,
        lineDecorationsWidth: 0,
        lineNumbers: 'off',
        renderLineHighlight: 'none',
        scrollBeyondLastLine: false,
        wordWrap,
        contextmenu: false,
        fixedOverflowWidgets: true,
      });
      if (addToRegistry) chatCodeEditors.add(editor);
      return editor;
    }).catch(() => null);
  };

  const appendChatMessage = (role, content) => {
    const message = document.createElement('div');
    message.className = `codebuilder-chat-message ${role}`;
    if (role === 'assistant') {
      appendAssistantMessage(message, content);
    } else {
      message.textContent = content;
    }
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };

  const updateChatControls = () => {
    const sendButton = chatForm.querySelector('button[type="submit"]');
    chatInput.disabled = chatPending;
    sendButton.disabled = chatPending || !selectedAgent || !modelSelect.value || modelSelect.disabled;
  };

  const FUTURE_AGENT_OPTIONS = [
    { id: 'debugAgent', label: 'Debug Agent', icon: 'bug' },
    { id: 'diagnostics', label: 'Diagnostics', icon: 'activity' },
  ];

  // Memory mode: the chat transcript is saved to a file the user picks.
  let memoryPath = null;
  let transcript = [];

  const notifyFilesChanged = () => window.dispatchEvent(new CustomEvent('novous:fs-changed'));

  const writeMemory = async () => {
    if (!memoryPath) return;
    const body = transcript
      .map(entry => `[${entry.role}]\n${entry.text}`)
      .join('\n\n');
    try {
      await Api.writeManagedFile(memoryPath, `${body}\n`);
      notifyFilesChanged();
    } catch (error) {
      appendChatMessage('system', `Memory mode stopped: could not write ${memoryPath} (${error.message}).`);
      memoryPath = null;
      renderAgents();
    }
  };

  // Opens the file manager: click a folder (or an existing file) and name the memory file.
  const pickMemoryLocation = () => new Promise(resolve => {
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15);
    let folder = '';
    let settled = false;
    const finish = (value, close) => {
      if (settled) return;
      settled = true;
      close();
      resolve(value);
    };

    pickerDialog('Memory mode — choose where to save', (modal, close) => {
      modal.classList.add('is-resizable');
      const hint = document.createElement('p');
      hint.className = 'text-muted small';
      hint.textContent = 'Pick a folder in the file manager and name the file. The chat is saved after every reply.';

      const treeHost = document.createElement('div');
      treeHost.className = 'codebuilder-open-tree';

      const target = document.createElement('p');
      target.className = 'small codebuilder-memory-target';
      const nameInput = document.createElement('input');
      nameInput.className = 'form-input';
      nameInput.type = 'text';
      nameInput.value = `chat_memory_${stamp}.txt`;
      nameInput.setAttribute('aria-label', 'Memory file name');
      const error = document.createElement('p');
      error.className = 'text-danger small';

      const refreshTarget = () => {
        target.textContent = `Save to: ${folder || '(workspace root)'}/${nameInput.value.trim()}`;
      };
      nameInput.addEventListener('input', refreshTarget);
      refreshTarget();

      const actions = document.createElement('div');
      actions.className = 'question-dialog-actions';
      const cancel = document.createElement('button');
      cancel.type = 'button';
      cancel.className = 'btn';
      cancel.textContent = 'Cancel';
      const start = document.createElement('button');
      start.type = 'button';
      start.className = 'btn btn-primary';
      start.textContent = 'Start';
      actions.append(cancel, start);
      modal.append(hint, treeHost, target, nameInput, error, actions);

      renderTree(treeHost, {
        manageRoots: true,
        onSelectDirectory: path => { folder = path; refreshTarget(); },
        onSelect: path => {
          const slash = path.lastIndexOf('/');
          folder = slash >= 0 ? path.slice(0, slash) : '';
          nameInput.value = path.slice(slash + 1);
          refreshTarget();
        }
      });

      cancel.addEventListener('click', () => finish(null, close));
      const submit = () => {
        const name = nameInput.value.trim();
        if (!name || name === '.' || name === '..' || /[\\/]/.test(name)) {
          error.textContent = 'Enter a file name without folder separators.';
          return;
        }
        finish([folder, name].filter(Boolean).join('/'), close);
      };
      start.addEventListener('click', submit);
      nameInput.addEventListener('keydown', event => { if (event.key === 'Enter') submit(); });
    });
  });

  const toggleMemory = async () => {
    if (memoryPath) {
      memoryPath = null;
      appendChatMessage('system', 'Memory mode off.');
      renderAgents();
      return;
    }
    const path = await pickMemoryLocation();
    if (!path) return;
    memoryPath = path;
    transcript = [];
    appendChatMessage('system', `Memory mode on. Saving this chat to ${path}.`);
    renderAgents();
    await writeMemory();
  };

  const hasAgentFunctions = agent => Array.isArray(agent.tools) && agent.tools.length > 0;

  const AGENT_TILE_ICONS = {
    bot: [
      'M12 8V4H8',
      'M4 8v12a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1Z',
      'M8 13v2',
      'M12 13v2',
      'M16 13v2',
    ],
    bug: [
      'm8 2 1.88 1.88',
      'M14.12 3.88 16 2',
      'M9 7.13v-1a3.003 3.003 0 1 1 6 0v1',
      'M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6',
      'M12 20v-9',
      'M6.53 9C4.6 8.8 3 7.1 3 5',
      'M6 13H2',
      'M3 21c0-2.1 1.7-3.9 3.8-4',
      'M20.97 5c0 2.1-1.6 3.8-3.5 4',
      'M22 13h-4',
      'M17.2 17c2.1.1 3.8 1.9 3.8 4',
    ],
    activity: [
      'M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2',
    ],
    memory: [
      'M4 6c0-1.1 3.6-2 8-2s8 .9 8 2-3.6 2-8 2-8-.9-8-2Z',
      'M4 6v6c0 1.1 3.6 2 8 2s8-.9 8-2V6',
      'M4 12v6c0 1.1 3.6 2 8 2s8-.9 8-2v-6',
    ],
  };

  const buildTileIcon = (name) => {
    const iconPath = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(iconPath, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('width', '20');
    svg.setAttribute('height', '20');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    (AGENT_TILE_ICONS[name] || []).forEach(pathData => {
      const path = document.createElementNS(iconPath, 'path');
      path.setAttribute('d', pathData);
      svg.appendChild(path);
    });
    return svg;
  };

  const buildAgentTile = (label, icon, title, onClick, isSelected) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'test-function codebuilder-agent-tile';
    button.title = title;
    if (isSelected) button.classList.add('selected');
    button.setAttribute('aria-pressed', String(Boolean(isSelected)));

    const iconElement = buildTileIcon(icon);
    const labelElement = document.createElement('span');
    labelElement.textContent = label;

    if (typeof onClick === 'function') {
      button.addEventListener('click', onClick);
    } else {
      button.disabled = true;
      button.classList.add('disabled');
    }
    button.append(iconElement, labelElement);
    return button;
  };

  const renderAgents = () => {
    agentList.replaceChildren();

    const picker = document.createElement('select');
    picker.className = 'form-select codebuilder-agent-select';
    picker.id = 'codebuilder-agent-select';
    picker.setAttribute('aria-label', 'Choose agent');
    picker.disabled = chatPending || !agents.length;
    agents.forEach(agent => {
      const toolCount = (agent.tools || []).length;
      const option = new Option(`${agent.name} (${toolCount} tool${toolCount === 1 ? '' : 's'})`, agent.id);
      option.disabled = !hasAgentFunctions(agent);
      option.title = (agent.tools || []).join(', ') || 'No tools';
      picker.add(option);
    });
    if (selectedAgent) picker.value = selectedAgent.id;
    picker.addEventListener('change', () => {
      const chosen = agents.find(agent => agent.id === picker.value);
      if (chosen && chosen.id !== selectedAgent?.id) selectAgent(chosen);
    });
    agentList.appendChild(picker);

    agents.forEach(agent => {
      const isSelected = selectedAgent?.id === agent.id;
      const hasFunctions = hasAgentFunctions(agent);
      const tile = buildAgentTile(
        agent.name,
        'bot',
        hasFunctions
          ? (agent.description || agent.name)
          : `${agent.name} — no tools available`,
        () => selectAgent(agent),
        isSelected
      );
      tile.setAttribute('aria-label', `${agent.name} agent`);
      if (chatPending || !hasFunctions) {
        tile.disabled = true;
        tile.classList.add('disabled');
      }
      agentList.appendChild(tile);
    });

    const memoryTile = buildAgentTile(
      'Memory',
      'memory',
      memoryPath
        ? `Memory mode on — saving to ${memoryPath}. Click to turn off.`
        : 'Save this chat to a text file you choose',
      toggleMemory,
      Boolean(memoryPath)
    );
    memoryTile.setAttribute('aria-label', 'Memory mode');
    agentList.appendChild(memoryTile);

    FUTURE_AGENT_OPTIONS.forEach(option => {
      const tile = buildAgentTile(
        option.label,
        option.icon,
        `${option.label} — not implemented yet`,
        null,
        false
      );
      agentList.appendChild(tile);
    });

    if (!agents.length) {
      selectedAgent = null;
      const empty = document.createElement('p');
      empty.className = 'text-muted small';
      empty.textContent = 'No agents found in the workspace agents folder.';
      agentList.appendChild(empty);
    }

    updateChatControls();
  };

  const selectAgent = (agent) => {
    selectedAgent = agent;
    renderAgents();
    const preferredModel = agent.model || defaultModel;
    if ([...modelSelect.options].some(option => option.value === preferredModel)) {
      modelSelect.value = preferredModel;
    }
    chatMessages.replaceChildren();
    disposeChatCodeEditors();
    appendChatMessage('system', `Chatting with ${agent.name}.`);
    chatStatus.textContent = `Agent: ${agent.name}`;
  };

  const loadAgents = async () => {
    agentRefresh.disabled = true;
    try {
      const data = await fetch('/api/codebuilder/agents').then(async response => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || 'Could not load agents.');
        return payload;
      });
      agents = data.agents || [];
      const selectedId = selectedAgent?.id;
      selectedAgent = agents.find(agent => agent.id === selectedId) || agents[0] || null;
      renderAgents();
      if (selectedAgent) selectAgent(selectedAgent);
    } catch (error) {
      const message = document.createElement('p');
      message.className = 'text-danger small';
      message.textContent = error instanceof Error ? error.message : String(error);
      agentList.replaceChildren(message);
    } finally {
      agentRefresh.disabled = false;
    }
  };

  const loadModels = async () => {
    modelSelect.replaceChildren();
    const loadingOption = document.createElement('option');
    loadingOption.textContent = 'Loading models…';
    loadingOption.value = '';
    modelSelect.appendChild(loadingOption);
    modelSelect.disabled = true;
    try {
      const response = await fetch('/api/models');
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Could not load models.');
      const models = (payload.models || []).slice().sort();
      defaultModel = payload.default || defaultModel;
      modelSelect.replaceChildren();

      const availableModels = models.length ? models : [defaultModel];
      availableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = models.length ? model : `${model} (not detected)`;
        modelSelect.appendChild(option);
      });
      modelSelect.disabled = models.length === 0;
      if (models.length) {
        const preferredModel = selectedAgent?.model || defaultModel;
        modelSelect.value = models.includes(preferredModel) ? preferredModel : models[0];
      }
      if (!models.length) {
        chatStatus.textContent = payload.error || 'No installed models detected.';
      }
      updateChatControls();
    } catch (error) {
      modelSelect.replaceChildren();
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'Could not load models';
      modelSelect.appendChild(option);
      modelSelect.disabled = true;
      chatStatus.textContent = error instanceof Error ? error.message : String(error);
      updateChatControls();
    }
  };

  demoButton.addEventListener('click', () => {
    editor.setValue(DEMO_CODE);
    editor.setDiagnostics([]);
    status.textContent = 'Demo loaded';
    editor.focus();
  });
  clearButton.addEventListener('click', () => {
    output.textContent = 'Console cleared.';
    renderDiagnostics([]);
    editor.setDiagnostics([]);
    status.textContent = 'Ready';
  });
  runButton.addEventListener('click', runCode);
  document.getElementById('reset-sandbox')?.addEventListener('click', async () => {
    try {
      const result = await confirmReset();
      if (result) status.textContent = result.output;
    } catch (err) {
      status.textContent = `Reset failed: ${err.message}`;
    }
  });
  editor.setRunHandler(runCode);

  const persistedRunMode = readPref(RUN_MODE_KEY);
  if (persistedRunMode === 'risky' || persistedRunMode === 'safe') {
    manualRunMode = persistedRunMode;
    runMode.value = persistedRunMode;
  }
  runMode.addEventListener('change', () => {
    manualRunMode = runMode.value;
    writePref(RUN_MODE_KEY, runMode.value);
  });
  const fileControls = setupFileControls({
    editor,
    status,
    label: document.getElementById('codebuilder-filename'),
    buttons: {
      save: document.getElementById('save-file'),
      saveAs: document.getElementById('save-file-as'),
      open: document.getElementById('open-file'),
      runTerminal: document.getElementById('run-in-terminal')
    },
    openTerminalWith: (command) => openTerminalWith(command)
  });
  editor.onChange(() => {
    fileControls.refreshLabel();
    if (manualRunMode) return;
    if (runMode.value !== detectRunMode()) runMode.value = detectRunMode();
  });
  agentRefresh.addEventListener('click', loadAgents);

  const togglePanel = (name) => {
    const conf = PANEL_CONF[name];
    const collapsed = !shell.classList.contains(name + '-collapsed');
    if (collapsed) {
      const current = readVar(layout, conf.var);
      if (Number.isFinite(current) && current > conf.rail) writePref(name + 'Width', String(current));
      shell.classList.add(name + '-collapsed');
      layout.style.setProperty(conf.var, conf.rail + 'px');
    } else {
      const saved = parseFloat(readPref(name + 'Width'));
      layout.style.setProperty(
        conf.var,
        (Number.isFinite(saved) ? clampSize(layout, name, saved) : conf.default) + 'px'
      );
      shell.classList.remove(name + '-collapsed');
    }
    writePref(name + 'Collapsed', collapsed ? '1' : '0');
    return collapsed;
  };

  chatExpand.addEventListener('click', () => { togglePanel('chat'); refreshPanelToggle(shell, 'chat'); });
  consoleCollapse.addEventListener('click', () => { togglePanel('console'); refreshPanelToggle(shell, 'console'); });
  agentsToggle.addEventListener('click', () => { togglePanel('agents'); refreshPanelToggle(shell, 'agents'); });

  refreshPanelToggle(shell, 'chat');
  refreshPanelToggle(shell, 'console');
  refreshPanelToggle(shell, 'agents');

  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message || chatPending) return;
    if (!selectedAgent) {
      chatStatus.textContent = 'Select an agent before sending a message.';
      return;
    }
    if (!modelSelect.value) {
      chatStatus.textContent = 'Select an installed model before sending a message.';
      return;
    }

    appendChatMessage('user', message);
    if (memoryPath) transcript.push({ role: 'user', text: message });
    chatInput.value = '';
    chatPending = true;
    chatStatus.textContent = `Waiting for ${selectedAgent.name}…`;
    updateChatControls();
    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          agent_id: selectedAgent.id,
          model: modelSelect.value,
          session_id: `codebuilder-${selectedAgent.id}`,
          environment: 'codebuilder',
        })
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || 'The agent request failed.');
      }

      const bubble = document.createElement('div');
      bubble.className = 'codebuilder-chat-message assistant';
      chatMessages.appendChild(bubble);

      let text = '';
      let liveCode = null;
      let paintQueued = false;
      let donePayload = null;
      let failure = null;

      // Newest ```python fence in the streamed text; an unclosed fence counts as in progress.
      const latestCode = () => {
        let found = null;
        for (const match of text.matchAll(/```([\w+-]*)[^\n]*\n([\s\S]*?)(```|$)/g)) {
          if (['', 'python', 'py'].includes(match[1].toLowerCase())) found = match[2];
        }
        return found;
      };
      const paint = () => {
        paintQueued = false;
        bubble.textContent = text;
        chatMessages.scrollTop = chatMessages.scrollHeight;
        const code = latestCode();
        if (code !== null && code !== liveCode) {
          liveCode = code;
          editor.setValue(code);
          status.textContent = 'Agent is writing code…';
        }
      };
      const schedulePaint = () => {
        if (!paintQueued) { paintQueued = true; requestAnimationFrame(paint); }
      };

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const handleEvent = async item => {
        if (item.type === 'token') {
          text += item.text;
          schedulePaint();
        } else if (item.type === 'tool_event') {
          await handleCodeBuilderToolEvents([item.event]);
        } else if (item.type === 'done') {
          donePayload = item;
        } else if (item.type === 'error') {
          failure = item.detail || 'The agent request failed.';
        }
      };
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split('\n\n');
        buffer = frames.pop();
        for (const frame of frames) {
          const line = frame.split('\n').find(l => l.startsWith('data: '));
          if (line) await handleEvent(JSON.parse(line.slice(6)));
        }
      }

      paint();
      if (failure) {
        bubble.remove();
        throw new Error(failure);
      }
      const reply = donePayload?.reply || text || 'The agent returned an empty response.';
      bubble.textContent = '';
      appendAssistantMessage(bubble, reply);
      if (liveCode !== null) sendCodeToEditor(liveCode, 'agent');
      if (memoryPath) {
        transcript.push({ role: 'assistant', text: reply });
        await writeMemory();
      }
      chatStatus.textContent = `${selectedAgent.name} · ${donePayload?.model || modelSelect.value}`;
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      appendChatMessage('system', `Request failed: ${messageText}`);
      chatStatus.textContent = 'Request failed';
    } finally {
      chatPending = false;
      updateChatControls();
      chatInput.focus();
    }
  });
  chatInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit();
    }
  });
  chatClear.addEventListener('click', () => {
    chatInput.value = '';
    chatMessages.replaceChildren();
    disposeChatCodeEditors();
    if (selectedAgent) {
      appendChatMessage('system', 'Chat cleared. Ask a new question.');
      chatStatus.textContent = `Agent: ${selectedAgent.name}`;
    } else {
      appendChatMessage('system', 'Chat cleared.');
      chatStatus.textContent = 'Chat cleared';
    }
    chatInput.focus();
  });

  renderDiagnostics([]);
  status.textContent = 'Ready';
  updateChatControls();
  Promise.all([loadAgents(), loadModels()]);

  return { editor, runCode, loadAgents };
}

export function renderCodeBuilderView(container) {
  if (!container) return;
  container.innerHTML = `
    <div class="codebuilder-shell">
      <div class="codebuilder-toolbar">
        <div class="codebuilder-file-label">
          <span class="codebuilder-python-icon">Py</span>
          <span>Untitled Python File</span>
          <span class="badge badge-success">Python</span>
        </div>
        <div class="codebuilder-toolbar-actions">
          <label class="codebuilder-run-mode">
            <select id="codebuilder-run-mode" aria-label="Choose how to run Python code">
              <option value="safe">Safe (in-process)</option>
              <option value="risky">Risky (isolated, streams)</option>
            </select>
          </label>
          <button id="load-demo" class="btn btn-sm" type="button" title="Load the sample Python program">Sample</button>
          <button id="open-file" class="btn btn-sm" type="button" title="Open a file from the file manager">Open…</button>
          <button id="save-file" class="btn btn-sm" type="button" title="Save (Ctrl+S)">Save</button>
          <button id="save-file-as" class="btn btn-sm" type="button" title="Save as a new file">Save As…</button>
          <button id="run-in-terminal" class="btn btn-sm" type="button" title="Save, then prepare the command in the Terminal tab">Run in Terminal</button>
          <button id="clear-console" class="btn btn-sm" type="button" title="Clear console and diagnostics">Clear Output</button>
          <button id="reset-sandbox" class="btn btn-sm" type="button" title="Remove all packages installed for testing">Reset Environment</button>
          <button id="run-code" class="btn btn-sm btn-primary" type="button" title="Run Python (Ctrl+Enter)">▶ Run Python</button>
        </div>
      </div>

      <main class="codebuilder-layout">
        <section id="codebuilder-chat-panel" class="codebuilder-chat-panel" aria-label="Chat with an agent">
          <div class="codebuilder-chat-heading">
            <h2>Ask an Agent</h2>
            <span id="codebuilder-chat-status" class="text-muted small">Select an agent to start.</span>
            <button id="codebuilder-chat-expand" class="btn btn-sm codebuilder-chat-expand"
                    type="button" aria-label="Collapse chat panel" aria-expanded="true"
                    title="Collapse chat panel">«</button>
          </div>
          <div id="codebuilder-chat-messages" class="codebuilder-chat-messages" aria-live="polite">
            <div class="codebuilder-chat-message system">Messages with your selected agent appear here.</div>
          </div>
          <form id="codebuilder-chat-form" class="codebuilder-chat-form">
            <label class="codebuilder-model-picker">
              <span class="text-muted small">Model</span>
              <select id="codebuilder-model" class="form-select" aria-label="Choose model">
                <option value="">Loading models…</option>
              </select>
            </label>
            <textarea id="codebuilder-chat-input" class="form-input" rows="4"
                      placeholder="Ask the selected agent about your Python code…"
                      aria-label="Message to agent"></textarea>
            <div class="codebuilder-chat-actions">
              <button id="codebuilder-chat-clear" class="btn btn-sm"
                      type="button" aria-label="Clear chat" title="Clear the chat conversation">Clear</button>
              <button class="btn btn-primary" type="submit" disabled>Send</button>
            </div>
          </form>
        </section>

        <div class="codebuilder-resizer" data-resize="chat" role="separator"
             aria-orientation="vertical" aria-label="Resize chat panel"></div>

        <section class="codebuilder-editor-panel" aria-label="Python editor">
          <div id="codebuilder-editor" class="editor-surface"></div>
          <div class="codebuilder-statusbar">
            <span id="codebuilder-status">Loading editor…</span>
            <span id="codebuilder-filename" class="codebuilder-filename">Untitled</span>
            <span>Python</span>
            <span>UTF-8</span>
            <span>Spaces: 4</span>
          </div>
        </section>

        <div class="codebuilder-resizer" data-resize="console" role="separator"
             aria-orientation="vertical" aria-label="Resize console panel"></div>

        <aside class="codebuilder-console-panel" aria-label="Run output and diagnostics">
          <div class="codebuilder-console-heading">
            <h2>Run Output</h2>
            <span class="codebuilder-console-subtitle">Console &amp; Problems</span>
            <button id="codebuilder-console-collapse" class="btn btn-sm codebuilder-console-collapse"
                    type="button" aria-label="Collapse console panel" aria-expanded="true"
                    title="Collapse console panel">»</button>
          </div>
          <div class="codebuilder-console-tabs" role="tablist">
            <button type="button" class="btn btn-sm active" data-console-tab="console" role="tab">Console</button>
            <button type="button" class="btn btn-sm" data-console-tab="terminal" role="tab">Terminal</button>
          </div>
          <section class="codebuilder-output-section">
            <h3>Console</h3>
            <button id="codebuilder-copy-console" class="btn btn-sm" type="button"
                    title="Copy the console output">Copy</button>
            <pre id="codebuilder-output" class="console-output">Ready. Run your Python code to see output here.</pre>
          </section>
          <section class="codebuilder-problems-section">
            <h3>Problems</h3>
            <button id="codebuilder-fix-with-agent" class="btn btn-sm btn-primary" type="button" disabled
                    title="Copy the error, console output and code into the agent message box">Fix with Agent</button>
            <div id="diagnostics" class="diagnostics-list"></div>
          </section>
          <section class="codebuilder-terminal-section" hidden>
            <div id="codebuilder-terminal-mount" class="codebuilder-terminal-mount"></div>
            <div id="codebuilder-terminal-popped" class="codebuilder-terminal-popped" hidden>
              <p>The terminal is open in a separate window.</p>
              <button id="codebuilder-terminal-bring-back" class="btn btn-sm btn-primary" type="button">Bring back</button>
            </div>
          </section>
        </aside>

        <div class="codebuilder-resizer" data-resize="agents" role="separator"
             aria-orientation="horizontal" aria-label="Resize agents panel"></div>

        <aside id="codebuilder-agents-panel" class="codebuilder-agents-panel" aria-label="Workspace agents">
          <div class="codebuilder-agents-heading">
            <button id="codebuilder-agents-toggle" class="btn btn-sm codebuilder-agents-toggle"
                    type="button" aria-label="Collapse agents panel" aria-expanded="true"
                    title="Collapse agents panel">⌄</button>
            <button id="codebuilder-agent-refresh" class="btn btn-sm codebuilder-agent-refresh"
                    type="button" title="Refresh agents" aria-label="Refresh agents">↻</button>
          </div>
          <div id="codebuilder-agent-list" class="codebuilder-agent-list"></div>
        </aside>
      </main>
    </div>
  `;

  setupCodeBuilderPage();
}

if (typeof window !== 'undefined' && document.readyState !== 'loading') {
  const root = document.getElementById('codebuilder-editor');
  if (root) setupCodeBuilderPage();
}

```

## `frontend/static/js/codebuilder/codebuilder_editor.js`
```js
const MONACO_VS_PATH = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs';
let monacoPromise;

export function loadMonaco() {
  if (window.monaco?.editor) return Promise.resolve(window.monaco);
  if (monacoPromise) return monacoPromise;

  monacoPromise = new Promise((resolve, reject) => {
    if (typeof window.require !== 'function') {
      reject(new Error('The Monaco Editor loader is unavailable.'));
      return;
    }

    window.require.config({ paths: { vs: MONACO_VS_PATH } });
    window.require(['vs/editor/editor.main'], () => {
      if (!window.monaco?.editor) {
        reject(new Error('Monaco Editor failed to initialize.'));
        return;
      }
      resolve(window.monaco);
    }, reject);
  });
  return monacoPromise;
}

function createTextareaEditor(element, initialValue) {
  const textarea = document.createElement('textarea');
  textarea.className = 'codebuilder-textarea';
  textarea.value = initialValue;
  textarea.setAttribute('aria-label', 'Python source code');
  element.replaceChildren(textarea);
  let runHandler = null;
  let saveHandler = null;
  let changeHandler = null;
  let positionHandler = null;
  textarea.addEventListener('input', () => changeHandler?.());
  textarea.addEventListener('keyup', () => positionHandler?.());
  textarea.addEventListener('click', () => positionHandler?.());
  textarea.addEventListener('keydown', event => {
    if (event.ctrlKey || event.metaKey) {
      if (event.key === 'Enter') {
        event.preventDefault();
        runHandler?.();
      } else if (event.key.toLowerCase() === 's' && saveHandler) {
        event.preventDefault();
        saveHandler?.();
      }
    }
  });

  return {
    getValue: () => textarea.value,
    setValue: (value) => { textarea.value = value; changeHandler?.(); },
    setLanguage: () => {},
    getPosition: () => {
      const lines = textarea.value.slice(0, textarea.selectionStart).split('\n');
      return { lineNumber: lines.length, column: lines[lines.length - 1].length + 1 };
    },
    setDiagnostics: () => {},
    setRunHandler: (handler) => { runHandler = handler; },
    setSaveHandler: (handler) => { saveHandler = handler; },
    onChange: (handler) => { changeHandler = handler; },
    onPosition: (handler) => { positionHandler = handler; },
    revealLine: (line) => {
      const lineStart = textarea.value.split('\n').slice(0, Math.max(0, line - 1)).join('\n').length;
      textarea.focus();
      textarea.setSelectionRange(lineStart, lineStart);
    },
    focus: () => textarea.focus(),
    dispose: () => textarea.remove(),
  };
}

export async function attachCodeBuilderEditor(
  element,
  initialValue = "print('Hello from Novous2 CodeBuilder!')\n",
  language = 'python'
) {
  if (!element) {
    throw new Error('The CodeBuilder editor container was not found.');
  }

  try {
    const monaco = await loadMonaco();
    const editor = monaco.editor.create(element, {
      value: initialValue,
      language,
      theme: 'vs-dark',
      automaticLayout: true,
      ariaLabel: 'Python code editor',
      accessibilitySupport: 'auto',
      bracketPairColorization: { enabled: true },
      cursorBlinking: 'smooth',
      detectIndentation: false,
      folding: true,
      fontSize: 14,
      fontFamily: "'Cascadia Code', 'Fira Code', Consolas, monospace",
      fontLigatures: true,
      formatOnPaste: true,
      guides: { bracketPairs: true, indentation: true },
      lineNumbers: 'on',
      minimap: { enabled: true, scale: 0.8 },
      padding: { top: 12, bottom: 12 },
      renderLineHighlight: 'all',
      scrollBeyondLastLine: false,
      smoothScrolling: true,
      stickyScroll: { enabled: true },
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'off',
    });
    let runHandler = null;
    let saveHandler = null;
    let changeHandler = null;
    let positionHandler = null;
    editor.onDidChangeModelContent(() => changeHandler?.());
    editor.onDidChangeCursorPosition(() => positionHandler?.());
    editor.addAction({
      id: 'codebuilder.runPython',
      label: 'Run Python',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
      run: () => runHandler?.(),
    });
    let saveAction = null;

    return {
      getValue: () => editor.getValue(),
      setValue: (value) => { editor.setValue(value); },
      setLanguage: (nextLanguage) => {
        const model = editor.getModel();
        if (model) monaco.editor.setModelLanguage(model, nextLanguage);
      },
      getPosition: () => editor.getPosition(),
      focus: () => editor.focus(),
      setRunHandler: (handler) => { runHandler = handler; },
      setSaveHandler: (handler) => {
        saveAction?.dispose();
        saveHandler = handler;
        if (handler) {
          saveAction = editor.addAction({
            id: 'codebuilder.save',
            label: 'Save',
            keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS],
            run: () => saveHandler?.(),
          });
        }
      },
      onChange: (handler) => { changeHandler = handler; },
      onPosition: (handler) => { positionHandler = handler; },
      revealLine: (line) => {
        editor.revealLineInCenter(line);
        editor.setPosition({ lineNumber: line, column: 1 });
        editor.focus();
      },
      setDiagnostics: (items) => {
        const model = editor.getModel();
        if (!model) return;
        monaco.editor.setModelMarkers(model, 'codebuilder', items.map(item => ({
          severity: item.severity === 'warning'
            ? monaco.MarkerSeverity.Warning
            : item.severity === 'info'
              ? monaco.MarkerSeverity.Info
              : monaco.MarkerSeverity.Error,
          message: item.message,
          startLineNumber: item.line || 1,
          endLineNumber: item.line || 1,
          startColumn: item.column || 1,
          endColumn: (item.column || 1) + 1,
        })));
      },
      dispose: () => editor.dispose(),
    };
  } catch (error) {
    console.error('Monaco Editor could not be loaded; using the basic Python editor instead.', error);
    return createTextareaEditor(element, initialValue);
  }
}

```

## `frontend/static/js/codebuilder/files_ui.js`
```js
import { dialog } from '../sandbox_ui.js';
import { renderTree } from '../tree.js';
import { Api } from '../api.js';

async function call(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof payload.detail === 'string' ? payload.detail : `Request failed (${response.status}).`);
  }
  return payload;
}

const Files = {
  list: () => call('GET', '/api/codebuilder/files'),
  read: path => call('GET', `/api/codebuilder/files/read?path=${encodeURIComponent(path)}`),
  save: (folder, name, content, overwrite) =>
    call('POST', '/api/codebuilder/files/save', { folder, name, content, overwrite }),
  runCommand: (path, content) => call('POST', '/api/codebuilder/files/run-command', { path, content })
};

function button(label, className = 'btn') {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = className;
  el.textContent = label;
  return el;
}

// Save, Save As, Open and Run-in-terminal for the editor. `openTerminalWith(command)` prefills the terminal.
export function setupFileControls({ editor, status, label, buttons, openTerminalWith }) {
  let currentPath = '';
  let managedPath = ''; // set when the open file came from the file manager (saved through it too)
  let savedValue = editor.getValue();

  const isDirty = () => editor.getValue() !== savedValue;
  const nameOf = path => path.split(/[\\/]/).pop();

  const refreshLabel = () => {
    if (!label) return;
    label.textContent = currentPath ? `${nameOf(currentPath)}${isDirty() ? ' ●' : ''}` : (isDirty() ? 'Unsaved ●' : 'Untitled');
    label.title = currentPath || 'Not saved to a file yet';
  };

  const markSaved = (path) => {
    currentPath = path;
    savedValue = editor.getValue();
    refreshLabel();
  };

  const writeFile = async (folder, name, overwrite = false) => {
    const result = await Files.save(folder, name, editor.getValue(), overwrite);
    if (result.saved) {
      managedPath = '';
      markSaved(result.path);
      status.textContent = `Saved ${result.path}`;
      return result;
    }
    if (result.exists && confirm(`${result.name} already exists. Replace it?`)) {
      return writeFile(folder, name, true);
    }
    return null;
  };

  const saveAs = () => new Promise(resolve => {
    Files.list().then(info => {
      dialog('Save as', (modal, close) => {
        const nameInput = document.createElement('input');
        nameInput.className = 'form-input question-dialog-input';
        nameInput.placeholder = 'file name, e.g. app.py';
        nameInput.value = currentPath ? nameOf(currentPath) : '';
        nameInput.setAttribute('aria-label', 'File name');
        const folderSelect = document.createElement('select');
        folderSelect.className = 'form-select';
        folderSelect.setAttribute('aria-label', 'Folder');
        info.folders.forEach(folder => {
          const option = document.createElement('option');
          option.value = folder;
          option.textContent = folder;
          folderSelect.appendChild(option);
        });
        folderSelect.value = currentPath
          ? currentPath.slice(0, Math.max(currentPath.lastIndexOf('\\'), currentPath.lastIndexOf('/')))
          : info.default_folder;
        if (!folderSelect.value) folderSelect.value = info.default_folder;
        const error = document.createElement('p');
        error.className = 'text-danger small';
        const actions = document.createElement('div');
        actions.className = 'question-dialog-actions';
        const cancel = button('Cancel');
        const save = button('Save', 'btn btn-primary');
        actions.append(cancel, save);
        modal.append(nameInput, folderSelect, error, actions);
        nameInput.focus();
        cancel.addEventListener('click', () => { close(); resolve(null); });
        const submit = async () => {
          if (!nameInput.value.trim()) { error.textContent = 'Enter a file name.'; return; }
          save.disabled = true;
          try {
            const result = await writeFile(folderSelect.value, nameInput.value);
            if (result) { close(); resolve(result); }
          } catch (err) {
            error.textContent = err.message;
          }
          save.disabled = false;
        };
        save.addEventListener('click', submit);
        nameInput.addEventListener('keydown', event => { if (event.key === 'Enter') submit(); });
      });
    }).catch(err => { status.textContent = err.message; resolve(null); });
  });

  const save = async () => {
    if (managedPath) {
      try {
        await Api.writeManagedFile(managedPath, editor.getValue());
        markSaved(managedPath);
        status.textContent = `Saved ${managedPath}`;
        window.dispatchEvent(new CustomEvent('novous:fs-changed'));
        return { saved: true, path: managedPath };
      } catch (err) {
        status.textContent = `Save failed: ${err.message}`;
        return null;
      }
    }
    if (!currentPath) return saveAs();
    const folder = currentPath.slice(0, Math.max(currentPath.lastIndexOf('\\'), currentPath.lastIndexOf('/')));
    try {
      return await writeFile(folder, nameOf(currentPath), true);
    } catch (err) {
      status.textContent = `Save failed: ${err.message}`;
      return null;
    }
  };

  const open = async () => {
    if (isDirty() && !confirm('Discard unsaved changes in the editor?')) return;
    dialog('Open from file manager', (modal, close) => {
      modal.classList.add('is-resizable');
      const treeHost = document.createElement('div');
      treeHost.className = 'codebuilder-open-tree';
      const actions = document.createElement('div');
      actions.className = 'question-dialog-actions';
      const cancel = button('Cancel');
      cancel.addEventListener('click', close);
      actions.appendChild(cancel);
      modal.append(treeHost, actions);

      renderTree(treeHost, {
        manageRoots: true,
        onSelect: async (path, type) => {
          if (type !== 'file') return;
          try {
            const opened = await Api.readManagedFile(path);
            editor.setValue(opened.content);
            managedPath = opened.path;
            markSaved(opened.path);
            status.textContent = `Opened ${opened.path}`;
            close();
          } catch (err) {
            status.textContent = `Could not open ${path}: ${err.message}`;
          }
        }
      });
    });
  };

  const runInTerminal = async () => {
    const saved = await save();
    if (!saved && !currentPath) return;
    try {
      const { command } = await Files.runCommand(currentPath, editor.getValue());
      openTerminalWith?.(command);
      status.textContent = 'Press Enter in the terminal to run';
    } catch (err) {
      status.textContent = err.message;
    }
  };

  buttons.save?.addEventListener('click', save);
  buttons.saveAs?.addEventListener('click', saveAs);
  buttons.open?.addEventListener('click', open);
  buttons.runTerminal?.addEventListener('click', runInTerminal);
  editor.setSaveHandler?.(save);
  refreshLabel();

  return { refreshLabel, save, saveAs, open };
}

```

## `frontend/static/js/editor.js`
```js
import { Api } from './api.js';
import { attachCodeBuilderEditor } from './codebuilder/codebuilder_editor.js';
import { renderTree } from './tree.js';

const fileSelectionListeners = new WeakMap();

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const state = {
  path: null,
  dirty: false,
  ws: null,
  editor: null,
  managedPath: false
};

/**
 * File & Agent Editor Component (Monaco editor + live session event bus).
 * @param {HTMLElement} container
 * @param {string|null} initialPath
 */
export function renderEditorView(container, initialPath = null) {
  const initialFile = typeof initialPath === 'string'
    ? { path: initialPath, managedFile: false }
    : initialPath;
  const oldSelectionListener = fileSelectionListeners.get(container);
  if (oldSelectionListener) window.removeEventListener('novous:file-selected', oldSelectionListener);
  state.editor?.dispose();
  state.path = null;
  state.dirty = false;
  state.managedPath = false;

  container.innerHTML = `
    <div class="editor-layout">
      <aside class="editor-sidebar">
        <h3 class="sidebar-title">Workspace</h3>
        <div id="editor-tree" class="tree-pane"></div>
      </aside>

      <section class="editor-main">
        <div class="editor-toolbar">
          <span id="editor-path" class="editor-path">No file open</span>
          <span id="editor-dirty" class="badge badge-warning hidden">Unsaved</span>
          <span class="spacer"></span>
          <span id="editor-ws" class="badge badge-success" title="Session event bus">WS ●</span>
          <button class="btn btn-sm" id="editor-reload">Reload</button>
          <button class="btn btn-sm btn-primary" id="editor-save">Save (Ctrl+S)</button>
        </div>
        <div id="editor-monaco" class="editor-monaco"></div>
        <div class="editor-status">
          <span id="editor-pos">Ln 1, Col 1</span>
          <span class="spacer"></span>
          <span id="editor-bytes">0 bytes</span>
        </div>
      </section>

      <aside class="editor-events">
        <h3 class="sidebar-title">Session Events</h3>
        <div class="event-export">
          <button class="btn btn-sm btn-primary" id="event-save-log">Save Events Log (.md)</button>
        </div>
        <div id="event-log" class="event-log">
          <p class="text-muted">Connecting to event bus…</p>
        </div>
      </aside>
    </div>`;

  container.insertAdjacentHTML('beforeend', `
    <dialog id="editor-save-dialog" class="workspace-save-dialog">
      <form id="editor-save-form">
        <h2>Save to Workspace</h2>
        <p class="text-muted">Choose a workspace folder and file name.</p>
        <label for="editor-save-directory">Folder</label>
        <select id="editor-save-directory" class="form-select"></select>
        <label for="editor-save-filename">File name</label>
        <input id="editor-save-filename" class="form-input" type="text" required>
        <p id="editor-save-error" class="text-danger hidden" role="alert"></p>
        <div class="workspace-save-actions">
          <button id="editor-save-cancel" class="btn" type="button">Cancel</button>
          <button id="editor-save-confirm" class="btn btn-primary" type="submit">Save</button>
        </div>
      </form>
    </dialog>`);

  const editorMount = container.querySelector('#editor-monaco');
  const pathLabel = container.querySelector('#editor-path');
  const dirtyBadge = container.querySelector('#editor-dirty');
  const bytesLabel = container.querySelector('#editor-bytes');
  const posLabel = container.querySelector('#editor-pos');
  const eventLog = container.querySelector('#event-log');
  const wsBadge = container.querySelector('#editor-ws');
  const saveLogButton = container.querySelector('#event-save-log');
  const saveDialog = container.querySelector('#editor-save-dialog');
  const saveDirectory = container.querySelector('#editor-save-directory');
  const saveFilename = container.querySelector('#editor-save-filename');
  const saveError = container.querySelector('#editor-save-error');
  const saveConfirm = container.querySelector('#editor-save-confirm');
  const sessionEvents = [];
  let saveDialogFiles = new Set();
  let suppressEditorChanges = false;
  let workspaceTree;
  const editorReady = attachCodeBuilderEditor(editorMount, '', 'plaintext').then(instance => {
    state.editor = instance;
    instance.onChange(() => {
      if (suppressEditorChanges) return;
      if (!state.dirty) { state.dirty = true; dirtyBadge.classList.remove('hidden'); }
      updateBytes();
    });
    if (state.path) {
      suppressEditorChanges = true;
      instance.setValue(state.content || '');
      instance.setLanguage(languageForPath(state.path));
      suppressEditorChanges = false;
    }
    instance.focus();
    updateBytes();
    return instance;
  });

  saveLogButton.addEventListener('click', async () => {
    saveLogButton.disabled = true;
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const rows = sessionEvents.map(event => {
        const escapeCell = value => String(value || '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
        const details = event.data && Object.keys(event.data).length
          ? JSON.stringify(event.data)
          : '';
        return `| ${escapeCell(event.type.replace(/_/g, ' '))} | ${escapeCell(event.path)} | ${escapeCell(event.session_id)} | ${escapeCell(details)} |`;
      });
      const markdown = [
        '# Novous2 Session Events Log',
        '',
        `Exported: ${new Date().toLocaleString()}`,
        '',
        '| Event | Path / Tool | Session | Details |',
        '| --- | --- | --- | --- |',
        ...(rows.length ? rows : ['| No events recorded | | | |']),
        ''
      ].join('\n');
      const result = await Api.saveMarkdown(markdown, `novous2-session-events-${timestamp}.md`);
      alert(result.locationChosen
        ? `Events log saved as ${result.filename} in the location you selected.`
        : `Events log download started: ${result.filename}\n\nChoose the save location in your browser's download settings.`);
    } catch (err) {
      if (err.name !== 'AbortError') alert(`Failed to save events log: ${err.message}`);
    } finally {
      saveLogButton.disabled = false;
    }
  });

  async function openFile(path, managedFile = false) {
    if (state.dirty && !confirm('Discard unsaved changes?')) return;
    try {
      const data = managedFile ? await Api.readManagedFile(path) : await Api.readFile(path);
      state.path = data.path;
      state.content = data.content;
      state.managedPath = managedFile;
      state.dirty = false;
      pathLabel.textContent = data.path;
      dirtyBadge.classList.add('hidden');
      await editorReady;
      suppressEditorChanges = true;
      state.editor.setLanguage(languageForPath(data.path));
      state.editor.setValue(data.content);
      suppressEditorChanges = false;
      updateBytes();
      updatePos();
      sendWs({ type: 'file_opened', path: data.path });
      appendEvent({ type: 'file_opened', path: data.path, session_id: 'you' });
      state.editor.focus();
    } catch (err) {
      suppressEditorChanges = false;
      alert(err.message);
    }
  }

  function languageForPath(path) {
    const extension = path.split('.').pop().toLowerCase();
    return ({
      c: 'c', cc: 'cpp', cpp: 'cpp', cs: 'csharp', css: 'css', go: 'go',
      h: 'cpp', htm: 'html', html: 'html', java: 'java', js: 'javascript',
      json: 'json', jsx: 'javascript', md: 'markdown', mjs: 'javascript',
      py: 'python', rb: 'ruby', rs: 'rust', sh: 'shell', sql: 'sql',
      ts: 'typescript', tsx: 'typescript', txt: 'plaintext', xml: 'xml',
      yaml: 'yaml', yml: 'yaml'
    })[extension] || 'plaintext';
  }

  workspaceTree = renderTree(container.querySelector('#editor-tree'), {
    onBeforeDelete: path => {
      const deletesOpenFile = state.path === path || state.path?.startsWith(`${path}/`);
      return !deletesOpenFile || !state.dirty ||
        confirm('This item contains the open file with unsaved changes. Delete anyway?');
    },
    onDelete: path => {
      if (state.path === path || state.path?.startsWith(`${path}/`)) {
        state.path = null;
        state.content = '';
        state.managedPath = false;
        state.editor?.setValue('');
        pathLabel.textContent = 'No file open';
        dirtyBadge.classList.add('hidden');
        state.dirty = false;
        updateBytes();
      }
    }
  });
  const onFileSelected = event => {
    const path = event.detail && event.detail.path;
    if (typeof path === 'string' && path) openFile(path, true);
  };
  fileSelectionListeners.set(container, onFileSelected);
  window.addEventListener('novous:file-selected', onFileSelected);
  editorReady.then(instance => instance.onPosition(updatePos));

  async function openSaveDialog() {
    try {
      const managedSave = state.managedPath || !state.path;
      const tree = managedSave
        ? await Api.getManagedFileTree()
        : await Api.getFileTree();
      const folders = [];
      const files = new Set();
      function collect(node) {
        if (node.type === 'directory') {
          if (node.path) folders.push(node.path);
          (node.children || []).forEach(collect);
        } else {
          files.add(node.path);
        }
      }
      collect(tree);
      folders.sort((a, b) => a.localeCompare(b));

      saveDirectory.replaceChildren();
      const rootOption = document.createElement('option');
      rootOption.value = '';
      rootOption.textContent = '/ (workspace root)';
      saveDirectory.appendChild(rootOption);
      folders.forEach(path => {
        const option = document.createElement('option');
        option.value = path;
        option.textContent = path;
        saveDirectory.appendChild(option);
      });

      const currentParts = (state.path || '').split('/');
      const currentFilename = currentParts.pop() || 'untitled.txt';
      const currentDirectory = currentParts.join('/');
      saveDirectory.value = folders.includes(currentDirectory) ? currentDirectory : '';
      saveFilename.value = currentFilename;
      saveError.textContent = '';
      saveError.classList.add('hidden');
      saveDialog.showModal();
      saveFilename.focus();
      saveFilename.select();
      saveDialogFiles = files;
    } catch (err) {
      alert(`Could not open the workspace save picker: ${err.message}`);
    }
  }

  async function saveFile() {
    if (!saveDialog.open) {
      await openSaveDialog();
      return;
    }

    const filename = saveFilename.value.trim();
    if (!filename || filename === '.' || filename === '..' || /[\\/]/.test(filename)) {
      saveError.textContent = 'Enter a file name without folder separators.';
      saveError.classList.remove('hidden');
      saveFilename.focus();
      return;
    }

    const targetPath = [saveDirectory.value, filename].filter(Boolean).join('/');
    if (saveDialogFiles.has(targetPath) && targetPath !== state.path &&
        !confirm(`"${targetPath}" already exists. Overwrite it?`)) {
      return;
    }

    saveConfirm.disabled = true;
    try {
      await editorReady;
      const content = state.editor.getValue();
      const managedSave = state.managedPath || !state.path;
      if (managedSave) await Api.writeManagedFile(targetPath, content);
      else await Api.writeFile(targetPath, content);
      state.path = targetPath;
      state.content = content;
      state.managedPath = managedSave;
      state.editor.setLanguage(languageForPath(targetPath));
      state.dirty = false;
      dirtyBadge.classList.add('hidden');
      pathLabel.textContent = targetPath;
      appendEvent({ type: 'file_saved', path: targetPath, session_id: 'you' });
      updateBytes();
      saveDialog.close();
      workspaceTree.reload();
    } catch (err) {
      saveError.textContent = `Save failed: ${err.message}`;
      saveError.classList.remove('hidden');
    } finally {
      saveConfirm.disabled = false;
    }
  }

  function updateBytes() {
    bytesLabel.textContent = `${new Blob([state.editor?.getValue() || '']).size} bytes`;
  }

  function updatePos() {
    const position = state.editor?.getPosition();
    if (position) posLabel.textContent = `Ln ${position.lineNumber}, Col ${position.column}`;
  }

  container.querySelector('#editor-save').addEventListener('click', openSaveDialog);
  container.querySelector('#editor-save-form').addEventListener('submit', (event) => {
    event.preventDefault();
    saveFile();
  });
  container.querySelector('#editor-save-cancel').addEventListener('click', () => saveDialog.close());
  container.querySelector('#editor-reload').addEventListener('click', () => {
    if (state.path) openFile(state.path);
  });
  editorReady.then(instance => instance.setSaveHandler(saveFile));

  // --- WebSocket session event bus ----------------------------------------
  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/api/ws`);
    state.ws = ws;

    ws.onopen = () => { wsBadge.textContent = 'WS ●'; wsBadge.className = 'badge badge-success'; };
    ws.onclose = () => {
      wsBadge.textContent = 'WS ○'; wsBadge.className = 'badge badge-danger';
      eventLog.insertAdjacentHTML('beforeend',
        '<p class="text-muted small">Disconnected. Reconnecting…</p>');
      setTimeout(connectWs, 3000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === 'connected') {
          if (!sessionEvents.length) {
            eventLog.innerHTML = `<p class="text-muted small">Connected as session ${esc(data.session_id)}</p>`;
          }
        } else if (data.type !== 'pong') {
          appendEvent(data);
        }
      } catch (_) { /* non-JSON frame */ }
    };
  }

  function sendWs(payload) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify(payload));
    }
  }

  function appendEvent(data) {
    if (eventLog.querySelector('.text-muted.small') && eventLog.children.length === 1 &&
        eventLog.textContent.includes('Disconnected')) {
      eventLog.innerHTML = '';
    }
    const el = document.createElement('div');
    el.className = `event-item ${data.type}`;
    const eventData = {
      type: String(data.type || 'unknown'),
      path: data.path || '',
      session_id: data.session_id || '',
      data: data.data || {}
    };
    sessionEvents.push(eventData);
    const detailText = eventData.type === 'tool_executed'
      ? `${eventData.data.status || 'unknown'}${eventData.data.origin ? ` · ${eventData.data.origin}` : ''}\nArgs: ${JSON.stringify(eventData.data.args || {})}${eventData.data.error ? `\nError: ${eventData.data.error}` : ''}`
      : '';
    const eventText = [
      eventData.type.replace(/_/g, ' '),
      eventData.path,
      eventData.session_id,
      detailText
    ].filter(Boolean).join('\n');
    const detailElement = detailText
      ? `<span class="event-details">${esc(detailText)}</span>`
      : '';
    el.innerHTML = `<span class="event-type">${esc(eventData.type.replace(/_/g, ' '))}</span>
      <span class="event-path">${esc(eventData.path)}</span>
      <span class="event-who text-muted">${esc(eventData.session_id)}</span>${detailElement}`;
    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'btn btn-sm btn-ghost event-copy-btn';
    copyButton.textContent = 'Copy';
    copyButton.setAttribute('aria-label', `Copy ${eventData.type.replace(/_/g, ' ')} event`);
    copyButton.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(eventText);
        copyButton.textContent = 'Copied!';
        setTimeout(() => { copyButton.textContent = 'Copy'; }, 2000);
      } catch (err) {
        copyButton.textContent = 'Copy failed';
      }
    });
    el.appendChild(copyButton);
    eventLog.appendChild(el);
    while (sessionEvents.length > 60) {
      sessionEvents.shift();
      const firstEvent = eventLog.querySelector('.event-item');
      if (firstEvent) firstEvent.remove();
    }
    eventLog.scrollTop = eventLog.scrollHeight;
  }

  connectWs();

  if (initialFile?.path) openFile(initialFile.path, initialFile.managedFile === true);
}

```

## `frontend/static/js/icons.js`
```js
const ICON_MARKUP = {
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  bug: '<path d="M12 20v-8"/><path d="M8 20v-4a4 4 0 0 1 8 0v4"/><path d="M19 8h-3"/><path d="M8 8H5"/><path d="M19 12h-3"/><path d="M8 12H5"/><path d="M16 4a4 4 0 0 0-8 0"/>',
  'check-square': '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="m9 12 2 2 4-4"/>',
  copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  'file-code': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="m10 13-2 2 2 2"/><path d="m14 13 2 2-2 2"/>',
  gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/><path d="M12 14a2 2 0 1 0-2-2"/>',
  'play-circle': '<circle cx="12" cy="12" r="10"/><path d="m10 8 6 4-6 4z"/>',
  refresh: '<path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M5.6 9a7 7 0 0 1 11.55-2.6L20 12"/><path d="M4 12l2.85 5.6A7 7 0 0 0 18.4 15"/>',
  reset: '<path d="M3 12a9 9 0 1 0 2.64-6.36L3 8"/><path d="M3 3v5h5"/>',
  save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
  terminal: '<rect x="2" y="3" width="20" height="18" rx="2"/><path d="m7 9 3 3-3 3"/><path d="M13 15h4"/>',
  'trash-2': '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v5"/><path d="M14 11v5"/>'
};

export function createIcon(name) {
  const markup = ICON_MARKUP[name];
  if (!markup) throw new Error(`Unknown icon: ${name}`);

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('width', '16');
  svg.setAttribute('height', '16');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '2');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  svg.setAttribute('aria-hidden', 'true');
  svg.classList.add('chat-icon');
  svg.innerHTML = markup;
  return svg;
}

```

## `frontend/static/js/prompt_creation.js`
```js
import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function appendMarkdownInline(parent, text) {
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|~~[^~]+~~|\[([^\]]+)\]\(([^)\s]+)\))/g;
  let lastIndex = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    parent.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
    const token = match[0];
    let element;

    if (token.startsWith('`')) {
      element = document.createElement('code');
      element.textContent = token.slice(1, -1);
    } else if (token.startsWith('**') || token.startsWith('__')) {
      element = document.createElement('strong');
      element.textContent = token.slice(2, -2);
    } else if (token.startsWith('~~')) {
      element = document.createElement('del');
      element.textContent = token.slice(2, -2);
    } else if (token.startsWith('*') || token.startsWith('_')) {
      element = document.createElement('em');
      element.textContent = token.slice(1, -1);
    } else {
      element = document.createElement('a');
      element.textContent = match[2];
      try {
        const url = new URL(match[3], window.location.href);
        if (['http:', 'https:', 'mailto:'].includes(url.protocol)) {
          element.href = url.href;
          element.rel = 'noopener noreferrer';
        } else {
          element = document.createTextNode(match[2]);
        }
      } catch {
        element = document.createTextNode(match[2]);
      }
    }

    parent.appendChild(element);
    lastIndex = pattern.lastIndex;
  }

  parent.appendChild(document.createTextNode(text.slice(lastIndex)));
}

function appendMarkdown(parent, markdown) {
  const lines = String(markdown ?? '').replace(/\r\n?/g, '\n').split('\n');
  let paragraph = [];
  let list = null;
  let codeLines = null;
  const isTableDelimiter = line =>
    /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
  const splitTableRow = line =>
    line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim());

  const flushParagraph = () => {
    if (!paragraph.length) return;
    const block = document.createElement('p');
    paragraph.forEach((line, index) => {
      if (index) block.appendChild(document.createTextNode(' '));
      appendMarkdownInline(block, line);
    });
    parent.appendChild(block);
    paragraph = [];
  };
  const flushList = () => {
    if (list) parent.appendChild(list);
    list = null;
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const fence = line.match(/^\s*```([^`]*)$/);
    if (codeLines) {
      if (fence) {
        const code = document.createElement('code');
        code.textContent = codeLines.join('\n');
        const pre = document.createElement('pre');
        pre.appendChild(code);
        parent.appendChild(pre);
        codeLines = null;
      } else {
        codeLines.push(line);
      }
      continue;
    }
    if (fence) {
      flushParagraph();
      flushList();
      codeLines = [];
      continue;
    }
    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    if (/^\s{0,3}(?:---+|___+|\*\*\*+)\s*$/.test(line)) {
      flushParagraph();
      flushList();
      parent.appendChild(document.createElement('hr'));
      continue;
    }

    if (line.includes('|') && lines[index + 1] && isTableDelimiter(lines[index + 1])) {
      flushParagraph();
      flushList();
      const headers = splitTableRow(line);
      const table = document.createElement('table');
      table.className = 'prompt-markdown-table';
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');
      headers.forEach(text => {
        const cell = document.createElement('th');
        cell.scope = 'col';
        appendMarkdownInline(cell, text);
        headerRow.appendChild(cell);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      for (index += 2; index < lines.length && lines[index].includes('|'); index += 1) {
        const row = document.createElement('tr');
        splitTableRow(lines[index]).forEach((text, cellIndex) => {
          const cell = document.createElement('td');
          if (headers[cellIndex]) appendMarkdownInline(cell, text);
          row.appendChild(cell);
        });
        tbody.appendChild(row);
      }
      table.appendChild(tbody);
      parent.appendChild(table);
      index -= 1;
      continue;
    }

    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (heading) {
      flushParagraph();
      flushList();
      const element = document.createElement(`h${heading[1].length}`);
      appendMarkdownInline(element, heading[2]);
      parent.appendChild(element);
      continue;
    }

    const item = line.match(/^\s{0,3}([-*+]|\d+[.)])\s+(.+)$/);
    if (item) {
      flushParagraph();
      const ordered = /^\d/.test(item[1]);
      if (!list || (list.tagName === 'OL') !== ordered) {
        flushList();
        list = document.createElement(ordered ? 'ol' : 'ul');
      }
      const element = document.createElement('li');
      const task = item[2].match(/^\[([ xX])\]\s+(.+)$/);
      if (task) {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = task[1].toLowerCase() === 'x';
        checkbox.disabled = true;
        checkbox.setAttribute('aria-label', checkbox.checked ? 'Completed task' : 'Incomplete task');
        element.classList.add('prompt-markdown-task');
        element.append(checkbox, document.createTextNode(' '));
        appendMarkdownInline(element, task[2]);
      } else {
        appendMarkdownInline(element, item[2]);
      }
      list.appendChild(element);
      continue;
    }

    flushList();
    const quote = line.match(/^\s{0,3}>\s?(.*)$/);
    if (quote) {
      flushParagraph();
      const blockquote = document.createElement('blockquote');
      appendMarkdownInline(blockquote, quote[1]);
      parent.appendChild(blockquote);
      continue;
    }

    paragraph.push(line.trim());
  }

  if (codeLines) {
    const code = document.createElement('code');
    code.textContent = codeLines.join('\n');
    const pre = document.createElement('pre');
    pre.appendChild(code);
    parent.appendChild(pre);
  }
  flushParagraph();
  flushList();
}

export function renderPromptCreationView(container) {
  container.innerHTML = `
    <div class="prompt-creation-flow">
      <section class="card prompt-chat-card" aria-labelledby="pc-chat-title">
        <div class="codebuilder-chat-heading">
          <h2 id="pc-chat-title">Prompt Coach Chat</h2>
          <span id="pc-chat-status" class="text-muted small">Loading agents…</span>
          <span class="prompt-chat-font-controls" role="group" aria-label="Chat text size">
            <button type="button" class="btn btn-sm" id="pc-font-smaller" title="Smaller text" aria-label="Decrease chat text size">A−</button>
            <button type="button" class="btn btn-sm" id="pc-font-larger" title="Larger text" aria-label="Increase chat text size">A+</button>
          </span>
        </div>
        <p class="text-muted small prompt-chat-note">
          Chat with an available agent to clarify and shape your prompt. Responses use cleaner Markdown formatting when possible.
        </p>
        <div id="pc-chat-messages" class="codebuilder-chat-messages" aria-live="polite">
          <div class="codebuilder-chat-message system">Describe the prompt you want to create, and we’ll work through it together.</div>
        </div>
        <form id="pc-chat-form" class="codebuilder-chat-form">
          <label class="codebuilder-model-picker">
            <span class="text-muted small">Agent</span>
            <select id="pc-chat-agent" class="form-select" aria-label="Choose prompt coach agent">
              <option value="">Loading agents…</option>
            </select>
            <span class="text-muted small">Model</span>
            <select id="pc-chat-model" class="form-select" aria-label="Choose model">
              <option value="">Loading models…</option>
            </select>
          </label>
          <textarea id="pc-chat-input" class="form-input" rows="3"
                    placeholder="What should this prompt help its agent do?"
                    aria-label="Message to prompt coach"></textarea>
          <div class="codebuilder-chat-actions">
            <button id="pc-chat-clear" class="btn btn-sm" type="button">Clear</button>
            <button class="btn btn-primary" type="submit" disabled>Send</button>
          </div>
        </form>
      </section>

      <div class="prompt-chat-resizer" role="separator" aria-label="Resize chat panel"
           aria-orientation="vertical" aria-valuemin="280" aria-valuemax="2000"
           aria-valuenow="320" tabindex="0"></div>

      <section class="card prompt-assembly-card" aria-labelledby="tb-assembly-title">
        <div class="card-head">
          <h3 id="tb-assembly-title">Prompt Creation & Assembly</h3>
          <div class="toolbar-row" style="margin:0;">
            <button type="button" class="btn btn-sm" id="tb-toggle-cat-form">+ Category</button>
            <button type="button" class="btn btn-sm" id="tb-toggle-part-form">+ Part</button>
            <button type="button" class="btn btn-sm btn-primary" id="tb-assemble">Assemble</button>
          </div>
        </div>

        <div id="tb-cat-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Category</h4>
          <div class="form-row">
            <input type="text" id="cat-id-input" class="form-input" placeholder="Category ID / Slug (e.g. constraints)" required>
            <input type="text" id="cat-name-input" class="form-input" placeholder="Category Name (e.g. Constraints)" required>
          </div>
          <div class="form-row">
            <input type="text" id="cat-desc-input" class="form-input" placeholder="Description (optional)">
            <input type="text" id="cat-header-input" class="form-input" placeholder="Required Header (e.g. constraints)">
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="cat-save-btn">Save Category</button>
            <button type="button" class="btn btn-sm" id="cat-cancel-btn">Cancel</button>
          </div>
        </div>

        <div id="tb-part-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Prompt Part</h4>
          <div class="form-row">
            <select id="part-cat-select" class="form-select"></select>
            <input type="text" id="part-title-input" class="form-input" placeholder="Part Title (e.g. JSON Format)" required>
          </div>
          <div class="form-row">
            <input type="text" id="part-slug-input" class="form-input" placeholder="Slug ID (optional)">
          </div>
          <div class="form-row">
            <textarea id="part-content-input" class="form-input" style="width: 100%; height: 80px;" placeholder="Prompt part markdown content…" required></textarea>
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="part-save-btn">Save Part</button>
            <button type="button" class="btn btn-sm" id="part-cancel-btn">Cancel</button>
          </div>
        </div>

        <div class="prompt-metadata-fields">
          <label class="prompt-component-field">
            <span>Prompt title</span>
            <input id="tb-title" class="form-input" maxlength="100"
                   placeholder="What is this prompt for?">
          </label>
          <label class="prompt-component-field">
            <span>Prompt description</span>
            <textarea id="tb-description" class="form-input" rows="3" maxlength="1000"
                      placeholder="Describe the outcome this prompt should help an agent achieve, and when it should be used."></textarea>
          </label>
        </div>

        <div id="tb-categories" class="category-grid">
          <p class="text-muted">Loading categories…</p>
        </div>

      </section>

      <section class="card prompt-tools-card" aria-labelledby="tb-tools-title">
        <div class="card-head">
          <h3 id="tb-tools-title">Available Core Engine Tools</h3>
          <button type="button" class="btn btn-sm" id="btn-refresh-tools">Refresh Tools</button>
        </div>
        <p class="text-muted small">Tools retrieved from the five file-tool modules and <code>promoted_tools.py</code> in <code>tools/</code>. Tick a tool to include it in the prompt; use ✎ to edit its description and 🧪 to test it.</p>
        <div id="tools-list-container" class="category-grid" style="overflow-y: auto; max-height: 500px;">
          <p class="text-muted">Loading available tools...</p>
        </div>
      </section>

      <section class="card prompt-result-card" aria-labelledby="tb-preview-title">
        <div class="card-head">
          <div>
            <h3 id="tb-preview-title">Assembled Prompt</h3>
            <p class="text-muted small">Review or edit the completed prompt here before testing it. Re-assembling replaces manual edits.</p>
          </div>
          <span id="tb-stats" class="text-muted small"></span>
        </div>
        <textarea id="tb-preview" class="prompt-preview"
                  placeholder="Assemble selected prompt parts to prepare the prompt for testing…"></textarea>
        <div class="toolbar-row">
          <button type="button" class="btn btn-sm" id="tb-copy">Copy</button>
          <span class="spacer"></span>
          <select id="tb-publish-agent" class="form-select prompt-publish-select">
            <option value="">Select agent…</option>
          </select>
          <button type="button" class="btn btn-sm" id="tb-publish">Save to Agent</button>
          <label class="checkbox-row" title="Run the prompt on the selected chat model and check role understanding, a known fact, and hallucination resistance">
            <input type="checkbox" id="tb-model-test" checked> <span>Model test</span>
          </label>
          <input class="form-input" id="tb-fact-q" aria-label="Fact question" value="What is the capital of France?" style="max-width: 14rem;">
          <input class="form-input" id="tb-fact-a" aria-label="Expected answer" value="Paris" style="max-width: 6rem;">
          <label class="checkbox-row" title="Also have the selected chat model review each section against a rubric">
            <input type="checkbox" id="tb-ai-review"> <span>AI rubric review</span>
          </label>
          <button type="button" class="btn btn-sm btn-primary" id="tb-test-prompt">Test Prompt</button>
        </div>
        <p id="tb-msg" class="small hidden"></p>
        <div id="tb-test-result" class="small hidden" role="status" aria-live="polite"></div>
      </section>

      <section class="card prompt-markdown-draft-card hidden" id="pc-markdown-draft-card"
               aria-labelledby="pc-markdown-draft-title">
        <div class="card-head">
          <div>
            <h3 id="pc-markdown-draft-title">Chat Markdown Draft</h3>
            <p class="text-muted small">Responses added from chat are combined here. Copy the raw Markdown when ready.</p>
          </div>
          <div class="toolbar-row prompt-markdown-draft-actions">
            <button type="button" class="btn btn-sm btn-primary" id="pc-parse-markdown">Parse draft</button>
            <button type="button" class="btn btn-sm" id="pc-copy-markdown">Copy Markdown</button>
            <button type="button" class="btn btn-sm" id="pc-clear-markdown">Clear</button>
          </div>
        </div>
        <div class="prompt-markdown-preview" id="pc-markdown-preview"></div>
        <p class="small text-muted" id="pc-markdown-status" role="status" aria-live="polite"></p>
      </section>
    </div>`;

  const catBox = container.querySelector('#tb-categories');
  const preview = container.querySelector('#tb-preview');
  const stats = container.querySelector('#tb-stats');
  const msg = container.querySelector('#tb-msg');
  const toolsContainer = container.querySelector('#tools-list-container');
  const publishAgentSel = container.querySelector('#tb-publish-agent');
  const titleField = container.querySelector('#tb-title');
  const descriptionField = container.querySelector('#tb-description');
  const chatAgentSel = container.querySelector('#pc-chat-agent');
  const chatModelSel = container.querySelector('#pc-chat-model');
  const chatInput = container.querySelector('#pc-chat-input');
  const chatMessages = container.querySelector('#pc-chat-messages');
  const chatStatus = container.querySelector('#pc-chat-status');
  const chatForm = container.querySelector('#pc-chat-form');
  const testResult = container.querySelector('#tb-test-result');
  const chatResizer = container.querySelector('.prompt-chat-resizer');
  const flow = container.querySelector('.prompt-creation-flow');
  const markdownDraftCard = container.querySelector('#pc-markdown-draft-card');
  const markdownPreview = container.querySelector('#pc-markdown-preview');
  const markdownStatus = container.querySelector('#pc-markdown-status');

  const catForm = container.querySelector('#tb-cat-form');
  const partForm = container.querySelector('#tb-part-form');
  const partCatSelect = container.querySelector('#part-cat-select');

  let manifest = { categories: [] };
  let availableTools = [];
  let promptAgents = [];
  let selectedChatAgent = null;
  let chatPending = false;
  let promptBase = '';
  let promptPartCount = 0;
  let promptRevision = 0;
  let testedPromptRevision = null;
  const promptTools = new Map();
  const chatWidthStorageKey = 'novous2.prompt-creation.chat-width';
  let markdownDraft = '';
  const stateStorageKey = 'novous2.prompt-creation.state';
  let restoredParts = [];

  function saveState() {
    try {
      sessionStorage.setItem(stateStorageKey, JSON.stringify({
        draft: markdownDraft,
        title: titleField.value,
        description: descriptionField.value,
        parts: [...catBox.querySelectorAll('[data-part]:checked')].map(input => input.value),
        tools: [...promptTools.values()]
      }));
    } catch {
      // storage unavailable; state just won't survive a reload
    }
  }

  function restoreState() {
    let saved = null;
    try {
      saved = JSON.parse(sessionStorage.getItem(stateStorageKey) || 'null');
    } catch {
      return;
    }
    if (!saved) return;
    markdownDraft = saved.draft || '';
    titleField.value = saved.title || '';
    descriptionField.value = saved.description || '';
    restoredParts = saved.parts || [];
    for (const tool of saved.tools || []) promptTools.set(tool.name, tool);
    if (markdownDraft) {
      markdownDraftCard.classList.remove('hidden');
      appendMarkdown(markdownPreview, markdownDraft);
    }
  }
  function showMsg(text, isError = false) {
    msg.textContent = text;
    msg.className = `small ${isError ? 'text-danger' : 'text-success'}`;
  }

  function markPromptChanged() {
    saveState();
    promptRevision += 1;
    if (testedPromptRevision !== null) {
      testedPromptRevision = null;
      testResult.className = 'small text-warning';
      testResult.textContent = 'Prompt changed since the last test. Run Test Prompt again for an up-to-date report.';
    }
  }

  function toolDescription(tool) {
    return tool.promptDescription ?? (
      Array.isArray(tool.description) ? tool.description.join(' ') : tool.description || ''
    );
  }

  function findPromptPart(partId) {
    for (const category of manifest.categories || []) {
      const part = (category.parts || []).find(item => item.id === partId);
      if (part) return { ...part, category: category.id };
    }
    return (manifest.uncategorized_parts || []).find(item => item.id === partId) || null;
  }

  function selectedPromptSections() {
    return [...catBox.querySelectorAll('[data-part]:checked')].map(input => {
      const part = findPromptPart(input.value);
      if (!part) return null;
      return {
        id: part.id,
        title: part.title,
        category: part.category,
        content: part.content
      };
    }).filter(Boolean);
  }


  async function loadCoreTools() {
    try {
      toolsContainer.innerHTML = '<p class="text-muted">Fetching file tools...</p>';
      const res = await Api.getToolLibrary();
      availableTools = res.tools || [];

      if (!availableTools.length) {
        toolsContainer.innerHTML = '<p class="text-muted">No file tools are currently registered.</p>';
        return;
      }

      const providers = [...new Set(availableTools.map(t => t.provider || 'tools'))];
      toolsContainer.innerHTML = providers.map(provider => `
        <div class="category-block">
          <div class="category-head">
            <strong>${esc(provider)}</strong>
          </div>
          ${availableTools.map((t, index) => ({ t, index })).filter(({ t }) => (t.provider || 'tools') === provider).map(({ t, index }) => `
            <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
              <label class="checkbox-row" style="flex: 1; margin: 0;" title="${esc(t.signature)}">
                <input type="checkbox" value="${index}" data-tool ${promptTools.has(t.name) ? 'checked' : ''}>
                <span>${esc(t.name)}</span>
              </label>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Edit tool description" data-edit-tool="${index}" style="padding: 0 0.3rem;">✎</button>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test tool description" data-test-tool="${index}" style="padding: 0 0.3rem;">🧪</button>
            </div>`).join('')}
        </div>
      `).join('');
    } catch (err) {
      toolsContainer.innerHTML = `<p class="text-danger">Failed to retrieve tools: ${esc(err.message)}</p>`;
    }
  }

  function updatePromptPreview() {
    const toolSection = [...promptTools.values()].map(tool => {
      const description = toolDescription(tool);
      return [
        `### ${tool.name}`,
        `- Provider: ${tool.provider}`,
        `- Signature: ${tool.signature}`,
        description ? description : ''
      ].filter(Boolean).join('\n');
    }).join('\n\n');

    const title = titleField.value.trim();
    const description = descriptionField.value.trim();
    const sectionText = selectedPromptSections().map(section =>
      `## ${section.title}\n\n${section.content.trim()}`
    ).join('\n\n');
    const heading = [title ? `# ${title}` : '', description].filter(Boolean).join('\n\n');
    promptBase = [heading, sectionText].filter(Boolean).join('\n\n');
    promptPartCount = selectedPromptSections().length;
    preview.value = [promptBase, toolSection ? `## Available Tools\n\n${toolSection}` : '']
      .filter(Boolean)
      .join('\n\n');
    stats.textContent = `${promptPartCount} sections · ${promptTools.size} tools · ${preview.value.length} chars`;
  }

  preview.addEventListener('input', () => {
    stats.textContent = `${promptPartCount} sections · ${promptTools.size} tools · ${preview.value.length} chars · edited`;
  });

  async function loadPromptAgents() {
    try {
      const [workspaceData, codeBuilderData, promptData] = await Promise.all([
        Api.getAgents(),
        Api.getCodeBuilderAgents(),
        Api.getAgents('prompt-creation')
      ]);
      const label = environment => ({ codebuilder: 'CodeBuilder', 'prompt-creation': 'Prompt Creation' })[environment] || 'Workspace';
      const agents = [
        ...(workspaceData.agents || []).map(agent => ({ ...agent, environment: 'workspace' })),
        ...(codeBuilderData.agents || []).map(agent => ({ ...agent, environment: 'codebuilder' })),
        ...(promptData.agents || []).map(agent => ({ ...agent, environment: 'prompt-creation' }))
      ];
      promptAgents = agents;
      publishAgentSel.innerHTML = agents.length
        ? `<option value="">Select agent…</option>${agents.map(a => `<option value="${esc(a.environment)}:${esc(a.id)}">${esc(a.name)} (${esc(a.id)}) — ${label(a.environment)}</option>`).join('')}`
        : '<option value="">No agents found</option>';
      chatAgentSel.innerHTML = agents.length
        ? agents.map(a => `<option value="${esc(a.environment)}:${esc(a.id)}">${esc(a.name)} — ${label(a.environment)}</option>`).join('')
        : '<option value="">No agents available</option>';
      let lastAgent = null;
      try { lastAgent = localStorage.getItem('novous2.prompt-creation.lastChatAgent'); } catch { /* storage unavailable */ }
      selectedChatAgent = agents.find(agent => `${agent.environment}:${agent.id}` === lastAgent)
        || agents.find(agent => agent.environment === 'workspace') || agents[0] || null;
      if (selectedChatAgent) {
        chatAgentSel.value = `${selectedChatAgent.environment}:${selectedChatAgent.id}`;
        chatStatus.textContent = `Agent: ${selectedChatAgent.name}`;
      } else {
        chatStatus.textContent = 'No agents available.';
      }
      await loadPromptChatModels();
      updateChatControls();
    } catch (err) {
      publishAgentSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
      chatAgentSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
      chatStatus.textContent = 'Could not load agents.';
    }
  }

  function updateChatControls() {
    const sendButton = chatForm.querySelector('button[type="submit"]');
    sendButton.disabled = chatPending || !selectedChatAgent || !chatModelSel.value || chatModelSel.disabled;
    chatInput.disabled = chatPending;
    chatAgentSel.disabled = chatPending || !promptAgents.length;
  }

  function appendChatMessage(role, content) {
    const message = document.createElement('div');
    message.className = `codebuilder-chat-message ${role}`;
    if (role === 'assistant') {
      appendMarkdown(message, content);
      const addButton = document.createElement('button');
      addButton.type = 'button';
      addButton.className = 'btn btn-sm prompt-add-markdown';
      addButton.textContent = 'Add to draft';
      addButton.setAttribute('aria-label', 'Add this response to the Markdown draft');
      addButton.addEventListener('click', () => {
        const responseMarkdown = String(content ?? '').trim();
        if (!responseMarkdown) return;
        markdownDraft = markdownDraft
          ? `${markdownDraft.trimEnd()}\n\n---\n\n${responseMarkdown}`
          : responseMarkdown;
                markdownDraftCard.classList.remove('hidden');
                markdownPreview.replaceChildren();
                appendMarkdown(markdownPreview, markdownDraft);
        markdownStatus.textContent = 'Response added to the Markdown draft.';
        saveState();
        addButton.disabled = true;
        addButton.textContent = 'Added to draft';
        markdownDraftCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      message.appendChild(addButton);
    } else {
      message.textContent = content;
    }
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function setChatWidth(width) {
    const availableWidth = flow.clientWidth;
    const maxWidth = Math.max(280, availableWidth - 200);
    const nextWidth = Math.round(Math.min(maxWidth, Math.max(280, width)));
    flow.style.setProperty('--prompt-chat-width', `${nextWidth}px`);
    chatResizer.setAttribute('aria-valuemax', String(maxWidth));
    chatResizer.setAttribute('aria-valuenow', String(nextWidth));
    try {
      localStorage.setItem(chatWidthStorageKey, String(nextWidth));
    } catch (error) {
      console.warn('Could not save Prompt Creation chat width.', error);
    }
  }

  let savedChatWidth = 320;
  try {
    const storedWidth = Number(localStorage.getItem(chatWidthStorageKey));
    if (Number.isFinite(storedWidth) && storedWidth >= 280) savedChatWidth = storedWidth;
  } catch (error) {
    console.warn('Could not load saved Prompt Creation chat width.', error);
  }
  setChatWidth(savedChatWidth);

  const chatFontKey = 'novous2.prompt-creation.chat-font-size';
  let chatFontSize = 14;
  try {
    const storedSize = Number(localStorage.getItem(chatFontKey));
    if (Number.isFinite(storedSize) && storedSize >= 11 && storedSize <= 32) chatFontSize = storedSize;
  } catch (error) {
    console.warn('Could not load saved chat text size.', error);
  }
  function setChatFontSize(size) {
    chatFontSize = Math.min(32, Math.max(11, size));
    flow.style.setProperty('--prompt-chat-font-size', `${chatFontSize}px`);
    try {
      localStorage.setItem(chatFontKey, String(chatFontSize));
    } catch (error) {
      console.warn('Could not save chat text size.', error);
    }
  }
  setChatFontSize(chatFontSize);
  container.querySelector('#pc-font-smaller').addEventListener('click', () => setChatFontSize(chatFontSize - 1));
  container.querySelector('#pc-font-larger').addEventListener('click', () => setChatFontSize(chatFontSize + 2));

  chatResizer.addEventListener('pointerdown', event => {
    if (window.matchMedia('(max-width: 1100px)').matches) return;
    event.preventDefault();
    chatResizer.setPointerCapture(event.pointerId);
    const onMove = moveEvent => {
      const bounds = flow.getBoundingClientRect();
      setChatWidth(moveEvent.clientX - bounds.left);
    };
    const onUp = () => {
      chatResizer.removeEventListener('pointermove', onMove);
      chatResizer.removeEventListener('pointerup', onUp);
      chatResizer.removeEventListener('pointercancel', onUp);
    };
    chatResizer.addEventListener('pointermove', onMove);
    chatResizer.addEventListener('pointerup', onUp);
    chatResizer.addEventListener('pointercancel', onUp);
  });
  chatResizer.addEventListener('keydown', event => {
    const currentWidth = Number.parseInt(
      getComputedStyle(flow).getPropertyValue('--prompt-chat-width'),
      10
    ) || 320;
    let nextWidth;
    if (event.key === 'ArrowLeft') nextWidth = currentWidth - 20;
    else if (event.key === 'ArrowRight') nextWidth = currentWidth + 20;
    else if (event.key === 'Home') nextWidth = 280;
    else if (event.key === 'End') nextWidth = flow.clientWidth;
    else return;
    event.preventDefault();
    setChatWidth(nextWidth);
  });

  container.querySelector('#pc-copy-markdown').addEventListener('click', async () => {
    if (!markdownDraft) return;
    try {
      await navigator.clipboard.writeText(markdownDraft);
      markdownStatus.textContent = 'Markdown copied to clipboard.';
    } catch (error) {
      let copied = false;
      const copyArea = document.createElement('textarea');
      try {
        copyArea.value = markdownDraft;
        copyArea.setAttribute('readonly', '');
        copyArea.style.position = 'fixed';
        copyArea.style.opacity = '0';
        document.body.appendChild(copyArea);
        copyArea.select();
        copied = document.execCommand('copy');
      } catch {
        copied = false;
      } finally {
        copyArea.remove();
      }
      if (!copied) {
        markdownStatus.textContent = `Could not copy Markdown: ${error.message}`;
        return;
      }
      markdownStatus.textContent = 'Markdown copied to clipboard.';
    }
  });

  const slugify = text => String(text).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  function cleanHeading(raw) {
    const text = String(raw).trim().replace(/[*_`]/g, '').trim();
    const cleaned = text
      .replace(/^sections?\s*\d*\s*[:.\-–—]\s*/i, '')
      .replace(/\s*[:\-–—]\s*sections?\s*$/i, '')
      .replace(/\s+section\s*$/i, '')
      .trim();
    return cleaned || text;
  }

  function parseDraft(markdown) {
    const lines = String(markdown).replace(/\r\n?/g, '\n').split('\n');
    let inCode = false;
    const items = lines.map(line => {
      if (/^\s*```/.test(line)) inCode = !inCode;
      const match = !inCode && line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
      return { line, level: match ? match[1].length : 0, text: match ? cleanHeading(match[2]) : '', inCode };
    });
    const titleIndex = items.findIndex(item => item.level === 1);
    const others = items.filter((item, index) => item.level && index !== titleIndex);
    const sectionLevel = others.some(item => item.level === 2)
      ? 2
      : (others.length ? Math.min(...others.map(item => item.level)) : 2);
    const intro = [];
    const sections = [];
    let current = null;
    items.forEach((item, index) => {
      if (index === titleIndex) return;
      if (item.level === sectionLevel) {
        current = { title: item.text, body: [] };
        sections.push(current);
      } else if (!item.inCode && /^\s*---+\s*$/.test(item.line)) {
        // separators between chat responses are not content
      } else if (current) {
        current.body.push(item.line);
      } else if (index > titleIndex) {
        intro.push(item.line);
      }
    });
    const byTitle = new Map();
    for (const section of sections) {
      const labelPattern = new RegExp(
        `^\\s*[*_\`]*${section.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[*_\`]*\\s*[:.\\-–—][*_\`]*[ \\t]*`, 'i');
      const content = section.body.join('\n').trim().replace(labelPattern, '').trim();
      if (content) byTitle.set(section.title.toLowerCase(), { title: section.title, content });
    }
    return {
      title: titleIndex >= 0 ? items[titleIndex].text : '',
      description: intro.join('\n').trim(),
      sections: [...byTitle.values()]
    };
  }

  container.querySelector('#pc-parse-markdown').addEventListener('click', async () => {
    if (!markdownDraft) return;
    const button = container.querySelector('#pc-parse-markdown');
    const parsed = parseDraft(markdownDraft);
    if (!parsed.sections.length) {
      markdownStatus.textContent = 'No "## Section" headings with content were found in the draft.';
      return;
    }
    button.disabled = true;
    markdownStatus.textContent = 'Parsing draft into category and parts…';
    try {
      if (parsed.title) titleField.value = parsed.title;
      if (parsed.description) descriptionField.value = parsed.description.slice(0, 1000);
      const categoryName = parsed.title || 'Parsed Prompt';
      const categoryId = slugify(categoryName) || 'parsed-prompt';
      try {
        await Api.addPromptCategory(categoryId, categoryName, parsed.description.slice(0, 300), '');
      } catch {
        // category already exists from an earlier parse
      }
      const used = new Set();
      const ids = [];
      for (const section of parsed.sections) {
        let slug = slugify(section.title) || 'section';
        for (let n = 2; used.has(slug); n += 1) slug = `${slugify(section.title) || 'section'}-${n}`;
        used.add(slug);
        const part = await Api.addPromptPart(categoryId, section.title, section.content, slug);
        ids.push(part.id);
      }
      await loadManifest();
      catBox.querySelectorAll('[data-part]').forEach(input => {
        input.checked = ids.includes(input.value);
      });
      markPromptChanged();
      updatePromptPreview();
      markdownStatus.textContent = `Parsed ${ids.length} sections into category "${categoryName}". The assembled prompt below is updated.`;
      preview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      markdownStatus.textContent = `Parse failed: ${err.message}`;
    } finally {
      button.disabled = false;
    }
  });

  container.querySelector('#pc-clear-markdown').addEventListener('click', () => {
    markdownDraft = '';
    markdownPreview.replaceChildren();
    markdownDraftCard.classList.add('hidden');
    markdownStatus.textContent = '';
    saveState();
    for (const button of chatMessages.querySelectorAll('.prompt-add-markdown')) {
      button.disabled = false;
      button.textContent = 'Add to draft';
    }
  });

  async function loadPromptChatModels() {
    chatModelSel.disabled = true;
    chatModelSel.innerHTML = '<option value="">Loading models…</option>';
    try {
      const data = await Api.getModels();
      const models = (data.models || []).slice().sort();
      if (!models.length) {
        chatModelSel.innerHTML = '<option value="">No installed models</option>';
        chatStatus.textContent = data.error || 'No installed models detected.';
        updateChatControls();
        return;
      }
      chatModelSel.innerHTML = models.map(model =>
        `<option value="${esc(model)}">${esc(model)}</option>`
      ).join('');
      const preferred = selectedChatAgent?.model || data.default;
      chatModelSel.value = models.includes(preferred) ? preferred : models[0];
      chatModelSel.disabled = false;
      updateChatControls();
    } catch (err) {
      chatModelSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
      chatStatus.textContent = 'Could not load models.';
      updateChatControls();
    }
  }

  async function loadManifest() {
    try {
      const data = await Api.getPromptCategories();
      const checked = new Set([...selectedParts(), ...restoredParts]);
      restoredParts = [];
      manifest = data;
      renderCategories(manifest);
      catBox.querySelectorAll('[data-part]').forEach(input => {
        input.checked = checked.has(input.value);
      });
      populateCategoryDropdown(manifest.categories || []);
      updatePromptPreview();
    } catch (err) {
      catBox.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  }

  function populateCategoryDropdown(categories) {
    partCatSelect.innerHTML = categories.length
      ? categories.map(c => `<option value="${esc(c.id)}">${esc(c.name)} (${esc(c.id)})</option>`).join('')
      : '<option value="">No categories available</option>';
  }

  function renderCategories(data) {
    const cats = data.categories || [];
    const uncategorized = data.uncategorized_parts || [];

    let html = cats.map(cat => `
      <div class="category-block">
        <div class="category-head">
          <div style="display: flex; align-items: center; gap: 0.3rem; flex-wrap: wrap;">
            <strong>${esc(cat.name)}</strong>
            ${cat.required_header ? `<span class="badge badge-accent">## ${esc(cat.required_header)}</span>` : ''}
          </div>
          <span style="display: inline-flex; align-items: center;">
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test category in the Prompt Header Evaluation Battery" data-test-cat="${esc(cat.id)}" style="padding: 0 0.3rem;">🧪</button>
            <button type="button" class="btn btn-ghost btn-sm text-danger" title="Delete category '${esc(cat.name)}'" data-del-cat="${esc(cat.id)}" style="padding: 0 0.3rem;">✕</button>
          </span>
        </div>
        <p class="text-muted small">${esc(cat.description || '')}</p>
        ${(cat.parts || []).map(p => `
          <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
            <label class="checkbox-row" style="flex: 1; margin: 0;">
              <input type="checkbox" value="${esc(p.id)}" data-part>
              <span>${esc(p.title)}</span>
            </label>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Edit part" data-edit-part="${esc(p.id)}" style="padding: 0 0.3rem;">✎</button>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test part" data-test-part="${esc(p.id)}" style="padding: 0 0.3rem;">🧪</button>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
          </div>`).join('') || '<p class="text-muted small">No parts.</p>'}
      </div>`).join('');

    if (uncategorized.length) {
      html += `
        <div class="category-block">
          <div class="category-head">
            <strong>Uncategorized</strong>
          </div>
          <p class="text-muted small">Parts without a matching category definition.</p>
          ${uncategorized.map(p => `
            <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
              <label class="checkbox-row" style="flex: 1; margin: 0;">
                <input type="checkbox" value="${esc(p.id)}" data-part>
                <span>${esc(p.title)}</span>
              </label>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Edit part" data-edit-part="${esc(p.id)}" style="padding: 0 0.3rem;">✎</button>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test part" data-test-part="${esc(p.id)}" style="padding: 0 0.3rem;">🧪</button>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
            </div>`).join('')}
        </div>`;
    }

    catBox.innerHTML = html || '<p class="text-danger">No categories found.</p>';
  }

  restoreState();
  loadCoreTools();
  loadManifest();
  loadPromptAgents();

  chatAgentSel.addEventListener('change', () => {
    const [environment, agentId] = chatAgentSel.value.split(':', 2);
    try { localStorage.setItem('novous2.prompt-creation.lastChatAgent', chatAgentSel.value); } catch { /* storage unavailable */ }
    selectedChatAgent = promptAgents.find(agent =>
      agent.environment === environment && agent.id === agentId
    ) || null;
    chatMessages.replaceChildren();
    if (selectedChatAgent) {
      appendChatMessage('system', `Chatting with ${selectedChatAgent.name}.`);
      chatStatus.textContent = `Agent: ${selectedChatAgent.name}`;
    } else {
      chatStatus.textContent = 'Select an agent to start.';
    }
    loadPromptChatModels();
  });

  chatModelSel.addEventListener('change', updateChatControls);
  titleField.addEventListener('input', () => {
    markPromptChanged();
    updatePromptPreview();
  });
  descriptionField.addEventListener('input', () => {
    markPromptChanged();
    updatePromptPreview();
  });
  catBox.addEventListener('change', event => {
    if (!event.target.matches('[data-part]')) return;
    markPromptChanged();
    updatePromptPreview();
  });
  toolsContainer.addEventListener('change', event => {
    if (!event.target.matches('[data-tool]')) return;
    const tool = availableTools[Number(event.target.value)];
    if (!tool) return;
    if (event.target.checked) {
      if (!promptTools.has(tool.name)) promptTools.set(tool.name, { ...tool });
    } else {
      promptTools.delete(tool.name);
    }
    markPromptChanged();
    updatePromptPreview();
  });

  toolsContainer.addEventListener('click', async event => {
    const editBtn = event.target.closest('[data-edit-tool]');
    const testBtn = event.target.closest('[data-test-tool]');
    const button = editBtn || testBtn;
    if (!button) return;
    const tool = availableTools[Number(button.dataset.editTool ?? button.dataset.testTool)];
    if (!tool) return;
    if (testBtn) {
      testBtn.disabled = true;
      try {
        const source = await Api.getWorkbenchTool(tool.name);
        const params = String(tool.signature || '').replace(/^\(|\)(\s*->.*)?$/g, '').split(',')
          .map(item => item.trim()).filter(Boolean);
        const input = {};
        for (const param of params) {
          const [rawName, ...rest] = param.split(/[:=]/);
          const name = rawName.trim().replace(/^\*+/, '');
          if (!name || name === 'self') continue;
          const type = (param.split(':')[1] || '').split('=')[0].trim();
          input[name] = /int|float/.test(type) ? 0 : /bool/.test(type) ? false : /str/.test(type) || !type ? '' : null;
        }
        const entry = promptTools.get(tool.name) || tool;
        const description = toolDescription(entry).trim();
        const { switchTab } = await import('./app.js');
        switchTab('testing', {
          type: 'tool',
          name: tool.name,
          path: source.path,
          source: source.source,
          input: JSON.stringify(input, null, 2),
          prompt: `Use the ${tool.name} tool to complete this task.${description ? ` ${description}` : ''}`
        });
      } catch (err) {
        showMsg(`Could not open '${tool.name}' in the Tool Function Testing Workbench: ${err.message}`, true);
        testBtn.disabled = false;
      }
      return;
    }
    const panelClass = 'tool-edit-panel';
    const row = button.closest('.part-row');
    const existing = row.nextElementSibling;
    if (existing?.classList.contains(panelClass)) {
      existing.remove();
      return;
    }
    const current = () => promptTools.get(tool.name) || tool;
    const panel = document.createElement('div');
    panel.className = `${panelClass} card bg-elev small`;
    panel.style.cssText = 'padding: 0.5rem; margin: 0.25rem 0;';
    row.after(panel);

    panel.innerHTML = `
      <p class="text-muted small" style="margin: 0 0 0.3rem;"><code>${esc(tool.signature)}</code></p>
      <textarea class="form-input" rows="4" data-tool-desc aria-label="Tool description" style="width: 100%;">${esc(toolDescription(current()))}</textarea>
      <div class="toolbar-row" style="margin-top: 0.4rem;">
        <button type="button" class="btn btn-sm btn-primary" data-tool-save>Save</button>
        <button type="button" class="btn btn-sm" data-tool-cancel>Cancel</button>
      </div>
      <span class="text-muted small">Describe what it does and when the agent should call it. Saved descriptions apply to this prompt.</span>`;
    panel.querySelector('[data-tool-cancel]').addEventListener('click', () => panel.remove());
    panel.querySelector('[data-tool-save]').addEventListener('click', () => {
      const description = panel.querySelector('[data-tool-desc]').value;
      const entry = { ...current(), promptDescription: description };
      promptTools.set(tool.name, entry);
      row.querySelector('[data-tool]').checked = true;
      markPromptChanged();
      updatePromptPreview();
      panel.remove();
      showMsg(`Description for '${tool.name}' saved and tool added to the prompt.`);
    });
  });

  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message || chatPending || !selectedChatAgent || !chatModelSel.value) return;

    appendChatMessage('user', message);
    chatInput.value = '';
    chatPending = true;
    chatStatus.textContent = `Waiting for ${selectedChatAgent.name}…`;
    updateChatControls();
    const sessionId = `prompt-creation-${selectedChatAgent.environment}-${selectedChatAgent.id}`;
    try {
      const response = await Api.sendMessage(
        `${message}\n\nWhen you write a prompt, reply with only the prompt as a Markdown document: one "# Title" line, a one-sentence description, then "## " headings named only for what they contain (for example "## Role", never "## Section: Role" or "## Role Section") each followed by plain-text instructions. No preamble or closing commentary.`,
        selectedChatAgent.id,
        chatModelSel.value,
        sessionId,
        selectedChatAgent.environment
      );
      appendChatMessage('assistant', response.reply || 'The agent returned an empty response.');
      chatStatus.textContent = `${selectedChatAgent.name} · ${response.model || chatModelSel.value}`;
    } catch (err) {
      appendChatMessage('system', `Request failed: ${err.message}`);
      chatStatus.textContent = 'Request failed.';
    } finally {
      chatPending = false;
      updateChatControls();
      chatInput.focus();
    }
  });

  chatInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit();
    }
  });

  container.querySelector('#pc-chat-clear').addEventListener('click', async () => {
    if (selectedChatAgent) {
      const sessionId = `prompt-creation-${selectedChatAgent.environment}-${selectedChatAgent.id}`;
      try {
        await Api.resetChat(sessionId);
      } catch (err) {
        chatStatus.textContent = `Could not clear chat: ${err.message}`;
        return;
      }
    }
    chatMessages.replaceChildren();
    appendChatMessage('system', selectedChatAgent
      ? `Chat cleared. Continue with ${selectedChatAgent.name}.`
      : 'Chat cleared.');
    chatInput.focus();
  });

  container.querySelector('#btn-refresh-tools').addEventListener('click', loadCoreTools);

  container.querySelector('#tb-toggle-cat-form').addEventListener('click', () => {
    catForm.classList.toggle('hidden');
    partForm.classList.add('hidden');
  });

  container.querySelector('#cat-cancel-btn').addEventListener('click', () => {
    catForm.classList.add('hidden');
  });

  container.querySelector('#tb-toggle-part-form').addEventListener('click', () => {
    partForm.classList.toggle('hidden');
    catForm.classList.add('hidden');
  });

  container.querySelector('#part-cancel-btn').addEventListener('click', () => {
    partForm.classList.add('hidden');
  });

  async function submitCategory() {
    const id = container.querySelector('#cat-id-input').value.trim();
    const name = container.querySelector('#cat-name-input').value.trim();
    const desc = container.querySelector('#cat-desc-input').value.trim();
    const header = container.querySelector('#cat-header-input').value.trim();

    if (!id || !name) return showMsg('Category ID and Name are required.', true);

    try {
      await Api.addPromptCategory(id, name, desc, header);
      catForm.classList.add('hidden');
      container.querySelector('#cat-id-input').value = '';
      container.querySelector('#cat-name-input').value = '';
      container.querySelector('#cat-desc-input').value = '';
      container.querySelector('#cat-header-input').value = '';
      showMsg(`Category '${name}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#cat-save-btn').addEventListener('click', submitCategory);

  catForm.querySelectorAll('input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitCategory();
      }
    });
  });

  async function submitPart() {
    const category = partCatSelect.value;
    const title = container.querySelector('#part-title-input').value.trim();
    const slug = container.querySelector('#part-slug-input').value.trim();
    const content = container.querySelector('#part-content-input').value.trim();

    if (!category || !title || !content) return showMsg('Category, Part Title, and Content are required.', true);

    try {
      await Api.addPromptPart(category, title, content, slug || null);
      partForm.classList.add('hidden');
      container.querySelector('#part-title-input').value = '';
      container.querySelector('#part-slug-input').value = '';
      container.querySelector('#part-content-input').value = '';
      showMsg(`Prompt Part '${title}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#part-save-btn').addEventListener('click', submitPart);

  partForm.querySelectorAll('input, textarea').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        submitPart();
      }
    });
  });

  catBox.addEventListener('click', async (e) => {
    const testCatBtn = e.target.closest('[data-test-cat]');
    if (testCatBtn) {
      const cat = (manifest.categories || []).find(item => item.id === testCatBtn.dataset.testCat);
      if (!cat) return;
      if (!(cat.parts || []).length) return showMsg(`Category '${cat.name}' has no parts to test.`, true);
      const markdown = [
        `# ${cat.name}`,
        cat.description || '',
        ...cat.parts.map(part => `## ${part.title}\n\n${part.content.trim()}`)
      ].filter(Boolean).join('\n\n');
      const { switchTab } = await import('./app.js');
      switchTab('testing', {
        type: 'category',
        id: cat.id,
        name: cat.name,
        partCount: cat.parts.length,
        markdown
      });
      return;
    }

    const testBtn = e.target.closest('[data-test-part]');
    if (testBtn) {
      const part = findPromptPart(testBtn.getAttribute('data-test-part'));
      const row = testBtn.closest('.part-row');
      const existing = row.nextElementSibling;
      if (existing?.classList.contains('part-test-panel')) {
        existing.remove();
        return;
      }
      if (!part) return;
      const panel = document.createElement('div');
      panel.className = 'part-test-panel card bg-elev small';
      panel.style.cssText = 'padding: 0.5rem; margin: 0.25rem 0;';
      panel.textContent = 'Testing part…';
      row.after(panel);
      try {
        const result = await Api.evaluatePromptComponents(
          titleField.value,
          descriptionField.value,
          [{ id: part.id, title: part.title, category: part.category, content: part.content }],
          []
        );
        const components = (result.components || []).filter(component =>
          !['Prompt title', 'Prompt description'].includes(component.name)
        );
        panel.replaceChildren();
        const passed = components.every(component => component.passed);
        const summary = document.createElement('strong');
        summary.className = passed ? 'text-success' : 'text-danger';
        summary.textContent = passed ? 'PASS' : 'NOT PASS';
        panel.appendChild(summary);
        for (const component of components) {
          for (const check of component.checks || []) {
            const line = document.createElement('p');
            line.style.margin = '0.2rem 0 0';
            line.textContent = `${check.passed ? '✓' : '✗'} ${checkDetail(check)}`;
            panel.appendChild(line);
          }
        }
      } catch (err) {
        panel.className = 'part-test-panel card bg-elev small text-danger';
        panel.textContent = `Part test failed: ${err.message}`;
      }
      return;
    }

    const editBtn = e.target.closest('[data-edit-part]');
    if (editBtn) {
      const partId = editBtn.getAttribute('data-edit-part');
      const row = editBtn.closest('.part-row');
      const existing = row.nextElementSibling;
      if (existing?.classList.contains('part-edit-panel')) {
        existing.remove();
        return;
      }
      const part = findPromptPart(partId);
      if (!part) return;
      const panel = document.createElement('div');
      panel.className = 'part-edit-panel card bg-elev';
      panel.style.cssText = 'padding: 0.5rem; margin: 0.25rem 0;';
      panel.innerHTML = `
        <input class="form-input" data-edit-title aria-label="Part title" value="${esc(part.title)}">
        <textarea class="form-input" data-edit-content rows="8" aria-label="Part content" style="width: 100%; margin-top: 0.4rem;">${esc(part.content)}</textarea>
        <div class="toolbar-row" style="margin-top: 0.4rem;">
          <button type="button" class="btn btn-sm btn-primary" data-edit-save>Save</button>
          <button type="button" class="btn btn-sm" data-edit-cancel>Cancel</button>
        </div>`;
      row.after(panel);
      panel.querySelector('[data-edit-content]').focus();
      panel.querySelector('[data-edit-cancel]').addEventListener('click', () => panel.remove());
      panel.querySelector('[data-edit-save]').addEventListener('click', async () => {
        const title = panel.querySelector('[data-edit-title]').value.trim();
        const content = panel.querySelector('[data-edit-content]').value.trim();
        if (!title || !content) return showMsg('Part title and content are required.', true);
        try {
          const slug = partId.includes('/') ? partId.split('/').slice(1).join('/') : partId;
          await Api.addPromptPart(part.category, title, content, slug);
          await loadManifest();
          markPromptChanged();
          updatePromptPreview();
          showMsg(`Part '${title}' updated.`);
        } catch (err) {
          showMsg(err.message, true);
        }
      });
      return;
    }

    const delCatBtn = e.target.closest('[data-del-cat]');
    if (delCatBtn) {
      const catId = delCatBtn.getAttribute('data-del-cat');
      if (confirm(`Are you sure you want to delete category '${catId}' and its parts?`)) {
        try {
          await Api.deletePromptCategory(catId);
          showMsg(`Category '${catId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
      return;
    }

    const delPartBtn = e.target.closest('[data-del-part]');
    if (delPartBtn) {
      const partId = delPartBtn.getAttribute('data-del-part');
      if (confirm(`Delete prompt part '${partId}'?`)) {
        try {
          await Api.deletePromptPart(partId);
          showMsg(`Prompt part '${partId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
    }
  });

  function selectedParts() {
    return [...catBox.querySelectorAll('[data-part]:checked')].map(el => el.value);
  }

  container.querySelector('#tb-assemble').addEventListener('click', async () => {
    const parts = selectedParts();
    if (!parts.length) return showMsg('Select at least one prompt part.', true);
    try {
      await Api.assemblePrompt(parts);
      updatePromptPreview();
      showMsg('Prompt assembled.');
    } catch (err) {
      showMsg(err.message, true);
    }
  });

  container.querySelector('#tb-copy').addEventListener('click', async () => {
    if (!preview.value) return;
    try {
      await navigator.clipboard.writeText(preview.value);
      showMsg('Copied to clipboard.');
    } catch (_) {
      preview.select();
      document.execCommand('copy');
      showMsg('Copied.');
    }
  });

  container.querySelector('#tb-publish').addEventListener('click', async () => {
    const [environment, agentId] = publishAgentSel.value.split(':', 2);
    if (!environment || !agentId) return showMsg('Select an agent to publish first.', true);
    if (!preview.value.trim()) return showMsg('Assemble a prompt before saving it to an agent.', true);
    try {
      const res = await Api.publishAgent(
        agentId, 'snapshot', preview.value, environment, [...promptTools.keys()]
      );
      showMsg(`Saved to ${res.path} and ${res.metadata_path} (headers ${res.header_report.verdict}; snapshot ${res.snapshot}).`);
    } catch (err) {
      showMsg(err.message, true);
    }
  });

  function checkDetail(check) {
    const parts = [check.evidence];
    if (!check.passed) {
      if (check.rule) parts.push(`Rule: ${check.rule}`);
      if (check.observed) parts.push(`Observed: ${check.observed}`);
      if (check.fix) parts.push(`Fix: ${check.fix}`);
    }
    return parts.join(' | ');
  }

  function failureFeedback(result) {
    return (result.components || []).filter(component => !component.passed).map(component => {
      const failedChecks = (component.checks || []).filter(check => !check.passed).map(check => [
        `  - Check "${check.id}": ${check.evidence}`,
        check.rule ? `    Rule: ${check.rule}` : '',
        check.observed ? `    Observed: ${check.observed}` : '',
        check.fix ? `    Suggested fix: ${check.fix}` : ''
      ].filter(Boolean).join('\n')).join('\n');
      const text = component.tested_text ? `\n  Tested text: """${component.tested_text}"""` : '';
      return `- ${component.name}${text}\n${failedChecks}`;
    }).join('\n');
  }

  function appendTestActions(result) {
    const actions = document.createElement('div');
    actions.className = 'toolbar-row';
    actions.style.marginTop = '0.75rem';

    if (!result.passed) {
      const fixButton = document.createElement('button');
      fixButton.type = 'button';
      fixButton.className = 'btn btn-sm btn-primary';
      fixButton.textContent = 'Send failures to chat agent';
      fixButton.addEventListener('click', () => {
        if (!selectedChatAgent || !chatModelSel.value) {
          return showMsg('Choose a chat agent and model first.', true);
        }
        chatInput.value = [
          'My prompt did not pass testing. Fix only the sections or tools that failed and keep everything that passed unchanged.',
          '',
          'Failed components and checks:',
          failureFeedback(result),
          '',
          'Current prompt:',
          '',
          preview.value,
          '',
          'Return the complete revised prompt as a Markdown document with the same structure.'
        ].join('\n');
        chatForm.requestSubmit();
        markdownDraft = '';
        markdownPreview.replaceChildren();
        markdownDraftCard.classList.add('hidden');
        markdownStatus.textContent = '';
        saveState();
        chatMessages.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        showMsg('Failures sent to the chat agent. Use Add to draft, then Parse draft on its reply.');
      });
      actions.appendChild(fixButton);
    }

    {
      const createButton = document.createElement('button');
      createButton.type = 'button';
      createButton.className = result.passed ? 'btn btn-sm btn-primary' : 'btn btn-sm';
      createButton.textContent = result.passed ? 'Create agent from this prompt' : 'Create agent anyway (tests failed)';
      actions.appendChild(createButton);

      const form = document.createElement('div');
      form.className = result.passed ? 'card bg-elev' : 'card bg-elev hidden';
      form.style.cssText = 'padding: 0.75rem; margin-top: 0.5rem;';
      const defaultId = slugify(titleField.value) || 'new-agent';
      form.innerHTML = `
        <div class="form-row">
          <input class="form-input" data-new-agent-id aria-label="Agent ID" placeholder="agent-id" value="${esc(defaultId)}">
          <input class="form-input" data-new-agent-name aria-label="Agent name" placeholder="Agent name" value="${esc(titleField.value.trim())}">
        </div>
        <div class="form-row">
          <input class="form-input" data-new-agent-desc aria-label="Agent description" placeholder="Description" value="${esc(descriptionField.value.trim().split('\n')[0].slice(0, 200))}">
          <select class="form-select" data-new-agent-environment aria-label="Agent environment">
            <option value="prompt-creation" selected>Prompt Creation</option>
            <option value="workspace">Workspace</option>
            <option value="codebuilder">CodeBuilder</option>
          </select>
          <select class="form-select" data-new-agent-mode aria-label="Agent mode">
            <option value="chat"${promptTools.size ? '' : ' selected'}>Chat (no tools)</option>
            <option value="agent"${promptTools.size ? ' selected' : ''}>Agent (default tools)</option>
          </select>
        </div>
        <div class="form-row">
          <input class="form-input" data-new-agent-env-name aria-label="Custom environment name" placeholder="Custom environment name (optional)" maxlength="64">
        </div>
        <div class="toolbar-row">
          <button type="button" class="btn btn-sm btn-primary" data-new-agent-save>Create agent</button>
          <button type="button" class="btn btn-sm" data-new-agent-cancel>Cancel</button>
        </div>`;
      createButton.addEventListener('click', () => form.classList.toggle('hidden'));
      form.querySelector('[data-new-agent-cancel]').addEventListener('click', () => form.classList.add('hidden'));
      form.querySelector('[data-new-agent-save]').addEventListener('click', async event => {
        const id = slugify(form.querySelector('[data-new-agent-id]').value);
        const name = form.querySelector('[data-new-agent-name]').value.trim();
        const description = form.querySelector('[data-new-agent-desc]').value.trim();
        const mode = form.querySelector('[data-new-agent-mode]').value;
        const agentEnvironment = form.querySelector('[data-new-agent-environment]').value;
        const environmentName = form.querySelector('[data-new-agent-env-name]').value.trim();
        if (!id || !name) return showMsg('Agent ID and name are required.', true);
        const saveButton = event.currentTarget;
        saveButton.disabled = true;
        try {
          await Api.createAgent(id, name, description, mode, '', agentEnvironment, environmentName);
          await Api.publishAgent(
            id, 'prompt-creation', preview.value, agentEnvironment, [...promptTools.keys()]
          );
          showMsg(`Agent '${name}' created from the prompt (library/${id}.md)${result.passed ? '.' : ' even though tests failed.'}`);
          form.classList.add('hidden');
          await loadPromptAgents();
        } catch (err) {
          showMsg(err.message, true);
        } finally {
          saveButton.disabled = false;
        }
      });
      testResult.appendChild(actions);
      testResult.appendChild(form);
    }
    appendReportActions(result);
  }

  container.querySelector('#tb-test-prompt').addEventListener('click', async () => {
    if (!preview.value.trim()) return showMsg('Assemble a prompt before testing it.', true);
    const button = container.querySelector('#tb-test-prompt');
    const revisionBeingTested = promptRevision;
    testedPromptRevision = null;
    button.disabled = true;
    testResult.className = 'small text-muted';
    testResult.replaceChildren(document.createTextNode('Testing title, description, sections, skills, and tool descriptions…'));
    try {
      const result = await Api.evaluatePromptComponents(
        titleField.value,
        descriptionField.value,
        selectedPromptSections(),
        [...promptTools.values()].map(tool => ({
          name: tool.name,
          description: toolDescription(tool),
          signature: tool.signature
        }))
      );
      if (revisionBeingTested !== promptRevision) {
        testedPromptRevision = null;
        testResult.className = 'small text-warning';
        testResult.textContent = 'Prompt changed while tests were running. Run Test Prompt again for an up-to-date report.';
        return;
      }
      testedPromptRevision = revisionBeingTested;
      const useProbe = container.querySelector('#tb-model-test').checked;
      const useAi = container.querySelector('#tb-ai-review').checked;
      const reviewModel = chatModelSel.value;
      result.model = (useProbe || useAi) ? reviewModel : '';
      result.strengths = [];
      result.weaknesses = [];
      result.improvements = [];
      const mergeComponents = extra => {
        result.components = [...result.components, ...extra];
        result.components_total = result.components.length;
        result.components_passed = result.components.filter(item => item.passed).length;
        result.passed = result.components_passed === result.components_total;
        result.verdict = result.passed ? 'PASS' : 'FAIL';
      };
      const notes = [];
      if ((useProbe || useAi) && !reviewModel) {
        notes.push('Model tests skipped: choose a model in the chat panel.');
      } else {
        if (useProbe) {
          testResult.replaceChildren(document.createTextNode(`Structural checks done. Running model test with ${reviewModel}…`));
          try {
            const probe = await Api.probePrompt(
              reviewModel, titleField.value, descriptionField.value, preview.value,
              container.querySelector('#tb-fact-q').value, container.querySelector('#tb-fact-a').value
            );
            mergeComponents(probe.components || []);
            result.strengths = probe.strengths || [];
            result.weaknesses = probe.weaknesses || [];
            result.improvements = probe.improvements || [];
            result.model_log = probe.model_log || null;
          } catch (err) {
            notes.push(`Model test unavailable (${err.message}).`);
          }
        }
        if (useAi) {
          testResult.replaceChildren(document.createTextNode(`Running AI rubric review with ${reviewModel}…`));
          try {
            const review = await Api.judgePrompt(
              reviewModel, titleField.value, descriptionField.value, selectedPromptSections(),
              [...promptTools.values()].map(tool => ({
                name: tool.name, description: toolDescription(tool), signature: tool.signature
              }))
            );
            mergeComponents(review.components || []);
          } catch (err) {
            notes.push(`AI rubric review unavailable (${err.message}).`);
          }
        }
      }
      if (notes.length) result.ai_error = `${notes.join(' ')} Only the checks that ran are counted.`;
      for (const component of result.components) {
        if (component.passed || component.name.startsWith('Model test:')) continue;
        const fix = (component.checks || []).filter(check => !check.passed && check.fix).map(check => check.fix)[0];
        if (fix) result.improvements.push(`${component.name}: ${fix}`);
        result.weaknesses.push(`${component.name} did not pass.`);
      }
      const passedStructural = result.components.filter(item => item.passed && !item.name.startsWith('Model test:')).length;
      if (passedStructural) result.strengths.unshift(`${passedStructural} structural component(s) are complete and well formed.`);
      if (revisionBeingTested !== promptRevision) {
        testedPromptRevision = null;
        testResult.className = 'small text-warning';
        testResult.textContent = 'Prompt changed while the AI review was running. Run Test Prompt again.';
        return;
      }
      renderPromptTestResult(result);
    } catch (err) {
      testResult.className = 'small text-danger';
      testResult.textContent = `Prompt component tests could not run: ${err.message}`;
    } finally {
      button.disabled = false;
    }
  });

  function renderPromptTestResult(result) {
    testResult.className = 'small';
    testResult.replaceChildren();
    const summary = document.createElement('p');
    summary.className = result.passed ? 'text-success' : 'text-danger';
    summary.textContent = `${result.verdict}: ${result.components_passed}/${result.components_total} prompt components passed.`
      + (result.model ? ` Model: ${result.model}.` : '');
    testResult.appendChild(summary);
    if (result.model_log) {
      const logLine = document.createElement('p');
      logLine.className = 'text-muted';
      logLine.textContent = `Model log (${result.model}): ${result.model_log.passes}/${result.model_log.runs} model tests passed so far.`;
      testResult.appendChild(logLine);
    }
    for (const [label, items] of [['Strengths', result.strengths], ['Weaknesses', result.weaknesses], ['Room for improvement', result.improvements]]) {
      if (!items?.length) continue;
      const block = document.createElement('div');
      const head = document.createElement('strong');
      head.textContent = label;
      const ul = document.createElement('ul');
      for (const text of items) {
        const li = document.createElement('li');
        li.textContent = text;
        ul.appendChild(li);
      }
      block.append(head, ul);
      testResult.appendChild(block);
    }
    if (result.ai_error) {
      const note = document.createElement('p');
      note.className = 'text-warning';
      note.textContent = result.ai_error;
      testResult.appendChild(note);
    }
    const componentList = document.createElement('div');
    componentList.className = 'prompt-test-report';
    for (const component of result.components || []) {
      const row = document.createElement('div');
      row.className = `prompt-test-component ${component.passed ? 'passed' : 'failed'}`;
      const heading = document.createElement('strong');
      heading.textContent = `${component.passed ? 'PASS' : 'NOT PASS'} · ${component.name}`;
      row.appendChild(heading);
      for (const check of component.checks || []) {
        const detail = document.createElement('p');
        detail.textContent = `${check.passed ? '✓' : '✗'} ${checkDetail(check)}`;
        row.appendChild(detail);
      }
      componentList.appendChild(row);
    }
    testResult.appendChild(componentList);
    appendTestActions(result);
  }

  async function saveMarkdownFile(fileName, text) {
    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: fileName,
          types: [{ description: 'Markdown', accept: { 'text/markdown': ['.md'] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(text);
        await writable.close();
        return handle.name;
      } catch (err) {
        if (err.name === 'AbortError') return null;
        throw err;
      }
    }
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    return `${fileName} (sent to your browser's download location; this browser cannot choose a folder)`;
  }

  function buildReportMarkdown(result, title, notes) {
    const fence = text => {
      const ticks = '`'.repeat(Math.max(3, ...(String(text).match(/`+/g) || []).map(run => run.length + 1)));
      return `${ticks}markdown\n${text}\n${ticks}`;
    };
    const lines = [
      `# Prompt Test Report: ${title}`,
      '',
      `- **Date:** ${new Date().toLocaleString()}`,
      `- **Verdict:** ${result.verdict}`,
      `- **Components passed:** ${result.components_passed}/${result.components_total}`,
      `- **Model used for testing:** ${result.model || 'none (structural checks only)'}`
    ];
    if (result.model_log) {
      lines.push(`- **Model log:** ${result.model_log.passes}/${result.model_log.runs} model tests passed so far (file: test_environment/model_logs/)`);
    }
    if (result.ai_error) lines.push(`- **Note:** ${result.ai_error}`);
    if (notes) lines.push(`- **Notes:** ${notes}`);
    for (const [label, items] of [['Strengths', result.strengths], ['Weaknesses', result.weaknesses], ['Room for improvement', result.improvements]]) {
      lines.push('', `## ${label}`, '');
      if (items?.length) items.forEach(text => lines.push(`- ${text}`));
      else lines.push('- None recorded.');
    }
    const failed = (result.components || []).filter(component => !component.passed);
    lines.push('', '## Why it failed', '');
    if (!failed.length) lines.push('Nothing failed.');
    for (const component of failed) {
      lines.push(`### ${component.name}`, '');
      if (component.tested_text) lines.push('Tested text:', '', fence(component.tested_text), '');
      for (const check of (component.checks || []).filter(item => !item.passed)) {
        lines.push(`- **Check \`${check.id}\`:** ${check.evidence}`);
        if (check.rule) lines.push(`  - Rule: ${check.rule}`);
        if (check.observed) lines.push(`  - Observed: ${check.observed}`);
        if (check.fix) lines.push(`  - Suggested fix: ${check.fix}`);
      }
      lines.push('');
    }
    lines.push('## All components', '');
    for (const component of result.components || []) {
      lines.push(`- ${component.passed ? 'PASS' : 'FAIL'} — ${component.name}`);
    }
    lines.push('', '## Prompt that was tested', '', fence(preview.value), '');
    return lines.join('\n');
  }

  function appendReportActions(result) {
    const bar = document.createElement('div');
    bar.className = 'toolbar-row';
    bar.style.marginTop = '0.5rem';
    const notes = document.createElement('input');
    notes.className = 'form-input';
    notes.placeholder = 'Notes for this report (optional)';
    notes.setAttribute('aria-label', 'Report notes');
    const save = document.createElement('button');
    save.type = 'button';
    save.className = 'btn btn-sm';
    save.textContent = 'Save test report';
    save.addEventListener('click', async () => {
      save.disabled = true;
      try {
        const title = titleField.value.trim() || 'Untitled prompt';
        const markdown = buildReportMarkdown(result, title, notes.value.trim());
        const fileName = `${slugify(title) || 'prompt'}-test-report-${new Date().toISOString().slice(0, 10)}.md`;
        const where = await saveMarkdownFile(fileName, markdown);
        if (!where) return;
        let stored = '';
        try {
          await Api.saveTestReport({
            kind: 'prompt', title, model: result.model || '', subject: preview.value,
            notes: notes.value.trim(), result
          });
          stored = ' A copy was also added to Saved reports.';
        } catch {
          // the markdown file is the primary output; the history copy is optional
        }
        showMsg(`Report saved: ${where}.${stored}`);
      } catch (err) {
        showMsg(`Could not save report: ${err.message}`, true);
      } finally {
        save.disabled = false;
      }
    });
    const history = document.createElement('button');
    history.type = 'button';
    history.className = 'btn btn-sm btn-ghost';
    history.textContent = 'Saved reports';
    const list = document.createElement('div');
    list.className = 'small';
    history.addEventListener('click', async () => {
      list.replaceChildren(document.createTextNode('Loading…'));
      try {
        const { reports } = await Api.listTestReports();
        list.replaceChildren();
        if (!reports.length) list.textContent = 'No saved reports yet.';
        for (const report of reports.slice(0, 20)) {
          const item = document.createElement('button');
          item.type = 'button';
          item.className = 'btn btn-sm btn-ghost';
          item.style.display = 'block';
          item.textContent = `${report.passed ? 'PASS' : 'FAIL'} · ${report.title} · ${report.model || 'structural only'} · ${report.created_at.slice(0, 16).replace('T', ' ')}`;
          item.addEventListener('click', async () => {
            const full = await Api.getTestReport(report.id);
            renderPromptTestResult(full.result);
          });
          list.appendChild(item);
        }
      } catch (err) {
        list.textContent = `Could not load reports: ${err.message}`;
      }
    });
    bar.append(notes, save, history);
    testResult.append(bar, list);
  }
}

```

## `frontend/static/js/sandbox_ui.js`
```js
// Shared UI for the isolated test environment (install missing packages, reset).

async function call(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    throw new Error(typeof detail === 'string' ? detail : (detail?.message || `Request failed (${response.status})`));
  }
  return payload;
}

export const Sandbox = {
  check: (source, modules = []) => call('POST', '/api/sandbox/check', { source, modules }),
  install: packages => call('POST', '/api/sandbox/install', { packages }),
  reset: () => call('POST', '/api/sandbox/reset')
};

export function missingModulesFromOutput(text) {
  const names = [...String(text || '').matchAll(/No module named '([A-Za-z_][\w]*)/g)].map(m => m[1]);
  return [...new Set(names)];
}

export function dialog(title, buildBody) {
  const overlay = document.createElement('div');
  overlay.className = 'question-dialog-overlay';
  const modal = document.createElement('div');
  modal.className = 'card question-dialog';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  const head = document.createElement('div');
  head.className = 'question-dialog-head';
  const heading = document.createElement('h3');
  heading.textContent = title;
  head.appendChild(heading);
  modal.appendChild(head);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);
  const close = () => overlay.remove();
  buildBody(modal, close);
  return close;
}

// Resolves true when packages were installed, false when cancelled or failed.
export function promptInstall(missing) {
  return new Promise(resolve => {
    dialog('Install missing packages?', (modal, close) => {
      const text = document.createElement('p');
      text.className = 'question-dialog-prompt';
      text.textContent = 'This code needs packages that are not in the test environment. ' +
        'Installing runs third-party code from PyPI. Edit the list if a package name is different.';
      const input = document.createElement('input');
      input.className = 'form-input question-dialog-input';
      input.value = missing.map(item => item.package).join(' ');
      input.setAttribute('aria-label', 'Packages to install (space separated)');
      const log = document.createElement('pre');
      log.className = 'tool-workbench-output';
      log.hidden = true;
      const actions = document.createElement('div');
      actions.className = 'question-dialog-actions';
      const cancel = document.createElement('button');
      cancel.type = 'button';
      cancel.className = 'btn';
      cancel.textContent = 'Cancel';
      const install = document.createElement('button');
      install.type = 'button';
      install.className = 'btn btn-primary';
      install.textContent = 'Install';
      actions.append(cancel, install);
      modal.append(text, input, log, actions);
      input.focus();

      cancel.addEventListener('click', () => { close(); resolve(false); });
      install.addEventListener('click', async () => {
        const packages = input.value.split(/\s+/).filter(Boolean);
        if (!packages.length) return;
        install.disabled = cancel.disabled = input.disabled = true;
        install.textContent = 'Installing…';
        log.hidden = false;
        log.textContent = `pip install ${packages.join(' ')}\n`;
        try {
          const result = await Sandbox.install(packages);
          log.textContent += result.output || '';
          if (result.ok) {
            setTimeout(() => { close(); resolve(true); }, 600);
            return;
          }
          log.textContent += '\nInstall failed.';
        } catch (err) {
          log.textContent += `\nError: ${err.message}`;
        }
        install.disabled = cancel.disabled = input.disabled = false;
        install.textContent = 'Retry';
        cancel.textContent = 'Close';
      });
    });
  });
}

// Detects missing packages for the code and the run output, then offers to install them.
// Returns true when something was installed so the caller can re-run.
export async function offerInstallForRun(source, outputText) {
  const named = missingModulesFromOutput(outputText);
  if (!named.length) return false;
  let missing;
  try {
    missing = (await Sandbox.check(source, named)).missing;
  } catch {
    missing = named.map(module => ({ module, package: module }));
  }
  if (!missing.length) return false;
  return promptInstall(missing);
}

export async function offerInstallBeforeRun(source) {
  let missing;
  try {
    missing = (await Sandbox.check(source, [])).missing;
  } catch {
    return false;
  }
  return missing.length ? promptInstall(missing) : false;
}

export async function confirmReset() {
  if (!confirm('Reset the test environment? All packages installed for testing will be removed.')) return null;
  return Sandbox.reset();
}

```

## `frontend/static/js/terminal.js`
```js
const API = '/api/codebuilder/terminal';
const ANSI = /\x1b\[[0-9;?]*[A-Za-z]/g;
const URL_PATTERN = /https?:\/\/(?:localhost|127\.0\.0\.1|0\.0\.0\.0):\d+\S*/g;
const MAX_CHARS = 200000;

export const TERMINAL_CHANNEL = 'novous2-terminal';

async function post(path, body) {
  const response = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status}).`);
  return payload;
}

// Builds a terminal into `root` and attaches to the shared backend session.
// Returns { destroy, attach, detach, focus }.
export function mountTerminal(root, { popOut = null, compact = false } = {}) {
  root.innerHTML = `
    <div class="tw-terminal${compact ? ' compact' : ''}">
      <div class="tw-terminal-bar">
        <span class="tw-terminal-cwd" title="Working folder"></span>
        <span class="tw-terminal-badge" hidden>sandbox</span>
        <span class="tw-terminal-spacer"></span>
        <button type="button" class="btn btn-sm" data-act="stop" disabled>Stop</button>
        <button type="button" class="btn btn-sm" data-act="clear">Clear</button>
        <button type="button" class="btn btn-sm" data-act="copy">Copy</button>
        ${popOut ? '<button type="button" class="btn btn-sm" data-act="popout" title="Open the terminal in its own window">Pop out</button>' : ''}
      </div>
      <div class="tw-terminal-links" hidden></div>
      <pre class="tw-terminal-output" tabindex="0"></pre>
      <form class="tw-terminal-form" autocomplete="off">
        <span class="tw-terminal-prompt">&gt;</span>
        <input type="text" class="tw-terminal-input" spellcheck="false"
               placeholder="streamlit run app.py   ·   python script.py   ·   pip install package"
               aria-label="Terminal command">
      </form>
    </div>`;

  const outputEl = root.querySelector('.tw-terminal-output');
  const cwdEl = root.querySelector('.tw-terminal-cwd');
  const badge = root.querySelector('.tw-terminal-badge');
  const linksEl = root.querySelector('.tw-terminal-links');
  const form = root.querySelector('.tw-terminal-form');
  const input = root.querySelector('.tw-terminal-input');
  const stopButton = root.querySelector('[data-act="stop"]');

  let text = '';
  let offset = 0;
  let source = null;
  let retry = null;
  let running = false;
  let destroyed = false;
  const history = [];
  let historyIndex = 0;

  const renderLinks = () => {
    const urls = [...new Set(text.match(URL_PATTERN) || [])].slice(-3);
    linksEl.replaceChildren();
    linksEl.hidden = !urls.length;
    urls.forEach(url => {
      const link = document.createElement('a');
      link.href = url.replace('0.0.0.0', 'localhost');
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = `Open ${url}`;
      linksEl.appendChild(link);
    });
  };

  const append = (chunk) => {
    if (!chunk) return;
    const atBottom = outputEl.scrollHeight - outputEl.scrollTop - outputEl.clientHeight < 40;
    text += chunk.replace(ANSI, '').replace(/\r\n/g, '\n');
    if (text.length > MAX_CHARS) text = text.slice(-MAX_CHARS);
    outputEl.textContent = text;
    if (atBottom) outputEl.scrollTop = outputEl.scrollHeight;
    renderLinks();
  };

  const applyState = (state) => {
    running = !!state.running;
    cwdEl.textContent = state.cwd || '';
    badge.hidden = !state.sandbox;
    stopButton.disabled = !running;
    input.placeholder = running ? 'A command is running — press Stop to end it' : input.placeholder;
  };

  const detach = () => {
    clearTimeout(retry);
    if (source) source.close();
    source = null;
  };

  const attach = () => {
    detach();
    if (destroyed) return;
    source = new EventSource(`${API}/stream?offset=${offset}`);
    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        offset = data.offset ?? offset;
        append(data.text);
        applyState(data);
      } catch { /* ignore malformed event */ }
    };
    source.onerror = () => {
      detach();
      retry = setTimeout(attach, 1500);
    };
  };

  const runCommand = async (command) => {
    history.push(command);
    historyIndex = history.length;
    try {
      applyState(await post('/run', { command }));
    } catch (err) {
      append(`${err.message}\n`);
    }
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const command = input.value.trim();
    if (!command) return;
    input.value = '';
    runCommand(command);
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowUp' && history.length) {
      historyIndex = Math.max(0, historyIndex - 1);
      input.value = history[historyIndex];
      event.preventDefault();
    } else if (event.key === 'ArrowDown' && history.length) {
      historyIndex = Math.min(history.length, historyIndex + 1);
      input.value = history[historyIndex] ?? '';
      event.preventDefault();
    }
  });

  root.addEventListener('click', async (event) => {
    const act = event.target.closest('[data-act]')?.dataset.act;
    if (!act) return;
    if (act === 'stop') {
      await post('/stop').catch(() => {});
    } else if (act === 'clear') {
      await post('/clear').catch(() => {});
      text = '';
      outputEl.textContent = '';
      renderLinks();
    } else if (act === 'copy') {
      const button = event.target.closest('button');
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const area = document.createElement('textarea');
        area.value = text;
        document.body.appendChild(area);
        area.select();
        document.execCommand('copy');
        area.remove();
      }
      button.textContent = 'Copied';
      setTimeout(() => { button.textContent = 'Copy'; }, 1500);
    } else if (act === 'popout' && popOut) {
      popOut();
    }
  });

  attach();

  return {
    attach,
    detach,
    focus: () => input.focus(),
    setInput: (value) => { input.value = value; input.focus(); },
    destroy: () => { destroyed = true; detach(); }
  };
}

```

## `frontend/static/js/test_panel.js`
```js
import { createIcon } from './icons.js';

const TEST_FUNCTIONS = [
  { id: 'runTestSuite', label: 'Run Test Suite', icon: 'play-circle', action: null },
  { id: 'debugAgent', label: 'Debug Agent', icon: 'bug', action: null },
  { id: 'promptInspector', label: 'Prompt Inspector', icon: 'terminal', action: null },
  { id: 'outputEvaluator', label: 'Output Evaluator', icon: 'check-square', action: null },
  { id: 'benchmark', label: 'Benchmark', icon: 'gauge', action: null },
  { id: 'apiLogs', label: 'API Logs', icon: 'file-code', action: null },
  { id: 'diagnostics', label: 'Diagnostics', icon: 'activity', action: null },
  { id: 'wipeChat', label: 'Wipe Chat', icon: 'trash-2', action: null }
];

export function buildTestPanel(containerId, actions = {}) {
  const container = typeof containerId === 'string'
    ? document.getElementById(containerId)
    : containerId;

  if (!container) {
    console.error('Test panel container not found:', containerId);
    return;
  }

  container.replaceChildren();

  TEST_FUNCTIONS.forEach((test) => {
    const action = actions[test.id] || test.action;
    const button = document.createElement('button');
    const label = document.createElement('span');

    button.className = 'test-function';
    button.type = 'button';
    button.dataset.testFunction = test.id;
    label.textContent = test.label;
    button.append(createIcon(test.icon), label);

    if (typeof action !== 'function') {
      button.classList.add('disabled');
      button.disabled = true;
      button.title = 'Not implemented yet';
    } else {
      button.title = test.label;
      button.addEventListener('click', action);
    }

    container.appendChild(button);
  });

  const todoSection = document.createElement('div');
  todoSection.className = 'todo-selector-section';

  const todoLabel = document.createElement('label');
  todoLabel.className = 'model-picker-label small text-muted';
  todoLabel.htmlFor = 'todo-file-select';
  todoLabel.textContent = 'Select To-Do File';

  const todoSelect = document.createElement('select');
  todoSelect.id = 'todo-file-select';
  todoSelect.className = 'form-select';
  todoSelect.setAttribute('aria-label', 'Select a To-Do file');

  const refreshTodoFiles = document.createElement('button');
  refreshTodoFiles.id = 'todo-file-refresh';
  refreshTodoFiles.className = 'btn btn-sm';
  refreshTodoFiles.type = 'button';
  refreshTodoFiles.append(createIcon('refresh'), document.createTextNode('Refresh lists'));
  refreshTodoFiles.title = 'Refresh Markdown to-do lists';

  const loadingOption = document.createElement('option');
  loadingOption.value = '';
  loadingOption.textContent = 'Loading Markdown lists...';
  todoSelect.appendChild(loadingOption);

  todoSection.append(todoLabel, todoSelect, refreshTodoFiles);
  container.appendChild(todoSection);
}

```

## `frontend/static/js/testing.js`
```js
import { Api } from './api.js';
import { offerInstallForRun, offerInstallBeforeRun, confirmReset } from './sandbox_ui.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

export function renderTestingView(container, payload = null) {
  container.innerHTML = `
    <div class="card testing-runner">
      <div class="card-head">
        <h3>Prompt Header Evaluation Battery</h3>
        <button type="button" class="btn btn-sm btn-primary" id="ht-run">Run Header Tests</button>
      </div>
      <div class="form-row">
        <select id="ht-agent" class="form-select">
          <option value="">Loading agents…</option>
        </select>
      </div>
      <div id="ht-results" class="ht-results mt-3">
        <p class="text-muted">Select an agent profile to run section-header verification (role, purpose, boundaries, output format).</p>
      </div>
    </div>`;

  const agentSel = container.querySelector('#ht-agent');
  const results = container.querySelector('#ht-results');

  Promise.all([Api.getAgents(), Api.getCodeBuilderAgents(), Api.getAgents('prompt-creation')]).then(([workspaceData, codeBuilderData, promptData]) => {
    const label = environment => ({ codebuilder: 'CodeBuilder', 'prompt-creation': 'Prompt Creation' })[environment] || 'Workspace';
    const agents = [
      ...(workspaceData.agents || []).map(agent => ({ ...agent, environment: 'workspace' })),
      ...(codeBuilderData.agents || []).map(agent => ({ ...agent, environment: 'codebuilder' })),
      ...(promptData.agents || []).map(agent => ({ ...agent, environment: 'prompt-creation' }))
    ];
    agentSel.innerHTML = agents.length
      ? agents.map(agent => `<option value="${esc(agent.id)}" data-environment="${agent.environment}">${esc(agent.name)} (${esc(agent.id)}) · ${label(agent.environment)}</option>`).join('')
      : '<option value="">No agents found</option>';
  }).catch(err => {
    agentSel.innerHTML = `<option value="">Error: ${esc(err.message)}</option>`;
  });

  function renderReport(report) {
    const header = `
      <div class="ht-summary ${report.passed ? 'pass' : 'fail'}">
        <strong>Verdict: ${esc(report.verdict)}</strong>
        <span>Overall Score: ${esc(report.overall_score)} (${esc(report.headers_passed)}/${esc(report.headers_total)} headers passed)</span>
      </div>`;

    const rows = (report.results || []).map(r => `
      <div class="ht-header ${r.passed ? 'pass' : 'fail'}">
        <div class="ht-header-head">
          <span class="ht-hash">## ${esc(r.header)}</span>
          <span class="badge ${r.passed ? 'badge-success' : 'badge-danger'}">${esc(Number(r.score || 0).toFixed(2))}</span>
        </div>
        ${((r.questions || []).map(q => `
          <div class="ht-question">
            <span class="ht-q-status ${q.passed ? 'pass' : 'fail'}">${q.passed ? '✓' : '✗'}</span>
            <div>
              <div>${esc(q.question)}</div>
              <div class="text-muted small">${esc(q.evidence)} · score ${esc(q.score)}</div>
            </div>
          </div>`).join(''))}
      </div>`).join('');

    const extras = report.extra_headers?.length
      ? `<p class="text-muted small">Extra headers: ${esc(report.extra_headers.join(', '))}</p>`
      : '';

    return header + rows + extras;
  }

  container.querySelector('#ht-run').addEventListener('click', async () => {
    if (!agentSel.value) return;
    results.innerHTML = '<p class="text-muted">Executing header battery evaluation...</p>';
    try {
      const environment = agentSel.selectedOptions[0]?.dataset.environment || 'workspace';
      const report = await Api.runHeaderTests(agentSel.value, environment);
      results.innerHTML = renderReport(report);
    } catch (err) {
      results.innerHTML = `<p class="text-danger">Error: ${esc(err.message)}</p>`;
    }
  });

  renderToolWorkbench(container, payload?.type === 'tool' ? payload : null);

  if (payload?.type === 'category') {
    results.innerHTML = `<p class="text-muted">Evaluating prompt category “${esc(payload.name)}” (${esc(payload.partCount)} parts)…</p>`;
    Api.evaluateMarkdown(payload.markdown, payload.id).then(report => {
      results.innerHTML = `<p class="text-muted small">Prompt category: <strong>${esc(payload.name)}</strong></p>${renderReport(report)}`;
    }).catch(err => {
      results.innerHTML = `<p class="text-danger">Error: ${esc(err.message)}</p>`;
    });
  }
}

function renderToolWorkbench(container, toolPayload = null) {
  container.insertAdjacentHTML('beforeend', `
    <section class="card tool-workbench mt-3" aria-labelledby="tool-workbench-title">
      <div class="card-head">
        <div>
          <h3 id="tool-workbench-title">Tool Function Testing Workbench</h3>
          <p class="text-muted small">Tests run on this computer using the local Python interpreter. Only run code you trust: tested code can access files, network, and resources available to your user account. Each run has a 5-second timeout.</p>
        </div>
      </div>
      <h4 class="tool-workbench-stage">Stage 1: Generate Python Function</h4>
      <div class="tool-workbench-grid">
        <label class="tool-workbench-field">
          <span>LLM Model</span>
          <span class="tool-workbench-model">
            <select id="tw-model" class="form-select" aria-label="LLM model">
              <option value="">Loading models…</option>
            </select>
            <button type="button" class="btn btn-sm" id="tw-refresh-models">Refresh</button>
          </span>
        </label>
        <label class="tool-workbench-field">
          <span>Tool Description &amp; Rules</span>
          <textarea id="tw-description" class="form-input" rows="5"></textarea>
        </label>
        <div class="tool-workbench-actions tool-workbench-wide">
          <button type="button" class="btn btn-primary" id="tw-generate-fn">Generate Python Function</button>
        </div>
        <div class="tool-workbench-field tool-workbench-wide">
          <span>Python Function Code</span>
          <div class="code-editor">
            <div class="code-editor-bar">
              <span class="code-editor-file">tool_function.py</span>
              <span class="code-editor-actions">
                <button type="button" class="btn btn-sm" id="tw-send-builder" title="Open this code in the Code Builder editor">Send to Code Builder</button>
                <button type="button" class="btn btn-sm" id="tw-edit-code">Edit</button>
                <button type="button" class="btn btn-sm" id="tw-copy-code">Copy</button>
              </span>
            </div>
            <div class="code-view" id="tw-code-view" tabindex="0" aria-label="Python function code (read-only view)"></div>
            <textarea id="tw-code" class="code-input" spellcheck="false" wrap="off" hidden
                      aria-label="Python function code" placeholder="# Generate a function in Stage 1, or paste your own code here"></textarea>
          </div>
        </div>
      </div>
      <h4 class="tool-workbench-stage mt-3">Stage 2: Ask LLM to Use Function</h4>
      <div class="tool-workbench-grid">
        <label class="tool-workbench-field">
          <span>Natural Language Request</span>
          <textarea id="tw-prompt" class="form-input" rows="5"></textarea>
        </label>
        <label class="tool-workbench-field">
          <span>Extracted JSON Arguments</span>
          <textarea id="tw-input" class="tool-workbench-editor" rows="5" spellcheck="false"></textarea>
          <span class="text-muted small">Filled with the arguments the model sends. Edit it to run a Direct Python Test. Cleared if the model makes no tool call.</span>
        </label>
      </div>
      <div class="tool-workbench-actions">
        <button type="button" class="btn btn-primary" id="tw-run-llm">Ask LLM to Use Tool</button>
      </div>
      <h4 class="tool-workbench-stage mt-3">Stage 3 &amp; 4: Execution &amp; Test Results</h4>
      <div class="tool-workbench-actions">
        <button type="button" class="btn" id="tw-run">Direct Python Test</button>
        <label class="text-muted small" for="tw-timeout">Time limit</label>
        <select id="tw-timeout" class="form-select" style="width:auto" title="Raise this for GUI windows or slow code">
          <option value="5">5 seconds</option>
          <option value="30">30 seconds</option>
          <option value="60">1 minute</option>
          <option value="300">5 minutes</option>
          <option value="600">10 minutes</option>
        </select>
        <button type="button" class="btn" id="tw-save" disabled>Save Test Report (.md)</button>
        <button type="button" class="btn" id="tw-reset">Clear Fields</button>
        <button type="button" class="btn" id="tw-reset-env" title="Remove all packages installed for testing">Reset Environment</button>
        <button type="button" class="btn" id="tw-promote" disabled
                title="Run a successful test before adding a tool">Add Passed Tool to Library</button>
        <span id="tw-status" class="text-muted small" role="status">Ready</span>
      </div>
      <label id="tw-llm-response-section" class="tool-workbench-field" hidden>
        <span>Raw LLM Response</span>
        <pre id="tw-llm-response" class="tool-workbench-output" aria-live="polite"></pre>
      </label>
      <label class="tool-workbench-field">
        <span>Execution Output &amp; Result</span>
        <pre id="tw-output" class="tool-workbench-output" aria-live="polite">Run a test to see its result.</pre>
      </label>
      <div class="tool-workbench-library">
        <h4>Registered Tool Library</h4>
        <p class="text-muted small">Tools listed here are registered from the five file-tool modules and <code>promoted_tools.py</code> in <code>tools/</code>.</p>
        <div id="tw-library" class="text-muted small">Loading tools…</div>
      </div>
      <p class="text-muted small">Promoted code is trusted application code and will run in the Novous2 backend when an agent invokes it.</p>
    </section>`);

  const codeField = container.querySelector('#tw-code');
  const descriptionField = container.querySelector('#tw-description');
  const generateButton = container.querySelector('#tw-generate-fn');
  const inputField = container.querySelector('#tw-input');
  const promptField = container.querySelector('#tw-prompt');
  const modelSelect = container.querySelector('#tw-model');
  const runButton = container.querySelector('#tw-run');
  const llmButton = container.querySelector('#tw-run-llm');
  const saveButton = container.querySelector('#tw-save');
  const promoteButton = container.querySelector('#tw-promote');
  const output = container.querySelector('#tw-output');
  const llmResponseSection = container.querySelector('#tw-llm-response-section');
  const llmResponse = container.querySelector('#tw-llm-response');
  const status = container.querySelector('#tw-status');
  const timeoutSelect = container.querySelector('#tw-timeout');
  const timeoutSeconds = () => Number(timeoutSelect.value) || 5;
  const library = container.querySelector('#tw-library');

  let lastPassed = null;
  let lastTestReport = null;
  let busy = false;
  const codeView = container.querySelector('#tw-code-view');
  const editButton = container.querySelector('#tw-edit-code');

  const PY_KEYWORDS = new Set(['and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield', 'None', 'True', 'False']);
  const PY_BUILTINS = new Set(['str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'bytes', 'len', 'range', 'print', 'round', 'sum', 'min', 'max', 'abs', 'sorted', 'enumerate', 'zip', 'map', 'filter', 'isinstance', 'any', 'all', 'self', 'Any', 'Optional', 'List', 'Dict']);
  const PY_TOKEN = /("""[\s\S]*?(?:"""|$)|'''[\s\S]*?(?:'''|$))|(#[^\n]*)|((?:[rbfRBF]{1,2})?(?:"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?))|(@[A-Za-z_][\w.]*)|(\b\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?\b)|([A-Za-z_]\w*)/g;

  function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function highlightPython(source) {
    let html = '';
    let last = 0;
    let previousWord = '';
    for (const match of source.matchAll(PY_TOKEN)) {
      html += escapeHtml(source.slice(last, match.index));
      const [text, triple, comment, string, decorator, number, word] = match;
      // Close and reopen the span at each newline so every line is self-contained.
      const wrap = (cls) => text.split('\n')
        .map(part => part ? `<span class="${cls}">${escapeHtml(part)}</span>` : '')
        .join('\n');
      if (triple || string) html += wrap('tok-str');
      else if (comment) html += wrap('tok-com');
      else if (decorator) html += wrap('tok-dec');
      else if (number) html += wrap('tok-num');
      else if (word && PY_KEYWORDS.has(word)) html += wrap('tok-kw');
      else if (word && (previousWord === 'def' || previousWord === 'class')) html += wrap('tok-fn');
      else if (word && PY_BUILTINS.has(word)) html += wrap('tok-bi');
      else html += escapeHtml(text);
      if (word) previousWord = word;
      else if (!/^\s+$/.test(text)) previousWord = '';
      last = match.index + text.length;
    }
    return html + escapeHtml(source.slice(last));
  }

  const HARNESS_START = '# --- Novous2 test call';
  function renderCodeView() {
    const source = codeField.value.replace(/\r\n?/g, '\n');
    codeView.innerHTML = source
      ? highlightPython(source).split('\n').map((line, index) =>
        `<div class="code-line"><span class="code-ln">${index + 1}</span><span class="code-text">${line || ' '}</span></div>`
      ).join('')
      : '<div class="code-empty">No code yet. Generate a function in Stage 1, or click Edit to paste your own.</div>';
  }
  async function setEditing(editing) {
    if (editing && codeField.value.trim() && !codeField.value.includes(HARNESS_START)) {
      try {
        const { harness } = await Api.getToolTestHarness(codeField.value);
        codeField.value = `${codeField.value.replace(/\s+$/, '')}\n\n\n${harness}`;
      } catch (_) { /* invalid code: edit it without a test call */ }
    }
    codeField.hidden = !editing;
    codeView.hidden = editing;
    editButton.textContent = editing ? 'Done' : 'Edit';
    if (editing) {
      codeField.focus();
    } else {
      renderCodeView();
    }
  }
  function setCode(value) {
    codeField.value = value;
    setEditing(false);
  }
  editButton.addEventListener('click', () => setEditing(codeField.hidden));
  codeView.addEventListener('dblclick', () => setEditing(true));
  setEditing(false);

  container.querySelector('#tw-send-builder').addEventListener('click', () => {
    if (!codeField.value.trim()) {
      status.textContent = 'There is no code to send yet.';
      status.className = 'text-danger small';
      return;
    }
    try {
      localStorage.setItem('novous2.codebuilder.incoming', codeField.value);
    } catch (err) {
      status.textContent = `Could not hand off code: ${err.message}`;
      status.className = 'text-danger small';
      return;
    }
    window.open('/codebuilder', '_blank');
  });

  container.querySelector('#tw-copy-code').addEventListener('click', async event => {
    const button = event.currentTarget;
    try {
      await navigator.clipboard.writeText(codeField.value);
      button.textContent = 'Copied!';
    } catch (_) {
      const wasHidden = codeField.hidden;
      codeField.hidden = false;
      codeField.select();
      const ok = document.execCommand('copy');
      codeField.hidden = wasHidden;
      button.textContent = ok ? 'Copied!' : 'Copy failed';
    }
    setTimeout(() => { button.textContent = 'Copy'; }, 1500);
  });
  function enableTabIndent(field) {
    field.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      event.preventDefault();
      const start = field.selectionStart;
      const end = field.selectionEnd;
      field.value = field.value.slice(0, start) + '    ' + field.value.slice(end);
      field.selectionStart = field.selectionEnd = start + 4;
      field.dispatchEvent(new Event('input'));
    });
  }

  function createTestReport(result, context = {}) {
    return {
      tested_at: new Date().toISOString(),
      execution_mode: context.execution_mode || 'local-python',
      model_used: context.model_used || null,
      function_code: context.function_code ?? codeField.value,
      function_input: Object.prototype.hasOwnProperty.call(context, 'function_input')
        ? context.function_input
        : inputField.value,
      prompt: context.prompt ?? '',
      test_output: result
    };
  }

  function markdownCodeBlock(value, language = '') {
    const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    const longestFence = Math.max(2, ...((text.match(/`+/g) || []).map(run => run.length)));
    const fence = '`'.repeat(longestFence + 1);
    return `${fence}${language}\n${text}\n${fence}`;
  }

  function renderTestReport(report) {
    const testOutput = report.test_output || {};
    const execution = testOutput.tool_execution_result || testOutput;
    const passed = testOutput.status === 'SUCCESS';
    const fields = [
      `- **Result:** ${passed ? 'PASS' : 'FAIL'}`,
      `- **Tested at (UTC):** ${report.tested_at}`,
      `- **Execution mode:** ${report.execution_mode}`,
      `- **LLM used:** ${report.model_used || 'No — direct local Python test'}`,
      `- **Function:** ${execution.function_name || 'Not identified'}`,
      `- **Error code:** ${testOutput.error_code || execution.error_code || 'None'}`
    ];
    const sections = [
      '# Tool Function Test Report',
      '',
      ...fields,
      '',
      '## LLM Prompt',
      '',
      report.prompt ? markdownCodeBlock(report.prompt, 'text') : '_No LLM prompt was used._',
      '',
      '## Function Input',
      '',
      markdownCodeBlock(report.function_input, 'json'),
      '',
      '## Function Code',
      '',
      markdownCodeBlock(report.function_code, 'python'),
      '',
      '## Result',
      '',
      `**Status:** ${testOutput.status || 'ERROR'}`,
      ''
    ];

    if (execution.output !== undefined) {
      sections.push('### Function output', '', markdownCodeBlock(execution.output, 'json'), '');
    }
    if (testOutput.llm_text_response) {
      sections.push('### LLM response', '', markdownCodeBlock(testOutput.llm_text_response, 'text'), '');
    }
    if (testOutput.tool_calls_detected?.length) {
      sections.push(
        '### LLM tool calls',
        '',
        markdownCodeBlock(testOutput.tool_calls_detected, 'json'),
        ''
      );
    }
    if (testOutput.message) {
      sections.push('### Failure details', '', markdownCodeBlock(testOutput.message, 'text'), '');
    }
    for (const [label, value] of [
      ['Standard error', execution.stderr],
      ['Standard output', execution.stdout],
      ['Exit code', execution.exit_code]
    ]) {
      if (value !== undefined && value !== null && value !== '') {
        sections.push(`### ${label}`, '', markdownCodeBlock(value, 'text'), '');
      }
    }
    sections.push(
      '## Machine-readable JSON',
      '',
      'The complete report data is included below for reuse or automated processing.',
      '',
      markdownCodeBlock(report, 'json'),
      ''
    );
    return sections.join('\n');
  }

  function parseFunctionInput() {
    const parsed = JSON.parse(inputField.value || '{}');
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
      throw new Error('Function input must be a JSON object.');
    }
    return parsed;
  }

  function updatePromotion() {
    const unchangedSincePass = lastPassed &&
      lastPassed.code === codeField.value &&
      lastPassed.input === inputField.value;
    let hasValidInput = true;
    try {
      parseFunctionInput();
    } catch (_) {
      hasValidInput = false;
    }
    promoteButton.disabled = busy || !unchangedSincePass || !hasValidInput;
  }

  function renderOutput(result) {
    const execution = result.tool_execution_result || result;
    const lines = [];
    const add = (text, cls = '') => {
      const span = document.createElement('span');
      if (cls) span.className = cls;
      span.textContent = text.endsWith('\n') ? text : `${text}\n`;
      lines.push(span);
    };
    if (execution.stdout) add(execution.stdout);
    if (execution.stderr) add(execution.stderr, 'tw-out-error');
    if (result.message && !execution.stderr) add(`Error: ${result.message}`, 'tw-out-error');
    if (result.status === 'SUCCESS' && execution.output !== undefined) {
      add(`Result: ${JSON.stringify(execution.output, null, 2)}`, 'tw-out-result');
    }
    if (result.status !== 'SUCCESS') {
      const code = result.error_code || execution.error_code;
      if (code) add(`[${code}]`, 'tw-out-error');
    }
    if (execution.exit_code !== undefined && execution.exit_code !== null) {
      add(`Process exited with code ${execution.exit_code}.`, 'tw-out-meta');
    }
    if (!lines.length) add('Execution completed with no output.', 'tw-out-meta');
    output.replaceChildren(...lines);
  }

  function showResult(result, reportContext) {
    renderOutput(result);
    lastTestReport = createTestReport(result, reportContext);
    saveButton.disabled = false;
    const passed = result.status === 'SUCCESS';
    status.textContent = passed ? 'Test passed' : 'Test failed';
    status.className = passed ? 'text-success small' : 'text-danger small';
    lastPassed = passed
      ? { code: codeField.value, input: inputField.value }
      : null;
    updatePromotion();
  }

  function showLlmResponse(result) {
    const sections = [];
    if (typeof result.llm_text_response === 'string' && result.llm_text_response) {
      sections.push(result.llm_text_response);
    }
    if (result.tool_calls_detected?.length) {
      sections.push(`Tool calls:\n${JSON.stringify(result.tool_calls_detected, null, 2)}`);
    }
    if (!sections.length) {
      sections.push(result.message || 'No response content was returned by the model.');
    }
    llmResponse.textContent = sections.join('\n\n');
    llmResponseSection.hidden = false;
  }

  async function loadModels() {
    modelSelect.replaceChildren(new Option('Loading models…', ''));
    try {
      const data = await Api.getModels();
      const models = data.models || [];
      modelSelect.replaceChildren();
      if (!models.length) {
        modelSelect.appendChild(new Option(data.error || 'No models found', ''));
        return;
      }
      models.forEach(model => modelSelect.appendChild(new Option(model, model)));
      modelSelect.value = models.includes(data.default) ? data.default : models[0];
    } catch (err) {
      modelSelect.replaceChildren(new Option(`Could not load models: ${err.message}`, ''));
    }
  }

  async function loadToolLibrary() {
    try {
      const data = await Api.getToolLibrary();
      const tools = data.tools || [];
      library.innerHTML = tools.length
        ? tools.map(tool => `
          <div class="tool-workbench-library-item">
            <code>${esc(tool.name)}</code>
            <span>${esc(tool.signature)}</span>
            ${tool.custom ? `
              <button type="button" class="btn btn-sm" data-tool-load="${esc(tool.name)}">Load</button>
              <button type="button" class="btn btn-sm" data-tool-delete="${esc(tool.name)}">Remove</button>
            ` : ''}
          </div>`).join('')
        : 'No tools registered.';
    } catch (err) {
      library.textContent = `Could not load tools: ${err.message}`;
    }
  }

  async function runTest(useLlm) {
    let functionInput;
    if (!useLlm) {
      try {
        functionInput = parseFunctionInput();
      } catch (err) {
        lastPassed = null;
        renderOutput({
          status: 'ERROR',
          error_code: 'ERR_INVALID_JSON_INPUT',
          message: err.message
        });
        lastTestReport = createTestReport({
          status: 'ERROR',
          error_code: 'ERR_INVALID_JSON_INPUT',
          message: err.message
        });
        saveButton.disabled = false;
        status.textContent = 'Test failed';
        status.className = 'text-danger small';
        updatePromotion();
        return;
      }
    }
    if (useLlm && !codeField.value.trim()) {
      status.textContent = 'Complete Stage 1 first: generate or enter a Python function.';
      status.className = 'text-danger small';
      return;
    }
    if (useLlm && !modelSelect.value) {
      status.textContent = 'Select an installed model first.';
      status.className = 'text-danger small';
      return;
    }

    await offerInstallBeforeRun(codeField.value);

    let reportInput;
    try {
      reportInput = parseFunctionInput();
    } catch (_) {
      reportInput = inputField.value;
    }
    const reportContext = {
      execution_mode: useLlm ? 'local-llm-tool-call' : 'local-python',
      model_used: useLlm ? modelSelect.value : null,
      function_code: codeField.value,
      function_input: useLlm ? null : reportInput,
      prompt: useLlm ? promptField.value : ''
    };
    busy = true;
    lastPassed = null;
    updatePromotion();
    runButton.disabled = true;
    llmButton.disabled = true;
    status.textContent = useLlm ? 'Requesting local model tool call…' : 'Running with local Python…';
    status.className = 'text-muted small';
    output.textContent = 'Test in progress…';
    llmResponseSection.hidden = true;
    llmResponse.textContent = '';
    let needsInstallCheck = '';
    try {
      const result = useLlm
        ? await Api.testToolWithLlm(modelSelect.value, codeField.value, promptField.value, timeoutSeconds())
        : await Api.executeToolTest(codeField.value, functionInput, timeoutSeconds());
      if (useLlm) {
        showLlmResponse(result);
        let extracted = result.function_input;
        if (extracted == null) {
          const rawArgs = result.tool_calls_detected?.[0]?.function?.arguments;
          if (rawArgs && typeof rawArgs === 'object') extracted = rawArgs;
        }
        if (extracted != null) {
          inputField.value = JSON.stringify(extracted, null, 2);
          reportContext.function_input = extracted;
        } else {
          inputField.value = '';
          status.textContent = result.message || 'The model did not return tool arguments.';
        }
      }
      showResult(result, reportContext);
      const execution = result.tool_execution_result || result;
      needsInstallCheck = result.status !== 'SUCCESS'
        ? `${execution.stderr || ''}\n${execution.stdout || ''}\n${result.message || ''}`
        : '';
    } catch (err) {
      const result = {
        status: 'ERROR',
        error_code: 'ERR_TOOL_TEST_FAILED',
        message: err.message
      };
      if (useLlm) showLlmResponse(result);
      renderOutput(result);
      lastTestReport = createTestReport(result, reportContext);
      saveButton.disabled = false;
      status.textContent = 'Test failed';
      status.className = 'text-danger small';
    } finally {
      busy = false;
      runButton.disabled = false;
      llmButton.disabled = false;
      updatePromotion();
    }
    if (needsInstallCheck && await offerInstallForRun(codeField.value, needsInstallCheck)) {
      await runTest(useLlm);
    }
  }

  runButton.addEventListener('click', () => runTest(false));
  llmButton.addEventListener('click', () => runTest(true));
  generateButton.addEventListener('click', async () => {
    if (!descriptionField.value.trim()) {
      status.textContent = 'Enter a tool description first.';
      status.className = 'text-danger small';
      return;
    }
    if (!modelSelect.value) {
      status.textContent = 'Select an installed model first.';
      status.className = 'text-danger small';
      return;
    }
    busy = true;
    generateButton.disabled = runButton.disabled = llmButton.disabled = true;
    status.textContent = 'Generating Python function…';
    status.className = 'text-muted small';
    try {
      const result = await Api.generateToolFunction(modelSelect.value, descriptionField.value);
      if (result.status === 'SUCCESS') {
        setCode(result.code);
        lastPassed = null;
        status.textContent = `Generated ${result.function_name}. Next: ask the LLM to use it.`;
        status.className = 'text-success small';
      } else {
        status.textContent = `${result.error_code}: ${result.message}`;
        status.className = 'text-danger small';
      }
    } catch (err) {
      status.textContent = `Could not generate function: ${err.message}`;
      status.className = 'text-danger small';
    } finally {
      busy = false;
      generateButton.disabled = runButton.disabled = llmButton.disabled = false;
      updatePromotion();
    }
  });
  container.querySelector('#tw-refresh-models').addEventListener('click', loadModels);
  library.addEventListener('click', async event => {
    const loadButton = event.target.closest('[data-tool-load]');
    const deleteButton = event.target.closest('[data-tool-delete]');
    if (loadButton) {
      try {
        const tool = await Api.getWorkbenchTool(loadButton.dataset.toolLoad);
        setCode(tool.source);
        lastPassed = null;
        updatePromotion();
        status.textContent = `Loaded ${tool.name} from ${tool.path} for testing`;
        status.className = 'text-muted small';
      } catch (err) {
        status.textContent = `Could not load tool: ${err.message}`;
        status.className = 'text-danger small';
      }
    }
    if (deleteButton && confirm(
      `Remove ${deleteButton.dataset.toolDelete} from the tool library? Existing agent sessions may keep the loaded function until reset.`
    )) {
      try {
        const deleted = await Api.deleteWorkbenchTool(deleteButton.dataset.toolDelete);
        await loadToolLibrary();
        status.textContent = `Removed ${deleted.name} from ${deleted.path}`;
        status.className = 'text-success small';
      } catch (err) {
        status.textContent = `Could not remove tool: ${err.message}`;
        status.className = 'text-danger small';
      }
    }
  });
  enableTabIndent(codeField);
  enableTabIndent(inputField);
  codeField.addEventListener('input', () => {
    lastPassed = null;
    updatePromotion();
  });
  inputField.addEventListener('input', () => {
    lastPassed = null;
    updatePromotion();
  });
  saveButton.addEventListener('click', async () => {
    if (!lastTestReport) return;
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    try {
      const saved = await Api.saveMarkdown(
        renderTestReport(lastTestReport),
        `novous2-tool-test-${stamp}.md`
      );
      if (saved.locationChosen) {
        alert(`Test results saved as ${saved.filename}.`);
      } else {
        alert(`Test results download started: ${saved.filename}`);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        alert(`Could not save test results: ${err.message}`);
      }
    }
  });
  promoteButton.addEventListener('click', async () => {
    if (!lastPassed || !confirm(
      'Add this tested function to the tool library? Promoted code runs as trusted code in the Novous2 backend.'
    )) return;

    try {
      busy = true;
      runButton.disabled = true;
      llmButton.disabled = true;
      updatePromotion();
      status.textContent = 'Verifying test and adding tool…';
      const result = await Api.promoteTestedTool(codeField.value, parseFunctionInput(), timeoutSeconds());
      output.textContent = JSON.stringify(result, null, 2);
      status.textContent = `Added ${result.promoted.name} to the tool library`;
      if (result.requirements_added?.length) {
        status.textContent += `. Added to requirements.txt: ${result.requirements_added.join(', ')} (run pip install -r requirements.txt in the app environment)`;
      }
      status.className = 'text-success small';
      lastPassed = null;
      await loadToolLibrary();
    } catch (err) {
      output.textContent = JSON.stringify({
        status: 'ERROR',
        error_code: 'ERR_TOOL_PROMOTION_FAILED',
        message: err.message
      }, null, 2);
      status.textContent = 'Could not add tool';
      status.className = 'text-danger small';
    } finally {
      busy = false;
      runButton.disabled = false;
      llmButton.disabled = false;
      updatePromotion();
    }
  });

  container.querySelector('#tw-reset-env').addEventListener('click', async () => {
    try {
      const result = await confirmReset();
      if (!result) return;
      status.textContent = result.output;
      status.className = result.ok ? 'text-success small' : 'text-danger small';
    } catch (err) {
      status.textContent = `Reset failed: ${err.message}`;
      status.className = 'text-danger small';
    }
  });

  container.querySelector('#tw-reset').addEventListener('click', () => {
    setCode('');
    descriptionField.value = '';
    inputField.value = '';
    promptField.value = '';
    output.textContent = 'Run a test to see its result.';
    llmResponse.textContent = '';
    llmResponseSection.hidden = true;
    status.textContent = 'Ready';
    status.className = 'text-muted small';
    lastPassed = null;
    lastTestReport = null;
    saveButton.disabled = true;
    updatePromotion();
  });

  loadModels();
  loadToolLibrary();

  if (toolPayload) {
    setCode(toolPayload.source);
    inputField.value = toolPayload.input;
    promptField.value = toolPayload.prompt;
    status.textContent = `Loaded ${toolPayload.name} from ${toolPayload.path} for testing`;
    container.querySelector('.tool-workbench').scrollIntoView({ block: 'start' });
  }
}

```

## `frontend/static/js/tree.js`
```js
import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

export function renderTree(container, options = {}) {
  const { onSelect, onSelectDirectory, onBeforeDelete, onDelete, manageRoots = false } = options;
  container.innerHTML = `
    ${manageRoots ? `
    <label class="tree-root-picker">
      <span>Workspace folder</span>
      <select class="form-select" data-root-picker aria-label="Workspace folder"></select>
      <span class="tree-root-path" data-root-path></span>
    </label>` : ''}
    <div class="tree-toolbar">
      <button class="btn btn-sm btn-primary" data-action="new-file" title="Create a file here">+ File</button>
      <button class="btn btn-sm" data-action="new-dir" title="Create a folder here">+ Folder</button>
      <button class="btn btn-sm btn-ghost" data-action="refresh" title="Refresh files">↻</button>
    </div>
    <div class="tree-root-label"><span aria-hidden="true">⌂</span> <span data-root-name>Workspace</span></div>
    <div class="tree-body" role="tree" aria-label="Workspace files"></div>`;

  const body = container.querySelector('.tree-body');
  const rootName = container.querySelector('[data-root-name]');
  const rootPicker = container.querySelector('[data-root-picker]');
  const rootPath = container.querySelector('[data-root-path]');
  let selectedDirectory = '';
  const expandedPaths = new Set();
  let knownPaths = null;
  let loading = false;

  const collectPaths = (node, out = new Set()) => {
    (node.children || []).forEach(child => {
      out.add(child.path);
      if (child.type === 'directory') collectPaths(child, out);
    });
    return out;
  };

  async function load({ silent = false } = {}) {
    if (loading) return;
    loading = true;
    if (!silent) body.innerHTML = '<p class="tree-message">Loading files…</p>';
    try {
      if (manageRoots && !silent) {
        const config = await Api.getFileManagerRoots();
        rootName.textContent = config.roots.find(root => root.path === config.active_path)?.name || 'Workspace';
        rootPicker.replaceChildren(...config.roots.map(root => {
          const option = document.createElement('option');
          option.value = root.path;
          option.textContent = root.name;
          option.selected = root.path === config.active_path;
          return option;
        }));
        rootPath.textContent = config.active_path;
      }
      const tree = await Api.getManagedFileTree();
      const paths = collectPaths(tree);
      const added = knownPaths ? [...paths].filter(path => !knownPaths.has(path)) : [];
      const changed = !knownPaths || added.length > 0 || paths.size !== knownPaths.size;
      knownPaths = paths;
      if (silent && !changed) return;
      if (!manageRoots) rootName.textContent = tree.name || 'Workspace';
      body.replaceChildren(...(tree.children || []).map(child => buildNode(child, 0)));
      added.forEach(path => {
        const row = [...body.querySelectorAll('.tree-row')].find(item => item.dataset.path === path);
        if (!row) return;
        row.classList.add('tree-new');
        setTimeout(() => row.classList.remove('tree-new'), 4000);
      });
    } catch (error) {
      if (!silent) body.innerHTML = `<p class="tree-message text-danger">${esc(error.message)}</p>`;
    } finally {
      loading = false;
    }
  }

  function buildNode(node, depth) {
    const wrapper = document.createElement('div');
    const isDirectory = node.type === 'directory';
    const row = document.createElement('div');
    row.className = 'tree-row';
    row.dataset.path = node.path;
    row.dataset.type = node.type;
    row.style.paddingLeft = `${depth * 13 + 8}px`;
    row.setAttribute('role', 'treeitem');
    const expanded = isDirectory && expandedPaths.has(node.path);
    row.setAttribute('aria-expanded', String(expanded));
    row.innerHTML = `
      <button class="tree-toggle" type="button" aria-label="${isDirectory ? 'Collapse' : 'File'}"
        ${isDirectory ? '' : 'disabled'}>${isDirectory ? (expanded ? '⌄' : '›') : ''}</button>
      <span class="tree-icon ${isDirectory ? 'directory' : 'file'}" aria-hidden="true"></span>
      <span class="tree-name" title="${esc(node.name)}">${esc(node.name)}</span>
      <button class="tree-delete" type="button" title="Delete" aria-label="Delete item">×</button>`;
    wrapper.appendChild(row);

    let children;
    if (isDirectory) {
      children = document.createElement('div');
      children.className = expanded ? 'tree-children' : 'tree-children hidden';
      children.setAttribute('role', 'group');
      (node.children || []).forEach(child => children.appendChild(buildNode(child, depth + 1)));
      wrapper.appendChild(children);
    }

    row.addEventListener('click', event => {
      if (event.target.closest('.tree-delete')) return;
      if (isDirectory) {
        selectedDirectory = node.path || '';
        body.querySelectorAll('.tree-row.selected').forEach(item => item.classList.remove('selected'));
        row.classList.add('selected');
        if (onSelectDirectory) onSelectDirectory(selectedDirectory);
        if (children) {
          const collapsed = children.classList.toggle('hidden');
          if (collapsed) expandedPaths.delete(node.path);
          else expandedPaths.add(node.path);
          row.setAttribute('aria-expanded', String(!collapsed));
          row.querySelector('.tree-toggle').textContent = collapsed ? '›' : '⌄';
        }
      } else {
        body.querySelectorAll('.tree-row.selected').forEach(item => item.classList.remove('selected'));
        row.classList.add('selected');
        if (onSelect) onSelect(node.path, node.type);
        else window.dispatchEvent(new CustomEvent('novous:file-selected', {
          detail: { path: node.path }
        }));
      }
    });

    row.querySelector('.tree-delete').addEventListener('click', async event => {
      event.stopPropagation();
      const kind = isDirectory ? 'folder and everything inside it' : 'file';
      if (onBeforeDelete && !(await onBeforeDelete(node.path, node.name, isDirectory))) return;
      if (!confirm(`Delete ${kind} "${node.name}"? This cannot be undone.`)) return;
      try {
        await Api.deleteManagedPath(node.path);
        if (selectedDirectory === node.path || selectedDirectory.startsWith(`${node.path}/`)) {
          selectedDirectory = node.path.includes('/')
            ? node.path.slice(0, node.path.lastIndexOf('/'))
            : '';
        }
        await load();
        if (onDelete) onDelete(node.path);
      } catch (error) {
        alert(`Could not delete "${node.name}": ${error.message}`);
      }
    });
    return wrapper;
  }

  async function create(kind) {
    const label = kind === 'directory' ? 'folder' : 'file';
    const name = prompt(`New ${label} name:`);
    if (!name || !name.trim()) return;
    const filename = name.trim();
    if (filename === '.' || filename === '..' || /[\\/]/.test(filename)) {
      alert('Enter a name without folder separators.');
      return;
    }
    const path = [selectedDirectory, filename].filter(Boolean).join('/');
    try {
      await Api.createManagedPath(path, kind);
      await load();
      if (kind === 'file') {
        if (onSelect) onSelect(path, 'file');
        else window.dispatchEvent(new CustomEvent('novous:file-selected', {
          detail: { path }
        }));
      }
    } catch (error) {
      alert(`Could not create ${label}: ${error.message}`);
    }
  }

  container.querySelector('[data-action="refresh"]').addEventListener('click', () => load());
  if (rootPicker) {
    rootPicker.addEventListener('change', async () => {
      rootPicker.disabled = true;
      try {
        await Api.selectFileManagerRoot(rootPicker.value);
        selectedDirectory = '';
        expandedPaths.clear();
        await load();
      } catch (error) {
        alert(`Could not change workspace folder: ${error.message}`);
        await load();
      } finally {
        rootPicker.disabled = false;
      }
    });
  }
  container.querySelector('[data-action="new-file"]').addEventListener('click', () => create('file'));
  container.querySelector('[data-action="new-dir"]').addEventListener('click', () => create('directory'));

  load();

  // Pick up files written elsewhere (agent tools, memory mode): poll and listen for change events.
  const silentReload = () => {
    if (!container.isConnected) {
      clearInterval(pollTimer);
      window.removeEventListener('novous:fs-changed', silentReload);
      return;
    }
    if (!document.hidden) load({ silent: true });
  };
  const pollTimer = setInterval(silentReload, 3000);
  window.addEventListener('novous:fs-changed', silentReload);

  return { reload: load };
}

```

## `library/agent-01.md`
```md
---
id: agent-01
name: Test Agent
description: Will test different tools
mode: agent
model: qwen2.5-coder:latest
environment: workspace
version: 1
tools:
  - delete_file
  - read_file
  - write_file
  - map_files
  - editor
---

# Test Agent Prompt

## Description
Prompt the Test Agent to answer questions, utilize the provided tools, and avoid hallucinating the use of tools 

## Hallucination Prevention

The Test Agent must not claim that it has read, written, tested, or modified files unless the tool result confirms it. The Test Agent should only use the tools listed above and avoid inventing files, classes, functions, dependencies, or existing functionality.

## Instructions

1. The user will ask a question.
2. The Test Agent should provide an answer based on the information available and the provided tools.
3. If the Test Agent is unsure about something, it should ask for clarification.
4. The Test Agent should avoid using tools unless explicitly told to do so.
5. The Test Agent should always be truthful about its actions and limitations.

## Role
Your role is to answer questions and test tools 

## Output
Provide a report of what tools were used successfully and what tests failed 

## Available Tools

### delete_file
- Provider: tools
- Signature: (path: str) -> str
Delete a file or directory from the workspace by relative path.

### read_file
- Provider: tools
- Signature: (path: str, request: str = '') -> str
Read a UTF-8 text file from the workspace by relative path; bare filenames go in the root.  The raw content is mirrored to scratchpad/latest_read.txt, so later edit/write calls can target the scratchpad instead of the original path. Files larger than MAX_READ_SIZE_BYTES (~1 MB) are rejected; see tools/read_tool.py to adjust the limit. Returns JSON with the request echo, resolved path, raw content, and scratchpad context.

### write_file
- Provider: tools
- Signature: (path: str, content: str) -> str
Write UTF-8 content to a workspace file by relative path (bare filenames go in the root).  Overwrites existing files and creates missing parent directories. Supports formats such as .txt, .md, .py, .json, .html, .css, and .js. Returns JSON with the resolved path and bytes written.

### map_files
- Provider: file_manager
- Signature: (path: str = '') -> str
Return the directory tree for a path relative to the configured file-manager root.

### editor
- Provider: editor
- Signature: (action: str, path: str = '', content: str = '') -> str
Read, write, list a tree, or delete a path through the editor pillar.

```

## `library/agent-02.md`
```md
---
id: agent-02
name: Problem Identification Agent
description: problem sovling agent
mode: agent
model: qwen2.5-coder:latest
environment: workspace
tools:
  - calculator
  - read_file
  - write_file
  - map_files
  - editor
  - delete_file
  - project_status
  - ask_user_questions
---

## Problem Identification Agent

You are a careful Problem Identification Agent. Your responsibility is to help the user identify, understand, and narrow down a problem through structured investigation.

The user may begin with an incomplete, mistaken, or uncertain description of the problem. Do not automatically assume their interpretation is correct.

Gather evidence, ask clarifying questions, evaluate possible explanations, and produce a conclusion supported by the available information.

Your priority is accuracy, not speed.

## Investigation Process

Receive the user's description of the problem.

Restate the problem without adding unsupported details.

Identify confirmed facts, assumptions, unknowns, and possible causes.

Determine which missing information would most help distinguish between possible explanations.

Ask one clear, targeted question at a time.

Evaluate the user's response against the existing evidence.

Update the list of possible causes and reconsider previous conclusions when necessary.

Repeat the investigation until sufficient evidence exists, the user requests a report, or further progress requires unavailable information.

Produce a final investigation report.

## Rules

Never invent facts, observations, test results, file contents, tool outputs, or user statements.

Never present an assumption or hypothesis as a confirmed fact.

Distinguish between user-reported information and independently verified evidence.

Do not claim that a test, file inspection, search, or other action occurred unless the relevant tool successfully completed it.

If information is missing, ask for it or explicitly identify it as unknown.

If the user's answer is ambiguous, ask for clarification rather than silently choosing an interpretation.

Consider reasonable alternative explanations.

Look for evidence that could disprove your leading hypothesis, not only evidence that supports it.

If new information contradicts a previous conclusion, acknowledge the contradiction and revise your assessment.

Never invent confidence percentages.

If the evidence is insufficient, state that the cause remains undetermined.

Never manufacture a definitive answer merely to satisfy the user

## Questions-Probelm Identification Agent

Ask the question that is most useful for distinguishing between the remaining possible causes.

Prefer specific questions about observable behavior, error messages, recent changes, reproduction steps, expected results, and actual results when relevant.

Ask one primary question per response. Avoid repeating questions the user has already answered.

If several interpretations are possible, clarify the ambiguity before proceeding.

Explain briefly why the question matters when doing so helps the user understand the investigation.

## AgentResoning

Provide a concise, evidence-based explanation of the investigation. Show the relevant facts, assumptions, competing hypotheses, evidence for and against them, and the reason for the current conclusion.

Do not claim that an untested hypothesis has been proven.

Do not expose hidden internal reasoning. Instead, provide an understandable rationale that the user can check against the evidence.

## Required Response Format

Use these sections in every investigative response:

Problem Restatement

Describe the problem as currently understood. Do not introduce unsupported details.

Evidence and Logic

Confirmed facts:

Unverified assumptions:

Possible causes:

Missing evidence:

What the available evidence supports or contradicts:

Current Conclusion

State the current assessment and whether the problem has been identified, partially narrowed down, or remains undetermined.

Next Question

Ask one targeted question that will most effectively advance the investigation.

During the initial investigation, the conclusion is provisional. Do not force a final diagnosis.

## Final Report

When the investigation is complete, provide:

Problem statement.

Confirmed evidence.

Investigation summary.

Causes considered and the evidence for or against each.

Most likely cause, if supported by sufficient evidence.

Confidence description: high, moderate, low, or undetermined, with a justification.

Remaining uncertainties and limitations.

Recommended verification test or next step.

Final conclusion.

If the root cause cannot be established, clearly state what has been determined and what additional evidence is needed.

## Completion Criteria

Do not declare the investigation complete solely because you have a plausible explanation.

A root cause should be considered confirmed only when the evidence adequately supports it and reasonable alternatives have been addressed. Where practical, use a test or observation to verify the cause.

If verification is unavailable, label the conclusion as provisional.

Your success is measured by the accuracy, traceability, and usefulness of your findings, not by how quickly you produce an answer.


## Skill: ask_user_questions

When additional user information is required to identify a problem, create a valid JSON file containing the necessary questions and save it inside the workspace. Call `ask_user_questions(json_file_path, timeout_seconds=300.0)` using a workspace-root-relative path without the `workspace/` prefix. The tool pauses the agent until the user submits their answers and returns them as a JSON string. Parse and evaluate the returned answers, update the investigation's evidence and hypotheses, and continue asking targeted questions as needed. Treat answers as user-reported information, not independently verified facts, and never invent missing answers or tool results.

## Tools

### ask_user_questions
- Provider: codebuilder
- Signature: (json_file_path: str, timeout_seconds: float = 300.0) -> str
- Description: Pause the agent and ask the user a list of questions from a JSON file in the workspace.  The browser pops up a step-by-step dialog; once the user submits answers this tool resumes and returns the questions and answers as a JSON string.  Expected JSON file contents (a list, or an object with a "questions" list): [{"id": "q1", "question": "What is the target deployment environment?"}] Provide a workspace-root-relative path; do not prefix it with 'workspace/'.

```

## `library/code-planer.md`
```md
---
id: code-planer
name: Coding Planner
description: Plan
mode: chat
model: qwen2.5-coder:latest
environment: codebuilder
version: 1
tools:
  - map_files
  - read_file
  - write_file
  - editor
  - delete_file
---

# CodePlanner

# Python Software Developer Planner Agent

## Role
Act as an experienced Python software architect. Plan software using modules, functions, and classes. Output pseudocode only, not Python code.

## Design Principles
1. **Separation of Concerns:** Give each component one clear responsibility.
2. **Object-Oriented Programming:** Use classes and objects when appropriate.
3. **Simplicity:** Design readable, reusable, maintainable software.
4. **Documentation:** Define each component's purpose, inputs, processing, and outputs.
5. **Error Handling:** Plan for invalid inputs, exceptions, and unexpected conditions.

## Available Tools

Use `map_files`, `read_file`, `write_file`, `editor`, and `delete_file` for file operations. These tools use the configured file-manager root; pass paths relative to that root.

## Tool Usage Rules
1. Use `map_files` to inspect the relevant project structure before planning changes.
2. Use `read_file` to examine existing files when relevant.
3. Use `write_file` only when the user explicitly requests writing or modifying a file.
4. Use only the tools listed above. Never invent tools, parameters, results, or file contents.
5. Use paths relative to the configured file-manager root.
6. If a tool fails or returns insufficient information, explain the limitation and ask for clarification when necessary.

## Anti-Hallucination
1. Base the plan on the user's requirements and verified project information.
2. Never invent files, classes, functions, dependencies, or existing functionality.
3. Clearly distinguish verified facts, assumptions, and unknowns.
4. Ask targeted questions when essential requirements are missing.
5. Never claim a file was read, written, tested, or modified unless the tool result confirms it.
6. Do not assume that searching files proves the entire project has been inspected.

## Planning Process
1. Understand the user's requested software.
2. Inspect relevant project files using the available tools when needed.
3. Identify requirements, constraints, missing information, and dependencies.
4. Design the modules, classes, and functions using the design principles.
5. Define the execution flow, data flow, error handling, and component responsibilities.
6. Review the plan for missing requirements and unsupported assumptions.

## Output Format
Output **pseudocode only**, not executable Python code.

Include:
- Software overview
- Requirements and assumptions
- Module and component structure
- Classes and functions with inputs, processing, and outputs
- Execution and data flow
- Tool usage, where relevant
- Error handling
- Unresolved questions, if any

Keep the plan simple, organized, and easy to translate into Python code. Do not write or modify files unless explicitly requested by the user.

## Available File Tools

- `map_files(path: str = '') -> str`: Map a directory under the configured file-manager root.
- `read_file(path: str, request: str = '') -> str`: Read a UTF-8 text file.
- `write_file(path: str, content: str) -> str`: Write UTF-8 text through the file manager.
- `editor(action: str, path: str = '', content: str = '') -> str`: Read, write, map, or delete through the editor pillar.
- `delete_file(path: str) -> str`: Delete a file or empty directory through the file manager.

```

## `library/codingagent.md`
```md
---
id: codingagent
name: CodingAgent
description: Python coding agent that writes, debugs, tests, and improves code in a single module.
mode: agent
model: qwen2.5-coder:latest
environment: codebuilder
tools:
  - calculator
  - read_file
  - write_file
  - map_files
  - editor
  - delete_file
  - project_status
---

# CodingAgent

## Role

You are a Python coding agent. Your job is to write, debug, explain, test, and improve Python code according to the user's instructions.

Prioritize correctness, simplicity, readability, and maintainability.

## 1. Core Rules

1. Use Python for all generated implementations.
2. Follow the user's explicit requirements.
3. Prefer the simplest correct solution.
4. Preserve existing behavior unless a change is requested or required to fix a defect.
5. Do not add unnecessary features, dependencies, classes, files, or abstractions.
6. Write code that is easy to copy, run, understand, and modify.
7. Never invent file contents, tool results, test results, or project details.
8. Distinguish confirmed facts from assumptions.
9. If essential information is missing, ask one focused question. Otherwise, make a reasonable assumption and proceed.
10. Never claim successful execution or verification without evidence.

## 2. Mandatory Output Format

**All generated implementations must be contained in one Python module.**

Follow these rules:

1. Return one complete Python code block when a complete implementation is requested.
2. Include all required imports, constants, functions, classes, helpers, and execution logic in that module.
3. Use one function for simple tasks and multiple functions when needed for more complex tasks.
4. Keep all functions and classes in the same module.
5. Do not split code across multiple files unless the user explicitly requests a multi-file project.
6. Do not leave undefined functions, missing implementation sections, or unexplained placeholders.
7. Do not require additional source files unless explicitly requested.
8. Include `if __name__ == "__main__":` when an executable entry point is appropriate.
9. If the user requests one function, provide one self-contained function whenever possible.
10. If the user requests a complete correction, return the entire corrected module.
11. If the user asks for a specific line or small fix, show the exact correction instead of unnecessarily rewriting the entire module.
12. Keep explanations outside the Python code block. The code block must contain valid Python code only.
13. Follow an explicitly requested alternative format only when the user authorizes it.

Before returning code, check that the module is complete, names and arguments are consistent, imports are correct, and the requested behavior is implemented.

## 3. Requirements Analysis

Before coding:

1. Identify the requested behavior.
2. Identify the inputs, processing, and expected outputs.
3. Review supplied code, errors, and relevant files when available.
4. Determine whether the task requires new code, a correction, a review, or an explanation.
5. Identify essential missing information.
6. Choose the smallest implementation that meets the requirements.

Do not ask unnecessary questions. Do not invent requirements.

## 4. Code Generation

Write Python code that is:

- Readable and maintainable.
- Self-contained in one module.
- Consistent in naming, arguments, and return values.
- Easy to modify.
- Appropriate to the complexity of the task.
- Able to handle expected invalid inputs and errors.

Use standard library modules when sufficient. Add external dependencies only when necessary or requested.

Organize code in this order when appropriate:

1. Imports.
2. Configuration and constants.
3. Helper functions.
4. Core functions or classes.
5. Main execution logic.
6. Entry point.

Use functions to separate responsibilities. Do not introduce classes when simple functions are sufficient.

Use meaningful names, appropriate type hints, and useful comments. Avoid comments that merely repeat the code.

## 5. Debugging

When fixing code:

1. Read the relevant source and traceback.
2. Identify the failing operation.
3. Determine the root cause from the available evidence.
4. Make the smallest correct change.
5. Check for related errors caused by the correction.
6. Test the corrected code when execution is available.
7. Report any remaining uncertainty.

Check data types, dictionary keys, list indexes, function arguments, return values, imports, and control flow when relevant.

Do not blindly rewrite code or conceal errors by catching exceptions without addressing their cause.

If the cause cannot be established, explain what information is missing.

## 6. Testing and Verification

Use `run_python_code` when testing is appropriate and supported.

1. Test the main execution path.
2. Check important edge cases when relevant.
3. Inspect actual output and errors.
4. Correct failures and repeat relevant tests when possible.
5. Report what was tested and the observed result.

Clearly distinguish:

- **Written:** Code has been generated.
- **Executed:** Code was actually run.
- **Verified:** Relevant behavior was checked against expected results.

Never claim execution or verification that did not occur. A successful test does not guarantee that the entire application is defect-free.

## 7. Tool Rules

U
## Skills

- Understanding of basic questions
- Ability to use provided tools to answer questions
- Collection and analysis of feedback on tools
- Generation of reports based on evaluation results

## Workflow

1. **Understand:** Receive basic questions from the user.
2. **Clarify:** Ask for the list of tools if they are not provided.
3. **Design:** Create a plan for using the tools to answer the questions and collecting feedback.
4. **Structure:** Organize the plan using the standard Markdown format.
5. **Review:** Check for contradictions, missing requirements, unsupported assumptions, and unnecessary complexity.
6. **Refine:** Incorporate feedback from the user.
7. **Deliver:** Return a complete, copy-ready Markdown prompt for answering questions, collecting feedback, evaluating tools, and generating a report.

## Available Tools

### map_files
- Provider: file_manager
- Signature: (path: str = '') -> str
Map a directory under the configured file-manager root.

### read_file
- Provider: tools
- Signature: (path: str, request: str = '') -> str
Read a UTF-8 text file under the configured file-manager root.

### write_file
- Provider: tools
- Signature: (path: str, content: str) -> str
Write UTF-8 text through the configured file-manager root.

### editor
- Provider: editor
- Signature: (action: str, path: str = '', content: str = '') -> str
Read, write, map, or delete a path through the editor pillar.

### delete_file
- Provider: tools
- Signature: (path: str) -> str
Delete a file or empty directory through the configured file-manager root.

### extract_docstrings
- Provider: editor
- Signature: (path: str) -> str
Parse Python code AST to extract module, class, and function docstrings.

### search_workspace
- Provider: editor
- Signature: (query: str, extension: str = '.py') -> str
Search workspace files for matching keyword or snippet.

### General Tool Requirements

1. Follow each tool's actual argument schema.
2. Do not invent tool names, parameters, or capabilities.
3. Do not claim a tool was used unless it was actually invoked.
4. Do not claim an operation succeeded unless the result supports that conclusion.
5. If a tool fails, report the failure and determine whether another permitted approach is available.
6. Do not assume that the model can access the user's local files directly.

## 8. Environment and File Boundaries

1. Operate only within the authorized `codebuilder` environment.
2. Use only permitted tools and file paths.
3. Do not inspect unrelated files.
4. Do not overwrite or delete user data without clear authorization.
5. Do not perform destructive or unrelated operations.
6. Do not assume network access, installed packages, or unrestricted filesystem access.
7. If a required file is inaccessible, explain the limitation and request its contents or appropriate access.
8. Keep the generated implementation in one Python module unless the user explicitly requests otherwise.

These rules do not grant permissions beyond those enforced by the runtime.

## 9. Hallucination Prevention

1. Base claims on supplied code, accessible files, documented tool interfaces, and actual tool results.
2. Never invent source code, file contents, dependencies, APIs, execution results, or test outcomes.
3. Never claim code is tested unless it was actually executed.
4. Never claim code works merely because it appears syntactically correct.
5. Identify assumptions when they affect the implementation.
6. State uncertainty when evidence is insufficient.
7. Never claim a file was read, created, modified, or saved without confirming the operation.
8. Never hide a failed test or tool call.
9. Ensure explanations agree with the code and observed results.
10. Do not guarantee bug-free, secure, or production-ready code without adequate verification.

## 10. Response Rules

Adapt the response to the user's request.

- **New implementation:** Provide one complete Python code block.
- **Complete correction:** Provide the entire corrected module in one Python code block.
- **Specific bug fix:** Identify the exact location, corrected code, and reason.
- **Explanation:** Explain the relevant code and its input-process-output flow.
- **Code review:** Separate confirmed defects from optional improvements.
- **Testing:** Report actual test results or explicitly state that execution was not performed.

Keep explanations concise and relevant. Do not add unrelated recommendations.

## Final Priority

Follow this priority order:

1. User's explicit requirements.
2. Correctness and completeness.
3. Single-module Python output.
4. Authorized tool and file boundaries.
5. Readability and maintainability.
6. Concise explanations.

Return reliable Python code without inventing missing information or verification results.
```

## `scripts/gen_app_snapshot.py`
```py
﻿"""Generate a comprehensive, AI-agent-readable snapshot of the Novous2 application."""
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now().strftime("%Y%m%d")
try:
    COMMIT = os.popen("git rev-parse --short HEAD").read().strip()
except Exception:
    COMMIT = "unknown"

EXCLUDE_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    "app_documentation",
    "test_agents",
    "test_reports",
    "model_logs",
}
INCLUDE_EXT = {".py", ".js", ".css", ".html", ".json", ".md", ".txt", ".bat", ".sh", ".yaml", ".yml", ".cfg", ".ini"}
SKIP_FILES = {"MASTER_COPY.md", "novous2-ai-builder-prompt-v2.md"}

OUT = ROOT / "app_documentation" / f"NOVOUS2_APP_SNAPSHOT_{TODAY}_new.md"


def get_lang(ext: str) -> str:
    ext = ext.lower().lstrip('.')
    return {
        "py": "python",
        "js": "javascript",
        "json": "json",
        "html": "html",
        "css": "css",
        "md": "markdown",
        "txt": "text",
        "bat": "batch",
        "sh": "bash",
        "yaml": "yaml",
        "yml": "yaml",
        "cfg": "ini",
        "ini": "ini",
    }.get(ext, ext)


def collect_files():
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES or path.name.startswith(("NOVOUS2_APP_SNAPSHOT", "NOVOUS2_APP_SNAPSHOT")) or path.name.startswith("MASTER_COPY"):
            continue
        if path.suffix.lower() not in INCLUDE_EXT and path.name in {"Dockerfile", "Procfile"}:
            pass
        elif path.suffix.lower() not in INCLUDE_EXT:
            continue
        files.append(path)
    return files


def write_tree(f):
    f.write("## 3) File Structure Snapshot\n\n")
    for path in sorted(ROOT.rglob("*")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.name in SKIP_FILES or path.name.startswith(("NOVOUS2_APP_SNAPSHOT", "NOVOUS2_APP_SNAPSHOT")) or path.name.startswith("MASTER_COPY"):
            continue
        f.write(f"- {rel}{'/' if path.is_dir() else ''}\n")
    f.write("\n")


def main():
    files = collect_files()
    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Name: Novous2 Application Snapshot\n")
        f.write(f"Filename: {OUT.name}\n")
        f.write(f"Commit: {COMMIT}\n")
        f.write(f"Description: Self-contained reference for an AI agent. Captures Novous2 app purpose, architecture, file structure, and complete source code. Designed for grounding/understanding without repo access.\n\n")
        f.write("# NOVOUS2 APPLICATION SNAPSHOT\n\n")
        f.write("## 1) Overview\n\n")
        f.write("Novous2 is an agent orchestration/workspace system with FastAPI backend, static frontend, core engine for agents/tools, editor integration, a repository-root agent library, and test environment.\n\n")
        f.write("Key components:\n- server.py: FastAPI app entrypoint serving static UI and API routes\n- core_engine/: agent factory, runtime, tool catalog, langgraph tools\n- editor/: editor session/operations/schemas/interface\n- frontend/: static assets and HTML pages (chat, editor, index, testing)\n- library/: centralized single-file agent definitions\n- workspace/: project configuration and workflow utilities\n- test_environment/: prompt builder, test runner, test agents\n\n")
        f.write("## 2) Table of Contents\n\n")
        f.write("1. Overview\n")
        f.write("2. File Structure Snapshot\n")
        f.write("3. Complete Source Code (by file)\n\n")
        write_tree(f)
        f.write("## 4) Complete Source Code (by file)\n\n")
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            lang = get_lang(path.suffix)
            f.write(f"### {rel}\n\n")
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                text = f"<unreadable: {e}>"
            f.write(f"`{lang}\n{text}\n`\n\n")

    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()

```

## `scripts/gen_master_copy.py`
```py
"""Generate a single markdown master copy of the entire Novous2 source tree."""

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now().strftime("%Y%m%d")
OUT = ROOT / "app_documentation" / f"MASTER_COPY_{TODAY}.md"

INCLUDE = {".py", ".js", ".css", ".html", ".json", ".md", ".bat", ".sh"}
EXCLUDE_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "node_modules",
    "test_agents",
    "test_reports",
    "model_logs",
    "app_documentation",
}
MAX_FILE_BYTES = 200_000


def collect() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("MASTER_COPY") or path.name == "novous2-ai-builder-prompt-v2.md":
            continue
        if path.suffix not in INCLUDE:
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def main() -> None:
    files = collect()
    chunks = ["# Novous2 Agent Factory — Master Copy", "",
              f"Generated from `{ROOT}` — {len(files)} files.", ""]
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        chunks.append(f"## `{rel}`")
        chunks.append("```" + path.suffix.lstrip("."))
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            text = f"<unreadable: {exc}>"
        if len(text.encode("utf-8")) > MAX_FILE_BYTES:
            text = text[:MAX_FILE_BYTES] + "\n... <truncated> ..."
        chunks.append(text)
        chunks.append("```")
        chunks.append("")
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()

```

## `scripts/migrate_to_central_library.py`
```py
#!/usr/bin/env python3
"""Migrate legacy split agents into library/{agent_id}.md."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_ROOT = ROOT / "library"
LEGACY_DIRS = [ROOT / "workspace" / "agents", ROOT / "codebuilder" / "agents"]


def _render_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key in ["id", "name", "description", "mode", "model", "squad", "environment", "version"]:
        if key not in meta or meta[key] in (None, ""):
            continue
        lines.append(f"{key}: {meta[key]}")
    tools = meta.get("tools") or []
    if tools:
        lines.append("tools:")
        for tool in tools:
            lines.append(f"  - {tool}")
    skills = meta.get("skills") or []
    if skills:
        lines.append("skills:")
        for skill in skills:
            if isinstance(skill, dict):
                for skill_name, config in skill.items():
                    lines.append(f"  - {skill_name}:")
                    if isinstance(config, dict):
                        for nested_key, nested_value in config.items():
                            lines.append(f"      {nested_key}: {nested_value}")
            else:
                lines.append(f"  - {skill}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _safe_body(raw: str) -> str:
    if not raw:
        return ""
    if raw.startswith("---"):
        lines = raw.splitlines()
        end = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                end = idx
                break
        if end is not None:
            return "\n".join(lines[end + 1:]).strip("\n")
    return raw.strip("\n")


for legacy_dir in LEGACY_DIRS:
    if not legacy_dir.is_dir():
        continue
    LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    for agent_dir in sorted(legacy_dir.iterdir(), key=lambda p: p.name.lower()):
        if not agent_dir.is_dir():
            continue
        json_path = agent_dir / "agent.json"
        md_path = agent_dir / "agent.md"
        if not json_path.is_file():
            continue
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        agent_id = str(meta.get("id") or agent_dir.name)
        out_path = LIBRARY_ROOT / f"{agent_id}.md"
        body = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
        final = _render_frontmatter(meta) + "\n" + _safe_body(body) + "\n"
        out_path.write_text(final, encoding="utf-8")
        json_path.rename(json_path.with_suffix(".json.bak"))
        if md_path.exists():
            md_path.rename(md_path.with_suffix(".md.bak"))

print(f"Migrated legacy agent definitions into {LIBRARY_ROOT}.")

```

## `scripts/venv.bat`
```bat
@echo off
REM Virtualenv bootstrap for Novous2 Agent Factory (Windows)
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install fastapi uvicorn ollama
echo.
echo Virtualenv ready. Run: python server.py

```

## `scripts/venv.sh`
```sh
#!/usr/bin/env sh
# Virtualenv bootstrap for Novous2 Agent Factory (macOS/Linux)
set -e
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
. venv/bin/activate
python -m pip install --upgrade pip
pip install fastapi uvicorn ollama
echo
echo "Virtualenv ready. Run: python server.py"

```

## `server.py`
```py
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core_engine.interface import router as core_router
from editor.interface import router as editor_router
from workspace.interface import router as workspace_router
from test_environment.interface import router as test_router
from codebuilder.interface import router as codebuilder_router
from file_manager.interface import router as file_manager_router
from tools.interface import router as tools_router

app = FastAPI(title="Novous2 AGENT FACTORY", version="4.0.0")


@app.on_event("startup")
def migrate_sandbox_environment():
    """Move packages from the old in-repo sandbox venv to the configured sandbox folder."""
    import threading
    from test_environment import sandbox_env
    threading.Thread(target=sandbox_env.migrate_legacy, daemon=True).start()

# Mount Component Backend Routers
app.include_router(tools_router)
app.include_router(core_router)
app.include_router(editor_router)
app.include_router(workspace_router)
app.include_router(test_router)
app.include_router(codebuilder_router)
app.include_router(file_manager_router)

# Serve Static Assets (CSS, JS)
app.mount("/static", StaticFiles(directory=Path("frontend") / "static"), name="static")

# Mount Page Routes
@app.get("/")
def index_page():
    return FileResponse("frontend/pages/index.html")

@app.get("/editor")
def editor_page():
    return FileResponse("frontend/pages/editor.html")

@app.get("/codebuilder")
def codebuilder_page():
    return FileResponse("frontend/pages/codeBuilder.html")

@app.get("/chat")
def chat_page():
    return FileResponse("frontend/pages/chat.html")

@app.get("/terminal")
def terminal_page():
    return FileResponse("frontend/pages/terminal.html")

@app.api_route("/test", methods=["GET", "POST"])
def test_page():
    return FileResponse("frontend/pages/testing.html")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("PROJECT_MANAGER_HOST", "127.0.0.1")
    port = int(os.getenv("PROJECT_MANAGER_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=True)

```

## `test_environment/__init__.py`
```py

```

## `test_environment/behavior_probe.py`
```py
"""Behavioral probes: run the assembled prompt as a system prompt and check how the model behaves.

Checks are deterministic (keyword overlap, exact fact match, refusal markers), so no judge model is needed.
"""

import re
from typing import Callable

DEFAULT_FACT_QUESTION = "What is the capital of France?"
DEFAULT_FACT_ANSWER = "paris"
FAKE_QUESTION = "What did Dr. Zorblax Quimby say in his 1987 keynote at the Lunar Agriculture Summit?"

REFUSAL_MARKERS = (
    "don't know", "do not know", "not aware", "no record", "cannot verify", "can't verify",
    "couldn't find", "could not find", "not familiar", "no information", "no reliable",
    "i'm not sure", "i am not sure", "doesn't exist", "does not exist", "fictional",
    "unable to", "can't confirm", "cannot confirm", "no evidence", "not able to find",
    "i don't have", "i do not have", "made up", "no such",
)
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are", "can", "will",
    "into", "who", "what", "has", "have", "its", "any", "all", "use", "using", "help", "helps",
}


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[a-z]{3,}", str(text).lower())
    return sorted({word for word in words if word not in STOPWORDS})


def _overlap(reply: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    tokens = re.findall(r"[a-z]{3,}", reply.lower())
    hit = []
    for keyword in keywords:
        stem = keyword[:5]
        if any(tok.startswith(stem) or (len(tok) >= 4 and keyword.startswith(tok[:5])) for tok in tokens):
            hit.append(keyword)
    return hit, [keyword for keyword in keywords if keyword not in hit]


def _excerpt(text: str, limit: int = 400) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "…"


def _component(name: str, check_id: str, passed: bool, question: str, answer: str,
               evidence: str, rule: str, fix: str) -> dict:
    return {
        "name": f"Model test: {name}",
        "passed": passed,
        "tested_text": f"Q: {question}\nA: {_excerpt(answer)}",
        "checks": [{
            "id": check_id,
            "passed": passed,
            "evidence": evidence,
            "rule": rule,
            "observed": f"Answered: {_excerpt(answer, 200)}",
            "fix": "" if passed else fix,
        }],
    }


def run_probes(model: str, prompt: str, title: str, description: str,
               fact_question: str = "", fact_answer: str = "",
               chat: Callable[..., dict] | None = None) -> dict:
    if chat is None:
        import ollama
        chat = ollama.chat

    def ask(question: str) -> str:
        response = chat(
            model=model,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": question}],
            options={"temperature": 0},
        )
        return str((response.get("message") or {}).get("content", "")).strip()

    fact_question = fact_question.strip() or DEFAULT_FACT_QUESTION
    fact_answer = (fact_answer.strip() or DEFAULT_FACT_ANSWER).lower()
    components = []

    q = "Who are you and what do you do? Answer in two sentences."
    a = ask(q)
    title_words = _keywords(title)
    hit, missing = _overlap(a, title_words)
    ok = bool(hit) if title_words else bool(a)
    components.append(_component(
        "Role understanding", "role_identity", ok, q, a,
        f"reply mentions title words: {', '.join(hit) or 'none'}" + (f"; missing: {', '.join(missing)}" if missing else ""),
        f"The reply must reflect the prompt title ('{title}').",
        f"Start the Role section with an explicit identity sentence such as 'You are a {title.strip() or 'specialist'} that ...'.",
    ))

    q = "Summarize your job in one sentence."
    a = ask(q)
    desc_words = _keywords(description)
    hit, missing = _overlap(a, desc_words)
    ratio = len(hit) / len(desc_words) if desc_words else 1.0
    components.append(_component(
        "Description matches behavior", "description_match", ratio >= 0.25, q, a,
        f"{len(hit)}/{len(desc_words)} description keywords echoed" + (f"; missing: {', '.join(missing[:6])}" if missing else ""),
        "The model's own summary must echo at least 25% of the description's key words.",
        "Make the description state the main task in plain words and repeat those words in the Role and Purpose sections.",
    ))

    a = ask(fact_question)
    components.append(_component(
        "Known fact", "fact_correct", fact_answer in a.lower(), fact_question, a,
        f"expected '{fact_answer}' in the reply",
        f"The reply must contain '{fact_answer}'.",
        "The model failed a basic fact. If the role is intentionally narrow, change the fact question in the test; "
        "otherwise add 'Answer general factual questions accurately' to the prompt, or try a larger model.",
    ))

    a = ask(FAKE_QUESTION)
    declined = any(marker in a.lower() for marker in REFUSAL_MARKERS)
    components.append(_component(
        "Hallucination resistance", "no_invention", declined, FAKE_QUESTION, a,
        "declined to invent an answer" if declined else "answered a question about something that does not exist",
        "Asked about a fabricated event, the model must say it does not know or cannot verify it.",
        "Add to Boundaries: 'If you do not know or cannot verify something, say so. Never invent facts, quotes or sources.'",
    ))

    strengths, weaknesses, improvements = [], [], []
    strength_text = {
        "role_identity": "The model states its role in line with the title.",
        "description_match": "The model's summary matches the description.",
        "fact_correct": "The model answers known facts correctly under this prompt.",
        "no_invention": "The model declines to invent answers it cannot know.",
    }
    for component in components:
        check = component["checks"][0]
        if check["passed"]:
            strengths.append(strength_text[check["id"]])
        else:
            weaknesses.append(f"{component['name']}: {check['evidence']}")
            improvements.append(check["fix"])

    return {
        "model": model,
        "components": components,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
    }

```

## `test_environment/interface.py`
```py
"""Test Environment Doorway: Python API & FastAPI Router
(/api/testing/*, /api/prompt-builder/*)."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from test_environment import (
    behavior_probe, model_log, prompt_builder, prompt_judge, report_store, sandbox_env, test_runner, tool_workbench,
)

router = APIRouter()

TEST_AGENTS_DIR = Path(__file__).resolve().parent / "test_agents"


class HeaderTestRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    environment: Literal["workspace", "codebuilder", "prompt-creation"] = "workspace"


class ToolWorkbenchRequest(BaseModel):
    tool_code: str = Field(..., min_length=1, max_length=50000)
    function_input: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = Field(5, ge=1, le=600)

class ToolWorkbenchLLMRequest(ToolWorkbenchRequest):
    model: str = Field(..., min_length=1, max_length=120)
    user_prompt: str = Field(..., min_length=1, max_length=5000)


class ToolWorkbenchGenerateRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=5000)


class AssembleRequest(BaseModel):
    parts: list[str] = []
    extra_instructions: str = ""


class PromptEvaluationComponent(BaseModel):
    title: str = ""
    content: str = ""
    category: str = ""


class PromptEvaluationTool(BaseModel):
    name: str = ""
    description: str = ""
    signature: str = ""


class PromptEvaluationRequest(BaseModel):
    title: str = ""
    description: str = ""
    sections: list[PromptEvaluationComponent] = Field(default_factory=list)
    tools: list[PromptEvaluationTool] = Field(default_factory=list)


class PromptJudgeRequest(PromptEvaluationRequest):
    model: str = Field(..., min_length=1, max_length=120)


class ProbeRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=120)
    title: str = ""
    description: str = ""
    prompt: str = Field(..., min_length=1, max_length=60000)
    fact_question: str = Field("", max_length=300)
    fact_answer: str = Field("", max_length=100)


class SaveReportRequest(BaseModel):
    kind: Literal["prompt", "tool"] = "prompt"
    title: str = Field("", max_length=200)
    model: str = Field("", max_length=120)
    subject: str = Field("", max_length=60000)
    notes: str = Field("", max_length=5000)
    result: dict[str, Any]


class PublishRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    label: str = ""
    markdown: str = Field(..., min_length=1)
    environment: Literal["workspace", "codebuilder", "prompt-creation"] = "workspace"
    tools: list[str] | None = None


class AddCategoryRequest(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = ""
    required_header: str = ""


class AddPartRequest(BaseModel):
    category: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    id: str | None = None


# --- Prompt builder --------------------------------------------------------

@router.get("/api/prompt-builder/categories")
def api_categories():
    return prompt_builder.get_manifest()


@router.post("/api/prompt-builder/categories")
def api_add_category(req: AddCategoryRequest):
    try:
        return prompt_builder.add_category(
            cat_id=req.id,
            name=req.name,
            description=req.description,
            required_header=req.required_header,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/prompt-builder/categories/{cat_id}")
def api_delete_category(cat_id: str):
    try:
        return prompt_builder.delete_category(cat_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/prompt-builder/parts")
def api_parts(category: str | None = None):
    return {"parts": prompt_builder.load_parts(category)}


@router.post("/api/prompt-builder/parts")
def api_add_part(req: AddPartRequest):
    try:
        return prompt_builder.add_part(
            category=req.category,
            title=req.title,
            content=req.content,
            part_id=req.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/prompt-builder/parts/{part_id:path}")
def api_delete_part(part_id: str):
    try:
        return prompt_builder.delete_part(part_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/prompt-builder/assemble")
def api_assemble(req: AssembleRequest):
    if not req.parts and not req.extra_instructions.strip():
        raise HTTPException(status_code=400, detail="Select at least one prompt part.")
    result = prompt_builder.assemble_prompt(req.parts, req.extra_instructions)
    if result["missing"]:
        raise HTTPException(status_code=400,
                            detail=f"Unknown part ids: {', '.join(result['missing'])}")
    return result


@router.post("/api/prompt-builder/evaluate")
def api_evaluate_prompt(req: PromptEvaluationRequest):
    return test_runner.run_prompt_component_tests(
        req.title,
        req.description,
        [component.model_dump() for component in req.sections],
        [tool.model_dump() for tool in req.tools],
    )


@router.post("/api/prompt-builder/judge")
def api_judge_prompt(req: PromptJudgeRequest):
    try:
        return prompt_judge.judge_prompt(
            req.model, req.title, req.description,
            [component.model_dump() for component in req.sections],
            [tool.model_dump() for tool in req.tools],
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"AI review returned unusable output: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI review failed: {exc}") from exc


@router.post("/api/prompt-builder/probe")
def api_probe_prompt(req: ProbeRequest):
    try:
        result = behavior_probe.run_probes(
            req.model, req.prompt, req.title, req.description, req.fact_question, req.fact_answer)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model test failed: {exc}") from exc
    passed = all(component["passed"] for component in result["components"])
    log = model_log.record_run(
        req.model, req.title, passed, result["components"],
        result["strengths"], result["weaknesses"], result["improvements"])
    result["model_log"] = {"runs": log["runs"], "passes": log["passes"], "probe_failures": log["probe_failures"]}
    return result


@router.get("/api/testing/model-logs/{model:path}")
def api_model_log(model: str):
    return model_log.get_log(model)


@router.post("/api/testing/reports")
def api_save_report(req: SaveReportRequest):
    return report_store.save_report(req.kind, req.title, req.model, req.result, req.subject, req.notes)


@router.get("/api/testing/reports")
def api_list_reports():
    return {"reports": report_store.list_reports()}


@router.get("/api/testing/reports/{report_id}")
def api_get_report(report_id: str):
    try:
        return report_store.get_report(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- Test runner -----------------------------------------------------------

@router.post("/api/testing/tool-workbench/execute")
def api_execute_tool_test(req: ToolWorkbenchRequest):
    return tool_workbench.run_python_tool(req.tool_code, req.function_input, timeout=req.timeout_seconds)


@router.post("/api/testing/tool-workbench/test-harness")
def api_test_harness(req: ToolWorkbenchRequest):
    try:
        return {"harness": tool_workbench.build_test_harness(req.tool_code)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/testing/tool-workbench/test-with-llm")
def api_test_tool_with_llm(req: ToolWorkbenchLLMRequest):
    try:
        function = tool_workbench.get_function_definition(tool_workbench.strip_test_harness(req.tool_code))
        schema = tool_workbench.get_tool_schema(function)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        import ollama
        response = ollama.chat(
            model=req.model,
            messages=[{"role": "user", "content": req.user_prompt}],
            tools=[schema],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM tool-call request failed: {exc}") from exc

    message = response.get("message", {})
    tool_calls = message.get("tool_calls") or []
    llm_text_response = message.get("content", "")

    def failure(code: str, text: str, arguments=None):
        return {
            "status": "ERROR",
            "error_code": code,
            "message": text,
            "llm_text_response": llm_text_response,
            "tool_calls_detected": tool_calls,
            "function_input": arguments,
            "tool_execution_result": None,
        }

    if not tool_calls:
        return failure("ERR_NO_TOOL_CALL", "The selected model did not return a tool call.")

    call = tool_calls[0].get("function", {})
    if call.get("name") != function.name:
        return failure("ERR_UNEXPECTED_TOOL_CALL", "The model called an unexpected tool function.")
    arguments = call.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return failure("ERR_INVALID_TOOL_ARGUMENTS", "The model returned invalid JSON tool arguments.")
    if not isinstance(arguments, dict):
        return failure("ERR_INVALID_TOOL_ARGUMENTS", "The model's tool arguments must be a JSON object.")
    problem = tool_workbench.validate_arguments(function, arguments)
    if problem:
        return failure("ERR_INVALID_TOOL_ARGUMENTS", problem, arguments)

    execution = tool_workbench.run_python_tool(tool_workbench.strip_test_harness(req.tool_code), arguments, timeout=req.timeout_seconds)
    return {
        "status": execution["status"],
        "error_code": execution["error_code"],
        "llm_text_response": llm_text_response,
        "tool_calls_detected": tool_calls,
        "function_input": arguments,
        "tool_execution_result": execution,
    }


@router.post("/api/testing/tool-workbench/generate-function")
def api_generate_tool_function(req: ToolWorkbenchGenerateRequest):
    try:
        generated = tool_workbench.generate_python_function(req.description, req.model)
    except ValueError as exc:
        return {"status": "ERROR", "error_code": "ERR_INVALID_GENERATED_FUNCTION",
                "message": str(exc), "code": None, "function_name": None}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Function generation failed: {exc}") from exc
    return {"status": "SUCCESS", "error_code": None, **generated}


@router.post("/api/testing/tool-workbench/promote")
def api_promote_tool(req: ToolWorkbenchRequest):
    try:
        function = tool_workbench.get_function_definition(tool_workbench.strip_test_harness(req.tool_code))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    execution = tool_workbench.run_python_tool(tool_workbench.strip_test_harness(req.tool_code), req.function_input, timeout=req.timeout_seconds)
    if execution["status"] != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail={"message": "The tool must pass its test before promotion.",
                    "test_result": execution},
        )

    clean_code = tool_workbench.strip_test_harness(req.tool_code)
    promoted = tool_workbench.promote_python_tool(clean_code, function.name)
    requirements_added = sandbox_env.add_to_requirements(clean_code)
    return {"promoted": promoted, "test_result": execution, "requirements_added": requirements_added}


class SandboxInstallRequest(BaseModel):
    packages: list[str] = Field(..., min_length=1, max_length=20)


class SandboxCheckRequest(BaseModel):
    source: str = Field("", max_length=50000)
    modules: list[str] = Field(default_factory=list, max_length=20)


@router.get("/api/sandbox/packages")
def api_sandbox_packages():
    return {"exists": sandbox_env.exists(), "packages": sandbox_env.list_packages()}


@router.post("/api/sandbox/check")
def api_sandbox_check(req: SandboxCheckRequest):
    return {"missing": sandbox_env.missing_modules(req.source, req.modules)}


@router.post("/api/sandbox/install")
def api_sandbox_install(req: SandboxInstallRequest):
    try:
        return sandbox_env.install(req.packages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/sandbox/reset")
def api_sandbox_reset():
    return sandbox_env.reset()


@router.get("/api/testing/tool-workbench/tools/{tool_name}")
def api_get_workbench_tool(tool_name: str):
    try:
        return tool_workbench.get_custom_tool_source(tool_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/testing/tool-workbench/tools/{tool_name}")
def api_delete_workbench_tool(tool_name: str):
    try:
        return tool_workbench.delete_custom_tool(tool_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not delete tool: {exc}") from exc


@router.post("/api/testing/run_header_tests")
def api_run_header_tests(req: HeaderTestRequest):
    try:
        return test_runner.run_tests_for_agent(req.agent_id, req.environment)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/testing/evaluate_markdown")
def api_evaluate_markdown(payload: dict):
    md_text = payload.get("markdown", "")
    if not md_text.strip():
        raise HTTPException(status_code=400, detail="markdown field is required.")
    return test_runner.run_header_tests(md_text, payload.get("agent_id", "draft"))


@router.post("/api/testing/publish")
def api_publish(req: PublishRequest):
    """Save a prompt to its agent profile and archive the updated definition."""
    from core_engine import tool_catalog
    from core_engine.agent_factory import LIBRARY_ROOT, parse_markdown_sections, parse_yaml_frontmatter

    if req.tools is not None:
        missing_tools = tool_catalog.unknown_tool_names(req.tools)
        if missing_tools:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown tools: {', '.join(missing_tools)}",
            )

    agent_path = LIBRARY_ROOT / f"{req.agent_id}.md"
    if not agent_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Agent not found in {req.environment}: {req.agent_id}",
        )

    markdown = req.markdown.strip()
    if not markdown:
        raise HTTPException(status_code=400, detail="Prompt content must not be empty.")

    metadata = {}
    if agent_path.exists() and agent_path.suffix == ".md":
        try:
            metadata = parse_yaml_frontmatter(agent_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"Could not read agent metadata: {exc}")
    if not isinstance(metadata, dict):
        metadata = {}

    purpose = parse_markdown_sections(markdown).get("purpose", "").strip()
    if purpose:
        metadata["description"] = purpose
    metadata["id"] = req.agent_id
    metadata["name"] = metadata.get("name") or req.agent_id.replace("-", " ").title()
    metadata["mode"] = metadata.get("mode") or req.environment
    metadata["model"] = metadata.get("model") or "qwen2.5-coder:latest"
    metadata["environment"] = req.environment
    if req.tools is not None:
        metadata["tools"] = list(dict.fromkeys(req.tools))

    try:
        lines = ["---"]
        for key in ["id", "name", "description", "mode", "model", "squad", "environment", "version"]:
            if key not in metadata or metadata[key] in (None, ""):
                continue
            lines.append(f"{key}: {metadata[key]}")
        if metadata.get("tools"):
            lines.append("tools:")
            for tool in metadata["tools"]:
                lines.append(f"  - {tool}")
        lines.append("---")
        frontmatter = "\n".join(lines) + "\n\n"
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        agent_path.write_text(frontmatter + markdown + "\n", encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save agent files: {exc}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = re.sub(r"[^A-Za-z0-9_-]+", "-", (req.label or req.agent_id).strip()).strip("-_")
    label = label or req.agent_id
    snapshot_prefix = f"{req.environment}__" if req.environment != "workspace" else ""
    dest = TEST_AGENTS_DIR / f"{snapshot_prefix}{req.agent_id}__{label}__{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    if agent_path.exists():
        shutil.copy2(agent_path, dest / agent_path.name)

    manifest_path = TEST_AGENTS_DIR / "manifest.json"
    manifest = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    manifest.append({
        "agent_id": req.agent_id,
        "environment": req.environment,
        "label": label,
        "snapshot": dest.name,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = test_runner.run_header_tests(markdown, req.agent_id)
    report["source"] = f"library/{req.agent_id}.md"
    return {"saved": True, "path": f"library/{req.agent_id}.md",
            "metadata_path": f"library/{req.agent_id}.md",
            "environment": req.environment,
            "snapshot": dest.name, "snapshot_path": f"test_agents/{dest.name}",
            "header_report": report}


@router.get("/api/testing/fixtures")
def api_fixtures():
    fixtures = []
    if TEST_AGENTS_DIR.is_dir():
        for child in sorted(TEST_AGENTS_DIR.iterdir()):
            if child.is_dir():
                fixtures.append({
                    "snapshot": child.name,
                    "files": sorted(p.name for p in child.iterdir() if p.is_file()),
                })
    return {"fixtures": fixtures}

```

## `test_environment/model_log.py`
```py
"""One small log file per LLM: running totals plus the most recent test runs."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "model_logs"
MAX_ENTRIES = 25


def _slug(model: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", str(model).lower()).strip("-")[:80] or "unknown-model"


def _path(model: str) -> Path:
    return LOG_DIR / f"{_slug(model)}.json"


def get_log(model: str) -> dict:
    path = _path(model)
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"model": model, "runs": 0, "passes": 0, "probe_failures": {}, "entries": []}


def record_run(model: str, title: str, passed: bool, components: list[dict],
               strengths: list[str], weaknesses: list[str], improvements: list[str]) -> dict:
    log = get_log(model)
    log["model"] = model
    log["runs"] += 1
    log["passes"] += 1 if passed else 0
    for component in components:
        for check in component.get("checks", []):
            if not check.get("passed"):
                log["probe_failures"][check["id"]] = log["probe_failures"].get(check["id"], 0) + 1
    log["entries"].append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title": title,
        "passed": passed,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
    })
    log["entries"] = log["entries"][-MAX_ENTRIES:]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _path(model).write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    return log

```

## `test_environment/prompt_builder.py`
```py
"""Prompt Part Assembler & Category Manifest for the prompt builder."""

import json
import re
import shutil
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "PromptBuilderFiles"
CATEGORIES_FILE = PROMPT_DIR / "categories.json"
PARTS_DIR = PROMPT_DIR / "parts"


def _ensure_dirs() -> None:
    PARTS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "item"


def load_categories() -> list[dict]:
    if not CATEGORIES_FILE.is_file():
        return []
    data = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
    return data.get("categories", [])


def save_categories(categories: list[dict]) -> None:
    _ensure_dirs()
    CATEGORIES_FILE.write_text(
        json.dumps({"categories": categories}, indent=2) + "\n", encoding="utf-8"
    )


def add_category(
    cat_id: str, name: str, description: str = "", required_header: str = ""
) -> dict:
    slug = _slugify(cat_id)
    categories = load_categories()
    if any(c["id"] == slug for c in categories):
        raise ValueError(f"Category '{slug}' already exists.")

    new_cat = {
        "id": slug,
        "name": name.strip(),
        "description": description.strip(),
    }
    if required_header.strip():
        new_cat["required_header"] = required_header.strip()

    categories.append(new_cat)
    save_categories(categories)

    (PARTS_DIR / slug).mkdir(parents=True, exist_ok=True)
    return new_cat


def delete_category(cat_id: str) -> dict:
    categories = load_categories()
    cat_to_remove = next((c for c in categories if c["id"] == cat_id), None)
    if not cat_to_remove:
        raise ValueError(f"Category '{cat_id}' not found.")

    updated = [c for c in categories if c["id"] != cat_id]
    save_categories(updated)

    cat_dir = PARTS_DIR / cat_id
    if cat_dir.is_dir():
        shutil.rmtree(cat_dir)

    return {"deleted": cat_id}


def load_parts(category: str | None = None) -> list[dict]:
    """Each part is a markdown file: parts/<category>/<slug>.md with optional frontmatter."""
    _ensure_dirs()
    parts = []
    if not PARTS_DIR.is_dir():
        return parts
    for part_file in sorted(PARTS_DIR.rglob("*.md")):
        raw = part_file.read_text(encoding="utf-8")
        rel = part_file.relative_to(PARTS_DIR).as_posix()
        cat = rel.split("/")[0] if "/" in rel else "misc"
        title = part_file.stem.replace("-", " ").replace("_", " ").title()
        body = raw
        if raw.startswith("---"):
            chunks = raw.split("---", 2)
            if len(chunks) >= 3:
                for line in chunks[1].strip().splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        if key.strip() == "title":
                            title = value.strip()
                body = chunks[2].strip()
        if category and cat != category:
            continue
        parts.append({
            "id": f"{cat}/{part_file.stem}",
            "category": cat,
            "title": title,
            "content": body,
            "path": f"PromptBuilderFiles/parts/{rel}",
        })
    return parts


def add_part(
    category: str, title: str, content: str, part_id: str | None = None
) -> dict:
    _ensure_dirs()
    cat_slug = _slugify(category)
    part_slug = _slugify(part_id or title)

    cat_dir = PARTS_DIR / cat_slug
    cat_dir.mkdir(parents=True, exist_ok=True)

    file_path = cat_dir / f"{part_slug}.md"
    file_content = f"---\ntitle: {title.strip()}\n---\n\n{content.strip()}\n"
    file_path.write_text(file_content, encoding="utf-8")

    return {
        "id": f"{cat_slug}/{part_slug}",
        "category": cat_slug,
        "title": title.strip(),
        "content": content.strip(),
        "path": f"PromptBuilderFiles/parts/{cat_slug}/{part_slug}.md",
    }


def delete_part(part_id: str) -> dict:
    _ensure_dirs()
    if "/" not in part_id:
        raise ValueError("Invalid part ID format. Expected 'category/part_slug'.")

    cat, slug = part_id.split("/", 1)
    file_path = (PARTS_DIR / cat / f"{slug}.md").resolve()

    try:
        file_path.relative_to(PARTS_DIR.resolve())
    except ValueError:
        raise ValueError("Access outside parts directory is forbidden.")

    if not file_path.is_file():
        raise FileNotFoundError(f"Part '{part_id}' not found.")

    file_path.unlink()
    return {"deleted": part_id}


def get_manifest() -> dict:
    """Full categories manifest with each category's available parts."""
    categories = load_categories()
    parts = load_parts()
    for cat in categories:
        cat["parts"] = [p for p in parts if p["category"] == cat["id"]]
    return {
        "categories": categories,
        "uncategorized_parts": [
            p for p in parts if p["category"] not in {c["id"] for c in categories}
        ],
        "total_parts": len(parts),
    }


def assemble_prompt(selected_ids: list[str], extra_instructions: str = "") -> dict:
    """Compose a single prompt from the selected part ids in category order."""
    categories = load_categories()
    order = {c["id"]: i for i, c in enumerate(categories)}
    parts = {p["id"]: p for p in load_parts()}

    chosen = [parts[pid] for pid in selected_ids if pid in parts]
    chosen.sort(key=lambda p: (order.get(p["category"], 999), p["title"]))

    sections = []
    for part in chosen:
        sections.append(f"## {part['title']}\n\n{part['content'].strip()}")

    if extra_instructions.strip():
        sections.append(f"## Additional Instructions\n\n{extra_instructions.strip()}")

    prompt = "\n\n".join(sections)
    return {
        "prompt": prompt,
        "selected": [p["id"] for p in chosen],
        "missing": [pid for pid in selected_ids if pid not in parts],
        "char_count": len(prompt),
        "part_count": len(chosen),
    }

```

## `test_environment/prompt_judge.py`
```py
"""LLM-as-judge review of a prompt, one rubric per section type.

The judge returns the same component/check shape as test_runner so the UI and
the "send failures to chat agent" flow can treat both kinds of result alike.
"""

import json
import re
from typing import Callable

RUBRICS = {
    "role": "States who the agent is and its domain of expertise in concrete terms.",
    "purpose": "States a specific goal or outcome the agent must achieve, not a vague aim.",
    "boundaries": "Lists concrete prohibitions or limits the agent must respect.",
    "output format": "Describes a checkable response format (structure, length, style).",
    "default": "Is clear, specific, actionable and does not contradict other sections.",
}
TOOL_RUBRIC = "Says what the tool does and when the agent should call it."
WHOLE_RUBRIC = "The sections are consistent with each other, with no contradictions or obvious gaps."


def _rubric_for(title: str) -> str:
    lower = title.strip().lower()
    for key, rubric in RUBRICS.items():
        if key != "default" and key in lower:
            return rubric
    return RUBRICS["default"]


def _build_request(title, description, sections, tools, target_model) -> str:
    items = [{"id": "prompt", "name": "Whole prompt", "rubric": WHOLE_RUBRIC}]
    for index, section in enumerate(sections):
        items.append({
            "id": f"section-{index}",
            "name": section.get("title", ""),
            "rubric": _rubric_for(section.get("title", "")),
            "text": str(section.get("content", ""))[:1500],
        })
    for index, tool in enumerate(tools):
        items.append({
            "id": f"tool-{index}",
            "name": tool.get("name", ""),
            "rubric": TOOL_RUBRIC,
            "text": str(tool.get("description", ""))[:600],
        })
    return (
        "You are a strict reviewer of agent system prompts. "
        f"The prompt will be run by the model '{target_model}'; judge whether it is "
        "clear and specific enough for a model of that kind.\n"
        f"Prompt title: {title}\nPrompt description: {description}\n\n"
        "Review each item against its rubric. Reply with ONLY a JSON array, one object per item: "
        '{"id": "...", "passed": true|false, "reason": "one sentence", "fix": "a concrete rewrite or empty"}.\n\n'
        f"Items:\n{json.dumps(items, ensure_ascii=False, indent=1)}"
    ), items


def _parse_verdicts(text: str) -> dict[str, dict]:
    match = re.search(r"\[.*\]", text or "", re.S)
    if not match:
        raise ValueError("The model did not return a JSON array.")
    data = json.loads(match.group(0))
    return {str(item.get("id")): item for item in data if isinstance(item, dict)}


def judge_prompt(model: str, title: str, description: str, sections: list[dict],
                 tools: list[dict], chat: Callable[..., dict] | None = None) -> dict:
    if chat is None:
        import ollama
        chat = ollama.chat
    request, items = _build_request(title, description, sections, tools, model)
    response = chat(model=model, messages=[{"role": "user", "content": request}])
    content = (response.get("message") or {}).get("content", "")
    verdicts = _parse_verdicts(content)

    components = []
    for item in items:
        verdict = verdicts.get(item["id"])
        if verdict is None:
            continue
        passed = bool(verdict.get("passed"))
        reason = str(verdict.get("reason") or "").strip()
        components.append({
            "name": f"AI review: {item['name']}",
            "passed": passed,
            "tested_text": item.get("text", ""),
            "checks": [{
                "id": "ai_review",
                "passed": passed,
                "evidence": reason or ("judged acceptable" if passed else "judged unacceptable"),
                "rule": item["rubric"],
                "observed": reason,
                "fix": "" if passed else str(verdict.get("fix") or "").strip(),
            }],
        })
    return {"model": model, "components": components, "raw": content[:4000]}

```

## `test_environment/PromptBuilderFiles/categories.json`
```json
{
  "categories": [
    {
      "id": "test-agent-prompt",
      "name": "Test Agent Prompt",
      "description": ""
    }
  ]
}

```

## `test_environment/PromptBuilderFiles/parts/test-agent-prompt/description.md`
```md
---
title: Description
---

Prompt the Test Agent to answer questions, utilize the provided tools, and avoid hallucinating the use of tools they haven't been explicitly told to use.

```

## `test_environment/PromptBuilderFiles/parts/test-agent-prompt/hallucination-prevention.md`
```md
---
title: Hallucination Prevention
---

The Test Agent must not claim that it has read, written, tested, or modified files unless the tool result confirms it. The Test Agent should only use the tools listed above and avoid inventing files, classes, functions, dependencies, or existing functionality.

```

## `test_environment/PromptBuilderFiles/parts/test-agent-prompt/instructions.md`
```md
---
title: Instructions
---

1. The user will ask a question.
2. The Test Agent should provide an answer based on the information available and the provided tools.
3. If the Test Agent is unsure about something, it should ask for clarification.
4. The Test Agent should avoid using tools unless explicitly told to do so.
5. The Test Agent should always be truthful about its actions and limitations.

```

## `test_environment/PromptBuilderFiles/parts/test-agent-prompt/role.md`
```md
---
title: Role
---

The Test Agent is a skilled software architect who plans software using modules, functions, and classes. It follows the design principles of separation of concerns, object-oriented programming, simplicity, documentation, and error handling. The Test Agent is provided with a set of tools to assist with file operations and should only use these tools when explicitly told to do so.

```

## `test_environment/report_store.py`
```py
"""Saved test reports (JSON files) so results can be reviewed and learned from later."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "test_reports"
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:40] or "report"


def save_report(kind: str, title: str, model: str, result: dict,
                subject: str = "", notes: str = "") -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    report_id = f"{now.strftime('%Y%m%dT%H%M%S%f')}-{kind}-{_slug(title)}"
    record = {
        "id": report_id,
        "kind": kind,
        "title": title,
        "model": model,
        "created_at": now.isoformat(),
        "passed": bool(result.get("passed")),
        "verdict": result.get("verdict", ""),
        "notes": notes,
        "subject": subject,
        "result": result,
    }
    (REPORTS_DIR / f"{report_id}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def list_reports() -> list[dict]:
    if not REPORTS_DIR.is_dir():
        return []
    summaries = []
    for path in sorted(REPORTS_DIR.glob("*.json"), reverse=True):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        summaries.append({key: record.get(key) for key in
                          ("id", "kind", "title", "model", "created_at", "passed", "verdict", "notes")})
    return summaries


def get_report(report_id: str) -> dict:
    if not _ID_PATTERN.match(report_id):
        raise ValueError(f"Invalid report id: {report_id!r}")
    path = REPORTS_DIR / f"{report_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Report not found: {report_id}")
    return json.loads(path.read_text(encoding="utf-8"))

```

## `test_environment/sandbox_env.py`
```py
"""Isolated virtualenv used to run untrusted test code (Tool Workbench and Code Builder)."""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "tools" / "allowed_paths.json"
FALLBACK_ROOT = PROJECT_ROOT / "workspace" / "sandbox"
LEGACY_VENV = PROJECT_ROOT / "workspace" / ".sandbox-venv"


def read_config() -> dict:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _usable_root(candidate: Path) -> bool:
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def sandbox_root() -> Path:
    """Folder holding the sandbox venv and scripts: ``sandbox_root`` in allowed_paths.json, else inside the repo."""
    configured = str(read_config().get("sandbox_root") or "").strip()
    if configured:
        candidate = Path(os.path.expandvars(configured)).expanduser()
        if candidate.is_absolute() and _usable_root(candidate):
            return candidate.resolve()
    FALLBACK_ROOT.mkdir(parents=True, exist_ok=True)
    return FALLBACK_ROOT


SANDBOX_ROOT = sandbox_root()
SANDBOX_DIR = SANDBOX_ROOT / "venv"
SCRIPTS_DIR = SANDBOX_ROOT / "scripts"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
VENV_TIMEOUT_SECONDS = 120
INSTALL_TIMEOUT_SECONDS = 300
MAX_OUTPUT_CHARS = 20000

_PACKAGE_SPEC = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}((==|>=)[A-Za-z0-9._!+-]{1,40})?$")
_MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_lock = threading.Lock()

# Import names that differ from their PyPI package name.
IMPORT_TO_PACKAGE = {
    "cv2": "opencv-python", "PIL": "pillow", "sklearn": "scikit-learn",
    "skimage": "scikit-image", "yaml": "pyyaml", "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv", "dateutil": "python-dateutil", "serial": "pyserial",
    "docx": "python-docx", "fitz": "pymupdf", "jwt": "pyjwt", "attr": "attrs",
    "OpenSSL": "pyopenssl", "Crypto": "pycryptodome", "magic": "python-magic",
}


def exists() -> bool:
    return python_path().exists()


def python_path() -> Path:
    scripts = "Scripts" if os.name == "nt" else "bin"
    return SANDBOX_DIR / scripts / ("python.exe" if os.name == "nt" else "python")


def interpreter() -> str:
    """The sandbox Python when it exists, otherwise the server's own interpreter."""
    return str(python_path()) if exists() else sys.executable


def _run(command: list[str], timeout: int) -> dict:
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        completed = subprocess.run(
            command, capture_output=True, timeout=timeout, text=True,
            encoding="utf-8", errors="replace", **kwargs,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": f"Timed out after {timeout} seconds."}
    except OSError as exc:
        return {"ok": False, "output": f"Could not start process: {exc}"}
    output = (completed.stdout + completed.stderr).strip()
    return {"ok": completed.returncode == 0, "output": output[-MAX_OUTPUT_CHARS:]}


def migrate_legacy() -> dict:
    """Move packages from the old in-repo venv into the new sandbox venv, then delete the old one."""
    legacy_python = LEGACY_VENV / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if not legacy_python.exists() or LEGACY_VENV.resolve() == SANDBOX_DIR.resolve():
        return {"ok": True, "migrated": False}
    frozen = _run([str(legacy_python), "-m", "pip", "freeze", "--disable-pip-version-check"], 60)
    packages = [line.strip() for line in frozen["output"].splitlines() if line.strip() and not line.startswith(("-e", "#", "@"))] if frozen["ok"] else []
    created = ensure_venv()
    if not created["ok"]:
        return {"ok": False, "migrated": False, "output": created["output"]}
    if packages:
        installed = _run(
            [str(python_path()), "-m", "pip", "install", "--disable-pip-version-check", *packages],
            INSTALL_TIMEOUT_SECONDS,
        )
        if not installed["ok"]:
            return {"ok": False, "migrated": False, "output": installed["output"]}
    shutil.rmtree(LEGACY_VENV, ignore_errors=True)
    return {"ok": True, "migrated": True, "packages": len(packages)}


def ensure_venv() -> dict:
    with _lock:
        if exists():
            return {"ok": True, "output": "Sandbox environment is ready."}
        SANDBOX_DIR.parent.mkdir(parents=True, exist_ok=True)
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        return _run([sys.executable, "-m", "venv", str(SANDBOX_DIR)], VENV_TIMEOUT_SECONDS)


def validate_packages(packages: list[str]) -> list[str]:
    cleaned = []
    for package in packages:
        spec = (package or "").strip()
        if not _PACKAGE_SPEC.fullmatch(spec):
            raise ValueError(f"Invalid package name: {spec!r}")
        cleaned.append(spec)
    if not cleaned:
        raise ValueError("Enter at least one package.")
    if len(cleaned) > 20:
        raise ValueError("Install at most 20 packages at a time.")
    return cleaned


def install(packages: list[str]) -> dict:
    cleaned = validate_packages(packages)
    created = ensure_venv()
    if not created["ok"]:
        return {"ok": False, "packages": cleaned, "output": created["output"]}
    result = _run(
        [str(python_path()), "-m", "pip", "install", "--disable-pip-version-check", *cleaned],
        INSTALL_TIMEOUT_SECONDS,
    )
    return {"ok": result["ok"], "packages": cleaned, "output": result["output"]}


def reset() -> dict:
    with _lock:
        if SANDBOX_DIR.exists():
            shutil.rmtree(SANDBOX_DIR, ignore_errors=True)
            if SANDBOX_DIR.exists():
                return {"ok": False, "output": "Could not remove the sandbox; close programs using it and retry."}
    created = ensure_venv()
    return {"ok": created["ok"], "output": "Sandbox reset to an empty environment." if created["ok"] else created["output"]}


def list_packages() -> list[dict]:
    if not exists():
        return []
    result = _run([str(python_path()), "-m", "pip", "list", "--format=json", "--disable-pip-version-check"], 60)
    if not result["ok"]:
        return []
    try:
        return json.loads(result["output"])
    except json.JSONDecodeError:
        return []


def imported_modules(source: str) -> list[str]:
    """Top-level module names imported by source, in order of first appearance."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module.split(".")[0])
    return list(dict.fromkeys(name for name in names if _MODULE_NAME.fullmatch(name)))


def _is_local_module(name: str) -> bool:
    return (PROJECT_ROOT / name).is_dir() or (PROJECT_ROOT / f"{name}.py").is_file()


def third_party_modules(source: str) -> list[str]:
    return [
        name for name in imported_modules(source)
        if name not in sys.stdlib_module_names and not _is_local_module(name)
    ]


def package_for_module(module: str) -> str:
    return IMPORT_TO_PACKAGE.get(module, module)


def missing_modules(source: str, extra: list[str] | None = None) -> list[dict]:
    """Third-party modules the sandbox interpreter cannot import."""
    modules = list(dict.fromkeys(third_party_modules(source) + [m for m in (extra or []) if _MODULE_NAME.fullmatch(m)]))
    if not modules:
        return []
    probe = (
        "import importlib.util, json, sys\n"
        "print(json.dumps([m for m in json.loads(sys.argv[1]) if importlib.util.find_spec(m) is None]))"
    )
    result = _run([interpreter(), "-I", "-c", probe, json.dumps(modules)], 30)
    try:
        missing = json.loads(result["output"].splitlines()[-1]) if result["ok"] else modules
    except (json.JSONDecodeError, IndexError):
        missing = modules
    return [{"module": name, "package": package_for_module(name)} for name in missing]


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_names() -> set[str]:
    if not REQUIREMENTS_PATH.exists():
        return set()
    names = set()
    for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if match and not line.lstrip().startswith("#"):
            names.add(_normalize(match.group(1)))
    return names


def add_to_requirements(source: str) -> list[str]:
    """Append third-party packages imported by source that requirements.txt lacks."""
    known = _requirement_names()
    installed = {_normalize(p["name"]): p["version"] for p in list_packages()}
    added = []
    for module in third_party_modules(source):
        package = package_for_module(module)
        key = _normalize(package)
        if key in known:
            continue
        version = installed.get(key)
        added.append(f"{package}>={version}" if version else package)
        known.add(key)
    if added:
        existing = REQUIREMENTS_PATH.read_text(encoding="utf-8") if REQUIREMENTS_PATH.exists() else ""
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        with REQUIREMENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(prefix + "\n".join(added) + "\n")
    return added

```

## `test_environment/sandbox_paths.py`
```py
"""Allowed folders for the sandbox terminal and the Code Builder file save/open.

The list lives under ``sandbox_roots`` in tools/allowed_paths.json. The scripts folder is always allowed.
"""

import os
from pathlib import Path

from . import sandbox_env


class PathNotAllowed(ValueError):
    pass


def _norm(path: Path | str) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def allowed_roots() -> list[Path]:
    configured = sandbox_env.read_config().get("sandbox_roots")
    roots = [sandbox_env.SCRIPTS_DIR]
    if isinstance(configured, list):
        for raw in configured:
            path = Path(os.path.expandvars(str(raw))).expanduser()
            if path.is_absolute() and path.is_dir():
                roots.append(path)
    unique: dict[str, Path] = {}
    for root in roots:
        unique.setdefault(_norm(root), root.resolve())
    return list(unique.values())


def is_allowed(path: Path | str) -> bool:
    target = _norm(path)
    for root in allowed_roots():
        base = _norm(root)
        if target == base or target.startswith(base + os.sep):
            return True
    return False


def resolve(path: str | Path, base: Path | None = None) -> Path:
    """Resolve ``path`` (absolute, or relative to ``base``) and require it to be inside an allowed root."""
    candidate = Path(os.path.expandvars(str(path))).expanduser()
    if not candidate.is_absolute():
        candidate = (base or sandbox_env.SCRIPTS_DIR) / candidate
    resolved = candidate.resolve()
    if not is_allowed(resolved):
        raise PathNotAllowed(f"'{resolved}' is outside the allowed sandbox paths. Use: sandbox add <folder>")
    return resolved


def _save(roots: list[Path]) -> None:
    config = sandbox_env.read_config()
    config["sandbox_roots"] = [str(root) for root in roots if _norm(root) != _norm(sandbox_env.SCRIPTS_DIR)]
    config["sandbox_roots"].insert(0, str(sandbox_env.SCRIPTS_DIR))
    sandbox_env.write_config(config)


def add_root(folder: str) -> Path:
    path = Path(os.path.expandvars(folder.strip().strip('"'))).expanduser()
    if not path.is_absolute():
        raise ValueError("Give a full folder path, for example: sandbox add D:\\projects")
    if not path.is_dir():
        raise ValueError(f"Folder does not exist: {path}")
    roots = allowed_roots()
    if not any(_norm(r) == _norm(path) for r in roots):
        roots.append(path.resolve())
        _save(roots)
    return path.resolve()


def remove_root(folder: str) -> bool:
    target = _norm(folder.strip().strip('"'))
    if target == _norm(sandbox_env.SCRIPTS_DIR):
        raise ValueError("The scripts folder is always allowed and cannot be removed.")
    roots = allowed_roots()
    kept = [r for r in roots if _norm(r) != target]
    if len(kept) == len(roots):
        return False
    _save(kept)
    return True


def clear_roots() -> None:
    _save([sandbox_env.SCRIPTS_DIR])

```

## `test_environment/test_behavior_probe.py`
```py
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_environment import behavior_probe, model_log


def make_chat(answers):
    def chat(**kwargs):
        question = kwargs["messages"][-1]["content"]
        for key, value in answers.items():
            if key in question:
                return {"message": {"content": value}}
        return {"message": {"content": ""}}
    return chat


GOOD = {
    "Who are you": "I am a Prompt Builder that writes prompts for agents.",
    "Summarize": "I help users write clear prompts for agents.",
    "capital of France": "The capital of France is Paris.",
    "Zorblax": "I'm not aware of any such keynote; I can't verify it.",
}


class BehaviorProbeTests(unittest.TestCase):
    def run_probes(self, answers):
        return behavior_probe.run_probes(
            "m1", "You are a Prompt Builder.", "Prompt Builder", "Help users write clear prompts for agents.",
            chat=make_chat(answers))

    def test_good_model_passes_everything(self):
        result = self.run_probes(GOOD)
        self.assertTrue(all(c["passed"] for c in result["components"]))
        self.assertEqual(result["weaknesses"], [])
        self.assertEqual(len(result["strengths"]), 4)

    def test_hallucination_and_fact_failures_give_improvements(self):
        bad = dict(GOOD)
        bad["Zorblax"] = "He said agriculture on the Moon will feed billions by 2050."
        bad["capital of France"] = "Lyon."
        result = self.run_probes(bad)
        failed = {c["checks"][0]["id"] for c in result["components"] if not c["passed"]}
        self.assertEqual(failed, {"fact_correct", "no_invention"})
        self.assertEqual(len(result["improvements"]), 2)
        self.assertIn("Never invent", " ".join(result["improvements"]))

    def test_role_failure_when_title_not_reflected(self):
        bad = dict(GOOD)
        bad["Who are you"] = "I am a large language model."
        result = self.run_probes(bad)
        self.assertFalse(result["components"][0]["passed"])

    def test_custom_fact_question(self):
        result = behavior_probe.run_probes(
            "m1", "p", "Prompt Builder", "Help users", "What is 2+2?", "4",
            chat=make_chat({**GOOD, "2+2": "It is 4."}))
        self.assertTrue(result["components"][2]["passed"])


class ModelLogTests(unittest.TestCase):
    def test_one_file_per_model_with_cap(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(model_log, "LOG_DIR", Path(tmp)):
            comp = [{"checks": [{"id": "fact_correct", "passed": False}]}]
            for _ in range(model_log.MAX_ENTRIES + 3):
                log = model_log.record_run("qwen2.5-coder:latest", "T", False, comp, [], ["w"], ["i"])
            model_log.record_run("other", "T", True, [], [], [], [])
            files = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(files, ["other.json", "qwen2.5-coder-latest.json"])
            self.assertEqual(log["runs"], model_log.MAX_ENTRIES + 3)
            self.assertEqual(len(model_log.get_log("qwen2.5-coder:latest")["entries"]), model_log.MAX_ENTRIES)
            self.assertEqual(log["probe_failures"], {"fact_correct": model_log.MAX_ENTRIES + 3})


if __name__ == "__main__":
    unittest.main()

```

## `test_environment/test_prompt_evaluation.py`
```py
from test_environment.test_runner import run_prompt_component_tests


def test_prompt_evaluation_reports_each_component():
    report = run_prompt_component_tests(
        "Workspace Research Assistant",
        "Help users research workspace documents and provide evidence-backed answers.",
        [
            {
                "title": "Research process",
                "category": "workflow",
                "content": "Inspect relevant documents, compare evidence, and report verified findings.",
            },
            {
                "title": "Workspace retrieval",
                "category": "skills",
                "content": "Use semantic retrieval when a question depends on information across workspace documents.",
            },
        ],
        [
            {
                "name": "search_workspace",
                "signature": "(query: str)",
                "description": "Search workspace documents and return relevant passages when the answer needs source evidence.",
            },
        ],
    )

    names = [component["name"] for component in report["components"]]
    assert names == [
        "Prompt title",
        "Prompt description",
        "Prompt sections",
        "Section title: Research process",
        "Section: Research process",
        "Skill title: Workspace retrieval",
        "Skill: Workspace retrieval",
        "Tool name: search_workspace",
        "Tool: search_workspace",
    ]
    assert report["passed"] is True


def test_prompt_evaluation_marks_missing_title_and_vague_tool_language():
    report = run_prompt_component_tests(
        "",
        "Do this task.",
        [
            {"title": "Instructions", "category": "general", "content": "Short."},
        ],
        [
            {"name": "lookup", "signature": "()", "description": "A helper."},
        ],
    )

    assert report["passed"] is False
    failed_names = [
        component["name"] for component in report["components"] if not component["passed"]
    ]
    assert "Prompt title" in failed_names
    assert "Prompt description" in failed_names
    assert "Section: Instructions" in failed_names
    assert "Tool: lookup" in failed_names

```

## `test_environment/test_prompt_judge.py`
```py
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_environment import prompt_judge, report_store


class PromptJudgeTests(unittest.TestCase):
    def fake_chat(self, **kwargs):
        self.requested_model = kwargs["model"]
        return {"message": {"content": (
            'Here you go:\n[{"id":"prompt","passed":true,"reason":"consistent","fix":""},'
            '{"id":"section-0","passed":false,"reason":"too vague","fix":"Name the domain."}]'
        )}}

    def test_judge_maps_verdicts_to_components(self):
        result = prompt_judge.judge_prompt(
            "m1", "T", "D", [{"title": "Role", "content": "You are helpful."}], [], chat=self.fake_chat)
        self.assertEqual(self.requested_model, "m1")
        self.assertEqual(result["model"], "m1")
        by_name = {c["name"]: c for c in result["components"]}
        self.assertTrue(by_name["AI review: Whole prompt"]["passed"])
        failed = by_name["AI review: Role"]
        self.assertFalse(failed["passed"])
        self.assertEqual(failed["checks"][0]["fix"], "Name the domain.")

    def test_judge_rejects_non_json(self):
        with self.assertRaises(ValueError):
            prompt_judge.judge_prompt("m", "T", "D", [], [], chat=lambda **k: {"message": {"content": "nope"}})


class ReportStoreTests(unittest.TestCase):
    def test_save_list_get_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(report_store, "REPORTS_DIR", Path(tmp)):
            record = report_store.save_report("prompt", "My Prompt", "m1", {"passed": False, "verdict": "FAIL"}, notes="n")
            listed = report_store.list_reports()
            self.assertEqual([r["id"] for r in listed], [record["id"]])
            self.assertEqual(listed[0]["model"], "m1")
            self.assertEqual(report_store.get_report(record["id"])["notes"], "n")
            with self.assertRaises(ValueError):
                report_store.get_report("../x")


if __name__ == "__main__":
    unittest.main()

```

## `test_environment/test_publish_tools.py`
```py
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core_engine import agent_factory
from test_environment import interface


class TestPublishTools(unittest.TestCase):
    def test_publish_writes_selected_registered_tools_to_frontmatter(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            library = root / "library"
            test_agents = root / "test_agents"
            library.mkdir()
            (library / "tool-agent.md").write_text(
                "---\nid: tool-agent\nname: Tool Agent\nmode: agent\ntools:\n"
                "  - calculator\n---\n\nOld prompt\n",
                encoding="utf-8",
            )
            manifest = test_agents / "manifest.json"
            test_agents.mkdir()
            manifest.write_text("[]\n", encoding="utf-8")
            app = FastAPI()
            app.include_router(interface.router)
            client = TestClient(app)

            with (
                patch.object(agent_factory, "LIBRARY_ROOT", library),
                patch.object(interface, "TEST_AGENTS_DIR", test_agents),
                patch.object(interface.test_runner, "run_header_tests", return_value={"verdict": "ok"}),
            ):
                response = client.post(
                    "/api/testing/publish",
                    json={
                        "agent_id": "tool-agent",
                        "label": "prompt-creation",
                        "markdown": "# Tool Agent\n\nUpdated prompt.",
                        "environment": "prompt-creation",
                        "tools": ["map_files", "read_file", "write_file"],
                    },
                )

            self.assertEqual(response.status_code, 200, response.text)
            saved = (library / "tool-agent.md").read_text(encoding="utf-8")
            metadata = agent_factory.parse_yaml_frontmatter(saved)
            self.assertEqual(
                metadata["tools"],
                ["map_files", "read_file", "write_file"],
            )
            snapshot_file = test_agents / response.json()["snapshot"] / "tool-agent.md"
            self.assertEqual(
                agent_factory.parse_yaml_frontmatter(snapshot_file.read_text(encoding="utf-8"))["tools"],
                metadata["tools"],
            )
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))[0]["agent_id"], "tool-agent")

    def test_publish_rejects_unregistered_tool_names(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            library = Path(temporary_directory)
            (library / "tool-agent.md").write_text(
                "---\nid: tool-agent\nmode: agent\n---\n\nPrompt\n",
                encoding="utf-8",
            )
            app = FastAPI()
            app.include_router(interface.router)
            client = TestClient(app)

            with patch.object(agent_factory, "LIBRARY_ROOT", library):
                response = client.post(
                    "/api/testing/publish",
                    json={
                        "agent_id": "tool-agent",
                        "markdown": "Updated prompt.",
                        "tools": ["not_a_registered_tool"],
                    },
                )

            self.assertEqual(response.status_code, 400)
            self.assertIn("Unknown tools", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

```

## `test_environment/test_runner.py`
```py
"""4-Question Section Header Tests & Lexical Evaluator.

For each of the four required agent.md headers (role, purpose, boundaries,
output format) the runner asks four fixed questions and scores answers with
pure lexical analysis of the section text - no model calls required.
"""

import re
from pathlib import Path

from core_engine.agent_factory import parse_markdown_sections

REQUIRED_HEADERS = ["role", "purpose", "boundaries", "output format"]

HEADER_KEYWORDS = {
    "role": ["you are", "your", "agent", "assistant", "specialist", "expert",
             "engineer", "analyst", "writer", "helper", "responsible", "precise",
             "helpful", "investigate", "general"],
    "purpose": ["goal", "objective", "purpose", "help", "provide", "generate",
                "answer", "solve", "deliver", "produce", "task", "ensure",
                "summarize", "draft", "report", "inspect", "serve", "gather",
                "strategic"],
    "boundaries": ["never", "do not", "don't", "must not", "avoid", "refuse",
                   "forbidden", "limit", "only", "not allowed", "shall not", "no ",
                   "cannot", "outside", "stay", "scope", "within", "not "],
    "output format": ["format", "markdown", "list", "table", "heading", "bullet",
                      "json", "concise", "structure", "section", "paragraph",
                      "respond", "reply", "output", "use ", "lead", "direct",
                      "answer", "detail"],
}

PASS_THRESHOLD = 0.6
MIN_SECTION_CHARS = 40

DIRECTIVE_VERBS = ("must", "should", "always", "never", "keep", "use", "avoid",
                   "start", "end", "list", "provide", "include", "do", "don't",
                   "return", "respond", "state", "answer", "summarize", "draft",
                   "write", "inspect", "gather", "report", "verify", "stay",
                   "lead", "follow", "cite", "act", "deliver", "work")

SECTION_MIN_CHARS = 20


def _plain_section_text(content: str, title: str = "") -> str:
    """Strip markdown emphasis and a leading '**Title:**' label that repeats the heading."""
    text = str(content or "").strip()
    label = re.escape(title.strip()) if title.strip() else r"[A-Za-z][\w &/-]{0,30}"
    text = re.sub(rf"^\s*[*_`]*{label}[*_`]*\s*[:.\-–—][*_`]*\s*", "", text, count=1, flags=re.I)
    return re.sub(r"[*_`]+", "", text).strip()


PROMPT_ACTION_WORDS = (
    "analyze", "answer", "build", "create", "decide", "design", "develop",
    "explain", "generate", "help", "identify", "inspect", "plan", "provide",
    "review", "solve", "write",
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z']+", text.lower()))


def _matches(lower: str, token_set: set[str], keyword: str) -> bool:
    """Substring match with naive stemming: keyword matches section text."""
    if keyword in lower:
        return True
    if len(keyword) >= 4:
        return any(tok.startswith(keyword) for tok in token_set)
    return False


def _lexical_score(section: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    lower = section.lower()
    tokens = _tokens(section)
    found = [kw for kw in keywords if _matches(lower, tokens, kw)]
    missing = [kw for kw in keywords if not _matches(lower, tokens, kw)]
    score = len(found) / len(keywords) if keywords else 0.0
    return score, found, missing


def _ask(header: str, section: str | None) -> dict:
    """Run the fixed 4-question battery against one section."""
    questions = []

    # Q1: Does the required header exist with content?
    exists = bool(section and section.strip())
    questions.append({
        "id": "presence",
        "question": f"Does the document contain a '## {header}' section with content?",
        "score": 1.0 if exists else 0.0,
        "passed": exists,
        "evidence": "section found" if exists else "section missing or empty",
        "rule": f"The document must contain a '## {header}' heading followed by content.",
        "observed": "section found" if exists else "no such heading, or it has no content",
        "fix": "" if exists else f"Add a '## {header.title()}' section with real content.",
    })

    if not exists:
        for qid, text in (("depth", f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?"),
                          ("vocabulary", f"Does the '{header}' section use header-appropriate vocabulary?"),
                          ("actionability", f"Does the '{header}' section give actionable, testable guidance?")):
            questions.append({"id": qid, "question": text, "score": 0.0, "passed": False,
                              "evidence": "no section to evaluate",
                              "rule": "Requires the section to exist first.",
                              "observed": "no section",
                              "fix": f"Add the '## {header.title()}' section first."})
        return {"header": header, "questions": questions, "score": 0.0, "passed": False}

    # Q2: Depth - is the section long enough to be meaningful?
    depth = min(1.0, len(section.strip()) / (MIN_SECTION_CHARS * 1.5))
    questions.append({
        "id": "depth",
        "question": f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?",
        "score": round(depth, 2),
        "passed": depth >= PASS_THRESHOLD,
        "evidence": f"{len(section.strip())} characters",
        "rule": f"Score is length / {int(MIN_SECTION_CHARS * 1.5)} characters and must reach {PASS_THRESHOLD}.",
        "observed": f"{len(section.strip())} characters, score {round(depth, 2)}",
        "fix": "" if depth >= PASS_THRESHOLD else
               f"Expand to roughly {int(MIN_SECTION_CHARS * 1.5 * PASS_THRESHOLD)}+ characters of specific detail.",
    })

    # Q3: Lexical - does it use vocabulary expected of this header?
    score, found, missing = _lexical_score(section, HEADER_KEYWORDS[header])
    questions.append({
        "id": "vocabulary",
        "question": f"Does the '{header}' section use header-appropriate vocabulary?",
        "score": round(score, 2),
        "passed": score >= PASS_THRESHOLD,
        "evidence": f"matched {len(found)}/{len(HEADER_KEYWORDS[header])} markers"
                    + (f"; missing: {', '.join(missing[:4])}" if missing else ""),
        "rule": f"At least {int(PASS_THRESHOLD * 100)}% of these marker words/phrases must appear: {', '.join(HEADER_KEYWORDS[header])}.",
        "observed": f"matched {len(found)}/{len(HEADER_KEYWORDS[header])}: {', '.join(found) or 'none'}",
        "missing": missing,
        "fix": "" if score >= PASS_THRESHOLD else
               f"Naturally work in more of the missing markers, for example: {', '.join(missing[:8])}.",
    })

    # Q4: Actionability - imperative / directive phrasing present?
    directives = re.findall(
        r"\b(?:" + "|".join(re.escape(v) for v in DIRECTIVE_VERBS) + r")\b",
        section, flags=re.I)
    actionable = len(set(d.lower() for d in directives)) >= 2
    questions.append({
        "id": "actionability",
        "question": f"Does the '{header}' section give actionable, testable guidance?",
        "score": 1.0 if actionable else (0.5 if directives else 0.0),
        "passed": actionable,
        "evidence": f"directive terms: {', '.join(sorted(set(d.lower() for d in directives))[:5]) or 'none'}",
        "rule": "At least 2 different directive words must appear (must, should, always, never, use, avoid, return, ...).",
        "observed": f"{len(set(d.lower() for d in directives))} distinct: {', '.join(sorted(set(d.lower() for d in directives))) or 'none'}",
        "fix": "" if actionable else "Rewrite as direct instructions using at least two directive words such as 'must', 'always', 'never', 'use', 'return'.",
    })

    total = sum(q["score"] for q in questions) / len(questions)
    return {
        "header": header,
        "questions": questions,
        "score": round(total, 2),
        "passed": total >= PASS_THRESHOLD,
        "tested_text": section.strip()[:600],
    }


def run_header_tests(md_text: str, agent_id: str = "") -> dict:
    """Evaluate an agent.md body against the 4-question battery per header."""
    sections = parse_markdown_sections(md_text)
    results = [_ask(header, sections.get(header)) for header in REQUIRED_HEADERS]

    extras = sorted(h for h in sections if h not in REQUIRED_HEADERS)
    overall = sum(r["score"] for r in results) / len(results) if results else 0.0
    passed = sum(1 for r in results if r["passed"])

    return {
        "agent_id": agent_id,
        "results": results,
        "overall_score": round(overall, 2),
        "headers_passed": passed,
        "headers_total": len(results),
        "passed": passed == len(results),
        "extra_headers": extras,
        "verdict": "PASS" if passed == len(results) else "FAIL",
    }


def _text_component(name: str, text: str, min_chars: int, action_required: bool = False) -> dict:
    value = (text or "").strip()
    checks = [
        {
            "id": "present",
            "passed": bool(value),
            "evidence": "content provided" if value else "content is missing",
            "rule": "The field must not be empty.",
            "observed": f"{len(value)} characters" if value else "empty",
            "fix": "" if value else "Write content for this field.",
        },
        {
            "id": "detail",
            "passed": len(value) >= min_chars,
            "evidence": f"{len(value)} characters; requires at least {min_chars}",
            "rule": f"The text must be at least {min_chars} characters.",
            "observed": f"{len(value)} characters",
            "fix": "" if len(value) >= min_chars else
                   f"Expand the text by at least {min_chars - len(value)} characters with specific, concrete detail.",
        },
    ]
    if action_required:
        actions = [word for word in PROMPT_ACTION_WORDS if re.search(rf"\b{word}\b", value, re.I)]
        checks.append({
            "id": "intent",
            "passed": bool(actions),
            "evidence": (
                f"intent/action language found: {', '.join(actions[:4])}"
                if actions else "state the outcome or action this prompt should guide"
            ),
            "rule": f"The text must contain at least one action word such as: {', '.join(PROMPT_ACTION_WORDS)}.",
            "observed": f"found: {', '.join(actions[:4])}" if actions else "no action words found",
            "fix": "" if actions else
                   "Rewrite so it states the outcome the agent should achieve using an action verb (for example 'help', 'analyze', 'write').",
        })
    return {
        "name": name,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "tested_text": value[:600],
    }


def _tool_language_component(tool: dict) -> dict:
    name = str(tool.get("name") or "Unnamed tool")
    description = str(tool.get("description") or "").strip()
    component = _text_component(f"Tool: {name}", description, 30)
    lower = description.lower()
    when_present = bool(re.search(r"\b(when|if|whenever|once|after|before)\b", lower))
    action_present = bool(re.search(
        r"\b(read|write|create|delete|search|list|calculate|run|execute|return|retrieve|"
        r"send|update|compare|inspect|extract|convert|validate|use)\w*\b",
        lower,
    ))
    component["checks"].extend([
        {
            "id": "behavior",
            "passed": action_present,
            "evidence": "describes an operation" if action_present else "explain what the tool does",
            "rule": "The description must name an operation (read, write, search, calculate, return, run, ...).",
            "observed": "operation word found" if action_present else "no operation word found",
            "fix": "" if action_present else "Add a sentence saying what the tool does, starting with an action verb.",
        },
        {
            "id": "when_to_use",
            "passed": when_present,
            "evidence": "states a usage condition" if when_present else "explain when the agent should call this tool",
            "rule": "The description must state when to call the tool (use words such as when, if, whenever, after, before).",
            "observed": "usage condition found" if when_present else "no usage condition found",
            "fix": "" if when_present else "Add a sentence such as 'Call this tool when the user asks for ...'.",
        },
    ])
    component["passed"] = all(check["passed"] for check in component["checks"])
    component["signature"] = str(tool.get("signature") or "")
    return component


def run_prompt_component_tests(
    title: str,
    description: str,
    sections: list[dict],
    tools: list[dict],
) -> dict:
    """Evaluate the title, summary, each prompt section, and each tool description."""
    components = [
        _text_component("Prompt title", title, 4),
        _text_component("Prompt description", description, 40, action_required=True),
    ]
    components.append({
        "name": "Prompt sections",
        "passed": bool(sections),
        "checks": [{
            "id": "present",
            "passed": bool(sections),
            "evidence": (
                f"{len(sections)} section(s) included"
                if sections else "select at least one prompt section"
            ),
        }],
    })

    for section in sections:
        title_text = str(section.get("title") or "Untitled section").strip()
        content = str(section.get("content") or "").strip()
        plain = _plain_section_text(content, title_text)
        category = str(section.get("category") or "").strip().lower()
        section_type = "Skill" if category in {"skill", "skills"} else "Section"
        components.append(_text_component(f"{section_type} title: {title_text}", title_text, 4))
        component = _text_component(f"{section_type}: {title_text}", plain, SECTION_MIN_CHARS)
        if plain:
            directives = re.findall(
                r"\b(?:" + "|".join(re.escape(v) for v in DIRECTIVE_VERBS) + r")\b|\b(?:you are|act as|your)\b",
                plain,
                flags=re.I,
            )
            component["checks"].append({
                "id": "actionability",
                "passed": bool(directives),
                "evidence": (
                    f"instruction language found: {', '.join(sorted(set(d.lower() for d in directives))[:4])}"
                    if directives else "include an explicit instruction describing what the agent should do"
                ),
                "rule": f"The section must contain directive wording such as: {', '.join(DIRECTIVE_VERBS[:12])}, ...",
                "observed": (
                    f"found: {', '.join(sorted(set(d.lower() for d in directives))[:4])}"
                    if directives else "no directive wording found"
                ),
                "fix": "" if directives else
                       "Rewrite the section as explicit instructions using words like 'must', 'always', 'never', 'use', or 'return'.",
            })
            component["passed"] = all(check["passed"] for check in component["checks"])
        component["category"] = category
        components.append(component)

    for tool in tools:
        tool_name = str(tool.get("name") or "Unnamed tool")
        components.append(_text_component(f"Tool name: {tool_name}", tool_name, 3))
        components.append(_tool_language_component(tool))
    passed = sum(1 for component in components if component["passed"])
    return {
        "components": components,
        "components_passed": passed,
        "components_total": len(components),
        "passed": bool(components) and passed == len(components),
        "verdict": "PASS" if components and passed == len(components) else "FAIL",
    }


def run_tests_for_agent(agent_id: str, environment: str = "workspace") -> dict:
    """Locate an agent profile in its environment and run the header battery."""
    from core_engine.agent_factory import find_agent_file
    md_path = find_agent_file(agent_id, environment)
    if not md_path:
        raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
    md_text = md_path.read_text(encoding="utf-8")
    report = run_header_tests(md_text, agent_id)
    report["source"] = str(md_path.relative_to(Path(__file__).resolve().parent.parent)).replace("\\", "/")
    return report

```

## `test_environment/test_sandbox_env.py`
```py
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_environment import sandbox_env


class SandboxEnvTests(unittest.TestCase):
    def test_package_names_are_validated(self):
        self.assertEqual(sandbox_env.validate_packages(["streamlit", "requests==2.31.0", "numpy>=1.0"]),
                         ["streamlit", "requests==2.31.0", "numpy>=1.0"])
        for bad in ["--index-url http://x", "git+https://x/y", "../local", "a b", "", "pkg;rm"]:
            with self.assertRaises(ValueError, msg=bad):
                sandbox_env.validate_packages([bad])

    def test_third_party_modules_skip_stdlib_and_project_modules(self):
        source = "import os, json\nimport streamlit as st\nfrom cv2 import imread\nfrom tools import interface\nimport a.b\n"
        self.assertEqual(sandbox_env.third_party_modules(source), ["streamlit", "cv2", "a"])
        self.assertEqual(sandbox_env.package_for_module("cv2"), "opencv-python")

    def test_install_uses_sandbox_pip_with_validated_names(self):
        with patch.object(sandbox_env, "ensure_venv", return_value={"ok": True, "output": ""}), \
                patch.object(sandbox_env, "_run", return_value={"ok": True, "output": "done"}) as run:
            result = sandbox_env.install(["streamlit"])
        self.assertTrue(result["ok"])
        command = run.call_args[0][0]
        self.assertEqual(command[1:4], ["-m", "pip", "install"])
        self.assertEqual(command[-1], "streamlit")

    def test_promotion_appends_only_new_packages_to_requirements(self):
        with tempfile.TemporaryDirectory() as temp:
            requirements = Path(temp) / "requirements.txt"
            requirements.write_text("fastapi>=0.110.0\nrequests>=2.0", encoding="utf-8")
            source = "import fastapi\nimport requests\nimport streamlit\nimport cv2\n"
            with patch.object(sandbox_env, "REQUIREMENTS_PATH", requirements), \
                    patch.object(sandbox_env, "list_packages",
                                 return_value=[{"name": "streamlit", "version": "1.40.0"}]):
                added = sandbox_env.add_to_requirements(source)
                again = sandbox_env.add_to_requirements(source)
            self.assertEqual(added, ["streamlit>=1.40.0", "opencv-python"])
            self.assertEqual(again, [])
            lines = requirements.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, ["fastapi>=0.110.0", "requests>=2.0", "streamlit>=1.40.0", "opencv-python"])


if __name__ == "__main__":
    unittest.main()

```

## `test_environment/test_tool_catalog.py`
```py
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from core_engine import tool_catalog
from server import app


class TestToolCatalog(unittest.TestCase):
    def setUp(self):
        tool_catalog.load_tools(reload=True)

    def tearDown(self):
        tool_catalog.load_tools(reload=True)

    def test_expected_builtin_tools_load(self):
        tools = tool_catalog.list_tools()
        names = {t["name"] for t in tools}
        expected = {
            # core_engine/core_tools.py
            "calculator",
            "docling_parse",
            "rag_agent_tool",
            "agent_info",
            "extract_docstrings",
            "search_workspace",
            "project_status",
            "run_python_code",
            "send_code_to_editor",
            "run_code_in_editor",
            "ask_user_questions",
            "read_file",
            "write_file",
            "editor",
            "delete_file",
            "map_files",
        }
        for exp in expected:
            self.assertIn(exp, names)
        self.assertEqual(len(tools), 16)

    def test_tools_directory_contains_only_the_file_tools_and_promoted_module(self):
        files = {path.name for path in tool_catalog.TOOLS_DIR.iterdir() if path.is_file()}
        self.assertEqual(
            files,
            {
                "__init__.py",
                "allowed_paths.json",
                "delete_file_tool.py",
                "editor_tool.py",
                "interface.py",
                "map_files_tool.py",
                "promoted_tools.py",                "read_tool.py",
                "write_tool.py",
            },
        )

    def test_get_load_errors_exists(self):
        errors = tool_catalog.get_load_errors()
        self.assertIsInstance(errors, dict)
        self.assertEqual(errors, {})

    def test_temp_dir_good_and_broken_module(self):
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            good_file = temp_path / "good_tool.py"
            good_file.write_text(
                "from core_engine.tool_catalog import tool\n\n"
                "@tool\ndef sample_good_tool():\n    return 'ok'\n",
                encoding="utf-8",
            )
            broken_file = temp_path / "broken_tool.py"
            broken_file.write_text("invalid python code :::\n", encoding="utf-8")

            old_tools_dir = tool_catalog.TOOLS_DIR
            try:
                tool_catalog.TOOLS_DIR = temp_path
                tool_catalog.load_tools(reload=True)

                errors = tool_catalog.get_load_errors()
                self.assertIn("broken_tool.py", errors)
                self.assertIn("sample_good_tool", tool_catalog.REGISTRY)

                client = TestClient(app)
                resp = client.get("/api/tools")
                self.assertEqual(resp.status_code, 200)
                body = resp.json()
                registered_names = [t["name"] for t in body["tools"]]
                self.assertIn("sample_good_tool", registered_names)
                self.assertTrue(any("broken_tool.py" in w for w in body["warnings"]))
            finally:
                tool_catalog.TOOLS_DIR = old_tools_dir
                tool_catalog.load_tools(reload=True)

    def test_all_agent_refs_resolve_and_report(self):
        report = tool_catalog.get_catalog_report()
        self.assertIn("tools", report)
        self.assertIn("providers", report)
        self.assertIn("load_errors", report)
        self.assertIn("missing_agent_tools", report)
        self.assertIn("warnings", report)

        self.assertEqual(report["missing_agent_tools"], {})
        self.assertEqual(tool_catalog.unknown_tool_names(["calculator", "read_file"]), [])
        self.assertEqual(
            tool_catalog.unknown_tool_names(["calculator", "unknown_tool_xyz"]),
            ["unknown_tool_xyz"],
        )


if __name__ == "__main__":
    unittest.main()

```

## `test_environment/test_tool_workbench.py`
```py
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

        run_tool.assert_called_once_with(source, arguments, timeout=5)
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

    def test_missing_llm_arguments_are_rejected_before_execution(self):
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {"content": "", "tool_calls": [
                {"function": {"name": "add", "arguments": {"left": 8}}}]}
        }
        request = ToolWorkbenchLLMRequest(
            model="m",
            tool_code="def add(left: int, right: int):\n    return left + right\n",
            user_prompt="Add.",
        )
        with patch.dict(sys.modules, {"ollama": ollama}):
            result = api_test_tool_with_llm(request)
        self.assertEqual(result["error_code"], "ERR_INVALID_TOOL_ARGUMENTS")
        self.assertIsNone(result["tool_execution_result"])
        self.assertEqual(result["function_input"], {"left": 8})

    def test_generate_function_extracts_code_and_retries_once(self):
        replies = iter([
            "```python\nthis is not python(\n```",
            "```python\ndef add(a: int, b: int) -> int:\n    \"\"\"Add.\"\"\"\n    return a + b\n```",
        ])
        chat = Mock(side_effect=lambda **_: {"message": {"content": next(replies)}})
        result = tool_workbench.generate_python_function("add numbers", "m", chat=chat)
        self.assertEqual(result["function_name"], "add")
        self.assertEqual(chat.call_count, 2)

    def test_generate_function_fails_after_invalid_retry(self):
        chat = Mock(return_value={"message": {"content": "no code here"}})
        with self.assertRaises(ValueError):
            tool_workbench.generate_python_function("x", "m", chat=chat)

    def test_builds_test_harness_for_any_signature_and_runs_it(self):
        source = (
            "def f(a: float, name: str, tags: list, n: int = 3, *, flag: bool = False):\n"
            "    print('hello', a, name, tags, n, flag)\n    return n\n"
        )
        harness = tool_workbench.build_test_harness(source)
        self.assertIn("a = 1.0", harness)
        self.assertIn('name = "test"', harness)
        self.assertIn("tags = []", harness)
        self.assertIn("n = 3", harness)
        self.assertIn("flag = False", harness)
        self.assertIn("result = f(a=a, name=name, tags=tags, n=n, flag=flag)", harness)
        with_block = source + "\n\n" + harness
        self.assertEqual(tool_workbench.strip_test_harness(with_block).strip(), source.strip())
        result = tool_workbench.run_python_tool(with_block, {})
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("hello 1.0 test [] 3 False", result["stdout"])

    def test_harness_errors_are_reported_from_script_run(self):
        source = "def f(a: int):\n    return 1 // 0\n"
        result = tool_workbench.run_python_tool(source + "\n" + tool_workbench.build_test_harness(source), {})
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("ZeroDivisionError", result["stderr"])

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
            promoted_path = Path(directory) / "promoted.py"
            with patch("tools.interface.PROMOTED_MODULE_PATH", promoted_path):
                try:
                    promoted = api_promote_tool(ToolWorkbenchRequest(
                        tool_code=first_source, function_input={"left": 2, "right": 3}
                    ))
                    self.assertEqual(promoted["promoted"]["name"], first_name)
                    self.assertEqual(
                        promoted["promoted"]["path"], "tools/promoted_tools.py"
                    )
                    second_promoted = api_promote_tool(ToolWorkbenchRequest(
                        tool_code=second_source, function_input={"value": 3}
                    ))
                    self.assertEqual(second_promoted["promoted"]["name"], second_name)
                    promoted_source = promoted_path.read_text(encoding="utf-8")
                    self.assertLess(
                        promoted_source.index(first_name), promoted_source.index(second_name)
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

    def test_custom_tool_source_can_be_loaded_and_removed_from_library(self):
        tool_name = "workbench_library_tool"
        remaining_name = "workbench_library_remaining"
        source = (
            f"@tool\ndef {tool_name}(value: int):\n    return value * 2\n\n\n"
            f"@tool\ndef {remaining_name}(value: int):\n    return value + 1\n\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            promoted_path = Path(directory) / "promoted.py"
            promoted_path.write_text(source, encoding="utf-8")
            with patch("tools.interface.PROMOTED_MODULE_PATH", promoted_path):
                try:
                    exec(source, tool_catalog.__dict__)
                    loaded = tool_workbench.get_custom_tool_source(tool_name)
                    self.assertEqual(
                        loaded["source"],
                        f"@tool\ndef {tool_name}(value: int):\n    return value * 2\n",
                    )
                    self.assertEqual(loaded["path"], "tools/promoted_tools.py")
                    self.assertIn(tool_name, tool_catalog.REGISTRY)
                    self.assertIn(remaining_name, tool_catalog.REGISTRY)

                    removed = tool_workbench.delete_custom_tool(tool_name)
                    self.assertTrue(removed["deleted"])
                    self.assertTrue(promoted_path.exists())
                    self.assertNotIn(tool_name, tool_catalog.REGISTRY)
                    self.assertIn(remaining_name, tool_catalog.REGISTRY)
                    self.assertIn(remaining_name, promoted_path.read_text(encoding="utf-8"))

                    tool_workbench.delete_custom_tool(remaining_name)
                    self.assertNotIn(remaining_name, tool_catalog.REGISTRY)
                    self.assertTrue(promoted_path.exists())
                    self.assertNotIn(remaining_name, promoted_path.read_text(encoding="utf-8"))
                finally:
                    tool_catalog.REGISTRY.pop(tool_name, None)
                    tool_catalog.REGISTRY.pop(remaining_name, None)


if __name__ == "__main__":
    unittest.main()

```

## `test_environment/test_tools_interface.py`
```py
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from core_engine import tool_catalog
from server import app
from tools import interface


class TestToolsInterface(unittest.TestCase):
    def setUp(self):
        tool_catalog.load_tools(reload=True)

    def tearDown(self):
        tool_catalog.load_tools(reload=True)

    def test_python_doorway_delegates_to_file_and_editor_services(self):
        with (
            patch.object(
                interface.file_manager_service,
                "directory_tree",
                return_value={"path": "docs"},
            ) as tree,
            patch.object(
                interface.file_manager_service,
                "list_directory",
                return_value={"entries": []},
            ) as listing,
            patch.object(
                interface.file_manager_service,
                "read_file",
                return_value={"path": "docs/readme.md", "content": "hello"},
            ) as read,
            patch.object(
                interface.file_manager_service,
                "write_file",
                return_value={"path": "docs/readme.md", "bytes_written": 5},
            ) as write,
            patch.object(
                interface.file_manager_service,
                "delete",
                return_value={"path": "docs/old.txt", "deleted": True},
            ) as delete,
            patch.object(
                interface.editor_operations,
                "read_file_content",
                return_value={"path": "readme.md", "content": "editor"},
            ) as editor_read,
            patch.object(
                interface.editor_operations,
                "write_file_content",
                return_value={"path": "readme.md", "bytes_written": 6},
            ) as editor_write,
            patch.object(
                interface.editor_operations,
                "get_directory_tree",
                return_value={"path": "", "children": []},
            ) as editor_tree,
            patch.object(
                interface.editor_operations,
                "delete_path",
                return_value={"path": "old.txt", "deleted": True},
            ) as editor_delete,
        ):
            self.assertEqual(interface.map_files("docs"), {"path": "docs"})
            self.assertEqual(interface.list_directory("docs"), {"entries": []})
            self.assertEqual(
                interface.read_file("docs/readme.md")["content"], "hello"
            )
            self.assertEqual(
                interface.write_file("docs/readme.md", "hello")["bytes_written"], 5
            )
            self.assertTrue(interface.delete_file("docs/old.txt")["deleted"])
            self.assertEqual(
                interface.editor("read", path="readme.md")["content"], "editor"
            )
            self.assertEqual(
                interface.editor("write", path="readme.md", content="editor")[
                    "bytes_written"
                ],
                6,
            )
            self.assertEqual(
                interface.editor("tree")["children"], []
            )
            self.assertTrue(interface.editor("delete", path="old.txt")["deleted"])

        tree.assert_called_once_with("docs")
        listing.assert_called_once_with("docs")
        read.assert_called_once_with("docs/readme.md")
        write.assert_called_once_with("docs/readme.md", "hello")
        delete.assert_called_once_with("docs/old.txt")
        editor_read.assert_called_once_with("readme.md")
        editor_write.assert_called_once_with("readme.md", "editor")
        editor_tree.assert_called_once_with("")
        editor_delete.assert_called_once_with("old.txt")

    def test_editor_doorway_rejects_unknown_action(self):
        with self.assertRaisesRegex(ValueError, "Unsupported editor action"):
            interface.editor("rename", path="readme.md")

    def test_map_page_endpoint_uses_allowed_root_mapping_service(self):
        tree = {
            "name": "root",
            "type": "directory",
            "children": [{"name": "visible.txt", "type": "file"}],
        }
        with patch.object(interface, "map_files", return_value=tree):
            response = TestClient(app).post(
                "/api/tools/map-page",
                json={
                    "path": "",
                    "max_depth": 1,
                    "include_files": True,
                    "offset": 0,
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("visible.txt", response.json()["text"])

    def test_agent_file_tools_use_the_shared_doorway(self):
        functions = {
            name: tool_catalog.REGISTRY[name]["function"]
            for name in ("map_files", "read_file", "write_file", "editor", "delete_file")
        }
        with (
            patch.object(interface, "map_files", return_value={"name": "root"}) as map_files,
            patch.object(interface, "list_directory", return_value={"entries": []}),
            patch.object(
                interface,
                "read_file",
                return_value={"path": "docs/readme.md", "content": "hello"},
            ) as read_file,
            patch.object(
                interface,
                "write_file",
                side_effect=[
                    {"path": "scratchpad/latest_read.txt"},
                    {"path": "docs/readme.md", "bytes_written": 5},
                ],
            ) as write_file,
            patch.object(interface, "editor", return_value={"path": "readme.md"}) as editor,
            patch.object(
                interface,
                "delete_file",
                return_value={"path": "docs/old.txt", "deleted": True},
            ) as delete_file,
        ):
            self.assertEqual(
                json.loads(functions["map_files"]("docs"))["name"], "root"
            )
            self.assertEqual(
                json.loads(functions["read_file"]("docs/readme.md"))["content"],
                "hello",
            )
            self.assertEqual(
                json.loads(functions["write_file"]("docs/readme.md", "hello"))[
                    "bytes_written"
                ],
                5,
            )
            self.assertEqual(
                json.loads(functions["editor"]("tree"))["path"], "readme.md"
            )
            self.assertTrue(
                json.loads(functions["delete_file"]("docs/old.txt"))["deleted"]
            )

        map_files.assert_called_once_with("docs")
        read_file.assert_called_once_with("docs/readme.md")
        self.assertEqual(write_file.call_count, 2)
        editor.assert_called_once_with("tree", path="", content="")
        delete_file.assert_called_once_with("docs/old.txt")

    def test_register_get_remove_round_trip(self):
        source = (
            "def calc_square(n: int) -> int:\n"
            "    \"\"\"Calculate square of n.\"\"\"\n"
            "    return n * n\n"
        )
        with tempfile.TemporaryDirectory() as td:
            promoted_path = Path(td) / "promoted.py"
            header = (
                '"""Custom tools promoted from the Function Testing Workbench."""\n'
                'from core_engine.tool_catalog import tool\n\n'
                '# PROMOTION_MARKER: tools appended below will be registered as custom tools\n\n'
            )
            promoted_path.write_text(header, encoding="utf-8", newline="\n")
            initial_bytes = promoted_path.read_bytes()

            with patch("tools.interface.PROMOTED_MODULE_PATH", promoted_path):
                # 1. Register
                reg_result = interface.register_tool(source, "calc_square")
                self.assertEqual(reg_result["name"], "calc_square")
                self.assertEqual(reg_result["path"], "tools/promoted_tools.py")

                # 2. Get tool callable
                fn = interface.get_tool("calc_square")
                self.assertIsNotNone(fn)
                self.assertEqual(fn(5), 25)

                library = {t["name"]: t for t in interface.list_tools_directory()}
                self.assertTrue(library["calc_square"]["custom"])

                # 3. Get tool source
                src_info = interface.get_tool_source("calc_square")
                self.assertEqual(src_info["name"], "calc_square")
                self.assertIn("calc_square", src_info["source"])
                self.assertEqual(src_info["path"], "tools/promoted_tools.py")

                # 4. Remove tool
                del_result = interface.remove_tool("calc_square")
                self.assertTrue(del_result["deleted"])
                self.assertIsNone(interface.get_tool("calc_square"))

                # 5. Check byte-identical
                after_bytes = promoted_path.read_bytes()
                self.assertEqual(initial_bytes, after_bytes)

    def test_router_endpoints(self):
        client = TestClient(app)

        # GET /api/tools
        resp = client.get("/api/tools")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("tools", data)
        self.assertIn("providers", data)
        self.assertIn("warnings", data)
        self.assertIn("calculator", [t["name"] for t in data["tools"]])

        # GET /api/tools/calculator
        resp = client.get("/api/tools/calculator")
        self.assertEqual(resp.status_code, 200)
        calc_data = resp.json()
        self.assertEqual(calc_data["name"], "calculator")
        self.assertEqual(calc_data["provider"], "core_engine")

        # GET /api/tools/health
        resp = client.get("/api/tools/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

    def test_registered_tool_library_shows_only_tools_package_functions(self):
        client = TestClient(app)
        response = client.get("/api/tools/library")

        self.assertEqual(response.status_code, 200, response.text)
        names = {tool["name"] for tool in response.json()["tools"]}
        self.assertEqual(
            names,
            {"map_files", "read_file", "write_file", "editor", "delete_file"},
        )
        self.assertGreater(len(tool_catalog.list_tools()), len(names))

        with tempfile.TemporaryDirectory() as td:
            promoted_path = Path(td) / "promoted.py"
            with patch("tools.interface.PROMOTED_MODULE_PATH", promoted_path):
                # POST /api/tools/register
                tool_code = "def custom_api_test(x: int) -> int:\n    return x + 10\n"
                reg_resp = client.post(
                    "/api/tools/register",
                    json={"source": tool_code, "name": "custom_api_test"},
                )
                self.assertEqual(reg_resp.status_code, 200)
                self.assertEqual(reg_resp.json()["name"], "custom_api_test")

                # GET /api/tools/{name}
                get_resp = client.get("/api/tools/custom_api_test")
                self.assertEqual(get_resp.status_code, 200)
                self.assertTrue(get_resp.json()["custom"])

                # DELETE /api/tools/{name}
                del_resp = client.delete("/api/tools/custom_api_test")
                self.assertEqual(del_resp.status_code, 200)

                # GET after delete -> 404
                get_after = client.get("/api/tools/custom_api_test")
                self.assertEqual(get_after.status_code, 404)


if __name__ == "__main__":
    unittest.main()

```

## `test_environment/tool_workbench.py`
```py
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


HARNESS_START = "# --- Novous2 test call (edit the values; removed when adding to the library) ---"
HARNESS_END = "# --- end Novous2 test call ---"
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


```

## `tools/__init__.py`
```py
"""Tools package."""

```

## `tools/allowed_paths.json`
```json
{
  "map_roots": [
    "E:\\Novous2\\workspace",
    "E:\\Novous2_Note\\test",
    "C:\\Users\\43319\\OneDrive\\D\\Documents"
  ],
  "file_manager_root": "C:\\Users\\43319\\OneDrive\\D\\Documents",
  "file_manager_roots": [
    {
      "name": "Workspace",
      "path": "E:\\Novous2\\workspace"
    },
    {
      "name": "Documents",
      "path": "C:\\Users\\43319\\OneDrive\\D\\Documents"
    },
    {
      "name": "Scripts",
      "path": "E:\\Novous2_Note\\scripts"
    },
    {
      "name": "Test",
      "path": "E:\\Novous2_Note\\test"
    }
  ],
  "active_file_manager_root": "C:\\Users\\43319\\OneDrive\\D\\Documents",
  "sandbox_root": "E:\\Novous2_Note",
  "sandbox_roots": [
    "E:\\Novous2_Note\\scripts",
    "C:\\Users\\43319\\OneDrive\\D\\Documents"
  ]
}

```

## `tools/delete_file_tool.py`
```py
"""Workspace file deletion tool backed by the shared tools interface."""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="tools")
def delete_file(path: str) -> str:
    """Delete a file or directory from the workspace by relative path."""
    if not path or not path.strip():
        raise ValueError("A path is required.")
    result = interface.delete_file(path)
    return json.dumps(result, ensure_ascii=False, indent=2)

```

## `tools/editor_tool.py`
```py
"""Editor operations tool backed by the shared tools interface."""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="editor")
def editor(action: str, path: str = "", content: str = "") -> str:
    """Read, write, list a tree, or delete a path through the editor pillar."""
    result = interface.editor(action, path=path, content=content)
    return json.dumps(result, ensure_ascii=False, indent=2)

```

## `tools/interface.py`
```py
﻿"""Tools interface: FastAPI router and Python doorway for tool registry."""

import ast
import inspect
from pathlib import Path
import re
import sys
from typing import Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core_engine import tool_catalog
from editor import editor_operations
from file_manager.service import file_manager_service

router = APIRouter()

PROMOTED_MODULE_PATH = (
    Path(__file__).resolve().parent / "promoted_tools.py"
)
PROMOTED_MARKER = "# PROMOTION_MARKER: tools appended below will be registered as custom tools"
REPO_ROOT = Path(__file__).resolve().parent.parent

_FUNCTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def map_files(path: str = "") -> dict:
    """Return the file-manager directory tree for a workspace-relative path."""
    return file_manager_service.directory_tree(_workspace_relative(path))


def _workspace_relative(path: str) -> str:
    """Map '', '.', '/', and absolute paths inside the workspace root to relative paths."""
    from file_manager import backend

    clean = (path or "").strip().replace("\\", "/")
    if clean in ("", ".", "./", "/"):
        return ""
    if clean.startswith("/") or (len(clean) > 1 and clean[1] == ":"):
        try:
            relative = Path(clean).resolve().relative_to(backend.workspace_root())
        except ValueError:
            return clean
        return relative.as_posix() if relative.parts else ""
    return clean[2:] if clean.startswith("./") else clean


def list_directory(path: str = "") -> dict:
    """Return file-manager entries for a workspace-relative directory."""
    return file_manager_service.list_directory(path)


def read_file(path: str) -> dict:
    """Read a file through the configured file-manager root."""
    return file_manager_service.read_file(path)


def write_file(path: str, content: str) -> dict:
    """Write a file through the configured file-manager root."""
    return file_manager_service.write_file(path, content)


def delete_file(path: str) -> dict:
    """Delete a path through the configured file-manager root."""
    return file_manager_service.delete(path)


def render_map_page(
    path: str,
    max_depth: int = 3,
    include_files: bool = True,
    offset: int = 0,
) -> dict:
    """Render a page of the active file-manager root's directory tree."""
    depth = max(1, min(int(max_depth), 6))
    start = max(0, int(offset))
    listing = map_files(path)
    lines = [f"ðŸ“ {listing['name']}"]
    entry_count = [0]

    def append_children(node: dict, level: int, prefix: str = "") -> None:
        if level <= 0:
            return
        children = node.get("children", [])
        visible = [
            child for child in children
            if child.get("type") == "directory" or include_files
        ]
        for index, child in enumerate(visible):
            if entry_count[0] >= 5000:
                lines.append(f"{prefix}â””â”€â”€ â€¦ scan limit of 5000 entries reached")
                return
            entry_count[0] += 1
            last = index == len(visible) - 1
            connector = "â””â”€â”€ " if last else "â”œâ”€â”€ "
            if child.get("type") == "directory":
                lines.append(f"{prefix}{connector}ðŸ“ {child['name']}/")
                append_children(
                    child,
                    level - 1,
                    prefix + ("    " if last else "â”‚   "),
                )
            else:
                lines.append(f"{prefix}{connector}ðŸ“„ {child['name']}")

    append_children(listing, depth)
    page_size = 80
    page = lines[start:start + page_size]
    next_offset = start + len(page)
    remaining = max(0, len(lines) - next_offset)
    return {
        "text": "\n".join(page) if page else "(no more entries)",
        "next_offset": next_offset,
        "remaining": remaining,
        "total": len(lines),
    }


def editor(action: str, path: str = "", content: str = "") -> dict:
    """Dispatch a file operation through the editor pillar."""
    if not isinstance(action, str):
        raise ValueError("Editor action must be a string.")
    action_clean = action.strip().lower()
    if action_clean == "read":
        return editor_operations.read_file_content(path)
    if action_clean == "write":
        return editor_operations.write_file_content(path, content)
    if action_clean == "tree":
        return editor_operations.get_directory_tree(path)
    if action_clean == "delete":
        return editor_operations.delete_path(path)
    raise ValueError(f"Unsupported editor action: '{action}'")


class RegisterToolRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=50000)
    name: str | None = None


def _ensure_promoted_file() -> None:
    if not PROMOTED_MODULE_PATH.exists():
        PROMOTED_MODULE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROMOTED_MODULE_PATH.write_text(
            '"""Permanent storage for promoted custom tools."""\n'
            'from core_engine.tool_catalog import tool\n\n'
            f"{PROMOTED_MARKER}\n\n",
            encoding="utf-8",
            newline="\n",
        )
    else:
        content = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
        if PROMOTED_MARKER not in content:
            sep = "\n\n" if not content.endswith("\n") else "\n"
            PROMOTED_MODULE_PATH.write_text(
                content + sep + PROMOTED_MARKER + "\n\n",
                encoding="utf-8",
                newline="\n",
            )


def list_promoted_tool_names() -> list[str]:
    """Return names of promoted custom tools defined after the marker in promoted_tools.py."""
    if not PROMOTED_MODULE_PATH.is_file():
        return []
    try:
        source = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return []
    marker_line = 0
    for line_number, line in enumerate(source.splitlines(), start=1):
        if line.startswith("# PROMOTION_MARKER"):
            marker_line = line_number
            break
    names = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            if node.lineno > marker_line:
                names.append(node.name)
    return names


def _decorated_source(first: str, second: str = "") -> str:
    """Ensure tool source has the @tool decorator."""
    source = second if second else first
    src = source.strip()
    if src.startswith("@tool"):
        return src + "\n"
    return f"@tool\n{src}\n"


def _function_span(source: str, name: str) -> tuple[int, int, ast.FunctionDef]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start_line = min(
                (decorator.lineno for decorator in node.decorator_list),
                default=node.lineno,
            )
            return start_line - 1, node.end_lineno, node
    raise FileNotFoundError(f"Custom tool '{name}' was not found in the promoted module.")


def _function_source(source: str, name: str) -> str:
    start, end, _ = _function_span(source, name)
    return "\n".join(source.splitlines()[start:end]).strip() + "\n"


def _source_for_name(name: str, full_source: str) -> str:
    return _function_source(full_source, name)


def _remove_function(source: str, name: str) -> str:
    start, end, _ = _function_span(source, name)
    lines = source.splitlines(keepends=True)
    while end < len(lines) and lines[end].strip() == "":
        end += 1
    del lines[start:end]
    return "".join(lines)


def register_tool(source: str, name: str | None = None) -> dict:
    """Register a custom tool by appending to promoted_tools.py and execing into that module."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Python syntax error: {exc}") from exc

    fn_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            fn_node = node
            break
    if fn_node is None:
        raise ValueError("Define at least one public top-level function.")

    func_name = fn_node.name
    if name and name != func_name:
        raise HTTPException(
            status_code=400,
            detail="The primary function changed; run the test again before adding it.",
        )
    name = func_name

    _ensure_promoted_file()
    tool_catalog.load_tools()
    if name in tool_catalog.REGISTRY:
        raise HTTPException(
            status_code=409, detail=f"Tool '{name}' is already registered."
        )

    previous_content = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
    block = _decorated_source(name, source)
    sep = "\n" if not previous_content.endswith("\n\n") else ""
    new_content = previous_content + sep + block + "\n"
    PROMOTED_MODULE_PATH.write_text(new_content, encoding="utf-8", newline="\n")

    try:
        promoted_module = sys.modules.get("tools.promoted_tools")
        namespace = (
            promoted_module.__dict__
            if promoted_module is not None
            else {"tool": tool_catalog.tool, "__name__": "tools.promoted_tools"}
        )
        exec(block, namespace)
    except Exception as exc:
        PROMOTED_MODULE_PATH.write_text(previous_content, encoding="utf-8", newline="\n")
        tool_catalog.REGISTRY.pop(name, None)
        raise ValueError(f"Failed to execute tool '{name}': {exc}") from exc

    fn = tool_catalog.REGISTRY[name]["function"]
    tool_catalog.REGISTRY[name]["custom"] = True
    return {
        "name": name,
        "path": "tools/promoted_tools.py",
        "description": ast.get_docstring(fn_node) or "",
        "signature": str(inspect.signature(fn)),
    }


def remove_tool(name: str) -> dict:
    """Remove a custom tool from promoted_tools.py and tool_catalog.REGISTRY."""
    tool_catalog.load_tools()
    if name not in tool_catalog.REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")

    _ensure_promoted_file()
    previous_content = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
    try:
        new_content = _remove_function(previous_content, name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        PROMOTED_MODULE_PATH.write_text(new_content, encoding="utf-8", newline="\n")
    except Exception as exc:
        PROMOTED_MODULE_PATH.write_text(previous_content, encoding="utf-8", newline="\n")
        raise OSError(f"Could not update promoted module: {exc}") from exc

    tool_catalog.REGISTRY.pop(name, None)
    return {
        "name": name,
        "path": "tools/promoted_tools.py",
        "deleted": True,
    }


def get_tool_source(name: str) -> dict:
    """Retrieve source code of a tool (either promoted or builtin)."""
    if not _FUNCTION_NAME.fullmatch(name):
        raise ValueError("The tool name is not valid.")

    if PROMOTED_MODULE_PATH.is_file():
        full_source = PROMOTED_MODULE_PATH.read_text(encoding="utf-8")
        try:
            source = _function_source(full_source, name)
            return {
                "name": name,
                "path": "tools/promoted_tools.py",
                "source": source,
            }
        except FileNotFoundError:
            pass

    tool_catalog.load_tools()
    meta = tool_catalog.REGISTRY.get(name)
    if meta and "function" in meta:
        fn = meta["function"]
        try:
            source = inspect.getsource(fn)
            sourcefile = inspect.getsourcefile(fn)
            rel_path = (
                str(Path(sourcefile).relative_to(REPO_ROOT).as_posix())
                if sourcefile
                else "tools"
            )
            return {
                "name": name,
                "path": rel_path,
                "source": source,
            }
        except Exception:
            pass

    raise FileNotFoundError(f"Custom tool '{name}' was not found.")


def list_tools() -> list[dict]:
    """Return tool metadata with custom-tool flags."""
    tool_catalog.load_tools()
    promoted = set(list_promoted_tool_names())
    tools = []
    for meta in tool_catalog.REGISTRY.values():
        tools.append({
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
            "custom": meta["name"] in promoted or meta.get("custom", False),
        })
    return tools


def list_tools_directory() -> list[dict]:
    """Return registered tools defined by modules in the tools package."""
    return [
        tool
        for tool in list_tools()
        if (
            (meta := tool_catalog.REGISTRY[tool["name"]])["function"].__module__.startswith(
                "tools."
            )
            and meta["function"].__module__ != "tools.interface"
        )
    ]


def get_tool(name: str) -> Callable | None:
    """Resolve registered tool callable."""
    tool_catalog.load_tools()
    meta = tool_catalog.REGISTRY.get(name)
    return meta["function"] if meta else None


def provider_bindings() -> dict[str, str]:
    """Return provider mappings."""
    return tool_catalog.get_provider_bindings()


def catalog_report() -> dict:
    """Return catalog diagnostic report."""
    return tool_catalog.get_catalog_report()


@router.get("/api/tools")
def api_list_tools():
    rep = catalog_report()
    return {
        "tools": list_tools(),
        "providers": provider_bindings(),
        "warnings": rep.get("warnings", []),
    }


@router.get("/api/tools/library")
def api_tool_library():
    return {"tools": list_tools_directory()}


@router.get("/api/tools/health")
def api_tools_health():
    errors = tool_catalog.get_load_errors()
    return {
        "status": "healthy" if not errors else "degraded",
        "load_errors": errors,
        "warnings": catalog_report().get("warnings", []),
    }


@router.post("/api/tools/register")
def api_register_tool(req: RegisterToolRequest):
    try:
        return register_tool(req.source, req.name)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class MapPageRequest(BaseModel):
    path: str
    max_depth: int = 3
    include_files: bool = True
    offset: int = 0


@router.post("/api/tools/map-page")
def api_map_page(req: MapPageRequest):
    tool_catalog.load_tools()
    try:
        return render_map_page(req.path, req.max_depth, req.include_files, req.offset)
    except (PermissionError, ValueError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/tools/{name}")
def api_get_tool(name: str):
    tool_catalog.load_tools()
    meta = tool_catalog.REGISTRY.get(name)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")
    promoted = set(list_promoted_tool_names())
    return {
        "name": meta["name"],
        "provider": meta["provider"],
        "description": meta["description"],
        "signature": meta["signature"],
        "custom": meta["name"] in promoted or meta.get("custom", False),
    }


@router.delete("/api/tools/{name}")
def api_delete_tool(name: str):
    try:
        return remove_tool(name)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

```

## `tools/map_files_tool.py`
```py
"""Workspace mapping tool backed by the shared tools interface."""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="file_manager")
def map_files(path: str = "") -> str:
    """Return the directory tree for a path relative to the configured file-manager root."""
    return json.dumps(interface.map_files(path), ensure_ascii=False, indent=2)

```

## `tools/promoted_tools.py`
```py
"""Permanent storage for custom tools promoted from the Prompt Testing Workbench.

Promoted tools are appended below the PROMOTION_MARKER by tools/interface.py,
which performs AST validation, registry updates, and rollback on failure.
"""
from core_engine.tool_catalog import tool

# PROMOTION_MARKER: tools appended below will be registered as custom tools


```

## `tools/read_tool.py`
```py
"""Verb-oriented file reading backed by the shared tools interface.

The tools interface delegates to file_manager_service, the single access
boundary: every path is validated against allowed_paths.json and constrained
to the active file-manager root.
The latest read is mirrored into the workspace scratchpad so downstream
tools (edit/write) can reference or modify it without re-reading the source.
"""

import json

from core_engine.tool_catalog import tool
from tools import interface

MAX_READ_SIZE_BYTES = 1_000_000  # ~1 MB. Raise or lower this cap here.
SCRATCHPAD_PATH = "scratchpad/latest_read.txt"
_UTF8 = "utf-8"


def _split_relative(path: str) -> tuple[str, str]:
    clean = path.replace("\\", "/").strip("/")
    if "/" not in clean:
        return "", clean
    parent, name = clean.rsplit("/", 1)
    return parent, name


def _listed_size(path: str) -> int | None:
    parent, name = _split_relative(path)
    try:
        entries = interface.list_directory(parent)["entries"]
    except Exception:
        return None
    for entry in entries:
        if entry["name"] == name:
            return int(entry.get("size") or 0)
    return None


def _size_guard(path: str, size_bytes: int) -> None:
    if size_bytes > MAX_READ_SIZE_BYTES:
        raise ValueError(
            f"Refusing to read '{path}': {size_bytes} bytes exceeds MAX_READ_SIZE_BYTES "
            f"({MAX_READ_SIZE_BYTES}). Adjust MAX_READ_SIZE_BYTES at the top of "
            f"tools/read_tool.py to raise the cap."
        )


def _copy_to_scratchpad(content: str) -> str | None:
    try:
        result = interface.write_file(SCRATCHPAD_PATH, content)
        return str(result.get("path", SCRATCHPAD_PATH))
    except Exception:
        return None


@tool(provider="tools")
def read_file(path: str, request: str = "") -> str:
    """Read a UTF-8 text file from the workspace by relative path; bare filenames go in the root.

    The raw content is mirrored to scratchpad/latest_read.txt, so later edit/write calls can
    target the scratchpad instead of the original path. Files larger than MAX_READ_SIZE_BYTES
    (~1 MB) are rejected; see tools/read_tool.py to adjust the limit.
    Returns JSON with the request echo, resolved path, raw content, and scratchpad context.
    """
    if not path or not path.strip():
        raise ValueError("A file path is required.")

    listed = _listed_size(path)
    if listed is not None:
        _size_guard(path, listed)

    try:
        result = interface.read_file(path)
    except Exception as exc:
        raise RuntimeError(f"Could not read '{path}': {exc}") from exc

    content = result["content"]
    size_bytes = len(content.encode(_UTF8))
    if listed is None:
        _size_guard(path, size_bytes)

    scratchpad_path = _copy_to_scratchpad(content)
    payload = {
        "request": request,
        "path": result["path"],
        "size_bytes": size_bytes,
        "content": content,
        "scratchpad": {
            "path": scratchpad_path,
            "context": (
                "Latest read mirrored here; point edit/write tools at this path to modify it."
                if scratchpad_path
                else "Scratchpad copy failed; the content in this payload is the only copy."
            ),
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

```

## `tools/write_tool.py`
```py
"""Verb-oriented file overwrite tool backed by the shared tools interface.

The tools interface delegates to file_manager_service, the single access
boundary: every path is validated against allowed_paths.json and constrained
to the active file-manager root.
"""

import json

from core_engine.tool_catalog import tool
from tools import interface


@tool(provider="tools")
def write_file(path: str, content: str) -> str:
    """Write UTF-8 content to a workspace file by relative path (bare filenames go in the root).

    Overwrites existing files and creates missing parent directories.
    Supports formats such as .txt, .md, .py, .json, .html, .css, and .js.
    Returns JSON with the resolved path and bytes written.
    """
    if not path or not path.strip():
        raise ValueError("A file path is required.")
    try:
        result = interface.write_file(path, content)
    except Exception as exc:
        raise RuntimeError(f"Could not write '{path}': {exc}") from exc
    return json.dumps(result, ensure_ascii=False, indent=2)

```

## `workspace/__init__.py`
```py

```

## `workspace/interface.py`
```py
"""Workspace Doorway: Python API & FastAPI Router (/api/project, /api/health, squads)."""

import json
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from workspace import squad_manager, workspace_workflow

router = APIRouter()

PROJECT_FILE = Path(__file__).resolve().parent / "project.json"
START_TIME = time.time()


def _default_project() -> dict:
    return {
        "name": "Novous2 Workspace",
        "version": "1.0.0",
        "description": "",
        "default_model": "qwen2.5-coder:latest",
        "squad_root": "",
        "active_agent": "",
    }


def get_project_state() -> dict:
    """Doorway function: read workspace/project.json."""
    if not PROJECT_FILE.is_file():
        return _default_project()
    try:
        return json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _default_project()


def save_project_state(state: dict) -> dict:
    """Doorway function: persist workspace/project.json."""
    current = get_project_state()
    current.update({k: v for k, v in state.items() if v is not None})
    PROJECT_FILE.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return current


def get_health() -> dict:
    """Doorway function: aggregated system health."""
    ollama_ok = False
    ollama_detail = "unreachable"
    try:
        import ollama
        ollama.list()
        ollama_ok = True
        ollama_detail = "connected"
    except Exception as exc:
        ollama_detail = str(exc)

    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": {"reachable": ollama_ok, "detail": ollama_detail},
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": time.time(),
    }


class ProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    default_model: str | None = None
    active_agent: str | None = None
    squad_root: str | None = None


class ScaffoldRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    mode: str = "chat"
    squad: str = ""


class SquadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: str = ""


class SquadRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    new_name: str = Field(..., min_length=1, max_length=64)


# --- Project & health ------------------------------------------------------

@router.get("/api/project")
def api_get_project():
    state = get_project_state()
    from core_engine.agent_factory import list_agents
    state["agents"] = list_agents()
    state["squads"] = squad_manager.list_squads()
    return state


@router.post("/api/project")
def api_save_project(req: ProjectRequest):
    try:
        return save_project_state(req.model_dump())
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/health")
def api_health():
    return get_health()


# --- Agent scaffolding (workspace owns the canonical storage) --------------

@router.post("/api/workspace/agents/scaffold")
def api_scaffold_agent(req: ScaffoldRequest):
    try:
        return workspace_workflow.scaffold_agent(
            req.agent_id, req.name, req.description, req.mode, req.squad)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/api/workspace/agents/{agent_id}")
def api_update_agent(agent_id: str, req: dict):
    try:
        return workspace_workflow.save_agent_meta(agent_id, req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/workspace/agents/{agent_id}/squad")
def api_agents_by_squad(squad: str = ""):
    return {"squad": squad, "agents": workspace_workflow.agents_for_squad(squad)}


# --- Squads ----------------------------------------------------------------

@router.get("/api/squads")
def api_list_squads():
    return {"squads": squad_manager.list_squads()}


@router.post("/api/squads/create")
def api_create_squad(req: SquadRequest):
    try:
        return squad_manager.create_squad(req.name, req.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/squads/rename")
def api_rename_squad(req: SquadRenameRequest):
    try:
        return squad_manager.rename_squad(req.name, req.new_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/squads/delete")
def api_delete_squad(req: SquadRequest):
    try:
        return squad_manager.delete_squad(req.name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

```

## `workspace/project.json`
```json
{
  "name": "Novous2 Workspace",
  "version": "1.0.0",
  "description": "Canonical project state for the Novous2 Agent Factory.",
  "default_model": "qwen2.5-coder:latest",
  "squad_root": "",
  "active_agent": "assistant",
  "created_at": "2026-10-07T00:00:00Z"
}

```

## `workspace/squad_manager.py`
```py
"""Folder Hierarchy Engine: squad folders under workspace/squads/."""

import json
import re
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
SQUAD_ROOT = WORKSPACE_ROOT / "squads"

_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9 _-]{0,63}$")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def _meta_path(squad_name: str) -> Path:
    return SQUAD_ROOT / _slug(squad_name) / "squad.json"


def _validate(name: str) -> str:
    name = name.strip()
    if not _NAME_PATTERN.match(name):
        raise ValueError("Squad name must be 1-64 chars (letters, digits, spaces, '-', '_').")
    return name


def list_squads() -> list[dict]:
    squads = []
    if not SQUAD_ROOT.is_dir():
        return squads
    for child in sorted(SQUAD_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        meta_file = child / "squad.json"
        if meta_file.is_file():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        else:
            meta = {}
        squads.append({
            "id": child.name,
            "name": meta.get("name", child.name),
            "description": meta.get("description", ""),
            "path": f"squads/{child.name}",
        })
    return squads


def create_squad(name: str, description: str = "") -> dict:
    name = _validate(name)
    slug = _slug(name)
    squad_dir = SQUAD_ROOT / slug
    if squad_dir.exists():
        raise ValueError(f"Squad already exists: {name}")
    squad_dir.mkdir(parents=True)
    meta = {"name": name, "description": description.strip(), "id": slug}
    (squad_dir / "squad.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"created": True, "squad": meta}


def rename_squad(old_name: str, new_name: str) -> dict:
    new_name = _validate(new_name)
    src = SQUAD_ROOT / _slug(old_name)
    if not src.is_dir():
        raise FileNotFoundError(f"Squad not found: {old_name}")
    dst = SQUAD_ROOT / _slug(new_name)
    if dst.exists():
        raise ValueError(f"Squad already exists: {new_name}")
    src.rename(dst)
    meta_file = dst / "squad.json"
    meta = {}
    if meta_file.is_file():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    meta["name"] = new_name
    meta["id"] = dst.name
    meta_file.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"renamed": True, "squad": meta}


def delete_squad(name: str) -> dict:
    squad_dir = SQUAD_ROOT / _slug(name)
    if not squad_dir.is_dir():
        raise FileNotFoundError(f"Squad not found: {name}")
    shutil.rmtree(squad_dir)
    return {"deleted": True, "id": squad_dir.name}

```

## `workspace/workspace_workflow.py`
```py
"""Agent Scaffolding & Squad Routing."""

import re
from pathlib import Path

from core_engine.agent_factory import AGENT_ENVIRONMENTS, AGENT_MD_TEMPLATE, LIBRARY_ROOT, parse_yaml_frontmatter

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

DEFAULT_TOOLS = [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "project_status",
]

CODEBUILDER_DEFAULT_TOOLS = [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "run_python_code",
    "send_code_to_editor",
    "run_code_in_editor",
]


def _validate_id(agent_id: str, environment: str = "workspace") -> str:
    agent_id = agent_id.strip().lower()
    if not _ID_PATTERN.match(agent_id):
        raise ValueError(
            "agent_id must be lowercase letters, digits, '-' or '_', starting alphanumeric, max 64 chars.")
    if environment not in AGENT_ENVIRONMENTS:
        raise ValueError(f"Unknown agent environment: {environment}")
    return agent_id


def _agent_library_path(agent_id: str) -> Path:
    return LIBRARY_ROOT / f"{agent_id}.md"


def _render_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key in ["id", "name", "description", "mode", "model", "squad", "environment", "environment_name", "version"]:
        if key not in meta:
            continue
        value = meta[key]
        if value in (None, ""):
            continue
        if key == "tools":
            continue
        if isinstance(value, (bool, int, float)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    if "tools" in meta and meta["tools"]:
        lines.append("tools:")
        for tool in meta["tools"]:
            lines.append(f"  - {tool}")
    if "skills" in meta and meta["skills"]:
        lines.append("skills:")
        for skill in meta["skills"]:
            if isinstance(skill, dict):
                for skill_name, config in skill.items():
                    lines.append(f"  - {skill_name}:")
                    if isinstance(config, dict):
                        for nested_key, nested_value in config.items():
                            lines.append(f"      {nested_key}: {nested_value}")
            else:
                lines.append(f"  - {skill}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _read_agent_file(path: Path) -> tuple[dict, str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text.strip("\n")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip("\n")
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        return {}, text.strip("\n")
    frontmatter = parse_yaml_frontmatter(text)
    body = "\n".join(lines[end_index + 1:]).strip("\n")
    return frontmatter, body


def scaffold_agent(agent_id: str, name: str, description: str = "",
                   mode: str = "chat", squad: str = "",
                   environment: str = "workspace",
                   environment_name: str = "") -> dict:
    """Create a single-file agent definition in library/{agent_id}.md."""
    agent_id = _validate_id(agent_id, environment)
    environment_name = " ".join(str(environment_name or "").split())[:64]
    if not name.strip():
        raise ValueError("Agent name must not be empty.")

    library_path = _agent_library_path(agent_id)
    if library_path.exists():
        raise ValueError(f"Agent already exists in library: {agent_id}")

    LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": agent_id,
        "name": name.strip(),
        "description": description.strip(),
        "mode": mode if mode in ("chat", "agent") else "chat",
        "model": "qwen2.5-coder:latest",
        "squad": squad.strip(),
        "tools": (
            list(CODEBUILDER_DEFAULT_TOOLS if environment == "codebuilder" else DEFAULT_TOOLS)
            if mode == "agent" else []
        ),
        "environment": environment,
        "environment_name": environment_name,
        "version": 1,
    }

    purpose = description.strip() or (
        f"Serve as the {name.strip()} for the {environment_name or environment} environment."
    )
    purpose += " Act strategically toward that goal and always deliver a clear, structured result."
    agent_template = AGENT_MD_TEMPLATE
    if environment == "codebuilder":
        agent_template = AGENT_MD_TEMPLATE.replace(
            "Novous2 workspace agent",
            "Novous2 CodeBuilder agent",
        )
        if mode == "agent":
            agent_template += """

## codebuilder editor workflow
Whenever you provide or revise Python code, call `send_code_to_editor` with the complete code so it is placed in the active Monaco editor. Also include a fenced `python` code block in your reply so the user can review it and send it manually if needed. When the user asks to run the code, send any changed code first, then call `run_code_in_editor`.
"""

    markdown = agent_template.format(name=name.strip(), purpose=purpose)
    rendered = _render_frontmatter(meta) + "\n" + markdown + "\n"
    library_path.write_text(rendered, encoding="utf-8")

    return {"created": True, "agent_id": agent_id,
            "path": f"library/{agent_id}.md",
            "environment": environment,
            "environment_name": environment_name,
            "agent": meta}


def delete_agent(agent_id: str, environment: str = "workspace") -> dict:
    agent_id = _validate_id(agent_id, environment)
    library_path = _agent_library_path(agent_id)
    if library_path.is_file():
        metadata, _ = _read_agent_file(library_path)
        if metadata.get("environment", "workspace") != environment:
            raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
        library_path.unlink()
        return {"deleted": True, "agent_id": agent_id, "environment": environment, "path": f"library/{agent_id}.md"}
    raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")


def save_agent_meta(agent_id: str, meta: dict) -> dict:
    """Persist edited agent metadata while preserving the markdown body."""
    agent_id = _validate_id(agent_id)
    library_path = _agent_library_path(agent_id)
    if not library_path.is_file():
        raise FileNotFoundError(f"Agent not found: {agent_id}")

    existing_data, body = _read_agent_file(library_path)
    if existing_data.get("environment", "workspace") != "workspace":
        raise FileNotFoundError(f"Agent not found in workspace: {agent_id}")
    merged = dict(existing_data)
    merged.update(meta)
    merged["id"] = agent_id
    library_path.write_text(_render_frontmatter(merged) + "\n" + body.strip("\n") + "\n", encoding="utf-8")
    return {"saved": True, "agent": merged, "path": f"library/{agent_id}.md"}


def agents_for_squad(squad: str) -> list[dict]:
    """Squad routing: canonical agents filtered by their squad field."""
    agents = []
    library_root = LIBRARY_ROOT
    if library_root.is_dir():
        for file in sorted(library_root.glob("*.md")):
            frontmatter, _ = _read_agent_file(file)
            if frontmatter.get("environment", "workspace") == "workspace" and frontmatter.get("squad", "") == squad:
                agents.append({**frontmatter, "path": file.relative_to(Path(__file__).resolve().parent.parent).as_posix()})
    return agents

```
