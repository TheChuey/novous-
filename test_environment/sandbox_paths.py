"""Allowed folders for the sandbox terminal and the Code Builder file save/open.

The list lives under ``sandbox_roots`` in tools/allowed_paths.json. The scripts folder is always allowed.
"""

import os
from pathlib import Path

from . import sandbox_env


class PathNotAllowed(ValueError):
    pass


def _norm(path: Path | str) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def allowed_roots() -> list[Path]:
    configured = sandbox_env.read_config().get("sandbox_roots")
    roots = [sandbox_env.SCRIPTS_DIR]
    if isinstance(configured, list):
        for raw in configured:
            path = Path(os.path.expandvars(str(raw))).expanduser()
            if path.is_absolute() and path.is_dir():
                roots.append(path)
    unique: dict[str, Path] = {}
    for root in roots:
        unique.setdefault(_norm(root), root.resolve())
    return list(unique.values())


def is_allowed(path: Path | str) -> bool:
    target = _norm(path)
    for root in allowed_roots():
        base = _norm(root)
        if target == base or target.startswith(base + os.sep):
            return True
    return False


def resolve(path: str | Path, base: Path | None = None) -> Path:
    """Resolve ``path`` (absolute, or relative to ``base``) and require it to be inside an allowed root."""
    candidate = Path(os.path.expandvars(str(path))).expanduser()
    if not candidate.is_absolute():
        candidate = (base or sandbox_env.SCRIPTS_DIR) / candidate
    resolved = candidate.resolve()
    if not is_allowed(resolved):
        raise PathNotAllowed(f"'{resolved}' is outside the allowed sandbox paths. Use: sandbox add <folder>")
    return resolved


def _save(roots: list[Path]) -> None:
    config = sandbox_env.read_config()
    config["sandbox_roots"] = [str(root) for root in roots if _norm(root) != _norm(sandbox_env.SCRIPTS_DIR)]
    config["sandbox_roots"].insert(0, str(sandbox_env.SCRIPTS_DIR))
    sandbox_env.write_config(config)


def add_root(folder: str) -> Path:
    path = Path(os.path.expandvars(folder.strip().strip('"'))).expanduser()
    if not path.is_absolute():
        raise ValueError("Give a full folder path, for example: sandbox add D:\\projects")
    if not path.is_dir():
        raise ValueError(f"Folder does not exist: {path}")
    roots = allowed_roots()
    if not any(_norm(r) == _norm(path) for r in roots):
        roots.append(path.resolve())
        _save(roots)
    return path.resolve()


def remove_root(folder: str) -> bool:
    target = _norm(folder.strip().strip('"'))
    if target == _norm(sandbox_env.SCRIPTS_DIR):
        raise ValueError("The scripts folder is always allowed and cannot be removed.")
    roots = allowed_roots()
    kept = [r for r in roots if _norm(r) != target]
    if len(kept) == len(roots):
        return False
    _save(kept)
    return True


def clear_roots() -> None:
    _save([sandbox_env.SCRIPTS_DIR])
