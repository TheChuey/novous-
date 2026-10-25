"""Configuration and persistence for named RAG knowledge bases."""

import json
import os
import tempfile
import uuid
from contextlib import nullcontext
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parent / "rag_config.json"
DATA_DIR = Path(__file__).resolve().parent / "data"


def _read_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _normalized_config() -> dict:
    data = _read_config()
    original = json.dumps(data, sort_keys=True)
    bases = data.get("knowledge_bases")
    if not isinstance(bases, list) or not bases:
        legacy_path = str(data.get("knowledge_base_path") or "").strip()
        if legacy_path:
            legacy_folder = Path(legacy_path)
            bases = [{
                "id": "legacy",
                "name": legacy_folder.name or "Legacy source",
                "path": legacy_path,
                "active": True,
                "legacy_index": True,
            }]
        else:
            bases = []

    valid_bases = []
    nonlegacy_names = {
        str(entry.get("name", "")).strip().casefold()
        for entry in bases
        if isinstance(entry, dict)
        and entry.get("name")
        and not (
            str(entry.get("id")) == "default"
            or str(entry.get("name", "")).strip().casefold() == "default knowledge base"
        )
    }
    used_names = set()
    for entry in bases:
        if not isinstance(entry, dict) or not entry.get("id") or not entry.get("path"):
            continue
        base = dict(entry)
        path = str(base["path"])
        legacy_name = str(base.get("name", "")).strip().casefold() == "default knowledge base"
        legacy_source = str(base.get("id")) == "default" or legacy_name
        if legacy_source and not base.get("legacy_name_migrated"):
            folder_name = Path(path).name.strip() or "Legacy source"
            base["name"] = folder_name
            if folder_name.casefold() in used_names or folder_name.casefold() in nonlegacy_names:
                base["name"] = f"{folder_name} (legacy index)"
            base["legacy_name_migrated"] = True
        base["name"] = " ".join(str(base.get("name") or Path(path).name or "Knowledge source").split())
        if base["name"].casefold() in used_names:
            suffix = 2
            while f"{base['name']} ({suffix})".casefold() in used_names:
                suffix += 1
            base["name"] = f"{base['name']} ({suffix})"
        used_names.add(base["name"].casefold())
        valid_bases.append(base)
    bases = valid_bases
    data["knowledge_bases"] = bases
    data.pop("knowledge_base_path", None)

    valid_ids = {
        str(base.get("id"))
        for base in bases
        if isinstance(base, dict) and base.get("id")
    }
    selected = str(data.get("selected_knowledge_base") or "")
    active_ids = [
        str(base["id"]) for base in bases if base.get("active", True)
    ]
    if selected not in valid_ids or not any(
        str(base["id"]) == selected and base.get("active", True)
        for base in bases
    ):
        data["selected_knowledge_base"] = next(
            iter(active_ids),
            None,
        )
    if json.dumps(data, sort_keys=True) != original:
        _write_config(data)
    return data


def _write_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=CONFIG_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, CONFIG_PATH)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def configured_path() -> str:
    """Return the selected named source folder."""
    return str(get_knowledge_base()["path"])


def knowledge_base_path(base_id: str | None = None) -> Path:
    """Return the selected or specified knowledge-base folder."""
    base = get_knowledge_base(base_id)
    return Path(str(base["path"])).expanduser().resolve()


def get_knowledge_base(base_id: str | None = None) -> dict:
    data = _normalized_config()
    key = base_id or data.get("selected_knowledge_base")
    if not key:
        raise ValueError("No knowledge source exists. Add a named source first.")
    for base in data["knowledge_bases"]:
        if isinstance(base, dict) and str(base.get("id")) == key:
            return dict(base)
    raise ValueError(f"Unknown knowledge base: {key}")


def list_knowledge_bases(include_archived: bool = True) -> list[dict]:
    data = _normalized_config()
    bases = [
        dict(base) for base in data["knowledge_bases"]
        if isinstance(base, dict) and (include_archived or base.get("active", True))
    ]
    selected = data["selected_knowledge_base"]
    for base in bases:
        base["selected"] = str(base.get("id")) == selected
    return bases


def selected_knowledge_base_id() -> str:
    selected = _normalized_config().get("selected_knowledge_base")
    if not selected:
        raise ValueError("No knowledge source exists. Add a named source first.")
    return str(selected)


def database_path(base_id: str | None = None) -> Path | None:
    base = get_knowledge_base(base_id)
    if base.get("legacy_index"):
        return None
    return DATA_DIR / "rag_indexes" / f"{base['id']}.sqlite3"


def database_context(base_id: str | None = None):
    """Select the isolated index for one named source."""
    path = database_path(base_id)
    if path is None:
        return nullcontext()
    from agentMemory import rag_database

    return rag_database.use_database(path)


