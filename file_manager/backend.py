"""Secure physical file operations constrained to the configured file-manager root."""

import json
import os
import shutil
import tempfile
from pathlib import Path

from editor.editor_operations import PROJECT_ROOT

CONFIG_PATH = Path(__file__).resolve().parent.parent / "tools" / "allowed_paths.json"
SKIP_DIRECTORIES = {"__pycache__", "_pycache__"}


def _read_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Could not read file-manager configuration '{CONFIG_PATH}': {exc}"
        ) from exc
    if not isinstance(config, dict):
        raise RuntimeError(f"File-manager configuration must be a JSON object: {CONFIG_PATH}")
    return config


def configured_roots() -> list[dict[str, str]]:
    config = _read_config()
    roots = config.get("file_manager_roots")
    if roots is None:
        legacy_path = config.get("file_manager_root", str(PROJECT_ROOT.resolve()))
        roots = [{"name": "Workspace", "path": legacy_path}]
    if not isinstance(roots, list):
        raise RuntimeError("'file_manager_roots' must be a JSON array.")

    result = []
    names = set()
    paths = set()
    for entry in roots:
        if not isinstance(entry, dict):
            raise RuntimeError("Each file-manager root must have a name and path.")
        name = str(entry.get("name", "")).strip()
        raw_path = os.path.expandvars(str(entry.get("path", ""))).strip()
        if not name or not raw_path:
            raise RuntimeError("Each file-manager root must have a non-empty name and path.")
        root = Path(raw_path).expanduser()
        if not root.is_absolute():
            raise RuntimeError(f"File-manager root must be an absolute path: {raw_path}")
        resolved = root.resolve()
        if not resolved.is_dir():
            raise RuntimeError(f"Configured file-manager root is not an existing directory: {resolved}")
        name_key = name.casefold()
        path_key = os.path.normcase(str(resolved))
        if name_key in names or path_key in paths:
            raise RuntimeError("File-manager root names and paths must be unique.")
        names.add(name_key)
        paths.add(path_key)
        result.append({"name": name, "path": str(resolved)})
    if not result:
        raise RuntimeError("Configure at least one entry in 'file_manager_roots'.")
    return result


def active_root_path() -> Path:
    config = _read_config()
    roots = configured_roots()
    selected = config.get(
        "active_file_manager_root",
        config.get("file_manager_root", roots[0]["path"]),
    )
    for root in roots:
        if os.path.normcase(root["path"]) == os.path.normcase(str(selected)):
            return Path(root["path"])
    raise RuntimeError(
        "The active file-manager root is not present in 'file_manager_roots'."
    )


def workspace_root() -> Path:
    return active_root_path()


def _write_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=CONFIG_PATH.parent,
            prefix=f".{CONFIG_PATH.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(config, temp_file, indent=2)
            temp_file.write("\n")
        temp_path.replace(CONFIG_PATH)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def select_root(path: str) -> dict:
    roots = configured_roots()
    selected = next(
        (root for root in roots if os.path.normcase(root["path"]) == os.path.normcase(path)),
        None,
    )
    if selected is None:
        raise ValueError("Choose a configured file-manager root.")

    config = _read_config()
    config["file_manager_roots"] = roots
    config["active_file_manager_root"] = selected["path"]
    config["file_manager_root"] = selected["path"]
    _write_config(config)
    return {"roots": roots, "active_path": selected["path"]}


