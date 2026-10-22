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
MAX_TIMEOUT_SECONDS = 480.0
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
    if dump_after > 0:
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
    keep_running = bool(getattr(req, "keep_running", False)) and merge_output
    timeout = float("inf") if keep_running else _clamp_timeout(req.timeout_seconds)
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
        "timeout_seconds": None if keep_running else timeout,
        "keep_running": keep_running,
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

            if keep_running:
                dump_after = 0.0
            else:
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

            if not keep_running:
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
