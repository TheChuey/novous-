"""Bounded, thread-safe telemetry history and live trace subscriptions."""

from collections import OrderedDict, deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import queue
import re
import threading
from typing import Any, Iterator


_EVENT_DATA_KEYS = {
    "AGENT_MESSAGE": {"summary", "status"},
    "TOOL_CALL_START": {"tool_name"},
    "TOOL_CALL_END": {"tool_name", "status", "duration_ms"},
    "SCRATCHPAD_HANDOFF": {"status", "subagent_id", "result_count", "direction"},
    "ERROR": {"error", "status"},
    "RUN_STARTED": {"squad_id", "pattern"},
    "RUN_COMPLETE": {"status", "duration_ms"},
    "CODE_CHANGE_PREVIEW": {"path", "changed_lines", "file_exists"},
    "CODE_CHANGE_APPLIED": {"path", "changed_lines", "file_exists"},
    "EDITOR_CODE_PREVIEW": {"changed_lines"},
    "EDITOR_CODE_EXECUTION": {"status", "diagnostic_lines"},
    "EDITOR_CODE_UPDATE": {"content", "changed_lines"},
    "AGENT_STARTED": {"agent_id", "step", "attempt"},
    "AGENT_TOKEN": {"agent_id", "text"},
    "AGENT_DONE": {"agent_id", "step", "text"},
    "STEP_STATUS": {"step", "status", "attempt", "summary"},
}
_EVENT_TYPES = frozenset(_EVENT_DATA_KEYS)
# Streamed token chunks are delivered to live listeners only; AGENT_DONE carries
# the full text, so keeping them out of history stops them evicting real events.
_LIVE_ONLY_EVENTS = frozenset({"AGENT_TOKEN"})
_SAFE_STATUSES = {
    "running", "success", "nothing_found", "error", "no_context_found",
    "healthy", "degraded", "failing", "skipped", "cancelled",
}
_MULTILINE_LIMITS = {
    "text": 20_000,
    "content": 1_000_000,
}
_TRACE_CONTEXT: ContextVar[tuple[str, str] | None] = ContextVar(
    "orchestration_trace_context", default=None
)


def _bounded_text(value: Any, limit: int = 300) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ")[:limit]


def _safe_identifier(value: Any, limit: int = 80) -> str:
    text = _bounded_text(value, limit)
    return text if re.fullmatch(r"[A-Za-z0-9_.-]+", text) else "unknown"


def _sse_frame(trace_id: str, event: dict[str, Any]) -> str:
    payload = f"event: telemetry\ndata: {json.dumps(event)}\n\n"
    if event["event_type"] in _LIVE_ONLY_EVENTS:
        return payload
    return f"id: {trace_id}:{event['sequence']}\n{payload}"


def parse_last_event_id(value: str | None) -> int:
    """Read the sequence number from an SSE Last-Event-ID such as 'tr_x:12'."""
    try:
        return max(0, int(str(value or "").rsplit(":", 1)[-1]))
    except ValueError:
        return 0


