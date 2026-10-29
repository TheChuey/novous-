"""FastAPI REST API endpoints for orchestration."""

from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
import uuid

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from orchestration.orchestration_schemas import (
    OrchestrationRequest,
    OrchestrationResponse,
    SquadCreateRequest,
)
from orchestration.orchestration_service import run_orchestration
from orchestration.orchestration_telemetry import parse_last_event_id, telemetry_bus
from orchestration.orchestration_run_results import run_results
from orchestration.codebuilder_run_state import (
    MAX_EDITOR_CONTENT_BYTES,
    codebuilder_run_state,
)
from orchestration.squad_registry import (
    create_squad,
    delete_squad,
    get_squad,
    list_agent_catalog,
    list_squads,
)

router = APIRouter(prefix="/api/orchestration", tags=["Orchestration"])
_RUN_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="orchestration")
_RUN_CAPACITY = BoundedSemaphore(10)


@router.get("/squads")
def get_registered_squads():
    return {"squads": list_squads()}


@router.get("/catalog")
def get_agent_catalog():
    return list_agent_catalog()


@router.post("/squads", status_code=201)
def create_registered_squad(request: SquadCreateRequest):
    try:
        squad = create_squad(
            request.name,
            request.description,
            request.primary_agent,
            request.subagents,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"squad": squad}


@router.delete("/squads/{squad_id}")
def delete_registered_squad(squad_id: str):
    if not delete_squad(squad_id):
        raise HTTPException(status_code=404, detail="Squad not found.")
    return {"deleted": True, "squad_id": squad_id}


@router.get("/squads/{squad_id}/latest")
def get_latest_squad_run(squad_id: str):
    if get_squad(squad_id) is None:
        raise HTTPException(status_code=404, detail="Squad not found.")
    return {"result": run_results.latest_for_squad(squad_id)}


@router.post("/run", response_model=OrchestrationResponse)
def run_orchestration_endpoint(request: OrchestrationRequest):
    if request.workflow_action != "all" and request.squad_id != "code-squad":
        raise HTTPException(
            status_code=400,
            detail="Plan, Build, Test, and Fix actions require code-squad.",
        )
    try:
        return run_orchestration(request)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Orchestration execution failed: {exc}"
        ) from exc


def _run_background(request: OrchestrationRequest) -> None:
    try:
        run_orchestration(request)
    except Exception:
        history = telemetry_bus.get_trace_history(request.trace_id or "")
        run_results.save(
            request.trace_id or "",
            {
                "trace_id": request.trace_id,
                "squad_id": request.squad_id,
                "status": "error",
                "final_answer": "Workflow failed. See the execution trace for details.",
                "result_payload": None,
                "execution_trace": [],
            },
        )
        if not any(event["event_type"] == "RUN_COMPLETE" for event in history):
            telemetry_bus.log_event(
                request.trace_id or "",
                "ERROR",
                "orchestrator",
                request.squad_id or "orchestrator",
                {"error": "Orchestration execution failed", "status": "error"},
            )
            telemetry_bus.log_event(
                request.trace_id or "",
                "RUN_COMPLETE",
                "orchestrator",
                request.squad_id or "orchestrator",
                {"status": "error", "duration_ms": 0},
            )
            telemetry_bus.finish_trace(request.trace_id or "")
    finally:
        _RUN_CAPACITY.release()


@router.post("/run/start")
def start_orchestration_run(request: OrchestrationRequest):
    squad = get_squad(request.squad_id or "")
    if squad is None:
        raise HTTPException(status_code=400, detail="A registered squad_id is required.")
    if request.workflow_action != "all" and squad["squad_id"] != "code-squad":
        raise HTTPException(
            status_code=400,
            detail="Plan, Build, Test, and Fix actions are only available for code-squad.",
        )
    editor_code = request.parameters.get("editor_code", "")
    if not isinstance(editor_code, str):
        raise HTTPException(status_code=400, detail="The editor_code parameter must be text.")
    if len(editor_code.encode("utf-8")) > MAX_EDITOR_CONTENT_BYTES:
        raise HTTPException(
            status_code=413,
            detail="The CodeBuilder editor buffer exceeds the 1 MB workflow limit.",
        )
    if not _RUN_CAPACITY.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="Orchestration capacity is full. Try again after a run completes.",
        )
    request.trace_id = f"tr_{uuid.uuid4().hex}"
    request.pattern = squad["default_pattern"]
    try:
        codebuilder_run_state.begin(
            request.trace_id,
            editor_code,
            user_query=request.user_query,
            workflow_action=request.workflow_action,
            editor_path=str(request.parameters.get("editor_path") or ""),
        )
        telemetry_bus.initialize_trace(request.trace_id)
        _RUN_EXECUTOR.submit(_run_background, request)
    except Exception:
        # If trace initialization fails, do not leave a stale editor buffer behind.
        codebuilder_run_state.discard(request.trace_id)
        _RUN_CAPACITY.release()
        raise
    return {"trace_id": request.trace_id, "squad_id": squad["squad_id"]}


@router.get("/runs/{trace_id}")
def get_orchestration_run_result(trace_id: str):
    result = run_results.get(trace_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow result not found yet.")
    return result


@router.post("/runs/{trace_id}/cancel")
def cancel_orchestration_run(trace_id: str):
    if not codebuilder_run_state.cancel(trace_id):
        raise HTTPException(status_code=404, detail="Workflow run not found.")
    return {"cancelled": True, "trace_id": trace_id}


@router.get("/runs/{trace_id}/editor-preview")
def get_orchestration_editor_preview(trace_id: str):
    preview = codebuilder_run_state.get_preview(trace_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="No editor-buffer preview is available yet.")
    return preview


@router.get("/runs/{trace_id}/editor-execution")
def get_orchestration_editor_execution(trace_id: str):
    execution = codebuilder_run_state.get_execution(trace_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="No editor-buffer execution result is available yet.")
    return execution


@router.get("/runs/{trace_id}/scratchpad")
def get_orchestration_run_scratchpad(trace_id: str):
    result = run_results.get(trace_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow result not found yet.")
    snapshot = result.get("scratchpad_snapshot")
    if not snapshot:
        raise HTTPException(
            status_code=404, detail="This workflow did not capture a scratchpad snapshot."
        )
    return snapshot


@router.get("/stream/{trace_id}")
def stream_orchestration_trace(
    trace_id: str,
    after: int = 0,
    last_event_id: str | None = Header(default=None),
):
    if not telemetry_bus.has_trace(trace_id):
        raise HTTPException(status_code=404, detail="Trace not found.")
    if not telemetry_bus.has_listener_capacity(trace_id):
        raise HTTPException(status_code=429, detail="Trace stream capacity is full.")
    return StreamingResponse(
        telemetry_bus.subscribe(trace_id, max(after, parse_last_event_id(last_event_id))),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
