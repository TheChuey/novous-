"""CodeBuilder doorway: FastAPI router for execution and structured edits."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .agent_loader import load_codebuilder_agent_meta
from .execution import execute_python_code
from .runner import run_risky
from .schemas import CodeExecutionRequest, CodeExecutionResult, StructuredEditRequest
from core_engine.agent_factory import list_agents

router = APIRouter(prefix="/api/codebuilder", tags=["CodeBuilder"])


@router.get("/health")
def api_codebuilder_health():
    """Return the health state of the CodeBuilder pillar."""
    return {"status": "ok", "pillar": "codebuilder"}


@router.get("/agent")
def api_get_agent():
    """Return the CodeBuilder specialist profile."""
    return load_codebuilder_agent_meta()


@router.get("/agents")
def api_codebuilder_agents():
    """List only agents stored in the CodeBuilder environment."""
    return {"agents": list_agents("codebuilder")}


@router.post("/execute", response_model=CodeExecutionResult)
def api_execute_code(req: CodeExecutionRequest):
    """Execute Python source and return any collected diagnostics."""
    try:
        return execute_python_code(req)
    except Exception as exc:  # pragma: no cover - surfaced as HTTP 500
        raise HTTPException(status_code=500, detail=f"CodeBuilder execution error: {exc}") from exc


def _sse_events(events):
    for event in events:
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/execute/stream")
def api_stream_execute(req: CodeExecutionRequest):
    """Stream risky-mode execution output live as Server-Sent Events."""
    if req.mode != "risky":
        raise HTTPException(status_code=400, detail="Streaming is only supported in risky mode.")

    def stream():
        for event in _sse_events(run_risky(req)):
            yield event

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/edit")
def api_apply_structured_edit(req: StructuredEditRequest):
    """Write an approved file update to the workspace."""
    target = Path(req.target_path)
    if not target.is_absolute():
        target = Path.cwd() / target

    if target.exists() and target.is_dir():
        raise HTTPException(status_code=400, detail="Target path points to a directory, not a file.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")

    return {
        "status": "applied",
        "target_path": str(target),
        "bytes_written": len(req.content.encode("utf-8")),
        "explanation": req.explanation,
    }
