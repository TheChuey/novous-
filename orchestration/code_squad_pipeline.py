"""Deterministic Code Development Squad pipeline for the CodeBuilder editor.

Agents only write text and one fenced Python block. The orchestrator applies that
code to the editor buffer, runs it, and records factual handoffs, so a small local
model never has to produce a large tool-call argument to deliver its work.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
import time
from typing import Any
import uuid

from agentMemory import interface as memory_interface
from orchestration import orchestration_interface as interface
from orchestration.code_handoffs import TASK_TYPE_BY_AGENT, execution_evidence
from orchestration.codebuilder_run_state import codebuilder_run_state
from orchestration.orchestration_run_results import run_results
from orchestration.orchestration_schemas import (
    OrchestrationRequest,
    OrchestrationResponse,
    TraceStep,
)
from orchestration.orchestration_telemetry import telemetry_bus
from orchestration.squad_registry import get_squad, record_squad_run

SQUAD_ID = "code-squad"
MAX_FIX_ATTEMPTS = 3
SHARED_NOTES = 3
SHARED_NOTES_CHARS = 2_000
TEST_TIMEOUT_SECONDS = 15.0
_TEST_NAME = "__codebuilder_test__"
_ACTION_ALIASES = {"troubleshoot": "fix"}
STEP_AGENTS = {
    "plan": "code-planer",
    "build": "code-builder",
    "test": "tester",
    "fix": "code-troubleshooter",
}


class PipelineCancelled(Exception):
    pass


@dataclass
class RunContext:
    trace_id: str
    request: OrchestrationRequest
    code: str
    plan: str = ""
    model: str | None = None
    last_test: dict[str, Any] | None = None
    steps: list[TraceStep] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def query(self) -> str:
        return self.request.user_query


# --- code extraction ---------------------------------------------------------
def fenced_code_blocks(response: str) -> list[tuple[str, str]]:
    return [
        ((match.group(1) or "").strip().split(" ", 1)[0].lower(), match.group(2))
        for match in re.finditer(r"```([^\r\n`]*)\r?\n([\s\S]*?)```", response or "")
        if match.group(2).strip()
    ]


def extract_python_block(response: str) -> str | None:
    """Return the module the agent produced: the single block, else the largest Python block."""
    blocks = fenced_code_blocks(response)
    if len(blocks) == 1:
        return blocks[0][1]
    python_blocks = [
        content for language, content in blocks if language in {"python", "py", "python3"}
    ]
    if not python_blocks:
        return None
    return max(python_blocks, key=len)


# --- step bookkeeping --------------------------------------------------------
def _check_cancel(ctx: RunContext) -> None:
    if codebuilder_run_state.is_cancelled(ctx.trace_id):
        raise PipelineCancelled()


def _step_status(ctx: RunContext, step: str, status: str, attempt: int = 0, summary: str = "") -> None:
    telemetry_bus.log_event(
        ctx.trace_id, "STEP_STATUS", "orchestrator", STEP_AGENTS.get(step, step),
        {"step": step, "status": status, "attempt": attempt, "summary": summary},
    )


def _record(ctx: RunContext, step: str, status: str, details: str, error: str | None = None) -> None:
    ctx.steps.append(
        TraceStep(
            step_number=len(ctx.steps) + 1,
            agent_id=STEP_AGENTS.get(step, step),
            phase=step.upper(),
            status=status,
            details=details,
            error_reason=error,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )


def _handoff(ctx: RunContext, agent_id: str, status: str, payload: dict[str, Any]) -> None:
    codebuilder_run_state.save_handoff(
        ctx.trace_id, agent_id, TASK_TYPE_BY_AGENT.get(agent_id, "code_plan"), status, payload
    )


def _note(ctx: RunContext, author: str, kind: str, title: str, content: str, status: str = "success") -> None:
    """Record a step on the coding agents' shared scratchpad; never fail the run over it."""
    try:
        memory_interface.post_code_note(author, kind, title, content, run_id=ctx.trace_id)
    except Exception as exc:  # noqa: BLE001 - the scratchpad is a record, not a dependency
        telemetry_bus.log_event(
            ctx.trace_id, "ERROR", "orchestrator", "scratchpad",
            {"error": f"Could not write the code scratchpad: {exc}", "status": "error"},
        )
        return
    telemetry_bus.log_event(
        ctx.trace_id, "SCRATCHPAD_HANDOFF", author, "scratchpad",
        {"status": status, "subagent_id": author, "result_count": 1, "direction": "write"},
    )