def select_knowledge_base(base_id: str) -> dict:
    data = _normalized_config()
    base = next(
        (
            entry for entry in data["knowledge_bases"]
            if isinstance(entry, dict) and str(entry.get("id")) == str(base_id)
        ),
        None,
    )
    if base is None or not base.get("active", True):
        raise ValueError(f"Active knowledge base not found: {base_id}")
    data["selected_knowledge_base"] = str(base_id)
    _write_config(data)
    return dict(base)


def add_knowledge_base(name: str, raw_path: str) -> dict:
    clean_name = " ".join(str(name or "").split())
    raw = str(raw_path or "").strip().strip('"')
    if not clean_name:
        raise ValueError("A knowledge-base name is required.")
    if clean_name.casefold() == "default knowledge base":
        raise ValueError("The default knowledge-base name is reserved; choose a branch name.")
    if not raw:
        raise ValueError("A knowledge-base folder path is required.")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ValueError("The RAG folder path must be absolute.")
    path = path.resolve()
    data = _normalized_config()
    if any(
        str(base.get("name", "")).casefold() == clean_name.casefold()
        for base in data["knowledge_bases"]
    ):
        raise ValueError(f"A knowledge source named '{clean_name}' already exists.")
    base = {
        "id": uuid.uuid4().hex,
        "name": clean_name,
        "path": str(path),
        "active": True,
        "legacy_index": False,
    }
    data["knowledge_bases"].append(base)
    data["selected_knowledge_base"] = base["id"]
    _write_config(data)
    return base


def rename_knowledge_base(base_id: str, name: str) -> dict:
    clean_name = " ".join(str(name or "").split())
    if not clean_name:
        raise ValueError("A knowledge-source name is required.")
    if clean_name.casefold() == "default knowledge base":
        raise ValueError("The default knowledge-base name is reserved; choose a branch name.")
    data = _normalized_config()
    base = next(
        (
            entry for entry in data["knowledge_bases"]
            if str(entry.get("id")) == str(base_id)
        ),
        None,
    )
    if base is None:
        raise ValueError(f"Unknown knowledge base: {base_id}")
    if any(
        str(entry.get("id")) != str(base_id)
        and str(entry.get("name", "")).casefold() == clean_name.casefold()
        for entry in data["knowledge_bases"]
    ):
        raise ValueError(f"A knowledge source named '{clean_name}' already exists.")
    base["name"] = clean_name
    _write_config(data)
    return dict(base)


def delete_knowledge_base(base_id: str) -> dict:
    data = _normalized_config()
    base = next(
        (
            entry for entry in data["knowledge_bases"]
            if str(entry.get("id")) == str(base_id)
        ),
        None,
    )
    if base is None:
        raise ValueError(f"Unknown knowledge base: {base_id}")
    data["knowledge_bases"].remove(base)
    if data.get("selected_knowledge_base") == str(base_id):
        data["selected_knowledge_base"] = next(
            (
                str(entry["id"])
                for entry in data["knowledge_bases"]
                if entry.get("active", True)
            ),
            None,
        )
    _write_config(data)
    return dict(base)


def archive_knowledge_base(base_id: str) -> dict:
    data = _normalized_config()
    base = next(
        (
            entry for entry in data["knowledge_bases"]
            if isinstance(entry, dict) and str(entry.get("id")) == str(base_id)
        ),
        None,
    )
    if base is None:
        raise ValueError(f"Unknown knowledge base: {base_id}")
    base["active"] = False
    if data["selected_knowledge_base"] == str(base_id):
        data["selected_knowledge_base"] = next(
            (
                str(item["id"])
                for item in data["knowledge_bases"]
                if item.get("active", True)
            ),
            None,
        )
    _write_config(data)
    return dict(base)


def restore_knowledge_base(base_id: str) -> dict:
    data = _normalized_config()
    base = next(
        (
            entry for entry in data["knowledge_bases"]
            if isinstance(entry, dict) and str(entry.get("id")) == str(base_id)
        ),
        None,
    )
    if base is None:
        raise ValueError(f"Unknown knowledge base: {base_id}")
    base["active"] = True
    data["selected_knowledge_base"] = str(base_id)
    _write_config(data)
    return dict(base)


def set_knowledge_base_path(raw_path: str) -> Path:
    """Change the selected named source folder."""
    raw = str(raw_path or "").strip().strip('"')
    if not raw:
        raise ValueError("A knowledge-source folder path is required.")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ValueError("The RAG folder path must be absolute.")
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"The RAG folder does not exist or is not a directory: {path}")
    data = _normalized_config()
    selected = data.get("selected_knowledge_base")
    if not selected:
        raise ValueError("Select or add a named knowledge source first.")
    base = next(item for item in data["knowledge_bases"] if str(item["id"]) == selected)
    base["path"] = str(path)
    _write_config(data)
    return path
