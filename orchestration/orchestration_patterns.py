"""Execution strategies for multi-subagent orchestration workflows."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import re
import time
import uuid

from orchestration import orchestration_interface as interface
from orchestration.orchestration_schemas import (
    OrchestrationRequest,
    OrchestrationResponse,
    TraceStep,
)
from orchestration.orchestration_run_results import run_results
from orchestration.codebuilder_run_state import codebuilder_run_state
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


def _single_code_block(response: str) -> str | None:
    """Return one complete fenced code block; avoid guessing from partial snippets."""
    blocks = [
        match.group(1)
        for match in re.finditer(r"```[^\r\n`]*\r?\n([\s\S]*?)```", response or "")
    ]
    return blocks[0] if len(blocks) == 1 and blocks[0].strip() else None


def _registered_tool(name: str):
    from core_engine import tool_catalog

    if name not in tool_catalog.REGISTRY:
        tool_catalog.load_tools()
    entry = tool_catalog.REGISTRY.get(name)
    if entry is None:
        raise RuntimeError(f"Required CodeBuilder tool '{name}' is not registered.")
    return entry["function"]


def _preview_editor_handoff(trace_id: str, agent_id: str, content: str) -> None:
    started = time.perf_counter()
    telemetry_bus.log_event(
        trace_id,
        "TOOL_CALL_START",
        agent_id,
        "preview_editor_code",
        {"tool_name": "preview_editor_code"},
    )
    try:
        preview_editor_code = _registered_tool("preview_editor_code")

        with telemetry_bus.agent_context(trace_id, agent_id):
            preview_editor_code(content)
    except Exception:
        telemetry_bus.log_event(
            trace_id,
            "TOOL_CALL_END",
            "preview_editor_code",
            agent_id,
            {
                "tool_name": "preview_editor_code",
                "status": "error",
                "duration_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        raise
    telemetry_bus.log_event(
        trace_id,
        "TOOL_CALL_END",
        "preview_editor_code",
        agent_id,
        {
            "tool_name": "preview_editor_code",
            "status": "success",
            "duration_ms": int((time.perf_counter() - started) * 1000),
        },
    )


def _capture_missing_code_handoff(
    trace_id: str, agent_id: str, task_type: str, worker_result: str
) -> None:
    payload = {
        "handoff_source": "orchestrator_fallback",
        "reason": "The sub-agent returned without writing its required scratchpad handoff.",
        "agent_response": (worker_result or "")[:12_000],
    }
    if len(worker_result or "") > 12_000:
        payload["agent_response_truncated"] = True

    started = time.perf_counter()
    telemetry_bus.log_event(
        trace_id,
        "TOOL_CALL_START",
        agent_id,
        "write_agent_scratchpad",
        {"tool_name": "write_agent_scratchpad"},
    )
    try:
        write_scratchpad = _registered_tool("write_agent_scratchpad")
        with telemetry_bus.agent_context(trace_id, agent_id):
            write_scratchpad(
                subagent_id=agent_id,
                task_type=task_type,
                status="error",
                payload=payload,
            )
    except Exception:
        telemetry_bus.log_event(
            trace_id,
            "TOOL_CALL_END",
            "write_agent_scratchpad",
            agent_id,
            {
                "tool_name": "write_agent_scratchpad",
                "status": "error",
                "duration_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        raise
    telemetry_bus.log_event(
        trace_id,
        "TOOL_CALL_END",
        "write_agent_scratchpad",
        agent_id,
        {
            "tool_name": "write_agent_scratchpad",
            "status": "success",
            "duration_ms": int((time.perf_counter() - started) * 1000),
        },
    )


def _squad_for_request(request: OrchestrationRequest) -> str | None:
    if request.squad_id:
        squad = get_squad(request.squad_id)
        if squad is None:
            raise ValueError(f"Unknown registered squad: {request.squad_id}")
        request.primary_agent = squad["primary_agent"]
        if request.workflow_action == "all":
            request.subagents = list(squad["subagents"])
        elif request.squad_id == "code-squad":
            request.subagents = {
                "plan": [],
                "build": ["code-builder", "tester", "code-troubleshooter"],
                "troubleshoot": ["code-troubleshooter"],
            }[request.workflow_action]
        else:
            raise ValueError(
                "Plan, Build, and Troubleshoot actions are only available for code-squad."
            )
        return request.squad_id
    if request.workflow_action != "all":
        raise ValueError("A registered code-squad is required for this workflow action.")
    return get_squad_id_for_primary_agent(request.primary_agent)


class BasePattern(ABC):
    @abstractmethod
    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        pass


class SequentialPattern(BasePattern):
    """Executes sub-agents sequentially to avoid local LLM hardware bottlenecks."""

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        trace_id = request.trace_id or f"tr_{uuid.uuid4().hex}"
        request.trace_id = trace_id
        squad_id = _squad_for_request(request)

        started = time.perf_counter()
        telemetry_bus.log_event(
            trace_id,
            "RUN_STARTED",
            "orchestrator",
            squad_id or request.primary_agent,
            {"squad_id": squad_id or "unregistered", "pattern": request.pattern},
        )
        _print_trace(
            f"\n\033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m "
            "Starting sequential pipeline."
        )

        trace_steps: list[TraceStep] = []
        step_counter = 1
        primary_id = request.primary_agent or "rag-presenter"
        primary_only = request.workflow_action == "plan" and squad_id == "code-squad"
        should_plan = (
            squad_id == "code-squad"
            and request.workflow_action in {"build", "all"}
        )
        workers = (
            []
            if primary_only
            else request.subagents if request.subagents else ["rag-retriever"]
        )
        code_worker_ids = {
            "code-builder",
            "tester",
            "code-troubleshooter",
        }
        implementation_plan = ""
        metrics_attempted = False
        try:
            if should_plan:
                now = datetime.now(timezone.utc).isoformat()
                _print_trace(
                    f" ├── [{step_counter}] Planning implementation with "
                    f"'\033[95m{primary_id}\033[0m'..."
                )
                telemetry_bus.log_event(
                    trace_id, "AGENT_MESSAGE", "orchestrator", primary_id,
                    {"summary": "Implementation plan started", "status": "running"},
                )
                plan_prompt = (
                    f"User request: '{request.user_query}'. "
                    "Create a concise, evidence-based implementation plan for the "
                    "Code Builder. Follow only the user's exact request; do not add "
                    "features or choose an unstated framework. Include target files, "
                    "the Python implementation steps, and focused verification steps. "
                    "Do not edit files or claim tests were run."
                )
                editor_code = request.parameters.get("editor_code")
                if isinstance(editor_code, str) and editor_code:
                    editor_path = request.parameters.get("editor_path") or "unsaved editor buffer"
                    plan_prompt += (
                        f"\n\nCurrent editor source ({editor_path}):\n"
                        f"```python\n{editor_code}\n```"
                    )
                implementation_plan = str(
                    interface.run_agent_turn(
                        primary_id,
                        plan_prompt,
                        {
                            key: value
                            for key, value in request.parameters.items()
                            if key != "editor_code"
                        },
                        trace_id=trace_id,
                    )
                    or ""
                ).strip()
                trace_steps.append(
                    TraceStep(
                        step_number=step_counter,
                        agent_id=primary_id,
                        phase="IMPLEMENTATION_PLANNING",
                        status="SUCCESS" if implementation_plan else "ERROR",
                        details="Created implementation plan for the Code Builder"
                        if implementation_plan
                        else "Planner returned an empty implementation plan",
                        timestamp=now,
                    )
                )
                telemetry_bus.log_event(
                    trace_id, "AGENT_MESSAGE", primary_id, "orchestrator",
                    {
                        "summary": "Implementation plan completed",
                        "status": "success" if implementation_plan else "error",
                    },
                )
                step_counter += 1
                if not implementation_plan:
                    raise RuntimeError(
                        "The Code Planner returned an empty implementation plan; "
                        "the Code Builder was not started."
                    )
            for worker_id in workers:
                worker_is_retest = False
                if worker_id == "tester":
                    handoff_history = codebuilder_run_state.get_handoffs(trace_id)
                    tester_positions = [
                        index
                        for index, handoff in enumerate(handoff_history)
                        if handoff.get("subagent_id") == "tester"
                    ]
                    troubleshooter_positions = [
                        index
                        for index, handoff in enumerate(handoff_history)
                        if handoff.get("subagent_id") == "code-troubleshooter"
                    ]
                    latest_tester_position = (
                        tester_positions[-1] if tester_positions else -1
                    )
                    latest_troubleshooter_position = (
                        troubleshooter_positions[-1]
                        if troubleshooter_positions
                        else -1
                    )
                    worker_is_retest = (
                        latest_troubleshooter_position > latest_tester_position
                        and handoff_history[latest_troubleshooter_position].get("status")
                        == "success"
                    )
                    if tester_positions and not worker_is_retest:
                        trace_steps.append(
                            TraceStep(
                                step_number=step_counter,
                                agent_id=worker_id,
                                phase="SUBAGENT_EXECUTION",
                                status="SUCCESS",
                                details="Skipped duplicate testing because troubleshooting did not produce a newer implementation",
                                timestamp=datetime.now(timezone.utc).isoformat(),
                            )
                        )
                        step_counter += 1
                        continue
                    builder_handoff = next(
                        (
                            handoff for handoff in reversed(handoff_history)
                            if handoff.get("subagent_id") == "code-builder"
                        ),
                        None,
                    )
                    if (
                        not worker_is_retest
                        and (
                            not builder_handoff
                            or builder_handoff.get("status") != "success"
                        )
                    ):
                        telemetry_bus.log_event(
                            trace_id,
                            "AGENT_MESSAGE",
                            "orchestrator",
                            worker_id,
                            {
                                "summary": "Code Tester skipped because builder did not succeed",
                                "status": "nothing_found",
                            },
                        )
                        trace_steps.append(
                            TraceStep(
                                step_number=step_counter,
                                agent_id=worker_id,
                                phase="SUBAGENT_EXECUTION",
                                status="SUCCESS",
                                details="Skipped testing because the builder did not report a successful implementation",
                                timestamp=datetime.now(timezone.utc).isoformat(),
                            )
                        )
                        step_counter += 1
                        continue
                if worker_id == "code-troubleshooter" and "tester" in workers:
                    upstream_errors = [
                        handoff
                        for handoff in codebuilder_run_state.get_handoffs(trace_id)
                        if handoff.get("status") == "error"
                        and handoff.get("subagent_id") != "code-troubleshooter"
                    ]
                    if not upstream_errors:
                        telemetry_bus.log_event(
                            trace_id,
                            "AGENT_MESSAGE",
                            "orchestrator",
                            worker_id,
                            {
                                "summary": "Code Troubleshooter skipped because no upstream error was reported",
                                "status": "success",
                            },
                        )
                        trace_steps.append(
                            TraceStep(
                                step_number=step_counter,
                                agent_id=worker_id,
                                phase="SUBAGENT_EXECUTION",
                                status="SUCCESS",
                                details="Skipped error triage because no upstream worker reported an error",
                                timestamp=datetime.now(timezone.utc).isoformat(),
                            )
                        )
                        step_counter += 1
                        continue
                now = datetime.now(timezone.utc).isoformat()
                _print_trace(
                    f" ├── [{step_counter}] Executing sub-agent "
                    f"'\033[93m{worker_id}\033[0m'..."
                )
                telemetry_bus.log_event(
                    trace_id, "AGENT_MESSAGE", "orchestrator", worker_id,
                    {"summary": "Sub-agent phase started", "status": "running"},
                )
                try:
                    if worker_id == "rag-retriever":
                        interface.run_agent_turn(
                            worker_id,
                            request.user_query,
                            request.parameters,
                            trace_id=trace_id,
                        )
                    else:
                        parameters = {
                            key: value
                            for key, value in request.parameters.items()
                            if key != "editor_code"
                        }
                        worker_prompt = (
                            f"Task: '{request.user_query}'. Parameters: {parameters}"
                        )
                        if worker_id == "code-builder" and implementation_plan:
                            worker_prompt += (
                                "\n\nCode Planner implementation plan (follow this "
                                "plan unless repository evidence shows a specific "
                                "conflict; explain any deviation):\n"
                                + implementation_plan[:12_000]
                            )
                        if worker_id in code_worker_ids:
                            task_type = {
                                "code-builder": "code_build",
                                "tester": "code_test",
                                "code-troubleshooter": "code_troubleshooting",
                            }[worker_id]
                            worker_prompt += (
                                "\n\nBefore finishing, you MUST call "
                                "write_agent_scratchpad exactly once with your agent ID, "
                                f"task_type `{task_type}`, an accurate status (`success`, "
                                "`nothing_found`, or `error`), and a concise factual "
                                "payload. Do this for every outcome, including missing "
                                "evidence or tool failures. Do not mark an unverified fix "
                                "as successful. Use the exact canonical sub-agent ID "
                                f"`{worker_id}`. The scratchpad tool response confirms the "
                                "write; do not read the scratchpad file or call the tool "
                                "again afterward."
                            )
                        if worker_id == "tester":
                            builder_handoff = next(
                                (
                                    handoff
                                    for handoff in reversed(
                                        codebuilder_run_state.get_handoffs(trace_id)
                                    )
                                    if handoff.get("subagent_id") == "code-builder"
                                ),
                                None,
                            )
                            preview = codebuilder_run_state.get_preview(trace_id)
                            source = (
                                preview.get("content")
                                if preview is not None
                                else (
                                    request.parameters.get("editor_code")
                                    if not request.parameters.get("editor_path")
                                    else None
                                )
                            )
                            worker_prompt += (
                                "\n\nCode Builder handoff (JSON):\n"
                                + json.dumps(builder_handoff or {}, ensure_ascii=False)[:8_000]
                                + "\n\nTest the builder's actual output. The code plan "
                                "was:\n"
                                + implementation_plan[:8_000]
                            )
                            if worker_is_retest:
                                previous_test = next(
                                    (
                                        handoff
                                        for handoff in reversed(
                                            codebuilder_run_state.get_handoffs(trace_id)
                                        )
                                        if handoff.get("subagent_id") == "tester"
                                    ),
                                    {},
                                )
                                troubleshooting = next(
                                    (
                                        handoff
                                        for handoff in reversed(
                                            codebuilder_run_state.get_handoffs(trace_id)
                                        )
                                        if handoff.get("subagent_id")
                                        == "code-troubleshooter"
                                    ),
                                    {},
                                )
                                worker_prompt += (
                                    "\n\nThis is the post-troubleshooting recheck. "
                                    "Use the updated source and verify the prior failure "
                                    "again. Previous tester handoff:\n"
                                    + json.dumps(previous_test, ensure_ascii=False)[:4_000]
                                    + "\nTroubleshooter handoff:\n"
                                    + json.dumps(troubleshooting, ensure_ascii=False)[:4_000]
                                )
                            if request.parameters.get("editor_path"):
                                worker_prompt += (
                                    "\n\nThe builder targets the saved workspace file "
                                    f"`{request.parameters['editor_path']}`. Read that file "
                                    "now to test the builder's latest saved content; the "
                                    "editor buffer included at workflow start may be stale."
                                )
                            if isinstance(source, str) and source:
                                worker_prompt += (
                                    "\n\nCurrent editor source to verify "
                                    "(do not treat this as permission to edit):\n"
                                    f"```python\n{source}\n```"
                                )
                        if worker_id == "code-troubleshooter" and "tester" in workers:
                            upstream_errors = [
                                handoff
                                for handoff in codebuilder_run_state.get_handoffs(trace_id)
                                if handoff.get("status") == "error"
                                and handoff.get("subagent_id") != worker_id
                            ]
                            worker_prompt += (
                                "\n\nUpstream code-agent errors to triage (JSON):\n"
                                + json.dumps(upstream_errors, ensure_ascii=False)[:12_000]
                                + "\nUse the tester's observed failure as evidence. Make "
                                "a minimal evidence-based fix when the cause is confirmed; "
                                "do not claim a fix is verified unless you actually rerun "
                                "a focused check. Do not invent unrelated functionality."
                            )
                        editor_code = request.parameters.get("editor_code")
                        editor_path = request.parameters.get("editor_path")
                        if isinstance(editor_code, str) and editor_code and (
                            worker_id != "tester"
                            or not isinstance(editor_path, str)
                            or not editor_path
                        ):
                            editor_path = request.parameters.get("editor_path") or "unsaved editor buffer"
                            worker_prompt += (
                                f"\n\nCurrent CodeBuilder editor buffer ({editor_path}). "
                                "Treat the following as the exact current source; do not assume "
                                "it has been saved to the workspace:\n"
                                f"```python\n{editor_code}\n```"
                            )
                        if worker_id == "code-troubleshooter" and editor_code:
                            worker_prompt += (
                                "\n\nDo not assume the editor buffer was executed. The "
                                "workflow does not automatically run it. For an HTTP 404, "
                                "inspect the relevant source with inspect_http_routes and "
                                "compare the actual declared route with the exact requested "
                                "URL and method if provided. A generic 404 without a URL, "
                                "method, or request evidence is insufficient to identify a "
                                "fix: make no edits and ask for the missing details. Never "
                                "add unrelated features or replace application behavior. "
                                "Do not run a server, start a listener, or run the entire "
                                "editor buffer to claim an HTTP route was tested. Use "
                                "run_python_code only for a safe, focused, relevant snippet "
                                "or test, and report its actual result."
                                + (
                                    "The buffer is saved at the provided editor path; after "
                                    "a confirmed, relevant fix, preview and write only the "
                                    "affected file so the applied-change event reloads it."
                                    if request.parameters.get("editor_path")
                                    else "After correcting a confirmed issue in the active "
                                    "buffer, call "
                                    "preview_editor_code with the complete corrected buffer "
                                    "so it is shown in the user's editor; this preview does "
                                    "not save the file."
                                )
                            )
                        elif worker_id == "code-builder" and editor_code:
                            worker_prompt += (
                                "\n\nIf the requested change targets this editor buffer and "
                                + (
                                    "a saved workspace path was not provided, you MUST call "
                                    "preview_editor_code with the complete resulting buffer "
                                    "and return exactly one complete fenced code block as "
                                    "a reliable fallback for the editor handoff. Do not "
                                    "report success before the preview tool succeeds."
                                    if not request.parameters.get("editor_path")
                                    else "a saved workspace path was provided, use the "
                                    "workspace file tools and preview/write that file. "
                                    "If the user is asking to edit the active buffer, also "
                                    "call preview_editor_code with the complete final buffer."
                                )
                            )
                        worker_result = interface.run_agent_turn(
                            worker_id, worker_prompt, trace_id=trace_id
                        )
                        if worker_id in {"code-builder", "code-troubleshooter"}:
                            if (
                                codebuilder_run_state.get_editor_code(trace_id) is not None
                                and codebuilder_run_state.get_preview(trace_id) is None
                            ):
                                proposed_code = _single_code_block(worker_result)
                                if proposed_code is not None and (
                                    not isinstance(editor_code, str)
                                    or proposed_code != editor_code
                                ):
                                    _preview_editor_handoff(
                                        trace_id, worker_id, proposed_code
                                    )
                            handoff = codebuilder_run_state.get_handoff(trace_id)
                            if not handoff or handoff.get("subagent_id") != worker_id:
                                _capture_missing_code_handoff(
                                    trace_id,
                                    worker_id,
                                    "code_build"
                                    if worker_id == "code-builder"
                                    else "code_troubleshooting",
                                    worker_result,
                                )
                        elif worker_id == "tester":
                            handoff = codebuilder_run_state.get_handoff(trace_id)
                            if not handoff or handoff.get("subagent_id") != worker_id:
                                _capture_missing_code_handoff(
                                    trace_id,
                                    worker_id,
                                    "code_test",
                                    worker_result,
                                )

                    worker_handoff = (
                        codebuilder_run_state.get_handoff(trace_id)
                        if worker_id in code_worker_ids
                        else None
                    )
                    worker_status = (
                        str(worker_handoff.get("status") or "error")
                        if worker_handoff
                        and worker_handoff.get("subagent_id") == worker_id
                        else "success"
                    )
                    trace_steps.append(
                        TraceStep(
                            step_number=step_counter,
                            agent_id=worker_id,
                            phase="SUBAGENT_EXECUTION",
                            status="ERROR" if worker_status == "error" else "SUCCESS",
                            details=(
                                f"Worker '{worker_id}' reported status '{worker_status}'"
                            ),
                            timestamp=now,
                        )
                    )
                    telemetry_bus.log_event(
                        trace_id, "AGENT_MESSAGE", worker_id, "orchestrator",
                        {
                            "summary": "Sub-agent phase completed",
                            "status": worker_status,
                        },
                    )
                    if (
                        worker_id == "code-troubleshooter"
                        and worker_status == "success"
                    ):
                        workers.append("tester")
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
                    telemetry_bus.log_event(
                        trace_id, "ERROR", worker_id, "orchestrator",
                        {"error": "Sub-agent execution failed", "status": "error"},
                    )
                    if worker_id in code_worker_ids:
                        task_type = {
                            "code-builder": "code_build",
                            "tester": "code_test",
                            "code-troubleshooter": "code_troubleshooting",
                        }[worker_id]
                        codebuilder_run_state.save_handoff(
                            trace_id,
                            worker_id,
                            task_type,
                            "error",
                            {
                                "handoff_source": "orchestrator_exception",
                                "error": err_msg[:2_000],
                            },
                        )
                step_counter += 1

            now = datetime.now(timezone.utc).isoformat()
            _print_trace(f" ├── [{step_counter}] Inspecting scratchpad barrier...")
            if squad_id == "code-squad" and workers:
                scratchpad_entry = codebuilder_run_state.get_handoff(trace_id) or {}
                if scratchpad_entry.get("subagent_id") not in workers:
                    scratchpad_entry = {}
                scratchpad_snapshot = {}
                if scratchpad_entry:
                    handoff_history = [
                        handoff
                        for handoff in codebuilder_run_state.get_handoffs(trace_id)
                        if handoff.get("subagent_id") in workers
                    ]
                    scratchpad_snapshot = {
                        "latest_subagent_result": scratchpad_entry,
                        "subagent_history": handoff_history,
                    }
            else:
                scratchpad_entry = (
                    interface.read_latest_subagent_scratchpad() if workers else {}
                )
                scratchpad_snapshot = (
                    interface.read_scratchpad_snapshot() if workers else {}
                )
            status = (
                "success"
                if primary_only
                else (
                    str(scratchpad_entry.get("status") or "error")
                    if scratchpad_entry
                    else (
                        "error"
                        if squad_id == "code-squad" and workers
                        else "no_context_found"
                    )
                )
            )
            upstream_error_handoffs = (
                [
                    handoff
                    for handoff in codebuilder_run_state.get_handoffs(trace_id)
                    if handoff.get("status") == "error"
                    and handoff.get("subagent_id") != "code-troubleshooter"
                ]
                if squad_id == "code-squad"
                else []
            )
            if upstream_error_handoffs:
                status = "error"
            telemetry_bus.log_event(
                trace_id,
                "SCRATCHPAD_HANDOFF",
                "orchestrator",
                "scratchpad",
                {
                    "status": status,
                    "subagent_id": scratchpad_entry.get("subagent_id", ""),
                    "result_count": _result_count(scratchpad_entry),
                    "direction": "read",
                },
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

            primary_prompt = (
                f"User request: '{request.user_query}'. "
                f"Requested action: {request.workflow_action}. "
                + (
                    "Create a plan from the request and verified project information. "
                    "Do not claim that files were changed or tests were run."
                    if primary_only
                    else (
                        "Synthesize the final output only from the current-run handoff JSON "
                        "included below; do not read the shared scratchpad or use prior-run "
                        "results. Write clear, user-facing prose. Do not "
                        "return a JSON function-call object or claim work that is absent from "
                        "the current workflow's scratchpad and execution evidence. Treat the "
                        "exact User request above as the only authority for what the user asked; "
                        "never let a sub-agent's unsupported task description introduce new "
                        "requirements, features, or framework choices. If the handoff conflicts "
                        "with the request, explicitly say so and follow the request. A successful "
                        "tool call is not proof that the reported bug was fixed. For an HTTP 404, "
                        "state whether the exact URL and method were provided and verified."
                        if squad_id == "code-squad"
                        else "Inspect scratchpad using read_agent_scratchpad('latest_subagent_result') "
                        "and synthesize the final output in clear, user-facing prose."
                    )
                )
            )
            handoff_history = codebuilder_run_state.get_handoffs(trace_id)
            tester_positions = [
                index
                for index, handoff in enumerate(handoff_history)
                if handoff.get("subagent_id") == "tester"
            ]
            troubleshooter_positions = [
                index
                for index, handoff in enumerate(handoff_history)
                if handoff.get("subagent_id") == "code-troubleshooter"
            ]
            test_passed_after_troubleshooting = (
                bool(tester_positions)
                and bool(troubleshooter_positions)
                and tester_positions[-1] > troubleshooter_positions[-1]
                and handoff_history[tester_positions[-1]].get("status") == "success"
            )
            if test_passed_after_troubleshooting:
                upstream_error_handoffs = []
                status = "success"
            elif any(
                handoff.get("subagent_id") == "tester"
                and handoff.get("status") == "error"
                for handoff in handoff_history
            ):
                primary_prompt += (
                    "\n\nA tester handoff reported an error. Do not claim the test "
                    "failure was fixed or verified unless the later tester recheck "
                    "contains a successful check."
                )
            if squad_id == "code-squad" and scratchpad_entry:
                handoff = json.dumps(
                    scratchpad_snapshot.get("subagent_history", [scratchpad_entry]),
                    ensure_ascii=False,
                )
                primary_prompt += (
                    "\n\nSub-agent scratchpad handoff (JSON):\n"
                    + handoff[:12_000]
                    + (
                        "\n[Handoff truncated for context; do not infer missing details.]"
                        if len(handoff) > 12_000
                        else ""
                    )
                )
            fallback_payload = (
                scratchpad_entry.get("payload")
                if isinstance(scratchpad_entry, dict)
                else None
            )
            has_fallback_handoff = (
                isinstance(fallback_payload, dict)
                and fallback_payload.get("handoff_source") == "orchestrator_fallback"
            )
            blocked_change_reason = codebuilder_run_state.code_change_block_reason(
                trace_id
            )
            if blocked_change_reason:
                final_answer = (
                    "No code change was applied because the 404 request is missing "
                    "the URL/path or HTTP method needed to identify the failing route. "
                    "I will not infer an unrelated feature request. "
                    + blocked_change_reason
                    + " To continue, provide the exact URL/path, HTTP method, expected "
                    "behavior, and relevant request/server logs."
                )
                status = "error"
            elif has_fallback_handoff:
                agent_response = str(fallback_payload.get("agent_response") or "").strip()
                final_answer = (
                    "The Code Development sub-agent returned without writing its "
                    "required scratchpad handoff. Its response was saved with error "
                    "status for review; no changes or checks are verified by this "
                    "handoff."
                    + (f"\n\nSub-agent response:\n{agent_response}" if agent_response else "")
                )
                status = "error"
            elif squad_id == "code-squad" and workers and not scratchpad_entry:
                final_answer = (
                    "The Code Development sub-agent did not provide a current-run "
                    "scratchpad handoff. No fix is verified, and no completion claim "
                    "should be inferred."
                )
                status = "error"
            elif (
                squad_id == "code-squad"
                and workers
                and scratchpad_entry.get("status") != "success"
            ):
                status = str(scratchpad_entry.get("status") or "error")
                if status == "nothing_found":
                    if scratchpad_entry.get("subagent_id") == "tester":
                        tester_payload = fallback_payload or {}
                        summary = str(tester_payload.get("summary") or "").strip()
                        final_answer = (
                            "The Code Builder completed, but the Code Tester could not "
                            "run a relevant check from the available evidence. No test "
                            "pass is claimed."
                        )
                        if summary:
                            final_answer += f"\n\nTester report: {summary}"
                    else:
                        final_answer = (
                            "The Code Development sub-agent could not confirm a code-level "
                            "cause from the available evidence. No code change or successful "
                            "check is verified, and I will not infer a feature request from "
                            "the sub-agent's assumptions."
                        )
                    if request.workflow_action == "troubleshoot" and scratchpad_entry.get("subagent_id") != "tester":
                        final_answer += (
                            " To continue, provide the exact error and steps to reproduce, "
                            "what you expected to happen, and the relevant file or request "
                            "details. For a server 404, include the exact URL/path, HTTP "
                            "method, expected response, and relevant request/server logs."
                        )
                    else:
                        final_answer += (
                            " To continue the build, state the specific change you want "
                            "and the target file or behavior."
                        )
                else:
                    final_answer = (
                        "The Code Development sub-agent reported an error. No fix or "
                        "successful check is verified."
                    )
            else:
                now = datetime.now(timezone.utc).isoformat()
                _print_trace(
                    f" ├── [{step_counter}] Executing primary agent "
                    f"'\033[95m{primary_id}\033[0m'..."
                )
                telemetry_bus.log_event(
                    trace_id, "AGENT_MESSAGE", "orchestrator", primary_id,
                    {"summary": "Primary synthesis started", "status": "running"},
                )
                final_answer = interface.run_agent_turn(
                    primary_id, primary_prompt, trace_id=trace_id
                )
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
                telemetry_bus.log_event(
                    trace_id, "AGENT_MESSAGE", primary_id, "orchestrator",
                    {"summary": "Primary synthesis completed", "status": "success"},
                )

            if (
                any(step.status == "ERROR" for step in trace_steps)
                and not test_passed_after_troubleshooting
            ):
                status = "error"
            duration_ms = int((time.perf_counter() - started) * 1000)
            if squad_id:
                metrics_attempted = True
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
            run_results.save(
                trace_id,
                {
                    **response.model_dump(),
                    "squad_id": squad_id,
                    "scratchpad_snapshot": scratchpad_snapshot,
                },
            )
            telemetry_bus.log_event(
                trace_id, "RUN_COMPLETE", "orchestrator", squad_id or primary_id,
                {"status": status, "duration_ms": duration_ms},
            )
            telemetry_bus.finish_trace(trace_id)
            _print_trace(
                f" \033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m Pipeline complete.\n"
            )

            return response
        except Exception:
            duration_ms = int((time.perf_counter() - started) * 1000)
            telemetry_bus.log_event(
                trace_id, "ERROR", "orchestrator", squad_id or primary_id,
                {"error": "Orchestration execution failed", "status": "error"},
            )
            if squad_id and not metrics_attempted:
                metrics_attempted = True
                record_squad_run(squad_id, False, duration_ms)
            telemetry_bus.log_event(
                trace_id, "RUN_COMPLETE", "orchestrator", squad_id or primary_id,
                {"status": "error", "duration_ms": duration_ms},
            )
            telemetry_bus.finish_trace(trace_id)
            raise


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