def _shared_notes_section() -> str:
    """Notes chat agents or the user left on the code scratchpad, newest first."""
    try:
        notes = memory_interface.read_code_scratchpad(limit=SHARED_NOTES, kind="note")
    except Exception:  # noqa: BLE001
        return ""
    if not notes:
        return ""
    lines = "\n".join(f"- ({note['author']}) {note['title']}: {note['content']}" for note in notes)
    return "\nNotes from other agents on the code scratchpad:\n" + lines[:SHARED_NOTES_CHARS] + "\n"


def _ask_agent(ctx: RunContext, step: str, prompt: str, attempt: int = 0) -> str:
    agent_id = STEP_AGENTS[step]
    _check_cancel(ctx)
    telemetry_bus.log_event(
        ctx.trace_id, "AGENT_STARTED", "orchestrator", agent_id,
        {"agent_id": agent_id, "step": step, "attempt": attempt},
    )
    try:
        reply = interface.run_agent_turn_stream(
            agent_id,
            prompt,
            ctx.trace_id,
            model=ctx.model,
            should_stop=lambda: codebuilder_run_state.is_cancelled(ctx.trace_id),
        )
    except interface.AgentTurnCancelled as exc:
        raise PipelineCancelled() from exc
    telemetry_bus.log_event(
        ctx.trace_id, "AGENT_DONE", agent_id, "orchestrator",
        {"agent_id": agent_id, "step": step, "text": reply},
    )
    return reply


def apply_code(ctx: RunContext, code: str, agent_id: str) -> list[int]:
    """Place agent code in the editor buffer and announce it to the frontend."""
    from tools.code_change_preview import changed_line_numbers

    try:
        lines = changed_line_numbers(ctx.code, code, "after")
    except ValueError:
        lines = []
    codebuilder_run_state.save_preview(ctx.trace_id, code, lines)
    ctx.code = code
    telemetry_bus.log_event(
        ctx.trace_id, "EDITOR_CODE_UPDATE", agent_id, "editor",
        {"content": code, "changed_lines": lines},
    )
    return lines


def _buffer_section(code: str) -> str:
    if not code.strip():
        return "The editor is currently empty."
    return f"Current editor module:\n```python\n{code}\n```"


# --- test harness ------------------------------------------------------------
def _test_harness(code: str) -> tuple[str, int]:
    """Return runnable source that imports the module without running its main guard.

    The ``__name__`` override shares the first line when that is valid, so traceback
    line numbers match the editor. Otherwise it gets its own line (offset 1).
    """
    first = code.splitlines()[0] if code else ""
    override = f"__name__ = {_TEST_NAME!r}"
    # Only simple statements may follow ';' on one line (not def/class/if/@...).
    if first.startswith(("import ", "from ", "#", '"', "'")) and not first.startswith("from __future__"):
        return f"{override}; {code}", 0
    return f"{override}\n{code}", 1


def _run(code: str) -> dict[str, Any]:
    from codebuilder.execution import execute_python_code
    from codebuilder.schemas import CodeExecutionRequest

    result = execute_python_code(
        CodeExecutionRequest(code=code, timeout_seconds=TEST_TIMEOUT_SECONDS)
    )
    return result.model_dump()


def _compile_error(code: str) -> dict[str, Any] | None:
    try:
        compile(code, "editor.py", "exec")
    except SyntaxError as exc:
        message = f"{type(exc).__name__}: {exc.msg} (line {exc.lineno})"
        return {
            "status": "ERROR",
            "stdout": "",
            "stderr": message + ("\n" + exc.text if exc.text else ""),
            "return_code": 1,
            "timed_out": False,
            "diagnostics": [
                {"path": None, "line": exc.lineno, "column": exc.offset, "message": message, "severity": "error"}
            ],
        }
    return None


