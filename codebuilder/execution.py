"""Compatibility wrapper: the public CodeBuilder execution entry points.

The implementation lives in :mod:`codebuilder.runner`; this module keeps the
historical import surface (``execute_python_code``) working for callers such as
``core_engine.tool_catalog`` and ``codebuilder.interface``.
"""

from .runner import (
    execute_python_code,
    execute_risky,
    execute_safe,
    resolve_python,
    run_risky,
)

__all__ = ["execute_python_code", "execute_risky", "execute_safe", "resolve_python", "run_risky"]