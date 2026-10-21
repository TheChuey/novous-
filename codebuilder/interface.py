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