def _publish_execution(ctx: RunContext, result: dict[str, Any], offset: int, agent_id: str) -> dict[str, Any]:
    """Map diagnostics back to editor lines, store the result, and notify the UI."""
    total = len(ctx.code.splitlines())
    diagnostics = []
    for item in result.get("diagnostics") or []:
        item = dict(item)
        line = item.get("line")
        if isinstance(line, int):
            line -= offset
            item["line"] = line if 0 < line <= total else None
        diagnostics.append(item)
    result = {**result, "diagnostics": diagnostics}
    codebuilder_run_state.save_execution(ctx.trace_id, ctx.code, result, allow_non_editor_source=True)
    passed = result.get("status") == "SUCCESS"
    telemetry_bus.log_event(
        ctx.trace_id, "EDITOR_CODE_EXECUTION", agent_id, "editor",
        {
            "status": "success" if passed else "error",
            "diagnostic_lines": sorted({d["line"] for d in diagnostics if d.get("line")})[:120],
        },
    )
    return result


# --- steps -------------------------------------------------------------------
def step_plan(ctx: RunContext) -> None:
    _step_status(ctx, "plan", "running")
    prompt = (
        f"User request: {ctx.query}\n\n{_buffer_section(ctx.code)}\n{_shared_notes_section()}\n"
        "Write a short implementation plan for a single Python module: the functions "
        "to add or change, what each does, and how the result will be checked. "
        "Do not write the full code."
    )
    ctx.plan = _ask_agent(ctx, "plan", prompt).strip()
    _handoff(ctx, "code-planer", "success" if ctx.plan else "error", {"plan": ctx.plan[:4_000]})
    if ctx.plan:
        _note(ctx, "code-planer", "plan", f"Plan: {ctx.query[:120]}", ctx.plan)
    _record(ctx, "plan", "SUCCESS" if ctx.plan else "ERROR", "Created implementation plan")
    _step_status(ctx, "plan", "success" if ctx.plan else "error")


def step_build(ctx: RunContext) -> bool:
    _step_status(ctx, "build", "running")
    prompt = f"User request: {ctx.query}\n\n{_buffer_section(ctx.code)}\n{_shared_notes_section()}"
    if ctx.plan:
        prompt += f"\nPlan to follow:\n{ctx.plan[:8_000]}\n"
    prompt += (
        "\nReturn the COMPLETE resulting Python module in exactly one ```python block, "
        "then 1-3 short lines saying what you did."
    )
    reply = _ask_agent(ctx, "build", prompt)
    code = extract_python_block(reply)
    if code is None:
        _handoff(ctx, "code-builder", "error", {"summary": "No Python code block in reply.", "reply": reply[:4_000]})
        _note(ctx, "code-builder", "code", "Build failed: no Python code block", reply, "error")
        _record(ctx, "build", "ERROR", "Builder returned no Python code block")
        _step_status(ctx, "build", "error", summary="The builder did not return a Python code block.")
        return False
    lines = apply_code(ctx, code, "code-builder")
    _handoff(ctx, "code-builder", "success", {"summary": "Applied module to editor.", "changed_lines": len(lines)})
    _note(ctx, "code-builder", "code", f"Built module ({len(lines)} lines changed)", reply)
    _record(ctx, "build", "SUCCESS", f"Applied builder code ({len(lines)} changed lines)")
    _step_status(ctx, "build", "success", summary=f"{len(lines)} lines changed")
    return True


