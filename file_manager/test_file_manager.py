import base64
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from file_manager import backend
from file_manager.interface import router


def test_file_manager_uses_configured_root(tmp_path, monkeypatch):
    root = tmp_path / "configured"
    root.mkdir()
    alternate_root = tmp_path / "alternate"
    alternate_root.mkdir()
    config = tmp_path / "allowed_paths.json"
    config.write_text(json.dumps({
        "map_roots": ["read-only"],
        "file_manager_roots": [
            {"name": "Main", "path": str(root)},
            {"name": "Alternate", "path": str(alternate_root)},
        ],
        "active_file_manager_root": str(root),
    }), encoding="utf-8")
    monkeypatch.setattr(backend, "CONFIG_PATH", config)

    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "ignored.pyc").touch()
    backend.create_path("notes/hello.txt")
    assert (root / "notes" / "hello.txt").is_file()
    assert backend.directory_tree()["name"] == root.name
    assert [entry["name"] for entry in backend.list_directory()] == ["notes"]
    selected = backend.select_root(str(alternate_root))
    assert selected["active_path"] == str(alternate_root)
    assert backend.workspace_root() == alternate_root
    saved_config = json.loads(config.read_text(encoding="utf-8"))
    assert saved_config["map_roots"] == ["read-only"]
    assert saved_config["active_file_manager_root"] == str(alternate_root)


def _hash(path: str) -> str:
    value = path or "/"
    encoded = base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")
    return f"l1_{encoded}"


