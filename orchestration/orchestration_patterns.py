"""Execution strategies for multi-subagent orchestration workflows.

The Code Development Squad runs through ``code_squad_pipeline``; these patterns
serve the RAG squad and user-defined squads.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import time
import uuid

from orchestration import orchestration_interface as interface
from orchestration.orchestration_schemas import (
    OrchestrationRequest,
    OrchestrationResponse,
    TraceStep,
)
from orchestration.orchestration_run_results import run_results
from orchestration.orchestration_telemetry import telemetry_bus
from orchestration.squad_registry import (
    get_squad,
    get_squad_id_for_primary_agent,
    record_squad_run,
)


def _print_trace(message: str) -> None:
    """Print a trace line without failing on terminals that cannot encode box glyphs."""
    try:
        print(message, flush=True)
    except UnicodeEncodeError:
        print(message.encode("ascii", "replace").decode("ascii"), flush=True)


def _result_count(scratchpad_entry: dict) -> int:
    payload = scratchpad_entry.get("payload")
    results = payload.get("results") if isinstance(payload, dict) else None
    return len(results) if isinstance(results, list) else int(bool(payload))


def _squad_for_request(request: OrchestrationRequest) -> str | None:
    if request.workflow_action != "all":
        raise ValueError("Plan, Build, Test, and Fix actions are only available for code-squad.")
    if request.squad_id:
        squad = get_squad(request.squad_id)
        if squad is None:
            raise ValueError(f"Unknown registered squad: {request.squad_id}")
        request.primary_agent = squad["primary_agent"]
        request.subagents = list(squad["subagents"])
        return request.squad_id
    return get_squad_id_for_primary_agent(request.primary_agent)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BasePattern(ABC):
    @abstractmethod
    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        pass


class SequentialPattern(BasePattern):
    """Executes sub-agents sequentially to avoid local LLM hardware bottlenecks."""

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        if request.squad_id == "code-squad":
            from orchestration.code_squad_pipeline import run_code_squad

            return run_code_squad(request)

        trace_id = request.trace_id or f"tr_{uuid.uuid4().hex}"
        request.trace_id = trace_id
        squad_id = _squad_for_request(request)
        primary_id = request.primary_agent or "rag-presenter"
        workers = request.subagents or ["rag-retriever"]

        started = time.perf_counter()
        telemetry_bus.log_event(
            trace_id, "RUN_STARTED", "orchestrator", squad_id or primary_id,
            {"squad_id": squad_id or "unregistered", "pattern": request.pattern},
        )
        _print_trace(
            f"\n\033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m Starting sequential pipeline."
        )
        trace_steps: list[TraceStep] = []
        try:
            for worker_id in workers:
                step_number = len(trace_steps) + 1
                _print_trace(f" ├── [{step_number}] Executing sub-agent '\033[93m{worker_id}\033[0m'...")
                telemetry_bus.log_event(
                    trace_id, "AGENT_MESSAGE", "orchestrator", worker_id,
                    {"summary": "Sub-agent phase started", "status": "running"},
                )
                try:
                    if worker_id == "rag-retriever":
                        prompt = request.user_query
                    else:
                        prompt = f"Task: '{request.user_query}'. Parameters: {request.parameters}"
                    interface.run_agent_turn(worker_id, prompt, request.parameters, trace_id=trace_id)
                    trace_steps.append(TraceStep(
                        step_number=step_number, agent_id=worker_id, phase="SUBAGENT_EXECUTION",
                        status="SUCCESS", details=f"Executed worker '{worker_id}'", timestamp=_now(),
                    ))
                    telemetry_bus.log_event(
                        trace_id, "AGENT_MESSAGE", worker_id, "orchestrator",
                        {"summary": "Sub-agent phase completed", "status": "success"},
                    )
                except Exception as exc:
                    _print_trace(f" │   \033[91m[ERROR]\033[0m Worker '{worker_id}' failed: {exc}")
                    trace_steps.append(TraceStep(
                        step_number=step_number, agent_id=worker_id, phase="SUBAGENT_EXECUTION",
                        status="ERROR", details=f"Sub-agent '{worker_id}' raised an exception",
                        error_reason=str(exc), timestamp=_now(),
                    ))
                    telemetry_bus.log_event(
                        trace_id, "ERROR", worker_id, "orchestrator",
                        {"error": f"Sub-agent '{worker_id}' failed: {exc}", "status": "error"},
                    )

            scratchpad_entry = interface.read_latest_subagent_scratchpad()
            scratchpad_snapshot = interface.read_scratchpad_snapshot()
            status = (
                str(scratchpad_entry.get("status") or "success")
                if scratchpad_entry
                else "no_context_found"
            )
            telemetry_bus.log_event(
                trace_id, "SCRATCHPAD_HANDOFF", "orchestrator", "scratchpad",
                {
                    "status": status,
                    "subagent_id": scratchpad_entry.get("subagent_id", ""),
                    "result_count": _result_count(scratchpad_entry),
                    "direction": "read",
                },
            )
            trace_steps.append(TraceStep(
                step_number=len(trace_steps) + 1, agent_id="scratchpad", phase="SCRATCHPAD_BARRIER",
                status=status, details="Retrieved latest sub-agent payload from scratchpad",
                timestamp=_now(),
            ))

            telemetry_bus.log_event(
                trace_id, "AGENT_MESSAGE", "orchestrator", primary_id,
                {"summary": "Primary synthesis started", "status": "running"},
            )
            final_answer = interface.run_agent_turn(
                primary_id,
                f"User request: '{request.user_query}'. "
                "Inspect scratchpad using read_agent_scratchpad('latest_subagent_result') "
                "and synthesize the final output in clear, user-facing prose.",
                trace_id=trace_id,
            )
            trace_steps.append(TraceStep(
                step_number=len(trace_steps) + 1, agent_id=primary_id, phase="PRIMARY_SYNTHESIS",
                status="SUCCESS", details=f"Primary agent '{primary_id}' completed response",
                timestamp=_now(),
            ))
            telemetry_bus.log_event(
                trace_id, "AGENT_MESSAGE", primary_id, "orchestrator",
                {"summary": "Primary synthesis completed", "status": "success"},
            )
            if any(step.status == "ERROR" for step in trace_steps):
                status = "error"
        except Exception as exc:
            status = "error"
            final_answer = f"Workflow failed: {exc}"
            scratchpad_entry, scratchpad_snapshot = {}, {}
            telemetry_bus.log_event(
                trace_id, "ERROR", "orchestrator", squad_id or primary_id,
                {"error": final_answer, "status": "error"},
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        if squad_id:
            record_squad_run(squad_id, status != "error", duration_ms)
        response = OrchestrationResponse(
            trace_id=trace_id,
            pattern=request.pattern,
            query=request.user_query,
            status=status,
            final_answer=final_answer,
            result_payload=scratchpad_entry.get("payload") if scratchpad_entry else None,
            execution_trace=trace_steps,
        )
        # Save before RUN_COMPLETE so the client's result fetch never races a 404.
        run_results.save(
            trace_id,
            {**response.model_dump(), "squad_id": squad_id, "scratchpad_snapshot": scratchpad_snapshot},
        )
        telemetry_bus.log_event(
            trace_id, "RUN_COMPLETE", "orchestrator", squad_id or primary_id,
            {"status": status, "duration_ms": duration_ms},
        )
        telemetry_bus.finish_trace(trace_id)
        _print_trace(f" \033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m Pipeline complete.\n")
        return response


class FanOutPattern(BasePattern):
    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        res = SequentialPattern().execute(request)
        res.pattern = "fanout"
        return res


class RouterPattern(BasePattern):
    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        res = SequentialPattern().execute(request)
        res.pattern = "router"
        return res
