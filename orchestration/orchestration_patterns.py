"""Execution strategies for multi-subagent orchestration workflows."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import uuid

from orchestration import orchestration_interface as interface
from orchestration.orchestration_schemas import (
    OrchestrationRequest,
    OrchestrationResponse,
    TraceStep,
)


def _print_trace(message: str) -> None:
    """Print a trace line without failing on terminals that cannot encode box glyphs."""
    try:
        print(message, flush=True)
    except UnicodeEncodeError:
        print(message.encode("ascii", "replace").decode("ascii"), flush=True)


class BasePattern(ABC):

    @abstractmethod
    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        pass


class SequentialPattern(BasePattern):
    """Executes sub-agents sequentially to avoid local LLM hardware bottlenecks."""

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        trace_id = f"tr_{uuid.uuid4().hex[:8]}"
        trace_steps: list[TraceStep] = []
        step_counter = 1

        _print_trace(
            f"\n\033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m "
            f"Starting sequential pipeline for: '{request.user_query}'"
        )

        workers = request.subagents if request.subagents else ["rag-retriever"]
        primary_id = request.primary_agent or "rag-presenter"

        for worker_id in workers:
            now = datetime.now(timezone.utc).isoformat()
            _print_trace(
                f" ├── [{step_counter}] Executing sub-agent "
                f"'\033[93m{worker_id}\033[0m'..."
            )

            try:
                if worker_id == "rag-retriever":
                    _ = interface.run_agent_turn(
                        worker_id, request.user_query, request.parameters
                    )
                else:
                    worker_prompt = (
                        f"Task: '{request.user_query}'. Parameters: {request.parameters}"
                    )
                    _ = interface.run_agent_turn(worker_id, worker_prompt)

                trace_steps.append(
                    TraceStep(
                        step_number=step_counter,
                        agent_id=worker_id,
                        phase="SUBAGENT_EXECUTION",
                        status="SUCCESS",
                        details=f"Executed worker '{worker_id}' successfully",
                        timestamp=now,
                    )
                )
            except Exception as exc:
                err_msg = str(exc)
                _print_trace(
                    f" │   \033[91m[ERROR]\033[0m Worker '{worker_id}' failed: {err_msg}"
                )
                trace_steps.append(
                    TraceStep(
                        step_number=step_counter,
                        agent_id=worker_id,
                        phase="SUBAGENT_EXECUTION",
                        status="ERROR",
                        details=f"Sub-agent '{worker_id}' raised an exception",
                        error_reason=err_msg,
                        timestamp=now,
                    )
                )
            step_counter += 1

        now = datetime.now(timezone.utc).isoformat()
        _print_trace(f" ├── [{step_counter}] Inspecting scratchpad barrier...")
        scratchpad_entry = interface.read_latest_subagent_scratchpad()
        status = (
            str(scratchpad_entry.get("status") or "success")
            if scratchpad_entry
            else "no_context_found"
        )

        trace_steps.append(
            TraceStep(
                step_number=step_counter,
                agent_id="scratchpad",
                phase="SCRATCHPAD_BARRIER",
                status=status,
                details="Retrieved latest sub-agent payload from scratchpad",
                timestamp=now,
            )
        )
        step_counter += 1

        now = datetime.now(timezone.utc).isoformat()
        _print_trace(
            f" ├── [{step_counter}] Executing primary agent "
            f"'\033[95m{primary_id}\033[0m'..."
        )

        primary_prompt = (
            f"User request: '{request.user_query}'. "
            "Inspect scratchpad using read_agent_scratchpad('latest_subagent_result') "
            "and synthesize the final output."
        )
        final_answer = interface.run_agent_turn(primary_id, primary_prompt)

        trace_steps.append(
            TraceStep(
                step_number=step_counter,
                agent_id=primary_id,
                phase="PRIMARY_SYNTHESIS",
                status="SUCCESS",
                details=f"Primary agent '{primary_id}' completed response",
                timestamp=now,
            )
        )

        _print_trace(f" \033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m Pipeline complete.\n")

        return OrchestrationResponse(
            trace_id=trace_id,
            pattern="sequential",
            query=request.user_query,
            status=status,
            final_answer=final_answer,
            result_payload=scratchpad_entry.get("payload") if scratchpad_entry else None,
            execution_trace=trace_steps,
        )


class FanOutPattern(BasePattern):

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        seq = SequentialPattern()
        res = seq.execute(request)
        res.pattern = "fanout"
        return res


class RouterPattern(BasePattern):

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        seq = SequentialPattern()
        res = seq.execute(request)
        res.pattern = "router"
        return res
