"""Diagnostic funnel utilities for the CodeBuilder pillar."""

from typing import Any, Iterable, List


def funnel_diagnostics(items: Iterable[Any]) -> List[dict]:
    """Normalize arbitrary diagnostic payloads to dictionary entries."""
    return [
        {
            "path": getattr(item, "path", None),
            "line": getattr(item, "line", None),
            "column": getattr(item, "column", None),
            "message": getattr(item, "message", str(item)),
            "severity": getattr(item, "severity", "error"),
            "run_id": getattr(item, "run_id", None),
        }
        for item in items
    ]