def step_test(ctx: RunContext, attempt: int = 0) -> bool:
    _step_status(ctx, "test", "running", attempt)
    agent_id = "tester"
    if not ctx.code.strip():
        ctx.last_test = {"status": "ERROR", "stderr": "The editor is empty; there is nothing to test.", "diagnostics": []}
        _record(ctx, "test", "ERROR", "Nothing to test")
        _step_status(ctx, "test", "error", attempt, "The editor is empty.")
        return False

    result = _compile_error(ctx.code)
    offset = 0
    stage = "syntax check"
    snippet = None
    if result is None:
        harness, offset = _test_harness(ctx.code)
        _check_cancel(ctx)
        result = _run(harness)
        stage = "import smoke test"
        if result.get("status") == "SUCCESS":
            prompt = (
                f"User request: {ctx.query}\n\n{_buffer_section(ctx.code)}\n\n"
                "Write a short Python test snippet that will run directly after this "
                "module's code (its functions and classes are already defined; do not "
                "import it). Use plain assert statements on the module's functions, "
                "with no input(), servers, loops waiting on users, or file writes. "
                "Return exactly one ```python block and nothing else."
            )
            snippet = extract_python_block(_ask_agent(ctx, "test", prompt, attempt))
            if snippet and snippet.strip():
                _check_cancel(ctx)
                result = _run(f"{harness}\n\n# --- tester checks ---\n{snippet}")
                stage = "tester checks"
    result = _publish_execution(ctx, result, offset, agent_id)
    passed = result.get("status") == "SUCCESS"
    ctx.last_test = {**execution_evidence(result), "stage": stage}
    _handoff(ctx, agent_id, "success" if passed else "error", ctx.last_test)
    evidence = json.dumps(ctx.last_test, ensure_ascii=False, indent=2)[:8_000]
    _note(
        ctx, agent_id, "test", f"{stage} {'passed' if passed else 'failed'}",
        f"```json\n{evidence}\n```" + (f"\n\nTester checks:\n```python\n{snippet}\n```" if snippet else ""),
        "success" if passed else "error",
    )
    _record(ctx, "test", "SUCCESS" if passed else "ERROR", f"{stage} {'passed' if passed else 'failed'}")
    _step_status(ctx, "test", "success" if passed else "error", attempt, f"{stage} {'passed' if passed else 'failed'}")
    return passed


def step_fix(ctx: RunContext, attempt: int = 1) -> bool:
    _step_status(ctx, "fix", "running", attempt)
    evidence = json.dumps(ctx.last_test or {}, ensure_ascii=False, indent=2)[:8_000]
    prompt = (
        f"User request: {ctx.query}\n\n{_buffer_section(ctx.code)}\n\n"
        f"The latest test failed with this evidence:\n{evidence}\n\n"
        "Find the root cause in the module and fix it with the smallest correct change. "
        "Interactive or entry-point code must stay under `if __name__ == \"__main__\":`. "
        "Return the COMPLETE corrected module in exactly one ```python block, then 1-3 "
        "short lines explaining the cause and the fix."
    )
    reply = _ask_agent(ctx, "fix", prompt, attempt)
    code = extract_python_block(reply)
    if code is None or code == ctx.code:
        reason = "no Python code block" if code is None else "an unchanged module"
        _handoff(ctx, "code-troubleshooter", "nothing_found", {"summary": f"Troubleshooter returned {reason}."})
        _note(ctx, "code-troubleshooter", "fix", f"Fix attempt {attempt}: returned {reason}", reply, "nothing_found")
        _record(ctx, "fix", "ERROR", f"Troubleshooter returned {reason}")
        _step_status(ctx, "fix", "error", attempt, f"Returned {reason}.")
        return False
    lines = apply_code(ctx, code, "code-troubleshooter")
    _handoff(ctx, "code-troubleshooter", "success", {"summary": "Applied fix to editor.", "changed_lines": len(lines)})
    _note(ctx, "code-troubleshooter", "fix", f"Fix attempt {attempt} ({len(lines)} lines changed)", reply)
    _record(ctx, "fix", "SUCCESS", f"Applied fix attempt {attempt} ({len(lines)} changed lines)")
    _step_status(ctx, "fix", "success", attempt, f"{len(lines)} lines changed")
    return True


def _fix_loop(ctx: RunContext) -> bool:
    """Fix and retest until the tests pass or attempts run out."""
    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        if not step_fix(ctx, attempt):
            return False
        if step_test(ctx, attempt):
            return True
    ctx.notes.append(f"Tests still fail after {MAX_FIX_ATTEMPTS} fix attempts.")
    return False


def _summary(ctx: RunContext, action: str, passed: bool | None) -> str:
    lines = [f"**{action.capitalize()}** finished."]
    for step in ctx.steps:
        mark = "✓" if step.status == "SUCCESS" else "✗"
        lines.append(f"- {mark} {step.details}")
    if passed is True:
        lines.append("\nThe module passed its checks.")
    elif passed is False and ctx.last_test:
        detail = (ctx.last_test.get("stderr") or ctx.last_test.get("stdout") or "").strip()
        if detail:
            lines.append(f"\nLast failure:\n```\n{detail[-1_500:]}\n```")
    lines.extend(ctx.notes)
    return "\n".join(lines)


