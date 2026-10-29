"""Workflow execution supervisor for orchestration requests."""

from orchestration.orchestration_registry import get_pattern
from orchestration.orchestration_schemas import OrchestrationRequest, OrchestrationResponse


def run_orchestration(request: OrchestrationRequest) -> OrchestrationResponse:
    if request.squad_id == "code-squad":
        from orchestration.code_squad_pipeline import run_code_squad

        return run_code_squad(request)
    pattern_handler = get_pattern(request.pattern)
    return pattern_handler.execute(request)