def test_workspace_file_operations_and_traversal_rejection(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    assert client.post(
        "/api/file-manager/create",
        json={"path": "docs", "kind": "directory"},
    ).status_code == 200
    write_response = client.post(
        "/api/file-manager/write",
        json={"path": "docs/readme.md", "content": "workspace file"},
    )
    assert write_response.json()["bytes_written"] == len("workspace file")
    assert client.get("/api/file-manager/read", params={"path": "docs/readme.md"}).json() == {
        "path": "docs/readme.md",
        "content": "workspace file",
    }

    listing = client.get("/api/file-manager/list", params={"path": "docs"}).json()
    assert [entry["name"] for entry in listing["entries"]] == ["readme.md"]
    assert client.post(
        "/api/file-manager/move",
        json={"source_path": "docs/readme.md", "destination_path": "readme.md"},
    ).json()["moved"]
    assert client.get("/api/file-manager/read", params={"path": "../outside.txt"}).status_code == 400


def test_select_root_only_accepts_configured_directories(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    alternate = tmp_path / "alternate"
    alternate.mkdir()
    config = tmp_path / "allowed_paths.json"
    config.write_text(json.dumps({
        "file_manager_roots": [
            {"name": "Root", "path": str(root)},
            {"name": "Alternate", "path": str(alternate)},
        ],
        "active_file_manager_root": str(root),
    }), encoding="utf-8")
    monkeypatch.setattr(backend, "CONFIG_PATH", config)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    assert client.get("/api/file-manager/roots").json() == {
        "roots": [
            {"name": "Root", "path": str(root)},
            {"name": "Alternate", "path": str(alternate)},
        ],
        "active_path": str(root),
    }
    assert client.post(
        "/api/file-manager/roots/select",
        json={"path": str(tmp_path)},
    ).status_code == 400
    assert client.post(
        "/api/file-manager/roots/select",
        json={"path": str(alternate)},
    ).json()["active_path"] == str(alternate)
    assert client.get("/api/file-manager/tree").json()["name"] == "alternate"


def test_manage_file_manager_roots_adds_and_removes_paths(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    added_root = tmp_path / "added"
    added_root.mkdir()
    config = tmp_path / "allowed_paths.json"
    original_config = {
        "map_roots": ["keep-map-root"],
        "file_manager_roots": [{"name": "Root", "path": str(root)}],
        "active_file_manager_root": str(root),
        "sandbox_roots": ["keep-sandbox-root"],
    }
    config.write_text(json.dumps(original_config), encoding="utf-8")
    monkeypatch.setattr(backend, "CONFIG_PATH", config)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    added = client.post(
        "/api/file-manager/roots/manage",
        json={"action": "add", "paths": [str(added_root), str(root)]},
    )
    assert added.status_code == 200
    assert added.json()["added"] == [str(added_root)]
    assert added.json()["unchanged"] == [str(root)]
    saved_config = json.loads(config.read_text(encoding="utf-8"))
    assert saved_config["map_roots"] == original_config["map_roots"]
    assert saved_config["sandbox_roots"] == original_config["sandbox_roots"]
    assert len(saved_config["file_manager_roots"]) == 2

    removed = client.post(
        "/api/file-manager/roots/manage",
        json={"action": "remove", "paths": [str(root)]},
    )
    assert removed.status_code == 200
    assert removed.json()["active_path"] == str(added_root)
    assert removed.json()["removed"] == [str(root)]

    last_root = client.post(
        "/api/file-manager/roots/manage",
        json={"action": "remove", "paths": [str(added_root)]},
    )
    assert last_root.status_code == 400
    assert backend.configured_roots() == [{"name": "added", "path": str(added_root)}]

    invalid_path = client.post(
        "/api/file-manager/roots/manage",
        json={"action": "add", "paths": [str(tmp_path / "missing")]},
    )
    assert invalid_path.status_code == 400


def test_elfinder_open_and_put_use_the_shared_workspace_service(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "workspace_root", lambda: tmp_path)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    opened = client.post(
        "/api/elfinder/connector",
        data={"cmd": "open", "target": _hash("")},
    ).json()
    assert opened["cwd"]["hash"] == _hash("")

    created = client.post(
        "/api/elfinder/connector",
        data={"cmd": "mkfile", "target": _hash(""), "name": "note.txt"},
    ).json()
    target_hash = created["added"][0]["hash"]
    updated = client.post(
        "/api/elfinder/connector",
        data={"cmd": "put", "target": target_hash, "content": "from elFinder"},
    ).json()

    assert updated["changed"][0]["path"] == "note.txt"
    assert client.get(
        "/api/file-manager/read", params={"path": "note.txt"}
    ).json()["content"] == "from elFinder"

    folder = client.post(
        "/api/elfinder/connector",
        data={"cmd": "mkdir", "target": _hash(""), "name": "folder"},
    ).json()["added"][0]
    assert client.post(
        "/api/elfinder/connector",
        data={
            "cmd": "paste",
            "src[]": target_hash,
            "dst": folder["hash"],
            "cut": "0",
        },
    ).json()["added"][0]["path"] == "folder/note.txt"

    renamed = client.post(
        "/api/elfinder/connector",
        data={
            "cmd": "rename",
            "target": _hash("folder/note.txt"),
            "name": "renamed.txt",
        },
    ).json()
    assert renamed["added"][0]["path"] == "folder/renamed.txt"
    assert client.post(
        "/api/elfinder/connector",
        data={"cmd": "tree", "target": _hash("")},
    ).json()["tree"][0]["hash"] == _hash("folder")
    assert "note.txt" in client.post(
        "/api/elfinder/connector",
        data={"cmd": "ls", "target": _hash("")},
    ).json()["list"].values()

    moved = client.post(
        "/api/elfinder/connector",
        data={
            "cmd": "paste",
            "src[]": target_hash,
            "dst": folder["hash"],
            "cut": "1",
        },
    ).json()
    assert moved["added"][0]["path"] == "folder/note.txt"
    assert moved["removed"] == [target_hash]

    assert client.post(
        "/api/elfinder/connector",
        data={"cmd": "rm", "targets[]": _hash("folder")},
    ).json()["removed"] == [_hash("folder")]

    rejected = client.post(
        "/api/elfinder/connector",
        data={"cmd": "rm", "targets[]": _hash("")},
    ).json()
    assert "error" in rejected