# --- entry point -------------------------------------------------------------
def run_code_squad(request: OrchestrationRequest) -> OrchestrationResponse:
    if not request.trace_id:
        request.trace_id = f"tr_{uuid.uuid4().hex}"
        telemetry_bus.initialize_trace(request.trace_id)
    trace_id = request.trace_id
    action = _ACTION_ALIASES.get(request.workflow_action, request.workflow_action)
    squad = get_squad(SQUAD_ID) or {}
    params = request.parameters or {}
    editor_code = params.get("editor_code")
    ctx = RunContext(
        trace_id=trace_id,
        request=request,
        code=editor_code if isinstance(editor_code, str) else "",
        plan=str(params.get("plan") or ""),
        model=str(params.get("model") or "") or None,
    )
    if codebuilder_run_state.get_editor_code(trace_id) is None:
        codebuilder_run_state.begin(trace_id, ctx.code, request.user_query, action)
    started = time.perf_counter()
    telemetry_bus.log_event(
        trace_id, "RUN_STARTED", "orchestrator", SQUAD_ID,
        {"squad_id": SQUAD_ID, "pattern": squad.get("default_pattern", "sequential")},
    )
    status = "success"
    passed: bool | None = None
    try:
        if action == "plan":
            step_plan(ctx)
        elif action == "build":
            if not ctx.plan:
                stored = memory_interface.latest_code_note("plan")
                ctx.plan = stored["content"] if stored else ""
            if not step_build(ctx):
                status = "error"
        elif action == "test":
            passed = step_test(ctx)
        elif action == "fix":
            if ctx.last_test is None and step_test(ctx):
                passed = True
                ctx.notes.append("Tests already pass; no fix was needed.")
            else:
                passed = _fix_loop(ctx)
        else:  # all
            step_plan(ctx)
            if not step_build(ctx):
                status = "error"
            else:
                passed = step_test(ctx) or _fix_loop(ctx)
        if passed is False:
            status = "error"
        final_answer = _summary(ctx, action, passed)
    except PipelineCancelled:
        status = "cancelled"
        final_answer = _summary(ctx, action, None) + "\n\nStopped by user."
    except Exception as exc:
        status = "error"
        final_answer = _summary(ctx, action, None) + f"\n\nWorkflow failed: {exc}"
        telemetry_bus.log_event(
            trace_id, "ERROR", "orchestrator", SQUAD_ID,
            {"error": f"Workflow failed: {exc}", "status": "error"},
        )

    _note(
        ctx, "orchestrator", "summary", f"{action.capitalize()} {status}: {request.user_query[:120]}",
        final_answer, status if status in {"success", "error"} else "nothing_found",
    )
    duration_ms = int((time.perf_counter() - started) * 1000)
    record_squad_run(SQUAD_ID, status == "success", duration_ms)
    handoffs = codebuilder_run_state.get_handoffs(trace_id)
    response = OrchestrationResponse(
        trace_id=trace_id,
        pattern=request.pattern,
        query=request.user_query,
        status=status,
        final_answer=final_answer,
        result_payload={
            "action": action,
            "plan": ctx.plan,
            "code": ctx.code,
            "last_test": ctx.last_test,
        },
        execution_trace=ctx.steps,
    )
    # Save before RUN_COMPLETE so the client's result fetch never races a 404.
    run_results.save(
        trace_id,
        {
            **response.model_dump(),
            "squad_id": SQUAD_ID,
            "scratchpad_snapshot": {
                "latest_subagent_result": handoffs[-1] if handoffs else {},
                "subagent_history": handoffs,
            },
        },
    )
    telemetry_bus.log_event(
        trace_id, "RUN_COMPLETE", "orchestrator", SQUAD_ID,
        {"status": status, "duration_ms": duration_ms},
    )
    telemetry_bus.finish_trace(trace_id)
    return response
