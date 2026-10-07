"""directory_layout/code.py

Stateful engine classes, core objects and active execution loops.

Component: Multi-Root Security & Path Boundaries. This file holds the
core path-resolution and tree-reading primitives: resolving a path to a
safe absolute location inside its root, enforcing writability, and
walking the filesystem into JSON-friendly trees.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .data import BROWSE_ROOTS, PROJECT_ROOT
from .helperfunctions import (
    is_oversized,
    is_text_file,
    is_writable_root,
    should_ignore,
    split_root,
)


# ============================================================
# PATH SECURITY
# ============================================================

def resolve_project_path(
    relative_path: str,
    root: Path | None = None,
) -> Path:
    """
    Convert a project-relative path into a safe absolute path.

    This prevents paths such as ``../../some_file.txt`` from escaping
    the active project root. The default root is the managed workspace;
    scope-aware callers pass the repository root to reach application
    files.

    Args:
        relative_path:
            Path relative to the active root.
        root:
            Filesystem root the path must stay inside. Defaults to
            the managed workspace.

    Returns:
        Safe absolute Path.

    Raises:
        ValueError:
            If the path is empty or outside the root.
    """

    if root is None:
        root = PROJECT_ROOT

    if not relative_path:
        raise ValueError("A project-relative path is required.")

    # Normalize Windows separators.
    relative_path = relative_path.replace("\\", "/")

    candidate = (root / relative_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(
            "Access outside the project directory is not allowed."
        )

    return candidate


# ============================================================
# BROWSER ROOT RESOLUTION
# ============================================================

def resolve_browse_target(
    relative_path: str,
    legacy_root: Path | None = None,
) -> tuple[str, Path, str | None]:
    """
    Split a possibly root-qualified path into the arguments the
    filesystem operations expect.

    ``source_files/APP_CODE_SNAPSHOT.md`` resolves inside the
    ``source_files`` root. Paths without a known root prefix fall back to
    ``legacy_root`` (the managed workspace by default) so existing
    API callers are unaffected.

    Args:
        relative_path:
            Root-qualified or legacy relative path.
        legacy_root:
            Root used when the path carries no root prefix.

    Returns:
        ``(stripped_relative, root, root_name)``. ``root_name`` is
        None for legacy paths.

    Raises:
        ValueError:
            If the path is empty or names a root with no remainder.
    """

    root_name, remainder = split_root(relative_path)

    if root_name is None:
        return (
            relative_path,
            legacy_root if legacy_root is not None else PROJECT_ROOT,
            None,
        )

    if not remainder:
        raise ValueError(f"A path inside {root_name} is required.")

    return remainder, BROWSE_ROOTS[root_name]["path"], root_name


def resolve_browse_path(
    relative_path: str,
    legacy_root: Path | None = None,
) -> tuple[Path, str | None]:
    """
    Resolve a possibly root-qualified path to a safe absolute path.

    Returns:
        ``(absolute_path, root_name)``. ``root_name`` is None for
        legacy paths.

    Raises:
        ValueError:
            If the path is empty or escapes its root.
    """

    stripped, root, root_name = resolve_browse_target(
        relative_path,
        legacy_root,
    )

    return resolve_project_path(stripped, root), root_name


def require_writable(
    relative_path: str,
    legacy_root: Path | None = None,
) -> str | None:
    """
    Ensure a path may be written to.

    Args:
        relative_path:
            Root-qualified or legacy relative path.
        legacy_root:
            Root used when the path carries no root prefix.

    Returns:
        The resolved root name (None for legacy paths).

    Raises:
        ValueError:
            If the path targets a read-only root.
    """

    _, root_name = resolve_browse_path(relative_path, legacy_root)

    if not is_writable_root(root_name):
        raise ValueError(f"{root_name} is read-only.")

    return root_name


# ============================================================
# READ FILESYSTEM
# ============================================================

def read_filesystem(
    directory: Path | None = None,
    _root: Path | None = None,
    _prefix: str = "",
) -> list[dict[str, Any]]:
    """
    Recursively read the project filesystem.

    Args:
        directory:
            Directory to list.
        _root:
            Root the emitted paths are relative to.
        _prefix:
            Prepended to every emitted path. Used by
            :func:`read_browse_filesystem` so each node carries its
            browser-root name (``source_files/APP_CODE_SNAPSHOT.md``),
            which is what lets the API resolve the path back to its root.

    Returns:
        JSON-friendly file/folder tree.
    """

    if directory is None:
        directory = PROJECT_ROOT

    if _root is None:
        _root = directory

    results: list[dict[str, Any]] = []

    try:
        children = sorted(
            directory.iterdir(),
            key=lambda item: (not item.is_dir(), item.name.lower()),
        )
    except (OSError, PermissionError):
        return results

    for child in children:

        if should_ignore(child):
            continue

        relative_path = child.relative_to(_root)
        relative_path = str(relative_path).replace("\\", "/")

        if _prefix:
            relative_path = f"{_prefix}/{relative_path}"

        # ----------------------------------------------------
        # DIRECTORY
        # ----------------------------------------------------

        if child.is_dir():
            results.append(
                {
                    "name": child.name,
                    "path": relative_path,
                    "type": "directory",
                    "children": read_filesystem(
                        child,
                        _root=_root,
                        _prefix=_prefix,
                    ),
                }
            )

        # ----------------------------------------------------
        # FILE
        # ----------------------------------------------------

        else:
            try:
                size = child.stat().st_size
            except OSError:
                size = 0

            results.append(
                {
                    "name": child.name,
                    "path": relative_path,
                    "type": "file",
                    "size": size,
                    "editable": (
                        is_text_file(child) and not is_oversized(child)
                    ),
                }
            )

    return results


def read_browse_filesystem(
    roots: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Build the browser tree.

    The top level is always the configured ``BROWSE_ROOTS`` folders,
    so the tree itself acts as the folder switcher. Every node path
    is prefixed with its root name.

    Roots that do not exist on disk are skipped.

    Args:
        roots:
            Names to include, or None for all of them. This narrows
            what a page is *shown*, nothing more: the omitted roots
            stay in ``BROWSE_ROOTS``, so their paths still resolve
            for read, write and delete. A page that lists one root
            can therefore hand a file from another root to a page
            that does list it.

    Returns:
        JSON-friendly tree, in ``BROWSE_ROOTS`` declaration order.
    """

    wanted = None if roots is None else set(roots)

    results: list[dict[str, Any]] = []

    for root_name, config in BROWSE_ROOTS.items():

        if wanted is not None and root_name not in wanted:
            continue

        root_path: Path = config["path"]

        if not root_path.is_dir():
            continue

        results.append(
            {
                "name": root_name,
                "path": root_name,
                "type": "directory",
                "root": root_name,
                "writable": bool(config.get("writable", False)),
                "children": read_filesystem(
                    root_path,
                    _root=root_path,
                    _prefix=root_name,
                ),
            }
        )

    return results
