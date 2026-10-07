"""directory_layout/logic.py

Workflows, step sequencing, conditional routing and error orchestration.

Component: Multi-Root Security & Path Boundaries. Scope-to-root routing
lives here: every request path is first routed to the root its scope
(or browser-root prefix) names, then resolved by code.py.
"""

from __future__ import annotations

from pathlib import Path

from .code import resolve_browse_target
from .data import PROJECT_ROOT, REPO_ROOT, VALID_SCOPES


def root_for(scope: str | None) -> Path:
    """
    Resolve a scope string into a filesystem root.

    ``app`` reaches the application repository root (dev files);
    everything else defaults to the managed workspace.
    """

    if scope == "app":
        return REPO_ROOT

    return PROJECT_ROOT


def resolve_request_target(
    path: str,
    scope: str | None = None,
) -> tuple[str, Path, str | None]:
    """
    Resolve a request path into the arguments the filesystem
    operations expect.

    A path prefixed with a browser root (``source_files/AGENTS.md``)
    resolves inside that root. Anything else keeps the legacy
    behaviour and resolves against the scope's root.

    Returns:
        ``(stripped_relative, root, root_name)``.
    """

    return resolve_browse_target(path, root_for(scope))


def is_valid_scope(scope: str | None) -> bool:
    """Whether a scope value is one of the known scopes."""

    return scope is None or scope in VALID_SCOPES
