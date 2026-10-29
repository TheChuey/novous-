"""Bounded in-memory storage for completed workflow results."""

from collections import OrderedDict
import threading
from typing import Any


class OrchestrationRunResults:
    def __init__(self, max_results: int = 100):
        self._max_results = max_results
        self._results: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()

    def save(self, trace_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            self._results[trace_id] = result
            self._results.move_to_end(trace_id)
            while len(self._results) > self._max_results:
                self._results.popitem(last=False)

    def get(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            result = self._results.get(trace_id)
            return dict(result) if result is not None else None

    def latest_for_squad(self, squad_id: str) -> dict[str, Any] | None:
        with self._lock:
            return next(
                (
                    dict(result)
                    for result in reversed(self._results.values())
                    if result.get("squad_id") == squad_id
                ),
                None,
            )


run_results = OrchestrationRunResults()
