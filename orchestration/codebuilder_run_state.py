"""Bounded, trace-scoped CodeBuilder editor previews and execution results."""

from collections import OrderedDict
import re
import threading
from typing import Any


MAX_EDITOR_CONTENT_BYTES = 1_000_000


class CodeBuilderRunState:
    def __init__(self, max_traces: int = 100):
        self._max_traces = max_traces
        self._states: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()

    def begin(
        self,
        trace_id: str,
        editor_code: str,
        user_query: str = "",
        workflow_action: str = "all",
        editor_path: str = "",
    ) -> None:
        if not isinstance(editor_code, str):
            raise ValueError("The CodeBuilder editor buffer must be text.")
        if len(editor_code.encode("utf-8")) > MAX_EDITOR_CONTENT_BYTES:
            raise ValueError("The CodeBuilder editor buffer exceeds the 1 MB limit.")
        with self._lock:
            self._states[trace_id] = {
                "editor_code": editor_code,
                "user_query": user_query,
                "workflow_action": workflow_action,
                "editor_path": editor_path,
                "workspace_source": None,
                "preview": None,
                "execution": None,
                "handoff": None,
                "handoffs": [],
            }
            self._states.move_to_end(trace_id)
            while len(self._states) > self._max_traces:
                self._states.popitem(last=False)

    def code_change_block_reason(self, trace_id: str) -> str | None:
        with self._lock:
            state = self._states.get(trace_id)
            if state is None:
                return None
            query = str(state.get("user_query") or "")
            action = state.get("workflow_action")

        if action not in {"build", "troubleshoot", "all"} or not re.search(
            r"\b404\b", query, re.IGNORECASE
        ):
            return None

        has_url_or_path = bool(
            re.search(
                r"https?://\S+|(?:^|\s)/[A-Za-z0-9._~!$&'()*+,;=:@%/-]+",
                query,
                re.IGNORECASE,
            )
        )
        has_http_method = bool(
            re.search(
                r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b",
                query,
                re.IGNORECASE,
            )
        )
        if has_url_or_path and has_http_method:
            return None
        return (
            "Code changes are blocked for this 404 workflow until the request "
            "includes both the exact URL/path and HTTP method. No editor preview "
            "or workspace write was applied."
        )

    def assert_code_changes_allowed(self, trace_id: str) -> None:
        reason = self.code_change_block_reason(trace_id)
        if reason:
            raise ValueError(reason)

    def save_preview(self, trace_id: str, content: str, changed_lines: list[int]) -> bool:
        if not isinstance(content, str):
            raise ValueError("The editor preview must be text.")
        if len(content.encode("utf-8")) > MAX_EDITOR_CONTENT_BYTES:
            raise ValueError("The editor preview exceeds the 1 MB limit.")
        with self._lock:
            state = self._states.get(trace_id)
            if state is None:
                return False
            state["preview"] = {
                "content": content,
                "changed_lines": list(changed_lines),
            }
            self._states.move_to_end(trace_id)
            return True

    def save_execution(
        self,
        trace_id: str,
        code: str,
        result: dict[str, Any],
        allow_non_editor_source: bool = False,
    ) -> bool:
        with self._lock:
            state = self._states.get(trace_id)
            if state is None:
                return False
            preview = state.get("preview")
            source_matches_editor = (
                code == state["editor_code"]
                or (preview is not None and code == preview["content"])
                or code == state.get("workspace_source")
            )
            if not source_matches_editor and not allow_non_editor_source:
                return False
            state["execution"] = {
                **result,
                "source_matches_editor": source_matches_editor,
            }
            self._states.move_to_end(trace_id)
            return True

    def save_workspace_source(
        self, trace_id: str, path: str, content: str
    ) -> bool:
        def normalize(value: str) -> str:
            return value.replace("\\", "/").removeprefix("./").casefold()

        with self._lock:
            state = self._states.get(trace_id)
            if (
                state is None
                or not state.get("editor_path")
                or normalize(path) != normalize(str(state["editor_path"]))
            ):
                return False
            state["workspace_source"] = content
            self._states.move_to_end(trace_id)
            return True

    def matches_editor_source(self, trace_id: str, code: str) -> bool:
        with self._lock:
            state = self._states.get(trace_id)
            if state is None:
                return False
            preview = state.get("preview")
            return (
                code == state["editor_code"]
                or (preview is not None and code == preview["content"])
                or code == state.get("workspace_source")
            )

    def save_handoff(
        self, trace_id: str, subagent_id: str, task_type: str, status: str, payload: Any
    ) -> None:
        with self._lock:
            state = self._states.setdefault(
                trace_id,
                {
                    "editor_code": "",
                    "preview": None,
                    "execution": None,
                    "handoff": None,
                    "handoffs": [],
                },
            )
            handoff = {
                "subagent_id": subagent_id,
                "task_type": task_type,
                "status": status,
                "payload": payload,
            }
            handoffs = state.setdefault("handoffs", [])
            if handoffs and handoffs[-1] == handoff:
                state["handoff"] = handoffs[-1]
                return
            handoffs.append(handoff)
            state["handoff"] = handoff
            self._states.move_to_end(trace_id)

    def get_handoff(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._states.get(trace_id)
            handoff = state.get("handoff") if state else None
            return dict(handoff) if handoff is not None else None

    def get_handoffs(self, trace_id: str) -> list[dict[str, Any]]:
        with self._lock:
            state = self._states.get(trace_id)
            handoffs = state.get("handoffs", []) if state else []
            return [dict(handoff) for handoff in handoffs]

    def get_preview(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._states.get(trace_id)
            preview = state.get("preview") if state else None
            return dict(preview) if preview is not None else None

    def get_execution(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._states.get(trace_id)
            execution = state.get("execution") if state else None
            return dict(execution) if execution is not None else None

    def get_editor_code(self, trace_id: str) -> str | None:
        with self._lock:
            state = self._states.get(trace_id)
            return state.get("editor_code") if state else None

    def discard(self, trace_id: str) -> None:
        with self._lock:
            self._states.pop(trace_id, None)


codebuilder_run_state = CodeBuilderRunState()