class TelemetryBus:
    def __init__(
        self,
        max_traces: int = 100,
        max_events_per_trace: int = 500,
        max_listeners_per_trace: int = 8,
        max_listeners: int = 32,
    ):
        self._max_traces = max_traces
        self._max_events_per_trace = max_events_per_trace
        self._max_listeners_per_trace = max_listeners_per_trace
        self._max_listeners = max_listeners
        self._traces: OrderedDict[str, deque[dict[str, Any]]] = OrderedDict()
        self._listeners: dict[str, set[queue.Queue]] = {}
        self._sequence: dict[str, int] = {}
        self._finished: set[str] = set()
        self._lock = threading.RLock()

    def initialize_trace(self, trace_id: str) -> None:
        with self._lock:
            if trace_id in self._traces:
                raise ValueError(f"Trace ID already exists: {trace_id}")
            self._traces[trace_id] = deque(maxlen=self._max_events_per_trace)
            self._sequence[trace_id] = 0
            while len(self._traces) > self._max_traces:
                old_trace_id, _ = self._traces.popitem(last=False)
                if old_trace_id not in self._listeners:
                    self._sequence.pop(old_trace_id, None)
                    self._finished.discard(old_trace_id)

    def log_event(
        self,
        trace_id: str,
        event_type: str,
        sender: str,
        receiver: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if event_type not in _EVENT_TYPES:
            raise ValueError(f"Unknown telemetry event type: {event_type}")
        allowed = _EVENT_DATA_KEYS.get(event_type, {"status"})
        safe_data: dict[str, Any] = {}
        for key in allowed:
            if not data or key not in data:
                continue
            value = data[key]
            if key == "duration_ms":
                safe_data[key] = max(0, int(value))
            elif key in {"result_count", "attempt"}:
                safe_data[key] = max(0, int(value))
            elif key in {"tool_name", "subagent_id", "squad_id", "agent_id", "step"}:
                safe_data[key] = _safe_identifier(value)
            elif key == "path":
                path = _bounded_text(value, 512).replace("\\", "/")
                parts = path.split("/")
                safe_data[key] = (
                    path
                    if path
                    and not path.startswith("/")
                    and not (len(path) > 1 and path[1] == ":")
                    and all(part not in {".", ".."} for part in parts)
                    else ""
                )
            elif key in {"changed_lines", "diagnostic_lines"}:
                safe_data[key] = [
                    max(1, int(line))
                    for line in value[:120]
                    if isinstance(line, int) and not isinstance(line, bool) and line > 0
                ] if isinstance(value, list) else []
            elif key == "file_exists":
                safe_data[key] = bool(value)
            elif key == "status":
                status = _bounded_text(value, 40)
                safe_data[key] = status if status in _SAFE_STATUSES else "unknown"
            elif key in {"summary", "error"}:
                safe_data[key] = _bounded_text(value, 500)
            elif key in _MULTILINE_LIMITS:
                safe_data[key] = str(value or "")[: _MULTILINE_LIMITS[key]]
            elif key == "pattern":
                pattern = _bounded_text(value, 40)
                safe_data[key] = (
                    pattern if pattern in {"sequential", "fanout", "router"}
                    else "unknown"
                )
            elif key == "direction":
                direction = _bounded_text(value, 20)
                safe_data[key] = (
                    direction if direction in {"read", "write"} else "unknown"
                )
            else:
                safe_data[key] = _bounded_text(value)
        live_only = event_type in _LIVE_ONLY_EVENTS
        with self._lock:
            events = self._traces.get(trace_id)
            if events is None:
                events = deque(maxlen=self._max_events_per_trace)
                self._traces[trace_id] = events
                self._sequence[trace_id] = 0
            self._traces.move_to_end(trace_id)
            if not live_only:
                self._sequence[trace_id] += 1
            event = {
                "trace_id": trace_id,
                "sequence": self._sequence[trace_id],
                "event_type": event_type,
                "sender": _safe_identifier(sender),
                "receiver": _safe_identifier(receiver),
                "data": safe_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if not live_only:
                events.append(event)
            listeners = tuple(self._listeners.get(trace_id, ()))
            while len(self._traces) > self._max_traces:
                old_trace_id, _ = self._traces.popitem(last=False)
                if old_trace_id not in self._listeners:
                    self._sequence.pop(old_trace_id, None)
                    self._finished.discard(old_trace_id)
            for listener in listeners:
                try:
                    listener.put_nowait(event)
                except queue.Full:
                    try:
                        listener.get_nowait()
                    except queue.Empty:
                        pass
                    listener.put_nowait(event)
            return event

    def has_trace(self, trace_id: str) -> bool:
        with self._lock:
            return trace_id in self._traces

    def has_listener_capacity(self, trace_id: str) -> bool:
        with self._lock:
            listeners = self._listeners.get(trace_id, set())
            total_listeners = sum(len(items) for items in self._listeners.values())
            return (
                len(listeners) < self._max_listeners_per_trace
                and total_listeners < self._max_listeners
            )

    def get_trace_history(self, trace_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._traces.get(trace_id, ()))

    def finish_trace(self, trace_id: str) -> None:
        with self._lock:
            self._finished.add(trace_id)
            listeners = tuple(self._listeners.get(trace_id, ()))
            for listener in listeners:
                try:
                    listener.put_nowait(None)
                except queue.Full:
                    try:
                        listener.get_nowait()
                    except queue.Empty:
                        pass
                    listener.put_nowait(None)

    def subscribe(self, trace_id: str, after: int = 0) -> Iterator[str]:
        """Stream events newer than ``after`` so a reconnect does not replay history."""
        listener: queue.Queue = queue.Queue(maxsize=100)
        with self._lock:
            if trace_id not in self._traces:
                raise KeyError(trace_id)
            listeners = self._listeners.setdefault(trace_id, set())
            total_listeners = sum(len(items) for items in self._listeners.values())
            if (
                len(listeners) >= self._max_listeners_per_trace
                or total_listeners >= self._max_listeners
            ):
                raise RuntimeError(f"Trace listener limit reached: {trace_id}")
            listeners.add(listener)
            history = list(self._traces[trace_id])
            finished = trace_id in self._finished

        sequence = max(0, int(after or 0))
        try:
            for event in history:
                if event["sequence"] <= sequence:
                    if event["event_type"] == "RUN_COMPLETE":
                        return
                    continue
                sequence = event["sequence"]
                yield _sse_frame(trace_id, event)
                if event["event_type"] == "RUN_COMPLETE":
                    return
            if finished:
                return

            keep_alive_count = 0
            while True:
                try:
                    event = listener.get(timeout=15)
                except queue.Empty:
                    yield ": keep-alive\n\n"
                    keep_alive_count += 1
                    if keep_alive_count >= 40:
                        return
                    continue
                keep_alive_count = 0
                if event is None:
                    with self._lock:
                        if trace_id in self._finished:
                            return
                    continue
                if event["event_type"] in _LIVE_ONLY_EVENTS:
                    yield _sse_frame(trace_id, event)
                    continue
                if event["sequence"] <= sequence:
                    continue
                sequence = event["sequence"]
                yield _sse_frame(trace_id, event)
                if event["event_type"] == "RUN_COMPLETE":
                    return
        finally:
            with self._lock:
                listeners = self._listeners.get(trace_id)
                if listeners:
                    listeners.discard(listener)
                    if not listeners:
                        self._listeners.pop(trace_id, None)

    @contextmanager
    def agent_context(self, trace_id: str, agent_id: str) -> Iterator[None]:
        token = _TRACE_CONTEXT.set((trace_id, agent_id))
        try:
            yield
        finally:
            _TRACE_CONTEXT.reset(token)

    def current_context(self) -> tuple[str, str] | None:
        return _TRACE_CONTEXT.get()


telemetry_bus = TelemetryBus()
