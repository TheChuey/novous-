"""FastAPI REST API endpoints for orchestration."""

from fastapi import APIRouter, HTTPException

from orchestration.orchestration_schemas import OrchestrationRequest, OrchestrationResponse
from orchestration.orchestration_service import run_orchestration

router = APIRouter(prefix="/api/orchestration", tags=["Orchestration"])


@router.post("/run", response_model=OrchestrationResponse)
def run_orchestration_endpoint(request: OrchestrationRequest):
    try:
        return run_orchestration(request)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Orchestration execution failed: {exc}"
        ) from exc