def manage_roots(action: str, paths: list[str]) -> dict:
    """Add or remove configured file-manager directories."""
    if action not in {"add", "remove"}:
        raise ValueError("Action must be 'add' or 'remove'.")
    if not paths:
        raise ValueError("Provide at least one directory path.")

    roots = configured_roots()
    config = _read_config()
    current_active = str(
        config.get("active_file_manager_root", config.get("file_manager_root", roots[0]["path"]))
    )
    normalized_paths = []
    for raw_path in paths:
        value = os.path.expandvars(str(raw_path)).strip()
        if not value:
            raise ValueError("Directory paths cannot be empty.")
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            raise ValueError(f"Directory path must be absolute: {value}")
        resolved = candidate.resolve()
        if action == "add" and not resolved.is_dir():
            raise ValueError(f"Directory does not exist: {resolved}")
        normalized_paths.append(str(resolved))

    path_keys = {os.path.normcase(path) for path in normalized_paths}
    added = []
    removed = []
    unchanged = []
    if action == "add":
        existing_paths = {os.path.normcase(root["path"]) for root in roots}
        existing_names = {root["name"].casefold() for root in roots}
        for path in normalized_paths:
            path_key = os.path.normcase(path)
            if path_key in existing_paths:
                unchanged.append(path)
                continue
            folder_name = Path(path).name or path
            name = folder_name
            suffix = 2
            while name.casefold() in existing_names:
                name = f"{folder_name} ({suffix})"
                suffix += 1
            roots.append({"name": name, "path": path})
            existing_paths.add(path_key)
            existing_names.add(name.casefold())
            added.append(path)
    else:
        configured_paths = {os.path.normcase(root["path"]) for root in roots}
        removed = [root["path"] for root in roots if os.path.normcase(root["path"]) in path_keys]
        unchanged = [
            path for path in normalized_paths
            if os.path.normcase(path) not in configured_paths
        ]
        roots = [root for root in roots if os.path.normcase(root["path"]) not in path_keys]
        if not removed:
            raise ValueError("None of the provided paths are configured file-manager roots.")
        if not roots:
            raise ValueError("At least one file-manager root must remain configured.")

    active_path = next(
        (root["path"] for root in roots if os.path.normcase(root["path"]) == os.path.normcase(current_active)),
        roots[0]["path"],
    )
    config["file_manager_roots"] = roots
    config["active_file_manager_root"] = active_path
    config["file_manager_root"] = active_path
    _write_config(config)
    return {
        "roots": roots,
        "active_path": active_path,
        "added": added,
        "removed": removed,
        "unchanged": unchanged,
    }


def resolve_workspace_path(relative_path: str = "") -> Path:
    if not isinstance(relative_path, str):
        raise ValueError("A workspace-relative path is required.")

    clean_path = relative_path.replace("\\", "/")
    if clean_path.startswith("/") or (len(clean_path) > 1 and clean_path[1] == ":"):
        raise ValueError("Absolute paths are not allowed.")
    base_root = workspace_root()
    parts = Path(clean_path).parts
    if any(part in {".", ".."} for part in parts):
        raise ValueError("Relative path traversal is not allowed.")
    candidate = base_root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("Symbolic links are not supported by the file manager.")
    path = candidate.resolve()
    try:
        path.relative_to(base_root)
    except ValueError:
        raise ValueError("Access outside the workspace is forbidden.") from None
    return path


def list_directory(relative_path: str = "") -> list[dict]:
    directory = resolve_workspace_path(relative_path)
    if not directory.is_dir():
        if directory.exists():
            raise NotADirectoryError(f"Not a directory: {relative_path}")
        raise FileNotFoundError(f"Directory not found: {relative_path}")

    entries = []
    for child in sorted(
        directory.iterdir(),
        key=lambda item: (
            not (not item.is_symlink() and item.is_dir()),
            item.name.lower(),
        ),
    ):
        if (
            child.is_symlink()
            or child.name.startswith(".")
            or (child.is_dir() and child.name.lower() in SKIP_DIRECTORIES)
            or (child.is_file() and child.suffix.lower() == ".pyc")
        ):
            continue
        try:
            resolved = child.resolve()
            resolved.relative_to(workspace_root())
        except ValueError:
            continue
        if not resolved.exists():
            continue
        stat = resolved.stat()
        entries.append({
            "name": resolved.name,
            "path": resolved.relative_to(workspace_root()).as_posix(),
            "type": "directory" if resolved.is_dir() else "file",
            "size": 0 if resolved.is_dir() else stat.st_size,
            "modified": stat.st_mtime,
        })
    return entries


