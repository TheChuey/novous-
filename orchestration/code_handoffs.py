"""Normalization and evidence helpers for Code Development handoffs.

The local models used by the code squad do not always follow the handoff
contract exactly.  These helpers keep the stored audit payload intact while
giving orchestration a predictable, evidence-aware view of each handoff.
"""

from __future__ import annotations

import json
from typing import Any

CODE_SUBAGENT_IDS = {"code-builder", "tester", "code-troubleshooter"}

TASK_TYPE_BY_AGENT = {
    "code-builder": "code_build",
    "tester": "code_test",
    "code-troubleshooter": "code_troubleshooting",
}

REQUIRED_FIELDS = {
    "code_build": ("summary", "files_changed", "checks_run"),
    "code_test": ("summary", "checks_run", "observed_output"),
    "code_troubleshooting": (
        "observed_problem",
        "evidence_inspected",
        "root_cause",
        "files_changed",
        "checks_run",
    ),
}

_ALIASES = {
    "files_changed": ("changed_files", "files_modified", "files"),
    "checks_run": ("tests_run", "checks", "tests"),
    "observed_output": ("output", "stdout", "result"),
    "evidence_inspected": ("evidence", "inspected"),
    "root_cause": ("cause",),
    "remaining_issues": ("issues",),
    "remaining_questions": ("questions",),
    "error": ("failure", "error_message"),
}

_FAILURE_TEXT_FIELDS = ("error", "stderr", "traceback")
_FAILURE_LIST_FIELDS = ("diagnostics",)


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def normalize_payload(payload: Any) -> dict[str, Any]:
    """Return a structured payload without discarding prose responses."""
    if isinstance(payload, dict):
        normalized = dict(payload)
    elif isinstance(payload, list):
        normalized = {"items": payload}
    elif isinstance(payload, str):
        text = payload.strip()
        if not text:
            normalized = {}
        elif text.startswith(("{", "[")):
            try:
                decoded = json.loads(text)
            except (TypeError, ValueError):
                normalized = {"summary": text, "raw_payload": text}
            else:
                normalized = (
                    dict(decoded)
                    if isinstance(decoded, dict)
                    else {"items": decoded}
                    if isinstance(decoded, list)
                    else {"summary": str(decoded)}
                )
        else:
            normalized = {"summary": text, "raw_payload": text}
    elif payload is None:
        normalized = {}
    else:
        normalized = {"summary": str(payload)}

    for target, aliases in _ALIASES.items():
        if _non_empty(normalized.get(target)):
            continue
        for alias in aliases:
            if _non_empty(normalized.get(alias)):
                normalized[target] = normalized[alias]
                break

    if not _non_empty(normalized.get("summary")):
        for candidate in ("message", "reason", "root_cause", "observed_problem"):
            if _non_empty(normalized.get(candidate)):
                normalized["summary"] = str(normalized[candidate])
                break

    return normalized


def execution_status(execution: dict[str, Any] | None) -> str:
    return str((execution or {}).get("status") or "").upper()


def execution_failed(execution: dict[str, Any] | None) -> bool:
    if not execution:
        return False
    if execution_status(execution) == "ERROR":
        return True
    if execution.get("timed_out") or execution.get("stuck"):
        return True
    return_code = execution.get("return_code")
    return return_code is not None and return_code != 0


def has_failure_evidence(
    handoff: dict[str, Any] | None,
    execution: dict[str, Any] | None = None,
) -> bool:
    """Return True only for concrete failures, not speculative prose."""
    if execution_failed(execution):
        return True

    payload = normalize_payload((handoff or {}).get("payload"))
    for key in _FAILURE_TEXT_FIELDS:
        if _non_empty(payload.get(key)):
            return True
    for key in _FAILURE_LIST_FIELDS:
        if _non_empty(payload.get(key)):
            return True
    if payload.get("timed_out") or payload.get("stuck"):
        return True
    return_code = payload.get("return_code")
    if return_code is not None and return_code != 0:
        return True

    status = str((handoff or {}).get("status") or "").lower()
    if status == "error" and _non_empty(payload.get("observed_output")):
        return True
    if (
        status == "error"
        and payload.get("handoff_source") == "orchestrator_fallback"
    ):
        return True
    return False


def effective_status(
    handoff: dict[str, Any] | None,
    execution: dict[str, Any] | None = None,
) -> str:
    """Return the status orchestration should use for routing decisions."""
    entry = handoff or {}
    status = str(entry.get("status") or "error")
    if (
        entry.get("subagent_id") == "tester"
        and status == "error"
        and not has_failure_evidence(entry, execution)
    ):
        return "nothing_found"
    return status


def normalize_handoff(
    handoff: dict[str, Any] | None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a copy with normalized payload, validation, and effective status."""
    entry = dict(handoff or {})
    payload = normalize_payload(entry.get("payload"))
    task_type = str(entry.get("task_type") or "")
    missing = [
        field
        for field in REQUIRED_FIELDS.get(task_type, ())
        if not _non_empty(payload.get(field))
    ]
    entry["payload"] = payload
    entry["missing_fields"] = missing
    entry["has_failure_evidence"] = has_failure_evidence(entry, execution)
    entry["effective_status"] = effective_status(entry, execution)
    return entry


def normalize_handoffs(
    handoffs: list[dict[str, Any]],
    execution: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return [normalize_handoff(handoff, execution) for handoff in handoffs or []]


def _bounded_text(value: Any, limit: int) -> tuple[str, bool]:
    text = str(value or "")
    if len(text) <= limit:
        return text, False
    return text[-limit:], True


def execution_evidence(
    execution: dict[str, Any] | None,
    text_limit: int = 8_000,
    diagnostic_limit: int = 20,
) -> dict[str, Any]:
    """Return a bounded, prompt-safe view of the latest execution result."""
    if not execution:
        return {}

    evidence: dict[str, Any] = {}
    for key in (
        "run_id",
        "status",
        "return_code",
        "timed_out",
        "duration_seconds",
        "source_matches_editor",
    ):
        if key in execution:
            evidence[key] = execution[key]

    for key in ("stdout", "stderr", "error"):
        text, truncated = _bounded_text(execution.get(key), text_limit)
        if text:
            evidence[key] = text
            if truncated:
                evidence[f"{key}_truncated"] = True

    diagnostics = execution.get("diagnostics")
    if isinstance(diagnostics, list) and diagnostics:
        evidence["diagnostics"] = diagnostics[:diagnostic_limit]
        if len(diagnostics) > diagnostic_limit:
            evidence["diagnostics_truncated"] = True

    stuck = execution.get("stuck")
    if stuck:
        evidence["stuck"] = stuck

    return evidence