def directory_tree(relative_path: str = "") -> dict:
    directory = resolve_workspace_path(relative_path)
    if not directory.is_dir():
        if directory.exists():
            raise NotADirectoryError(f"Not a directory: {relative_path}")
        raise FileNotFoundError(f"Directory not found: {relative_path}")
    root = workspace_root()
    rel_path = directory.relative_to(root).as_posix()
    node = {
        "name": directory.name or root.name,
        "path": "" if rel_path == "." else rel_path,
        "type": "directory",
        "children": [],
    }
    for item in list_directory(node["path"]):
        if item["type"] == "directory":
            node["children"].append(directory_tree(item["path"]))
        else:
            node["children"].append({
                "name": item["name"],
                "path": item["path"],
                "type": "file",
            })
    return node


def read_file(relative_path: str) -> dict:
    path = resolve_workspace_path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")
    return {
        "path": path.relative_to(workspace_root()).as_posix(),
        "content": path.read_text(encoding="utf-8"),
    }


def write_file(relative_path: str, content: str) -> dict:
    path = resolve_workspace_path(relative_path)
    if path.exists() and not path.is_file():
        raise IsADirectoryError(f"Path is not a file: {relative_path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {
        "path": path.relative_to(workspace_root()).as_posix(),
        "bytes_written": len(content.encode("utf-8")),
    }


def create_path(relative_path: str, kind: str = "file") -> dict:
    path = resolve_workspace_path(relative_path)
    if path.exists():
        raise FileExistsError(f"Path already exists: {relative_path}")
    if kind == "directory":
        path.mkdir(parents=True)
    elif kind == "file":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    else:
        raise ValueError("Kind must be 'file' or 'directory'.")
    return {
        "path": path.relative_to(workspace_root()).as_posix(),
        "created": kind,
    }


def delete_path(relative_path: str) -> dict:
    path = resolve_workspace_path(relative_path)
    if path == workspace_root():
        raise ValueError("The workspace root cannot be deleted.")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()
    else:
        raise FileNotFoundError(f"Path not found: {relative_path}")
    return {"path": relative_path.replace("\\", "/"), "deleted": True}


def move_path(source_path: str, destination_path: str) -> dict:
    source = resolve_workspace_path(source_path)
    destination = resolve_workspace_path(destination_path)
    if source == workspace_root():
        raise ValueError("The workspace root cannot be moved.")
    if not source.exists():
        raise FileNotFoundError(f"Path not found: {source_path}")
    if destination.exists():
        raise FileExistsError(f"Path already exists: {destination_path}")
    if source.is_dir():
        try:
            destination.relative_to(source)
        except ValueError:
            pass
        else:
            raise ValueError("A directory cannot be moved into itself.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return {
        "source_path": source_path.replace("\\", "/"),
        "destination_path": destination.relative_to(workspace_root()).as_posix(),
        "moved": True,
    }


def copy_path(source_path: str, destination_path: str) -> dict:
    source = resolve_workspace_path(source_path)
    destination = resolve_workspace_path(destination_path)
    if source == workspace_root():
        raise ValueError("The workspace root cannot be copied.")
    if not source.exists():
        raise FileNotFoundError(f"Path not found: {source_path}")
    if destination.exists():
        raise FileExistsError(f"Path already exists: {destination_path}")
    if source.is_dir():
        try:
            destination.relative_to(source)
        except ValueError:
            pass
        else:
            raise ValueError("A directory cannot be copied into itself.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, symlinks=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return {
        "source_path": source_path.replace("\\", "/"),
        "destination_path": destination.relative_to(workspace_root()).as_posix(),
        "copied": True,
    }
